import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
from typing import Optional, List
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.company_name = os.getenv("COMPANY_NAME", "AI-Insight-Pro")
        self.company_website = os.getenv("COMPANY_WEBSITE", "https://frontend-1071432896229.asia-south2.run.app")
        self.support_email = os.getenv("SUPPORT_EMAIL", "aiplanetech@aipglobal.in")

        if not self.email_address or not self.email_password:
            logger.warning("Email credentials not configured. Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
    
    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Send an email with HTML content and optional attachments
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text version (optional)
            attachments: List of file paths to attach (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, 
                          user_email: str, 
                          full_name: str, 
                          username: str, 
                          company_name: str) -> bool:
        """
        Send a welcome email to a newly registered user
        
        Args:
            user_email: User's email address
            full_name: User's full name
            username: User's username
            company_name: User's company name
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        from email_templates import WelcomeEmailTemplate
        
        template = WelcomeEmailTemplate()
        
        subject = f"Welcome to {self.company_name} - Your Account is Ready!"
        
        html_content = template.generate_welcome_email(
            full_name=full_name,
            username=username,
            company_name=company_name,
            user_email=user_email,
            platform_name=self.company_name,
            platform_website=self.company_website,
            support_email=self.support_email
        )
        
        text_content = template.generate_welcome_text(
            full_name=full_name,
            username=username,
            platform_name=self.company_name,
            platform_website=self.company_website,
            support_email=self.support_email
        )
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    def send_password_reset_email(self, user_email: str, full_name: str, reset_link: str) -> bool:
        """
        Send a password reset email
        
        Args:
            user_email: User's email address
            full_name: User's full name
            reset_link: Password reset link
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        from email_templates import PasswordResetEmailTemplate
        
        template = PasswordResetEmailTemplate()
        
        subject = f"Password Reset Request - {self.company_name}"
        
        html_content = template.generate_password_reset_email(
            full_name=full_name,
            reset_link=reset_link,
            platform_name=self.company_name,
            support_email=self.support_email
        )
        
        text_content = template.generate_password_reset_text(
            full_name=full_name,
            reset_link=reset_link,
            platform_name=self.company_name,
            support_email=self.support_email
        )
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    def send_notification_email(self, 
                               user_email: str, 
                               full_name: str, 
                               notification_type: str,
                               message: str,
                               action_url: Optional[str] = None) -> bool:
        """
        Send a general notification email
        
        Args:
            user_email: User's email address
            full_name: User's full name
            notification_type: Type of notification (e.g., "Security Alert", "Account Update")
            message: Notification message
            action_url: Optional URL for user action
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        from email_templates import NotificationEmailTemplate
        
        template = NotificationEmailTemplate()
        
        subject = f"{notification_type} - {self.company_name}"
        
        html_content = template.generate_notification_email(
            full_name=full_name,
            notification_type=notification_type,
            message=message,
            action_url=action_url,
            platform_name=self.company_name,
            support_email=self.support_email
        )
        
        text_content = template.generate_notification_text(
            full_name=full_name,
            notification_type=notification_type,
            message=message,
            action_url=action_url,
            platform_name=self.company_name,
            support_email=self.support_email
        )
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    def send_compliance_officer_welcome_email(self, 
                                             user_email: str, 
                                             full_name: str, 
                                             username: str, 
                                             company_name: str) -> bool:
        """
        Send a welcome email to a newly registered compliance officer
        
        Args:
            user_email: Compliance officer's email address
            full_name: Compliance officer's full name
            username: Compliance officer's username
            company_name: Company name
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        from email_templates import ComplianceOfficerWelcomeEmailTemplate
        
        template = ComplianceOfficerWelcomeEmailTemplate()
        
        subject = f"Welcome to {self.company_name} - Compliance Officer Access"
        
        html_content = template.generate_compliance_officer_welcome_email(
            full_name=full_name,
            username=username,
            company_name=company_name,
            user_email=user_email,
            platform_name=self.company_name,
            platform_website=self.company_website,
            support_email=self.support_email
        )
        
        text_content = template.generate_compliance_officer_welcome_text(
            full_name=full_name,
            username=username,
            company_name=company_name,
            platform_name=self.company_name,
            platform_website=self.company_website,
            support_email=self.support_email
        )
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

# Singleton instance
email_service = EmailService()
