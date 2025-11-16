import React from 'react';
import { 
  Database, 
  Shield, 
  Activity, 
  AlertTriangle, 
  Lock, 
  BarChart3, 
  TrendingUp,
  Eye,
  Clock,
  Users
} from 'lucide-react';

function RiskOverviewDashboard({ metrics, loading }) {
  if (loading || !metrics) {
    return (
      <div className="risk-overview-dashboard loading">
        <div className="metrics-grid">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="metric-card skeleton">
              <div className="metric-icon skeleton-icon"></div>
              <div className="metric-content">
                <div className="metric-value skeleton-text"></div>
                <div className="metric-label skeleton-text"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const metricCards = [
    {
      title: 'Total Data Sources',
      value: metrics.total_data_sources || 0,
      icon: <Database className="metric-icon" />,
      color: '#3B82F6',
      trend: '+12% from last scan'
    },
    {
      title: 'Total SDEs',
      value: metrics.total_sdes || 0,
      icon: <Shield className="metric-icon" />,
      color: '#10B981',
      trend: `${metrics.scanned_sdes || 0} scanned`
    },
    {
      title: 'High-Risk SDEs',
      value: metrics.high_risk_sdes || 0,
      icon: <AlertTriangle className="metric-icon" />,
      color: '#EF4444',
      trend: 'Requires attention'
    },
    {
      title: 'Sensitive Records',
      value: formatNumber(metrics.total_sensitive_records || 0),
      icon: <Lock className="metric-icon" />,
      color: '#F59E0B',
      trend: 'Protected data'
    },
    {
      title: 'Risk Score',
      value: `${Math.round(metrics.risk_score || 0)}/100`,
      icon: <BarChart3 className="metric-icon" />,
      color: getRiskScoreColor(metrics.risk_score || 0),
      trend: getRiskScoreStatus(metrics.risk_score || 0)
    },
    {
      title: 'Confidence Score',
      value: `${Math.round(metrics.confidence_score || 0)}/100`,
      icon: <TrendingUp className="metric-icon" />,
      color: '#8B5CF6',
      trend: 'Analysis accuracy'
    },
    {
      title: 'Total Scans',
      value: metrics.total_scans || 0,
      icon: <Eye className="metric-icon" />,
      color: '#06B6D4',
      trend: 'Completed scans'
    },
    {
      title: 'Last Scan',
      value: formatTime(metrics.last_scan_time),
      icon: <Clock className="metric-icon" />,
      color: '#84CC16',
      trend: 'Most recent activity'
    }
  ];

  return (
    <div className="risk-overview-dashboard">
      <div className="dashboard-header">
        <h2 className="dashboard-title">Risk Overview Dashboard</h2>
        <div className="dashboard-summary">
          <span className="summary-text">
            Overall Risk Level: <span className={`risk-level ${getRiskLevelClass(metrics.risk_score || 0)}`}>
              {getRiskLevel(metrics.risk_score || 0)}
            </span>
          </span>
        </div>
      </div>
      
      <div className="metrics-grid">
        {metricCards.map((metric, index) => (
          <div key={index} className="metric-card" style={{ '--accent-color': metric.color }}>
            <div className="metric-header">
              <div className="metric-icon-container" style={{ backgroundColor: `${metric.color}20` }}>
                {React.cloneElement(metric.icon, { style: { color: metric.color } })}
              </div>
              <div className="metric-label">{metric.title}</div>
            </div>
            <div className="metric-value">{metric.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Helper functions
function formatNumber(num) {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function formatTime(timestamp) {
  if (!timestamp) return 'Never';
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffDays > 0) return `${diffDays}d ago`;
  if (diffHours > 0) return `${diffHours}h ago`;
  return 'Recently';
}

function getRiskScoreColor(score) {
  if (score >= 75) return '#EF4444';
  if (score >= 50) return '#F59E0B';
  if (score >= 25) return '#10B981';
  return '#6B7280';
}

function getRiskScoreStatus(score) {
  if (score >= 75) return 'Critical Risk';
  if (score >= 50) return 'High Risk';
  if (score >= 25) return 'Medium Risk';
  return 'Low Risk';
}

function getRiskLevel(score) {
  if (score >= 75) return 'CRITICAL';
  if (score >= 50) return 'HIGH';
  if (score >= 25) return 'MEDIUM';
  return 'LOW';
}

function getRiskLevelClass(score) {
  if (score >= 75) return 'critical';
  if (score >= 50) return 'high';
  if (score >= 25) return 'medium';
  return 'low';
}

export default RiskOverviewDashboard;
