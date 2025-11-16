import React, { useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from '../../apiConfig';

function RiskSummaryWidget({ riskSummary, onViewFullRiskAssessment }) {
  const [topFindings, setTopFindings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTopFindings = async () => {
      try {
        const clientId = localStorage.getItem('client_id');
        const response = await fetch(`${API_BASE_URL}/risk/top-findings/${clientId}?limit=3`);
        const data = await response.json();
        setTopFindings(data.findings || []);
      } catch (error) {
        console.error('Error fetching top findings:', error);
        setTopFindings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTopFindings();
  }, []);

  return (
    <div className="dashboard-card risk-summary-widget">
      <div className="card-header">
        <span className="card-icon"><AlertTriangle className="lucide-icon" /></span>
        <h3 className="card-title">Risk Summary</h3>
      </div>
      <div className="card-content">
        <h4>Activity</h4>
        <div className="scan-activity-summary">
          <div className="scan-stat">
            <span className="stat-label">Total Scans:</span>
            <span className="stat-value">{riskSummary.totalScans || 0}</span>
          </div>
          <div className="scan-stat">
            <span className="stat-label">Last Scan:</span>
            <span className="stat-value">{riskSummary.lastScan || 'Never'}</span>
          </div>
          <div className="scan-stat">
            <span className="stat-label">Active Sources:</span>
            <span className="stat-value">{riskSummary.activeSources || 0}</span>
          </div>
        </div>

        <h4>Findings</h4>
        {loading ? (
          <div className="loading-message">Loading findings...</div>
        ) : topFindings.length > 0 ? (
          <ul className="top-risks-list">
            {topFindings.map((finding, index) => (
              <li key={index}>
                <div className="finding-info">
                  <span className="finding-type">{finding.finding_type || 'Unknown'}</span>
                  <span className="finding-data-value">{finding.data_value || 'N/A'}</span>
                  <span className="finding-location">{finding.location || 'Unknown'}</span>
                </div>
                <span className={`risk-score ${finding.sensitivity || 'Medium'}`}>
                  {finding.sensitivity || 'Medium'}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="no-findings">No high-risk findings detected</div>
        )}

        <button className="view-full-risk-button" onClick={onViewFullRiskAssessment}>
          View Assessment
        </button>
      </div>
    </div>
  );
}

export default RiskSummaryWidget;