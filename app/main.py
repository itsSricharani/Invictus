from sqlalchemy.orm import Session
from fastapi import Depends
from scraper.collector import run_collection
from pipeline.cleaner import clean_fares
import io

from app.database import get_db
from app.models import FareRecord

from datetime import datetime
from fastapi.responses import HTMLResponse

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
    df = clean_fares(df)
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
    df = clean_fares(df)

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
    df = clean_fares(df)

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
    df = clean_fares(df)

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
    df = clean_fares(df)

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


@app.get("/export")
def export_data(db: Session = Depends(get_db)):
    """
    Export all fare data and computed index statistics as a multi-sheet Excel workbook.
    Sheets: Raw Fares · Index Summary · Route Indices · Lead-Time Indices · Historical Index
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

    # ---- Gather data ----
    df = load_unified_data()
    weights_df = pd.read_csv(WEIGHTS_FILE)
    validate_weights(weights_df)

    available_dates = sorted(df["date"].unique())
    base_date = available_dates[0]
    current_date = available_dates[-1]

    route_indices = calculate_route_index(df, base_date, current_date)
    national_index = calculate_weighted_national_index(route_indices, weights_df)
    history = calculate_historical_index(df, weights_df)
    lead_time_indices = calculate_lead_time_index(df, base_date, current_date)

    # ---- Raw fare records from DB ----
    raw_records = db.query(FareRecord).order_by(FareRecord.id.desc()).all()

    # ---- Styling helpers ----
    HEADER_FILL   = PatternFill("solid", fgColor="0B1728")
    HEADER_FONT   = Font(name="Calibri", bold=True, color="7DD3FC", size=11)
    CELL_FONT     = Font(name="Calibri", size=10, color="F5F7FA")
    ALT_FILL      = PatternFill("solid", fgColor="101D30")
    PLAIN_FILL    = PatternFill("solid", fgColor="0B1728")
    THIN_BORDER   = Border(
        bottom=Side(style="thin", color="1A2D45"),
        right=Side(style="thin", color="1A2D45"),
    )
    ACCENT_FONT   = Font(name="Calibri", bold=True, color="38BDF8", size=12)

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

    # ============================================================
    # Sheet 1: Index Summary
    # ============================================================
    ws_summary = wb.active
    ws_summary.title = "Index Summary"
    ws_summary.sheet_view.showGridLines = False
    ws_summary.freeze_panes = "A2"

    _style_header(ws_summary, ["Metric", "Value"], row=1)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sched = get_scheduler_status()
    summary_rows = [
        ("Export Generated",       now_str),
        ("Base Period",            base_date),
        ("Current Period",         current_date),
        ("National Airfare Index", round(float(national_index), 2)),
        ("Change from Base (pts)", round(float(national_index) - 100, 2)),
        ("Total Records",          len(df)),
        ("Routes Monitored",       df["route"].nunique()),
        ("Airlines Monitored",     df["airline"].nunique()),
        ("Data Sources",           df["source"].nunique()),
        ("Scheduler Status",       sched.get("status", "N/A")),
        ("Next Collection",        sched.get("next_run", "N/A")),
    ]
    for r_idx, (metric, value) in enumerate(summary_rows, start=2):
        ws_summary.cell(row=r_idx, column=1, value=metric)
        ws_summary.cell(row=r_idx, column=2, value=value)
    _style_data_rows(ws_summary, 2, len(summary_rows) + 1, 2)
    _auto_width(ws_summary)

    # ============================================================
    # Sheet 2: Route Indices
    # ============================================================
    ws_routes = wb.create_sheet("Route Indices")
    ws_routes.sheet_view.showGridLines = False
    _style_header(ws_routes, ["Route", "Index Value", "Change from Base (pts)", "Weight"], row=1)
    weights_lookup = dict(zip(weights_df["route"], weights_df["weight"]))
    for r_idx, (route, val) in enumerate(sorted(route_indices.items()), start=2):
        ws_routes.cell(row=r_idx, column=1, value=route)
        ws_routes.cell(row=r_idx, column=2, value=round(float(val), 2))
        ws_routes.cell(row=r_idx, column=3, value=round(float(val) - 100, 2))
        ws_routes.cell(row=r_idx, column=4, value=weights_lookup.get(route, "N/A"))
    _style_data_rows(ws_routes, 2, len(route_indices) + 1, 4)
    _auto_width(ws_routes)

    # ============================================================
    # Sheet 3: Lead-Time Indices
    # ============================================================
    ws_lead = wb.create_sheet("Lead-Time Indices")
    ws_lead.sheet_view.showGridLines = False
    _style_header(ws_lead, ["Lead Time (Days)", "Index Value", "Change from Base (pts)"], row=1)
    for r_idx, (lead, val) in enumerate(sorted(lead_time_indices.items()), start=2):
        ws_lead.cell(row=r_idx, column=1, value=lead)
        ws_lead.cell(row=r_idx, column=2, value=round(float(val), 2))
        ws_lead.cell(row=r_idx, column=3, value=round(float(val) - 100, 2))
    _style_data_rows(ws_lead, 2, len(lead_time_indices) + 1, 3)
    _auto_width(ws_lead)

    # ============================================================
    # Sheet 4: Historical Index
    # ============================================================
    ws_hist = wb.create_sheet("Historical Index")
    ws_hist.sheet_view.showGridLines = False
    _style_header(ws_hist, ["Date", "Index Value", "Change (pts)"], row=1)
    hist_dates = sorted(history.keys())
    prev = None
    for r_idx, date in enumerate(hist_dates, start=2):
        val = float(history[date])
        chg = round(val - prev, 2) if prev is not None else 0.0
        ws_hist.cell(row=r_idx, column=1, value=date)
        ws_hist.cell(row=r_idx, column=2, value=round(val, 2))
        ws_hist.cell(row=r_idx, column=3, value=chg)
        prev = val
    _style_data_rows(ws_hist, 2, len(hist_dates) + 1, 3)
    _auto_width(ws_hist)

    # ============================================================
    # Sheet 5: Raw Fare Records
    # ============================================================
    ws_raw = wb.create_sheet("Raw Fares")
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

    # ---- Stream the workbook ----
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"aeir_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
