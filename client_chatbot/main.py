import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError
from dotenv import load_dotenv
import logging
import re
import pytz
from enum import Enum
import traceback

# --- Configuration ---
class Config:
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
    LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO
    MAX_QUERY_RETRIES = 2
    DEFAULT_QUERY_LIMIT = 10
    MAX_QUERY_LIMIT = 500
    QUERY_TIMEOUT = 30  # seconds
    MAX_FALLBACK_RESULTS = 5

# Configure logging with better formatting
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chatbot.log') if Config.DEBUG_MODE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Custom Exceptions ---
class ChatbotError(Exception):
    """Base exception for chatbot-related errors"""
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR", details: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

class DatabaseConnectionError(ChatbotError):
    """Database connection related errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "DB_CONNECTION_ERROR", details)

class SQLGenerationError(ChatbotError):
    """SQL generation related errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "SQL_GENERATION_ERROR", details)

class QueryExecutionError(ChatbotError):
    """Query execution related errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "QUERY_EXECUTION_ERROR", details)

class ValidationError(ChatbotError):
    """Input validation related errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

# --- Enums ---
class QueryType(str, Enum):
    COUNT = "count"
    LIST = "list"
    SUMMARY = "summary"
    AGGREGATE = "aggregate"

class RiskLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

# --- Enhanced Pydantic Models ---
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    client_id: str = Field(..., min_length=1, max_length=128, description="Client identifier")
    user_id: Optional[str] = Field(None, max_length=128, description="User identifier for logging")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty or whitespace only")
        # Check for potential SQL injection attempts
        dangerous_patterns = [
            r';\s*(drop|delete|update|insert|alter|create|truncate)',
            r'--',
            r'/\*.*\*/',
            r'xp_cmdshell',
            r'sp_executesql'
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Question contains potentially unsafe content")
        return v.strip()
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not re.fullmatch(r"[A-Za-z0-9_\-]{1,128}", v):
            raise ValueError("Client ID contains invalid characters")
        return v

class ChatResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[str] = None
    timestamp: str
    execution_time_ms: Optional[int] = None
    fallback_used: bool = False

class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    llm_available: bool
    available_tables: List[str]
    timestamp: str
    error_details: Optional[str] = None

class Client(BaseModel):
    client_id: str
    client_name: str

class ErrorResponse(BaseModel):
    error: str
    error_code: str
    details: Optional[str] = None
    timestamp: str

# --- Initialize FastAPI with better error handling ---
app = FastAPI(
    title="Risk Analyzer Chatbot API",
    description="API for querying risk analysis data using natural language",
    version="2.0.0",
    docs_url="/docs" if Config.DEBUG_MODE else None,
    redoc_url="/redoc" if Config.DEBUG_MODE else None,
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(ChatbotError)
async def chatbot_exception_handler(request, exc: ChatbotError):
    logger.error(f"ChatbotError: {exc.message} - {exc.error_code} - {exc.details}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=exc.message,
            error_code=exc.error_code,
            details=exc.details if Config.DEBUG_MODE else None,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code="HTTP_ERROR",
            details=None,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            details=str(exc) if Config.DEBUG_MODE else None,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

# --- Global Variables ---
db_engine = None
llm = None
available_tables: List[str] = []
sql_database_utility: Optional[SQLDatabase] = None

# --- Table Schema Configuration (same as before) ---
TABLE_SCHEMAS_FOR_CHATBOT = {
    "isde_catalogue": {
        "description": "Catalog of Information Security Data Elements (ISDEs) and their properties like sde_key (unique identifier), name, data_type, sensitivity, regex pattern, classification_level, and industry_classification. This is a global reference table.",
        "return_columns": ["name", "data_type", "sensitivity", "classification_level", "industry_classification"]
    },
    "scan_baselines_simple": {
        "description": "Simplified baseline information for various data sources. Includes source_name, source_type, source_location, last_scan_timestamp (text format 'YYYY-MM-DD'), scan_status (e.g., 'never_scanned', 'completed'), total_scans_completed, and scan_frequency (e.g., 'manual', 'daily').",
        "return_columns": ["source_name", "source_type", "last_scan_timestamp", "total_scans_completed", "scan_status", "scan_frequency"]
    },
    "storage_connections": {
        "description": "Records details of storage connections, including id, user_id (who configured it), storage_type (e.g., 'S3', 'GCS'), name (connection alias), created_at and updated_at (timestamps). Note: 'config' contains sensitive credentials and is not for display.",
        "return_columns": ["name", "storage_type", "user_id", "created_at"]
    },
    "data_stores": {
        "description": "Information about data storage locations associated with a client. Contains client_id (FK to client_prof), store_id, store_name, store_type (e.g., 'AWS S3', 'PostgreSQL'), location, and discovery_timestamp (timestamp).",
        "return_columns": ["store_name", "store_type", "location", "discovery_timestamp"]
    },
    "aggregate": {
        "description": "Aggregated data summaries, linked to data_stores. Includes aggregation_id, store_id, aggregation_type, and aggregated value.",
        "return_columns": ["aggregation_type", "value"]
    },
    "client_connections": {
        "description": "Details of a client's specific data source connections (e.g., to their AWS or GCP accounts). Links to client_prof via client_id. Includes cli_conn_id, connections_type, and conn_name (user-defined name). Note: 'connection_cred' contains sensitive credentials and is not for display.",
        "return_columns": ["cli_conn_id", "connections_type", "conn_name"]
    },
    "client_connection_history": {
        "description": "Logs connection status and last usage for client connections. Links to client_connections via cli_conn_id. Includes cli_conn_hist_id, connection_status (e.g., 'success', 'failed'), last_used timestamp, and created_at timestamp.",
        "return_columns": ["cli_conn_id", "connection_status", "last_used"]
    },
    "client_prof": {
        "description": "Stores client profiles. Includes client_id (unique identifier), full_name, username, email, company_name, industry, country, and created_at timestamp.",
        "return_columns": ["full_name", "company_name", "email", "industry", "country", "created_at"]
    },
    "dp_policies": {
        "description": "Data privacy policies, generally applicable or specific. Includes policy_id, policy_name, description, compliance_status (e.g., 'Compliant', 'Non-compliant', 'In Progress'), and last_updated date (text format 'YYYY-MM-DD').",
        "return_columns": ["policy_name", "compliance_status", "last_updated", "description"]
    },
    "compliance": {
        "description": "Compliance status of identified Sensitive Data Elements (SDEs) against data policies. Links to sdes and dp_policies. Includes compliance_id, sde_id, policy_id, status (e.g., 'Compliant', 'Non-compliant'), audit_date (text format 'YYYY-MM-DD'), and a report reference.",
        "return_columns": ["sde_id", "policy_id", "status", "audit_date", "report"]
    },
    "client_selected_sdes": {
        "description": "SDEs that have been selected/chosen by the client for monitoring or action. Links to client_prof. Contains id, client_id, pattern_name, sensitivity, protection_method, and selected_at timestamp. These are the SDEs that the user has specifically chosen to focus on.",
        "return_columns": ["pattern_name", "sensitivity", "protection_method", "selected_at"]
    },
    "sdes": {
        "description": "Identified Sensitive Data Elements (SDEs) within a client's datasets. Links to client_prof and data_stores. Contains sde_id, client_id, store_id, dataset_name, dataset_column, sensitivity, protection_method, and column_name.",
        "return_columns": ["dataset_name", "dataset_column", "sensitivity", "protection_method", "column_name"]
    },
    "dp_procedures": {
        "description": "Procedures linked to data privacy policies. Includes procedure_id, policy_id, procedure_name, description, and owner.",
        "return_columns": ["procedure_name", "description", "owner"]
    },
    "model_inventory": {
        "description": "Inventory of AI/ML models used or deployed by a client. Links to client_prof. Includes model_id (UUID), client_id, model_name, provider_name, and a description. Note: 'weights_location' and 'bias_notes' are internal and not for display.",
        "return_columns": ["model_name", "provider_name", "description", "created_at"]
    },
    "pii_catalog": {
        "description": "Catalog of Personally Identifiable Information (PII) detected, linked to identified SDEs. Contains catalog_id, sde_id, dataset_name, purpose, owner, lineage, retention_policy, compliance_status, risk_level ('High', 'Medium', 'Low'), infosec_measures, and legal_compliance.",
        "return_columns": ["dataset_name", "purpose", "owner", "risk_level", "compliance_status", "retention_policy", "legal_compliance"]
    },
    "protection": {
        "description": "Details of data protection methods applied to SDEs. Links to sdes. Includes protection_id, sde_id, method (e.g., 'encryption', 'masking'), key_id (technical), and applied_date (text format 'YYYY-MM-DD').",
        "return_columns": ["method", "applied_date"]
    },
    "regulatory_reporting": {
        "description": "Records of regulatory reports generated based on compliance data. Links to compliance. Includes report_id, compliance_id, report_name, report_content (sensitive), and submit_date (text format 'YYYY-MM-DD').",
        "return_columns": ["report_name", "submit_date"]
    },
    "risk_assessments": {
        "description": "Records of risk assessments performed for clients. Contains client_id, assessment_id, total_data_sources, total_sdes, scanned_sdes, high_risk_sdes, scans_completed, last_scan_time (text format 'YYYY-MM-DD HH:MI:SS'), next_scheduled_scan (text format 'YYYY-MM-DD HH:MI:SS'), risk_score, confidence_score, and an LLM-generated summary of findings. Timestamps are in text format.",
        "return_columns": ["total_data_sources", "total_sdes", "high_risk_sdes", "scans_completed", "risk_score", "confidence_score", "last_scan_time", "next_scheduled_scan", "llm_summary"]
    },
    "reports": {
        "description": "General reports generated for clients, often linked to risk assessments. Contains report_id, client_id, assessment_id, report_type, report_format, report_content (sensitive), created_at (text format 'YYYY-MM-DD HH:MI:SS'), and title.",
        "return_columns": ["report_type", "title", "created_at"]
    },
    "scan_baselines": {
        "description": "Detailed baseline information for client data stores, linked to client_prof and data_stores. Includes client_id, baseline_id, store_id, last_scan_timestamp (text format 'YYYY-MM-DD HH:MI:SS'), scan_status, total_scans_completed, scan_frequency, next_scan_scheduled, and baseline_metadata. Timestamps are in text format.",
        "return_columns": ["store_id", "last_scan_timestamp", "scan_status", "total_scans_completed", "last_scan_findings", "scan_frequency", "next_scan_scheduled"]
    },
    "scan_findings": {
        "description": "Detailed findings from data scans for a client. Links to client_prof, scans, and sdes. Contains client_id, finding_id, scan_id, sde_id, data_value (sensitive/redacted), sensitivity, finding_type, is_sde (boolean), sde_category, risk_level ('High', 'Medium', 'Low'), object_path, confidence_score, detection_method, pattern_matched, matches_found, sample_matches (sensitive), location_metadata, privacy_implications, and scan_timestamp (text format 'YYYY-MM-DD HH:MI:SS').",
        "return_columns": ["finding_id", "sensitivity", "finding_type", "risk_level", "scan_timestamp", "object_path", "pattern_matched", "matches_found"]
    },
    "scan_findings_history": {
        "description": "Historical actions taken on scan findings for a client. Links to client_prof and scans. Includes client_id, finding_id, scan_id, data_value (sensitive/redacted), sensitivity, and action_taken (e.g., 'redacted', 'ignored', 'reviewed').",
        "return_columns": ["finding_id", "sensitivity", "action_taken"]
    },
    "scans": {
        "description": "Records of data scans performed. Links to regexes, sde_patterns, and data_stores. Contains scan_id, regex_id, pattern_id, store_id, scan_data (date of scan in text 'YYYY-MM-DD'), and status (e.g., 'completed', 'failed', 'in_progress').",
        "return_columns": ["scan_id", "scan_data", "status", "store_id"]
    },
    "sde_patterns": {
        "description": "Predefined patterns for Sensitive Data Elements (SDEs). Contains pattern_id, pattern_name, data_type, sensitivity, protection_method, regex_pattern, and classification. This is a global reference table.",
        "return_columns": ["pattern_name", "data_type", "sensitivity", "protection_method", "classification"]
    },
    "regexes": {
        "description": "Regular expressions used for data pattern matching, linked to sde_patterns. Contains regex_id, data_type, pattern_name, and regex_pattern. This is a global reference table.",
        "return_columns": ["pattern_name", "regex_pattern", "data_type"]
    },
    "discovered_objects": {
        "description": "Objects discovered during data store scanning. Contains object_id, cli_conn_id, object_name, object_type, object_path, object_size, last_modified, and metadata.",
        "return_columns": ["object_name", "object_type", "object_path", "object_size", "last_modified"]
    },
    "discovered_objects_optimized": {
        "description": "Optimized table for discovered objects with enhanced metadata. Contains object_id, store_id, client_id, name, type, path, size_bytes, last_modified, and metadata in JSONB format.",
        "return_columns": ["name", "type", "path", "size_bytes", "last_modified", "discovered_at"]
    },
    "selected_objects": {
        "description": "Objects selected by client for scanning. Links to discovered_objects_optimized and data_stores. Contains selection_id, client_id, object_id, store_id, object_name, object_type, object_path, and selected_at.",
        "return_columns": ["object_name", "object_type", "object_path", "selected_at"]
    },
    "compliance_scores": {
        "description": "Compliance scores for different regulations per client. Contains client_id, inferred_regulation, total_required, matched, score, status, and recommendation.",
        "return_columns": ["inferred_regulation", "score", "status", "recommendation"]
    }
}

# --- Relationships and Configuration (same as before) ---
KNOWN_RELATIONSHIPS: List[Tuple[str, str, str, str, str]] = [
    ("client_selected_sdes", "client_id", "client_prof", "client_id", "Each selected SDE belongs to a client"),
    ("sdes", "client_id", "client_prof", "client_id", "Each SDE belongs to a client"),
    ("sdes", "store_id", "data_stores", "store_id", "SDEs are found within a data store"),
    ("scans", "store_id", "data_stores", "store_id", "Scans run on data stores"),
    ("scan_findings", "scan_id", "scans", "scan_id", "Findings belong to a scan"),
    ("scan_findings", "sde_id", "client_selected_sdes", "id", "Findings may reference a selected SDE"),
    ("scan_findings", "client_id", "client_prof", "client_id", "Findings are client-specific"),
    ("compliance", "sde_id", "sdes", "sde_id", "Compliance is evaluated per SDE"),
    ("compliance", "policy_id", "dp_policies", "policy_id", "Compliance references a data policy"),
    ("dp_procedures", "policy_id", "dp_policies", "policy_id", "Procedures implement policies"),
    ("pii_catalog", "sde_id", "sdes", "sde_id", "PII catalog entries are linked to SDEs"),
    ("protection", "sde_id", "sdes", "sde_id", "Protection methods are applied to SDEs"),
    ("risk_assessments", "client_id", "client_prof", "client_id", "Risk assessments are client-specific"),
    ("reports", "client_id", "client_prof", "client_id", "Reports are client-specific"),
    ("reports", "assessment_id", "risk_assessments", "assessment_id", "Reports often summarize an assessment"),
    ("scan_baselines", "client_id", "client_prof", "client_id", "Baselines are client-specific"),
    ("scan_baselines", "store_id", "data_stores", "store_id", "Baselines are created per data store"),
    ("client_connections", "client_id", "client_prof", "client_id", "Connections belong to a client"),
    ("client_connection_history", "cli_conn_id", "client_connections", "cli_conn_id", "History is logged per connection"),
    ("model_inventory", "client_id", "client_prof", "client_id", "Models belong to a client"),
    ("discovered_objects", "cli_conn_id", "client_connections", "cli_conn_id", "Discovered objects belong to a connection"),
    ("selected_objects", "client_id", "client_prof", "client_id", "Selected objects belong to a client"),
    ("selected_objects", "store_id", "data_stores", "store_id", "Selected objects are from data stores"),
]

SEMANTIC_ALIASES: Dict[str, str] = {
    "data sources": "data_stores",
    "sources": "data_stores",
    "stores": "data_stores",
    "findings": "scan_findings",
    "issues": "scan_findings",
    "alerts": "scan_findings",
    "sde": "client_selected_sdes",
    "sdes": "client_selected_sdes",
    "selected sdes": "client_selected_sdes",
    "chosen sdes": "client_selected_sdes",
    "my sdes": "client_selected_sdes",
    "policies": "dp_policies",
    "procedures": "dp_procedures",
    "models": "model_inventory",
    "connections": "client_connections",
    "reports": "reports",
    "baselines": "scan_baselines",
    "last scan": "scan_baselines|scans",
}

FALLBACK_SEARCH_COLUMNS: Dict[str, List[str]] = {
    "scan_findings": ["finding_type", "risk_level", "sensitivity", "sde_category", "object_path", "pattern_matched"],
    "pii_catalog": ["dataset_name", "purpose", "owner", "risk_level", "compliance_status", "retention_policy", "legal_compliance"],
    "dp_policies": ["policy_name", "description", "compliance_status"],
    "dp_procedures": ["procedure_name", "description", "owner"],
    "scan_baselines": ["scan_status", "scan_frequency"],
    "scan_baselines_simple": ["source_name", "source_type", "scan_status", "scan_frequency"],
    "data_stores": ["store_name", "store_type", "location"],
    "client_connections": ["connections_type", "conn_name"],
    "client_connection_history": ["connection_status"],
    "model_inventory": ["model_name", "provider_name", "description"],
    "reports": ["report_type", "title"],
    "risk_assessments": ["llm_summary"],
    "client_selected_sdes": ["pattern_name", "sensitivity", "protection_method", "selected_at"],
    "sdes": ["dataset_name", "dataset_column", "sensitivity", "protection_method"],
    "discovered_objects": ["object_name", "object_type", "object_path"],
    "discovered_objects_optimized": ["name", "type", "path"],
    "selected_objects": ["object_name", "object_type", "object_path"],
    "compliance_scores": ["inferred_regulation", "status", "recommendation"],
    "sdes": ["dataset_name", "dataset_column", "sensitivity", "protection_method"],
    "discovered_objects": ["object_name", "object_type", "object_path"],
    "discovered_objects_optimized": ["name", "type", "path"],
    "selected_objects": ["object_name", "object_type", "object_path"],
    "compliance_scores": ["inferred_regulation", "status", "recommendation"],
    "isde_catalogue": ["name", "data_type", "sensitivity", "classification_level", "industry_classification"],
    "regexes": ["pattern_name", "data_type"],
    "sde_patterns": ["pattern_name", "data_type", "sensitivity", "classification"],
}

STOPWORDS = {
    "the","a","an","and","or","of","in","on","for","to","with","by","at","is","are","was","were",
    "top","first","show","list","give","get","latest","last","find","how","many","much","what","which","all",
    "me","from","within","client","client_id","data","source","sources","over","past","days","day","hours","hour"
}

# --- Enhanced Utility Functions ---
class DatabaseManager:
    """Manages database connections and operations with better error handling"""
    
    @staticmethod
    def create_connection() -> Any:
        """Create database connection with proper error handling"""
        try:
            required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                raise DatabaseConnectionError(
                    f"Missing required database environment variables: {', '.join(missing_vars)}"
                )
            
            db_connection_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:5432/{os.getenv('DB_NAME')}"
            engine = create_engine(
                db_connection_str,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": Config.QUERY_TIMEOUT}
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connection established successfully")
            return engine
            
        except OperationalError as e:
            raise DatabaseConnectionError(
                "Failed to connect to database. Please check your database configuration.",
                str(e)
            )
        except Exception as e:
            raise DatabaseConnectionError(
                "Unexpected error during database connection",
                str(e)
            )

    @staticmethod
    def get_available_tables(engine) -> List[str]:
        """Get list of available tables with error handling"""
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                )
                all_db_tables = [row[0] for row in result.fetchall()]
                
                available = [
                    table for table in TABLE_SCHEMAS_FOR_CHATBOT.keys() 
                    if table in all_db_tables
                ]
                
                logger.info(f"Found {len(available)} available tables: {available}")
                return available
                
        except Exception as e:
            logger.error(f"Failed to get available tables: {e}")
            raise DatabaseConnectionError("Failed to retrieve database schema", str(e))

class LLMManager:
    """Manages LLM operations with better error handling"""
    
    @staticmethod
    def create_llm() -> ChatGoogleGenerativeAI:
        """Create LLM instance with proper error handling"""
        try:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            llm_instance = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=gemini_api_key,
                temperature=0.1,
                timeout=Config.QUERY_TIMEOUT
            )
            
            # Test LLM with a simple query
            test_response = llm_instance.invoke("Say 'test successful'")
            if not test_response.content:
                raise ValueError("LLM test failed - no response content")
            
            logger.info("LLM initialized and tested successfully")
            return llm_instance
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise ChatbotError("Failed to initialize AI service", "LLM_INIT_ERROR", str(e))

class QueryValidator:
    """Enhanced SQL query validation"""
    
    @staticmethod
    def validate_sql_safety(sql: str) -> bool:
        """Enhanced SQL safety validation"""
        if not sql or not sql.strip():
            return False
            
        sql_upper = sql.strip().upper()
        
        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            logger.warning(f"SQL doesn't start with SELECT: {sql}")
            return False
        
        # Check for dangerous operations
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE",
            "GRANT", "REVOKE", "VACUUM", "ANALYZE", "EXPLAIN", "COPY", "LOAD",
            "IMPORT", "EXPORT", "BACKUP", "RESTORE", "SHUTDOWN", "RESTART"
        ]
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_upper):
                logger.warning(f"Dangerous keyword found in SQL: {keyword}")
                return False
        
        # Check for comments and potential injection
        if "--" in sql or "/*" in sql or "*/" in sql:
            logger.warning("Comments found in SQL query")
            return False
        
        # Check for multiple statements
        if sql.count(";") > 1:
            logger.warning("Multiple statements found in SQL")
            return False
        
        # Check for suspicious functions
        suspicious_functions = ["pg_sleep", "pg_read_file", "pg_ls_dir", "version()"]
        for func in suspicious_functions:
            if func.lower() in sql.lower():
                logger.warning(f"Suspicious function found: {func}")
                return False
        
        return True
    
    @staticmethod
    def validate_client_id(client_id: str) -> bool:
        """Enhanced client ID validation"""
        if not client_id:
            return False
        return bool(re.fullmatch(r"[A-Za-z0-9_\-]{1,128}", client_id))

