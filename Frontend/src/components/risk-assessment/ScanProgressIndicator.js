import React from 'react';

function ScanProgressIndicator({ progress, eta, status }) {
  // Determine status styling
  let statusClass = '';
  let statusText = '';
  switch (status) {
    case 'Queued':
      statusClass = 'status-queued';
      statusText = 'Queued';
      break;
    case 'Running':
      statusClass = 'status-running';
      statusText = 'Running';
      break;
    case 'Completed':
      statusClass = 'status-completed';
      statusText = 'Completed';
      break;
    case 'Failed':
      statusClass = 'status-failed';
      statusText = 'Failed';
      break;
    default:
      statusClass = 'status-idle';
      statusText = 'Idle';
  }

  return (
    <div className="dashboard-card scan-progress-indicator">
      <div className="card-header">
        <span className="card-icon">⏳</span>
        <h3 className="card-title">Current Scan Progress</h3>
      </div>
      <div className="card-content">
        <div className="progress-bar-container">
          <div
            className="progress-bar-fill"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="progress-details">
          <span className="progress-percentage">{progress}%</span>
          <span className="progress-eta">ETA: {eta}</span>
        </div>
        <div className={`scan-status-badge ${statusClass}`}>
          {statusText}
        </div>
        {status === 'Running' && (
          <div className="scan-actions">
            <button className="scan-action-button pause-button">Pause Scan</button>
            <button className="scan-action-button cancel-button">Cancel Scan</button>
          </div>
        )}
        {status === 'Completed' && (
          <p className="scan-message success">Scan completed successfully!</p>
        )}
        {status === 'Failed' && (
          <p className="scan-message error">Scan failed. Please review logs.</p>
        )}
      </div>
    </div>
  );
}

export default ScanProgressIndicator;
