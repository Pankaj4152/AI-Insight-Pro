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

        # Total SDEs - Count from sdes table (SDE definitions)
        try:
            cur.execute("SELECT COUNT(DISTINCT sde_id) AS total_sdes FROM sdes WHERE client_id = %s", (client_id,))
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
            
            if total_sdes > 0:
                risk_score = (scanned_sdes / total_sdes) * 40
                logger.debug(f"Risk score calculation: ({scanned_sdes} / {total_sdes}) * 40 = {risk_score}")
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
            
            # Component 1: Scan coverage (50%) - same as test-calculation
            if total_sdes > 0:
                scan_coverage = (scanned_sdes / total_sdes) * 50
                logger.debug(f"Scan coverage component: ({scanned_sdes} / {total_sdes}) * 50 = {scan_coverage}")
                confidence_score += scan_coverage
            else:
                logger.debug("No SDEs found, scan coverage component: 0")
            
            # Component 2: Scan frequency (30%) - same as test-calculation
            scan_frequency = 30  # Fixed value as in test-calculation
            logger.debug(f"Scan frequency component: {scan_frequency}")
            confidence_score += scan_frequency
            
            # Component 3: Data freshness (20%) - same as test-calculation
            data_freshness = 20  # Fixed value as in test-calculation
            logger.debug(f"Data freshness component: {data_freshness}")
            confidence_score += data_freshness
            
            confidence_score = min(100, round(confidence_score, 2))
            logger.debug(f"Final confidence score: {confidence_score}")
            
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
        
        # Count from sdes table (SDE definitions)
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS total_sdes FROM sdes WHERE client_id = %s", (client_id,))
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
              AND LOWER(sensitivity) = 'high'
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
        
        # Get scanned SDEs and total SDEs
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS scanned_sdes FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        scanned_sdes = row["scanned_sdes"] if row and "scanned_sdes" in row else 0
        
        cur.execute("SELECT COUNT(*) AS total_sdes FROM sdes WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sdes = row["total_sdes"] if row and "total_sdes" in row else 0
        
        # Calculate risk score
        if total_sdes > 0:
            risk_score = (scanned_sdes / total_sdes) * 40
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
    """Get confidence score for a client"""
    try:
        agent = ModularRiskAssessmentAgent()
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Get scanned SDEs and total SDEs
        cur.execute("SELECT COUNT(DISTINCT sde_id) AS scanned_sdes FROM scan_findings WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        scanned_sdes = row["scanned_sdes"] if row and "scanned_sdes" in row else 0
        
        cur.execute("SELECT COUNT(*) AS total_sdes FROM sdes WHERE client_id = %s", (client_id,))
        row = cur.fetchone()
        total_sdes = row["total_sdes"] if row and "total_sdes" in row else 0
        
        # Calculate confidence score
        confidence_score = 0.0
        
        # Component 1: Scan coverage (50%)
        if total_sdes > 0:
            scan_coverage = (scanned_sdes / total_sdes) * 50
            confidence_score += scan_coverage
        
        # Component 2: Scan frequency (30%)
        scan_frequency = 30
        confidence_score += scan_frequency
        
        # Component 3: Data freshness (20%)
        data_freshness = 20
        confidence_score += data_freshness
        
        confidence_score = min(100, round(confidence_score, 2))
        
        conn.close()
        return {"client_id": client_id, "confidence_score": confidence_score}
    except Exception as e:
        logger.error(f"Error calculating confidence score for client {client_id}: {e}")
        return {"client_id": client_id, "confidence_score": 50.0, "error": str(e)}

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
        if total_sdes > 0:
            risk_score = (high_risk_sdes / total_sdes) * 100
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
        if metrics["total_sdes"] > 0:
            metrics["risk_score"] = (metrics["scanned_sdes"] / metrics["total_sdes"]) * 40
        else:
            metrics["risk_score"] = 25.0
        
        metrics["risk_score"] = min(100, round(metrics["risk_score"], 2))
        
        # Confidence score
        confidence_score = 0.0
        if metrics["total_sdes"] > 0:
            scan_coverage = (metrics["scanned_sdes"] / metrics["total_sdes"]) * 50
            confidence_score += scan_coverage
        confidence_score += 30 + 20  # scan frequency + data freshness
        metrics["confidence_score"] = min(100, round(confidence_score, 2))
        
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
        return {"error": str(e)}

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
        
        # Get all data stores for this client
        cur.execute("""
            SELECT store_id, store_name, store_type, location 
            FROM data_stores 
            WHERE client_id = %s
        """, (client_id,))
        data_stores = [dict(row) for row in cur.fetchall()]
        
        # Get recent scans for this client (last 10 scans)
        cur.execute("""
            SELECT 
                s.scan_id,
                s.store_id,
                s.scan_data,
                s.status,
                s.timestamp,
                ds.store_name,
                ds.store_type,
                ds.location,
                COUNT(sf.finding_id) as findings_count
            FROM scans s
            LEFT JOIN data_stores ds ON s.store_id = ds.store_id
            LEFT JOIN scan_findings sf ON s.scan_id = sf.scan_id
            WHERE ds.client_id = %s
            GROUP BY s.scan_id, s.store_id, s.scan_data, s.status, s.timestamp, ds.store_name, ds.store_type, ds.location
            ORDER BY s.timestamp DESC
            LIMIT 10
        """, (client_id,))
        
        recent_scans = []
        for row in cur.fetchall():
            scan_data = row["scan_data"]
            scan_info = {}
            if scan_data:
                try:
                    scan_info = json.loads(scan_data)
                except:
                    scan_info = {"bucket": "Unknown", "file_name": "Unknown"}
            
            recent_scans.append({
                "scan_id": row["scan_id"],
                "store_id": row["store_id"],
                "store_name": row["store_name"] or "Unknown",
                "store_type": row["store_type"] or "Unknown",
                "location": row["location"] or "Unknown",
                "status": row["status"] or "Unknown",
                "findings_count": row["findings_count"] or 0,
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                "scan_info": scan_info
            })
        
        # Get daily scan counts for the last 7 days
        cur.execute("""
            SELECT 
                DATE(s.timestamp) as scan_date,
                COUNT(*) as daily_scans
            FROM scans s
            LEFT JOIN data_stores ds ON s.store_id = ds.store_id
            WHERE ds.client_id = %s 
                AND s.timestamp >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(s.timestamp)
            ORDER BY scan_date DESC
        """, (client_id,))
        
        daily_scans = []
        for row in cur.fetchall():
            daily_scans.append({
                "day": row["scan_date"].strftime("%Y-%m-%d"),
                "scans": row["daily_scans"]
            })
        
        # Fill in missing days with 0 scans
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if not any(day["day"] == date for day in daily_scans):
                daily_scans.append({"day": date, "scans": 0})
        
        # Sort by date (oldest first for chart)
        daily_scans.sort(key=lambda x: x["day"])
        
        conn.close()
        
        return {
            "client_id": client_id,
            "recent_scans": recent_scans,
            "daily_scans": daily_scans,
            "total_scans": len(recent_scans),
            "data_stores": data_stores
        }
        
    except Exception as e:
        logger.error(f"Error fetching scan activity for client {client_id}: {e}")
        return {
            "client_id": client_id,
            "recent_scans": [],
            "daily_scans": [],
            "total_scans": 0,
            "data_stores": [],
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

class ReportRequest(BaseModel):
    client_id: str
    format: str = 'pdf'  # 'pdf', or 'html'
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None

@app.post("/risk/report")
async def generate_risk_report(request: ReportRequest):
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
        pdf_result = agent.generate_pdf_report()
        if pdf_result and not pdf_result.startswith('Error'):
            # Return the file response without immediate cleanup
            # The file will be cleaned up by the agent's cleanup methods later
            # Use client name for filename instead of ID
            client_name = request.company or request.name or request.client_id
            safe_client_name = agent._sanitize_filename(client_name)
            return FileResponse(pdf_result, filename=f"risk_report_{safe_client_name}.pdf", media_type="application/pdf")
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
