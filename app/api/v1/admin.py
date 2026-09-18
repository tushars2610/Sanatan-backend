import os
import sys
import subprocess
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Header, HTTPException, Depends
from app.core.config import get_settings

router = APIRouter(prefix="/admin", tags=["Admin"])

def verify_admin(x_admin_token: str = Header(...)):
    settings = get_settings()
    if not settings.ADMIN_SECRET_TOKEN or x_admin_token != settings.ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing admin token")

def run_script(script_name: str):
    print(f"Starting background script: {script_name}")
    try:
        # Use sys.executable to run the script in the same python environment as FastAPI
        result = subprocess.run(
            [sys.executable, script_name], 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"[{script_name}] finished successfully.\nOutput: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[{script_name}] failed with error code {e.returncode}.\nOutput: {e.stdout}\nError: {e.stderr}")

@router.post("/upload-data")
async def upload_data(
    background_tasks: BackgroundTasks,
    raw_verses: UploadFile = File(...),
    tagged_verses: UploadFile = File(...),
    _: None = Depends(verify_admin)
):
    """
    Uploads raw and categorized JSON data and triggers the PostgreSQL insertion script in the background.
    """
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/categorized", exist_ok=True)
    
    with open("data/raw/all_verses.json", "wb") as f:
        f.write(await raw_verses.read())
        
    with open("data/categorized/all_tagged_verses.json", "wb") as f:
        f.write(await tagged_verses.read())
        
    background_tasks.add_task(run_script, "load_to_postgress.py")
    return {"message": "Files saved successfully. Database insertion started in the background."}

@router.post("/sync-milvus")
async def sync_milvus(
    background_tasks: BackgroundTasks, 
    _: None = Depends(verify_admin)
):
    """
    Triggers the Milvus embedding and indexing script in the background.
    """
    background_tasks.add_task(run_script, "index_to_milvus.py")
    return {"message": "Milvus embedding and sync started in the background."}
