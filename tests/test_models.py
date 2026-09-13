import datetime

import pytest

from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot


class TestDaySlotState:
    def test_has_three_states(self):
        assert {member.value for member in DaySlotState} == {
            "NOT_YET_OPEN",
            "FULL",
            "AVAILABLE",
        }


class TestTimeSlot:
    def test_stores_time(self):
        slot = TimeSlot(time=datetime.time(19, 30))

        assert slot.time == datetime.time(19, 30)

    def test_is_immutable(self):
        slot = TimeSlot(time=datetime.time(19, 30))

        with pytest.raises(AttributeError):
            slot.time = datetime.time(20, 0)


class TestDateEntry:
    def test_stores_date_party_size_and_state(self):
        entry = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.FULL,
            time_slots=(),
        )

        assert entry.date == datetime.date(2026, 11, 2)
        assert entry.party_size == 2
        assert entry.state == DaySlotState.FULL
        assert entry.time_slots == ()

    def test_available_entry_can_carry_time_slots(self):
        slot = TimeSlot(time=datetime.time(19, 30))

        entry = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.AVAILABLE,
            time_slots=(slot,),
        )

        assert entry.time_slots == (slot,)

    def test_rejects_non_positive_party_size(self):
        with pytest.raises(ValueError):
            DateEntry(
                date=datetime.date(2026, 11, 2),
                party_size=0,
                state=DaySlotState.FULL,
                time_slots=(),
            )

    @pytest.mark.parametrize("state", [DaySlotState.NOT_YET_OPEN, DaySlotState.FULL])
    def test_non_available_state_rejects_time_slots(self, state):
        with pytest.raises(ValueError):
            DateEntry(
                date=datetime.date(2026, 11, 2),
                party_size=2,
                state=state,
                time_slots=(TimeSlot(time=datetime.time(19, 30)),),
            )

    def test_is_immutable(self):
        entry = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.FULL,
            time_slots=(),
        )

        with pytest.raises(AttributeError):
            entry.state = DaySlotState.AVAILABLE


class TestStateSnapshot:
    def test_stores_entries(self):
        entry = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.FULL,
            time_slots=(),
        )

        snapshot = StateSnapshot(entries=(entry,))

        assert snapshot.entries == (entry,)

    def test_looks_up_entry_by_date_and_party_size(self):
        entry_2 = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.FULL,
            time_slots=(),
        )
        entry_3 = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=3,
            state=DaySlotState.AVAILABLE,
            time_slots=(TimeSlot(time=datetime.time(19, 30)),),
        )
        snapshot = StateSnapshot(entries=(entry_2, entry_3))

        assert snapshot.entry_for(datetime.date(2026, 11, 2), 3) == entry_3

    def test_lookup_returns_none_when_missing(self):
        snapshot = StateSnapshot(entries=())

        assert snapshot.entry_for(datetime.date(2026, 11, 2), 2) is None

    def test_rejects_duplicate_date_and_party_size(self):
        entry = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.FULL,
            time_slots=(),
        )
        duplicate = DateEntry(
            date=datetime.date(2026, 11, 2),
            party_size=2,
            state=DaySlotState.AVAILABLE,
            time_slots=(TimeSlot(time=datetime.time(19, 30)),),
        )

        with pytest.raises(ValueError):
            StateSnapshot(entries=(entry, duplicate))

    def test_is_immutable(self):
        snapshot = StateSnapshot(entries=())

        with pytest.raises(AttributeError):
            snapshot.entries = ()
