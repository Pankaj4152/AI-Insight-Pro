from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import psycopg2
import uuid
from psycopg2.extras import RealDictCursor # <-- IMPORT THIS
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
import requests
import logging
from email_service import email_service

# --- ENV & Firebase Initialization ---
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary storage for verified admin data during signup process
# In production, consider using Redis or database session storage
verified_admins_storage = {}

private_key = os.environ.get("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n')

firebase_credentials = {
    "type": os.environ.get("FIREBASE_TYPE"),
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": private_key,
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
}
cred = credentials.Certificate(firebase_credentials)
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

# --- FastAPI App & CORS ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB Setup (PostgreSQL) ---
DATABASE_URL = os.getenv("DB_URL")
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def insert_client_postgresql(client_id: str, full_name: str, username: str, email: str,
                             company_name: str, Industry: str, Country: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO client_prof(client_id, full_name, username, email, company_name, Industry, Country, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (client_id, full_name, username, email, company_name, Industry, Country, datetime.utcnow()))
        conn.commit()
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'username' in str(e):
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="User already exists")
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def is_username_unique_postgresql(username: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM client_prof WHERE username=%s', (username,))
        exists = cursor.fetchone() is not None
        return not exists
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def is_compliance_username_unique(username: str) -> bool:
    """Check if username is unique in role_base table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM role_base WHERE role_username=%s', (username,))
        exists = cursor.fetchone() is not None
        return not exists
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def is_email_unique_across_system(email: str) -> bool:
    """Check if email is unique across both client_prof and role_base tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check in client_prof table
        cursor.execute('SELECT 1 FROM client_prof WHERE email=%s', (email,))
        exists_in_client = cursor.fetchone() is not None

        # Check in role_base table
        cursor.execute('SELECT 1 FROM role_base WHERE role_email=%s', (email,))
        exists_in_role = cursor.fetchone() is not None

        return not (exists_in_client or exists_in_role)
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def check_company_exists(company_name: str) -> bool:
    """Check if company exists in client_prof table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM client_prof WHERE company_name=%s', (company_name,))
        exists = cursor.fetchone() is not None
        return exists
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def validate_admin_credentials(admin_username: str, admin_email: str, company_name: str):
    """Validate admin credentials against client_prof table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT client_id FROM client_prof
            WHERE username=%s AND email=%s AND company_name=%s
        ''', (admin_username, admin_email, company_name))
        admin_data = cursor.fetchone()
        return admin_data[0] if admin_data else None
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def insert_compliance_officer(role_client_id: str, full_name: str, username: str,
                            email: str, company_name: str, admin_client_ids: list):
    """Insert compliance officer into role_base table with multiple admin client IDs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Prepare admin client IDs (up to 3)
        admin1 = admin_client_ids[0] if len(admin_client_ids) > 0 else None
        admin2 = admin_client_ids[1] if len(admin_client_ids) > 1 else None
        admin3 = admin_client_ids[2] if len(admin_client_ids) > 2 else None

        cursor.execute('''
            INSERT INTO role_base(role_client_id, role_fullname, role_username, role_email,
                                company_name, admin_clientid_1, admin_clientid_2, admin_clientid_3, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (role_client_id, full_name, username, email, company_name, admin1, admin2, admin3, datetime.utcnow()))
        conn.commit()
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'role_username' in str(e):
            raise HTTPException(status_code=400, detail="Username already exists")
        elif 'role_email' in str(e):
            raise HTTPException(status_code=400, detail="Email already exists")
        else:
            raise HTTPException(status_code=400, detail="Compliance officer already exists")
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# --- Modular Auth Logic ---
def firebase_signup(email: str, password: str, display_name: str) -> str:
    try:
        user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        return user.uid
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Firebase error: {str(e)}")

# --- Pydantic Models ---
class SignupRequest(BaseModel):
    full_name: str
    username: str
    email: str
    company_name: str
    password: str
    industry: str
    country: str

class UsernameCheckRequest(BaseModel):
    username: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateProfileRequest(BaseModel):
    client_id: str
    full_name: str
    username: str
    email: str
    company_name: str
    industry: str
    country: str

# --- Additional Email Pydantic Models ---
class SendWelcomeEmailRequest(BaseModel):
    client_id: str

class SendNotificationEmailRequest(BaseModel):
    client_id: str
    notification_type: str
    message: str
    action_url: Optional[str] = None

class TestEmailRequest(BaseModel):
    to_email: str
    subject: str
    message: str

class ComplianceOfficerSignupRequest(BaseModel):
    full_name: str
    username: str
    email: str
    password: str
    company_name: str
    admin_credentials: list[dict]  # List of {"admin_username": str, "admin_email": str}

class ComplianceOfficerLoginRequest(BaseModel):
    email: str
    password: str

class CompanyCheckRequest(BaseModel):
    company_name: str

class AdminVerifyRequest(BaseModel):
    admin_username: str
    admin_email: str
    company_name: str
    session_id: Optional[str] = None  # Optional session ID for storing verified admins

class GetVerifiedAdminsRequest(BaseModel):
    session_id: str

# --- API Endpoints ---
@app.post("/signup")
def signup(data: SignupRequest):
    if not is_username_unique_postgresql(data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    uid = firebase_signup(data.email, data.password, data.username)
    insert_client_postgresql(
        uid,
        data.full_name,
        data.username,
        data.email,
        data.company_name,
        data.industry,
        data.country
    )
    
    # Send welcome email (non-blocking - don't fail signup if email fails)
    try:
        email_sent = email_service.send_welcome_email(
            user_email=data.email,
            full_name=data.full_name,
            username=data.username,
            company_name=data.company_name
        )
        if email_sent:
            logger.info(f"Welcome email sent successfully to {data.email}")
        else:
            logger.warning(f"Failed to send welcome email to {data.email}")
    except Exception as e:
        logger.error(f"Error sending welcome email to {data.email}: {str(e)}")
    
    return {
        "message": "Signup successful", 
        "client_id": uid,
        "email_sent": True  # Always return True to not worry frontend about email issues
    }

@app.post("/check-username")
def check_username(data: UsernameCheckRequest):
    available = is_username_unique_postgresql(data.username)
    return {"available": available}

@app.get("/check-username")
def check_username_get(username: str):
    available = is_username_unique_postgresql(username)
    return {"available": available}

@app.get("/")
def root():
    return {"status": "Auth agent is running"}

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

@app.post("/login")
def login(data: LoginRequest):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": data.email,
        "password": data.password,
        "returnSecureToken": True,
    }
    r = requests.post(url, json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=r.json().get("error", {}).get("message", "Login failed"))

    conn = get_db_connection()
    # UPDATED: Using RealDictCursor to get a dictionary
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            cursor.execute('SELECT client_id, username FROM client_prof WHERE email=%s', (data.email,))
            user_data = cursor.fetchone()
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()

    if not user_data:
        raise HTTPException(status_code=404, detail="User profile not found in local database.")

    return {
        "idToken": r.json()["idToken"],
        "email": data.email,
        "username": user_data['username'],
        "client_id": user_data['client_id'],
        "message": "Login successful"
    }

@app.get("/get-profile")
def get_profile(client_id: str = Query(...)):
    """Get profile using query parameter: /get-profile?client_id=value"""
    return get_profile_data(client_id)

@app.get("/get-profile/{client_id}")
def get_profile_path(client_id: str):
    """Get profile using path parameter: /get-profile/client_id_value"""
    return get_profile_data(client_id)

def get_profile_data(client_id: str):
    """Common function to get profile data"""
    conn = get_db_connection()
    # UPDATED: Using RealDictCursor to get a dictionary
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            # First check in client_prof table
            cursor.execute('''
                SELECT full_name, username, email, company_name, industry, country, 'client' as user_type
                FROM client_prof WHERE client_id = %s
            ''', (client_id,))
            profile_data = cursor.fetchone()

            # If not found in client_prof, check in role_base table
            if not profile_data:
                cursor.execute('''
                    SELECT role_fullname as full_name, role_username as username,
                           role_email as email, company_name, role, 'compliance_officer' as user_type
                    FROM role_base WHERE role_client_id = %s
                ''', (client_id,))
                profile_data = cursor.fetchone()

            if not profile_data:
                raise HTTPException(status_code=404, detail="Profile not found")

            return profile_data

        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()

@app.post("/update-profile")
def update_profile(data: UpdateProfileRequest):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            # First try to update in client_prof table
            cursor.execute('''
                UPDATE client_prof
                SET full_name = %s,
                    username = %s,
                    email = %s,
                    company_name = %s,
                    industry = %s,
                    country = %s
                WHERE client_id = %s
            ''', (
                data.full_name,
                data.username,
                data.email,
                data.company_name,
                data.industry,
                data.country,
                data.client_id
            ))

            # If no rows affected, try role_base table
            if cursor.rowcount == 0:
                cursor.execute('''
                    UPDATE role_base
                    SET role_fullname = %s,
                        role_username = %s,
                        role_email = %s,
                        company_name = %s
                    WHERE role_client_id = %s
                ''', (
                    data.full_name,
                    data.username,
                    data.email,
                    data.company_name,
                    data.client_id
                ))

                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Profile not found")

            conn.commit()
            return {"message": "Profile updated successfully"}
        except psycopg2.Error as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()

# --- Additional Email Endpoints ---
@app.post("/send-welcome-email")
def resend_welcome_email(data: SendWelcomeEmailRequest):
    """Endpoint to resend welcome email to a user"""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            cursor.execute('''
                SELECT full_name, username, email, company_name
                FROM client_prof WHERE client_id = %s
            ''', (data.client_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            # Send welcome email
            email_sent = email_service.send_welcome_email(
                user_email=user_data['email'],
                full_name=user_data['full_name'],
                username=user_data['username'],
                company_name=user_data['company_name']
            )
            
            if email_sent:
                logger.info(f"Welcome email resent successfully to {user_data['email']}")
                return {"message": "Welcome email sent successfully", "email_sent": True}
            else:
                logger.error(f"Failed to send welcome email to {user_data['email']}")
                raise HTTPException(status_code=500, detail="Failed to send email")
                
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()

@app.post("/send-notification-email")
def send_notification_email(data: SendNotificationEmailRequest):
    """Endpoint to send notification emails to users"""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            cursor.execute('''
                SELECT full_name, email
                FROM client_prof WHERE client_id = %s
            ''', (data.client_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            # Send notification email
            email_sent = email_service.send_notification_email(
                user_email=user_data['email'],
                full_name=user_data['full_name'],
                notification_type=data.notification_type,
                message=data.message,
                action_url=data.action_url
            )
            
            if email_sent:
                logger.info(f"Notification email sent successfully to {user_data['email']}")
                return {"message": "Notification email sent successfully", "email_sent": True}
            else:
                logger.error(f"Failed to send notification email to {user_data['email']}")
                raise HTTPException(status_code=500, detail="Failed to send email")
                
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()

@app.post("/test-email")
def send_test_email(data: TestEmailRequest):
    """Endpoint to send test emails (for development/testing)"""
    try:
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email from AiPlane Technologies</h2>
            <p>This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Message:</strong> {data.message}</p>
            <hr>
            <p><em>This is an automated test email.</em></p>
        </body>
        </html>
        """
        
        text_content = f"""
        Test Email from AiPlane Technologies
        
        This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Message: {data.message}
        
        ---
        This is an automated test email.
        """
        
        email_sent = email_service.send_email(
            to_email=data.to_email,
            subject=data.subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if email_sent:
            logger.info(f"Test email sent successfully to {data.to_email}")
            return {"message": "Test email sent successfully", "email_sent": True}
        else:
            logger.error(f"Failed to send test email to {data.to_email}")
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")

@app.get("/email-status")
def get_email_status():
    """Check if email service is configured and ready"""
    try:
        is_configured = (
            email_service.email_address is not None and
            email_service.email_password is not None
        )

        return {
            "email_configured": is_configured,
            "smtp_server": email_service.smtp_server,
            "smtp_port": email_service.smtp_port,
            "company_name": email_service.company_name,
            "company_website": email_service.company_website,
            "support_email": email_service.support_email
        }
    except Exception as e:
        logger.error(f"Error checking email status: {str(e)}")
        return {
            "email_configured": False,
            "error": str(e)
        }

# --- Compliance Officer Endpoints ---

@app.post("/compliance-officer/check-company")
def check_company_exists_endpoint(data: CompanyCheckRequest):
    """Check if company exists in client_prof table"""
    exists = check_company_exists(data.company_name)
    if not exists:
        raise HTTPException(status_code=404, detail="Company not found in our records")
    return {"exists": True, "message": "Company found"}

@app.post("/compliance-officer/verify-admin")
def verify_admin_credentials(data: AdminVerifyRequest):
    """Verify admin credentials and return client_id if valid"""
    admin_client_id = validate_admin_credentials(
        data.admin_username,
        data.admin_email,
        data.company_name
    )

    if not admin_client_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid admin credentials or company name mismatch"
        )

    # Store verified admin data if session_id is provided
    if data.session_id:
        if data.session_id not in verified_admins_storage:
            verified_admins_storage[data.session_id] = []

        # Check if this admin is already verified for this session
        existing_admin = next((admin for admin in verified_admins_storage[data.session_id]
                              if admin["admin_client_id"] == admin_client_id), None)

        if not existing_admin:
            # Limit to 3 admins maximum
            if len(verified_admins_storage[data.session_id]) >= 3:
                raise HTTPException(
                    status_code=400,
                    detail="Maximum 3 admins can be verified"
                )

            verified_admins_storage[data.session_id].append({
                "admin_username": data.admin_username,
                "admin_email": data.admin_email,
                "admin_client_id": admin_client_id
            })

    return {
        "verified": True,
        "admin_client_id": admin_client_id,
        "message": "Admin credentials verified successfully"
    }

@app.post("/compliance-officer/get-verified-admins")
def get_verified_admins(data: GetVerifiedAdminsRequest):
    """Get list of verified admins for a session"""
    if data.session_id not in verified_admins_storage:
        return {"verified_admins": []}

    return {"verified_admins": verified_admins_storage[data.session_id]}

@app.post("/compliance-officer/clear-verified-admins")
def clear_verified_admins(data: GetVerifiedAdminsRequest):
    """Clear verified admins for a session"""
    if data.session_id in verified_admins_storage:
        del verified_admins_storage[data.session_id]

    return {"message": "Verified admins cleared successfully"}

@app.post("/compliance-officer/signup")
def compliance_officer_signup(data: ComplianceOfficerSignupRequest):
    """Final signup endpoint for compliance officers after all verifications"""

    # Log the received data for debugging
    logger.info(f"Received signup data: {data}")

    # Check if username is unique in role_base table
    if not is_compliance_username_unique(data.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email is unique across the entire system
    if not is_email_unique_across_system(data.email):
        raise HTTPException(status_code=400, detail="Email already exists in the system")

    # Validate that we have at least 1 and at most 3 admin credentials
    if not data.admin_credentials or len(data.admin_credentials) == 0:
        raise HTTPException(status_code=400, detail="At least one admin credential is required")

    if len(data.admin_credentials) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 admin credentials allowed")

    # Validate all admin credentials and collect client IDs
    admin_client_ids = []
    for admin_cred in data.admin_credentials:
        admin_client_id = validate_admin_credentials(
            admin_cred["admin_username"],
            admin_cred["admin_email"],
            data.company_name
        )

        if not admin_client_id:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid admin credentials for {admin_cred['admin_username']}"
            )

        admin_client_ids.append(admin_client_id)

    # Create Firebase user for compliance officer
    try:
        uid = firebase_signup(data.email, data.password, data.username)
    except HTTPException as e:
        # Re-raise Firebase errors
        raise e

    # Insert compliance officer into role_base table
    try:
        insert_compliance_officer(
            uid,
            data.full_name,
            data.username,
            data.email,
            data.company_name,
            admin_client_ids
        )
    except HTTPException as e:
        # If database insertion fails, we should ideally delete the Firebase user
        # For now, we'll just raise the error
        raise e

    # Send compliance officer welcome email (non-blocking)
    try:
        email_sent = email_service.send_compliance_officer_welcome_email(
            user_email=data.email,
            full_name=data.full_name,
            username=data.username,
            company_name=data.company_name
        )
        if email_sent:
            logger.info(f"Compliance officer welcome email sent successfully to {data.email}")
        else:
            logger.warning(f"Failed to send compliance officer welcome email to {data.email}")
    except Exception as e:
        logger.error(f"Error sending compliance officer welcome email to {data.email}: {str(e)}")

    return {
        "message": "Compliance officer signup successful",
        "role_client_id": uid,
        "email_sent": True
    }

@app.post("/compliance-officer/login")
def compliance_officer_login(data: ComplianceOfficerLoginRequest):
    """Login endpoint for compliance officers using email and password"""

    # Get officer data and admin usernames in one database connection
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            # Get officer data from role_base table
            cursor.execute('''
                SELECT role_client_id, role_email, role_username, role_fullname, company_name,
                       admin_clientid_1, admin_clientid_2, admin_clientid_3
                FROM role_base WHERE role_email=%s
            ''', (data.email,))
            officer_data = cursor.fetchone()

            if not officer_data:
                raise HTTPException(status_code=404, detail="Compliance officer not found")

            # Get admin usernames for the client IDs to create key-value pairs
            admin_username_mapping = {}

            # Query client_prof to get usernames for each admin client ID
            if officer_data['admin_clientid_1']:
                cursor.execute('SELECT username FROM client_prof WHERE client_id = %s', (officer_data['admin_clientid_1'],))
                admin1_data = cursor.fetchone()
                if admin1_data:
                    admin_username_mapping[admin1_data['username']] = officer_data['admin_clientid_1']

            if officer_data['admin_clientid_2']:
                cursor.execute('SELECT username FROM client_prof WHERE client_id = %s', (officer_data['admin_clientid_2'],))
                admin2_data = cursor.fetchone()
                if admin2_data:
                    admin_username_mapping[admin2_data['username']] = officer_data['admin_clientid_2']

            if officer_data['admin_clientid_3']:
                cursor.execute('SELECT username FROM client_prof WHERE client_id = %s', (officer_data['admin_clientid_3'],))
                admin3_data = cursor.fetchone()
                if admin3_data:
                    admin_username_mapping[admin3_data['username']] = officer_data['admin_clientid_3']

        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()

    # Authenticate with Firebase using email and password
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": data.email,
        "password": data.password,
        "returnSecureToken": True,
    }
    r = requests.post(url, json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=r.json().get("error", {}).get("message", "Login failed"))

    response_data = {
        "idToken": r.json()["idToken"],
        "email": data.email,
        "username": officer_data['role_username'],
        "client_id": officer_data['role_client_id'],
        "role": "compliance-officer",
        "message": "Login successful"
    }

    # Add client_id_list as key-value pairs only if it's not empty
    if admin_username_mapping:
        response_data["client_id_list"] = admin_username_mapping

    return response_data

@app.post("/compliance-officer/check-username")
def check_compliance_username(data: UsernameCheckRequest):
    """Check if username is available for compliance officers"""
    available = is_compliance_username_unique(data.username)
    return {"available": available}

@app.get("/compliance-officer/check-username")
def check_compliance_username_get(username: str):
    """Check if username is available for compliance officers (GET method)"""
    available = is_compliance_username_unique(username)
    return {"available": available}

@app.post("/compliance-officer/check-email")
def check_compliance_email(data: dict):
    """Check if email is available across the entire system"""
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    available = is_email_unique_across_system(email)
    return {"available": available}

@app.get("/compliance-officer/check-email")
def check_compliance_email_get(email: str):
    """Check if email is available across the entire system (GET method)"""
    available = is_email_unique_across_system(email)
    return {"available": available}

@app.post("/compliance-officer/debug-signup-format")
def debug_signup_format(data: dict):
    """Debug endpoint to see what format is being sent"""
    logger.info(f"Debug - Received data: {data}")
    logger.info(f"Debug - Data type: {type(data)}")

    # Check each field
    for key, value in data.items():
        logger.info(f"Debug - {key}: {value} (type: {type(value)})")

    return {
        "received_data": data,
        "expected_format": {
            "full_name": "string",
            "username": "string",
            "email": "string",
            "password": "string",
            "company_name": "string",
            "admin_credentials": [
                {
                    "admin_username": "string",
                    "admin_email": "string"
                }
            ]
        }
    }
