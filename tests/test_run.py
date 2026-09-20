import datetime

from restaurantwatcher.discord_notifier import format_baseline_message, format_change_message
from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot
from restaurantwatcher.run import run
from restaurantwatcher.state_store import load_snapshot, save_snapshot

DATE = datetime.date(2026, 11, 5)
SLOT_1930 = TimeSlot(time=datetime.time(19, 30))


def _entry(state, time_slots=()):
    return DateEntry(date=DATE, party_size=2, state=state, time_slots=time_slots)


class _RecordingSender:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def __call__(self, webhook_url: str, content: str) -> None:
        self.calls.append((webhook_url, content))


class TestRunFirstEverRun:
    def test_sends_baseline_message_and_saves_state(self, tmp_path):
        state_path = tmp_path / "state.json"
        new_snapshot = StateSnapshot(entries=(_entry(DaySlotState.FULL),))
        sender = _RecordingSender()

        result = run(
            scrape_fn=lambda: new_snapshot,
            send_fn=sender,
            state_path=state_path,
            webhook_url="https://discord.example/webhook",
        )

        assert result == new_snapshot
        assert sender.calls == [
            ("https://discord.example/webhook", format_baseline_message(new_snapshot))
        ]
        assert load_snapshot(state_path) == new_snapshot


class TestRunSubsequentRun:
    def test_sends_change_message_when_availability_changed(self, tmp_path):
        state_path = tmp_path / "state.json"
        old_snapshot = StateSnapshot(entries=(_entry(DaySlotState.FULL),))
        save_snapshot(state_path, old_snapshot)
        new_snapshot = StateSnapshot(
            entries=(_entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),)
        )
        sender = _RecordingSender()

        run(
            scrape_fn=lambda: new_snapshot,
            send_fn=sender,
            state_path=state_path,
            webhook_url="https://discord.example/webhook",
        )

        from restaurantwatcher.diff import diff_snapshots

        expected_changes = diff_snapshots(old_snapshot, new_snapshot)
        assert sender.calls == [
            (
                "https://discord.example/webhook",
                format_change_message(expected_changes),
            )
        ]
        assert load_snapshot(state_path) == new_snapshot

    def test_sends_nothing_when_no_changes(self, tmp_path):
        state_path = tmp_path / "state.json"
        snapshot = StateSnapshot(entries=(_entry(DaySlotState.FULL),))
        save_snapshot(state_path, snapshot)
        sender = _RecordingSender()

        run(
            scrape_fn=lambda: snapshot,
            send_fn=sender,
            state_path=state_path,
            webhook_url="https://discord.example/webhook",
        )

        assert sender.calls == []
        assert load_snapshot(state_path) == snapshot