class ResponseFormatter:
    """Handles response formatting and summarization"""
    
    @staticmethod
    def should_summarize(question: str, row_count: int, column_count: int) -> bool:
        """Determine if results should be summarized"""
        summary_keywords = [
            "summarize", "overview", "dashboard", "total", "breakdown",
            "analyze", "insights", "trends", "summary", "report"
        ]
        
        question_wants_summary = any(keyword in question.lower() for keyword in summary_keywords)
        too_much_data = row_count > 5 or column_count > 4
        
        return question_wants_summary or too_much_data

    @staticmethod
    def redact_sensitive_data(column_name: str, value: Any, table_context: List[str]) -> str:
        """Enhanced sensitive data redaction"""
        if value is None:
            return "NULL"
        
        column_lower = column_name.lower()
        redaction_rules = {
            'connection_cred': "<CREDENTIALS_REDACTED>",
            'data_value': "<SENSITIVE_DATA_REDACTED>",
            'sample_matches': "<SAMPLE_DATA_REDACTED>",
            'regex_pattern': "<PATTERN_REDACTED>",
            'report_content': "<REPORT_CONTENT_AVAILABLE>",
            'config': "<CONFIG_REDACTED>",
            'weights_location': "<MODEL_LOCATION_REDACTED>",
            'baseline_hash': "<HASH_REDACTED>",
            'api_key': "<API_KEY_REDACTED>",
            'password': "<PASSWORD_REDACTED>",
            'secret': "<SECRET_REDACTED>",
        }
        
        for pattern, redaction in redaction_rules.items():
            if pattern in column_lower:
                return redaction
        
        # Special handling for LLM summaries in specific contexts
        if column_lower == 'llm_summary' and 'risk_assessments' in table_context:
            return "<SUMMARY_AVAILABLE>"
        
        return str(value)

