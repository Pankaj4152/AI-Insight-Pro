
# AI-Insight-Pro: Consolidated Data Documentation

This document provides a comprehensive overview of the AI-Insight-Pro platform, its features, and its functionalities. It is intended to be a central repository of information for the website's chatbot.

## 1. Introduction to AI-Insight-Pro

AI-Insight-Pro is a comprehensive AI-powered system designed to help businesses identify, assess, and manage data privacy risks across distributed data sources. The platform acts as a privacy-aware AI system that performs automated data discovery, sensitive data detection, risk assessment, and compliance monitoring.

## 2. Core Features

- **Automated Data Discovery**: Scans and identifies data from connected sources like PostgreSQL, BigQuery, GCS, and MySQL.
- **Sensitive Data Element (SDE) Detection**: Detects sensitive data elements like PII, financial data, and healthcare data.
- **Risk Scoring and Confidence Calculation**: Calculates risk scores and confidence levels for identified vulnerabilities.
- **LLM-Generated Summaries and Business-Ready Reports**: Generates insightful summaries and reports.
- **Compliance Monitoring**: Aligns with frameworks like GDPR, HIPAA, CCPA, and the DPDP Act.
- **User-Friendly Interface**: A React-based frontend for easy interaction.
- **CLI and API Access**: Offers a command-line interface and API for programmatic access.

## 3. How it Works: The Workflow

The AI-Insight-Pro workflow is divided into frontend and backend processes:

### Frontend Workflow

1.  **Login**: Secure user authentication and session management.
2.  **SDE Selection**: Users can select, add, edit, or delete Sensitive Data Elements (SDEs) to be scanned.
3.  **Model Registry**: Manage and register custom AI models for SDE detection.
4.  **Data Connection**: Connect to various data sources.
5.  **Dashboard**: View a comprehensive overview of data sources, SDEs, scans, and risk scores.
6.  **Risk and Compliance**: Advanced assessment of risks with a risk matrix and trend charts.
7.  **Report Generation**: Generate reports in PDF, HTML, and LaTeX formats.

### Backend Workflow

1.  **User Management**: Handles user authentication, profiles, and roles.
2.  **Data Source Connection Engine**: Manages connections to various data sources.
3.  **SDE Processing Engine**: Ingests, preprocesses, detects, and classifies SDEs.
4.  **Risk Assessment Engine**: Calculates risk scores based on various factors.
5.  **API Endpoints**: Provides a set of APIs for integration.
6.  **Security and Compliance**: Ensures data protection and compliance.

## 4. Supported Data Sources

AI-Insight-Pro supports a wide range of data sources:

- **Cloud Databases**: Google BigQuery, PostgreSQL, MySQL.
- **Cloud Storage**: Google Cloud Storage (GCS) Buckets, AWS S3.
- **On-Premise Databases**: Local PostgreSQL and MySQL servers.
- **File Systems**: Local and network file storage.

## 5. Data Security and Compliance

- **Data Encryption**: End-to-end encryption for data in transit (TLS 1.3) and at rest (AES-256).
- **Secure Credential Storage**: Encrypted storage of data source credentials.
- **Access Controls**: Strong user authentication, session management, and Role-Based Access Control (RBAC).
- **Audit Logging**: Comprehensive logging of all significant actions.
- **Supported Compliance Frameworks**: GDPR, HIPAA, CCPA, and the DPDP Act.

## 6. User Roles and Management

The platform has a robust User Management System with the following roles:

-   **Admin**:
    -   **Permissions**: Has full system access. Can manage users, roles, system settings, and has all permissions of a Compliance Officer.
    -   **Responsibilities**: System administration, user management, and overall platform configuration.

-   **Compliance Officer**:
    -   **Permissions**: Can monitor and manage compliance across multiple clients or departments. Can view all reports, dashboards, and risk assessments. Can manage SDEs and compliance policies.
    -   **Responsibilities**: Ensuring the organization adheres to data privacy regulations, managing compliance-related tasks, and overseeing risk management activities.

- 

## 7. Reporting and Analytics

AI-Insight-Pro offers a variety of report types:

-   **Executive Summary Reports**: High-level overviews for management.
-   **Technical Risk Assessments**: Detailed reports for technical teams.
-   **Compliance Gap Analysis**: Reports highlighting deviations from regulatory requirements.
-   **Data Inventory Reports**: Comprehensive listings of all discovered data sources and SDEs.

Reports can be downloaded in **PDF, HTML, and LaTeX** formats.

## 8. API and Integration

The backend is powered by FastAPI and provides a comprehensive set of API endpoints for:

-   **Data Source Management**: `/api/connect`, `/api/test-connection`, `/api/connections`, `/api/connections/{id}`
-   **Scanning and Analysis**: `/api/scan/start`, `/api/scan/status/{job_id}`, `/api/scan/results/{scan_id}`, `/api/risk/assessment`
-   **Dashboard and Reporting**: `/api/dashboard/metrics`, `/api/risk/analysis`, `/api/report/generate`, `/api/report/download/{report_id}`
-   **SDE Management**: `/api/sde`, `/api/sde/{sde_id}`

## 9. Future Enhancements

-   **Agent Orchestration with DAGs**: For automated and scalable pipeline scheduling.
-   **Enhanced Compliance Policy Mapping**: Deeper automation for mapping scan findings to regulatory requirements.
-   **SOC2 Report Generator**: Automated generation of SOC2 reports.
-   **Advanced RBAC**: More granular Role-Based Access Control.
-   **Threat Intelligence Feed Mapping**: Integration with external threat intelligence feeds.

## 10. Frequently Asked Questions (FAQ)

-   **What does AI-Insight-Pro do?**
    It automates data privacy risk assessment, SDE detection, and compliance reporting.
-   **What data sources are supported?**
    Databases (SQLite, MySQL, PostgreSQL), files (CSV, Excel, JSON, etc.), and cloud sources (GCS, BigQuery, AWS S3).
-   **What is an SDE?**
    A Sensitive Data Element, such as email, phone number, credit card number, etc.
-   **How is risk calculated?**
    Using a weighted scoring approach based on the number and sensitivity of findings.
-   **What report formats are available?**
    PDF and visual dashboards.

## 11. Troubleshooting

-   **Chatbot Not Starting**: Check your internet connection and try using offline mode.
-   **Dashboard Not Loading**: Connect a data source first and refresh the page.
-   **Connection Test Failed**: Check your credentials and internet connection.
-   **Can't Log In**: Check your email and password, and check for caps lock.
-   **No Scan Results**: Connect a data source and run a scan.
-   **Can't Download Report**: Wait for the scan to complete and check browser settings.
