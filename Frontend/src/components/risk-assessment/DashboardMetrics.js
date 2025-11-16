// src/components/risk-assessment/DashboardMetrics.js
import React from 'react';
import { 
  Database, 
  Shield, 
  AlertTriangle, 
  Clock, 
  Target 
} from 'lucide-react';

const DashboardMetrics = ({ metrics, loading }) => {
  const formatRiskScore = (score) => {
    if (score === null || score === undefined) return 'N/A';
    return `${score}/10`;
  };

  const formatLastScanTime = (timestamp) => {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Less than 1 hour ago';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    if (diffInHours < 48) return 'Yesterday';
    return date.toLocaleDateString();
  };

  const getRiskScoreColor = (score) => {
    if (score >= 8) return '#ff4757'; // Red
    if (score >= 6) return '#ffa502'; // Orange
    if (score >= 4) return '#ffb82f'; // Yellow
    return '#2ed573'; // Green
  };

  if (loading) {
    return (
      <div className="dashboard-metrics">
        <h3>Dashboard Overview</h3>
        <div className="metrics-grid">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="metric-card loading">
              <div className="metric-icon skeleton"></div>
              <div className="metric-content">
                <div className="metric-value skeleton"></div>
                <div className="metric-label skeleton"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-metrics">
      <h3>Dashboard Overview</h3>
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <div className="metric-icon-container" style={{ backgroundColor: '#36A2EB' }}>
              <Database size={32} color="white" />
            </div>
            <div className="metric-title-section">
              <div className="metric-label">Total Data Sources</div>
            </div>
          </div>
          <div className="metric-content">
            <div className="metric-value">{metrics.totalDataSources || 0}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <div className="metric-icon-container" style={{ backgroundColor: '#FFCE56' }}>
              <Shield size={32} color="white" />
            </div>
            <div className="metric-title-section">
              <div className="metric-label">Sensitive Data Elements</div>
            </div>
          </div>
          <div className="metric-content">
            <div className="metric-value">{metrics.totalSDEs || 0}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <div className="metric-icon-container" style={{ backgroundColor: '#FF6384' }}>
              <AlertTriangle size={32} color="white" />
            </div>
            <div className="metric-title-section">
              <div className="metric-label">High-Risk Findings</div>
            </div>
          </div>
          <div className="metric-content">
            <div className="metric-value">{metrics.highRiskFindings || 0}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <div className="metric-icon-container" style={{ backgroundColor: '#4BC0C0' }}>
              <Clock size={32} color="white" />
            </div>
            <div className="metric-title-section">
              <div className="metric-label">Last Scan</div>
            </div>
          </div>
          <div className="metric-content">
            <div className="metric-value">{formatLastScanTime(metrics.lastScanTime)}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <div className="metric-icon-container" style={{ backgroundColor: getRiskScoreColor(metrics.riskScore) }}>
              <Target size={32} color="white" />
            </div>
            <div className="metric-title-section">
              <div className="metric-label">Risk Score</div>
            </div>
          </div>
          <div className="metric-content">
            <div className="metric-value" style={{ color: getRiskScoreColor(metrics.riskScore) }}>
              {formatRiskScore(metrics.riskScore)}
            </div>
            <div className="metric-label">Overall Risk Score</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardMetrics;
