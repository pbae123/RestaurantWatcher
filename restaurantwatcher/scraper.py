import datetime
import re
import time

from playwright.sync_api import Page

from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot

_MONTH_LABEL_PATTERN = re.compile(r"^[A-Za-z]{3} \d{4}$")
_NOT_YET_OPEN_TEXT = "Reservations not yet open"
_TIME_BUTTON_PATTERN = re.compile(r"^\d{1,2}:\d{2} (AM|PM)$")

_DEFAULT_TIMEOUT_MS = 5000
_POLL_INTERVAL_MS = 50


def scrape_availability(
    page: Page,
    watch_window: list[datetime.date],
    party_sizes: list[int],
    timeout_ms: int = _DEFAULT_TIMEOUT_MS,
) -> StateSnapshot:
    _open_date_picker(page)

    entries = []
    for date in sorted(watch_window):
        _navigate_to_month(page, date)
        _select_date(page, date)
        for party_size in party_sizes:
            _select_party_size(page, party_size)
            state, time_slots = _read_result(page, timeout_ms)
            entries.append(
                DateEntry(
                    date=date, party_size=party_size, state=state, time_slots=time_slots
                )
            )

    return StateSnapshot(entries=tuple(entries))


def _open_date_picker(page: Page) -> None:
    page.get_by_role("button", name="Date • Time • guests").click()
    page.get_by_role("dialog").wait_for()


def _current_month(page: Page) -> datetime.date:
    label = page.get_by_role("button", name=_MONTH_LABEL_PATTERN).inner_text()
    parsed = datetime.datetime.strptime(label, "%b %Y")
    return datetime.date(parsed.year, parsed.month, 1)


def _navigate_to_month(page: Page, date: datetime.date) -> None:
    target = datetime.date(date.year, date.month, 1)
    current = _current_month(page)
    delta = (target.year - current.year) * 12 + (target.month - current.month)
    if delta == 0:
        return
    button_name = "Next page" if delta > 0 else "Previous page"
    for _ in range(abs(delta)):
        page.get_by_role("button", name=button_name).click()


def _select_date(page: Page, date: datetime.date) -> None:
    # %-d (no leading zero) matches macOS/Linux glibc strftime, which is what
    # this project's CI (GitHub Actions Linux runners) and dev machines use.
    accessible_name = date.strftime("%A, %b %-d, %Y")
    page.get_by_role("button", name=accessible_name, exact=True).click()


def _select_party_size(page: Page, party_size: int) -> None:
    page.get_by_role("button", name=str(party_size), exact=True).click()


def _read_result(
    page: Page, timeout_ms: int
) -> tuple[DaySlotState, tuple[TimeSlot, ...]]:
    not_yet_open = page.get_by_text(_NOT_YET_OPEN_TEXT)
    time_buttons = page.get_by_role("button", name=_TIME_BUTTON_PATTERN)

    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if not_yet_open.count() > 0:
            return DaySlotState.NOT_YET_OPEN, ()
        if time_buttons.count() > 0:
            slots = tuple(
                _parse_time_slot(text) for text in time_buttons.all_inner_texts()
            )
            return DaySlotState.AVAILABLE, slots
        page.wait_for_timeout(_POLL_INTERVAL_MS)

    return DaySlotState.FULL, ()


def _parse_time_slot(text: str) -> TimeSlot:
    parsed = datetime.datetime.strptime(text.strip(), "%I:%M %p")
    return TimeSlot(time=parsed.time())
