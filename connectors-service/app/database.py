import psycopg2
import json
from datetime import datetime
from app.config import DB_URL

# Optional database connectors
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


def validate_and_normalize_credentials(connections_type, connection_cred):
    """Validate and normalize connection credentials based on connection type."""
    if isinstance(connection_cred, str):
        cred_dict = json.loads(connection_cred)
    else:
        cred_dict = connection_cred.copy()
    
    # Normalize database connection credentials
    if connections_type in ['postgresql', 'mysql']:
        # Ensure required fields are present
        required_fields = ['host', 'port', 'username', 'password']
        database_field = 'databaseName' if 'databaseName' in cred_dict else 'database'
        
        if database_field not in cred_dict:
            raise ValueError(f"Missing database name in {connections_type} credentials")
        
        for field in required_fields:
            if field not in cred_dict:
                raise ValueError(f"Missing required field '{field}' in {connections_type} credentials")
        
        # Standardize the database name field to 'databaseName'
        if 'database' in cred_dict and 'databaseName' not in cred_dict:
            cred_dict['databaseName'] = cred_dict['database']
            del cred_dict['database']
    
    return cred_dict


def insert_client_connection(client_id, connections_type, connection_cred, conn_name, dataset_id=None):
    """Insert a new client connection record and return the connection ID."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        # Validate and normalize credentials
        normalized_creds = validate_and_normalize_credentials(connections_type, connection_cred)
        
        # For database connections (postgresql, mysql), use the database name as dataset_id if not provided
        if dataset_id is None and connections_type in ['postgresql', 'mysql']:
            dataset_id = normalized_creds.get('databaseName')
            if not dataset_id:
                raise ValueError(f"No database name found in {connections_type} credentials for dataset_id")
        
        cursor.execute(
            """
            INSERT INTO client_connections (client_id, connections_type, connection_cred, conn_name, dataset_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING cli_conn_id
            """,
            (client_id, connections_type, json.dumps(normalized_creds), conn_name, dataset_id)
        )
        cli_conn_id = cursor.fetchone()[0]
        conn.commit()
        return cli_conn_id
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        conn.rollback()
        raise ValueError(f"Invalid credentials for {connections_type}: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def insert_client_connection_history(cli_conn_id, connection_status):
    """Insert a connection history record."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO client_connection_history (cli_conn_id, connection_status, last_used)
            VALUES (%s, %s, %s)
            """,
            (cli_conn_id, connection_status, datetime.utcnow())
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_latest_cli_conn_id(client_id, connections_type):
    """Get the latest connection ID for a client and connection type."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT cli_conn_id FROM client_connections
            WHERE client_id = %s AND connections_type = %s
            ORDER BY cli_conn_id DESC LIMIT 1
            """,
            (client_id, connections_type)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
        conn.close()


def get_connection_history(client_id):
    """Get connection history for a client."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT h.cli_conn_hist_id, h.cli_conn_id, c.conn_name, c.connections_type,c.dataset_id, 
                   h.connection_status, h.last_used, h.created_at
            FROM client_connection_history h
            JOIN client_connections c ON h.cli_conn_id = c.cli_conn_id
            WHERE c.client_id = %s
            ORDER BY h.cli_conn_hist_id DESC
            """,
            (client_id,)
        )
        rows = cursor.fetchall()
        history = [
            {
                "cli_conn_hist_id": r[0],
                "cli_conn_id": r[1],
                "conn_name": r[2],
                "connections_type": r[3],
                "dataset_id": r[4],
                "connection_status": r[5],
                "last_used": r[6].isoformat() if r[6] else None,
                "created_at": r[7].isoformat() if r[7] else None,
            }
            for r in rows
        ]
        return {"history": history}
    finally:
        cursor.close()
        conn.close()


def get_industry_classifications():
    """Get all industry classifications."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT industry_classification FROM isde_catalogue;")
        rows = cur.fetchall()
        industries = [row[0] for row in rows if row[0]]
        return {"industries": industries}
    finally:
        cur.close()
        conn.close()


def get_sde_by_industry(selected_industry):
    """Get SDEs by industry classification."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
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
    finally:
        cur.close()
        conn.close()


def add_sde(sde_data):
    """Add a new SDE to the catalogue."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        sde_key = "sde" + sde_data.name
        cur.execute(
            """
            INSERT INTO isde_catalogue (sde_key, name, data_type, sensitivity, regex, classification_level, industry_classification)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (sde_key, sde_data.name, sde_data.data_type, sde_data.sensitivity, 
             sde_data.regex, sde_data.classification, sde_data.selected_industry)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"status": "success", "id": new_id, "sde_key": sde_key}
    finally:
        cur.close()
        conn.close()


def test_database_connection(connection_cred, connections_type):
    """Test a database connection with the provided credentials."""
    try:
        # Validate and normalize credentials first
        normalized_creds = validate_and_normalize_credentials(connections_type, connection_cred)
        
        if connections_type == 'postgresql':
            # psycopg2 is already imported at the top
            test_conn = psycopg2.connect(
                host=normalized_creds['host'],
                port=normalized_creds['port'],
                database=normalized_creds['databaseName'],
                user=normalized_creds['username'],
                password=normalized_creds['password']
            )
            test_conn.close()
            return {"status": "success", "message": "PostgreSQL connection successful"}
            
        elif connections_type == 'mysql':
            if not MYSQL_AVAILABLE:
                return {"status": "error", "message": "MySQL connector not available. Install mysql-connector-python"}
            
            test_conn = mysql.connector.connect(
                host=normalized_creds['host'],
                port=normalized_creds['port'],
                database=normalized_creds['databaseName'],
                user=normalized_creds['username'],
                password=normalized_creds['password']
            )
            test_conn.close()
            return {"status": "success", "message": "MySQL connection successful"}
        
        else:
            return {"status": "error", "message": f"Connection testing not implemented for {connections_type}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}


def get_connection_credentials(client_id, connections_type):
    """Get connection credentials for a client and connection type."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT connection_cred, dataset_id FROM client_connections
            WHERE client_id = %s AND connections_type = %s
            ORDER BY cli_conn_id DESC LIMIT 1
            """,
            (client_id, connections_type)
        )
        row = cursor.fetchone()
        if row:
            connection_cred, dataset_id = row
            if isinstance(connection_cred, str):
                cred_dict = json.loads(connection_cred)
            else:
                cred_dict = connection_cred
            
            return {
                "credentials": cred_dict,
                "dataset_id": dataset_id,
                "status": "success"
            }
        else:
            return {
                "status": "error", 
                "message": f"No credentials found for client {client_id} with connection type {connections_type}"
            }
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