# --- Core Business Logic ---
def is_client_specific_table(table_name: str) -> bool:
    """Check if table requires client_id filtering"""
    table_info = TABLE_SCHEMAS_FOR_CHATBOT.get(table_name.lower())
    if table_info:
        return 'client_id' in table_info['description'].lower()
    return False

def extract_keywords(question: str) -> List[str]:
    """Extract meaningful keywords from question for fallback search"""
    try:
        tokens = re.findall(r"[A-Za-z0-9_\-]+", question.lower())
        keywords = [t for t in tokens if t not in STOPWORDS and len(t) >= 3 and not t.isdigit()]
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for keyword in keywords:
            if keyword not in seen:
                result.append(keyword)
                seen.add(keyword)
        
        return result[:6]  # Limit to 6 keywords for performance
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []

def run_fallback_keyword_search(question: str, client_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Enhanced fallback search with better error handling"""
    if db_engine is None:
        logger.warning("Database engine not available for fallback search")
        return {}
    
    keywords = extract_keywords(question)
    if not keywords:
        logger.debug("No keywords extracted for fallback search")
        return {}
    
    try:
        inspector = inspect(db_engine)
        results: Dict[str, List[Dict[str, Any]]] = {}
        
        for table_name, search_columns in FALLBACK_SEARCH_COLUMNS.items():
            if available_tables and table_name not in available_tables:
                continue
            
            try:
                # Verify table and columns exist
                actual_columns = {col['name'] for col in inspector.get_columns(table_name)}
                valid_search_columns = [col for col in search_columns if col in actual_columns]
                
                if not valid_search_columns:
                    continue
                
                # Build search query
                select_columns = valid_search_columns[:]
                
                # Add timestamp column if available
                timestamp_columns = ["scan_timestamp", "last_scan_timestamp", "created_at", "updated_at"]
                for ts_col in timestamp_columns:
                    if ts_col in actual_columns and ts_col not in select_columns:
                        select_columns.append(ts_col)
                        break
                
                # Build WHERE conditions
                where_conditions = []
                query_params = {}
                param_counter = 0
                
                for keyword in keywords:
                    keyword_conditions = []
                    for column in valid_search_columns:
                        param_name = f"kw_{param_counter}"
                        keyword_conditions.append(f"{column} ILIKE :{param_name}")
                        query_params[param_name] = f"%{keyword}%"
                        param_counter += 1
                    
                    if keyword_conditions:
                        where_conditions.append(f"({' OR '.join(keyword_conditions)})")
                
                if not where_conditions:
                    continue
                
                # Add client filter if needed
                if is_client_specific_table(table_name) and "client_id" in actual_columns:
                    where_conditions.append("client_id = :client_id")
                    query_params["client_id"] = client_id
                
                # Construct final query
                columns_sql = ", ".join(select_columns)
                where_sql = " AND ".join(where_conditions)
                query = f"SELECT {columns_sql} FROM {table_name} WHERE {where_sql} LIMIT {Config.MAX_FALLBACK_RESULTS}"
                
                # Execute query
                with db_engine.connect() as connection:
                    result = connection.execute(text(query), query_params)
                    rows = result.fetchall()
                    
                    if rows:
                        column_names = list(result.keys())
                        table_results = [dict(zip(column_names, row)) for row in rows]
                        results[table_name] = table_results
                        
            except Exception as table_error:
                logger.debug(f"Fallback search failed for table {table_name}: {table_error}")
                continue
        
        logger.info(f"Fallback search completed. Found results in {len(results)} tables")
        return results
        
    except Exception as e:
        logger.error(f"Error in fallback keyword search: {e}")
        return {}

def initialize_services():
    """Enhanced service initialization with comprehensive error handling"""
    global db_engine, llm, available_tables, sql_database_utility
    
    logger.info("Starting service initialization...")
    
    try:
        # Initialize LLM
        logger.info("Initializing LLM service...")
        llm = LLMManager.create_llm()
        
        # Initialize database
        logger.info("Initializing database connection...")
        db_engine = DatabaseManager.create_connection()
        available_tables = DatabaseManager.get_available_tables(db_engine)
        
        # Initialize SQLDatabase utility
        logger.info("Initializing SQLDatabase utility...")
        sql_database_utility = SQLDatabase(db_engine, include_tables=available_tables)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        # Don't raise here - let the app start but mark services as unavailable
        # The health check endpoint will reflect the actual status

def get_table_info_for_llm_prompt() -> str:
    """Enhanced table info generation with error handling"""
    if sql_database_utility is None:
        logger.error("SQLDatabase utility not initialized")
        return "Database schema information unavailable."
    
    try:
        default_schema_info = sql_database_utility.get_table_info()
        lines = default_schema_info.split('\n')
        formatted_schema = []
        current_table = None

        for line in lines:
            if line.startswith("Table: "):
                current_table = line.replace("Table: ", "").strip()
                formatted_schema.append(line)
                
                # Add custom description and column guidance
                if current_table in TABLE_SCHEMAS_FOR_CHATBOT:
                    table_config = TABLE_SCHEMAS_FOR_CHATBOT[current_table]
                    
                    if "description" in table_config:
                        formatted_schema.append(f"  Description: {table_config['description']}")
                    
                    if table_config.get("return_columns"):
                        preferred_cols = ", ".join(table_config["return_columns"])
                        formatted_schema.append(f"  Preferred columns: {preferred_cols}")
            else:
                formatted_schema.append(line)
        
        return "\n".join(formatted_schema)
        
    except Exception as e:
        logger.error(f"Error generating table info for LLM: {e}")
        return "Database schema information unavailable due to error."

def _get_desired_limit_from_question(question: str, default_limit: int = Config.DEFAULT_QUERY_LIMIT) -> int:
    """Extract limit from question with validation"""
    try:
        match = re.search(r"\b(top|first|limit)\s+(\d{1,4})\b", question, re.IGNORECASE)
        if match:
            requested_limit = int(match.group(2))
            return min(max(requested_limit, 1), Config.MAX_QUERY_LIMIT)
    except (ValueError, AttributeError) as e:
        logger.debug(f"Error parsing limit from question: {e}")
    
    return default_limit

def _sanitize_llm_sql(raw_sql: str) -> str:
    """Enhanced SQL sanitization"""
    if not raw_sql:
        return ""
    
    sql = raw_sql.strip()
    
    # Remove code block markers
    if sql.startswith("```sql"):
        sql = sql[6:]
    elif sql.startswith("```"):
        sql = sql[3:]
    
    if sql.endswith("```"):
        sql = sql[:-3]
    
    sql = sql.strip()
    
    # Handle multiple statements - keep only the first
    if ";" in sql:
        statements = sql.split(";")
        sql = statements[0].strip()
    
    return sql

def _ensure_limit(sql: str, limit: int) -> str:
    """Ensure LIMIT clause exists for appropriate queries"""
    sql_upper = sql.upper()
    
    # Don't add LIMIT to aggregate queries or queries that already have LIMIT
    if any(keyword in sql_upper for keyword in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN(", "LIMIT ", "GROUP BY"]):
        return sql
    
    return f"{sql} LIMIT {limit}"

def detect_query_intent(question: str) -> Dict[str, Any]:
    """Enhanced intent detection"""
    question_lower = question.lower()
    
    intent = {
        "type": QueryType.LIST,
        "group_by": None,
        "risk_level": None,
        "top_n": _get_desired_limit_from_question(question),
        "time_window": None,
        "requires_summary": False
    }
    
    # Detect query type
    if re.search(r'\b(count|how many|total|number of)\b', question_lower):
        intent["type"] = QueryType.COUNT
    elif re.search(r'\b(summarize|overview|dashboard|breakdown|analyze)\b', question_lower):
        intent["type"] = QueryType.SUMMARY
        intent["requires_summary"] = True
    elif re.search(r'\b(group by|grouped by|by type|by category)\b', question_lower):
        intent["type"] = QueryType.AGGREGATE
    
    # Detect grouping
    if re.search(r'by\s+(risk\s*level|risklevel)', question_lower):
        intent["group_by"] = "risk_level"
    elif re.search(r'by\s+sensitivity', question_lower):
        intent["group_by"] = "sensitivity"
    elif re.search(r'by\s+(source\s*type|store[_\s]*type)', question_lower):
        intent["group_by"] = "store_type"
    
    # Detect risk level filter
    risk_patterns = {
        RiskLevel.HIGH: [r'\bhigh\s*risk\b', r'\brisk\s*high\b', r'\bhigh-risk\b'],
        RiskLevel.MEDIUM: [r'\bmedium\s*risk\b', r'\brisk\s*medium\b', r'\bmedium-risk\b'],
        RiskLevel.LOW: [r'\blow\s*risk\b', r'\brisk\s*low\b', r'\blow-risk\b']
    }
    
    for risk_level, patterns in risk_patterns.items():
        if any(re.search(pattern, question_lower) for pattern in patterns):
            intent["risk_level"] = risk_level
            break
    
    # Detect time window
    time_match = re.search(r'last\s+(\d{1,4})\s+(day|days|hour|hours|week|weeks|month|months)', question_lower)
    if time_match:
        number = int(time_match.group(1))
        unit = time_match.group(2).lower()
        # Normalize unit
        if unit.startswith('day'):
            unit = 'days'
        elif unit.startswith('hour'):
            unit = 'hours'
        elif unit.startswith('week'):
            unit = 'weeks'
        elif unit.startswith('month'):
            unit = 'months'
        intent["time_window"] = (number, unit)
    
    return intent

def generate_sql_with_retry(question: str, client_id: str, max_retries: int = Config.MAX_QUERY_RETRIES) -> Optional[str]:
    """Generate SQL with retry logic and better error handling"""
    if not llm:
        raise SQLGenerationError("LLM service not available")
    
    schema_info = get_table_info_for_llm_prompt()
    if "unavailable" in schema_info.lower():
        raise SQLGenerationError("Database schema information unavailable")
    
    intent = detect_query_intent(question)
    limit = intent.get("top_n", Config.DEFAULT_QUERY_LIMIT)
    
    # Build enhanced prompt
    prompt = build_enhanced_sql_prompt(question, client_id, limit, schema_info, intent)
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Generating SQL query (attempt {attempt + 1}/{max_retries + 1})")
            
            response = llm.invoke(prompt)
            if not response or not response.content:
                raise SQLGenerationError("LLM returned empty response")
            
            sql_query = _sanitize_llm_sql(response.content)
            
            if not sql_query:
                raise SQLGenerationError("Failed to extract valid SQL from LLM response")
            
            # Validate the generated SQL
            if not QueryValidator.validate_sql_safety(sql_query):
                raise SQLGenerationError("Generated SQL failed safety validation")
            
            # Ensure LIMIT clause
            sql_query = _ensure_limit(sql_query, limit)
            
            logger.info(f"Successfully generated SQL: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.warning(f"SQL generation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries:
                raise SQLGenerationError(f"Failed to generate SQL after {max_retries + 1} attempts", str(e))
            
            # Modify prompt for retry
            prompt += f"\n\nPrevious attempt failed with error: {str(e)}\nPlease generate a corrected query."
    
    return None

def build_enhanced_sql_prompt(question: str, client_id: str, limit: int, schema_info: str, intent: Dict[str, Any]) -> str:
    """Build enhanced SQL generation prompt"""
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S IST')
    
    examples = """
Examples:
Q: count high risk findings in last 7 days
A: SELECT COUNT(*) FROM scan_findings WHERE risk_level = 'High' AND TO_TIMESTAMP(scan_timestamp, 'YYYY-MM-DD HH24:MI:SS') >= CURRENT_TIMESTAMP - INTERVAL '7 days' AND client_id = 'CLIENT_ID';

Q: list data sources
A: SELECT store_name, store_type, location, discovery_timestamp FROM data_stores WHERE client_id = 'CLIENT_ID' LIMIT 10;

Q: list sdes
A: SELECT pattern_name, sensitivity, protection_method, selected_at FROM client_selected_sdes WHERE client_id = 'CLIENT_ID' LIMIT 10;

Q: show me sdes
A: SELECT pattern_name, sensitivity, protection_method, selected_at FROM client_selected_sdes WHERE client_id = 'CLIENT_ID' LIMIT 10;

Q: what are my sdes
A: SELECT pattern_name, sensitivity, protection_method, selected_at FROM client_selected_sdes WHERE client_id = 'CLIENT_ID' LIMIT 10;

Q: my selected sdes
A: SELECT pattern_name, sensitivity, protection_method, selected_at FROM client_selected_sdes WHERE client_id = 'CLIENT_ID' LIMIT 10;

Q: show my chosen sdes
A: SELECT pattern_name, sensitivity, protection_method, selected_at FROM client_selected_sdes WHERE client_id = 'CLIENT_ID' LIMIT 10;

Q: how many sdes have I selected
A: SELECT COUNT(*) FROM client_selected_sdes WHERE client_id = 'CLIENT_ID';

Q: findings for my selected sdes
A: SELECT sf.finding_id, sf.risk_level, sf.sensitivity, sf.scan_timestamp FROM scan_findings sf WHERE sf.client_id = 'CLIENT_ID' LIMIT 10;

Q: selected sdes with high risk findings
A: SELECT COUNT(*) FROM scan_findings sf WHERE sf.client_id = 'CLIENT_ID' AND sf.risk_level = 'High';

Q: sdes by sensitivity
A: SELECT sf.sensitivity, COUNT(*) AS total FROM scan_findings sf WHERE sf.client_id = 'CLIENT_ID' GROUP BY sf.sensitivity ORDER BY total DESC;
"""
    
    return f"""You are an expert PostgreSQL analyst. Generate a single, correct SELECT statement.

STRICT REQUIREMENTS:
- Return ONLY a SELECT query, no explanations or markdown
- Use only tables and columns from the provided schema
- For client-specific tables, include WHERE client_id = '{client_id}'
- Use exact column names and table names as shown in schema
- Apply appropriate LIMIT clauses for list queries
- Use proper PostgreSQL syntax for date/time operations

IMPORTANT TABLE RELATIONSHIPS:
- client_selected_sdes: Contains SDEs that the user has specifically selected/chosen for monitoring. Use this for "my SDEs" or "selected SDEs" queries.
- sdes: Contains all identified SDEs in the system. Use this for general SDE queries or when needing SDE details.
- scan_findings: Contains all findings discovered during scans, may reference both sdes and client_selected_sdes
- Use appropriate table based on user's intent - "my/selected SDEs" → client_selected_sdes, "all SDEs" → sdes

KEY QUERY PATTERNS:
- When user asks about "my SDEs" or "selected SDEs" → Use client_selected_sdes 
- When user asks about general "SDEs" → Use sdes table
- When user asks "findings for my SDEs" → JOIN scan_findings with client_selected_sdes 
- When user asks "how many SDEs selected" → COUNT from client_selected_sdes
- When user asks "how many SDEs total" → COUNT from scan_findings

Current Context:
- Current time: {current_time}
- Query intent: {intent.get('type', 'list')}
- Expected limit: {limit}

{examples}

Database Schema:
{schema_info}

User Question: {question}

SQL Query:"""

def enforce_client_security_filter(sql_query: str, client_id: str) -> str:
    """Enhanced client filtering with comprehensive security checks"""
    if not sql_query or not client_id:
        raise ValidationError("Invalid SQL query or client ID for security filtering")
    
    original_query = sql_query
    sql_lower = sql_query.lower()
    
    try:
        # Find all tables in the query
        table_pattern = r'(?:FROM|JOIN)\s+(?:"?([a-zA-Z0-9_]+)"?)(?:\s+AS\s+(?:"?([a-zA-Z0-9_]+)"?))?'
        table_matches = re.findall(table_pattern, sql_query, re.IGNORECASE)
        
        tables_with_aliases = []
        for table_name, alias in table_matches:
            if table_name:
                effective_name = alias if alias else table_name
                tables_with_aliases.append((table_name.lower(), effective_name))
        
        logger.debug(f"Identified tables for client filtering: {tables_with_aliases}")
        
        # Apply client filtering to client-specific tables
        filter_applied = False
        for table_name, table_alias in tables_with_aliases:
            if is_client_specific_table(table_name):
                # Check if client_id filter already exists
                client_filter_pattern = rf"(?:\b{re.escape(table_alias)}\.)?client_id\s*=\s*['\"]([^'\"]*)['\"]"
                existing_filter = re.search(client_filter_pattern, sql_query, re.IGNORECASE)
                
                if existing_filter:
                    # Replace existing client_id with correct one
                    sql_query = re.sub(
                        client_filter_pattern,
                        f"{table_alias}.client_id = '{client_id}'",
                        sql_query,
                        count=1,
                        flags=re.IGNORECASE
                    )
                    logger.info(f"Replaced existing client filter for table {table_name}")
                else:
                    # Add client_id filter
                    if re.search(r'\bWHERE\b', sql_query, re.IGNORECASE):
                        sql_query = re.sub(
                            r'(\bWHERE\s+)',
                            rf'\1{table_alias}.client_id = \'{client_id}\' AND ',
                            sql_query,
                            count=1,
                            flags=re.IGNORECASE
                        )
                    else:
                        # Find where to insert WHERE clause
                        insert_keywords = ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]
                        inserted = False
                        for keyword in insert_keywords:
                            if keyword in sql_query.upper():
                                sql_query = sql_query.replace(
                                    keyword,
                                    f"WHERE {table_alias}.client_id = '{client_id}' {keyword}",
                                    1
                                )
                                inserted = True
                                break
                        
                        if not inserted:
                            sql_query += f" WHERE {table_alias}.client_id = '{client_id}'"
                    
                    logger.info(f"Added client filter for table {table_name}")
                
                filter_applied = True
                break  # Only apply to first client-specific table found
        
        # Special handling for 'scans' table that needs JOIN to data_stores
        if not filter_applied and any(table[0] == "scans" for table in tables_with_aliases):
            if "data_stores" not in sql_lower:
                sql_query = re.sub(
                    r'(FROM\s+scans\b)',
                    r'\1 JOIN data_stores ds ON scans.store_id = ds.store_id',
                    sql_query,
                    count=1,
                    flags=re.IGNORECASE
                )
            
            # Add client filter through data_stores
            if re.search(r'\bWHERE\b', sql_query, re.IGNORECASE):
                sql_query = re.sub(
                    r'(\bWHERE\s+)',
                    rf'\1ds.client_id = \'{client_id}\' AND ',
                    sql_query,
                    count=1,
                    flags=re.IGNORECASE
                )
            else:
                sql_query += f" WHERE ds.client_id = '{client_id}'"
            
            filter_applied = True
        
        # Security check: Ensure client filtering was applied where needed
        client_specific_tables = [t[0] for t in tables_with_aliases if is_client_specific_table(t[0])]
        if client_specific_tables and not filter_applied:
            logger.error(f"SECURITY ALERT: Could not apply client filter to query: {original_query}")
            raise ValidationError("Query could not be safely filtered for client access")
        
        logger.debug(f"Client security filter applied. Original: {original_query} -> Filtered: {sql_query}")
        return sql_query
        
    except Exception as e:
        logger.error(f"Error in client security filtering: {e}")
        raise ValidationError("Failed to apply security filters to query", str(e))

def execute_query_with_retry(sql_query: str, max_retries: int = Config.MAX_QUERY_RETRIES) -> Tuple[List[Any], List[str]]:
    """Execute SQL query with retry logic and comprehensive error handling"""
    if not db_engine:
        raise QueryExecutionError("Database connection not available")
    
    if not QueryValidator.validate_sql_safety(sql_query):
        raise QueryExecutionError("SQL query failed safety validation")
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Executing query (attempt {attempt + 1}/{max_retries + 1}): {sql_query}")
            
            with db_engine.connect() as connection:
                # Set query timeout
                connection.execute(text(f"SET statement_timeout = '{Config.QUERY_TIMEOUT}s'"))
                
                result = connection.execute(text(sql_query))
                rows = result.fetchall()
                column_names = list(result.keys())
                
                logger.info(f"Query executed successfully. Returned {len(rows)} rows with {len(column_names)} columns")
                return rows, column_names
                
        except OperationalError as e:
            last_error = e
            error_msg = str(e).lower()
            
            if "timeout" in error_msg:
                raise QueryExecutionError("Query timed out. Please try a simpler query or add more filters.")
            elif "connection" in error_msg:
                if attempt < max_retries:
                    logger.warning(f"Database connection lost, retrying... (attempt {attempt + 1})")
                    continue
                else:
                    raise QueryExecutionError("Database connection lost. Please try again later.")
            else:
                raise QueryExecutionError(f"Database operation failed: {str(e)}")
                
        except ProgrammingError as e:
            error_msg = str(e).lower()
            
            if "column" in error_msg and "does not exist" in error_msg:
                raise QueryExecutionError("The requested data column doesn't exist. Please rephrase your question.")
            elif "relation" in error_msg and "does not exist" in error_msg:
                raise QueryExecutionError("The requested data table doesn't exist. Please rephrase your question.")
            elif "syntax error" in error_msg:
                if attempt < max_retries:
                    logger.warning(f"SQL syntax error, attempting correction... (attempt {attempt + 1})")
                    # Here you could implement SQL correction logic
                    continue
                else:
                    raise QueryExecutionError("Failed to generate a valid database query. Please rephrase your question.")
            else:
                raise QueryExecutionError(f"Query error: {str(e)}")
                
        except SQLAlchemyError as e:
            last_error = e
            logger.error(f"SQLAlchemy error on attempt {attempt + 1}: {e}")
            if attempt == max_retries:
                raise QueryExecutionError("Database query failed. Please try again or contact support.")
                
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error during query execution: {e}")
            if attempt == max_retries:
                raise QueryExecutionError("An unexpected error occurred during query execution.")
    
    # If we get here, all retries failed
    if last_error:
        raise QueryExecutionError(f"Query execution failed after {max_retries + 1} attempts", str(last_error))

def format_query_results(
    rows: List[Any], 
    column_names: List[str], 
    question: str, 
    sql_query: str, 
    client_id: str,
    intent: Dict[str, Any]
) -> Dict[str, Any]:
    """Enhanced result formatting with comprehensive query type handling"""
    start_time = datetime.now()
    
    try:
        # Check if we have no rows at all (this should be rare for valid queries)
        if not rows:
            return handle_empty_results(question, client_id, sql_query)
        
        # Determine the query type based on SQL and results structure
        query_type = detect_sql_query_type(sql_query, rows, column_names)
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Handle different query types appropriately
        if query_type == "COUNT":
            count_value = rows[0][0]
            if count_value == 0:
                return handle_empty_results(question, client_id, sql_query)
            else:
                # Make count responses more natural and conversational
                if count_value == 1:
                    answer = "I found 1 result."
                else:
                    answer = f"I found {count_value:,} results."
                
                return {
                    "answer": answer,
                    "sql_query": sql_query if Config.DEBUG_MODE else None,
                    "error_code": None,
                    "error_details": None,
                    "execution_time_ms": execution_time,
                    "fallback_used": False
                }
        
        elif query_type == "AGGREGATE":
            # Handle SUM, AVG, MAX, MIN, or GROUP BY queries
            return handle_aggregate_results(rows, column_names, sql_query, execution_time)
        
        elif query_type == "SINGLE_VALUE":
            # Handle queries that return a single value (like MAX, MIN, AVG without GROUP BY)
            value = rows[0][0]
            column_name = column_names[0]
            
            # Make single value responses more natural
            friendly_name = column_name.lower().replace('_', ' ').replace('(', '').replace(')', '')
            if 'max' in friendly_name:
                answer = f"The highest {friendly_name.replace('max ', '')} is **{value}**."
            elif 'min' in friendly_name:
                answer = f"The lowest {friendly_name.replace('min ', '')} is **{value}**."
            elif 'avg' in friendly_name or 'average' in friendly_name:
                answer = f"The average {friendly_name.replace('avg ', '').replace('average ', '')} is **{value}**."
            elif 'sum' in friendly_name or 'total' in friendly_name:
                answer = f"The total {friendly_name.replace('sum ', '').replace('total ', '')} is **{value}**."
            else:
                answer = f"The {friendly_name} is **{value}**."
            
            return {
                "answer": answer,
                "sql_query": sql_query if Config.DEBUG_MODE else None,
                "error_code": None,
                "error_details": None,
                "execution_time_ms": execution_time,
                "fallback_used": False
            }
        
        elif query_type == "EXISTS_CHECK":
            # Handle EXISTS or boolean-like queries
            exists = bool(rows[0][0]) if rows and len(rows) > 0 else False
            return {
                "answer": f"**{'Yes' if exists else 'No'}**",
                "sql_query": sql_query if Config.DEBUG_MODE else None,
                "error_code": None,
                "error_details": None,
                "execution_time_ms": execution_time,
                "fallback_used": False
            }
        
        else:  # LIST or complex queries
            # Determine which tables were queried
            queried_tables = extract_queried_tables(sql_query)
            
            # Filter and redact columns
            processed_rows = process_and_redact_rows(rows, column_names, queried_tables)
            
            # Check if processed rows are empty after filtering
            if not processed_rows:
                return handle_empty_results(question, client_id, sql_query)
            
            # Determine if summarization is needed
            should_summarize = (
                intent.get("requires_summary", False) or 
                ResponseFormatter.should_summarize(question, len(processed_rows), len(column_names))
            )
            
            if should_summarize:
                result = generate_summarized_response(question, processed_rows, sql_query, client_id)
            else:
                result = generate_formatted_response(processed_rows, sql_query)
            
            # Add execution time
            result["execution_time_ms"] = execution_time
            return result
            
    except Exception as e:
        logger.error(f"Error formatting query results: {e}")
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "answer": "I found your information but had trouble displaying it properly. Please try again.",
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": "FORMATTING_ERROR",
            "error_details": str(e) if Config.DEBUG_MODE else None,
            "execution_time_ms": execution_time,
            "fallback_used": False
        }
def detect_sql_query_type(sql_query: str, rows: List[Any], column_names: List[str]) -> str:
    """Detect the type of SQL query based on SQL text and result structure"""
    sql_upper = sql_query.upper()
    
    # Check for COUNT queries
    if 'COUNT(' in sql_upper and len(rows) == 1 and len(column_names) == 1:
        if 'count' in column_names[0].lower():
            return "COUNT"
    
    # Check for other aggregate functions without GROUP BY
    if len(rows) == 1 and len(column_names) == 1 and 'GROUP BY' not in sql_upper:
        col_name = column_names[0].lower()
        if any(func in col_name for func in ['sum', 'avg', 'max', 'min', 'average']):
            return "SINGLE_VALUE"
    
    # Check for GROUP BY or multiple aggregate columns
    if 'GROUP BY' in sql_upper or any(func in sql_upper for func in ['SUM(', 'AVG(', 'MAX(', 'MIN(', 'COUNT(']):
        return "AGGREGATE"
    
    # Check for EXISTS or boolean queries
    if 'EXISTS' in sql_upper or (len(rows) == 1 and len(column_names) == 1 and isinstance(rows[0][0], bool)):
        return "EXISTS_CHECK"
    
    # Default to LIST query
    return "LIST"

def handle_aggregate_results(rows: List[Any], column_names: List[str], sql_query: str, execution_time: int) -> Dict[str, Any]:
    """Handle aggregate query results (GROUP BY, SUM, AVG, etc.) with user-friendly language"""
    try:
        if len(rows) == 1 and len(column_names) <= 2:
            # Single aggregate result
            if len(column_names) == 1:
                value = rows[0][0]
                col_name = column_names[0].replace('_', ' ').title()
                answer = f"**{col_name}**: {value:,}" if isinstance(value, (int, float)) else f"**{col_name}**: {value}"
            else:
                # Two columns, likely a group and its aggregate
                group_col, agg_col = column_names
                group_val, agg_val = rows[0]
                formatted_val = f"{agg_val:,}" if isinstance(agg_val, (int, float)) else str(agg_val)
                answer = f"For **{group_val}**: {formatted_val}"
        else:
            # Multiple aggregate results - format as a friendly breakdown
            answer_parts = ["Here's the breakdown:"]
            for row in rows[:15]:  # Limit to 15 for readability
                if len(column_names) == 2:
                    # GROUP BY with aggregate
                    group_val, agg_val = row[:2]
                    formatted_val = f"{agg_val:,}" if isinstance(agg_val, (int, float)) else str(agg_val)
                    answer_parts.append(f"• **{group_val}**: {formatted_val}")
                else:
                    # Multiple columns - make it conversational
                    row_items = []
                    for col, val in zip(column_names, row):
                        if val is not None:
                            formatted_val = f"{val:,}" if isinstance(val, (int, float)) else str(val)
                            row_items.append(f"**{col.replace('_', ' ').title()}**: {formatted_val}")
                    if row_items:
                        answer_parts.append(f"• {', '.join(row_items)}")
            
            answer = "\n".join(answer_parts)
            
            if len(rows) > 15:
                remaining = len(rows) - 15
                answer += f"\n\n*...and {remaining} more items.*"
        
        return {
            "answer": answer,
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": None,
            "error_details": None,
            "execution_time_ms": execution_time,
            "fallback_used": False
        }
        
    except Exception as e:
        logger.error(f"Error handling aggregate results: {e}")
        return {
            "answer": "I found the data but had trouble organizing it. Please try again.",
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": "FORMATTING_ERROR",
            "error_details": str(e) if Config.DEBUG_MODE else None,
            "execution_time_ms": execution_time,
            "fallback_used": False
        }

def handle_empty_results(question: str, client_id: str, sql_query: str) -> Dict[str, Any]:
    """Handle empty query results with fallback search"""
    logger.info("No results found, attempting fallback search")
    
    try:
        fallback_results = run_fallback_keyword_search(question, client_id)
        if fallback_results:
            # Very brief fallback - just acknowledge we found something related
            return {
                "answer": "I didn't find exact matches. Try rephrasing your question with different terms.",
                "sql_query": sql_query if Config.DEBUG_MODE else None,
                "error_code": None,
                "error_details": None,
                "fallback_used": True
            }
        # If we got here, the query ran, but there is simply no matching data
        # Try to check if the relevant table(s) have any data at all
        queried_tables = extract_queried_tables(sql_query)
        table_has_data = False
        table_empty = False
        checked_tables = []
        if db_engine and queried_tables:
            try:
                with db_engine.connect() as connection:
                    for table in queried_tables:
                        checked_tables.append(table)
                        count_sql = f"SELECT COUNT(*) FROM {table}"
                        result = connection.execute(text(count_sql))
                        count = result.scalar()
                        if count and count > 0:
                            table_has_data = True
                        else:
                            table_empty = True
            except Exception as e:
                logger.error(f"Error checking table data for {queried_tables}: {e}")
        if table_has_data:
            answer = "No matches found. Try different terms."
        elif table_empty:
            answer = "No data available for this type."
        else:
            answer = "No matching information found."
        return {
            "answer": answer,
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": "NO_DATA_FOUND",
            "error_details": None,
            "fallback_used": True
        }
    except Exception as e:
        logger.error(f"Fallback search failed: {e}")
        err_msg = str(e).lower()
        if "permission" in err_msg or "forbidden" in err_msg or "access denied" in err_msg:
            specific = "Access denied."
        elif "connection" in err_msg or "could not connect" in err_msg or "network" in err_msg or "timeout" in err_msg:
            specific = "Connection issue. Try again."
        else:
            specific = f"Error: {e}" if Config.DEBUG_MODE else "Search error. Try again."
        return {
            "answer": specific,
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": "NO_DATA_FOUND",
            "error_details": str(e) if Config.DEBUG_MODE else None,
            "fallback_used": False
        }

def extract_queried_tables(sql_query: str) -> List[str]:
    """Extract table names from SQL query"""
    try:
        table_pattern = r'(?:FROM|JOIN)\s+(?:"?([a-zA-Z0-9_]+)"?)'
        matches = re.findall(table_pattern, sql_query, re.IGNORECASE)
        return [match.lower() for match in matches]
    except Exception as e:
        logger.error(f"Error extracting queried tables: {e}")
        return []

def process_and_redact_rows(rows: List[Any], column_names: List[str], queried_tables: List[str]) -> List[Dict[str, Any]]:
    """Process rows and apply redaction rules"""
    try:
        # Determine which columns to display
        display_columns = set()
        for table_name in queried_tables:
            if table_name in TABLE_SCHEMAS_FOR_CHATBOT:
                configured_columns = TABLE_SCHEMAS_FOR_CHATBOT[table_name].get("return_columns", [])
                display_columns.update(col.lower() for col in configured_columns)
        
        # Fallback to all columns if none configured
        if not display_columns:
            display_columns = set(col.lower() for col in column_names)
        
        processed_rows = []
        for row in rows:
            row_dict = {}
            for i, column_name in enumerate(column_names):
                if column_name.lower() in display_columns:
                    raw_value = row[i]
                    redacted_value = ResponseFormatter.redact_sensitive_data(
                        column_name, raw_value, queried_tables
                    )
                    row_dict[column_name] = redacted_value
            
            if row_dict:  # Only add if there are displayable columns
                processed_rows.append(row_dict)
        
        return processed_rows
        
    except Exception as e:
        logger.error(f"Error processing and redacting rows: {e}")
        raise ChatbotError("Error processing query results", "PROCESSING_ERROR", str(e))

def generate_summarized_response(question: str, processed_rows: List[Dict[str, Any]], sql_query: str, client_id: str) -> Dict[str, Any]:
    """Generate LLM-summarized response"""
    try:
        if not llm:
            raise ChatbotError("LLM service not available for summarization")
        
        # Prepare data for summarization (remove verbose fields)
        summary_data = []
        for row in processed_rows:
            filtered_row = {k: v for k, v in row.items() if not k.lower().endswith('_summary')}
            summary_data.append(filtered_row)
        
        summary_prompt = f"""
        Analyze and summarize the following data for the question: "{question}"
        
        Data to summarize:
        {summary_data[:20]}  # Limit data for prompt size
        
        Instructions:
        - Provide a concise, actionable summary
        - Highlight key metrics, trends, and important findings
        - Use bullet points for clarity
        - Include specific numbers and counts where relevant
        - Don't mention client IDs or internal identifiers
        - If data shows concerning security issues, highlight them appropriately
        - Keep the response under 300 words
        """
        
        summary_response = llm.invoke(summary_prompt)
        answer = summary_response.content.strip()
        
        return {
            "answer": answer,
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": None,
            "error_details": None,
            "fallback_used": False
        }
        
    except Exception as e:
        logger.error(f"Error generating summarized response: {e}")
        # Fallback to formatted response
        return generate_formatted_response(processed_rows, sql_query)

def generate_formatted_response(processed_rows: List[Dict[str, Any]], sql_query: str) -> Dict[str, Any]:
    """Generate formatted list response"""
    try:
        if not processed_rows:
            # This should not happen as we check for empty results earlier
            return {
                "answer": "I couldn't find any matching records after applying filters.",
                "sql_query": sql_query if Config.DEBUG_MODE else None,
                "error_code": "NO_DATA_FOUND",
                "error_details": None,
                "fallback_used": False
            }
        
        response_parts = []
        display_limit = 10
        
        for i, row in enumerate(processed_rows[:display_limit]):
            row_parts = []
            for column, value in row.items():
                if value is not None and str(value).strip():
                    row_parts.append(f"**{column}**: {value}")
            
            if row_parts:
                response_parts.append(f"• {', '.join(row_parts)}")
        
        answer = "Here's what I found:\n\n" + "\n".join(response_parts)
        
        if len(processed_rows) > display_limit:
            remaining = len(processed_rows) - display_limit
            answer += f"\n\n*...and {remaining} more items.*"
        
        return {
            "answer": answer,
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": None,
            "error_details": None,
            "fallback_used": False
        }
        
    except Exception as e:
        logger.error(f"Error generating formatted response: {e}")
        return {
            "answer": "I found the information but had trouble displaying it properly. Please try again.",
            "sql_query": sql_query if Config.DEBUG_MODE else None,
            "error_code": "FORMATTING_ERROR",
            "error_details": str(e) if Config.DEBUG_MODE else None,
            "fallback_used": False
        }

def ask_database_chatbot(question: str, client_id: str) -> Dict[str, Any]:
    """Main chatbot logic with comprehensive error handling"""
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing question for client {client_id}: {question}")
        
        # Validate inputs
        if not QueryValidator.validate_client_id(client_id):
            raise ValidationError("Invalid client ID format")
        
        if not question.strip():
            raise ValidationError("Question cannot be empty")
        
        # Check service availability
        if not all([db_engine, llm, sql_database_utility]):
            raise ChatbotError("Chatbot services are not fully initialized. Please try again later.")
        
        # Detect query intent
        intent = detect_query_intent(question)
        
        # Try deterministic planner first
        sql_query = plan_and_build_sql(question, client_id, intent)
        planner_used = sql_query is not None
        
        if not planner_used:
            # Fallback to LLM generation
            logger.info("Using LLM for SQL generation")
            sql_query = generate_sql_with_retry(question, client_id)
        
        if not sql_query:
            raise SQLGenerationError("Failed to generate SQL query for your question")
        
        # Apply security filters
        safe_sql_query = enforce_client_security_filter(sql_query, client_id)
        
        # Execute query
        rows, column_names = execute_query_with_retry(safe_sql_query)
        
        # Format results
        result = format_query_results(rows, column_names, question, safe_sql_query, client_id, intent)
        
        # Add execution time
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        result["execution_time_ms"] = execution_time
        
        logger.info(f"Query processed successfully in {execution_time}ms")
        return result
        
    except (ValidationError, SQLGenerationError, QueryExecutionError, DatabaseConnectionError) as e:
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.error(f"Known error in chatbot processing: {e}")
        
        return {
            "answer": e.message,
            "sql_query": None,
            "error_code": e.error_code,
            "error_details": e.details if Config.DEBUG_MODE else None,
            "execution_time_ms": execution_time,
            "fallback_used": False
        }
        
    except Exception as e:
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.error(f"Unexpected error in chatbot processing: {e}\n{traceback.format_exc()}")
        
        return {
            "answer": "I encountered an unexpected error while processing your question. Please try again or contact support if the issue persists.",
            "sql_query": None,
            "error_code": "UNEXPECTED_ERROR",
            "error_details": str(e) if Config.DEBUG_MODE else None,
            "execution_time_ms": execution_time,
            "fallback_used": False
        }

# --- Deterministic Query Planner (Enhanced) ---
def plan_and_build_sql(question: str, client_id: str, intent: Dict[str, Any]) -> Optional[str]:
    """Enhanced deterministic SQL planner"""
    try:
        primary_table = choose_primary_table(question)
        if not primary_table:
            logger.debug("No primary table identified by planner")
            return None
        
        sql_query = build_sql_by_table(primary_table, intent, client_id)
        
        if sql_query:
            logger.info(f"Planner generated SQL for table {primary_table}: {sql_query}")
        
        return sql_query
        
    except Exception as e:
        logger.error(f"Error in deterministic planner: {e}")
        return None

def choose_primary_table(question: str) -> Optional[str]:
    """Enhanced table selection logic"""
    question_lower = question.lower()
    
    # Specific patterns for user's selected SDEs
    my_sde_patterns = [
        "my sde", "my selected sde", "my chosen sde", "what are my sde",
        "show my sde", "list my sde", "how many sde", "selected sde",
        "show sde", "list sde", "what sde", "sde ", " sde", "sdes ",
        "sensitive data element", "data element"
    ]
    
    if any(pattern in question_lower for pattern in my_sde_patterns):
        return "client_selected_sdes"
    
    # Direct alias mapping
    for alias, table_mapping in SEMANTIC_ALIASES.items():
        if alias in question_lower:
            return table_mapping.split('|')[0]  # Take first if multiple options
    
    # Keyword-based detection with priority
    table_keywords = {
        "scan_findings": ["finding", "alert", "issue", "detection", "vulnerability"],
        "data_stores": ["data source", "store", "storage", "repository", "database"],
        "client_selected_sdes": ["sde", "sensitive data", "data element", "selected", "chosen", "picked"],
        "risk_assessments": ["assessment", "risk score", "evaluation"],
        "dp_policies": ["policy", "policies", "governance", "compliance rule"],
        "scan_baselines": ["baseline", "scan status", "scanning"],
        "reports": ["report", "documentation"],
        "client_connections": ["connection", "integration"],
        "pii_catalog": ["pii", "personal data", "personally identifiable"]
    }
    
    # Score each table based on keyword matches
    table_scores = {}
    for table, keywords in table_keywords.items():
        score = sum(1 for keyword in keywords if keyword in question_lower)
        if score > 0:
            table_scores[table] = score
    
    # Return table with highest score
    if table_scores:
        best_table = max(table_scores, key=table_scores.get)
        logger.debug(f"Selected table {best_table} with score {table_scores[best_table]}")
        return best_table
    
    return None

def build_sql_by_table(table: str, intent: Dict[str, Any], client_id: str) -> Optional[str]:
    """Enhanced SQL building for specific tables"""
    try:
        where_parts = build_where_conditions(table, intent)
        limit = intent.get("top_n", Config.DEFAULT_QUERY_LIMIT)
        query_type = intent.get("type", QueryType.LIST)
        
        # Handle COUNT queries
        if query_type == QueryType.COUNT:
            return build_count_query(table, where_parts, client_id)
        
        # Handle GROUP BY queries
        if intent.get("group_by"):
            return build_group_by_query(table, intent, where_parts, client_id)
        
        # Handle LIST queries
        return build_list_query(table, where_parts, client_id, limit)
        
    except Exception as e:
        logger.error(f"Error building SQL for table {table}: {e}")
        return None

def build_where_conditions(table: str, intent: Dict[str, Any]) -> List[str]:
    """Build WHERE conditions based on intent"""
    conditions = []
    
    # Risk level filter
    if intent.get("risk_level") and table in ("scan_findings", "pii_catalog"):
        conditions.append(f"risk_level = '{intent['risk_level']}'")
    
    # Time window filter
    time_window = intent.get("time_window")
    if time_window:
        number, unit = time_window
        time_condition = build_time_condition(table, number, unit)
        if time_condition:
            conditions.append(time_condition)
    
    return conditions

def build_time_condition(table: str, number: int, unit: str) -> Optional[str]:
    """Build time-based WHERE condition"""
    time_columns = {
        "scan_findings": ("scan_timestamp", "TIMESTAMP"),
        "scan_baselines": ("last_scan_timestamp", "TIMESTAMP"),
        "risk_assessments": ("last_scan_time", "TIMESTAMP"),
        "reports": ("created_at", "TIMESTAMP"),
        "scans": ("scan_data", "DATE"),
    }
    
    if table not in time_columns:
        return None
    
    column, data_type = time_columns[table]
    
    if data_type == "TIMESTAMP":
        return f"TO_TIMESTAMP({column}, 'YYYY-MM-DD HH24:MI:SS') >= CURRENT_TIMESTAMP - INTERVAL '{number} {unit}'"
    elif data_type == "DATE":
        return f"TO_DATE({column}, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '{number} {unit}'"
    
    return None

def build_count_query(table: str, where_parts: List[str], client_id: str) -> str:
    """Build COUNT query"""
    where_clause = " AND ".join(where_parts) if where_parts else "TRUE"
    
    if is_client_specific_table(table):
        where_clause = f"client_id = '{client_id}' AND ({where_clause})" if where_parts else f"client_id = '{client_id}'"
    
    return f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"

def build_group_by_query(table: str, intent: Dict[str, Any], where_parts: List[str], client_id: str) -> str:
    """Build GROUP BY query"""
    group_column = intent["group_by"]
    where_clause = " AND ".join(where_parts) if where_parts else "TRUE"
    
    if is_client_specific_table(table):
        where_clause = f"client_id = '{client_id}' AND ({where_clause})" if where_parts else f"client_id = '{client_id}'"
    
    return f"SELECT {group_column}, COUNT(*) AS total FROM {table} WHERE {where_clause} GROUP BY {group_column} ORDER BY total DESC"

def build_list_query(table: str, where_parts: List[str], client_id: str, limit: int) -> str:
    """Build LIST query"""
    # Special handling for client_selected_sdes - query it directly without JOIN to sdes
    if table == "client_selected_sdes":
        where_clause = " AND ".join(where_parts) if where_parts else "TRUE"
        return f"""SELECT pattern_name, sensitivity, protection_method, selected_at 
                  FROM client_selected_sdes 
                  WHERE client_id = '{client_id}' AND ({where_clause})
                  ORDER BY selected_at DESC 
                  LIMIT {limit}"""
    
    # Get preferred columns for the table
    table_config = TABLE_SCHEMAS_FOR_CHATBOT.get(table, {})
    return_columns = table_config.get("return_columns", ["*"])
    
    if return_columns and return_columns != ["*"]:
        columns_sql = ", ".join(return_columns)
    else:
        columns_sql = "*"
    
    where_clause = " AND ".join(where_parts) if where_parts else "TRUE"
    
    if is_client_specific_table(table):
        where_clause = f"client_id = '{client_id}' AND ({where_clause})" if where_parts else f"client_id = '{client_id}'"
    
    # Add appropriate ORDER BY
    order_by = get_default_order_by(table)
    order_clause = f" ORDER BY {order_by}" if order_by else ""
    
    return f"SELECT {columns_sql} FROM {table} WHERE {where_clause}{order_clause} LIMIT {limit}"

def get_default_order_by(table: str) -> Optional[str]:
    """Get default ORDER BY clause for table"""
    order_mappings = {
        "scan_findings": "TO_TIMESTAMP(scan_timestamp, 'YYYY-MM-DD HH24:MI:SS') DESC",
        "scan_baselines": "TO_TIMESTAMP(last_scan_timestamp, 'YYYY-MM-DD HH24:MI:SS') DESC",
        "risk_assessments": "TO_TIMESTAMP(last_scan_time, 'YYYY-MM-DD HH24:MI:SS') DESC",
        "reports": "TO_TIMESTAMP(created_at, 'YYYY-MM-DD HH24:MI:SS') DESC",
        "data_stores": "discovery_timestamp DESC",
        "client_prof": "created_at DESC"
    }
    
    return order_mappings.get(table)

# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    """Enhanced startup with better error handling"""
    logger.info("FastAPI startup event triggered")
    try:
        initialize_services()
        logger.info("Chatbot API startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Don't fail startup - let health check indicate status

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Risk Analyzer Chatbot API", 
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs" if Config.DEBUG_MODE else "disabled"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint"""
    check_time = datetime.now()
    
    try:
        db_connected = False
        llm_available = llm is not None
        error_details = None
        
        # Test database connection
        if db_engine:
            try:
                with db_engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                    db_connected = True
            except Exception as db_error:
                error_details = f"Database check failed: {str(db_error)}"
                logger.error(error_details)
        
        # Test LLM availability
        if llm:
            try:
                test_response = llm.invoke("test")
                if not test_response.content:
                    llm_available = False
                    error_details = "LLM test failed"
            except Exception as llm_error:
                llm_available = False
                error_details = f"LLM check failed: {str(llm_error)}"
                logger.error(error_details)
        
        overall_status = "healthy" if (db_connected and llm_available) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            database_connected=db_connected,
            llm_available=llm_available,
            available_tables=available_tables,
            timestamp=check_time.isoformat(),
            error_details=error_details if Config.DEBUG_MODE else None
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            llm_available=False,
            available_tables=[],
            timestamp=check_time.isoformat(),
            error_details=str(e) if Config.DEBUG_MODE else None
        )

