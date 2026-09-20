import datetime
from pathlib import Path

from restaurantwatcher.models import DaySlotState
from restaurantwatcher.scraper import (
    _navigate_to_month,
    _open_date_picker,
    scrape_availability,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "reservation_dialog.html"


def _load_fixture(page):
    page.goto(f"file://{FIXTURE_PATH}")


class TestScrapeAvailability:
    def test_reads_available_full_and_not_yet_open_states(self, page):
        _load_fixture(page)

        snapshot = scrape_availability(
            page,
            watch_window=[datetime.date(2026, 11, 2), datetime.date(2026, 11, 3)],
            party_sizes=[2, 3],
            timeout_ms=1000,
        )

        available = snapshot.entry_for(datetime.date(2026, 11, 2), 2)
        assert available.state == DaySlotState.AVAILABLE
        assert [slot.time for slot in available.time_slots] == [
            datetime.time(12, 0),
            datetime.time(19, 30),
        ]

        full = snapshot.entry_for(datetime.date(2026, 11, 2), 3)
        assert full.state == DaySlotState.FULL
        assert full.time_slots == ()

        not_yet_open = snapshot.entry_for(datetime.date(2026, 11, 3), 2)
        assert not_yet_open.state == DaySlotState.NOT_YET_OPEN
        assert not_yet_open.time_slots == ()

    def test_treats_missing_data_as_not_yet_open(self, page):
        _load_fixture(page)

        snapshot = scrape_availability(
            page,
            watch_window=[datetime.date(2026, 11, 3)],
            party_sizes=[3],
            timeout_ms=1000,
        )

        entry = snapshot.entry_for(datetime.date(2026, 11, 3), 3)
        assert entry.state == DaySlotState.NOT_YET_OPEN

    def test_navigates_months_forward_from_initial_view(self, page):
        _load_fixture(page)

        snapshot = scrape_availability(
            page,
            watch_window=[datetime.date(2026, 11, 2)],
            party_sizes=[2],
            timeout_ms=1000,
        )

        entry = snapshot.entry_for(datetime.date(2026, 11, 2), 2)
        assert entry is not None
        assert entry.state == DaySlotState.AVAILABLE

    def test_does_not_navigate_when_date_is_in_the_initially_displayed_month(self, page):
        _load_fixture(page)

        snapshot = scrape_availability(
            page,
            watch_window=[datetime.date(2026, 9, 15)],
            party_sizes=[2],
            timeout_ms=1000,
        )

        entry = snapshot.entry_for(datetime.date(2026, 9, 15), 2)
        assert entry.state == DaySlotState.NOT_YET_OPEN


class TestNavigateToMonth:
    def test_clicks_previous_page_when_target_month_is_earlier(self, page):
        _load_fixture(page)
        _open_date_picker(page)
        _navigate_to_month(page, datetime.date(2026, 11, 1))
        assert page.get_by_role("button", name="Nov 2026").count() == 1

        _navigate_to_month(page, datetime.date(2026, 10, 1))

        assert page.get_by_role("button", name="Oct 2026").count() == 1
