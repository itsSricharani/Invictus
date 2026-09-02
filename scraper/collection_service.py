from scraper.collector import run_collection


def collect_fares():

    result = run_collection()

    return {
        "status": "success",
        "message": "Fare collection completed",
        "result": result
    }