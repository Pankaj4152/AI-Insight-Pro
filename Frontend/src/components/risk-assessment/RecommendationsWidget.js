import React from 'react';
import { Lightbulb } from 'lucide-react';

function RecommendationsWidget({ recommendations, onTakeAction }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="dashboard-card">
        <div className="card-header">
          <Lightbulb className="card-icon" />
          <h3 className="card-title">AI Recommendations</h3>
        </div>
        <div className="no-data-message">No recommendations available.</div>
      </div>
    );
  }

  return (
    <div className="dashboard-card recommendations-widget">
      <div className="card-header">
        <Lightbulb className="card-icon" />
        <h3 className="card-title">AI Recommendations</h3>
      </div>
      <div className="card-content">
        {recommendations.length > 0 ? (
          <ul className="recommendations-list">
            {recommendations.map(rec => (
              <li key={rec.id} className="recommendation-item">
                <p className="recommendation-message">{rec.message}</p>
                <span className={`recommendation-severity ${rec.severity}`}>{rec.severity} Severity</span>
                <div className="recommendation-actions">
                  <button className="action-cta-button" onClick={() => console.log(`Assigning owner for recommendation: ${rec.id}`)}>Assign Owner</button>
                  <button className="action-cta-button" onClick={() => onTakeAction(rec.id)}>Take Action</button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-recommendations">No new recommendations at this time.</p>
        )}
      </div>
    </div>
  );
}

export default RecommendationsWidget;
