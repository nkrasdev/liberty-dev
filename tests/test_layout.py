from pathlib import Path


def test_dirs_exist():
    for p in [
        "services/scrapers/farfetch",
        "services/scrapers/goat",
        "services/scrapers/stockx",
        "services/scraper_core",
        "services/saver",
        "services/api",
    ]:
        assert Path(p).exists(), f"missing {p}"