import React from 'react';
import { Link } from 'lucide-react';

function LinkedComplianceImpactWidget({ complianceImpact, onViewDetail }) {
  if (!complianceImpact || complianceImpact.length === 0) {
    return (
      <div className="dashboard-card">
        <div className="card-header">
          <Link className="card-icon" />
          <h3 className="card-title">Compliance Impact</h3>
        </div>
        <div className="no-data-message">No compliance impact data available.</div>
      </div>
    );
  }

  return (
    <div className="dashboard-card linked-compliance-impact-widget">
      <div className="card-header">
        <Link className="card-icon" />
        <h3 className="card-title">Compliance Impact</h3>
      </div>
      <div className="card-content">
        {complianceImpact.length > 0 ? (
          <ul className="compliance-impact-list">
            {complianceImpact.map(impact => (
              <li key={impact.policy} className="compliance-impact-item">
                <span className="compliance-policy">{impact.policy}:</span>
                <span className="risks-blocking">{impact.risksBlocking} risks blocking</span>
                <button className="view-detail-button" onClick={() => console.log(`Viewing detailed compliance impact for policy: ${impact.policy}`)}>
                  {impact.details}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-impact">No direct compliance impact identified.</p>
        )}
      </div>
    </div>
  );
}

export default LinkedComplianceImpactWidget;
