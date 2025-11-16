from datetime import datetime
from typing import Optional

class BaseEmailTemplate:
    """Base class for email templates with common styling and structure"""
    
    @staticmethod
    def get_base_styles():
        """Common CSS styles for all email templates"""
        return """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            .email-container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 28px;
                font-weight: 300;
            }
            .content {
                padding: 40px 30px;
            }
            .welcome-message {
                font-size: 24px;
                color: #667eea;
                margin-bottom: 20px;
                text-align: center;
            }
            .user-info {
                background-color: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 25px 0;
                border-radius: 4px;
            }
            .cta-button {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
                transition: all 0.3s ease;
            }
            .cta-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            .feature-list {
                list-style: none;
                padding: 0;
            }
            .feature-list li {
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
            .feature-list li:before {
                content: "✓";
                color: #28a745;
                font-weight: bold;
                margin-right: 10px;
            }
            .footer {
                background-color: #f8f9fa;
                padding: 30px 20px;
                text-align: center;
                border-top: 1px solid #eee;
                font-size: 14px;
                color: #6c757d;
            }
            .social-links {
                margin: 20px 0;
            }
            .social-links a {
                color: #667eea;
                text-decoration: none;
                margin: 0 10px;
            }
            .warning {
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
                color: #856404;
            }
            .success {
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
                color: #155724;
            }
            @media only screen and (max-width: 600px) {
                .email-container {
                    width: 100% !important;
                }
                .content {
                    padding: 20px !important;
                }
                .header {
                    padding: 20px !important;
                }
            }
        </style>
        """

class WelcomeEmailTemplate(BaseEmailTemplate):
    """Template for welcome emails sent to new users"""
    
    def generate_welcome_email(self, 
                              full_name: str, 
                              username: str, 
                              company_name: str,
                              user_email: str,
                              platform_name: str,
                              platform_website: str,
                              support_email: str) -> str:
        """Generate HTML content for welcome email"""
        
        current_year = datetime.now().year
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to {platform_name}</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>{platform_name}</h1>
                    <p>Advanced Data Protection & Privacy Solutions</p>
                </div>
                
                <div class="content">
                    <h2 class="welcome-message">🎉 Welcome to the Future of Data Protection!</h2>
                    
                    <p>Dear <strong>{full_name}</strong>,</p>
                    
                    <p>Welcome to {platform_name}! We're thrilled to have you join our community of forward-thinking organizations committed to robust data protection and privacy compliance.</p>
                    
                    <div class="user-info">
                        <h3>Your Account Details:</h3>
                        <ul>
                            <li><strong>Full Name:</strong> {full_name}</li>
                            <li><strong>Username:</strong> {username}</li>
                            <li><strong>Email:</strong> {user_email}</li>
                            <li><strong>Company:</strong> {company_name}</li>
                            <li><strong>Registration Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                        </ul>
                    </div>
                    
                    <div class="success">
                        <strong>🔐 Your account is now active and ready to use!</strong>
                    </div>
                    
                    <h3>What's Next? Get Started with These Features:</h3>
                    <ul class="feature-list">
                        <li><strong>Data Discovery:</strong> Automatically discover and classify sensitive data across your infrastructure</li>
                        <li><strong>Risk Assessment:</strong> Comprehensive PII risk scoring and vulnerability analysis</li>
                        <li><strong>Smart Data Protection:</strong> AI-powered data anonymization and encryption recommendations</li>
                        <li><strong>Audit & Reporting:</strong> Detailed compliance reports and audit trails</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{platform_website}/dashboard" class="cta-button">
                            🚀 Access Your Dashboard
                        </a>
                    </div>
                    
                    <h3>Quick Start Guide:</h3>
                    <ol>
                        <li><strong>Connect Your Data Sources:</strong> Link databases, cloud storage, and applications</li>
                        <li><strong>Run Discovery:</strong> Let our AI discover and classify your sensitive data</li>
                        <li><strong>Review Risk Assessment:</strong> Understand your data protection posture</li>
                        <li><strong>Implement Recommendations:</strong> Apply suggested security measures</li>
                        <li><strong>Monitor Compliance:</strong> Track your ongoing compliance status</li>
                    </ol>
                    
                    <div class="warning">
                        <strong>Security Notice:</strong> Keep your login credentials secure and never share them with anyone. If you didn't create this account, please contact our support team immediately.
                    </div>
                    
                    <h3>Need Help Getting Started?</h3>
                    <p>Our team is here to help you every step of the way:</p>
                    <ul>
                        <li>💬 <a href="{platform_website}/support">Live Chat Support</a></li>
                        <li>📧 Email us at <a href="mailto:{support_email}">{support_email}</a></li>
                    </ul>
                    
                    <p>Thank you for choosing {platform_name} to protect your organization's most valuable asset - your data.</p>
                    
                    <p>Best regards,<br>
                    <strong>The {platform_name} Team</strong></p>
                </div>
                
                <div class="footer">
                    <div class="social-links">
                        <a href="{platform_website}">Website</a> |
                        <a href="{platform_website}/about">About Us</a> |
                        <a href="{platform_website}/contact">Contact Us</a> |
                        <a href="mailto:{support_email}">Support</a>
                    </div>
                    <p>&copy; {current_year} {platform_name}. All rights reserved.</p>
                    <p>You received this email because you created an account with us.</p>
                    <p style="font-size: 12px; color: #999;">
                        If you didn't create this account, please ignore this email or contact support.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_welcome_text(self, 
                             full_name: str, 
                             username: str,
                             platform_name: str,
                             platform_website: str,
                             support_email: str) -> str:
        """Generate plain text version of welcome email"""
        
        text_content = f"""
Welcome to {platform_name}!

Dear {full_name},

Welcome to {platform_name}! We're thrilled to have you join our community of organizations committed to robust data protection and privacy compliance.

Your Account Details:
- Username: {username}
- Registration Date: {datetime.now().strftime('%B %d, %Y')}

Your account is now active and ready to use!

Get Started with These Features:
- Data Discovery: Automatically discover and classify sensitive data
- Risk Assessment: Comprehensive PII risk scoring
- Smart Data Protection: AI-powered security recommendations
- Audit & Reporting: Detailed compliance reports

Quick Start:
1. Connect Your Data Sources
2. Run Discovery
3. Review Risk Assessment
4. Implement Recommendations
5. Monitor Compliance

Access your dashboard: {platform_website}/dashboard

Need Help?
- Documentation: {platform_website}/docs
- Support: {support_email}

Thank you for choosing {platform_name}!

Best regards,
The {platform_name} Team

---
© {datetime.now().year} {platform_name}. All rights reserved.
You received this email because you created an account with us.
If you didn't create this account, please contact support.
        """
        
        return text_content

