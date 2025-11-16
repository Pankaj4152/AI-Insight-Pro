"""
Driver function to orchestrate Discovery, SDE, Scanning, and Detection agents
Exposed as a FastAPI endpoint with retry logic for failed steps
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import agent classes
from modular_discovery_agent import ModularDiscoveryAgent
from modular_scanning_agent import ModularScanningAgent
from modular_detection_agent import ModularDetectionAgent

# Optional import for compliance calculator
try:
    from compliance_calculator import ComplianceCalculator
    COMPLIANCE_AVAILABLE = True
except ImportError:
    ComplianceCalculator = None
    COMPLIANCE_AVAILABLE = False
    logger.info("ComplianceCalculator not available - compliance endpoints will be disabled")

# Load environment variables
load_dotenv()

# Hardcode the database connection string
DB_URL = "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"
os.environ["DB_URL"] = DB_URL

# FastAPI app
app = FastAPI(title="Data Protection Pipeline API")

# CORS middleware configuration

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request validation
class ClientRequest(BaseModel):
    client_id: str

# Pydantic model for specific database scan request
class SpecificDatabaseScanRequest(BaseModel):
    client_id: str
    store_name: str  # Now only requires store_name (actual resource name)
    tables: List[str] = None

# Pydantic model for SDE selection request
class SDESelectionRequest(BaseModel):
    client_id: str
    pattern_names: List[str]  # List of SDE pattern names to select
    
class SDESelectionItem(BaseModel):
    pattern_name: str
    sensitivity: str
    protection_method: str

class SDESelectionsResponse(BaseModel):
    client_id: str
    selected_sdes: List[SDESelectionItem]

# Pydantic models for file selection
class FileSelectionItem(BaseModel):
    file_name: str
    store_id: int
    path: Optional[str] = None
    object_id: Optional[int] = None
    object_type: str = "file"
    metadata: Optional[str] = None

class FileSelectionRequest(BaseModel):
    client_id: str
    scan_session_id: Optional[str] = None  # Optional session ID, will be generated if not provided
    selected_files: List[FileSelectionItem]  # List of file details

# Pydantic model for response
class DriverResponse(BaseModel):
    status: str
    message: str
    discovery_results: Dict[str, Any]
    scan_results: Dict[str, Any]
    detection_results: List[Dict[str, Any]]
    execution_timestamp: str
    errors: List[str]

def driver(client_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Orchestrates the execution of Discovery, Scanning, and Detection agents for a given client_id.
    Retries from the failed step if an agent fails.

    Args:
        client_id: Client ID for multi-tenant operations
        max_retries: Maximum number of retries for each agent

    Returns:
        Dictionary containing results from all agents and execution status
    """
    logger.info(f"Starting driver for client_id: {client_id}")
    result = {
        'status': 'pending',
        'message': 'Pipeline execution started',
        'discovery_results': {},
        'scan_results': {},
        'detection_results': [],
        'execution_timestamp': datetime.now().isoformat(),
        'errors': []
    }

    # Initialize agents
    try:
        discovery_agent = ModularDiscoveryAgent(client_id=client_id)
        scanning_agent = ModularScanningAgent(client_id=client_id)
        detection_agent = ModularDetectionAgent(client_id=client_id)
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        result['status'] = 'failed'
        result['message'] = f"Agent initialization failed: {e}"
        result['errors'].append(str(e))
        return result

    # Step 1: Run Discovery Agent
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} - Running Discovery Agent")
            discovery_results = discovery_agent.discover_all_sources()
            if discovery_results.get('status') == 'completed':
                result['discovery_results'] = discovery_results
                logger.info("Discovery Agent completed successfully")
                break
            else:
                logger.warning(f"Discovery Agent attempt {attempt} failed: {discovery_results}")
                result['errors'].append(f"Discovery Agent attempt {attempt} failed")
        except Exception as e:
            logger.error(f"Discovery Agent attempt {attempt} failed with error: {e}")
            result['errors'].append(f"Discovery Agent attempt {attempt} failed: {e}")
        if attempt == max_retries:
            result['status'] = 'failed'
            result['message'] = "Discovery Agent failed after maximum retries"
            return result

    # Step 2: Run Scanning Agent
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} - Running Scanning Agent")
            scan_results = scanning_agent.scan_all_databases()  # Updated method name
            if scan_results.get('total_findings', 0) >= 0:  # Assuming non-negative findings indicate success
                result['scan_results'] = scan_results
                logger.info("Scanning Agent completed successfully")
                break
            else:
                logger.warning(f"Scanning Agent attempt {attempt} failed: {scan_results}")
                result['errors'].append(f"Scanning Agent attempt {attempt} failed")
        except Exception as e:
            logger.error(f"Scanning Agent attempt {attempt} failed with error: {e}")
            result['errors'].append(f"Scanning Agent attempt {attempt} failed: {e}")
            if attempt == max_retries:
                result['status'] = 'failed'
                result['message'] = "Scanning Agent failed after maximum retries"
                return result

    # Step 3: Run Detection Agent
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} - Running Detection Agent")
            detection_results = detection_agent.analyze_all_scans_for_client(client_id)
            result['detection_results'] = detection_results
            logger.info("Detection Agent completed successfully")
            break
        except Exception as e:
            logger.error(f"Detection Agent attempt {attempt} failed with error: {e}")
            result['errors'].append(f"Detection Agent attempt {attempt} failed: {e}")
            if attempt == max_retries:
                result['status'] = 'failed'
                result['message'] = "Detection Agent failed after maximum retries"
                return result

    result['status'] = 'success'
    result['message'] = "Pipeline execution completed successfully"
    logger.info("Driver pipeline completed successfully")
    return result

