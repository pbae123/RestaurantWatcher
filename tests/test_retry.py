import pytest

from restaurantwatcher.discord_notifier import format_failure_message
from restaurantwatcher.retry import run_with_retry


class _RecordingSender:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def __call__(self, webhook_url: str, content: str) -> None:
        self.calls.append((webhook_url, content))


class _FlakyCallable:
    def __init__(self, failures_before_success: int):
        self.failures_before_success = failures_before_success
        self.call_count = 0

    def __call__(self):
        self.call_count += 1
        if self.call_count <= self.failures_before_success:
            raise RuntimeError(f"attempt {self.call_count} failed")
        return "success"


class TestRunWithRetrySucceedsFirstTry:
    def test_does_not_sleep_or_retry_or_notify(self):
        run_fn = _FlakyCallable(failures_before_success=0)
        sender = _RecordingSender()
        sleeps: list[float] = []

        result = run_with_retry(
            run_fn=run_fn,
            send_fn=sender,
            webhook_url="https://discord.example/webhook",
            retry_delay_seconds=5.0,
            sleep_fn=sleeps.append,
        )

        assert result == "success"
        assert run_fn.call_count == 1
        assert sleeps == []
        assert sender.calls == []


class TestRunWithRetrySucceedsOnRetry:
    def test_retries_once_after_a_delay_and_sends_no_failure_alert(self):
        run_fn = _FlakyCallable(failures_before_success=1)
        sender = _RecordingSender()
        sleeps: list[float] = []

        result = run_with_retry(
            run_fn=run_fn,
            send_fn=sender,
            webhook_url="https://discord.example/webhook",
            retry_delay_seconds=5.0,
            sleep_fn=sleeps.append,
        )

        assert result == "success"
        assert run_fn.call_count == 2
        assert sleeps == [5.0]
        assert sender.calls == []


class TestRunWithRetryFailsBothAttempts:
    def test_sends_failure_alert_and_reraises(self):
        run_fn = _FlakyCallable(failures_before_success=2)
        sender = _RecordingSender()
        sleeps: list[float] = []

        with pytest.raises(RuntimeError, match="attempt 2 failed"):
            run_with_retry(
                run_fn=run_fn,
                send_fn=sender,
                webhook_url="https://discord.example/webhook",
                retry_delay_seconds=5.0,
                sleep_fn=sleeps.append,
            )

        assert run_fn.call_count == 2
        assert sleeps == [5.0]
        assert sender.calls == [
            (
                "https://discord.example/webhook",
                format_failure_message("attempt 2 failed"),
            )
        ]