class PasswordResetEmailTemplate(BaseEmailTemplate):
    """Template for password reset emails"""
    
    def generate_password_reset_email(self, 
                                     full_name: str, 
                                     reset_link: str,
                                     platform_name: str,
                                     support_email: str) -> str:
        """Generate HTML content for password reset email"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - {platform_name}</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>{platform_name}</h1>
                    <p>Password Reset Request</p>
                </div>
                
                <div class="content">
                    <h2 class="welcome-message">🔐 Password Reset Request</h2>
                    
                    <p>Dear <strong>{full_name}</strong>,</p>
                    
                    <p>We received a request to reset your password for your {platform_name} account.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" class="cta-button">
                            Reset Your Password
                        </a>
                    </div>
                    
                    <div class="warning">
                        <strong>Important:</strong> This link will expire in 24 hours for security reasons.
                    </div>
                    
                    <p>If you didn't request this password reset, please ignore this email or contact our support team if you have concerns.</p>
                    
                    <p>For security reasons, this link can only be used once.</p>
                    
                    <p>If you're having trouble clicking the button, copy and paste this URL into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                        {reset_link}
                    </p>
                    
                    <p>Best regards,<br>
                    <strong>The {platform_name} Security Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>If you need help, contact us at <a href="mailto:{support_email}">{support_email}</a></p>
                    <p>&copy; {datetime.now().year} {platform_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_password_reset_text(self, 
                                    full_name: str, 
                                    reset_link: str,
                                    platform_name: str,
                                    support_email: str) -> str:
        """Generate plain text version of password reset email"""
        
        text_content = f"""
Password Reset Request - {platform_name}

Dear {full_name},

We received a request to reset your password for your {platform_name} account.

Reset your password: {reset_link}

Important: This link will expire in 24 hours for security reasons.

