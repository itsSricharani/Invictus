from datetime import datetime
from fastapi.responses import HTMLResponse
from scraper.collection_service import collect_fares
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import pandas as pd
from fastapi import FastAPI, HTTPException
from pipeline.data_repository import load_database_data, load_unified_data
from pipeline.validator import validate_weights
from pipeline.index_calculator import (
    calculate_route_index,
    calculate_lead_time_index,
    calculate_weighted_national_index,
    calculate_route_trend,
    calculate_historical_index  
)


app = FastAPI(
    title="APIx",
    version="0.1.0",
    description="Real-Time Airfare Price Index for India"
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)


DATA_FILE = "data/sample_fares.csv"
WEIGHTS_FILE = "data/route_weights.csv"


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )



@app.get("/system-status")
def get_system_status():

    df = load_unified_data()

    latest_date = df["date"].max()

    return {

        "status": "operational",

        "total_records": len(df),

        "latest_data_date": str(latest_date),

        "routes_monitored":
            df["route"].nunique(),

        "airlines_monitored":
            df["airline"].nunique(),

        "last_checked":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    }

@app.get("/index")
def get_index():

    df = load_unified_data()

    weights_df = pd.read_csv(WEIGHTS_FILE)

    validate_weights(weights_df)

    available_dates = sorted(df["date"].unique())

    base_date = available_dates[0]
    current_date = available_dates[-1]

    route_indices = calculate_route_index(
        df,
        base_date,
        current_date
    )

    national_index = calculate_weighted_national_index(
        route_indices,
        weights_df
    )

    return {
        "base_date": base_date,
        "current_date": current_date,
        "national_index": round(float(national_index), 2),
        "route_indices": {
            route: round(float(value), 2)
            for route, value in route_indices.items()
        }
    }

@app.get("/index/history")
def get_index_history():
    df = load_unified_data()
    weights_df = pd.read_csv(WEIGHTS_FILE)

    validate_weights(weights_df)

    history = calculate_historical_index(
        df,
        weights_df
    )

    dates = list(history.keys())

    history_with_changes = []

    previous_value = None

    for date in dates:
        current_value = history[date]

        if previous_value is None:
            percentage_change = 0
        else:
            percentage_change = (
                (current_value - previous_value)
                / previous_value
            ) * 100

        history_with_changes.append({
            "date": date,
            "index": current_value,
            "change_percent": round(
                percentage_change,
                2
            )
        })

        previous_value = current_value

    return {
        "base_date": dates[0],
        "history": history_with_changes
    }


@app.get("/lead-times")
def get_lead_time_indices():

    df = load_unified_data()

    available_dates = sorted(df["date"].unique())

    base_date = available_dates[0]
    current_date = available_dates[-1]

    lead_time_indices = calculate_lead_time_index(
        df,
        base_date,
        current_date
    )

    return {
        "base_date": base_date,
        "current_date": current_date,
        "lead_time_indices": {
            f"T+{lead_time}": round(float(value), 2)
            for lead_time, value in lead_time_indices.items()
        }
    }


@app.get("/routes")
def get_routes():
    df = load_unified_data()

    routes = sorted(df["route"].unique().tolist())

    return {
        "routes": routes
    }


@app.get("/routes/{route}")
def get_route(route: str):
    df = load_unified_data()

    available_routes = df["route"].unique()

    if route not in available_routes:
        raise HTTPException(
            status_code=404,
            detail=f"Route {route} not found"
        )

    trend = calculate_route_trend(df, route)

    return {
        "route": route,
        "average_fares": {
            date: round(float(price), 2)
            for date, price in trend.items()
        }
    }

@app.get("/data-quality")

def get_data_quality():

    df = load_unified_data()

    database_df = load_database_data()

    return {

        "total_records": len(df),

        "live_database_records": len(database_df),

        "historical_records": (
            len(df) - len(database_df)
        ),

        "routes": df["route"].nunique(),

        "airlines": df["airline"].nunique(),

        "sources": df["source"].nunique(),

        "date_range": {

            "start": str(
                df["date"].min()
            ),

            "end": str(
                df["date"].max()
            )

        }

    }

@app.get("/summary")
def get_summary():

    df = load_unified_data()

    weights_df = pd.read_csv(
        WEIGHTS_FILE
    )

    validate_weights(weights_df)

    available_dates = sorted(
        df["date"].unique()
    )

    base_date = available_dates[0]

    current_date = available_dates[-1]


    route_indices = calculate_route_index(
        df,
        base_date,
        current_date
    )


    national_index = (
        calculate_weighted_national_index(
            route_indices,
            weights_df
        )
    )


    history = calculate_historical_index(
        df,
        weights_df
    )


    lead_time_indices = (
        calculate_lead_time_index(
            df,
            base_date,
            current_date
        )
    )


    return {

        "index": {

            "base_date": base_date,

            "current_date": current_date,

            "national_index":
                round(
                    float(national_index),
                    2
                ),

            "route_indices": {

                route:
                round(float(value), 2)

                for route, value
                in route_indices.items()

            }

        },


        "history": {

            date:
            round(float(value), 2)

            for date, value
            in history.items()

        },


        "lead_times": {

            f"T+{lead_time}":
            round(float(value), 2)

            for lead_time, value
            in lead_time_indices.items()

        },


        "data_quality": {

            "records":
                len(df),

            "routes":
                df["route"].nunique(),

            "airlines":
                df["airline"].nunique(),

            "sources":
                df["source"].nunique()

        }

    }

@app.post("/collect")
def collect_latest_fares():

    try:

        result = collect_fares()

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )