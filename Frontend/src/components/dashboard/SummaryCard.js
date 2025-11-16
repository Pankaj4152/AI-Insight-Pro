import React from 'react';

function SummaryCard({ title, value, icon }) {
  return (
    <div className="dashboard-card summary-card">
      <div className="card-header">
        <span className="card-icon">{icon}</span>
        <h3 className="card-title">{title}</h3>
      </div>
      <div className="card-value">{value}</div>
    </div>
  );
}

export default SummaryCard;