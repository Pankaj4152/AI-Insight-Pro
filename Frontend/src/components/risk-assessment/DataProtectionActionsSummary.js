import React, { useEffect, useRef } from 'react';
import { Shield } from 'lucide-react';

function DataProtectionActionsSummary({ actions }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Set canvas dimensions for high-DPI displays
    const dpi = window.devicePixelRatio || 1;
    const styleWidth = getComputedStyle(canvas).getPropertyValue('width');
    const styleHeight = getComputedStyle(canvas).getPropertyValue('height');
    canvas.width = parseFloat(styleWidth) * dpi;
    canvas.height = parseFloat(styleHeight) * dpi;
    ctx.scale(dpi, dpi);

    const totalActions = actions.masked + actions.encrypted + actions.notProtected;
    const centerX = canvas.width / (2 * dpi);
    const centerY = canvas.height / (2 * dpi);
    const radius = Math.min(centerX, centerY) * 0.8; // Adjust radius to fit

    // Colors for the pie chart segments
    const colors = {
      masked: 'var(--navbar-logo-color-start)', // Greenish
      encrypted: 'var(--button-border-gradient-end)', // Blueish
      notProtected: '#ff4d4d', // Red
    };

    let startAngle = 0;
    for (const actionType in actions) {
      if (actions.hasOwnProperty(actionType) && totalActions > 0) {
        const sliceAngle = (actions[actionType] / totalActions) * 2 * Math.PI;
        ctx.fillStyle = colors[actionType];
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
        ctx.closePath();
        ctx.fill();
        startAngle += sliceAngle;
      }
    }

    // Draw the center circle to make it a donut chart
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--card-background').trim();
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.6, 0, Math.PI * 2); // 60% of outer radius
    ctx.fill();

    // Add percentage labels inside the donut segments (optional, can be complex to place perfectly)
    // For simplicity, we'll just show total in the center HTML div.

  }, [actions]);

  if (!actions) {
    return (
      <div className="dashboard-card">
        <div className="card-header">
          <Shield className="card-icon" />
          <h3 className="card-title">Data Protection Actions</h3>
        </div>
        <div className="no-data-message">No data protection actions available.</div>
      </div>
    );
  }

  return (
    <div className="dashboard-card data-protection-actions-summary-widget">
      <div className="card-header">
        <Shield className="card-icon" />
        <h3 className="card-title">Data Protection Actions</h3>
      </div>
      <div className="card-content">
        <div className="action-chart-container">
          <canvas ref={canvasRef} className="action-chart-canvas"></canvas>
          <div className="action-chart-center-circle">
            {actions.masked + actions.encrypted + actions.notProtected} Total
          </div>
        </div>
        <ul className="action-legend">
          <li className="action-legend-item">
            <span className="legend-color-box" style={{ backgroundColor: 'var(--navbar-logo-color-start)' }}></span>
            Masked: {actions.masked}
          </li>
          <li className="action-legend-item">
            <span className="legend-color-box" style={{ backgroundColor: 'var(--button-border-gradient-end)' }}></span>
            Encrypted: {actions.encrypted}
          </li>
          <li className="action-legend-item">
            <span className="legend-color-box" style={{ backgroundColor: '#ff4d4d' }}></span>
            Not Protected: {actions.notProtected}
          </li>
        </ul>
      </div>
    </div>
  );
}

export default DataProtectionActionsSummary;