If you didn't request this password reset, please ignore this email or contact our support team if you have concerns.

For security reasons, this link can only be used once.

Best regards,
The {platform_name} Security Team

---
If you need help, contact us at {support_email}
© {datetime.now().year} {platform_name}. All rights reserved.
        """
        
        return text_content

class NotificationEmailTemplate(BaseEmailTemplate):
    """Template for general notification emails"""
    
    def generate_notification_email(self, 
                                   full_name: str, 
                                   notification_type: str,
                                   message: str,
                                   action_url: Optional[str],
                                   platform_name: str,
                                   support_email: str) -> str:
        """Generate HTML content for notification email"""
        
        # Choose icon based on notification type
        icon = "🔔"
        if "security" in notification_type.lower():
            icon = "🔒"
        elif "success" in notification_type.lower():
            icon = "✅"
        elif "warning" in notification_type.lower():
            icon = "⚠️"
        elif "update" in notification_type.lower():
            icon = "🔄"
        
        action_button = ""
        if action_url:
            action_button = f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="{action_url}" class="cta-button">
                    Take Action
                </a>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{notification_type} - {platform_name}</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>{platform_name}</h1>
                    <p>{notification_type}</p>
                </div>
                
                <div class="content">
                    <h2 class="welcome-message">{icon} {notification_type}</h2>
                    
                    <p>Dear <strong>{full_name}</strong>,</p>
                    
                    <div class="user-info">
                        {message}
                    </div>
                    
                    {action_button}
                    
                    <p>If you have any questions or concerns, please don't hesitate to contact our support team.</p>
                    
                    <p>Best regards,<br>
                    <strong>The {platform_name} Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>If you need help, contact us at <a href="mailto:{support_email}">{support_email}</a></p>
                    <p>&copy; {datetime.now().year} {platform_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_notification_text(self, 
                                  full_name: str, 
                                  notification_type: str,
                                  message: str,
                                  action_url: Optional[str],
                                  platform_name: str,
                                  support_email: str) -> str:
        """Generate plain text version of notification email"""
        
        action_text = ""
        if action_url:
            action_text = f"\n\nTake action: {action_url}\n"
        
        text_content = f"""
{notification_type} - {platform_name}

Dear {full_name},

{message}
{action_text}
If you have any questions or concerns, please don't hesitate to contact our support team.

Best regards,
The {platform_name} Team

