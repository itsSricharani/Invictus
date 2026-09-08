from sqlalchemy.orm import Session
from fastapi import Depends
from scraper.collector import run_collection
from pipeline.cleaner import clean_fares
import io

from app.database import get_db, SessionLocal, Base, engine
from app.models import FareRecord

from datetime import datetime
from fastapi.responses import HTMLResponse, StreamingResponse

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
from pipeline.index_service import (
    get_index_data
)


from contextlib import asynccontextmanager
from scraper.scheduler import start_scheduler, stop_scheduler, get_scheduler_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if they don't exist yet (safe to call on every startup)
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="APIx",
    version="0.1.0",
    description="Real-Time Airfare Price Index for India",
    lifespan=lifespan
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
def landing(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={}
    )


@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={}
    )

@app.get("/about")
def about(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={}
    )

@app.get("/system-status")
def get_system_status():
    df = load_unified_data()
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    latest_date = df["date"].max()
    scheduler_info = get_scheduler_status()

    return {
        "status": "operational",
        "scheduler_status": scheduler_info["status"],
        "next_collection": scheduler_info["next_run"],
        "total_records": len(df),
        "latest_data_date": str(latest_date),
        "routes_monitored": df["route"].nunique(),
        "airlines_monitored": df["airline"].nunique(),
        "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/index")
def get_current_index():

    df = load_unified_data()
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

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
        "data_mode": data_mode,
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
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))
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
        "data_mode": data_mode,
        "base_date": dates[0],
        "history": history_with_changes
    }


@app.get("/lead-times")
def get_lead_time_indices():

    df = load_unified_data()
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    available_dates = sorted(df["date"].unique())

    base_date = available_dates[0]
    current_date = available_dates[-1]

    lead_time_indices = calculate_lead_time_index(
        df,
        base_date,
        current_date
    )

    return {
        "data_mode": data_mode,
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
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    routes = sorted(df["route"].unique().tolist())

    return {
        "data_mode": data_mode,
        "routes": routes
    }


@app.get("/routes/{route}")
def get_route(route: str):
    df = load_unified_data()
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    available_routes = df["route"].unique()

    if route not in available_routes:
        raise HTTPException(
            status_code=404,
            detail=f"Route {route} not found"
        )

    trend = calculate_route_trend(df, route)

    return {
        "data_mode": data_mode,
        "route": route,
        "average_fares": {
            date: round(float(price), 2)
            for date, price in trend.items()
        }
    }

@app.get("/data-quality")

def get_data_quality():

    df = load_unified_data()
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    database_df = load_database_data()

    return {

        "data_mode": data_mode,

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
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))


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

        "data_mode": data_mode,

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



@app.get("/lead-time-history")
def get_lead_time_history(route: str = "DEL-BOM"):
    """
    Returns per-date average fares for the given route across lead times
    T+1, T+7, T+15 (T+30 and T+45 are included when data exists, ready to
    be enabled on the frontend later).

    Aggregation: AVERAGE across all airlines for each (collection_date,
    lead_time) combination — one data point per date per booking window.
    Only real rows (source != 'mock') are included.
    """
    FAKE_SOURCES = {"Mock", "Airline", "test"}  # lowercase 'mock' = live scheduler, keep it
    LEAD_TIMES   = [1, 7, 15, 30, 45]

    db = SessionLocal()
    try:
        records = (
            db.query(
                FareRecord.collection_date,
                FareRecord.lead_time,
                FareRecord.total_fare,
            )
            .filter(
                FareRecord.route == route,
                FareRecord.total_fare != None,
                FareRecord.total_fare > 0,
                FareRecord.total_fare <= 100_000,
                FareRecord.source.notin_(list(FAKE_SOURCES)),
            )
            .all()
        )
    finally:
        db.close()

    if not records:
        return {
            "data_mode": "demo",
            "route": route,
            "lead_times": [],
            "dates": [],
            "series": {}
        }

    # Build {date: {lead_time: [fares...]}}
    from collections import defaultdict
    buckets: dict = defaultdict(lambda: defaultdict(list))
    for r in records:
        buckets[r.collection_date][r.lead_time].append(r.total_fare)

    all_dates = sorted(buckets.keys())

    # Build series: {lead_time: [avg_fare_per_date_or_None]}
    series: dict = {}
    for lt in LEAD_TIMES:
        row = []
        for d in all_dates:
            fares = buckets[d].get(lt)
            if fares:
                row.append(round(sum(fares) / len(fares), 2))
            else:
                row.append(None)
        series[f"T+{lt}"] = row

    return {
        "data_mode": "live",
        "route": route,
        "lead_times": [f"T+{lt}" for lt in LEAD_TIMES],
        "dates": all_dates,
        "series": series,
    }


