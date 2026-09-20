import datetime
import json
from pathlib import Path

from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot


def _entry_to_dict(entry: DateEntry) -> dict:
    return {
        "date": entry.date.isoformat(),
        "party_size": entry.party_size,
        "state": entry.state.value,
        "time_slots": [slot.time.strftime("%H:%M") for slot in entry.time_slots],
    }


def _entry_from_dict(data: dict) -> DateEntry:
    return DateEntry(
        date=datetime.date.fromisoformat(data["date"]),
        party_size=data["party_size"],
        state=DaySlotState(data["state"]),
        time_slots=tuple(
            TimeSlot(time=datetime.datetime.strptime(raw, "%H:%M").time())
            for raw in data["time_slots"]
        ),
    )


def save_snapshot(path: Path, snapshot: StateSnapshot) -> None:
    data = {"entries": [_entry_to_dict(entry) for entry in snapshot.entries]}
    Path(path).write_text(json.dumps(data, indent=2))


def load_snapshot(path: Path) -> StateSnapshot | None:
    path = Path(path)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    entries = tuple(_entry_from_dict(entry) for entry in data["entries"])
    return StateSnapshot(entries=entries)
