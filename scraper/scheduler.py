import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from scraper.collector import run_collection


_scheduler = None


def start_scheduler():
    """
    Starts a background job that runs the fare collector once a day.
    Safe to call more than once (e.g. with --reload) — only starts a
    single scheduler instance per process.
    """
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    _scheduler.add_job(
        run_collection,
        trigger="cron",
        hour=6,
        minute=0,
        id="daily_fare_collection",
        replace_existing=True
    )

    _scheduler.start()

    atexit.register(lambda: _scheduler.shutdown(wait=False))

    print("Scheduler started: daily fare collection at 06:00 IST")

    return _scheduler