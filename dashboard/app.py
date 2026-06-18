import logging
import asyncio
from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database.db import Database
from pipeline import run_pipeline
from config import Config

logger = logging.getLogger(__name__)

app = FastAPI(title="Sıcak Fırsatlar Takip Kontrol Paneli")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")

# Simple state tracking for background scans
class ScanState:
    is_running = False

@app.on_event("startup")
async def startup_event():
    """Ensure database tables are initialized on start."""
    await Database.initialize()
    logger.info("FastAPI App initialized and DB connected.")

async def background_scan_task():
    """Background task to run the scraping and validation pipeline."""
    if ScanState.is_running:
        return
    try:
        ScanState.is_running = True
        await run_pipeline()
    except Exception as e:
        logger.error(f"Error during manual background scan: {e}")
    finally:
        ScanState.is_running = False

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Retrieve verified deals
    deals = await Database.get_deals(limit=50, only_verified=True)
    
    # Retrieve all keywords
    keywords = await Database.get_all_keywords()
    
    # Check config warnings
    warnings = Config.validate()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "deals": deals,
            "keywords": keywords,
            "scan_running": ScanState.is_running,
            "warnings": warnings,
            "config": Config
        }
    )

@app.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Triggers an asynchronous scan run."""
    if ScanState.is_running:
        return JSONResponse({"status": "error", "message": "Tarama zaten çalışıyor."})
    
    background_tasks.add_task(background_scan_task)
    return JSONResponse({"status": "success", "message": "Tarama arka planda başlatıldı."})

@app.get("/scan-status")
async def get_scan_status():
    """Returns the current state of the crawler."""
    return JSONResponse({"running": ScanState.is_running})

@app.post("/keywords/add")
async def add_keyword(keyword: str = Form(...)):
    """Adds a tracking keyword to the system."""
    if keyword.strip():
        await Database.add_keyword(keyword)
    return RedirectResponse(url="/", status_code=303)

@app.post("/keywords/{keyword_id}/toggle")
async def toggle_keyword(keyword_id: int, active: int = Form(...)):
    """Toggles keyword active/inactive status."""
    await Database.toggle_keyword_status(keyword_id, active == 1)
    return RedirectResponse(url="/", status_code=303)

@app.post("/keywords/{keyword_id}/delete")
async def delete_keyword(keyword_id: int):
    """Deletes a keyword."""
    await Database.delete_keyword(keyword_id)
    return RedirectResponse(url="/", status_code=303)
