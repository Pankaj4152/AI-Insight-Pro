from fastapi import status
"""
Main API entry point for scanning operations
Exposes endpoints to scan data sources (cloud, file, etc.), retrieve findings, and generate reports.
"""

from fastapi import status
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import uuid

from scanning_engine.scanner import MultiConnectorScanner
from scanning_engine.baseline_manager import SimpleBaselineManager
from scanning_engine.storage_config import ScannerStorageManager

app = FastAPI(title="Data Scanner API")

scanner = MultiConnectorScanner()
baseline_manager = SimpleBaselineManager()
storage = ScannerStorageManager()

# In-memory store for scan results (for demo; replace with DB/storage in prod)
SCAN_RESULTS = {}

class ScanSourceConfig(BaseModel):
    name: str
    type: str  # 'file', 'cloud', etc.
    file_path: Optional[str] = None
    connection_string: Optional[str] = None
    perform_content_scan: Optional[bool] = True
    baseline_config: Optional[dict] = None
    # Add other fields as needed

@app.post("/scan", summary="Scan a data source (file/cloud)")
def scan_source(config: ScanSourceConfig):
    """
    Submit a scan job for a data source (file, cloud, etc.)
    """
    try:
        findings = scanner.scan_single_source(config.dict())
        scan_id = str(uuid.uuid4())
        SCAN_RESULTS[scan_id] = findings
        return {"scan_id": scan_id, "total_findings": len(findings), "findings": findings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.post("/scan/upload", summary="Scan an uploaded file")
def scan_uploaded_file(file: UploadFile = File(...), perform_content_scan: bool = True):
    """
    Upload a file and scan it for SDEs
    """
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        config = {
            "name": file.filename,
            "type": "file",
            "file_path": tmp_path,
            "perform_content_scan": perform_content_scan
        }
        findings = scanner.scan_single_source(config)
        scan_id = str(uuid.uuid4())
        SCAN_RESULTS[scan_id] = findings
        os.unlink(tmp_path)
        return {"scan_id": scan_id, "total_findings": len(findings), "findings": findings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File scan failed: {str(e)}")

@app.get("/findings/{scan_id}", summary="Get findings for a scan")
def get_findings(scan_id: str):
    findings = SCAN_RESULTS.get(scan_id)
    if findings is None:
        raise HTTPException(status_code=404, detail="Scan ID not found")
    return {"scan_id": scan_id, "findings": findings}

@app.get("/report/{scan_id}", summary="Download scan report as JSON")
def download_report(scan_id: str):
    findings = SCAN_RESULTS.get(scan_id)
    if findings is None:
        raise HTTPException(status_code=404, detail="Scan ID not found")
    # Save to temp file
    tmp_path = os.path.join(tempfile.gettempdir(), f"scan_report_{scan_id}.json")
    with open(tmp_path, "w", encoding="utf-8") as f:
        import json
        json.dump({"scan_id": scan_id, "findings": findings}, f, indent=2)
    return FileResponse(tmp_path, filename=f"scan_report_{scan_id}.json", media_type="application/json")
@app.get("/scans", summary="List all scan jobs")
def list_scans():
    """
    List all scan jobs with their IDs and total findings.
    """
    return [
        {"scan_id": scan_id, "total_findings": len(findings)}
        for scan_id, findings in SCAN_RESULTS.items()
    ]

@app.delete("/scan/{scan_id}", summary="Delete a scan job and its report", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(scan_id: str):
    """
    Delete a scan job and its report from memory (and temp file if exists).
    """
    if scan_id in SCAN_RESULTS:
        del SCAN_RESULTS[scan_id]
        tmp_path = os.path.join(tempfile.gettempdir(), f"scan_report_{scan_id}.json")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return
    raise HTTPException(status_code=404, detail="Scan ID not found")

@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}