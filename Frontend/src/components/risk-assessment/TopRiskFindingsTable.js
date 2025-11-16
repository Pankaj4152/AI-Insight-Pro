import React from 'react';
import { ClipboardList } from 'lucide-react';

function TopRiskFindingsTable({ findings }) {
  console.log('TopRiskFindingsTable received findings:', findings);
  
  if (!findings || findings.length === 0) {
    return (
      <div className="dashboard-card">
        <div className="card-header">
          <ClipboardList className="card-icon" />
          <h3 className="card-title">Top Risk Findings</h3>
        </div>
        <div className="no-data-message">No risk findings available.</div>
      </div>
    );
  }

  // Removed action handlers since we're removing the Actions column

  return (
    <div className="top-risk-findings-table">
      <div className="card-header">
        <ClipboardList className="card-icon" />
        <h3 className="card-title">Top Risk Findings</h3>
      </div>
      <table>
        <thead>
          <tr>
            <th>Finding ID</th>
            <th>Sensitivity</th>
            <th>Location</th>
            <th>Finding Type</th>
            <th>Data Value</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((finding, index) => {
            console.log('Rendering finding:', finding);
            return (
              <tr key={finding.finding_id || finding.id || index}>
                <td>{finding.finding_id || finding.id || `F-${index + 1}`}</td>
                <td>{finding.sensitivity || 'Unknown'}</td>
                <td>{finding.location || finding.dataset || 'Unknown'}</td>
                <td>{finding.finding_type || finding.patternType || 'Unknown'}</td>
                <td 
                 className="data-value-cell" 
                 title={finding.data_value || finding.detectedValue || 'N/A'}
               >
                 {finding.data_value || finding.detectedValue || 'N/A'}
               </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default TopRiskFindingsTable;
