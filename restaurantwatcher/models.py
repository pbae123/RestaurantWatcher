import datetime
from dataclasses import dataclass, field
from enum import Enum


class DaySlotState(Enum):
    NOT_YET_OPEN = "NOT_YET_OPEN"
    FULL = "FULL"
    AVAILABLE = "AVAILABLE"


@dataclass(frozen=True)
class TimeSlot:
    time: datetime.time


@dataclass(frozen=True)
class DateEntry:
    date: datetime.date
    party_size: int
    state: DaySlotState
    time_slots: tuple[TimeSlot, ...] = field(default=())

    def __post_init__(self):
        if self.party_size <= 0:
            raise ValueError("party_size must be positive")
        if self.state != DaySlotState.AVAILABLE and self.time_slots:
            raise ValueError(
                f"time_slots must be empty when state is {self.state.value}"
            )


@dataclass(frozen=True)
class StateSnapshot:
    entries: tuple[DateEntry, ...] = field(default=())

    def __post_init__(self):
        keys = [(entry.date, entry.party_size) for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate (date, party_size) entries in StateSnapshot")

    def entry_for(self, date: datetime.date, party_size: int) -> DateEntry | None:
        for entry in self.entries:
            if entry.date == date and entry.party_size == party_size:
                return entry
        return None
