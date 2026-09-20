import datetime

from restaurantwatcher.run import SHOP_URL, scrape_live_site


def run_canary() -> None:
    probe_date = datetime.date.today() + datetime.timedelta(days=1)
    snapshot = scrape_live_site(SHOP_URL, watch_window=[probe_date], party_sizes=[2])
    if not snapshot.entries:
        raise RuntimeError("Canary scrape produced no entries")


if __name__ == "__main__":
    run_canary()
