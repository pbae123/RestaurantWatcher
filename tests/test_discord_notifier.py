import datetime
import json

from restaurantwatcher.diff import ChangeNotification
from restaurantwatcher.discord_notifier import (
    format_baseline_message,
    format_change_message,
    format_failure_message,
    send_discord_message,
)
from restaurantwatcher.models import DateEntry, DaySlotState, StateSnapshot, TimeSlot

DATE = datetime.date(2026, 11, 5)
SLOT_1930 = TimeSlot(time=datetime.time(19, 30))
SLOT_2000 = TimeSlot(time=datetime.time(20, 0))


class TestFormatBaselineMessage:
    def test_lists_currently_available_entries(self):
        snapshot = StateSnapshot(
            entries=(
                DateEntry(
                    date=DATE,
                    party_size=2,
                    state=DaySlotState.AVAILABLE,
                    time_slots=(SLOT_1930, SLOT_2000),
                ),
                DateEntry(
                    date=datetime.date(2026, 11, 6),
                    party_size=2,
                    state=DaySlotState.FULL,
                    time_slots=(),
                ),
            )
        )

        message = format_baseline_message(snapshot)

        assert "2026-11-05" in message
        assert "party of 2" in message
        assert "19:30" in message
        assert "20:00" in message
        assert "2026-11-06" not in message

    def test_notes_when_nothing_is_available(self):
        snapshot = StateSnapshot(
            entries=(
                DateEntry(
                    date=DATE, party_size=2, state=DaySlotState.FULL, time_slots=()
                ),
            )
        )

        message = format_baseline_message(snapshot)

        assert "no open tables" in message.lower()


class TestFormatChangeMessage:
    def test_lists_each_change_with_date_party_size_and_times(self):
        changes = [
            ChangeNotification(date=DATE, party_size=2, time_slots=(SLOT_1930,)),
            ChangeNotification(
                date=datetime.date(2026, 11, 6),
                party_size=3,
                time_slots=(SLOT_2000,),
            ),
        ]

        message = format_change_message(changes)

        assert "2026-11-05" in message
        assert "party of 2" in message
        assert "19:30" in message
        assert "2026-11-06" in message
        assert "party of 3" in message
        assert "20:00" in message


class TestFormatFailureMessage:
    def test_includes_the_error_text(self):
        message = format_failure_message("Playwright timeout after 30s")

        assert "Playwright timeout after 30s" in message


class TestSendDiscordMessage:
    def test_posts_content_as_json_to_the_webhook_url(self, monkeypatch):
        captured = {}

        def fake_urlopen(request):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["content_type"] = request.get_header("Content-type")

        monkeypatch.setattr(
            "restaurantwatcher.discord_notifier.urllib.request.urlopen", fake_urlopen
        )

        send_discord_message("https://discord.com/api/webhooks/test/token", "hello")

        assert captured["url"] == "https://discord.com/api/webhooks/test/token"
        assert captured["method"] == "POST"
        assert captured["body"] == {"content": "hello"}
        assert captured["content_type"] == "application/json"
