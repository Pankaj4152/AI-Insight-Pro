# AI-Insight-Pro

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-Proprietary-blue?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge" alt="PRs Welcome" />
</p>

> **Advanced AI-Powered Data Analytics, Risk Assessment & Compliance Platform**

AI-Insight-Pro is an enterprise-grade platform designed for software development environment (SDE) selection, data store connectivity, security risk assessment, and compliance monitoring. Powered by microservice architecture and intelligent AI agents, it provides deep data discovery, automated risk scoring, and interactive compliance reporting.

---

## 🚀 Key Capabilities

- 🤖 **AI Chatbot Assistants**: Interactive query engines for data store findings, compliance guidance, and risk inspection.
- 🔌 **Multi-Data Store Connectivity**: Connectors service integrating PostgreSQL, MySQL, Google BigQuery, and Google Cloud Storage.
- 🛡️ **Risk Assessment Engine**: Automated scanning for vulnerabilities, data privacy risks, and security score generation.
- 📜 **Compliance Reporting**: Standardized report generation aligned with security frameworks (GDPR, HIPAA, SOC2).
- 🔍 **Automated Data Discovery**: Intelligent crawling and metadata cataloging across connected data infrastructure.
- 📊 **Interactive Dashboard**: Modern React dashboard for real-time progress visualization and insights.

---

## 🏗️ Architecture & Directory Overview

```
AI-Insight-Pro/
├── Frontend/                           # Interactive React 19 web dashboard
├── connectors-service/                 # FastAPI service for multi-DB connectivity (SQL/NoSQL/Cloud)
├── login-system/                       # Authentication & user management service
├── compliance/                         # Compliance auditing & framework evaluation module
├── risk_assessment_report_gen_service/ # Automated risk assessment & PDF report generation service
├── client_chatbot/                     # Client-facing AI conversational assistant
├── website-chatbot/                    # Public site chatbot module
└── agents/                             # Autonomous AI agents for automated data discovery & workflows
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend UI** | React 19, React Router v7, Lucide Icons, Chart.js / Recharts |
| **Backend Services** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **Data Connectors** | `psycopg2-binary`, `mysql-connector-python`, `google-cloud-bigquery`, `google-cloud-storage` |
| **Data Processing & ML** | Python Data Science Stack, Pandas, Custom AI Agents |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18.0 or higher
- **Python** v3.10 or higher
- **pip** package manager

---

### 1️⃣ Setting Up the Frontend

```bash
# Navigate to the Frontend directory
cd Frontend

# Install dependencies
npm install

# Start the development server
npm start
```
The dashboard will run locally at `http://localhost:3000`.

---

### 2️⃣ Setting Up the Connectors Service (Backend)

```bash
# Navigate to the connectors service
cd connectors-service

# Create and activate virtual environment (Optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Launch the FastAPI service
uvicorn app.main:app --reload
```
The API documentation will be available at `http://localhost:8000/docs`.

---

## 🔒 Security & Compliance

- **Role-Based Access Control (RBAC)**: Secure access points integrated via `login-system`.
- **Encrypted Connectors**: Secure credential management for data storage integrations.
- **Audit Logging**: Traceability across all automated risk and discovery scans.

---

## 🤝 Team & Organization

- **Organization**: AIPlaneTech India
- **Maintained by**: Team A - AIPlaneTech India

---

## 📄 License

Proprietary Software - Developed by AIPlaneTech India. All rights reserved.