# Discovery endpoint
@app.post("/discover")
async def discover_sources(request: ClientRequest):
    """
    Run discovery agent to find and register data sources for a client.
    This should be run first before scanning.
    """
    try:
        logger.info(f"Starting discovery for client_id: {request.client_id}")
        discovery_agent = ModularDiscoveryAgent(client_id=request.client_id)
        result = discovery_agent.discover_all_sources()
        return {
            "status": "success",
            "client_id": request.client_id,
            "action": "discovery",
            "results": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@app.post("/discover-all-missing")
async def discover_all_missing_clients():
    """
    Run discovery for all clients that have connections but no data_stores entries.
    This fixes the sync issue between client_connections and data_stores.
    """
    try:
        import psycopg2
        
        logger.info("Starting bulk discovery for all missing clients...")
        
        # Get clients with connections but no data_stores
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT DISTINCT cc.client_id, COUNT(cc.cli_conn_id) as connection_count
                    FROM client_connections cc
                    LEFT JOIN data_stores ds ON cc.client_id = ds.client_id
                    WHERE ds.client_id IS NULL
                    GROUP BY cc.client_id
                    ORDER BY cc.client_id
                ''')
                missing_clients = cursor.fetchall()
        
        if not missing_clients:
            return {
                "status": "success",
                "message": "No missing clients found - all clients are already discovered",
                "clients_processed": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Found {len(missing_clients)} clients missing from data_stores")
        
        results = {
            "status": "success",
            "message": f"Bulk discovery completed for {len(missing_clients)} clients",
            "clients_processed": 0,
            "successful_discoveries": 0,
            "failed_discoveries": 0,
            "discovery_results": {},
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Run discovery for each missing client
        for client_id, connection_count in missing_clients:
            try:
                logger.info(f"Running discovery for client: {client_id} ({connection_count} connections)")
                
                discovery_agent = ModularDiscoveryAgent(client_id=client_id)
                client_result = discovery_agent.discover_all_sources()
                
                results["discovery_results"][client_id] = {
                    "status": "success",
                    "sources_discovered": len(client_result.get("sources_discovered", [])),
                    "connection_count": connection_count,
                    "details": client_result
                }
                results["successful_discoveries"] += 1
                logger.info(f"✅ Discovery successful for {client_id}: {len(client_result.get('sources_discovered', []))} sources")
                
            except Exception as e:
                error_msg = f"Discovery failed for client {client_id}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["discovery_results"][client_id] = {
                    "status": "failed",
                    "error": str(e),
                    "connection_count": connection_count
                }
                results["failed_discoveries"] += 1
            
            results["clients_processed"] += 1
        
        logger.info(f"✅ Bulk discovery completed: {results['successful_discoveries']} successful, {results['failed_discoveries']} failed")
        return results
        
    except Exception as e:
        logger.error(f"Bulk discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk discovery failed: {str(e)}")

# New scanning endpoints for testing
@app.post("/scan-latest")
async def scan_latest_database(request: ClientRequest):
    """
    Scan only the latest database for a client.
    Prioritizes scanning files from the MOST RECENT selection session only,
    otherwise falls back to scanning all discovered files.
    This ensures only current selections are scanned, not accumulated selections.
    """
    try:
        logger.info(f"Starting latest database scan for client_id: {request.client_id}")
        
        # Import database manager to check for selected objects
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        scanning_agent = ModularScanningAgent(client_id=request.client_id)
        db_manager = PostgreSQLCloudScanDBManager()
        
        # Get the latest scan session ID to ensure we only scan current selections
        latest_session_id = db_manager.get_latest_scan_session_id(request.client_id)
        
        if latest_session_id:
            logger.info(f"Found latest scan session: {latest_session_id} for client {request.client_id}")
            
            # Check if there are selected objects in the latest session
            has_selections = db_manager.has_selected_objects(request.client_id, latest_session_id)
            
            if has_selections:
                logger.info(f"Found selected objects in latest session {latest_session_id}, performing selective scan")
                # Use selective scanning for latest session only
                result = scanning_agent.scan_selected_objects(scan_session_id=latest_session_id)
                scan_type = "latest_database_selective"
            else:
                logger.info(f"No selected objects found in latest session {latest_session_id}, falling back to full latest database scan")
                # Fall back to full latest database scan
                result = scanning_agent.scan_latest_database(client_id=request.client_id)
                scan_type = "latest_database_full"
        else:
            logger.info(f"No scan sessions found for client {request.client_id}, falling back to full latest database scan")
            # Fall back to full latest database scan
            result = scanning_agent.scan_latest_database(client_id=request.client_id)
            scan_type = "latest_database_full"
            has_selections = False
        
        # Automatically trigger detection agent after scanning
        detection_results = []
        if result and 'scan_results' in result:
            logger.info(f"Scanning completed. Triggering detection agent for confidence score calculation...")
            try:
                detection_agent = ModularDetectionAgent(client_id=request.client_id)
                
                # Analyze findings for each scan that was performed
                for scan_result in result['scan_results']:
                    scan_id = scan_result.get('scan_id')
                    if scan_id:
                        logger.info(f"Running detection analysis for scan ID: {scan_id}")
                        analysis_results = detection_agent.analyze_scan_findings(scan_id)
                        detection_results.append({
                            'scan_id': scan_id,
                            'total_findings': analysis_results.get('total_findings', 0),
                            'confidence_updates': analysis_results.get('confidence_updates', 0),
                            'analysis_summary': analysis_results.get('analysis_results', {})
                        })
                        logger.info(f"Detection analysis completed for scan ID: {scan_id}")
                
                logger.info(f"Detection agent completed for {len(detection_results)} scans")
            except Exception as e:
                logger.error(f"Detection agent failed: {e}")
                detection_results = [{"error": f"Detection analysis failed: {str(e)}"}]
        
        return {
            "status": "success",
            "client_id": request.client_id,
            "scan_type": scan_type,
            "selective_scan_used": has_selections,
            "latest_session_id": latest_session_id,
            "results": result,
            "detection_results": detection_results,
            "confidence_scoring": "automatic" if detection_results else "skipped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Latest database scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Latest database scan failed: {str(e)}")

@app.post("/scan-all")
async def scan_all_databases(request: ClientRequest):
    """
    Scan all databases for a client.
    Ignores selected_objects table and performs a full scan of all databases and files.
    """
    try:
        logger.info(f"Starting all databases scan for client_id: {request.client_id}")
        logger.info("Performing full scan - ignoring any selected objects")
        
        scanning_agent = ModularScanningAgent(client_id=request.client_id)
        
        # Force full scan regardless of selected objects
        result = scanning_agent.scan_all_databases(client_id=request.client_id)
        
        # Automatically trigger detection agent after scanning
        detection_results = []
        if result and 'scan_results' in result:
            logger.info(f"All databases scanning completed. Triggering detection agent for confidence score calculation...")
            try:
                detection_agent = ModularDetectionAgent(client_id=request.client_id)
                
                # Analyze findings for each scan that was performed
                for scan_result in result['scan_results']:
                    scan_id = scan_result.get('scan_id')
                    if scan_id:
                        logger.info(f"Running detection analysis for scan ID: {scan_id}")
                        analysis_results = detection_agent.analyze_scan_findings(scan_id)
                        detection_results.append({
                            'scan_id': scan_id,
                            'total_findings': analysis_results.get('total_findings', 0),
                            'confidence_updates': analysis_results.get('confidence_updates', 0),
                            'analysis_summary': analysis_results.get('analysis_results', {})
                        })
                        logger.info(f"Detection analysis completed for scan ID: {scan_id}")
                
                logger.info(f"Detection agent completed for {len(detection_results)} scans")
            except Exception as e:
                logger.error(f"Detection agent failed: {e}")
                detection_results = [{"error": f"Detection analysis failed: {str(e)}"}]
        
        return {
            "status": "success",
            "client_id": request.client_id,
            "scan_type": "all_databases_full",
            "selective_scan_used": False,
            "message": "Full scan completed with automatic confidence scoring",
            "results": result,
            "detection_results": detection_results,
            "confidence_scoring": "automatic" if detection_results else "skipped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"All databases scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"All databases scan failed: {str(e)}")

@app.post("/scan-specific")
async def scan_specific_database(request: SpecificDatabaseScanRequest):
    """
    Scan a specific database and optionally specific tables within it.
    
    Args:
        request: SpecificDatabaseScanRequest object containing:
            - client_id: Client ID
            - store_name: Name of the specific resource to scan (bucket, dataset, database)
            - tables: List of specific table names to scan (optional)
    
    Returns:
        Scan results for the specific database and tables
    """
    try:
        # Validate that store_name is provided
        if not request.store_name:
            raise HTTPException(
                status_code=400, 
                detail="store_name must be provided"
            )
        
        logger.info(f"Starting specific database scan for client_id: {request.client_id}")
        logger.info(f"Target store_name: {request.store_name}")
        if request.tables:
            logger.info(f"Tables: {request.tables}")
        
        scanning_agent = ModularScanningAgent(client_id=request.client_id)
        result = scanning_agent.scan_specific_database(
            client_id=request.client_id,
            store_name=request.store_name,
            tables=request.tables
        )
        
        # Automatically trigger detection agent after scanning
        detection_results = []
        if result and 'scan_results' in result:
            logger.info(f"Specific database scanning completed. Triggering detection agent for confidence score calculation...")
            try:
                detection_agent = ModularDetectionAgent(client_id=request.client_id)
                
                # Analyze findings for each scan that was performed
                for scan_result in result['scan_results']:
                    scan_id = scan_result.get('scan_id')
                    if scan_id:
                        logger.info(f"Running detection analysis for scan ID: {scan_id}")
                        analysis_results = detection_agent.analyze_scan_findings(scan_id)
                        detection_results.append({
                            'scan_id': scan_id,
                            'total_findings': analysis_results.get('total_findings', 0),
                            'confidence_updates': analysis_results.get('confidence_updates', 0),
                            'analysis_summary': analysis_results.get('analysis_results', {})
                        })
                        logger.info(f"Detection analysis completed for scan ID: {scan_id}")
                
                logger.info(f"Detection agent completed for {len(detection_results)} scans")
            except Exception as e:
                logger.error(f"Detection agent failed: {e}")
                detection_results = [{"error": f"Detection analysis failed: {str(e)}"}]
        
        return {
            "status": "success",
            "client_id": request.client_id,
            "scan_type": "specific_database",
            "target_store_name": request.store_name,
            "target_tables": request.tables,
            "results": result,
            "detection_results": detection_results,
            "confidence_scoring": "automatic" if detection_results else "skipped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Specific database scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Specific database scan failed: {str(e)}")

@app.post("/scan-selected-only")
async def scan_selected_objects_only(request: ClientRequest):
    """
    Scan only the objects explicitly selected in the selected_objects table.
    Fails if no objects are selected.
    """
    try:
        logger.info(f"Starting selective scan for client_id: {request.client_id}")
        
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        scanning_agent = ModularScanningAgent(client_id=request.client_id)
        db_manager = PostgreSQLCloudScanDBManager()
        
        # Check if there are selected objects
        has_selections = db_manager.has_selected_objects(request.client_id)
        
        if not has_selections:
            raise HTTPException(
                status_code=400, 
                detail=f"No objects selected for scanning for client {request.client_id}. Use /scan-all for full scan or select objects first."
            )
        
        # Get count of selected objects for reporting
        selected_objects = db_manager.get_selected_objects(request.client_id)
        selected_count = len(selected_objects)
        
        logger.info(f"Scanning {selected_count} selected objects for client {request.client_id}")
        
        # Perform selective scan
        result = scanning_agent.scan_selected_objects()
        
        # Automatically trigger detection agent after scanning
        detection_results = []
        if result and 'scan_results' in result:
            logger.info(f"Selected objects scanning completed. Triggering detection agent for confidence score calculation...")
            try:
                detection_agent = ModularDetectionAgent(client_id=request.client_id)
                
                # Analyze findings for each scan that was performed
                for scan_result in result['scan_results']:
                    scan_id = scan_result.get('scan_id')
                    if scan_id:
                        logger.info(f"Running detection analysis for scan ID: {scan_id}")
                        analysis_results = detection_agent.analyze_scan_findings(scan_id)
                        detection_results.append({
                            'scan_id': scan_id,
                            'total_findings': analysis_results.get('total_findings', 0),
                            'confidence_updates': analysis_results.get('confidence_updates', 0),
                            'analysis_summary': analysis_results.get('analysis_results', {})
                        })
                        logger.info(f"Detection analysis completed for scan ID: {scan_id}")
                
                logger.info(f"Detection agent completed for {len(detection_results)} scans")
            except Exception as e:
                logger.error(f"Detection agent failed: {e}")
                detection_results = [{"error": f"Detection analysis failed: {str(e)}"}]
        
        return {
            "status": "success",
            "client_id": request.client_id,
            "scan_type": "selected_objects_only",
            "selective_scan_used": True,
            "selected_objects_count": selected_count,
            "message": f"Selective scan completed for {selected_count} selected objects with automatic confidence scoring",
            "results": result,
            "detection_results": detection_results,
            "confidence_scoring": "automatic" if detection_results else "skipped",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selective scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Selective scan failed: {str(e)}")

@app.post("/save-selection")
async def save_file_selection(request: FileSelectionRequest):
    """
    Save selected files to the selected_objects table for scanning.
    
    Args:
        request: File selection request containing client_id, selected files, and optional session_id
    
    Returns:
        Success/failure status with details about saved files
    """
    try:
        logger.info(f"Saving file selection for client_id: {request.client_id}")
        
        # Generate unique session ID if not provided to prevent accumulation
        # This ensures each new selection creates a new session by default
        scan_session_id = request.scan_session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(datetime.now().timestamp() * 1000) % 10000}"
        
        # Validate that we have files to save
        if not request.selected_files:
            return {
                "status": "error",
                "message": "No files provided for selection",
                "saved_count": 0,
                "errors": ["selected_files list is empty"]
            }
        
        # Initialize database manager
        from config_manager import AgentConfigManager
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        config_manager = AgentConfigManager()
        db_manager = PostgreSQLCloudScanDBManager(config_manager, client_id=request.client_id)
        
        # Save the file selections
        # Convert Pydantic models to dictionaries for database manager
        selected_files_dicts = [file_item.dict() for file_item in request.selected_files]
        
        result = db_manager.save_file_selections(
            client_id=request.client_id,
            scan_session_id=scan_session_id,
            selected_files=selected_files_dicts
        )
        
        if result['success']:
            logger.info(f"Successfully saved {result['saved_count']} file selections for client {request.client_id}")
            return {
                "status": "success",
                "client_id": request.client_id,
                "scan_session_id": scan_session_id,
                "message": result['message'],
                "saved_count": result['saved_count'],
                "duplicate_count": result.get('duplicate_count', 0),
                "error_count": result.get('error_count', 0),
                "errors": result.get('errors', []),
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"Failed to save file selections: {result['message']}")
            return {
                "status": "error",
                "client_id": request.client_id,
                "scan_session_id": scan_session_id,
                "message": result['message'],
                "saved_count": result.get('saved_count', 0),
                "error_count": result.get('error_count', 0),
                "errors": result.get('errors', []),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Save file selection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Save file selection failed: {str(e)}")

@app.post("/clear-selections")
async def clear_all_selections(request: ClientRequest):
    """
    Clear all selected objects for a client across all sessions.
    This can be used to reset the selection state when accumulation issues occur.
    
    Args:
        request: Client request containing client_id
    
    Returns:
        Success/failure status
    """
    try:
        logger.info(f"Clearing all selections for client_id: {request.client_id}")
        
        # Initialize database manager
        from config_manager import AgentConfigManager
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        config_manager = AgentConfigManager()
        db_manager = PostgreSQLCloudScanDBManager(config_manager, client_id=request.client_id)
        
        # Clear all selections
        success = db_manager.clear_all_selected_objects(request.client_id)
        
        if success:
            logger.info(f"Successfully cleared all selections for client {request.client_id}")
            return {
                "status": "success",
                "client_id": request.client_id,
                "message": "All file selections cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"Failed to clear selections for client {request.client_id}")
            raise HTTPException(status_code=500, detail="Failed to clear file selections")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear selections failed: {e}")
        raise HTTPException(status_code=500, detail=f"Clear selections failed: {str(e)}")

@app.get("/get-selections/{client_id}")
async def get_file_selections(client_id: str, scan_session_id: str = None):
    """
    Get currently selected files for a client.
    
    Args:
        client_id: Client ID
        scan_session_id: Optional session ID (if None, gets all selections for client)
    
    Returns:
        List of currently selected files
    """
    try:
        logger.info(f"Getting file selections for client_id: {client_id}")
        
        # Initialize database manager
        from config_manager import AgentConfigManager
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        config_manager = AgentConfigManager()
        db_manager = PostgreSQLCloudScanDBManager(config_manager, client_id=client_id)
        
        # Get selected objects
        selected_objects = db_manager.get_selected_objects(client_id, scan_session_id)
        
        return {
            "status": "success",
            "client_id": client_id,
            "scan_session_id": scan_session_id,
            "selected_files_count": len(selected_objects),
            "selected_files": selected_objects,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get file selections failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get file selections failed: {str(e)}")

@app.delete("/clear-selections/{client_id}")
async def clear_file_selections(client_id: str, scan_session_id: str = None):
    """
    Clear selected files for a client.
    
    Args:
        client_id: Client ID
        scan_session_id: Optional session ID (if None, clears all selections for client)
    
    Returns:
        Success/failure status
    """
    try:
        logger.info(f"Clearing file selections for client_id: {client_id}")
        
        # Initialize database manager
        from config_manager import AgentConfigManager
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        config_manager = AgentConfigManager()
        db_manager = PostgreSQLCloudScanDBManager(config_manager, client_id=client_id)
        
        # Clear selected objects
        success = db_manager.clear_selected_objects(client_id, scan_session_id)
        
        if success:
            return {
                "status": "success",
                "client_id": client_id,
                "scan_session_id": scan_session_id,
                "message": "File selections cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "client_id": client_id,
                "scan_session_id": scan_session_id,
                "message": "Failed to clear file selections",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Clear file selections failed: {e}")
        raise HTTPException(status_code=500, detail=f"Clear file selections failed: {str(e)}")

@app.get("/list-databases/{client_id}")
async def list_available_databases(client_id: str):
    """
    List all available databases for a client.
    
    Args:
        client_id: Client ID
    
    Returns:
        List of available databases with their details
    """
    try:
        logger.info(f"Listing available databases for client_id: {client_id}")
        
        scanning_agent = ModularScanningAgent(client_id=client_id)
        data_sources = scanning_agent.config_manager.get_discovered_data_sources_for_client(client_id)
        
        databases = []
        for source in data_sources:
            databases.append({
                "store_name": source.name,  # Use store_name (actual resource name)
                "type": source.type,
                "location": source.location,  # Now contains project_id/host info
                "project_id": getattr(source, 'project_id', None),
                "database_name": getattr(source, 'database_name', None)
            })
        
        return {
            "status": "success",
            "client_id": client_id,
            "total_databases": len(databases),
            "databases": databases,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list databases: {str(e)}")

# SDE Management Endpoints
@app.get("/client-sdes/{client_id}")
async def get_client_sde_selections(client_id: str):
    """
    Get the current SDE selections for a client.
    
    Args:
        client_id: Client ID to get SDE selections for
        
    Returns:
        List of selected SDEs with their configurations
    """
    try:
        import psycopg2
        
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT pattern_name, sensitivity, protection_method, selected_at 
                    FROM client_selected_sdes 
                    WHERE client_id = %s
                    ORDER BY selected_at DESC
                """, (client_id,))
                
                results = cursor.fetchall()
                selected_sdes = [
                    {
                        "pattern_name": row[0],
                        "sensitivity": row[1],
                        "protection_method": row[2],
                        "selected_at": row[3].isoformat() if row[3] else None
                    }
                    for row in results
                ]
                
                return {
                    "client_id": client_id,
                    "selected_sdes": selected_sdes,
                    "total_count": len(selected_sdes),
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Failed to get client SDE selections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get client SDE selections: {str(e)}")

@app.post("/client-sdes")
async def update_client_sde_selections(request: SDESelectionRequest):
    """
    Update SDE selections for a client. This replaces all existing selections.
    
    Args:
        request: SDESelectionRequest containing client_id and list of pattern names
        
    Returns:
        Updated SDE selections
    """
    try:
        import psycopg2
        
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cursor:
                # First, delete existing selections for this client
                cursor.execute("DELETE FROM client_selected_sdes WHERE client_id = %s", (request.client_id,))
                
                # Insert new selections
                for pattern_name in request.pattern_names:
                    cursor.execute("""
                        INSERT INTO client_selected_sdes (client_id, pattern_name, sensitivity, protection_method)
                        VALUES (%s, %s, 'medium', 'encryption')
                        ON CONFLICT (client_id, pattern_name) DO NOTHING
                    """, (request.client_id, pattern_name))
                
                conn.commit()
                
                # Return updated selections
                cursor.execute("""
                    SELECT pattern_name, sensitivity, protection_method, selected_at 
                    FROM client_selected_sdes 
                    WHERE client_id = %s
                    ORDER BY pattern_name
                """, (request.client_id,))
                
                results = cursor.fetchall()
                selected_sdes = [
                    {
                        "pattern_name": row[0],
                        "sensitivity": row[1],
                        "protection_method": row[2],
                        "selected_at": row[3].isoformat() if row[3] else None
                    }
                    for row in results
                ]
                
                return {
                    "status": "success",
                    "client_id": request.client_id,
                    "selected_sdes": selected_sdes,
                    "total_count": len(selected_sdes),
                    "message": f"Updated SDE selections for client {request.client_id}",
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Failed to update client SDE selections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update client SDE selections: {str(e)}")

@app.get("/available-sdes")
async def get_available_sdes():
    """
    Get the list of all available SDE patterns that clients can select from.
    
    Returns:
        List of available SDE patterns with their descriptions
    """
    try:
        # Read available patterns from the regex patterns YAML file
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'regex_patterns.yaml')
        
        with open(config_path, 'r') as f:
            patterns = yaml.safe_load(f)
        
        available_sdes = []
        for pattern in patterns:
            if isinstance(pattern, dict) and 'data_type' in pattern:
                available_sdes.append({
                    "pattern_name": pattern['data_type'],
                    "description": pattern.get('description', f"Pattern for detecting {pattern['data_type'].replace('_', ' ')}")
                })
        
        return {
            "available_sdes": available_sdes,
            "total_count": len(available_sdes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get available SDEs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available SDEs: {str(e)}")

@app.post("/run-pipeline", response_model=DriverResponse)
async def run_pipeline(request: ClientRequest):
    """
    FastAPI endpoint to run the data protection pipeline for a given client_id.

    Args:
        request: ClientRequest object containing client_id

    Returns:
        DriverResponse with results from all agents
    """
    try:
        result = driver(request.client_id)
        return DriverResponse(**result)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ===== DISCOVERED OBJECTS ENDPOINTS =====

@app.get("/discovered-objects/{client_id}")
async def get_discovered_objects(client_id: str, store_id: Optional[int] = None, limit: int = 100):
    """
    Get discovered objects (files/tables) for a client
    
    Args:
        client_id: Client ID
        store_id: Optional store ID to filter by specific data store
        limit: Maximum number of objects to return (default: 100)
    
    Returns:
        List of discovered objects with metadata
    """
    try:
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        
        db_manager = PostgreSQLCloudScanDBManager()
        discovered_objects = db_manager.get_discovered_objects(
            store_id=store_id,
            client_id=client_id,
            limit=limit
        )
        
        # Group objects by type for better UI organization
        objects_by_type = {}
        objects_by_store = {}
        
        for obj in discovered_objects:
            obj_type = obj.get('type', 'unknown')  # Use 'type' instead of 'object_type'
            store_id_key = obj.get('store_id', 'unknown')
            
            if obj_type not in objects_by_type:
                objects_by_type[obj_type] = []
            objects_by_type[obj_type].append(obj)
            
            if store_id_key not in objects_by_store:
                objects_by_store[store_id_key] = []
            objects_by_store[store_id_key].append(obj)
        
        return {
            "status": "success",
            "client_id": client_id,
            "total_objects": len(discovered_objects),
            "objects": discovered_objects,
            "objects_by_type": objects_by_type,
            "objects_by_store": objects_by_store,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting discovered objects for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovered objects: {str(e)}")

@app.get("/discovered-objects/{client_id}/stores")
async def get_discovered_objects_by_store(client_id: str):
    """
    Get discovered objects grouped by data store for a client
    
    Args:
        client_id: Client ID
    
    Returns:
        Dictionary with store information and their discovered objects
    """
    try:
        from postgresql_db_manager import PostgreSQLCloudScanDBManager

        db_manager = PostgreSQLCloudScanDBManager()
        
        # Get all data stores for the client
        data_stores = db_manager.get_data_stores_with_sequence(client_id=client_id)
        
        # Get discovered objects for each store
        stores_with_objects = []
        for store in data_stores:
            store_id = store['store_id']
            objects = db_manager.get_discovered_objects(store_id=store_id, client_id=client_id)
            
            # Group objects by type
            objects_by_type = {}
            for obj in objects:
                obj_type = obj.get('type', 'unknown')  # Use 'type' instead of 'object_type'
                if obj_type not in objects_by_type:
                    objects_by_type[obj_type] = []
                objects_by_type[obj_type].append(obj)
            
            store_info = {
                **store,
                'total_objects': len(objects),
                'objects': objects,
                'objects_by_type': objects_by_type,
                'object_type_counts': {obj_type: len(objs) for obj_type, objs in objects_by_type.items()}
            }
            stores_with_objects.append(store_info)
        
        return {
            "status": "success",
            "client_id": client_id,
            "total_stores": len(stores_with_objects),
            "stores": stores_with_objects,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting discovered objects by store for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovered objects by store: {str(e)}")

@app.get("/discovered-objects/{client_id}/summary")
async def get_discovered_objects_summary(client_id: str):
    """
    Get summary statistics of discovered objects for a client
    
    Args:
        client_id: Client ID
    
    Returns:
        Summary statistics of discovered objects
    """
    try:
        from postgresql_db_manager import PostgreSQLCloudScanDBManager

        db_manager = PostgreSQLCloudScanDBManager()
        discovered_objects = db_manager.get_discovered_objects(client_id=client_id, limit=1000)
        
        # Calculate summary statistics
        total_objects = len(discovered_objects)
        
        # Group by type
        type_counts = {}
        size_by_type = {}
        
        # Group by store
        store_counts = {}
        
        # Track accessibility
        accessible_count = 0
        inaccessible_count = 0
        
        total_size = 0
        
        for obj in discovered_objects:
            obj_type = obj.get('type', 'unknown')  # Use 'type' instead of 'object_type'
            store_id = obj.get('store_id', 'unknown')
            size_bytes = obj.get('size_bytes') or 0
            is_accessible = obj.get('is_accessible', True)
            
            # Type counts
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            size_by_type[obj_type] = size_by_type.get(obj_type, 0) + size_bytes
            
            # Store counts
            store_counts[store_id] = store_counts.get(store_id, 0) + 1
            
            # Accessibility
            if is_accessible:
                accessible_count += 1
            else:
                inaccessible_count += 1
            
            total_size += size_bytes
        
        return {
            "status": "success",
            "client_id": client_id,
            "summary": {
                "total_objects": total_objects,
                "total_size_bytes": total_size,
                "total_size_human": _format_bytes(total_size),
                "accessible_objects": accessible_count,
                "inaccessible_objects": inaccessible_count,
                "accessibility_rate": round((accessible_count / total_objects * 100), 2) if total_objects > 0 else 0
            },
            "by_type": {
                "counts": type_counts,
                "sizes": size_by_type,
                "sizes_human": {obj_type: _format_bytes(size) for obj_type, size in size_by_type.items()}
            },
            "by_store": store_counts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting discovered objects summary for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovered objects summary: {str(e)}")

@app.get("/discovered-objects/{client_id}/store/{store_id}")
async def get_discovered_objects_for_store(client_id: str, store_id: int, limit: int = 100):
    """
    Get discovered objects for a specific data store
    
    Args:
        client_id: Client ID
        store_id: Data store ID
        limit: Maximum number of objects to return
    
    Returns:
        List of discovered objects for the specified store
    """
    try:
        from postgresql_db_manager import PostgreSQLCloudScanDBManager

        db_manager = PostgreSQLCloudScanDBManager()
        
        # Get store information
        store_info = db_manager.get_data_store_by_id(store_id=store_id, client_id=client_id)
        if not store_info:
            raise HTTPException(status_code=404, detail=f"Data store {store_id} not found for client {client_id}")
        
        # Get discovered objects for this store
        discovered_objects = db_manager.get_discovered_objects(
            store_id=store_id,
            client_id=client_id,
            limit=limit
        )
        
        # Group by type
        objects_by_type = {}
        for obj in discovered_objects:
            obj_type = obj.get('type', 'unknown')  # Use 'type' instead of 'object_type'
            if obj_type not in objects_by_type:
                objects_by_type[obj_type] = []
            objects_by_type[obj_type].append(obj)
        
        return {
            "status": "success",
            "client_id": client_id,
            "store": store_info,
            "total_objects": len(discovered_objects),
            "objects": discovered_objects,
            "objects_by_type": objects_by_type,
            "type_counts": {obj_type: len(objs) for obj_type, objs in objects_by_type.items()},
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovered objects for store {store_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovered objects for store: {str(e)}")

def _format_bytes(bytes_size):
    """Convert bytes to human readable format"""
    if bytes_size == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_size >= 1024 and i < len(size_names) - 1:
        bytes_size /= 1024.0
        i += 1
    
    return f"{bytes_size:.2f} {size_names[i]}"

@app.delete("/discovered-objects/{client_id}/store/{store_id}")
async def clear_discovered_objects_for_store(client_id: str, store_id: int):
    """
    Clear all discovered objects for a specific data store
    (Useful for re-discovery)
    
    Args:
        client_id: Client ID
        store_id: Data store ID
    
    Returns:
        Success confirmation
    """
    try:
        from postgresql_db_manager import PostgreSQLCloudScanDBManager

        db_manager = PostgreSQLCloudScanDBManager()
        
        # Verify store exists
        store_info = db_manager.get_data_store_by_id(store_id=store_id, client_id=client_id)
        if not store_info:
            raise HTTPException(status_code=404, detail=f"Data store {store_id} not found for client {client_id}")
        
        # Clear discovered objects
        success = db_manager.clear_discovered_objects(store_id=store_id, client_id=client_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Cleared discovered objects for store {store_id}",
                "client_id": client_id,
                "store_id": store_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear discovered objects")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing discovered objects for store {store_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear discovered objects: {str(e)}")

@app.get("/discovered-objects/{client_id}/search")
async def search_discovered_objects(
    client_id: str, 
    query: str, 
    object_type: Optional[str] = None,
    store_id: Optional[int] = None,
    limit: int = 50
):
    """
    Search discovered objects by name, path, or metadata
    
    Args:
        client_id: Client ID
        query: Search query (searches in name, path, metadata)
        object_type: Optional filter by object type (file, table, etc.)
        store_id: Optional filter by store ID
        limit: Maximum number of results
    
    Returns:
        List of matching discovered objects
    """
    try:
        from postgresql_db_manager import PostgreSQLCloudScanDBManager

        db_manager = PostgreSQLCloudScanDBManager()
        
        # Get all discovered objects for the client
        all_objects = db_manager.get_discovered_objects(
            store_id=store_id,
            client_id=client_id,
            limit=1000  # Get more for searching
        )
        
        # Filter by search query
        query_lower = query.lower()
        matching_objects = []
        
        for obj in all_objects:
            # Check if query matches in name, path, or metadata
            matches = False
            
            # Search in name (unified field)
            if query_lower in obj.get('name', '').lower():
                matches = True
            
            # Search in path (unified field)  
            if query_lower in obj.get('path', '').lower():
                matches = True
            
            # Search in metadata (if it's a string)
            metadata = obj.get('metadata', '')
            if isinstance(metadata, str) and query_lower in metadata.lower():
                matches = True
            
            # Filter by object type if specified
            if object_type and obj.get('type') != object_type:
                matches = False
            
            if matches:
                matching_objects.append(obj)
                
            # Limit results
            if len(matching_objects) >= limit:
                break
        
        return {
            "status": "success",
            "client_id": client_id,
            "query": query,
            "filters": {
                "object_type": object_type,
                "store_id": store_id
            },
            "total_matches": len(matching_objects),
            "objects": matching_objects,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching discovered objects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search discovered objects: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
