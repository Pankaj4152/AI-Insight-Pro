from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import Dict
import json
import time
import mysql.connector
import psycopg2
from google.cloud import bigquery, storage
from google.oauth2 import service_account

from app.models import MySQLCredentials, PostgreSQLCredentials
from app.database import insert_client_connection, insert_client_connection_history, get_latest_cli_conn_id
from app.utils import upload_credentials_via_cloud_run, delete_local_credentials, create_credentials_file

router = APIRouter(prefix="/validate", tags=["validation"])


# JSON-based validation endpoints (recommended)
@router.post("/mysql-json")
async def validate_mysql_json(payload: Dict = Body(...)):
    """Validate MySQL connection using JSON payload"""
    local_file_path = None
    try:
        # Extract data from JSON payload
        creds_data = payload.get("creds")
        client_id = payload.get("client_id")
        conn_name = payload.get("conn_name")
        
        if not (creds_data and client_id and conn_name):
            raise HTTPException(status_code=400, detail="creds, client_id, and conn_name are required")
        
        # Validate credentials structure
        creds = MySQLCredentials(**creds_data)
        
        # Step 1: Save credentials locally first
        filename = f"mysql-{conn_name}-{int(time.time())}.json"
        local_file_path = create_credentials_file(client_id, filename, creds.dict())
        
        # Step 2: Validate credentials
        conn = mysql.connector.connect(
            host=creds.host,
            port=creds.port,
            database=creds.databaseName,
            user=creds.username,
            password=creds.password
        )
        conn.close()
        
        # Step 3: Upload to GCS bucket via Cloud Run service
        blob_name = upload_credentials_via_cloud_run(client_id, local_file_path)
        
        # Step 4: Delete local credentials after successful upload
        delete_local_credentials(local_file_path)
        
        # Step 5: Store connection info in database with blob_name
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type="mysql",
            connection_cred={"location": blob_name},
            conn_name=conn_name,
            dataset_id=creds.databaseName
        )
        insert_client_connection_history(cli_conn_id, "success")
        return {"status": "success", "message": "MySQL credentials are valid and uploaded to GCS.", "blob_name": blob_name}
    except Exception as e:
        # Clean up local file if it exists and validation failed
        if local_file_path:
            delete_local_credentials(local_file_path)
        
        cli_conn_id = get_latest_cli_conn_id(client_id, "mysql")
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/postgresql-json")
async def validate_postgresql_json(payload: Dict = Body(...)):
    """Validate PostgreSQL connection using JSON payload"""
    local_file_path = None
    try:
        # Extract data from JSON payload
        creds_data = payload.get("creds")
        client_id = payload.get("client_id")
        conn_name = payload.get("conn_name")
        
        if not (creds_data and client_id and conn_name):
            raise HTTPException(status_code=400, detail="creds, client_id, and conn_name are required")
        
        # Validate credentials structure
        creds = PostgreSQLCredentials(**creds_data)
        
        # Step 1: Save credentials locally first
        filename = f"postgresql-{conn_name}-{int(time.time())}.json"
        local_file_path = create_credentials_file(client_id, filename, creds.dict())
        
        # Step 2: Validate credentials
        conn = psycopg2.connect(
            host=creds.host,
            port=creds.port,
            dbname=creds.databaseName,
            user=creds.username,
            password=creds.password
        )
        conn.close()
        
        # Step 3: Upload to GCS bucket via Cloud Run service
        blob_name = upload_credentials_via_cloud_run(client_id, local_file_path)
        
        # Step 4: Delete local credentials after successful upload
        delete_local_credentials(local_file_path)
        
        # Step 5: Store connection info in database with blob_name
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type="postgresql",
            connection_cred={"location": blob_name},
            conn_name=conn_name,
            dataset_id=creds.databaseName
        )
        insert_client_connection_history(cli_conn_id, "success")
        return {"status": "success", "message": "PostgreSQL credentials are valid and uploaded to GCS.", "blob_name": blob_name}
    except Exception as e:
        # Clean up local file if it exists and validation failed
        if local_file_path:
            delete_local_credentials(local_file_path)
        
        cli_conn_id = get_latest_cli_conn_id(client_id, "postgresql")
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        raise HTTPException(status_code=400, detail=str(e))


