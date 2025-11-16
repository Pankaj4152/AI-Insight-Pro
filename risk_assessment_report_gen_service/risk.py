import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, FastAPI, Query
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import yaml

import pytz
import json
from modular_report_generation_agent import ModularReportGenerationAgent
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi import BackgroundTasks

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct")

app=FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SDE API Models (from sdeapi.py)
class AddSDEModel(BaseModel):
    name: str
    data_type: str
    sensitivity: str
    regex: str
    classification: str
    selected_industry: str

class SDEModel(BaseModel):
    name: str
    sensitivity: str
    classification_level: str

class ClientSelectedSDEModel(BaseModel):
    client_id: str
    sdes: list[SDEModel]

# SDE Removal API Models
class RemoveSDERequest(BaseModel):
    client_id: str
    pattern_name: str

class ClearAllSDERequest(BaseModel):
    client_id: str

class APIResponse(BaseModel):
    status: str
    message: str
    client_id: str
    timestamp: str

class RemoveSDEResponse(APIResponse):
    removed_pattern: str

class ClearAllSDEResponse(APIResponse):
    cleared_count: int

class ForceRemoveSDERequest(BaseModel):
    client_id: str
    pattern_name: str
    force: bool = True
    admin_override: bool = False

class ForceRemoveSDEResponse(APIResponse):
    removed_pattern: str
    deleted_findings: int

# Database URL function (from sdeapi.py)
def get_db_url():
    # Try environment variable first
    db_url = os.getenv('DB_URL')
    if db_url:
        return db_url
    
    # Fall back to YAML config
    try:
        with open('agent_config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            db_config = config['database']['postgresql']
            return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?sslmode={db_config['sslmode']}"
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

DB_URL = get_db_url()

class OpenRouterLLMClient:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.available = self._check_connection()

    def _check_connection(self) -> bool:
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenRouter API connection failed: {e}")
            return False

    def generate_response(self, prompt: str) -> str:
        if not self.available:
            raise ValueError("OpenRouter API is not available")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://yourdomain.com",
            "X-Title": "RiskAgent"
        }
        json_payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a risk assessment expert."},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(self.api_url, json=json_payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No summary generated.")
        except Exception as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise

class RiskAssessmentRequest(BaseModel):
    client_id: str
    risk_level: Optional[List[int]] = None  # 0=medium, 1=high, -1=low
    sensitivity: Optional[List[int]] = None  # 0=medium, 1=high, -1=low
    data_source: Optional[List[int]] = None  # List of store_ids

class ModularRiskAssessmentAgent:
    RISK_MAP = {1: "high", 0: "medium", -1: "low"}

    def __init__(self):
        # Initialize LLM client
        try:
            self.llm_client = OpenRouterLLMClient()
            self.ai_analysis_available = self.llm_client.available
            logger.info(f"OpenRouter LLM client initialized: {self.ai_analysis_available}")
        except Exception as e:
            self.llm_client = None
            self.ai_analysis_available = False
            logger.warning(f"LLM client initialization failed: {e}")
        
        # Database connection will be handled by get_db_connection method
        logger.info("Risk assessment agent initialized successfully")

    def get_db_connection(self):
        """Get database connection using postgresql_db_manager"""
        try:
            from postgresql_db_manager import PostgreSQLCloudScanDBManager
            db_manager = PostgreSQLCloudScanDBManager()
            return db_manager.get_connection()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def assess_risk_for_client(self, client_id: str, risk_level: Optional[List[int]] = None, 
                             sensitivity: Optional[List[int]] = None, 
                             data_source: Optional[List[int]] = None) -> Dict[str, any]:
        conn = self.get_db_connection()
        try:
            return self._assess_risk_sql(client_id, risk_level, sensitivity, data_source, conn)
        finally:
            conn.close()

    def _assess_risk_sql(self, client_id: str, risk_level: Optional[List[int]], 
                        sensitivity: Optional[List[int]], data_source: Optional[List[int]], 
                        conn) -> Dict[str, any]:
        cur = conn.cursor()

        # Data Sources
        try:
            cur.execute("SELECT COUNT(*) as count FROM data_stores WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            total_data_sources = row["count"] if row and "count" in row else 0
            logger.debug(f"Total data sources for client {client_id}: {total_data_sources}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching total_data_sources for client {client_id}: {e}")
            conn.rollback()
            total_data_sources = 0

        # Total SDEs - Count from client_selected_sdes table (user-selected SDEs)
        try:
            cur.execute("SELECT COUNT(*) AS total_sdes FROM client_selected_sdes WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            total_sdes = row["total_sdes"] if row and "total_sdes" in row else 0
            logger.debug(f"Total SDEs for client {client_id}: {total_sdes}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching total_sdes for client {client_id}: {e}")
            conn.rollback()
            total_sdes = 0

        # Scanned SDEs
        try:
            cur.execute("SELECT COUNT(DISTINCT sde_id) AS scanned_sdes FROM scan_findings WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            scanned_sdes = row["scanned_sdes"] if row and "scanned_sdes" in row else 0
            logger.debug(f"Scanned SDEs for client {client_id}: {scanned_sdes}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching scanned_sdes for client {client_id}: {e}")
            conn.rollback()
            scanned_sdes = 0

        # High Risk SDEs - FIXED: Use scan_findings with sensitivity filter
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT sde_id) AS high_risk_sdes
                FROM scan_findings
                WHERE client_id = %s
                  AND LOWER(sensitivity) = 'high'
            """, (client_id,))
            row = cur.fetchone()
            high_risk_sdes = row["high_risk_sdes"] if row and "high_risk_sdes" in row else 0
            logger.debug(f"High Risk SDEs for client {client_id}: {high_risk_sdes}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching high_risk_sdes for client {client_id}: {e}")
            conn.rollback()
            high_risk_sdes = 0

        # High Risk Records - FIXED: Count from scan_findings
        try:
            cur.execute("""
                SELECT COUNT(*) AS high_risk_records
                FROM scan_findings
                WHERE client_id = %s
                  AND LOWER(sensitivity) = 'high'
            """, (client_id,))
            row = cur.fetchone()
            high_risk_records = row["high_risk_records"] if row and "high_risk_records" in row else 0
            logger.debug(f"High Risk Records for client {client_id}: {high_risk_records}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching high_risk_records for client {client_id}: {e}")
            conn.rollback()
            high_risk_records = 0

        # Total Sensitive Records - FIXED: Count from scan_findings
        try:
            cur.execute("SELECT COUNT(*) AS total_sensitive_records FROM scan_findings WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            total_sensitive_records = row["total_sensitive_records"] if row and "total_sensitive_records" in row else 0
            logger.debug(f"Total Sensitive Records for client {client_id}: {total_sensitive_records}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching total_sensitive_records for client {client_id}: {e}")
            conn.rollback()
            total_sensitive_records = 0

        # Calculate total scans
        try:
            # Count distinct scan sessions from scan_findings table
            cur.execute("SELECT COUNT(DISTINCT scan_id) AS total_scans FROM scan_findings WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            total_scans = row["total_scans"] if row and "total_scans" in row else 0
            logger.debug(f"Total scans for client {client_id}: {total_scans}")
            conn.commit()
        except Exception as e:
            logger.error(f"Error fetching total_scans for client {client_id}: {e}")
            conn.rollback()
            total_scans = 0

        # Calculate risk score using the same logic as test-calculation
        logger.debug(f"=== RISK SCORE CALCULATION DEBUG ===")
        logger.debug(f"scanned_sdes: {scanned_sdes}")
        logger.debug(f"total_sdes: {total_sdes}")
        logger.debug(f"high_risk_records: {high_risk_records}")
        logger.debug(f"total_sensitive_records: {total_sensitive_records}")
        
        try:
            # Risk score calculation with safety checks (same as test-calculation)
            risk_score = 0.0
            
            if total_sensitive_records > 0:
                # Risk score based on high-risk findings and total sensitive records
                high_risk_ratio = (high_risk_records / total_sensitive_records) * 100
                # Add base risk for having sensitive data
                base_risk = min(30, total_sensitive_records / 100)  # Cap at 30
                risk_score = min(100, high_risk_ratio + base_risk)
                logger.debug(f"Risk score calculation: high_risk_ratio({high_risk_ratio}) + base_risk({base_risk}) = {risk_score}")
            else:
                risk_score = 25.0  # Base risk score
                logger.debug(f"Base risk score: {risk_score}")
            
            risk_score = min(100, round(risk_score, 2))
            logger.debug(f"Final risk score: {risk_score}")
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            risk_score = 50.0  # Default risk score
            logger.debug(f"Using default risk score: {risk_score}")

        # Calculate confidence score using the same logic as test-calculation
        logger.debug(f"=== CONFIDENCE SCORE CALCULATION DEBUG ===")
        logger.debug(f"scanned_sdes: {scanned_sdes}")
        logger.debug(f"total_sdes: {total_sdes}")
        logger.debug(f"total_scans: {total_scans}")
        
        try:
            confidence_score = 0.0
            
            # Component 1: Scan coverage (50% weight)
            if total_sdes > 0:
                scan_coverage = (scanned_sdes / total_sdes) * 50
                logger.debug(f"Scan coverage component: ({scanned_sdes} / {total_sdes}) * 50 = {scan_coverage}")
                confidence_score += scan_coverage
            else:
                logger.debug("No SDEs found, scan coverage component: 0")
            
            # Component 2: Scan frequency (30% weight) - based on actual scan activity
            scan_frequency_score = 0.0
            if total_scans > 0:
                # Calculate scans per day over the last 30 days
                try:
                    cur.execute("""
                        SELECT COUNT(*) as recent_scans 
                        FROM scan_findings 
                        WHERE client_id = %s 
                        AND scan_timestamp > NOW() - INTERVAL '30 days'
                    """, (client_id,))
                    recent_scans_result = cur.fetchone()
                    recent_scans = recent_scans_result["recent_scans"] if recent_scans_result else 0
                    
                    # Score based on scan frequency: 0-30 points
                    if recent_scans >= 30:  # Daily scans
                        scan_frequency_score = 30
                    elif recent_scans >= 15:  # Every other day
                        scan_frequency_score = 25
                    elif recent_scans >= 7:  # Weekly scans
                        scan_frequency_score = 20
                    elif recent_scans >= 3:  # Bi-weekly scans
                        scan_frequency_score = 15
                    elif recent_scans >= 1:  # Monthly scans
                        scan_frequency_score = 10
                    else:
                        scan_frequency_score = 5  # No recent scans
                        
                    logger.debug(f"Recent scans (30 days): {recent_scans}, frequency score: {scan_frequency_score}")
                except Exception as e:
                    logger.warning(f"Error calculating scan frequency: {e}")
                    scan_frequency_score = 10  # Default to low frequency
            else:
                scan_frequency_score = 5  # No scans at all
                logger.debug("No scans found, frequency score: 5")
            
            confidence_score += scan_frequency_score
            
            # Component 3: Data freshness (20% weight) - based on time since last scan
            data_freshness_score = 0.0
            try:
                cur.execute("""
                    SELECT MAX(scan_timestamp) as last_scan 
                    FROM scan_findings 
                    WHERE client_id = %s
                """, (client_id,))
                last_scan_result = cur.fetchone()
                
                if last_scan_result and last_scan_result["last_scan"]:
                    last_scan_time = last_scan_result["last_scan"]
                    time_diff = datetime.now() - last_scan_time
                    days_since_scan = time_diff.days
                    
                    # Score based on data freshness: 0-20 points
                    if days_since_scan <= 1:  # Within 24 hours
                        data_freshness_score = 20
                    elif days_since_scan <= 7:  # Within a week
                        data_freshness_score = 15
                    elif days_since_scan <= 30:  # Within a month
                        data_freshness_score = 10
                    elif days_since_scan <= 90:  # Within 3 months
                        data_freshness_score = 5
                    else:  # Over 3 months old
                        data_freshness_score = 0
                        
                    logger.debug(f"Days since last scan: {days_since_scan}, freshness score: {data_freshness_score}")
                else:
                    data_freshness_score = 0  # No scan history
                    logger.debug("No scan history, freshness score: 0")
            except Exception as e:
                logger.warning(f"Error calculating data freshness: {e}")
                data_freshness_score = 5  # Default to low freshness
            
            confidence_score += data_freshness_score
            
            # Ensure confidence score is within 0-100 range
            confidence_score = min(100, max(0, round(confidence_score, 2)))
            
            # If confidence score is 100, replace with random number between 80-90
            if confidence_score == 100:
                import random
                confidence_score = random.uniform(80, 90)
                confidence_score = round(confidence_score, 2)
                logger.debug(f"Confidence score was 100, replaced with random value: {confidence_score}")
            else:
                logger.debug(f"Final confidence score: {confidence_score}")
            
            # Force replace any 100 with random value
            if confidence_score >= 99.5:
                import random
                confidence_score = random.uniform(80, 90)
                confidence_score = round(confidence_score, 2)
                logger.debug(f"Confidence score was too high ({confidence_score}), forced to random: {confidence_score}")
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            confidence_score = 50.0  # Default confidence score
            logger.debug(f"Using default confidence score: {confidence_score}")

        # Last Scan Time
        ist = pytz.timezone('Asia/Kolkata')
        last_scan_time = datetime.now(ist).isoformat()
        logger.debug(f"Last scan time: {last_scan_time}")

        # Next Scheduled Scan
        next_scan = (datetime.now(ist) + timedelta(days=2)).isoformat()
        logger.debug(f"Next scheduled scan: {next_scan}")

        # LLM Summary
        llm_prompt = f"""
        You are a risk assessment expert. Analyze the following:
        - Client ID: {client_id}
        - Total SDEs: {total_sdes}
        - High Risk SDEs: {high_risk_sdes}
        - High Risk Records: {high_risk_records}
        - Total Sensitive Records: {total_sensitive_records}
        - Risk Score: {risk_score}
        - Confidence Score: {confidence_score}

        Provide a short, clear risk summary and actionable recommendations.
        """

        if self.ai_analysis_available:
            try:
                summary = self.llm_client.generate_response(llm_prompt)
                logger.debug(f"OpenRouter LLM summary: {summary}")
            except Exception as e:
                logger.error(f"OpenRouter LLM request failed: {e}")
                summary = self._mock_llm_summary(risk_score, confidence_score, total_sdes, high_risk_sdes, high_risk_records)
        else:
            summary = self._mock_llm_summary(risk_score, confidence_score, total_sdes, high_risk_sdes, high_risk_records)
        logger.debug(f"Final LLM summary: {summary}")

        # Store results
        assessment = {
            "client_id": client_id,
            "total_data_sources": total_data_sources,
            "total_sdes": total_sdes,
            "scanned_sdes": scanned_sdes,
            "high_risk_sdes": high_risk_sdes,
            "high_risk_records": high_risk_records,
            "total_sensitive_records": total_sensitive_records,
            "scans_completed": total_scans,
            "last_scan_time": last_scan_time,
            "next_scheduled_scan": next_scan,
            "risk_score": risk_score,
            "confidence_score": confidence_score,
            "llm_summary": summary.strip()
        }
        
        logger.debug(f"=== FINAL ASSESSMENT DEBUG ===")
        logger.debug(f"Assessment object: {assessment}")
        
        try:
            assessment_id = self.store_risk_assessment(assessment)
            assessment["assessment_id"] = assessment_id
            logger.debug(f"Assessment stored with ID: {assessment_id}")
        except Exception as e:
            logger.error(f"Error storing risk assessment: {e}")
            assessment["assessment_id"] = None

        # Store in reports table
        try:
            if assessment_id is not None:
                self.store_report(assessment, assessment_id)
                logger.debug("Report stored successfully")
            else:
                logger.warning("Skipping report storage - assessment_id is None")
        except Exception as e:
            logger.error(f"Error storing report: {e}")

        return assessment

    def _mock_llm_summary(self, risk_score: float, confidence_score: float, total_sdes: int, 
                         high_risk_sdes: int, total_sensitive_records: int) -> str:
        risk_level = 'high' if risk_score > 75 else 'medium' if risk_score > 50 else 'low'
        return f"""
        Risk Assessment Summary:
        - Risk Score: {risk_score} indicates {risk_level} risk.
        - Confidence Score: {confidence_score}%.
        - Findings: {high_risk_sdes} high-risk SDEs detected out of {total_sdes} total SDEs, with {total_sensitive_records} sensitive records.
        Recommendations:
        - Review high-risk SDEs for immediate mitigation.
        - Increase scan frequency if confidence is low (<70%).
        """

    def store_risk_assessment(self, assessment: Dict[str, any]) -> int:
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO risk_assessments (
                    client_id, total_data_sources, total_sdes, scanned_sdes, high_risk_sdes,
                    total_sensitive_records, scans_completed, last_scan_time, next_scheduled_scan,
                    risk_score, confidence_score, llm_summary, timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING assessment_id
                """,
                (
                    assessment["client_id"],
                    assessment["total_data_sources"],
                    assessment["total_sdes"],
                    assessment["scanned_sdes"],
                    assessment["high_risk_sdes"],
                    assessment["total_sensitive_records"],
                    assessment["scans_completed"],
                    assessment["last_scan_time"],
                    assessment["next_scheduled_scan"],
                    assessment["risk_score"],
                    assessment["confidence_score"],
                    assessment["llm_summary"],
                    datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                ),
            )
            row = cur.fetchone()
            if row:
                # Handle both dict and tuple responses
                if isinstance(row, dict) and "assessment_id" in row:
                    assessment_id = row["assessment_id"]
                elif isinstance(row, (list, tuple)) and len(row) > 0:
                    assessment_id = row[0]
                else:
                    logger.error(f"Unexpected row format: {row}")
                    raise ValueError("Failed to retrieve assessment_id")
                
                logger.info(f"Successfully stored risk assessment for client_id {assessment['client_id']} with assessment_id {assessment_id}")
                conn.commit()
                return assessment_id
            else:
                logger.error("Failed to retrieve assessment_id from insert")
                raise ValueError("Failed to retrieve assessment_id")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store risk assessment for client_id {assessment['client_id']}: {e}")
            raise
        finally:
            conn.close()

    def store_report(self, assessment: Dict[str, any], assessment_id: int):
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            report_content = json.dumps(assessment)
            cur.execute(
                """
                INSERT INTO reports (
                    client_id, assessment_id, report_type, report_format, report_content, created_at, title
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING report_id
                """,
                (
                    assessment["client_id"],
                    assessment_id,
                    "risk_assessment",
                    "json",
                    report_content,
                    datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                    f"Risk Assessment Report for {assessment['client_id']} - {assessment['last_scan_time']}"
                ),
            )
            row = cur.fetchone()
            if row:
                # Handle both dict and tuple responses
                if isinstance(row, dict) and "report_id" in row:
                    report_id = row["report_id"]
                elif isinstance(row, (list, tuple)) and len(row) > 0:
                    report_id = row[0]
                else:
                    logger.error(f"Unexpected row format: {row}")
                    raise ValueError("Failed to retrieve report_id")
                
                logger.info(f"Successfully stored report for client_id {assessment['client_id']} with report_id {report_id}")
                conn.commit()
            else:
                logger.error("Failed to retrieve report_id from insert")
                raise ValueError("Failed to retrieve report_id")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store report for client_id {assessment['client_id']}: {e}")
            raise
        finally:
            conn.close()

    def assess_all_clients(self) -> List[Dict[str, any]]:
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT client_id FROM client_prof")
            clients = [row["client_id"] for row in cur.fetchall()]
            conn.commit()
            
            results = []
            for client_id in clients:
                result = self.assess_risk_for_client(client_id)
                results.append(result)
            return results
        except Exception as e:
            conn.rollback()
            logger.error(f"Error assessing all clients: {e}")
            raise
        finally:
            conn.close()

    def get_latest_risk_assessments(self, client_id: str, limit: int = 10) -> List[Dict[str, any]]:
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM risk_assessments WHERE client_id = %s ORDER BY timestamp DESC LIMIT %s",
                (client_id, limit)
            )
            results = [dict(row) for row in cur.fetchall()]
            conn.commit()
            return results
        except Exception as e:
            conn.rollback()
            logger.error(f"Error fetching risk assessments for client {client_id}: {e}")
            raise
        finally:
            conn.close()



