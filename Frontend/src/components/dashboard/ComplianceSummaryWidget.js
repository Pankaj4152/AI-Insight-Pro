import React from 'react';
import { Scale3DIcon } from 'lucide-react';

function ComplianceSummaryWidget({ complianceSummary }) {
  // Calculate overall compliance percentage for the pie chart
  const totalCompliant = complianceSummary.policies.reduce((sum, policy) => sum + policy.compliant, 0);
  const overallCompliance = complianceSummary.policies.length > 0
    ? (totalCompliant / complianceSummary.policies.length).toFixed(0) // Average compliance
    : 0;

  // CSS variable for conic-gradient
  const compliantPercentageStyle = {
    '--compliant-percentage': `${overallCompliance}%`,
  };

  return (
    <div className="dashboard-card compliance-summary-widget">
      <div className="card-header">
        <span className="card-icon"><Scale3DIcon className='lucida-icon' /></span>
        <h3 className="card-title">Compliance Summary</h3>
      </div>
      <div className="card-content">
        <div className="pie-chart-container" style={compliantPercentageStyle}>
          <div className="pie-chart-center-circle">
            {overallCompliance}%
          </div>
        </div>
        <div className="compliance-details">
          {complianceSummary.policies.map((policy, index) => (
            <div key={index} className="compliance-item">
              <span>{policy.name}:</span>
              <span>{policy.compliant}% compliant</span>
            </div>
          ))}
          <p className="violations-count">Violations Count: {complianceSummary.violations}</p>
        </div>
      </div>
    </div>
  );
}

export default ComplianceSummaryWidget;