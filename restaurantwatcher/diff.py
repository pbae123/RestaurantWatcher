import datetime
from dataclasses import dataclass

from restaurantwatcher.models import DaySlotState, StateSnapshot, TimeSlot


@dataclass(frozen=True)
class ChangeNotification:
    date: datetime.date
    party_size: int
    time_slots: tuple[TimeSlot, ...]


def diff_snapshots(
    old: StateSnapshot | None, new: StateSnapshot
) -> list[ChangeNotification]:
    if old is None:
        return []

    changes = []
    for entry in new.entries:
        if entry.state != DaySlotState.AVAILABLE:
            continue

        old_entry = old.entry_for(entry.date, entry.party_size)
        if old_entry is not None and old_entry.state == DaySlotState.AVAILABLE:
            old_times = {slot.time for slot in old_entry.time_slots}
            new_slots = tuple(
                slot for slot in entry.time_slots if slot.time not in old_times
            )
        else:
            new_slots = entry.time_slots

        if new_slots:
            changes.append(
                ChangeNotification(
                    date=entry.date, party_size=entry.party_size, time_slots=new_slots
                )
            )

    return changes
