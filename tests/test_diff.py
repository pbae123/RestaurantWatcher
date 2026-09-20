import datetime

from restaurantwatcher.diff import ChangeNotification, diff_snapshots
from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot

DATE = datetime.date(2026, 11, 2)
SLOT_1930 = TimeSlot(time=datetime.time(19, 30))
SLOT_2000 = TimeSlot(time=datetime.time(20, 0))


def entry(state, party_size=2, time_slots=()):
    return DateEntry(date=DATE, party_size=party_size, state=state, time_slots=time_slots)


class TestDiffSnapshotsBaseline:
    def test_returns_no_changes_when_old_is_none(self):
        new = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))

        assert diff_snapshots(None, new) == []


class TestDiffSnapshotsBecameAvailable:
    def test_reports_all_slots_when_day_opens_from_not_yet_open(self):
        old = StateSnapshot(entries=(entry(DaySlotState.NOT_YET_OPEN),))
        new = StateSnapshot(
            entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930, SLOT_2000)),)
        )

        changes = diff_snapshots(old, new)

        assert changes == [
            ChangeNotification(date=DATE, party_size=2, time_slots=(SLOT_1930, SLOT_2000))
        ]

    def test_reports_all_slots_when_day_opens_from_full(self):
        old = StateSnapshot(entries=(entry(DaySlotState.FULL),))
        new = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))

        changes = diff_snapshots(old, new)

        assert changes == [
            ChangeNotification(date=DATE, party_size=2, time_slots=(SLOT_1930,))
        ]

    def test_no_change_when_still_full(self):
        old = StateSnapshot(entries=(entry(DaySlotState.FULL),))
        new = StateSnapshot(entries=(entry(DaySlotState.FULL),))

        assert diff_snapshots(old, new) == []

    def test_no_change_when_still_not_yet_open(self):
        old = StateSnapshot(entries=(entry(DaySlotState.NOT_YET_OPEN),))
        new = StateSnapshot(entries=(entry(DaySlotState.NOT_YET_OPEN),))

        assert diff_snapshots(old, new) == []


class TestDiffSnapshotsNewTimeSlot:
    def test_reports_only_newly_opened_slots_on_already_available_day(self):
        old = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))
        new = StateSnapshot(
            entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930, SLOT_2000)),)
        )

        changes = diff_snapshots(old, new)

        assert changes == [
            ChangeNotification(date=DATE, party_size=2, time_slots=(SLOT_2000,))
        ]

    def test_no_change_when_slots_unchanged(self):
        old = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))
        new = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))

        assert diff_snapshots(old, new) == []

    def test_no_change_when_a_slot_closes(self):
        old = StateSnapshot(
            entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930, SLOT_2000)),)
        )
        new = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))

        assert diff_snapshots(old, new) == []


class TestDiffSnapshotsMultipleEntries:
    def test_only_reports_changed_entries(self):
        other_party = entry(DaySlotState.FULL, party_size=3)
        old = StateSnapshot(entries=(entry(DaySlotState.FULL), other_party))
        new = StateSnapshot(
            entries=(
                entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),
                other_party,
            )
        )

        changes = diff_snapshots(old, new)

        assert changes == [
            ChangeNotification(date=DATE, party_size=2, time_slots=(SLOT_1930,))
        ]

    def test_treats_entry_missing_from_old_as_not_yet_open(self):
        old = StateSnapshot(entries=())
        new = StateSnapshot(entries=(entry(DaySlotState.AVAILABLE, time_slots=(SLOT_1930,)),))

        changes = diff_snapshots(old, new)

        assert changes == [
            ChangeNotification(date=DATE, party_size=2, time_slots=(SLOT_1930,))
        ]