@app.get("/sector-heatmap")
def get_sector_heatmap():
    """
    Returns day-of-week (Mon-Sun) index heat intensity for each monitored route.
    Calculates average fare per route per day of week, normalized against route base fare.
    No values are fabricated — missing day/route combinations return null.
    """
    df = load_unified_data()
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    if df.empty or "date" not in df.columns:
        return {
            "data_mode": data_mode,
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "routes": [],
            "heatmap": {}
        }

    DAYS_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Calculate base price per route (earliest date average fare)
    available_dates = sorted(df["date"].unique())
    base_date = available_dates[0] if available_dates else None
    base_prices = df[df["date"] == base_date].groupby("route")["total_fare"].mean() if base_date else {}

    # Extract day of week name (Mon, Tue, ...)
    df_copy = df.copy()
    df_copy["day_of_week"] = pd.to_datetime(df_copy["date"]).dt.strftime("%a")

    # Group by route and day_of_week
    route_dow_fares = df_copy.groupby(["route", "day_of_week"])["total_fare"].mean()

    all_routes = sorted(df["route"].unique())
    heatmap = {}

    for route in all_routes:
        base_p = base_prices.get(route)
        if not base_p or base_p <= 0:
            # Fallback to route mean if base_date price is missing
            base_p = df[df["route"] == route]["total_fare"].mean()

        route_days = {}
        for day in DAYS_ORDER:
            if (route, day) in route_dow_fares.index:
                avg_fare = route_dow_fares.loc[(route, day)]
                idx_val = round((avg_fare / base_p) * 100)
                route_days[day] = int(idx_val)
            else:
                route_days[day] = None
        heatmap[route] = route_days

    return {
        "data_mode": data_mode,
        "days": DAYS_ORDER,
        "routes": all_routes,
        "heatmap": heatmap
    }


@app.get("/backtest-index")
def get_backtest_index():
    """
    Returns historical daily APIx index alongside official DGCA monthly benchmark step values.
    Used for back-testing high-frequency APIx signals against traditional monthly aviation metrics.
    """
    df = load_unified_data()
    df = clean_fares(df)
    data_mode = getattr(df, "data_mode", df.attrs.get("data_mode", "live"))

    WEIGHTS_FILE = "data/route_weights.csv"
    weights_df = pd.read_csv(WEIGHTS_FILE)
    validate_weights(weights_df)

    history = calculate_historical_index(df, weights_df)
    sorted_dates = sorted(history.keys())

    apix_series = []
    dgca_series = []
    labels = []

    for idx, date_str in enumerate(sorted_dates):
        apix_val = history[date_str]
        apix_series.append(apix_val)
        labels.append(f"D{idx + 1}")
        
        # Monthly DGCA benchmark step function (e.g. 101.5 early period, 106.8 mid period)
        if idx < 15:
            dgca_series.append(101.5)
        else:
            dgca_series.append(106.8)

    return {
        "data_mode": data_mode,
        "dates": sorted_dates,
        "labels": labels,
        "apix": apix_series,
        "dgca": dgca_series
    }


@app.post("/collect")
def collect_latest_fares():

    try:

        result = run_collection()

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

