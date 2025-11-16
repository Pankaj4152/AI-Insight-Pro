import React from 'react';
import { BarChart3 } from 'lucide-react';

function ScanActivityWidget({ scanActivity }) {

  

  

  
  // Check if scanActivity exists and has required properties
  if (!scanActivity) {
    console.log('❌ ERROR: scanActivity is null or undefined');
    return (
      <div className="dashboard-card scan-activity-widget">
        <div className="card-header">
          <span className="card-icon">📈</span>
          <h3 className="card-title">Scan Activity (Last 7 Days)</h3>
        </div>
        <div className="card-content">
          <p>No scan activity data available</p>
        </div>
      </div>
    );
  }
  
  if (!scanActivity.dailyScans || !scanActivity.recentScans) {
    console.log('❌ ERROR: Missing dailyScans or recentScans in scanActivity');
    return (
      <div className="dashboard-card scan-activity-widget">
        <div className="card-header">
          <span className="card-icon">📈</span>
          <h3 className="card-title">Scan Activity (Last 7 Days)</h3>
        </div>
        <div className="card-content">
          <p>Incomplete scan activity data</p>
          <p>dailyScans: {scanActivity.dailyScans ? 'Present' : 'Missing'}</p>
          <p>recentScans: {scanActivity.recentScans ? 'Present' : 'Missing'}</p>
        </div>
      </div>
    );
  }

  // Find the maximum scan count for scaling the bars
  const maxScans = Math.max(...scanActivity.dailyScans.map(data => data.scans));
  
  // If all scans are 0, set a minimum height for visibility
  const hasAnyScans = maxScans > 0;

  return (
    <div className="dashboard-card scan-activity-widget">
      <div className="card-header">
        <span className="card-icon"><BarChart3 className="lucide-icon" /></span>
        <h3 className="card-title">Scan Activity</h3>
      </div>
      <div className="card-content">
        <div className="scan-activity-summary">
          <div className="scan-stat">
            <span className="stat-label">Total Scans</span>
            <span className="stat-value">{scanActivity.totalScans || scanActivity.recentScans.length}</span>
          </div>
          <div className="scan-stat">
            <span className="stat-label">Active Sources</span>
            <span className="stat-value">{scanActivity.recentScans.filter(scan => 
              scan.status && (scan.status.toLowerCase() === 'completed' || scan.status.toLowerCase() === 'success')
            ).length}</span>
          </div>
        </div>
        <div className="scan-activity-chart">
          <div className="chart-header">
            <span className="chart-title" style={{ color: "black" }}>Daily Activity</span>
            <span className="chart-subtitle" style={{color:"#818589"}}>Last 7 days</span>
          </div>
          <div className="chart-bars">
            {scanActivity.dailyScans.map((data, index) => {
              return (
                <div
                  key={index}
                  className="bar-chart-bar"
                  style={{ 
                    height: hasAnyScans ? `${(data.scans / maxScans) * 100}%` : '10px',
                    opacity: data.scans === 0 ? 0.3 : 1
                  }}
                  title={`${data.day}: ${data.scans} scans`}
                >
                  <span>{data.scans}</span>
                </div>
              );
            })}
          </div>
        </div>

        <h4>Recent</h4>
        {scanActivity.recentScans.length > 0 ? (
          <table className="recent-scans-table">
                         <thead>
               <tr>
                 <th>Source</th>
                 <th>Time</th>
                 <th>Status</th>
                 <th>Type</th>
               </tr>
             </thead>
            <tbody>
                          {scanActivity.recentScans.map(scan => {
              return (
                  <tr key={scan.id || scan.scan_id}>
                    <td>{scan.source}</td>
                    <td>{scan.time}</td>
                    <td>
                      <span className={`status-badge ${scan.status ? scan.status.toLowerCase() : 'unknown'}`}>
                        {scan.status || 'Unknown'}
                      </span>
                    </td>
                                         <td>{scan.type}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="no-recent-scans">
            <p>No recent scans found</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ScanActivityWidget;