@app.post("/risk/risk-assessment")
async def assess_risk(request: RiskAssessmentRequest):
    # Fetch and log SDEs for the given client_id
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sdes WHERE client_id = %s", (request.client_id,))
        sdes = cur.fetchall()
        logger.debug(f"[POST /risk-assessment] SDEs for client_id {request.client_id}: {len(sdes)} records found")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[POST /risk-assessment] Error fetching SDEs for client_id {request.client_id}: {e}")
    
    try:
        agent = ModularRiskAssessmentAgent()
        result = agent.assess_risk_for_client(
            request.client_id,
            request.risk_level,
            request.sensitivity,
            request.data_source
        )
        return result
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk/risk-assessments/{client_id}")
async def get_risk_assessments(client_id: str, limit: int = 10):
    try:
        agent = ModularRiskAssessmentAgent()
        results = agent.get_latest_risk_assessments(client_id, limit)
        return results
    except Exception as e:
        logger.error(f"Fetching risk assessments failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk/db-status")
def db_status():
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        if conn:
            conn.close()
            return {"status": "connected"}
        else:
            return {"status": "not connected", "error": "No connection object returned"}
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {"status": "not connected", "error": str(e)}





@app.get("/risk/total-data-sources/{client_id}")
async def get_total_data_sources(client_id: str):
    """Get total data sources for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) as count FROM data_stores WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_data_sources = row["count"] if row and "count" in row else 0
        
        conn.close()
        return {"client_id": client_id, "total_data_sources": total_data_sources}
    except Exception as e:
        logger.error(f"Error fetching total data sources for client {client_id}: {e}")
        return {"client_id": client_id, "total_data_sources": 0, "error": str(e)}

@app.get("/risk/total-sdes/{client_id}")
async def get_total_sdes(client_id: str):
    """Get total SDEs for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Count from client_selected_sdes table
        cur.execute("SELECT COUNT(*) AS total_sdes FROM client_selected_sdes WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sdes = row["total_sdes"] if row and "total_sdes" in row else 0
        
        conn.close()
        return {"client_id": client_id, "total_sdes": total_sdes}
    except Exception as e:
        logger.error(f"Error fetching total SDEs for client {client_id}: {e}")
        return {"client_id": client_id, "total_sdes": 0, "error": str(e)}

@app.get("/risk/scanned-sdes/{client_id}")
async def get_scanned_sdes(client_id: str):
    """Get scanned SDEs for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS scanned_sdes FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        scanned_sdes = row["scanned_sdes"] if row and "scanned_sdes" in row else 20
        
        conn.close()
        return {"client_id": client_id, "scanned_sdes": scanned_sdes}
    except Exception as e:
        logger.error(f"Error fetching scanned SDEs for client {client_id}: {e}")
        return {"client_id": client_id, "scanned_sdes": 0, "error": str(e)}

@app.get("/risk/high-risk-sdes/{client_id}")
async def get_high_risk_sdes(client_id: str):
    """Get high risk SDEs for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # FIXED: Use scan_findings instead of sdes
        cur.execute("""
            SELECT COUNT(DISTINCT sde_id) AS high_risk_sdes
            FROM scan_findings
            WHERE client_id = %s
              AND LOWER(sensitivity) = 'high'
        """, (client_id,))
        row = cur.fetchone()
        high_risk_sdes = row["high_risk_sdes"] if row and "high_risk_sdes" in row else 0
        
        conn.close()
        return {"client_id": client_id, "high_risk_sdes": high_risk_sdes}
    except Exception as e:
        logger.error(f"Error fetching high risk SDEs for client {client_id}: {e}")
        return {"client_id": client_id, "high_risk_sdes": 0, "error": str(e)}

@app.get("/risk/high-risk-records/{client_id}")
async def get_high_risk_records(client_id: str):
    """Get high risk records for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # FIXED: Use scan_findings instead of sdes
        cur.execute("""
            SELECT COUNT(*) AS high_risk_records
            FROM scan_findings
            WHERE client_id = %s
              AND (COALESCE(NULLIF(LOWER(sensitivity), ''), 'high') = 'high')
        """, (client_id,))
        row = cur.fetchone()
        high_risk_records = row["high_risk_records"] if row and "high_risk_records" in row else 0
        
        conn.close()
        return {"client_id": client_id, "high_risk_records": high_risk_records}
    except Exception as e:
        logger.error(f"Error fetching high risk records for client {client_id}: {e}")
        return {"client_id": client_id, "high_risk_records": 0, "error": str(e)}

@app.get("/risk/total-sensitive-records/{client_id}")
async def get_total_sensitive_records(client_id: str):
    """Get total sensitive records for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # FIXED: Use scan_findings instead of sdes
        cur.execute("SELECT COUNT(*) AS total_sensitive_records FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sensitive_records = row["total_sensitive_records"] if row and "total_sensitive_records" in row else 0
        
        conn.close()
        return {"client_id": client_id, "total_sensitive_records": total_sensitive_records}
    except Exception as e:
        logger.error(f"Error fetching total sensitive records for client {client_id}: {e}")
        return {"client_id": client_id, "total_sensitive_records": 0, "error": str(e)}

@app.get("/risk/total-scans/{client_id}")
async def get_total_scans(client_id: str):
    """Get total scans for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Count distinct scan sessions from scan_findings table
        cur.execute("SELECT COUNT(DISTINCT scan_id) AS total_scans FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_scans = row["total_scans"] if row and "total_scans" in row else 0
        
        conn.close()
        return {"client_id": client_id, "total_scans": total_scans}
    except Exception as e:
        logger.error(f"Error fetching total scans for client {client_id}: {e}")
        return {"client_id": client_id, "total_scans": 0, "error": str(e)}

@app.get("/risk/risk-score/{client_id}")
async def get_risk_score(client_id: str):
    """Get risk score for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get high-risk records and total sensitive records
        cur.execute("""
            SELECT COUNT(*) AS high_risk_records
            FROM scan_findings
            WHERE client_id = %s
              AND LOWER(sensitivity) = 'high'
        """, (client_id,))
        row = cur.fetchone()
        high_risk_records = row["high_risk_records"] if row and "high_risk_records" in row else 0
        
        cur.execute("SELECT COUNT(*) AS total_sensitive_records FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sensitive_records = row["total_sensitive_records"] if row and "total_sensitive_records" in row else 0
        
        # Calculate risk score
        if total_sensitive_records > 0:
            # Risk score based on high-risk findings and total sensitive records
            high_risk_ratio = (high_risk_records / total_sensitive_records) * 100
            # Add base risk for having sensitive data
            base_risk = min(30, total_sensitive_records / 100)  # Cap at 30
            risk_score = min(100, high_risk_ratio + base_risk)
        else:
            risk_score = 25.0
        
        risk_score = min(100, round(risk_score, 2))
        
        conn.close()
        return {"client_id": client_id, "risk_score": risk_score}
    except Exception as e:
        logger.error(f"Error calculating risk score for client {client_id}: {e}")
        return {"client_id": client_id, "risk_score": 50.0, "error": str(e)}

@app.get("/risk/confidence-score/{client_id}")
async def get_confidence_score(client_id: str):
    """Get confidence score for a client using the same calculation as main risk assessment"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()

        # Get the same metrics used in main risk assessment calculation
        # Total SDEs - Count from client_selected_sdes table (user-selected SDEs)
        cur.execute("SELECT COUNT(*) AS total_sdes FROM client_selected_sdes WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sdes = row["total_sdes"] if row and "total_sdes" in row else 0

        # Scanned SDEs
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS scanned_sdes FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        scanned_sdes = row["scanned_sdes"] if row and "scanned_sdes" in row else 0

        # Total scans
        cur.execute("SELECT COUNT(DISTINCT scan_id) AS total_scans FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_scans = row["total_scans"] if row and "total_scans" in row else 0

        # Calculate confidence score using the same logic as main risk assessment
        confidence_score = 0.0

        # Component 1: Scan coverage (50% weight)
        if total_sdes > 0:
            scan_coverage = (scanned_sdes / total_sdes) * 50
            confidence_score += scan_coverage

        # Component 2: Scan frequency (30% weight) - based on actual scan activity
        scan_frequency_score = 0.0
        if total_scans > 0:
            # Calculate scans per day over the last 30 days
            try:
                cur.execute("""
                    SELECT COUNT(*) as recent_scans
                    FROM scan_findings
                    WHERE client_id = %s
                    AND scan_timestamp > NOW() - INTERVAL '30 days'
                """, (client_id,))
                recent_scans_result = cur.fetchone()
                recent_scans = recent_scans_result["recent_scans"] if recent_scans_result else 0

                # Score based on scan frequency: 0-30 points
                if recent_scans >= 30:  # Daily scans
                    scan_frequency_score = 30
                elif recent_scans >= 15:  # Every other day
                    scan_frequency_score = 25
                elif recent_scans >= 7:  # Weekly scans
                    scan_frequency_score = 20
                elif recent_scans >= 3:  # Bi-weekly scans
                    scan_frequency_score = 15
                elif recent_scans >= 1:  # Monthly scans
                    scan_frequency_score = 10
                else:
                    scan_frequency_score = 5  # No recent scans
            except Exception as e:
                logger.warning(f"Error calculating scan frequency: {e}")
                scan_frequency_score = 10  # Default to low frequency
        else:
            scan_frequency_score = 5  # No scans at all

        confidence_score += scan_frequency_score

        # Component 3: Data freshness (20% weight) - based on time since last scan
        data_freshness_score = 0.0
        try:
            cur.execute("""
                SELECT MAX(scan_timestamp) as last_scan
                FROM scan_findings
                WHERE client_id = %s
            """, (client_id,))
            last_scan_result = cur.fetchone()

            if last_scan_result and last_scan_result["last_scan"]:
                last_scan_time = last_scan_result["last_scan"]
                time_diff = datetime.now() - last_scan_time
                days_since_scan = time_diff.days

                # Score based on data freshness: 0-20 points
                if days_since_scan <= 1:  # Within 24 hours
                    data_freshness_score = 20
                elif days_since_scan <= 7:  # Within a week
                    data_freshness_score = 15
                elif days_since_scan <= 30:  # Within a month
                    data_freshness_score = 10
                elif days_since_scan <= 90:  # Within 3 months
                    data_freshness_score = 5
                else:  # Over 3 months old
                    data_freshness_score = 0
            else:
                data_freshness_score = 0  # No scan history
        except Exception as e:
            logger.warning(f"Error calculating data freshness: {e}")
            data_freshness_score = 5  # Default to low freshness

        confidence_score += data_freshness_score

        # Ensure confidence score is within 0-100 range
        confidence_score = min(100, max(0, round(confidence_score, 2)))

        # If confidence score is 100, replace with random number between 80-90
        if confidence_score == 100:
            import random
            confidence_score = random.uniform(80, 90)
            confidence_score = round(confidence_score, 2)
        elif confidence_score >= 99.5:
            import random
            confidence_score = random.uniform(80, 90)
            confidence_score = round(confidence_score, 2)

        conn.close()
        return {"client_id": client_id, "confidence_score": confidence_score}
    except Exception as e:
        logger.error(f"Error calculating confidence score for client {client_id}: {e}")
        return {"client_id": client_id, "confidence_score": 0, "error": str(e)}

@app.get("/risk/last-scan-time/{client_id}")
async def get_last_scan_time(client_id: str):
    """Get last scan time for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT MAX(scan_timestamp) as last_scan_time 
            FROM scan_findings 
            WHERE client_id = %s
        """, (client_id,))
        row = cur.fetchone()
        
        if row and row["last_scan_time"]:
            last_scan_time = row["last_scan_time"].isoformat()
        else:
            ist = pytz.timezone('Asia/Kolkata')
            last_scan_time = datetime.now(ist).isoformat()
        
        conn.close()
        return {"client_id": client_id, "last_scan_time": last_scan_time}
    except Exception as e:
        logger.error(f"Error fetching last scan time for client {client_id}: {e}")
        ist = pytz.timezone('Asia/Kolkata')
        return {"client_id": client_id, "last_scan_time": datetime.now(ist).isoformat(), "error": str(e)}

@app.get("/risk/next-scheduled-scan/{client_id}")
async def get_next_scheduled_scan(client_id: str):
    """Get next scheduled scan for a client"""
    try:
        ist = pytz.timezone('Asia/Kolkata')
        next_scan = (datetime.now(ist) + timedelta(days=2)).isoformat()
        
        return {"client_id": client_id, "next_scheduled_scan": next_scan}
    except Exception as e:
        logger.error(f"Error calculating next scheduled scan for client {client_id}: {e}")
        ist = pytz.timezone('Asia/Kolkata')
        return {"client_id": client_id, "next_scheduled_scan": datetime.now(ist).isoformat(), "error": str(e)}

@app.get("/risk/llm-summary/{client_id}")
async def get_llm_summary(client_id: str):
    """Get LLM summary for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        
        # Get basic metrics for summary
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) AS total_sdes FROM sdes WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sdes = row["total_sdes"] if row and "total_sdes" in row else 0
        
        cur.execute("""
            SELECT COUNT(DISTINCT sde_id) AS high_risk_sdes
            FROM scan_findings
            WHERE client_id = %s
              AND (COALESCE(NULLIF(LOWER(sensitivity), ''), 'high') = 'high')
        """, (client_id,))
        row = cur.fetchone()
        high_risk_sdes = row["high_risk_sdes"] if row and "high_risk_sdes" in row else 0
        
        cur.execute("SELECT COUNT(*) AS total_sensitive_records FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sensitive_records = row["total_sensitive_records"] if row and "total_sensitive_records" in row else 0
        
        conn.close()
        
        # Calculate risk score
        if total_sensitive_records > 0:
            # Risk score based on high-risk findings and total sensitive records
            high_risk_ratio = (high_risk_records / total_sensitive_records) * 100
            # Add base risk for having sensitive data
            base_risk = min(30, total_sensitive_records / 100)  # Cap at 30
            risk_score = min(100, high_risk_ratio + base_risk)
        else:
            risk_score = 25.0
        
        # Generate summary
        summary = agent._mock_llm_summary(risk_score, 85.0, total_sdes, high_risk_sdes, total_sensitive_records)
        
        return {"client_id": client_id, "llm_summary": summary.strip()}
    except Exception as e:
        logger.error(f"Error generating LLM summary for client {client_id}: {e}")
        return {"client_id": client_id, "llm_summary": "Risk assessment summary unavailable.", "error": str(e)}

@app.get("/risk/all-metrics/{client_id}")
async def get_all_risk_metrics(client_id: str):
    """Get all risk metrics for a client in one call"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get all metrics in parallel queries
        metrics = {}
        
        # Total data sources
        cur.execute("SELECT COUNT(*) as count FROM data_stores WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        metrics["total_data_sources"] = row["count"] if row and "count" in row else 0
        
        # Total SDEs - Count from sdes table (SDE definitions)
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS total_sdes FROM sdes WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        metrics["total_sdes"] = row["total_sdes"] if row and "total_sdes" in row else 0
        
        # Scanned SDEs
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS scanned_sdes FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        metrics["scanned_sdes"] = row["scanned_sdes"] if row and "scanned_sdes" in row else 0
        
        # High risk SDEs - FIXED: Use scan_findings with proper sensitivity filter
        cur.execute("""
            SELECT COUNT(DISTINCT sde_id) AS high_risk_sdes
            FROM scan_findings
            WHERE client_id = %s
              AND LOWER(sensitivity) = 'high'
        """, (client_id,))
        row = cur.fetchone()
        metrics["high_risk_sdes"] = row["high_risk_sdes"] if row and "high_risk_sdes" in row else 0
        
        # High risk records
        cur.execute("""
            SELECT COUNT(*) AS high_risk_records
            FROM scan_findings
            WHERE client_id = %s
              AND (COALESCE(NULLIF(LOWER(sensitivity), ''), 'high') = 'high')
        """, (client_id,))
        row = cur.fetchone()
        metrics["high_risk_records"] = row["high_risk_records"] if row and "high_risk_records" in row else 0
        
        # Total sensitive records
        cur.execute("SELECT COUNT(*) AS total_sensitive_records FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        metrics["total_sensitive_records"] = row["total_sensitive_records"] if row and "total_sensitive_records" in row else 0
        
        # Total scans
        cur.execute("SELECT COUNT(DISTINCT scan_id) AS total_scans FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        metrics["total_scans"] = row["total_scans"] if row and "total_scans" in row else 0
        
        # Calculate scores
        if metrics["total_sensitive_records"] > 0:
            # Risk score based on high-risk findings and total sensitive records
            high_risk_ratio = (metrics["high_risk_records"] / metrics["total_sensitive_records"]) * 100
            # Add base risk for having sensitive data
            base_risk = min(30, metrics["total_sensitive_records"] / 100)  # Cap at 30
            metrics["risk_score"] = min(100, high_risk_ratio + base_risk)
        else:
            metrics["risk_score"] = 25.0
        
        metrics["risk_score"] = min(100, round(metrics["risk_score"], 2))
        
        # Calculate real confidence score based on actual data
        confidence_score = 0.0
        
        # Component 1: Scan coverage (50% weight)
        if metrics["total_sdes"] > 0:
            scan_coverage = (metrics["scanned_sdes"] / metrics["total_sdes"]) * 50
            confidence_score += scan_coverage
            logger.debug(f"Scan coverage: {scan_coverage:.2f}%")
        else:
            logger.debug("No SDEs found, scan coverage: 0%")
        
        # Component 2: Scan frequency (30% weight) - based on actual scan activity
        scan_frequency_score = 0.0
        if metrics["total_scans"] > 0:
            # Calculate scans per day over the last 30 days
            try:
                cur.execute("""
                    SELECT COUNT(*) as recent_scans 
                    FROM scan_activity 
                    WHERE client_id = %s 
                    AND scan_time > NOW() - INTERVAL '30 days'
                """, (client_id,))
                recent_scans_result = cur.fetchone()
                recent_scans = recent_scans_result["recent_scans"] if recent_scans_result else 0
                
                # Score based on scan frequency: 0-30 points
                if recent_scans >= 30:  # Daily scans
                    scan_frequency_score = 30
                elif recent_scans >= 15:  # Every other day
                    scan_frequency_score = 25
                elif recent_scans >= 7:  # Weekly scans
                    scan_frequency_score = 20
                elif recent_scans >= 3:  # Bi-weekly scans
                    scan_frequency_score = 15
                elif recent_scans >= 1:  # Monthly scans
                    scan_frequency_score = 10
                else:
                    scan_frequency_score = 5  # No recent scans
                    
                logger.debug(f"Recent scans (30 days): {recent_scans}, frequency score: {scan_frequency_score}")
            except Exception as e:
                logger.warning(f"Error calculating scan frequency: {e}")
                scan_frequency_score = 10  # Default to low frequency
        else:
            scan_frequency_score = 5  # No scans at all
            logger.debug("No scans found, frequency score: 5")
        
        confidence_score += scan_frequency_score
        
        # Component 3: Data freshness (20% weight) - based on time since last scan
        data_freshness_score = 0.0
        try:
            cur.execute("""
                SELECT MAX(scan_time) as last_scan 
                FROM scan_activity 
                WHERE client_id = %s
            """, (client_id,))
            last_scan_result = cur.fetchone()
            
            if last_scan_result and last_scan_result["last_scan"]:
                last_scan_time = last_scan_result["last_scan"]
                time_diff = datetime.now() - last_scan_time
                days_since_scan = time_diff.days
                
                # Score based on data freshness: 0-20 points
                if days_since_scan <= 1:  # Within 24 hours
                    data_freshness_score = 20
                elif days_since_scan <= 7:  # Within a week
                    data_freshness_score = 15
                elif days_since_scan <= 30:  # Within a month
                    data_freshness_score = 10
                elif days_since_scan <= 90:  # Within 3 months
                    data_freshness_score = 5
                else:  # Over 3 months old
                    data_freshness_score = 0
                    
                logger.debug(f"Days since last scan: {days_since_scan}, freshness score: {data_freshness_score}")
            else:
                data_freshness_score = 0  # No scan history
                logger.debug("No scan history, freshness score: 0")
        except Exception as e:
            logger.warning(f"Error calculating data freshness: {e}")
            data_freshness_score = 5  # Default to low freshness
        
        confidence_score += data_freshness_score
        
        # Ensure confidence score is within 0-100 range
        metrics["confidence_score"] = min(100, max(0, round(confidence_score, 2)))
        
        # If confidence score is 100, replace with random number between 80-90
        if metrics["confidence_score"] == 100:
            import random
            metrics["confidence_score"] = random.uniform(80, 90)
            metrics["confidence_score"] = round(metrics["confidence_score"], 2)
            logger.debug(f"Confidence score was 100, replaced with random value: {metrics['confidence_score']}%")
        else:
            logger.debug(f"Final confidence score: {metrics['confidence_score']}%")
        
        # Force replace any 100 with random value
        if metrics["confidence_score"] >= 99.5:
            import random
            metrics["confidence_score"] = random.uniform(80, 90)
            metrics["confidence_score"] = round(metrics["confidence_score"], 2)
            logger.debug(f"Confidence score was too high ({metrics['confidence_score']}), forced to random: {metrics['confidence_score']}%")
        
        # Timestamps
        ist = pytz.timezone('Asia/Kolkata')
        metrics["last_scan_time"] = datetime.now(ist).isoformat()
        metrics["next_scheduled_scan"] = (datetime.now(ist) + timedelta(days=2)).isoformat()
        
        # LLM Summary
        summary = agent._mock_llm_summary(metrics["risk_score"], metrics["confidence_score"], 
                                         metrics["total_sdes"], metrics["high_risk_sdes"], 
                                         metrics["total_sensitive_records"])
        metrics["llm_summary"] = summary.strip()
        
        # AUTO-STORE RISK ASSESSMENT DATA
        try:
            # Check if recent assessment exists (within last 1 hour)
            cur.execute("""
                SELECT assessment_id FROM risk_assessments 
                WHERE client_id = %s 
                AND timestamp > NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (client_id,))
            recent_assessment = cur.fetchone()
            
            if not recent_assessment:
                # Only store if no recent assessment exists
                assessment = {
                    "client_id": client_id,
                    "total_data_sources": metrics["total_data_sources"],
                    "total_sdes": metrics["total_sdes"],
                    "scanned_sdes": metrics["scanned_sdes"],
                    "high_risk_sdes": metrics["high_risk_sdes"],
                    "total_sensitive_records": metrics["total_sensitive_records"],
                    "scans_completed": metrics["total_scans"],
                    "last_scan_time": metrics["last_scan_time"],
                    "next_scheduled_scan": metrics["next_scheduled_scan"],
                    "risk_score": metrics["risk_score"],
                    "confidence_score": metrics["confidence_score"],
                    "llm_summary": metrics["llm_summary"]
                }
                
                # Store risk assessment data
                assessment_id = agent.store_risk_assessment(assessment)
                logger.info(f"Auto-stored risk assessment for client {client_id} with ID {assessment_id}")
            else:
                logger.info(f"Recent assessment exists for client {client_id}, skipping auto-store")
            
        except Exception as e:
            logger.warning(f"Failed to auto-store risk assessment for client {client_id}: {e}")
            # Continue without failing the metrics request
        
        conn.close()
        
        return {"client_id": client_id, "metrics": metrics}
    except Exception as e:
        logger.error(f"Error fetching all metrics for client {client_id}: {e}")
        return {"client_id": client_id, "metrics": {}, "error": str(e)}

@app.get("/risk/dataset-names/{client_id}")
async def get_dataset_names(client_id: str):
    """Get dataset names for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT DISTINCT dataset_name FROM sdes WHERE client_id = %s AND dataset_name IS NOT NULL", (client_id,))
        rows = cur.fetchall()
        dataset_names = [row["dataset_name"] for row in rows if row["dataset_name"]]
        
        conn.close()
        return {"client_id": client_id, "dataset_names": dataset_names}
    except Exception as e:
        logger.error(f"Error fetching dataset names for client {client_id}: {e}")
        return {"client_id": client_id, "dataset_names": [], "error": str(e)}

@app.get("/risk/data-sources/{client_id}")
async def get_data_sources(client_id: str):
    """Get data sources for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # First, let's check what columns exist in data_stores table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'data_stores'")
        columns = [row["column_name"] for row in cur.fetchall()]
        print(f"Available columns in data_stores: {columns}")
        
        # Use the correct column names based on what exists
        if 'store_name' in columns:
            cur.execute("SELECT DISTINCT store_name, store_type FROM data_stores WHERE client_id = %s", (client_id,))
            rows = cur.fetchall()
            data_sources = [{"name": row["store_name"], "type": row["store_type"]} for row in rows if row["store_name"]]
        elif 'name' in columns:
            cur.execute("SELECT DISTINCT name, type FROM data_stores WHERE client_id = %s", (client_id,))
            rows = cur.fetchall()
            data_sources = [{"name": row["name"], "type": row["type"]} for row in rows if row["name"]]
        else:
            # Fallback - just get any data
            cur.execute("SELECT * FROM data_stores WHERE client_id = %s LIMIT 5", (client_id,))
            rows = cur.fetchall()
            data_sources = [{"name": str(row), "type": "unknown"} for row in rows]
        
        conn.close()
        return {"client_id": client_id, "data_sources": data_sources}
    except Exception as e:
        logger.error(f"Error fetching data sources for client {client_id}: {e}")
        return {"client_id": client_id, "data_sources": [], "error": str(e)}





@app.get("/risk/debug-regex-patterns")
async def debug_regex_patterns():
    """Debug endpoint to check regex patterns and scan findings"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        debug_info = {
            "regex_table_info": {},
            "scan_findings_info": {},
            "aadhaar_specific": {}
        }
        
        # Check regexes table
        try:
            cur.execute("SELECT COUNT(*) as count FROM regexes")
            row = cur.fetchone()
            debug_info["regex_table_info"]["total_patterns"] = row["count"] if row else 0
            
            # Get all regex patterns
            cur.execute("SELECT pattern_name, regex_pattern, data_type FROM regexes LIMIT 10")
            patterns = [dict(row) for row in cur.fetchall()]
            debug_info["regex_table_info"]["sample_patterns"] = patterns
            
            # Check for aadhaar specifically
            cur.execute("SELECT pattern_name, regex_pattern, data_type FROM regexes WHERE pattern_name ILIKE '%aadhaar%' OR data_type ILIKE '%aadhaar%'")
            aadhaar_patterns = [dict(row) for row in cur.fetchall()]
            debug_info["aadhaar_specific"]["patterns_found"] = aadhaar_patterns
            
        except Exception as e:
            debug_info["regex_table_info"]["error"] = str(e)
        
        # Check scan_findings table
        try:
            cur.execute("SELECT COUNT(*) as count FROM scan_findings")
            row = cur.fetchone()
            debug_info["scan_findings_info"]["total_findings"] = row["count"] if row else 0
            
            # Get sample scan_findings with pattern_matched
            cur.execute("SELECT finding_id, pattern_matched, data_value, sensitivity FROM scan_findings WHERE pattern_matched IS NOT NULL LIMIT 5")
            sample_findings = [dict(row) for row in cur.fetchall()]
            debug_info["scan_findings_info"]["sample_with_patterns"] = sample_findings
            
            # Check for aadhaar in pattern_matched
            cur.execute("SELECT finding_id, pattern_matched, data_value FROM scan_findings WHERE pattern_matched ILIKE '%aadhaar%'")
            aadhaar_findings = [dict(row) for row in cur.fetchall()]
            debug_info["aadhaar_specific"]["findings_found"] = aadhaar_findings
            
        except Exception as e:
            debug_info["scan_findings_info"]["error"] = str(e)
        
        conn.close()
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug regex patterns: {e}")
        return {"errorr": str(e)}

@app.get("/risk/filtered-findings/")
async def get_filtered_findings(
    client_id: str = Query(...),
    data_source: str = Query(None),
    risk_level: str = Query(None),
    sensitivity: str = Query(None)
):
    """Filter SDEs and scan_findings by data source, risk level, and sensitivity"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()

        # Build dynamic WHERE clauses for SDEs
        sdes_where = ["client_id = %s"]
        sdes_params = [client_id]
        if data_source:
            sdes_where.append("dataset_name = %s")
            sdes_params.append(data_source)
        if sensitivity and sensitivity.lower() != 'any':
            # Treat "Highly Sensitive" and "Sensitive" as "high"
            if sensitivity.lower() in ['highly sensitive', 'sensitive']:
                sdes_where.append("LOWER(sensitivity) IN ('high', 'highly sensitive', 'sensitive')")
            else:
                sdes_where.append("LOWER(sensitivity) = %s")
                sdes_params.append(sensitivity.lower())
        sdes_query = f"SELECT * FROM sdes WHERE {' AND '.join(sdes_where)} LIMIT 100"
        cur.execute(sdes_query, tuple(sdes_params))
        sdes_results = [dict(row) for row in cur.fetchall()]

        # Build dynamic WHERE clauses for scan_findings
        findings_where = ["client_id = %s"]
        findings_params = [client_id]
        if data_source:
            findings_where.append("object_path LIKE %s")
            findings_params.append(f"%{data_source}%")
        if risk_level and risk_level.lower() != 'any':
            findings_where.append("LOWER(risk_level) = %s")
            findings_params.append(risk_level.lower())
        if sensitivity and sensitivity.lower() != 'any':
            # Treat "Highly Sensitive" and "Sensitive" as "high"
            if sensitivity.lower() in ['highly sensitive', 'sensitive']:
                findings_where.append("LOWER(sensitivity) IN ('high', 'highly sensitive', 'sensitive')")
            else:
                findings_where.append("LOWER(sensitivity) = %s")
                findings_params.append(sensitivity.lower())
        findings_query = f"SELECT * FROM scan_findings WHERE {' AND '.join(findings_where)} LIMIT 100"
        cur.execute(findings_query, tuple(findings_params))
        findings_results = [dict(row) for row in cur.fetchall()]

        # Calculate summary statistics
        total_sdes = len(sdes_results)
        total_findings = len(findings_results)
        high_risk_findings = len([f for f in findings_results if f.get('risk_level', '').lower() == 'high'])
        high_sensitivity_findings = len([f for f in findings_results if f.get('sensitivity', '').lower() in ['high', 'highly sensitive', 'sensitive']])

        conn.close()
        return {
            "client_id": client_id,
            "filtered_sdes": sdes_results,
            "filtered_findings": findings_results,
            "summary": {
            "total_sdes": total_sdes,
                "total_findings": total_findings,
                "high_risk_findings": high_risk_findings,
                "high_sensitivity_findings": high_sensitivity_findings
            }
        }
    except Exception as e:
        logger.error(f"Error fetching filtered findings for client {client_id}: {e}")
        return {"client_id": client_id, "filtered_sdes": [], "filtered_findings": [], "summary": {}, "error": str(e)}

@app.get("/risk/scan-activity/{client_id}")
async def get_scan_activity(client_id: str):
    """Get scan activity data for a client including recent scans and their status"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get all data stores for this client including discovery_timestamp
        cur.execute("""
            SELECT store_id, store_name, store_type, location, discovery_timestamp
            FROM data_stores
            WHERE client_id = %s
        """, (client_id,))
        data_stores = [dict(row) for row in cur.fetchall()]
        
        # Get recent scans for this client (last 10 scans)
        cur.execute("""
            SELECT 
                s.scan_id,
                s.store_id,
                s.status,
                ds.store_name,
                ds.store_type,
                ds.location
            FROM scans s
            JOIN data_stores ds ON s.store_id = ds.store_id
            WHERE ds.client_id = %s
            ORDER BY s.scan_id DESC
            LIMIT 10
        """, (client_id,))
        
        recent_scans = []
        for row in cur.fetchall():
            recent_scans.append({
                "scan_id": row["scan_id"],
                "store_id": row["store_id"],
                "store_name": row["store_name"] or "Unknown",
                "store_type": row["store_type"] or "Unknown",
                "location": row["location"] or "Unknown",
                "status": row["status"] or "Unknown"
            })
        
        # Get unique active data sources (data sources with successful scans)
        cur.execute("""
            SELECT DISTINCT ds.store_id, ds.store_name, ds.store_type, ds.location, ds.discovery_timestamp
            FROM data_stores ds
            JOIN scans s ON ds.store_id = s.store_id
            WHERE ds.client_id = %s
            AND s.status IN ('completed', 'success')
        """, (client_id,))
        
        active_data_sources = [dict(row) for row in cur.fetchall()]
        
        # Since scan_id is integer, we'll create a simple daily count
        daily_scans = [
            {"day": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "scans": 0}
            for i in range(7)
        ]
        daily_scans.reverse()  # Oldest first for chart
        
        conn.close()
        
        return {
            "client_id": client_id,
            "recent_scans": recent_scans,
            "daily_scans": daily_scans,
            "total_scans": len(recent_scans),
            "data_stores": data_stores,
            "active_data_sources": active_data_sources,
            "total_data_sources": len(data_stores),
            "active_sources_count": len(active_data_sources)
        }
        
    except Exception as e:
        logger.error(f"Error fetching scan activity for client {client_id}: {e}")
        return {
            "client_id": client_id,
            "recent_scans": [],
            "daily_scans": [],
            "total_scans": 0,
            "data_stores": [],
            "active_data_sources": [],
            "total_data_sources": 0,
            "active_sources_count": 0,
            "error": str(e)
        }

@app.get("/risk/sde-count/")
async def get_sde_count(pattern_name: str = Query(...), data_source: str = Query(...)):
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        # Get regex pattern for the pattern_name
        cur.execute("SELECT regex_pattern FROM regexes WHERE pattern_name = %s", (pattern_name,))
        row = cur.fetchone()
        if not row:
            return {"pattern_name": pattern_name, "data_source": data_source, "found_count": 0, "message": "Not found"}
        regex_pattern = row["regex_pattern"]
        # Count scan_findings with this pattern and partial data source match
        cur.execute("""
            SELECT COUNT(*) AS found_count
            FROM scan_findings
            WHERE pattern_matched = %s
              AND location_metadata::text ILIKE %s
        """, (regex_pattern, f"%{data_source}%"))
        count_row = cur.fetchone()
        found_count = count_row["found_count"] if count_row else 0
        conn.close()
        return {
            "pattern_name": pattern_name,
            "data_source": data_source,
            "found_count": found_count,
            "message": "Not found" if found_count == 0 else None
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/top-findings/{client_id}")
async def get_top_risk_findings(
    client_id: str, 
    limit: int = Query(7, description="Number of findings to return"),
    sensitivity: str = Query(None, description="Filter by sensitivity level"),
    risk_level: str = Query(None, description="Filter by risk level")
):
    """Get top risk findings for a client with specific columns and filters"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Build dynamic WHERE clause with specific filters
        where_conditions = ["client_id = %s"]
        params = [client_id]
        
        # Add optional filters if provided
        if sensitivity:
            where_conditions.append("LOWER(sensitivity) = %s")
            params.append(sensitivity.lower())
        
        if risk_level:
            where_conditions.append("LOWER(risk_level) = %s")
            params.append(risk_level.lower())
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                finding_id,
                sensitivity,
                location_metadata,
                field_type as finding_type,
                data_value
            FROM scan_findings 
            WHERE {where_clause}
            ORDER BY finding_id DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, tuple(params))
        findings = []
        
        for row in cur.fetchall():
            # Extract location from metadata
            location = "Unknown"
            if row["location_metadata"]:
                try:
                    location_data = json.loads(row["location_metadata"])
                    location = location_data.get("source_name", "Unknown")
                except:
                    location = "Unknown"
            
            findings.append({
                "finding_id": row["finding_id"],
                "sensitivity": row["sensitivity"] or "Unknown",
                "location": location,
                "finding_type": row["finding_type"] or "Unknown",
                "data_value": row["data_value"] or "N/A"
            })
        
        conn.close()
        return {"client_id": client_id, "findings": findings}
        
    except Exception as e:
        logger.error(f"Error fetching top risk findings for client {client_id}: {e}")
        return {"client_id": client_id, "findings": [], "error": str(e)}

@app.get("/risk/sensitivity-by-source/{client_id}")
async def get_sensitivity_by_source(client_id: str):
    """Get sensitivity analysis by data source"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get sensitivity counts by data source
        cur.execute("""
            SELECT 
                COALESCE(ds.store_name, 
                         COALESCE(
                             (sf.location_metadata::json->>'source_name'), 
                             'Unknown Source'
                         )
                ) as store_name,
                COUNT(*) as total_findings,
                COUNT(CASE WHEN sf.sensitivity = 'high' THEN 1 END) as high_sensitivity,
                COUNT(CASE WHEN sf.sensitivity = 'medium' THEN 1 END) as medium_sensitivity,
                COUNT(CASE WHEN sf.sensitivity = 'low' THEN 1 END) as low_sensitivity
            FROM scan_findings sf
            LEFT JOIN data_stores ds ON (
                ds.client_id = sf.client_id 
                AND ds.store_name = COALESCE(sf.location_metadata::json->>'source_name', 'Unknown')
            )
            WHERE sf.client_id = %s
            GROUP BY COALESCE(ds.store_name, 
                             COALESCE(
                                 (sf.location_metadata::json->>'source_name'), 
                                 'Unknown Source'
                             )
            )
            ORDER BY high_sensitivity DESC, total_findings DESC
        """, (client_id,))
        
        sensitivity_data = {}
        for row in cur.fetchall():
            store_name = row["store_name"] or "Unknown Source"
            # Use high sensitivity count as the main metric
            sensitivity_data[store_name] = row["high_sensitivity"] or 0
        
        conn.close()
        return {"client_id": client_id, "sensitivity_by_source": sensitivity_data}
        
    except Exception as e:
        logger.error(f"Error fetching sensitivity by source for client {client_id}: {e}")
        return {"client_id": client_id, "sensitivity_by_source": {}, "error": str(e)}

# ============================================================================
# NEW DASHBOARD & RISK ASSESSMENT APIs
# ============================================================================

@app.get("/risk/data-source-types/{client_id}")
async def get_data_source_types(client_id: str):
    """
    Get distribution of data sources by type for pie chart
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                store_type,
                COUNT(*) as count
            FROM data_stores 
            WHERE client_id = %s 
            GROUP BY store_type 
            ORDER BY count DESC
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "data_source_types": [
                {"type": row["store_type"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/risk-level-distribution/{client_id}")
async def get_risk_level_distribution(client_id: str):
    """
    Get risk level distribution for donut chart - OPTIMIZED
    """
    try:
        # Direct database connection for speed
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        db_manager = PostgreSQLCloudScanDBManager()
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        # Optimized query with LIMIT and faster execution
        cur.execute("""
            SELECT 
                COALESCE(risk_level, 'Unknown') as risk_level,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
            GROUP BY risk_level 
            ORDER BY count DESC
            LIMIT 10
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        # Ensure we have at least some data for the chart
        if not results:
            results = [{"risk_level": "Low", "count": 0}]
        
        return {
            "risk_distribution": [
                {"level": row["risk_level"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        logger.error(f"Error in risk level distribution for {client_id}: {e}")
        # Return fallback data
        return {
            "risk_distribution": [
                {"level": "Low", "count": 0},
                {"level": "Medium", "count": 0},
                {"level": "High", "count": 0}
            ]
        }

@app.get("/risk/sensitivity-categories/{client_id}")
async def get_sensitivity_categories(client_id: str):
    """
    Get sensitivity distribution for pie chart - OPTIMIZED
    """
    try:
        # Direct database connection for speed
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        db_manager = PostgreSQLCloudScanDBManager()
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        # Optimized query with LIMIT and faster execution
        cur.execute("""
            SELECT 
                COALESCE(sensitivity, 'Unknown') as sensitivity,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
            GROUP BY sensitivity 
            ORDER BY count DESC
            LIMIT 10
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        # Ensure we have at least some data for the chart
        if not results:
            results = [{"sensitivity": "Low", "count": 0}]
        
        return {
            "sensitivity_categories": [
                {"category": row["sensitivity"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        logger.error(f"Error in sensitivity categories for {client_id}: {e}")
        # Return fallback data
        return {
            "sensitivity_categories": [
                {"category": "Low", "count": 0},
                {"category": "Medium", "count": 0},
                {"category": "High", "count": 0}
            ]
        }



@app.get("/risk/scan-activity-timeline/{client_id}")
async def get_scan_activity_timeline(client_id: str, days: int = 30):
    """
    Get scan activity timeline for line chart
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                DATE(scan_timestamp::timestamp) as scan_date,
                COUNT(*) as findings_count
            FROM scan_findings 
            WHERE client_id = %s 
                AND scan_timestamp::timestamp >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(scan_timestamp::timestamp) 
            ORDER BY scan_date
        """, (client_id, days))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "scan_timeline": [
                {"date": str(row["scan_date"]), "findings": row["findings_count"]} 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/top-risk-locations/{client_id}")
async def get_top_risk_locations(client_id: str, limit: int = 10):
    """
    Get top risk locations for bar chart
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                ds.store_name,
                ds.store_type,
                COUNT(sf.finding_id) as risk_count,
                COUNT(CASE WHEN sf.risk_level = 'High' THEN 1 END) as high_risk_count
            FROM scan_findings sf
            JOIN data_stores ds ON sf.store_id = ds.store_id
            WHERE sf.client_id = %s 
            GROUP BY ds.store_name, ds.store_type
            ORDER BY high_risk_count DESC, risk_count DESC
            LIMIT %s
        """, (client_id, limit))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "top_risk_locations": [
                {
                    "store_name": row["store_name"],
                    "store_type": row["store_type"],
                    "total_risks": row["risk_count"],
                    "high_risks": row["high_risk_count"]
                } 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/sde-category-distribution/{client_id}")
async def get_sde_category_distribution(client_id: str):
    """Get SDE category distribution for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                pattern_name as sde_category,
                COUNT(*) as count
            FROM client_selected_sdes 
            WHERE client_id = %s 
            GROUP BY pattern_name 
            ORDER BY count DESC
        """, (client_id,))
        
        rows = cur.fetchall()
        distribution = [{"category": row["sde_category"], "count": row["count"]} for row in rows]
        
        conn.close()
        return {"client_id": client_id, "sde_category_distribution": distribution}
    except Exception as e:
        logger.error(f"Error fetching SDE category distribution for client {client_id}: {e}")
        return {"client_id": client_id, "sde_category_distribution": [], "error": str(e)}

@app.get("/risk/sde-category-risk-distribution/{client_id}")
async def get_sde_category_risk_distribution(client_id: str):
    """Get SDE category distribution grouped by risk level (high, medium, low)"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get SDE categories with their sensitivity levels and group by risk
        cur.execute("""
            SELECT 
                risk_level,
                COUNT(*) as count
            FROM (
                SELECT 
                    CASE 
                        WHEN LOWER(sensitivity) = 'high' THEN 'high'
                        WHEN LOWER(sensitivity) = 'medium' THEN 'medium'
                        WHEN LOWER(sensitivity) = 'low' THEN 'low'
                        ELSE 'medium'  -- default to medium if sensitivity is null or unknown
                    END as risk_level
                FROM client_selected_sdes
                WHERE client_id = %s
            ) sub
            GROUP BY risk_level
            ORDER BY 
                CASE 
                    WHEN risk_level = 'high' THEN 1
                    WHEN risk_level = 'medium' THEN 2
                    WHEN risk_level = 'low' THEN 3
                    ELSE 4
                END
        """, (client_id,))
        
        rows = cur.fetchall()
        risk_distribution = [{"risk_level": row["risk_level"], "count": row["count"]} for row in rows]
        
        # Calculate total for percentage calculation
        total_sdes = sum(row["count"] for row in risk_distribution)
        
        # Add percentages to each risk level
        for item in risk_distribution:
            item["percentage"] = round((item["count"] / total_sdes * 100), 2) if total_sdes > 0 else 0
        
        conn.close()
        return {
            "client_id": client_id, 
            "sde_risk_distribution": risk_distribution,
            "total_sdes": total_sdes
        }
    except Exception as e:
        logger.error(f"Error fetching SDE category risk distribution for client {client_id}: {e}")
        return {"client_id": client_id, "sde_risk_distribution": [], "total_sdes": 0, "error": str(e)}

@app.get("/risk/detection-method-stats/{client_id}")
async def get_detection_method_stats(client_id: str):
    """
    Get detection methods statistics for bar chart
    """
    try:
        agent = ModularRiskAssessmentAgent()

        conn = agent.get_db_connection()

        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                detection_method,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
            GROUP BY detection_method 
            ORDER BY count DESC
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "detection_methods": [
                {"method": row["detection_method"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/confidence-score-distribution/{client_id}")
async def get_confidence_score_distribution(client_id: str):
    """
    Get confidence score distribution for histogram - OPTIMIZED
    """
    try:
        # Direct database connection for speed
        from postgresql_db_manager import PostgreSQLCloudScanDBManager
        db_manager = PostgreSQLCloudScanDBManager()
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        # Optimized query with LIMIT and faster execution
        cur.execute("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.8 THEN 'High'
                    WHEN confidence_score >= 0.5 THEN 'Medium'
                    ELSE 'Low'
                END as confidence_level,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
            GROUP BY confidence_level 
            ORDER BY count DESC
            LIMIT 10
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        # Ensure we have at least some data for the chart
        if not results:
            results = [{"confidence_level": "Low", "count": 0}]
        
        return {
            "confidence_distribution": [
                {"level": row["confidence_level"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        logger.error(f"Error in confidence score distribution for {client_id}: {e}")
        # Return fallback data
        return {
            "confidence_distribution": [
                {"level": "Low", "count": 0},
                {"level": "Medium", "count": 0},
                {"level": "High", "count": 0}
            ]
        }

@app.get("/risk/field-type-analysis/{client_id}")
async def get_field_type_analysis(client_id: str):
    """
    Get field types analysis for bar chart
    """
    try:
        agent = ModularRiskAssessmentAgent()

        conn = agent.get_db_connection()

        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                field_type,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
            GROUP BY field_type 
            ORDER BY count DESC
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "field_types": [
                {"type": row["field_type"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/privacy-violation-types/{client_id}")
async def get_privacy_violation_types(client_id: str):
    """
    Get privacy implications for pie chart
    """
    try:
        agent = ModularRiskAssessmentAgent()

        conn = agent.get_db_connection()

        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                privacy_implications,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
                AND privacy_implications IS NOT NULL
            GROUP BY privacy_implications 
            ORDER BY count DESC
        """, (client_id,))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "privacy_violations": [
                {"implication": row["privacy_implications"], "count": row["count"]} 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}



@app.get("/risk/risk-matrix-data/{client_id}")
async def get_risk_matrix_data(client_id: str):
    """
    Get risk matrix data (likelihood vs impact)
    """
    try:
        agent = ModularRiskAssessmentAgent()

        conn = agent.get_db_connection()

        cur = conn.cursor()

        cur.execute("""
            SELECT
                risk_level as likelihood,
                sensitivity as impact,
                COUNT(*) as count
            FROM scan_findings
            WHERE client_id = %s
            AND risk_level IS NOT NULL
            AND sensitivity IS NOT NULL
            GROUP BY risk_level, sensitivity
            ORDER BY count DESC
        """, (client_id,))

        results = cur.fetchall()
        conn.close()

        # Helper function to normalize values
        def normalize_value(value):
            if not value:
                return None
            normalized = str(value).lower()
            if normalized in ['low', 'medium', 'high']:
                return normalized.capitalize()  # Returns 'Low', 'Medium', 'High'
            return None

        # Filter and normalize the results
        normalized_results = []
        for row in results:
            likelihood = normalize_value(row["likelihood"])
            impact = normalize_value(row["impact"])

            # Only include entries with valid normalized values
            if likelihood and impact:
                normalized_results.append({
                    "likelihood": likelihood,
                    "impact": impact,
                    "count": row["count"]
                })

        return {
            "risk_matrix": normalized_results
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/trend-analysis/{client_id}")
async def get_trend_analysis(client_id: str, days: int = 30):
    """
    Get risk trends over time for line chart
    """
    try:
        agent = ModularRiskAssessmentAgent()

        conn = agent.get_db_connection()

        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                DATE(scan_timestamp::timestamp) as scan_date,
                COUNT(*) as total_findings,
                COUNT(CASE WHEN LOWER(risk_level) = 'high' THEN 1 END) as high_risk_findings,
                COUNT(CASE WHEN LOWER(risk_level) = 'medium' THEN 1 END) as medium_risk_findings,
                COUNT(CASE WHEN LOWER(risk_level) = 'low' THEN 1 END) as low_risk_findings
            FROM scan_findings 
            WHERE client_id = %s 
                AND scan_timestamp::timestamp >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(scan_timestamp::timestamp) 
            ORDER BY scan_date
        """, (client_id, days))
        
        results = cur.fetchall()
        conn.close()
        
        return {
            "trend_analysis": [
                {
                    "date": str(row["scan_date"]),
                    "total_findings": row["total_findings"],
                    "high_risk": row["high_risk_findings"],
                    "medium_risk": row["medium_risk_findings"],
                    "low_risk": row["low_risk_findings"]
                } 
                for row in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/comprehensive-dashboard/{client_id}")
async def get_comprehensive_dashboard(client_id: str):
    """
    Get all dashboard metrics in one call
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Total counts
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM data_stores WHERE client_id = %s) as total_data_stores,
                (SELECT COUNT(*) FROM sdes WHERE client_id = %s) as total_sdes,
                (SELECT COUNT(*) FROM scan_findings WHERE client_id = %s) as total_findings,
                (SELECT COUNT(*) FROM scan_findings WHERE client_id = %s AND risk_level = 'High') as high_risk_findings,
                (SELECT AVG(confidence_score) FROM scan_findings WHERE client_id = %s) as avg_confidence,
                (SELECT COUNT(*) FROM sdes WHERE client_id = %s) as total_sdes_count
        """, (client_id, client_id, client_id, client_id, client_id, client_id))
        
        summary = cur.fetchone()
        
        # Data source types
        cur.execute("""
            SELECT store_type, COUNT(*) as count
            FROM data_stores WHERE client_id = %s 
            GROUP BY store_type ORDER BY count DESC
        """, (client_id,))
        data_sources = cur.fetchall()
        
        # Risk distribution
        cur.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM scan_findings WHERE client_id = %s 
            GROUP BY risk_level ORDER BY count DESC
        """, (client_id,))
        risk_distribution = cur.fetchall()
        
        # Sensitivity categories
        cur.execute("""
            SELECT sensitivity, COUNT(*) as count
            FROM scan_findings WHERE client_id = %s 
            GROUP BY sensitivity ORDER BY count DESC
        """, (client_id,))
        sensitivity_categories = cur.fetchall()
        

        
        conn.close()
        
        return {
            "summary": {
                "total_data_stores": summary["total_data_stores"],
                "total_sdes": summary["total_sdes"],
                "total_findings": summary["total_findings"],
                "high_risk_findings": summary["high_risk_findings"],
                "avg_confidence": float(summary["avg_confidence"]) if summary["avg_confidence"] else 0,
                "total_sdes_count": summary["total_sdes_count"]
            },
            "data_source_types": [{"type": row["store_type"], "count": row["count"]} for row in data_sources],
            "risk_distribution": [{"level": row["risk_level"], "count": row["count"]} for row in risk_distribution],
            "sensitivity_categories": [{"category": row["sensitivity"], "count": row["count"]} for row in sensitivity_categories],

        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/risk/comprehensive-risk-assessment/{client_id}")
async def get_comprehensive_risk_assessment(client_id: str):
    """
    Get all risk assessment metrics in one call
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # SDE categories - using scan_findings table
        cur.execute("""
            SELECT sde_category, COUNT(*) as count
            FROM scan_findings WHERE client_id = %s 
            GROUP BY sde_category ORDER BY count DESC
        """, (client_id,))
        sde_categories = cur.fetchall()
        
        # Detection methods
        cur.execute("""
            SELECT detection_method, COUNT(*) as count
            FROM scan_findings WHERE client_id = %s 
            GROUP BY detection_method ORDER BY count DESC
        """, (client_id,))
        detection_methods = cur.fetchall()
        
        # Confidence distribution - using confidence_score
        cur.execute("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.8 THEN 'High'
                    WHEN confidence_score >= 0.5 THEN 'Medium'
                    ELSE 'Low'
                END as confidence_level,
                COUNT(*) as count
            FROM scan_findings WHERE client_id = %s 
            GROUP BY 
                CASE 
                    WHEN confidence_score >= 0.8 THEN 'High'
                    WHEN confidence_score >= 0.5 THEN 'Medium'
                    ELSE 'Low'
                END 
            ORDER BY count DESC
        """, (client_id,))
        confidence_distribution = cur.fetchall()
        
        # Field types
        cur.execute("""
            SELECT field_type, COUNT(*) as count
            FROM scan_findings WHERE client_id = %s 
            GROUP BY field_type ORDER BY count DESC
        """, (client_id,))
        field_types = cur.fetchall()
        
        # Privacy violations
        cur.execute("""
            SELECT privacy_implications, COUNT(*) as count
            FROM scan_findings WHERE client_id = %s AND privacy_implications IS NOT NULL
            GROUP BY privacy_implications ORDER BY count DESC
        """, (client_id,))
        privacy_violations = cur.fetchall()
        

        
        # Risk matrix - with proper filtering and normalization
        cur.execute("""
            SELECT risk_level as likelihood, sensitivity as impact, COUNT(*) as count
            FROM scan_findings
            WHERE client_id = %s
            AND risk_level IS NOT NULL
            AND sensitivity IS NOT NULL
            GROUP BY risk_level, sensitivity
            ORDER BY count DESC
        """, (client_id,))
        risk_matrix_raw = cur.fetchall()

        # Helper function to normalize values
        def normalize_value(value):
            if not value:
                return None
            normalized = str(value).lower()
            if normalized in ['low', 'medium', 'high']:
                return normalized.capitalize()  # Returns 'Low', 'Medium', 'High'
            return None

        # Filter and normalize the risk matrix results
        risk_matrix = []
        for row in risk_matrix_raw:
            likelihood = normalize_value(row["likelihood"])
            impact = normalize_value(row["impact"])

            # Only include entries with valid normalized values
            if likelihood and impact:
                risk_matrix.append({
                    "likelihood": likelihood,
                    "impact": impact,
                    "count": row["count"]
                })
        
        conn.close()
        
        return {
            "sde_categories": [{"category": row["sde_category"], "count": row["count"]} for row in sde_categories],
            "detection_methods": [{"method": row["detection_method"], "count": row["count"]} for row in detection_methods],
            "confidence_distribution": [{"level": row["confidence_level"], "count": row["count"]} for row in confidence_distribution],
            "field_types": [{"type": row["field_type"], "count": row["count"]} for row in field_types],
            "privacy_violations": [{"implication": row["privacy_implications"], "count": row["count"]} for row in privacy_violations],
            "risk_matrix": risk_matrix
        }
    except Exception as e:
        return {"error": str(e)}

class ReportRequest(BaseModel):
    client_id: str
    format: str = 'pdf'  # 'pdf', or 'html'
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None

@app.post("/risk/report")
async def generate_risk_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate and return the latest risk assessment report for a client.
    Format can be 'pdf' or 'html'.
    """
    agent = ModularReportGenerationAgent(client_id=request.client_id)
    # Set user info if provided
    if request.name:
        agent.name = request.name
    if request.email:
        agent.email = request.email
    if request.company:
        agent.company = request.company
    # Always generate the latest report
    report_result = agent.generate_risk_assessment_report()
    status = report_result.get('status')
    if status == 'no_data':
        return JSONResponse({
            'status': 'error',
            'message': 'please analyse risk before report',
            'client_id': request.client_id
        }, status_code=404)
    if request.format == 'pdf':
        pdf_result = agent.generate_pdf_report()  # Use PDF generation with charts
        if pdf_result and not pdf_result.startswith('Error'):
            # Use client name for filename instead of ID
            client_name = request.company or request.name or request.client_id
            safe_client_name = agent._sanitize_filename(client_name)
            
            # Add background task to delete the temporary file after response is sent
            def cleanup_temp_file(file_path: str):
                try:
                    import os
                    import time
                    # Wait a bit to ensure file is sent
                    time.sleep(1)
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        logger.info(f"Temporary PDF file deleted: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary PDF file {file_path}: {e}")
            
            # Add cleanup task to background tasks
            background_tasks.add_task(cleanup_temp_file, pdf_result)
            
            # Return the file response
            return FileResponse(
                pdf_result, 
                filename=f"risk_report_{safe_client_name}.pdf", 
                media_type="application/pdf"
            )
        else:
            return JSONResponse({'status': 'error', 'message': 'Failed to generate PDF report.'}, status_code=500)
    elif request.format == 'html':
        html_file = report_result['generated_reports']['html_preview']
        if html_file and not html_file.startswith('Error'):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content, status_code=200)
        else:
            return JSONResponse({'status': 'error', 'message': 'Failed to generate HTML report.'}, status_code=500)
    else:
        return JSONResponse({'status': 'error', 'message': 'Invalid format. Use pdf or html.'}, status_code=400)

@app.post("/risk/compliance-report")
async def generate_compliance_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate a comprehensive compliance report
    """
    try:
        # Initialize the report generation agent
        agent = ModularReportGenerationAgent(client_id=request.client_id)
        
        # Set user information if provided
        if request.name:
            agent.name = request.name
        if request.email:
            agent.email = request.email
        if request.company:
            agent.company = request.company
        
        # Generate the compliance report (PDF only)
        report_filepath = agent.generate_compliance_report()
        
        # Check if report generation was successful
        if report_filepath.startswith('Error'):
            raise HTTPException(status_code=500, detail=f"Compliance report generation failed: {report_filepath}")
        
        # Use client name for filename instead of ID
        client_name = request.company or request.name or request.client_id
        safe_client_name = agent._sanitize_filename(client_name)
        
        # Add background task to delete the temporary file after response is sent
        def cleanup_temp_file(file_path: str):
            try:
                import os
                import time
                # Wait a bit to ensure file is sent
                time.sleep(1)
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.info(f"Temporary compliance PDF file deleted: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary compliance PDF file {file_path}: {e}")
        
        # Add cleanup task to background tasks
        background_tasks.add_task(cleanup_temp_file, report_filepath)
        
        # Return the file response
        return FileResponse(
            report_filepath, 
            filename=f"compliance_report_{safe_client_name}.pdf", 
            media_type="application/pdf"
        )
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance report generation failed: {str(e)}")

@app.post("/risk/cleanup")
async def cleanup_reports():
    """
    Clean up all report files - useful for Docker container maintenance
    """
    try:
        agent = ModularReportGenerationAgent()
        agent.cleanup_all_session_files()
        return JSONResponse({'status': 'success', 'message': 'All report files cleaned up'})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': f'Cleanup failed: {str(e)}'}, status_code=500)

@app.post("/risk/cleanup-html")
async def cleanup_html_files(max_age_minutes: int = 5):
    """
    Clean up HTML files older than specified age - useful for Docker container maintenance
    """
    try:
        agent = ModularReportGenerationAgent()
        agent.cleanup_old_html_files(max_age_minutes)
        return JSONResponse({'status': 'success', 'message': f'HTML files older than {max_age_minutes} minutes cleaned up'})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': f'HTML cleanup failed: {str(e)}'}, status_code=500)

@app.get("/connections/exists/{client_id}")
def connections_exist(client_id: str):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM client_connections WHERE client_id = %s", (client_id,))
        count = cursor.fetchone()[0]
        return {"exists": count > 0}
    finally:
        cursor.close()
        conn.close()

@app.post("/risk/database-report")
async def generate_database_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate a comprehensive database infrastructure report
    """
    try:
        # Initialize the report generation agent
        agent = ModularReportGenerationAgent(client_id=request.client_id)
        
        # Set user information if provided
        if request.name:
            agent.name = request.name
        if request.email:
            agent.email = request.email
        if request.company:
            agent.company = request.company
        
        # Generate the database report (PDF only)
        report_filepath = agent.generate_database_report()
        
        # Check if report generation was successful
        if report_filepath.startswith('Error'):
            raise HTTPException(status_code=500, detail=f"Database report generation failed: {report_filepath}")
        
        # Use client name for filename instead of ID
        client_name = request.company or request.name or request.client_id
        safe_client_name = agent._sanitize_filename(client_name)
        
        # Add background task to delete the temporary file after response is sent
        def cleanup_temp_file(file_path: str):
            try:
                import os
                import time
                # Wait a bit to ensure file is sent
                time.sleep(1)
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.info(f"Temporary database PDF file deleted: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary database PDF file {file_path}: {e}")
        
        # Add cleanup task to background tasks
        background_tasks.add_task(cleanup_temp_file, report_filepath)
        
        # Return the file response
        return FileResponse(
            report_filepath,
            filename=f"database_report_{safe_client_name}.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        logger.error(f"Error generating database report: {e}")
        raise HTTPException(status_code=500, detail=f"Database report generation failed: {str(e)}")

@app.get("/risk/model-registry-metrics/{client_id}")
async def get_model_registry_metrics(client_id: str):
    """
    Get model registry metrics for a specific client
    Returns model inventory statistics including total models, active/inactive counts, and provider breakdown
    """
    try:
        logger.info(f"Fetching model registry metrics for client_id: {client_id}")
        
        # Step 1: Initialize agent and get connection
        try:
            agent = ModularRiskAssessmentAgent()
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")
        
        try:
            conn = agent.get_db_connection()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get database connection: {str(e)}")
        
        try:
            cursor = conn.cursor()
            logger.info("Cursor created successfully")
        except Exception as e:
            logger.error(f"Error creating cursor: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create cursor: {str(e)}")
        
        # Step 2: Debug queries
        try:
            cursor.execute("SELECT DISTINCT client_id FROM model_inventory LIMIT 5")
            rows = cursor.fetchall()
            # Handle both tuple and dict return types
            if rows and isinstance(rows[0], dict):
                existing_client_ids = [row.get('client_id') for row in rows]
            else:
                existing_client_ids = [row[0] for row in rows]
            logger.info(f"Existing client_ids in model_inventory: {existing_client_ids}")
        except Exception as e:
            logger.error(f"Error in debug query for existing client_ids: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get existing client_ids: {str(e)}")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM model_inventory WHERE client_id = %s", (client_id,))
            specific_count = cursor.fetchone()
            logger.info(f"Count for specific client_id {client_id}: {specific_count}")
        except Exception as e:
            logger.error(f"Error in debug query for specific client count: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get specific client count: {str(e)}")
        
        # Step 3: Get total models count
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_models
                FROM model_inventory 
                WHERE client_id = %s
            """, (client_id,))
            total_result = cursor.fetchone()
            logger.info(f"Total models query result: {total_result}")
            if total_result is None:
                total_models = 0
            else:
                # Handle both tuple and dict return types
                if isinstance(total_result, dict):
                    total_models = total_result.get('total_models', 0) or 0
                else:
                    total_models = total_result[0] or 0
            logger.info(f"Total models count: {total_models}")
        except Exception as e:
            logger.error(f"Error in total models query: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get total models: {str(e)}")
        
        # Step 4: Get active models count
        try:
            cursor.execute("""
                SELECT COUNT(*) as active_models
                FROM model_inventory 
                WHERE client_id = %s 
                AND created_at >= NOW() - INTERVAL '30 days'
            """, (client_id,))
            active_result = cursor.fetchone()
            logger.info(f"Active models query result: {active_result}")
            if active_result is None:
                active_models = 0
            else:
                # Handle both tuple and dict return types
                if isinstance(active_result, dict):
                    active_models = active_result.get('active_models', 0) or 0
                else:
                    active_models = active_result[0] or 0
            logger.info(f"Active models count: {active_models}")
        except Exception as e:
            logger.error(f"Error in active models query: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get active models: {str(e)}")
        
        # Step 5: Calculate inactive models
        try:
            inactive_models = total_models - active_models
            logger.info(f"Inactive models calculated: {inactive_models}")
        except Exception as e:
            logger.error(f"Error calculating inactive models: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to calculate inactive models: {str(e)}")
        
        # Step 6: Get provider breakdown
        try:
            cursor.execute("""
                SELECT 
                    provider_name,
                    COUNT(*) as model_count
                FROM model_inventory 
                WHERE client_id = %s
                GROUP BY provider_name
                ORDER BY model_count DESC
            """, (client_id,))
            rows = cursor.fetchall()
            # Handle both tuple and dict return types
            if rows and isinstance(rows[0], dict):
                provider_breakdown = [
                    {"provider_name": row.get('provider_name'), "model_count": row.get('model_count')} 
                    for row in rows
                ]
            else:
                provider_breakdown = [
                    {"provider_name": row[0], "model_count": row[1]} 
                    for row in rows
                ]
            logger.info(f"Provider breakdown: {provider_breakdown}")
        except Exception as e:
            logger.error(f"Error in provider breakdown query: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get provider breakdown: {str(e)}")
        
        # Step 7: Get recent models
        try:
            cursor.execute("""
                SELECT 
                    model_name,
                    provider_name,
                    created_at
                FROM model_inventory 
                WHERE client_id = %s 
                AND created_at >= NOW() - INTERVAL '7 days'
                ORDER BY created_at DESC
                LIMIT 5
            """, (client_id,))
            rows = cursor.fetchall()
            # Handle both tuple and dict return types
            if rows and isinstance(rows[0], dict):
                recent_models = [
                    {
                        "model_name": row.get('model_name'),
                        "provider_name": row.get('provider_name'), 
                        "created_at": row.get('created_at').isoformat() if row.get('created_at') else None
                    }
                    for row in rows
                ]
            else:
                recent_models = [
                    {
                        "model_name": row[0],
                        "provider_name": row[1], 
                        "created_at": row[2].isoformat() if row[2] else None
                    }
                    for row in rows
                ]
            logger.info(f"Recent models: {recent_models}")
        except Exception as e:
            logger.error(f"Error in recent models query: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get recent models: {str(e)}")
        
        # Step 8: Close connections
        try:
            cursor.close()
            conn.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
            # Don't raise here as we already have the data
        
        # Step 9: Return response
        try:
            response = {
                "model_metrics": {
                    "total_models": total_models,
                    "active_models": active_models,
                    "inactive_models": inactive_models,
                    "provider_breakdown": provider_breakdown,
                    "recent_models": recent_models
                }
            }
            logger.info(f"Returning response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error creating response: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create response: {str(e)}")
        
    except HTTPException:
        # Re-raise HTTPExceptions as they already have proper detail
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching model registry metrics for client {client_id}: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch model registry metrics: {str(e)}")

@app.get("/risk/findings-by-data-store/{client_id}")
async def get_findings_by_data_store(client_id: str):
    """
    Get findings count grouped by data store for a specific client.
    
    Returns:
        {
            "findings_by_store": [
                {"store_name": "Primary PostgreSQL DB", "finding_count": 156}
            ]
        }
    """
    logger.info(f"Getting findings by data store for client_id: {client_id}")
    
    try:
        # Initialize agent and get connection
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Execute query to get findings by data store
        cursor.execute("""
            SELECT 
                ds.store_name, 
                COUNT(*) as finding_count 
            FROM scan_findings sf 
            JOIN scans s ON sf.scan_id = s.scan_id 
            JOIN data_stores ds ON s.store_id = ds.store_id 
            WHERE sf.client_id = %s 
            GROUP BY ds.store_name 
            ORDER BY finding_count DESC
        """, (client_id,))
        
        rows = cursor.fetchall()
        findings_by_store = []
        
        for row in rows:
            if isinstance(row, dict):
                findings_by_store.append({
                    "store_name": row.get('store_name'),
                    "finding_count": row.get('finding_count', 0)
                })
            else:
                findings_by_store.append({
                    "store_name": row[0],
                    "finding_count": row[1]
                })
        
        logger.info(f"Found {len(findings_by_store)} data stores with findings")
        
        response = {
            "findings_by_store": findings_by_store
        }
        
        cursor.close()
        conn.close()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting findings by data store for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get findings by data store: {str(e)}")

@app.get("/risk/regex-patterns-matched/{client_id}")
async def get_regex_patterns_matched(client_id: str):
    """
    Get regex patterns matched and their counts for a specific client.
    
    Returns:
        {
            "pattern_matches": [
                {"pattern_matched": "credit_card_pattern", "count": 89}
            ]
        }
    """
    logger.info(f"Getting regex patterns matched for client_id: {client_id}")
    
    try:
        # Initialize agent and get connection
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Execute query to get regex patterns matched and their counts
        cursor.execute("""
            SELECT 
                pattern_matched,
                COUNT(*) as count
            FROM scan_findings 
            WHERE client_id = %s 
            AND pattern_matched IS NOT NULL
            GROUP BY pattern_matched 
            ORDER BY count DESC
        """, (client_id,))
        
        rows = cursor.fetchall()
        pattern_matches = []
        
        for row in rows:
            if isinstance(row, dict):
                pattern_matches.append({
                    "pattern_matched": row.get('pattern_matched'),
                    "count": row.get('count', 0)
                })
            else:
                pattern_matches.append({
                    "pattern_matched": row[0],
                    "count": row[1]
                })
        
        logger.info(f"Found {len(pattern_matches)} regex patterns matched")
        
        response = {
            "pattern_matches": pattern_matches
        }
        
        cursor.close()
        conn.close()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting regex patterns matched for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get regex patterns matched: {str(e)}")

@app.get("/risk/new-findings-per-scan/{client_id}")
async def get_new_findings_per_scan(client_id: str):
    """
    Get new findings per scan for a specific client.
    
    Returns:
        {
            "findings_per_scan": [
                {"scan_id": "SCAN_001", "scan_timestamp": "2024-08-01T09:00:00Z", "new_findings": 23}
            ]
        }
    """
    logger.info(f"Getting new findings per scan for client_id: {client_id}")
    
    try:
        # Initialize agent and get connection
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Execute query to get new findings per scan
        cursor.execute("""
            SELECT 
                scan_id, 
                scan_timestamp, 
                COUNT(*) as new_findings 
            FROM scan_findings
            WHERE client_id = %s
            GROUP BY scan_id, scan_timestamp
            ORDER BY scan_timestamp DESC
            LIMIT 10
        """, (client_id,))
        
        rows = cursor.fetchall()
        findings_per_scan = []
        
        for row in rows:
            if isinstance(row, dict):
                findings_per_scan.append({
                    "scan_id": row.get('scan_id'),
                    "scan_timestamp": row.get('scan_timestamp'),
                    "new_findings": row.get('new_findings', 0)
                })
            else:
                findings_per_scan.append({
                    "scan_id": row[0],
                    "scan_timestamp": row[1],
                    "new_findings": row[2]
                })
        
        logger.info(f"Found {len(findings_per_scan)} scan records with findings")
        
        response = {
            "findings_per_scan": findings_per_scan
        }
        
        cursor.close()
        conn.close()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting new findings per scan for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get new findings per scan: {str(e)}")

@app.get("/risk/connection-status/{client_id}")
async def get_connection_status(client_id: str):
    """
    Get connection status overview for a specific client.
    
    Returns:
        {
            "connection_status": [
                {"connection_status": "Active", "count": 89},
                {"connection_status": "Inactive", "count": 23},
                {"connection_status": "Failed", "count": 12},
                {"connection_status": "Pending", "count": 7}
            ]
        }
    """
    logger.info(f"Getting connection status for client_id: {client_id}")
    
    try:
        # Initialize agent and get connection
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Execute query to get connection status
        cursor.execute("""
            SELECT 
                cc.connections_type as connection_status,
                COUNT(*) as count
            FROM client_connections cc
            WHERE cc.client_id = %s
            GROUP BY cc.connections_type
        """, (client_id,))
        
        rows = cursor.fetchall()
        connection_status = []
        
        for row in rows:
            if isinstance(row, dict):
                connection_status.append({
                    "connection_status": row.get('connection_status'),
                    "count": row.get('count', 0)
                })
            else:
                connection_status.append({
                    "connection_status": row[0],
                    "count": row[1]
                })
        
        logger.info(f"Found {len(connection_status)} connection status records")
        
        response = {
            "connection_status": connection_status
        }
        
        cursor.close()
        conn.close()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting connection status for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection status: {str(e)}")

@app.get("/risk/risk-findings/{client_id}")
async def get_risk_findings(
    client_id: str,
    risk_level: Optional[str] = None,
    sde_category: Optional[str] = None,
    data_value_search: Optional[str] = None,
    sensitivity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get comprehensive risk findings with filtering options.
    Returns finding_id, data_value, sensitivity, finding_type, sde_category, 
    risk_level, confidence_score, scan_timestamp
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Build dynamic WHERE clause
        where_conditions = ["client_id = %s"]
        params = [client_id]
        
        # Add risk_level filter
        if risk_level:
            where_conditions.append("LOWER(risk_level) = %s")
            params.append(risk_level.lower())
        
        # Add sde_category filter
        if sde_category:
            where_conditions.append("LOWER(sde_category) = %s")
            params.append(sde_category.lower())
            
        # Add sensitivity filter
        if sensitivity:
            where_conditions.append("LOWER(sensitivity) = %s")
            params.append(sensitivity.lower())
                
        # Add data_value search filter
        if data_value_search:
            where_conditions.append("LOWER(data_value) LIKE %s")
            params.append(f"%{data_value_search.lower()}%")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                finding_id,
                data_value,
                sensitivity,
                finding_type,
                sde_category,
                risk_level,
                confidence_score,
                scan_timestamp
            FROM scan_findings 
            WHERE {where_clause}
            ORDER BY 
                CASE 
                    WHEN sde_category IS NULL OR sde_category = '' OR LOWER(sde_category) IN ('unknown', 'unk', 'n/a', 'none') THEN 1
                    ELSE 0
                END,
                finding_id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cur.execute(query, tuple(params))
        findings = []
        
        for row in cur.fetchall():
            findings.append({
                "finding_id": row["finding_id"],
                "data_value": row["data_value"] or "N/A",
                "sensitivity": row["sensitivity"] or "Unknown",
                "finding_type": row["finding_type"] or "Unknown",
                "sde_category": row["sde_category"] or "Unknown",
                "risk_level": row["risk_level"] or "Unknown",
                "confidence_score": row["confidence_score"] or 0.0,
                "scan_timestamp": row["scan_timestamp"] or "Unknown"
            })
        
        # Get total count for pagination info
        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM scan_findings 
            WHERE {where_clause}
        """
        cur.execute(count_query, tuple(params[:-2]))  # Exclude LIMIT and OFFSET
        total_count = cur.fetchone()["total_count"]
        
        conn.close()
        
        return {
            "client_id": client_id,
            "findings": findings,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "filters_applied": {
                "risk_level": risk_level,
                "sde_category": sde_category,
                "data_value_search": data_value_search
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching risk findings for client {client_id}: {e}")
        return {
            "client_id": client_id,
            "findings": [],
            "total_count": 0,
            "error": str(e)
        }

@app.get("/risk/sde-names/{client_id}")
async def get_sde_names(client_id: str):
    """
    Get all SDE names (pattern names) for a specific client from client_selected_sdes table
    and distinct SDE categories from scan_findings table that are not null, unknown, or numbers.
    Returns both lists of unique SDE names and categories.
    """
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get all unique pattern names for the client from client_selected_sdes
        cur.execute("""
            SELECT DISTINCT pattern_name 
            FROM client_selected_sdes 
            WHERE client_id = %s 
            ORDER BY pattern_name
        """, (client_id,))
        
        rows = cur.fetchall()
        sde_names = [row["pattern_name"] for row in rows if row["pattern_name"]]
        
        # Get distinct SDE categories from scan_findings that are not null, unknown, or numbers
        cur.execute("""
            SELECT DISTINCT sde_category 
            FROM scan_findings 
            WHERE client_id = %s 
              AND sde_category IS NOT NULL 
              AND sde_category != ''
              AND LOWER(sde_category) NOT IN ('unknown', 'unk', 'n/a', 'none')
              AND sde_category ~ '^[^0-9]*$'  -- Exclude categories that are numbers
            ORDER BY sde_category
        """, (client_id,))
        
        category_rows = cur.fetchall()
        sde_categories = [row["sde_category"] for row in category_rows if row["sde_category"]]
        
        conn.close()
        
        return {
            "client_id": client_id,
            "sde_names": sde_names,
            "sde_categories": sde_categories,
            "total_sdes": len(sde_names),
            "total_categories": len(sde_categories)
        }
        
    except Exception as e:
        logger.error(f"Error fetching SDE names for client {client_id}: {e}")
        return {
            "client_id": client_id,
            "sde_names": [],
            "sde_categories": [],
            "total_sdes": 0,
            "total_categories": 0,
            "error": str(e)
        }

# ============================================================================
# SDE API ENDPOINTS (from sdeapi.py)
# ============================================================================

@app.get("/industry-classifications")
def get_industry_classifications():
    conn = None
    cur = None
    try:
        # Check if DB_URL is set
        if not DB_URL:
            raise HTTPException(status_code=500, detail="DB_URL environment variable not set")
        
        print(f"Connecting to database with URL: {DB_URL}")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT industry_classification FROM isde_catalogue;")
        rows = cur.fetchall()
        industries = [row[0] for row in rows if row[0]]
        print(f"Found industries: {industries}")
        return {"industries": industries}
    except Exception as e:
        print(f"Error in industry-classifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.get("/get-sde")
def get_sde(selected_industry: str = Query(...)):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, sde_key, name, data_type, sensitivity, regex, classification_level, industry_classification
            FROM isde_catalogue
            WHERE industry_classification = %s OR industry_classification = 'all_industries'
        """, (selected_industry,))
        rows = cur.fetchall()
        if not rows:
            return {"message": "This industry doesn't have predefined sdes yet", "sdes": []}
        sdes = [
            {
                "id": row[0],
                "sde_key": row[1],
                "name": row[2],
                "data_type": row[3],
                "sensitivity": row[4],
                "regex": row[5],
                "classification": row[6],
                "industry_classification": row[7],
            }
            for row in rows
        ]
        return {"sdes": sdes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
@app.post("/store-client-sdes")
def store_client_sdes(client_data: ClientSelectedSDEModel):
    """
    Store selected SDEs for a client in client_selected_sdes table
    Handles both new and existing SDEs properly
    """
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        from datetime import datetime
        selected_at = datetime.now()
        cur.execute("""
            SELECT pattern_name FROM client_selected_sdes 
            WHERE client_id = %s
        """, (client_data.client_id,))
        existing_sdes = {row[0] for row in cur.fetchall()}
        stored_sdes = []
        new_added_count = 0
        updated_count = 0
        for sde in client_data.sdes:
            if sde.name not in existing_sdes:
                # INSERT only if SDE doesn't exist
                cur.execute(
                    """
                    INSERT INTO client_selected_sdes 
                    (client_id, pattern_name, sensitivity, protection_method, selected_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (client_data.client_id, sde.name, sde.sensitivity, sde.classification_level, selected_at)
                )
                new_id = cur.fetchone()[0]
                stored_sdes.append({
                    "id": new_id,
                    "pattern_name": sde.name,
                    "sensitivity": sde.sensitivity,
                    "protection_method": sde.classification_level,
                    "action": "added"
                })
                new_added_count += 1
            else:
                # SDE already exists, just update timestamp and properties
                cur.execute(
                    """
                    UPDATE client_selected_sdes 
                    SET selected_at = %s, sensitivity = %s, protection_method = %s
                    WHERE client_id = %s AND pattern_name = %s
                    """,
                    (selected_at, sde.sensitivity, sde.classification_level, client_data.client_id, sde.name)
                )
                stored_sdes.append({
                    "pattern_name": sde.name,
                    "sensitivity": sde.sensitivity,
                    "protection_method": sde.classification_level,
                    "action": "updated"
                })
                updated_count += 1
        conn.commit()
        return {
            "status": "success", 
            "client_id": client_data.client_id,
            "stored_sdes": stored_sdes,
            "total_processed": len(stored_sdes),
            "new_added": new_added_count,
            "updated": updated_count,
            "existing_count_before": len(existing_sdes),
            "total_after": len(existing_sdes) + new_added_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
@app.delete("/remove-client-sdes")
def remove_client_sdes(client_id: str, pattern_names: List[str]):
    """
    Remove specific SDEs from client_selected_sdes table
    """
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        removed_count = 0
        for pattern_name in pattern_names:
            cur.execute(
                """
                DELETE FROM client_selected_sdes 
                WHERE client_id = %s AND pattern_name = %s
                """,
                (client_id, pattern_name)
            )
            removed_count += cur.rowcount
        
        conn.commit()
        return {
            "status": "success",
            "client_id": client_id,
            "removed_count": removed_count,
            "pattern_names": pattern_names
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
    

@app.post("/add-sde")
def add_sde(sde: AddSDEModel):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        sde_key = "sde" + sde.name
        cur.execute(
            """
            INSERT INTO isde_catalogue (sde_key, name, data_type, sensitivity, regex, classification, industry_classification)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (sde_key, sde.name, sde.data_type, sde.sensitivity, sde.regex, sde.classification, sde.selected_industry)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"status": "success", "id": new_id, "sde_key": sde_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# SDE Removal Endpoints
def verify_client_exists(client_id: str, conn) -> bool:
    """Verify if client exists in the database"""
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT client_id FROM client_prof WHERE client_id = %s", (client_id,))
            return cur.fetchone() is not None
        finally:
            cur.close()
    except Exception as e:
        logger.error(f"Error verifying client: {e}")
        return False

def get_client_sde_count(client_id: str, conn) -> int:
    """Get count of client's selected SDEs"""
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) as count FROM client_selected_sdes WHERE client_id = %s", (client_id,))
            result = cur.fetchone()
            return result[0] if result else 0
        finally:
            cur.close()
    except Exception as e:
        logger.error(f"Error getting SDE count: {e}")
        return 0
# the sdes will be deleted specifically
@app.delete("/sdes/remove", response_model=RemoveSDEResponse)
async def remove_client_sde(request: RemoveSDERequest):
    """
    Remove a specific SDE from client's selections

    Request Body:
    {
        "client_id": "client_123",
        "pattern_name": "email_address"
    }
    """
    logger.info(f"Removing SDEs '{request.pattern_name}' for client '{request.client_id}'")

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Verify client exists
        if not verify_client_exists(request.client_id, conn):
            raise HTTPException(
                status_code=404,
                detail=f"Client '{request.client_id}' not found"
            )

        # Check if the SDE selection exists
        cur.execute(
            """SELECT id FROM client_selected_sdes
               WHERE client_id = %s AND pattern_name = %s""",
            (request.client_id, request.pattern_name)
        )

        if not cur.fetchone():
            raise HTTPException(
                status_code=404,
                detail=f"SDE '{request.pattern_name}' not found in client's selections"
            )

        # Remove the specific SDE
        cur.execute(
            """DELETE FROM client_selected_sdes
               WHERE client_id = %s AND pattern_name = %s""",
            (request.client_id, request.pattern_name)
        )

        conn.commit()

        logger.info(f"Successfully removed SDE '{request.pattern_name}' for client '{request.client_id}'")

        return RemoveSDEResponse(
            status="success",
            message=f"Successfully removed SDE '{request.pattern_name}' from client selections",
            client_id=request.client_id,
            removed_pattern=request.pattern_name,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except psycopg2.IntegrityError as e:
        logger.warning(f"Foreign key constraint violation when removing SDE '{request.pattern_name}' for client '{request.client_id}': {e}")
        if 'conn' in locals():
            conn.rollback()

        # Check how many scan findings reference this SDE
        try:
            cur.execute(
                """SELECT COUNT(*) as finding_count
                   FROM scan_findings
                   WHERE client_id = %s AND pattern_matched = %s""",
                (request.client_id, request.pattern_name)
            )
            finding_count = cur.fetchone()[0] if cur.fetchone() else 0
        except:
            finding_count = 0

        # Extract more specific error information
        error_detail = str(e)
        if "foreign key constraint" in error_detail.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "constraint_violation",
                    "message": f"Cannot delete SDE '{request.pattern_name}' because it is referenced by {finding_count} scan findings.",
                    "suggestion": "Please delete associated scan findings first or contact administrator.",
                    "finding_count": finding_count,
                    "sde_name": request.pattern_name,
                    "client_id": request.client_id
                }
            )
        else:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "database_constraint",
                    "message": f"Cannot delete SDE '{request.pattern_name}' due to database constraints.",
                    "technical_details": error_detail,
                    "sde_name": request.pattern_name,
                    "client_id": request.client_id
                }
            )
    except Exception as e:
        logger.error(f"Database error removing SDE: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.delete("/sdes/clear-all", response_model=ClearAllSDEResponse)
async def clear_all_client_sdes(request: ClearAllSDERequest):
    """
    Clear all SDE selections for a client

    Request Body:
    {
        "client_id": "client_123"
    }
    """
    logger.info(f"Clearing all SDEs for client '{request.client_id}'")

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Verify client exists
        if not verify_client_exists(request.client_id, conn):
            raise HTTPException(
                status_code=404,
                detail=f"Client '{request.client_id}' not found"
            )

        # Get count before deletion for response
        sde_count = get_client_sde_count(request.client_id, conn)

        if sde_count == 0:
            return ClearAllSDEResponse(
                status="success",
                message="No SDE selections found for client",
                client_id=request.client_id,
                cleared_count=0,
                timestamp=datetime.now().isoformat()
            )

        # Clear all SDEs for the client
        cur.execute(
            "DELETE FROM client_selected_sdes WHERE client_id = %s",
            (request.client_id,)
        )

        conn.commit()

        logger.info(f"Successfully cleared {sde_count} SDEs for client '{request.client_id}'")

        return ClearAllSDEResponse(
            status="success",
            message=f"Successfully cleared all {sde_count} SDE selections for client",
            client_id=request.client_id,
            cleared_count=sde_count,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except psycopg2.IntegrityError as e:
        logger.warning(f"Foreign key constraint violation when clearing SDEs for client '{request.client_id}': {e}")
        if 'conn' in locals():
            conn.rollback()

        # Check how many scan findings reference client's SDEs
        try:
            cur.execute(
                """SELECT COUNT(*) as finding_count,
                          COUNT(DISTINCT pattern_matched) as affected_sdes
                   FROM scan_findings sf
                   JOIN client_selected_sdes css ON sf.pattern_matched = css.pattern_name
                   WHERE css.client_id = %s""",
                (request.client_id,)
            )
            result = cur.fetchone()
            finding_count = result[0] if result else 0
            affected_sdes = result[1] if result else 0
        except:
            finding_count = 0
            affected_sdes = 0

        # Extract more specific error information
        error_detail = str(e)
        if "foreign key constraint" in error_detail.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "constraint_violation",
                    "message": f"Cannot delete SDE selections because {affected_sdes} SDEs are referenced by {finding_count} scan findings.",
                    "suggestion": "Please delete associated scan findings first or contact administrator.",
                    "finding_count": finding_count,
                    "affected_sdes": affected_sdes,
                    "client_id": request.client_id
                }
            )
        else:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "database_constraint",
                    "message": "Cannot delete SDE selections due to database constraints.",
                    "technical_details": error_detail,
                    "client_id": request.client_id
                }
            )
    except Exception as e:
        logger.error(f"Database error clearing SDEs: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.delete("/sdes/force-remove", response_model=ForceRemoveSDEResponse)
async def force_remove_client_sde(request: ForceRemoveSDERequest):
    """
    Force remove a specific SDE from client's selections along with associated scan findings

    Request Body:
    {
        "client_id": "client_123",
        "pattern_name": "email_address",
        "force": true,
        "admin_override": false
    }
    """
    logger.info(f"Force removing SDE '{request.pattern_name}' for client '{request.client_id}'")

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Verify client exists
        if not verify_client_exists(request.client_id, conn):
            raise HTTPException(
                status_code=404,
                detail=f"Client '{request.client_id}' not found"
            )

        # Check if the SDE selection exists
        cur.execute(
            """SELECT id FROM client_selected_sdes
               WHERE client_id = %s AND pattern_name = %s""",
            (request.client_id, request.pattern_name)
        )

        if not cur.fetchone():
            raise HTTPException(
                status_code=404,
                detail=f"SDE '{request.pattern_name}' not found in client's selections"
            )

        # Count scan findings that will be deleted
        cur.execute(
            """SELECT COUNT(*) as finding_count
               FROM scan_findings
               WHERE client_id = %s AND pattern_matched = %s""",
            (request.client_id, request.pattern_name)
        )
        finding_count = cur.fetchone()[0] if cur.fetchone() else 0

        # Delete associated scan findings first
        if finding_count > 0:
            cur.execute(
                """DELETE FROM scan_findings
                   WHERE client_id = %s AND pattern_matched = %s""",
                (request.client_id, request.pattern_name)
            )
            logger.info(f"Deleted {finding_count} scan findings for SDE '{request.pattern_name}'")

        # Now remove the SDE selection
        cur.execute(
            """DELETE FROM client_selected_sdes
               WHERE client_id = %s AND pattern_name = %s""",
            (request.client_id, request.pattern_name)
        )

        conn.commit()

        logger.info(f"Successfully force removed SDE '{request.pattern_name}' for client '{request.client_id}' with {finding_count} findings")

        return ForceRemoveSDEResponse(
            status="success",
            message=f"Successfully force removed SDE '{request.pattern_name}' and {finding_count} associated scan findings",
            client_id=request.client_id,
            removed_pattern=request.pattern_name,
            deleted_findings=finding_count,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error force removing SDE: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.get("/sdes/client/{client_id}")
async def get_client_sdes_verification(client_id: str):
    """
    Get current SDE selections for a client (for verification)
    """
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify client exists
        if not verify_client_exists(client_id, conn):
            raise HTTPException(
                status_code=404,
                detail=f"Client '{client_id}' not found"
            )

        # Get client's selected SDEs
        cur.execute(
            """SELECT pattern_name, sensitivity, protection_method, selected_at
               FROM client_selected_sdes
               WHERE client_id = %s
               ORDER BY selected_at DESC""",
            (client_id,)
        )

        sdes = [dict(row) for row in cur.fetchall()]

        return {
            "status": "success",
            "client_id": client_id,
            "selected_sdes": sdes,
            "total_count": len(sdes),
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error getting client SDEs: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.get("/sdes/scan-findings-check/{client_id}")
async def check_sdes_with_scan_findings(client_id: str):
    """
    Check which SDEs have associated scan findings that would prevent deletion
    """
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify client exists
        if not verify_client_exists(client_id, conn):
            raise HTTPException(
                status_code=404,
                detail=f"Client '{client_id}' not found"
            )

        # Get SDEs with scan findings
        cur.execute(
            """SELECT
                css.pattern_name,
                css.sensitivity,
                css.protection_method,
                COUNT(sf.finding_id) as finding_count,
                MAX(sf.scan_timestamp) as last_finding_date
               FROM client_selected_sdes css
               LEFT JOIN scan_findings sf ON css.pattern_name = sf.pattern_matched
                                          AND css.client_id = sf.client_id
               WHERE css.client_id = %s
               GROUP BY css.pattern_name, css.sensitivity, css.protection_method
               ORDER BY finding_count DESC, css.pattern_name""",
            (client_id,)
        )

        sdes_info = []
        for row in cur.fetchall():
            sde_info = dict(row)
            sde_info['can_delete'] = sde_info['finding_count'] == 0
            sde_info['deletion_blocked'] = sde_info['finding_count'] > 0
            sdes_info.append(sde_info)

        # Summary statistics
        total_sdes = len(sdes_info)
        blocked_sdes = sum(1 for sde in sdes_info if sde['deletion_blocked'])
        deletable_sdes = total_sdes - blocked_sdes

        return {
            "status": "success",
            "client_id": client_id,
            "summary": {
                "total_sdes": total_sdes,
                "deletable_sdes": deletable_sdes,
                "blocked_sdes": blocked_sdes
            },
            "sdes": sdes_info,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error checking SDE scan findings: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)