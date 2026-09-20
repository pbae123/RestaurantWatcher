import datetime
import os
from pathlib import Path
from typing import Callable

from playwright.sync_api import sync_playwright

from restaurantwatcher.diff import diff_snapshots
from restaurantwatcher.discord_notifier import (
    format_baseline_message,
    format_change_message,
    send_discord_message,
)
from restaurantwatcher.models import StateSnapshot
from restaurantwatcher.scraper import scrape_availability
from restaurantwatcher.state_store import load_snapshot, save_snapshot

SHOP_URL = "https://www.catchtable.net/shop/jungsik"
WATCH_WINDOW = [
    datetime.date(2026, 11, 1) + datetime.timedelta(days=offset) for offset in range(10)
]
PARTY_SIZES = [2, 3]
DEFAULT_STATE_FILE_PATH = "state.json"


def run(
    scrape_fn: Callable[[], StateSnapshot],
    send_fn: Callable[[str, str], None],
    state_path: Path,
    webhook_url: str,
) -> StateSnapshot:
    new_snapshot = scrape_fn()
    old_snapshot = load_snapshot(state_path)

    if old_snapshot is None:
        send_fn(webhook_url, format_baseline_message(new_snapshot))
    else:
        changes = diff_snapshots(old_snapshot, new_snapshot)
        if changes:
            send_fn(webhook_url, format_change_message(changes))

    save_snapshot(state_path, new_snapshot)
    return new_snapshot


def scrape_live_site(
    shop_url: str, watch_window: list[datetime.date], party_sizes: list[int]
) -> StateSnapshot:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(shop_url)
            return scrape_availability(page, watch_window, party_sizes)
        finally:
            browser.close()


def main() -> StateSnapshot:
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    state_path = Path(os.environ.get("STATE_FILE_PATH", DEFAULT_STATE_FILE_PATH))

    return run(
        scrape_fn=lambda: scrape_live_site(SHOP_URL, WATCH_WINDOW, PARTY_SIZES),
        send_fn=send_discord_message,
        state_path=state_path,
        webhook_url=webhook_url,
    )


if __name__ == "__main__":
    main()
