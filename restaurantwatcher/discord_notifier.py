import json
import urllib.request

from restaurantwatcher.diff import ChangeNotification
from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot


def _format_entry_line(date, party_size, time_slots) -> str:
    times = ", ".join(slot.time.strftime("%H:%M") for slot in time_slots)
    return f"- {date.isoformat()} (party of {party_size}): {times}"


def format_baseline_message(snapshot: StateSnapshot) -> str:
    available: list[DateEntry] = [
        entry for entry in snapshot.entries if entry.state == DaySlotState.AVAILABLE
    ]

    lines = ["RestaurantWatcher is live. Current availability:"]
    if not available:
        lines.append("No open tables right now — you'll be notified when that changes.")
    else:
        for entry in sorted(available, key=lambda e: (e.date, e.party_size)):
            lines.append(_format_entry_line(entry.date, entry.party_size, entry.time_slots))

    return "\n".join(lines)


def format_change_message(changes: list[ChangeNotification]) -> str:
    lines = ["New availability!"]
    for change in sorted(changes, key=lambda c: (c.date, c.party_size)):
        lines.append(_format_entry_line(change.date, change.party_size, change.time_slots))

    return "\n".join(lines)


def format_failure_message(error: str) -> str:
    return f"RestaurantWatcher run failed: {error}"


def send_discord_message(webhook_url: str, content: str) -> None:
    body = json.dumps({"content": content}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "RestaurantWatcher (https://github.com/pbae123/RestaurantWatcher, 1.0)",
        },
        method="POST",
    )
    urllib.request.urlopen(request)
