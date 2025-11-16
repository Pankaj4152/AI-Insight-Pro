import React from 'react';
import { Lock, Unlock, Eye, EyeOff, Shield, AlertTriangle, CheckCircle } from 'lucide-react';

function DataProtectionWidget({ scanActivity, dataSources }) {
  // Calculate protection metrics
  const totalSources = dataSources?.length || 0;
  const scannedSources = scanActivity?.recentScans?.filter(scan => 
    scan.status && (scan.status.toLowerCase() === 'completed' || scan.status.toLowerCase() === 'success')
  ).length || 0;
  
  const protectedSources = scannedSources; // All scanned sources are considered protected
  const unprotectedSources = totalSources - protectedSources;
  
  const protectionRate = totalSources > 0 ? Math.round((protectedSources / totalSources) * 100) : 0;
  
  // Determine protection status
  const getProtectionStatus = () => {
    if (protectionRate >= 90) return { status: 'Fully Protected', color: '#25B365', icon: <CheckCircle className="lucide-icon" /> };
    if (protectionRate >= 70) return { status: 'Well Protected', color: '#FFA500', icon: <Shield className="lucide-icon" /> };
    return { status: 'Needs Protection', color: '#FF4D4D', icon: <AlertTriangle className="lucide-icon" /> };
  };
  
  const protectionStatus = getProtectionStatus();

  return (
    <div className="dashboard-card data-protection-widget">
      <h3 className="card-title">Data Protection Status</h3>
      
      <div className="protection-overview">
        <div className="protection-circle" style={{ borderColor: protectionStatus.color }}>
          <span className="protection-value">{protectionRate}%</span>
          <span className="protection-label">Protected</span>
        </div>
        <div className="protection-status">
          {protectionStatus.icon}
          <span className="status-text" style={{ color: protectionStatus.color }}>
            {protectionStatus.status}
          </span>
        </div>
      </div>
      
      <div className="protection-breakdown">
        <div className="protection-item protected">
          <Lock className="lucide-icon" />
          <div className="protection-content">
            <span className="protection-count">{protectedSources}</span>
            <span className="protection-label">Protected Sources</span>
          </div>
        </div>
        
        <div className="protection-item unprotected">
          <Unlock className="lucide-icon" />
          <div className="protection-content">
            <span className="protection-count">{unprotectedSources}</span>
            <span className="protection-label">Unprotected Sources</span>
          </div>
        </div>
        
        <div className="protection-item scanned">
          <Eye className="lucide-icon" />
          <div className="protection-content">
            <span className="protection-count">{scannedSources}</span>
            <span className="protection-label">Scanned Sources</span>
          </div>
        </div>
        
        <div className="protection-item total">
          <Shield className="lucide-icon" />
          <div className="protection-content">
            <span className="protection-count">{totalSources}</span>
            <span className="protection-label">Total Sources</span>
          </div>
        </div>
      </div>
      
      <div className="protection-actions">
        {protectionRate < 100 && (
          <div className="action-item">
            <AlertTriangle className="lucide-icon" />
            <span>Enable protection for remaining sources</span>
          </div>
        )}
        {protectionRate === 100 && (
          <div className="action-item positive">
            <CheckCircle className="lucide-icon" />
            <span>All data sources are protected</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default DataProtectionWidget; 