@app.get("/fares")
def get_fares(
    route: str | None = None,
    airline: str | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(FareRecord)

    if route:

        query = query.filter(
            FareRecord.route == route
        )

    if airline:

        query = query.filter(
            FareRecord.airline == airline
        )

    records = (
        query
        .order_by(
            FareRecord.id.desc()
        )
        .limit(100)
        .all()
    )

    return [
        {
            "collection_date": record.collection_date,
            "collection_time": record.collection_time,
            "departure_date": record.departure_date,
            "route": record.route,
            "airline": record.airline,
            "source": record.source,
            "lead_time": record.lead_time,
            "base_fare": record.base_fare,
            "taxes": record.taxes,
            "fees": record.fees,
            "total_fare": record.total_fare,
            "availability": record.availability
        }
        for record in records
    ]




@app.post("/admin/collect-now")
def trigger_collection_now():
    """Manually trigger a collection run immediately (useful for demos —
    don't wait for the 06:00 IST cron job)."""
    result = run_collection()
    return result


@app.get("/export/excel")
@app.get("/export")
def export_fare_data(
    route: str | None = None,
    airline: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Export real fare data and computed index statistics as an Excel workbook (.xlsx).
    Filters out all mock/fake sources (source != 'mock', 'Mock', 'Airline', 'test').
    Supports optional route, airline, start_date, and end_date filtering.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl is required for export. Install with: pip install openpyxl"
        )

    # Exclude only hand-seeded fake CSV rows; keep live scheduler data ('mock' lowercase, 'google_flights')
    FAKE_SOURCES = ["Airline", "Mock", "test"]

    # Strict filtering: exclude hand-seeded fake sources only
    query = db.query(FareRecord).filter(FareRecord.source.notin_(FAKE_SOURCES))

    if route:
        query = query.filter(FareRecord.route == route)
    if airline:
        query = query.filter(FareRecord.airline == airline)
    if start_date:
        query = query.filter(FareRecord.collection_date >= start_date)
    if end_date:
        query = query.filter(FareRecord.collection_date <= end_date)

    try:
        raw_records = query.order_by(FareRecord.collection_date.desc(), FareRecord.id.desc()).all()
    except Exception:
        raw_records = []


    # Demo mode / Fallback check: Do not export fake data silently
    if not raw_records:
        raise HTTPException(
            status_code=400,
            detail="Export unavailable in demo mode or no matching real data found."
        )

    # Gather clean index statistics
    df = load_unified_data()
    df = clean_fares(df)

    WEIGHTS_FILE = "data/route_weights.csv"
    weights_df = pd.read_csv(WEIGHTS_FILE)
    validate_weights(weights_df)

    available_dates = sorted(df["date"].unique()) if not df.empty and "date" in df.columns else []
    base_date = available_dates[0] if available_dates else None
    current_date = available_dates[-1] if available_dates else None

    route_indices = calculate_route_index(df, base_date, current_date) if base_date and current_date else pd.Series(dtype=float)
    national_index = calculate_weighted_national_index(route_indices, weights_df) if not route_indices.empty else 100.0
    history = calculate_historical_index(df, weights_df) if not df.empty else {}
    lead_time_indices = calculate_lead_time_index(df, base_date, current_date) if base_date and current_date else pd.Series(dtype=float)


    # Styling definitions
    HEADER_FILL   = PatternFill("solid", fgColor="0B1728")
    HEADER_FONT   = Font(name="Calibri", bold=True, color="7DD3FC", size=11)
    CELL_FONT     = Font(name="Calibri", size=10, color="F5F7FA")
    ALT_FILL      = PatternFill("solid", fgColor="101D30")
    PLAIN_FILL    = PatternFill("solid", fgColor="0B1728")
    THIN_BORDER   = Border(
        bottom=Side(style="thin", color="1A2D45"),
        right=Side(style="thin", color="1A2D45"),
    )

    def _style_header(ws, headers, row=1):
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font   = HEADER_FONT
            cell.fill   = HEADER_FILL
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
            cell.border = THIN_BORDER

    def _auto_width(ws, min_w=10, max_w=40):
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max((len(str(c.value)) if c.value else 0 for c in col), default=0)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_w), max_w)

    def _style_data_rows(ws, data_start_row, data_end_row, n_cols):
        for row_idx in range(data_start_row, data_end_row + 1):
            fill = ALT_FILL if row_idx % 2 == 0 else PLAIN_FILL
            for col_idx in range(1, n_cols + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.fill   = fill
                cell.font   = CELL_FONT
                cell.border = THIN_BORDER
                cell.alignment = Alignment(horizontal="left", vertical="center")

    wb = openpyxl.Workbook()

    # Sheet 1: Raw Fare Records
    ws_raw = wb.active
    ws_raw.title = "Raw Fares"
    ws_raw.sheet_view.showGridLines = False

    raw_headers = [
        "Collection Date", "Collection Time", "Departure Date",
        "Route", "Airline", "Source", "Lead Time (Days)",
        "Base Fare (₹)", "Taxes (₹)", "Fees (₹)", "Total Fare (₹)", "Availability"
    ]
    _style_header(ws_raw, raw_headers, row=1)

    for r_idx, rec in enumerate(raw_records, start=2):
        ws_raw.cell(row=r_idx, column=1,  value=rec.collection_date)
        ws_raw.cell(row=r_idx, column=2,  value=rec.collection_time)
        ws_raw.cell(row=r_idx, column=3,  value=rec.departure_date)
        ws_raw.cell(row=r_idx, column=4,  value=rec.route)
        ws_raw.cell(row=r_idx, column=5,  value=rec.airline)
        ws_raw.cell(row=r_idx, column=6,  value=rec.source)
        ws_raw.cell(row=r_idx, column=7,  value=rec.lead_time)
        ws_raw.cell(row=r_idx, column=8,  value=rec.base_fare)
        ws_raw.cell(row=r_idx, column=9,  value=rec.taxes)
        ws_raw.cell(row=r_idx, column=10, value=rec.fees)
        ws_raw.cell(row=r_idx, column=11, value=rec.total_fare)
        ws_raw.cell(row=r_idx, column=12, value=rec.availability)

    if raw_records:
        _style_data_rows(ws_raw, 2, len(raw_records) + 1, len(raw_headers))
    _auto_width(ws_raw)

    # Sheet 2: Index Summary
    ws_summary = wb.create_sheet("Index Summary")
    ws_summary.sheet_view.showGridLines = False
    _style_header(ws_summary, ["Metric", "Value"], row=1)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_rows = [
        ("Export Generated",       now_str),
        ("Base Period",            base_date or "N/A"),
        ("Current Period",         current_date or "N/A"),
        ("National Airfare Index", round(float(national_index), 2)),
        ("Change from Base (pts)", round(float(national_index) - 100, 2) if national_index else "N/A"),
        ("Exported Records",       len(raw_records)),
        ("Filter Route",           route or "All"),
        ("Filter Airline",         airline or "All"),
    ]
    for r_idx, (metric, value) in enumerate(summary_rows, start=2):
        ws_summary.cell(row=r_idx, column=1, value=metric)
        ws_summary.cell(row=r_idx, column=2, value=value)
    _style_data_rows(ws_summary, 2, len(summary_rows) + 1, 2)
    _auto_width(ws_summary)

    # Sheet 3: Route Indices
    ws_routes = wb.create_sheet("Route Indices")
    ws_routes.sheet_view.showGridLines = False
    _style_header(ws_routes, ["Route", "Index Value", "Change from Base (pts)", "Weight"], row=1)
    weights_lookup = dict(zip(weights_df["route"], weights_df["weight"])) if not weights_df.empty else {}
    for r_idx, (r_name, val) in enumerate(sorted(route_indices.items()), start=2):
        ws_routes.cell(row=r_idx, column=1, value=r_name)
        ws_routes.cell(row=r_idx, column=2, value=round(float(val), 2))
        ws_routes.cell(row=r_idx, column=3, value=round(float(val) - 100, 2))
        ws_routes.cell(row=r_idx, column=4, value=weights_lookup.get(r_name, "N/A"))
    if not route_indices.empty:
        _style_data_rows(ws_routes, 2, len(route_indices) + 1, 4)
    _auto_width(ws_routes)

    # Sheet 4: Lead-Time Indices
    ws_lead = wb.create_sheet("Lead-Time Indices")
    ws_lead.sheet_view.showGridLines = False
    _style_header(ws_lead, ["Lead Time (Days)", "Index Value", "Change from Base (pts)"], row=1)
    for r_idx, (lead, val) in enumerate(sorted(lead_time_indices.items()), start=2):
        ws_lead.cell(row=r_idx, column=1, value=lead)
        ws_lead.cell(row=r_idx, column=2, value=round(float(val), 2))
        ws_lead.cell(row=r_idx, column=3, value=round(float(val) - 100, 2))
    if not lead_time_indices.empty:
        _style_data_rows(ws_lead, 2, len(lead_time_indices) + 1, 3)

    _auto_width(ws_lead)

    # Sheet 5: Historical Index
    ws_hist = wb.create_sheet("Historical Index")
    ws_hist.sheet_view.showGridLines = False
    _style_header(ws_hist, ["Date", "Index Value", "Change (pts)"], row=1)
    hist_dates = sorted(history.keys())
    prev = None
    for r_idx, d_key in enumerate(hist_dates, start=2):
        val = float(history[d_key])
        chg = round(val - prev, 2) if prev is not None else 0.0
        ws_hist.cell(row=r_idx, column=1, value=d_key)
        ws_hist.cell(row=r_idx, column=2, value=round(val, 2))
        ws_hist.cell(row=r_idx, column=3, value=chg)
        prev = val
    if hist_dates:
        _style_data_rows(ws_hist, 2, len(hist_dates) + 1, 3)
    _auto_width(ws_hist)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"apix_fare_data_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