# Original form-based endpoints (kept for backward compatibility)
@router.post("/mysql")
async def validate_mysql(
    host: str = Form(...),
    port: int = Form(...),
    databaseName: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    conn_name: str = Form(...)
):
    try:
        # Create credentials object from form data
        creds = MySQLCredentials(
            host=host,
            port=port,
            databaseName=databaseName,
            username=username,
            password=password
        )
        
        # Step 1: Validate credentials
        conn = mysql.connector.connect(
            host=creds.host,
            port=creds.port,
            database=creds.databaseName,
            user=creds.username,
            password=creds.password
        )
        conn.close()
        
        # Step 2: Store connection info in database with credentials as JSON
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type="mysql",
            connection_cred=creds.dict(),
            conn_name=conn_name,
            dataset_id=creds.databaseName
        )
        insert_client_connection_history(cli_conn_id, "success")
        return {"status": "success", "message": "MySQL credentials are valid and stored securely."}
    except Exception as e:
        cli_conn_id = get_latest_cli_conn_id(client_id, "mysql")
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/postgresql")
async def validate_postgresql(
    host: str = Form(...),
    port: int = Form(...),
    databaseName: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    conn_name: str = Form(...)
):
    try:
        # Create credentials object from form data
        creds = PostgreSQLCredentials(
            host=host,
            port=port,
            databaseName=databaseName,
            username=username,
            password=password
        )
        
        # Step 1: Test database connection
        conn = psycopg2.connect(
            host=creds.host,
            port=creds.port,
            dbname=creds.databaseName,
            user=creds.username,
            password=creds.password
        )
        conn.close()
        
        # Step 2: Store connection info directly in database (no file upload for DB credentials)
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type="postgresql",
            connection_cred=creds.dict(),  # Store credentials directly as JSON
            conn_name=conn_name,
            dataset_id=creds.databaseName
        )
        insert_client_connection_history(cli_conn_id, "success")
        return {"status": "success", "message": "PostgreSQL credentials are valid and stored securely."}
    except Exception as e:
        cli_conn_id = get_latest_cli_conn_id(client_id, "postgresql")
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/gcp-bucket")
async def validate_gcp_bucket(
    credentialFile: UploadFile = File(...),
    projectId: str = Form(...),
    datasetId: str = Form(...),
    client_id: str = Form(...),
    conn_name: str = Form(...),
    connections_type: str = Form(...),
):
    file_path = None
    try:
        # Step 1: Save the uploaded file
        filename = f"{projectId}-{datasetId}-{int(time.time())}.json"
        content = await credentialFile.read()
        file_path = create_credentials_file(client_id, filename, json.loads(content))

        # Step 2: Test the credentials
        with open(file_path, 'r') as f:
            creds_json = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(creds_json)
        client = storage.Client(credentials=credentials, project=projectId)
        bucket = client.get_bucket(datasetId)
        blobs = list(bucket.list_blobs(max_results=1))

        # Step 3: Upload to GCS bucket via Cloud Run service
        blob_name = upload_credentials_via_cloud_run(client_id, file_path)

        # Step 4: Delete local credentials after successful upload
        delete_local_credentials(file_path)

        # Step 5: Store connection info in the database with blob_name
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type=connections_type,
            connection_cred={"location": blob_name},
            conn_name=conn_name,
            dataset_id=datasetId
        )
        insert_client_connection_history(cli_conn_id, "success")
        return {"status": "success", "message": "GCP Bucket credentials are valid and uploaded to GCS.", "blob_name": blob_name}
    except Exception as e:
        # Clean up local file if it exists and validation failed
        if file_path:
            delete_local_credentials(file_path)
        
        cli_conn_id = get_latest_cli_conn_id(client_id, connections_type)
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/gcp-bucket-json")
async def validate_gcp_bucket_json(payload: Dict = Body(...)):
    local_file_path = None
    try:
        projectId = payload.get("projectId")
        datasetId = payload.get("datasetId")
        creds_json = payload.get("credentials")
        client_id = payload.get("client_id")
        conn_name = payload.get("conn_name")
        connections_type = payload.get("connections_type", "gcp")
        
        if not (projectId and datasetId and creds_json and client_id and conn_name):
            raise HTTPException(status_code=400, detail="projectId, datasetId, credentials, client_id, and conn_name are required.")
        
        # Step 1: Validate credentials
        credentials = service_account.Credentials.from_service_account_info(creds_json)
        client = storage.Client(credentials=credentials, project=projectId)
        bucket = client.get_bucket(datasetId)
        blobs = list(bucket.list_blobs(max_results=1))
        
        # Step 2: Save credentials locally first
        filename = f"{projectId}-{datasetId}-{int(time.time())}.json"
        local_file_path = create_credentials_file(client_id, filename, creds_json)
        
        # Step 3: Upload to GCS bucket via Cloud Run service
        blob_name = upload_credentials_via_cloud_run(client_id, local_file_path)
        
        # Step 4: Delete local credentials after successful upload
        delete_local_credentials(local_file_path)
        
        # Step 5: Store connection info in database with blob_name
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type=connections_type,
            connection_cred={"location": blob_name},
            conn_name=conn_name,
            dataset_id=datasetId
        )
        insert_client_connection_history(cli_conn_id, "success")
        
        return {"status": "success", "message": "GCP Bucket credentials are valid and uploaded to GCS.", "blob_name": blob_name}
    except Exception as e:
        # Clean up local file if it exists and validation failed
        if local_file_path:
            delete_local_credentials(local_file_path)
        
        cli_conn_id = get_latest_cli_conn_id(client_id, "gcp")
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bigquery")
async def validate_bigquery(
    projectId: str = Form(...), 
    datasetId: str = Form(...), 
    credentialFile: UploadFile = File(...), 
    client_id: str = Form(...), 
    conn_name: str = Form(...)
):
    file_path = None
    try:
        content = await credentialFile.read()
        # Step 1: Save the uploaded file
        filename = f"{projectId}-{datasetId}-{int(time.time())}.json"
        file_path = create_credentials_file(client_id, filename, json.loads(content))
        
        # Step 2: Validate credentials
        credentials = service_account.Credentials.from_service_account_info(json.loads(content))
        client = bigquery.Client(credentials=credentials, project=projectId)

        # Check if dataset exists
        dataset_ref = client.dataset(datasetId)
        client.get_dataset(dataset_ref)  # Will raise exception if not found

        # Step 3: Upload to GCS bucket via Cloud Run service
        blob_name = upload_credentials_via_cloud_run(client_id, file_path)

        # Step 4: Delete local credentials after successful upload
        delete_local_credentials(file_path)

        # Step 5: Store connection info in database with blob_name
        cli_conn_id = insert_client_connection(
            client_id=client_id,
            connections_type="bigquery",
            connection_cred={"location": blob_name},
            conn_name=conn_name,
            dataset_id=datasetId
        )
        insert_client_connection_history(cli_conn_id, "success")
        return {"success": True, "message": "BigQuery credentials and dataset are valid and uploaded to GCS.", "blob_name": blob_name}
    except Exception as e:
        # Clean up local file if it exists and validation failed
        if file_path:
            delete_local_credentials(file_path)
        
        cli_conn_id = get_latest_cli_conn_id(client_id, "bigquery")
        if cli_conn_id:
            insert_client_connection_history(cli_conn_id, "fail")
        return {"success": False, "message": f"Validation failed: {str(e)}"}
