import time
from typing import Callable, TypeVar

from restaurantwatcher.discord_notifier import format_failure_message

T = TypeVar("T")

DEFAULT_RETRY_DELAY_SECONDS = 30.0


def run_with_retry(
    run_fn: Callable[[], T],
    send_fn: Callable[[str, str], None],
    webhook_url: str,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    try:
        return run_fn()
    except Exception:
        sleep_fn(retry_delay_seconds)

    try:
        return run_fn()
    except Exception as error:
        send_fn(webhook_url, format_failure_message(str(error)))
        raise
