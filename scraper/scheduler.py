import atexit
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from scraper.collector import run_collection


_scheduler = None


def _startup_collection():
    """Runs the initial collection in a background thread."""
    try:
        print("[Scheduler] Initial fare collection started.")
        result = run_collection()
        
        collected = result.get('collected', 0) if isinstance(result, dict) else 'Unknown'
        saved = result.get('saved', 0) if isinstance(result, dict) else 'Unknown'
        
        print(f"[Scheduler] Initial fare collection completed: {collected} records collected, {saved} records saved.")
        
        global _scheduler
        if _scheduler:
            job = _scheduler.get_job("fare_collection")
            if job and job.next_run_time:
                print(f"[Scheduler] Next collection scheduled in 5 hours at {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')}.")
    except Exception as e:
        print(f"[Scheduler] Initial fare collection failed: {e}")


def start_scheduler():
    """
    Starts a background job that runs the fare collector every 5 hours.
    Safe to call more than once (e.g. with --reload) — only starts a
    single scheduler instance per process.
    """
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    _scheduler.add_job(
        run_collection,
        trigger="interval",
        hours=5,
        id="fare_collection",
        replace_existing=True
    )

    _scheduler.start()

    # Trigger immediate collection without blocking
    threading.Thread(target=_startup_collection, daemon=True).start()

    print("[Scheduler] Started interval fare collection every 5 hours.")
    return _scheduler


def stop_scheduler():
    """Stops the scheduler cleanly."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        print("[Scheduler] Shutdown completed.")


def get_scheduler_status():
    """Returns the current status and next run time of the scheduler."""
    global _scheduler
    if not _scheduler:
        return {"status": "Scheduler unavailable", "next_run": None}
    
    job = _scheduler.get_job("fare_collection")
    if job and job.next_run_time:
        return {
            "status": "LIVE",
            "next_run": job.next_run_time.isoformat(),
            "interval_hours": 5
        }
    return {"status": "Scheduler unavailable", "next_run": None}