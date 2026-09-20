import datetime
import json

from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot
from restaurantwatcher.state_store import load_snapshot, save_snapshot


class TestSaveSnapshot:
    def test_writes_json_representing_entries(self, tmp_path):
        path = tmp_path / "state.json"
        snapshot = StateSnapshot(
            entries=(
                DateEntry(
                    date=datetime.date(2026, 11, 2),
                    party_size=2,
                    state=DaySlotState.FULL,
                    time_slots=(),
                ),
                DateEntry(
                    date=datetime.date(2026, 11, 2),
                    party_size=3,
                    state=DaySlotState.AVAILABLE,
                    time_slots=(TimeSlot(time=datetime.time(19, 30)),),
                ),
            )
        )

        save_snapshot(path, snapshot)

        data = json.loads(path.read_text())
        assert data == {
            "entries": [
                {
                    "date": "2026-11-02",
                    "party_size": 2,
                    "state": "FULL",
                    "time_slots": [],
                },
                {
                    "date": "2026-11-02",
                    "party_size": 3,
                    "state": "AVAILABLE",
                    "time_slots": ["19:30"],
                },
            ]
        }


class TestLoadSnapshot:
    def test_returns_none_when_file_missing(self, tmp_path):
        path = tmp_path / "does-not-exist.json"

        assert load_snapshot(path) is None

    def test_round_trips_a_saved_snapshot(self, tmp_path):
        path = tmp_path / "state.json"
        original = StateSnapshot(
            entries=(
                DateEntry(
                    date=datetime.date(2026, 11, 2),
                    party_size=2,
                    state=DaySlotState.NOT_YET_OPEN,
                    time_slots=(),
                ),
                DateEntry(
                    date=datetime.date(2026, 11, 3),
                    party_size=2,
                    state=DaySlotState.AVAILABLE,
                    time_slots=(
                        TimeSlot(time=datetime.time(18, 0)),
                        TimeSlot(time=datetime.time(19, 30)),
                    ),
                ),
            )
        )
        save_snapshot(path, original)

        loaded = load_snapshot(path)

        assert loaded == original
