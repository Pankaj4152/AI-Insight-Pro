// API base URLs from environment variables for deployment flexibility
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "https://report-risk-gen-1071432896229.asia-south2.run.app";
const API_BASE_URL_CONNECTOR = process.env.REACT_APP_API_BASE_URL_CONNECTOR || "https://storage-connectors-1071432896229.asia-south2.run.app";
const API_BASE_URL_DRIVER = process.env.REACT_APP_API_BASE_URL_DRIVER || "https://agents-1071432896229.asia-south2.run.app";
const API_BASE_URL_CHATBOT = process.env.REACT_APP_API_BASE_URL_CHATBOT || "https://aees-web-chatbot-1071432896229.asia-south2.run.app";
const API_BASE_URL_CLIENT_CHATBOT = process.env.REACT_APP_API_BASE_URL_CLIENT_CHATBOT || "https://client-db-chatbot-1071432896229.asia-south2.run.app";
const API_LOGIN_URL = process.env.REACT_APP_API_LOGIN_URL || "https://ai-insight-pro-login-1071432896229.asia-south2.run.app";
const API_RISK_ANALYSER = process.env.REACT_APP_API_RISK_ANALYSER || "https://risk-analyzer-1071432896229.asia-south2.run.app";
const API_BASE_URL_COMPLIANCE = process.env.REACT_APP_API_BASE_URL_COMPLIANCE || "https://compliance-app-1071432896229.asia-south2.run.app";

export { API_BASE_URL, API_LOGIN_URL, API_BASE_URL_CONNECTOR, API_BASE_URL_DRIVER, API_BASE_URL_CHATBOT, API_BASE_URL_CLIENT_CHATBOT, API_RISK_ANALYSER, API_BASE_URL_COMPLIANCE };