---
If you need help, contact us at {support_email}
© {datetime.now().year} {platform_name}. All rights reserved.
        """
        
        return text_content

class ComplianceOfficerWelcomeEmailTemplate(BaseEmailTemplate):
    """Template for welcome emails sent to new compliance officers"""
    
    def generate_compliance_officer_welcome_email(self, 
                                                  full_name: str, 
                                                  username: str, 
                                                  company_name: str,
                                                  user_email: str,
                                                  platform_name: str,
                                                  platform_website: str,
                                                  support_email: str) -> str:
        """Generate HTML content for compliance officer welcome email"""
        
        current_year = datetime.now().year
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to {platform_name} - Compliance Officer</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>{platform_name}</h1>
                    <p>Compliance & Risk Management Portal</p>
                </div>
                
                <div class="content">
                    <h2 class="welcome-message">🛡️ Welcome to Your Compliance Dashboard!</h2>
                    
                    <p>Dear <strong>{full_name}</strong>,</p>
                    
                    <p>Welcome to {platform_name}! Your Compliance Officer account has been successfully created. You now have access to essential compliance monitoring and risk assessment tools tailored specifically for your role.</p>
                    
                    <div class="user-info">
                        <h3>Your Account Details:</h3>
                        <ul>
                            <li><strong>Full Name:</strong> {full_name}</li>
                            <li><strong>Username:</strong> {username}</li>
                            <li><strong>Email:</strong> {user_email}</li>
                            <li><strong>Company:</strong> {company_name}</li>
                            <li><strong>Role:</strong> Compliance Officer</li>
                            <li><strong>Registration Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                        </ul>
                    </div>
                    
                    <div class="success">
                        <strong>Your compliance officer account is now active and ready to use!</strong>
                    </div>
                    
                    <h3>Your Access Permissions - Compliance Officer Features:</h3>
                    <ul class="feature-list">
                        <li><strong>Dashboard:</strong> Overview of compliance status and key metrics</li>
                        <li><strong>Risk Assessment:</strong> View and analyze data protection risk assessments</li>
                        <li><strong>Compliance Reports:</strong> Generate and review detailed compliance reports</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{platform_website}/compliance-dashboard" class="cta-button">
                            🚀 Access Your Compliance Dashboard
                        </a>
                    </div>
                    
                    <h3>Getting Started as a Compliance Officer:</h3>
                    <ol>
                        <li><strong>Access Dashboard:</strong> Review overall compliance status and metrics</li>
                        <li><strong>Review Risk Assessments:</strong> Examine current risk evaluation reports</li>
                        <li><strong>Generate Reports:</strong> Create compliance reports for stakeholders</li>
                        <li><strong>Monitor Compliance:</strong> Track ongoing compliance performance</li>
                    </ol>
                    
                    <div class="warning">
                        <strong>Security Notice:</strong> As a Compliance Officer, you have access to sensitive compliance data. Keep your login credentials secure and never share them with anyone. If you didn't create this account, please contact our support team immediately.
                    </div>
                    
                    <div style="background-color: #e8f4fd; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <h4 style="margin-top: 0; color: #1976D2;">📋 Role-Specific Access</h4>
                        <p style="margin-bottom: 0;">Your account provides compliance-focused access to monitor data protection adherence, review risk assessments, and generate compliance reports. For additional features or access requests, please contact your system administrator.</p>
                    </div>
                    
                    <h3>Need Help Getting Started?</h3>
                    <p>Our Support team is here to help you:</p>
                    <ul>
                        <li>💬 <a href="{platform_website}">Support Chat</a></li>
                        <li>📧 Email us at <a href="mailto:{support_email}">{support_email}</a></li>
                    </ul>
                    
                    <p>Thank you for joining {platform_name} as a Compliance Officer. We look forward to supporting your compliance monitoring and reporting needs.</p>
                    
                    <p>Best regards,<br>
                    <strong>The {platform_name} Team</strong></p>
                </div>
                
                <div class="footer">
                    <div class="social-links">
                        <a href="{platform_website}">Website</a> |
                        <a href="{platform_website}/role-login">Compliance Center</a> |
                        <a href="{platform_website}/contact">Contact Us</a> |
                        <a href="mailto:{support_email}">Support</a>
                    </div>
                    <p>&copy; {current_year} {platform_name}. All rights reserved.</p>
                    <p>You received this email because a Compliance Officer account was created for you.</p>
                    <p style="font-size: 12px; color: #999;">
                        If you didn't request this account, please contact support immediately.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_compliance_officer_welcome_text(self, 
                                                full_name: str, 
                                                username: str,
                                                company_name: str,
                                                platform_name: str,
                                                platform_website: str,
                                                support_email: str) -> str:
        """Generate plain text version of compliance officer welcome email"""
        
        text_content = f"""
Welcome to {platform_name} - Compliance Officer Portal!

Dear {full_name},

Welcome to {platform_name}! Your Compliance Officer account has been successfully created.

Your Account Details:
- Username: {username}
- Company: {company_name}
- Role: Compliance Officer
- Registration Date: {datetime.now().strftime('%B %d, %Y')}

Your compliance officer account is now active and ready to use!

Your Access Permissions - Compliance Officer Features:
- Dashboard: Overview of compliance status and key metrics
- Risk Assessment: View and analyze data protection risk assessments  
- Compliance Reports: Generate and review detailed compliance reports

Getting Started as a Compliance Officer:
1. Access Dashboard: Review overall compliance status and metrics
2. Review Risk Assessments: Examine current risk evaluation reports
3. Generate Reports: Create compliance reports for stakeholders
4. Monitor Compliance: Track ongoing compliance performance

Access your compliance dashboard: {platform_website}/role-login

Role-Specific Access:
Your account provides compliance-focused access to monitor data protection adherence, review risk assessments, and generate compliance reports. For additional features or access requests, please contact your system administrator.


Thank you for joining {platform_name} as a Compliance Officer.

Best regards,
The {platform_name} Team

---
© {datetime.now().year} {platform_name}. All rights reserved.
You received this email because a Compliance Officer account was created for you.
If you didn't request this account, please contact support immediately.
        """
        
        return text_content
