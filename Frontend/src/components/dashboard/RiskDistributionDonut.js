import React from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, TrendingUp, Database } from 'lucide-react';

function SecurityInsightsWidget({ dataSources, scanActivity, riskMetrics }) {
  // Calculate security insights
  const totalSources = dataSources?.length || 0;
  
  // Get unique data sources that have been successfully scanned
  const successfullyScannedSources = new Set();
  
  if (scanActivity?.recentScans) {
    scanActivity.recentScans.forEach(scan => {
      if (scan.status && (scan.status.toLowerCase() === 'completed' || scan.status.toLowerCase() === 'success')) {
        // Use source name or ID to identify unique sources
        const sourceIdentifier = scan.source || scan.store_name || scan.location;
        if (sourceIdentifier) {
          successfullyScannedSources.add(sourceIdentifier);
        }
      }
    });
  }
  
  const activeSources = successfullyScannedSources.size;
  const inactiveSources = Math.max(0, totalSources - activeSources);
  
  // Ensure protection percentage doesn't exceed 100%
  const securityScore = totalSources > 0 ? Math.min(100, Math.round((activeSources / totalSources) * 100)) : 0;
  
  // Determine security status
  const getSecurityStatus = () => {
    if (securityScore >= 80) return { status: 'Excellent', color: '#25B365', icon: <CheckCircle className="lucide-icon" /> };
    if (securityScore >= 60) return { status: 'Good', color: '#FFA500', icon: <TrendingUp className="lucide-icon" /> };
    return { status: 'Needs Attention', color: '#FF4D4D', icon: <AlertTriangle className="lucide-icon" /> };
  };
  
  const securityStatus = getSecurityStatus();
  
  return (
    <div className="dashboard-card security-insights-widget">
      <h3 className="card-title">Security Insights</h3>
      
      <div className="security-score-section">
        <div className="score-circle" style={{ borderColor: securityStatus.color }}>
          <span className="score-value">{securityScore}%</span>
          <span className="score-label">Security Score</span>
        </div>
        <div className="status-info">
          {securityStatus.icon}
          <span className="status-text" style={{ color: securityStatus.color }}>
            {securityStatus.status}
          </span>
        </div>
      </div>
      
      <div className="insights-grid">
        <div className="insight-item">
          <Database className="lucide-icon" />
          <div className="insight-content">
            <span className="insight-value">{totalSources}</span>
            <span className="insight-label">Total Sources</span>
          </div>
        </div>
        
        <div className="insight-item">
          <CheckCircle className="lucide-icon" />
          <div className="insight-content">
            <span className="insight-value">{activeSources}</span>
            <span className="insight-label">Active Sources</span>
          </div>
        </div>
        
        <div className="insight-item">
          <Clock className="lucide-icon" />
          <div className="insight-content">
            <span className="insight-value">{inactiveSources}</span>
            <span className="insight-label">Inactive Sources</span>
          </div>
        </div>
        
        <div className="insight-item">
          <Shield className="lucide-icon" />
          <div className="insight-content">
            <span className="insight-value">{securityScore}%</span>
            <span className="insight-label">Protected</span>
          </div>
        </div>
      </div>
      
      <div className="security-recommendations">
        {securityScore < 80 && (
          <div className="recommendation">
            <AlertTriangle className="lucide-icon" />
            <span>Consider scanning inactive data sources</span>
          </div>
        )}
        {securityScore >= 80 && (
          <div className="recommendation positive">
            <CheckCircle className="lucide-icon" />
            <span>All data sources are properly secured</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default SecurityInsightsWidget; 