@app.get("/clients", response_model=List[Client])
async def get_clients():
    """Enhanced client fetching with error handling"""
    logger.info("Fetching clients for dropdown")
    
    if not db_engine:
        raise DatabaseConnectionError("Database not initialized")
    
    try:
        with db_engine.connect() as connection:
            query = """
                SELECT client_id, full_name, company_name 
                FROM client_prof 
                WHERE client_id IS NOT NULL 
                ORDER BY COALESCE(full_name, company_name, client_id) 
                LIMIT 1000
            """
            result = connection.execute(text(query))
            
            clients = []
            for row in result:
                display_name = row.full_name or row.company_name or row.client_id
                clients.append(Client(
                    client_id=row.client_id,
                    client_name=display_name
                ))
            
            logger.info(f"Successfully fetched {len(clients)} clients")
            return clients
            
    except Exception as e:
        logger.error(f"Error fetching clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve client list. Please try again later."
        )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Enhanced chat endpoint with comprehensive error handling"""
    request_start = datetime.now()
    
    try:
        logger.info(f"Chat request from client {request.client_id}: {request.question}")
        
        # Process the question
        result = ask_database_chatbot(request.question, request.client_id)
        
        # Create response
        response = ChatResponse(
            answer=result["answer"],
            sql_query=result.get("sql_query"),
            error_code=result.get("error_code"),
            error_details=result.get("error_details"),
            timestamp=request_start.isoformat(),
            execution_time_ms=result.get("execution_time_ms"),
            fallback_used=result.get("fallback_used", False)
        )
        
        return response
        
    except ValidationError as e:
        logger.warning(f"Validation error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )

@app.get("/tables")
async def get_tables():
    """Get available tables endpoint"""
    try:
        global available_tables
        if not available_tables and db_engine:
            # Try to refresh available tables
            available_tables = DatabaseManager.get_available_tables(db_engine)
        return {
            "tables": available_tables,
            "count": len(available_tables),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve table information"
        )

@app.post("/test-sql")
async def test_sql_endpoint(request: Dict[str, str]):
    """Test SQL query endpoint (debug only)"""
    if not Config.DEBUG_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production mode"
        )
    
    sql_query = request.get("sql_query", "").strip()
    
    if not sql_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SQL query is required"
        )
    
    if not QueryValidator.validate_sql_safety(sql_query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SQL query failed safety validation"
        )
    
    try:
        rows, column_names = execute_query_with_retry(sql_query)
        
        # Convert to serializable format
        data = []
        for row in rows[:100]:  # Limit for testing
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = str(row[i]) if row[i] is not None else None
            data.append(row_dict)
        
        return {
            "success": True,
            "row_count": len(rows),
            "columns": list(column_names),
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing SQL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )

# --- Additional Utility Endpoints ---
@app.get("/metrics")
async def get_metrics():
    """Get basic API metrics (if debug mode)"""
    if not Config.DEBUG_MODE:
        raise HTTPException(status_code=404, detail="Not available in production")
    
    return {
        "debug_mode": Config.DEBUG_MODE,
        "available_tables_count": len(available_tables),
        "services_initialized": all([db_engine, llm, sql_database_utility]),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # For local development only
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=Config.DEBUG_MODE,
        log_level="debug" if Config.DEBUG_MODE else "info"
    )