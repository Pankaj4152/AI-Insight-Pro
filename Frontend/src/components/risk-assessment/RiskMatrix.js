import React, { useRef, useEffect, useState, useCallback } from 'react'; // Import useCallback
import { BowArrow } from 'lucide-react';

function RiskMatrix({ riskMatrixData }) {
  const canvasRef = useRef(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: '', id: null });
  const [clickMessage, setClickMessage] = useState(null); // New state for click message

  // Define handleClick using useCallback to prevent it from changing on every render
  const handleClick = useCallback((e) => {
    if (tooltip.visible) {
      const message = `Details for ${tooltip.content}. (ID: ${tooltip.id})`;
      setClickMessage(message); // Set the message to display
      // In a real application, this would trigger a modal, navigate to a detail page, etc.
      setTimeout(() => setClickMessage(null), 3000); // Clear message after 3 seconds
    }
  }, [tooltip.visible, tooltip.content, tooltip.id]); // Dependencies for useCallback

  const drawMatrix = (ctx, canvas, data) => {
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    const cellWidth = (width - padding) / 3;
    const cellHeight = (height - padding) / 3;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Test rectangle to ensure canvas is working
    ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
    ctx.fillRect(0, 0, width, height);

    // Draw background for better visibility
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.fillRect(padding, padding, width - 2 * padding, height - 2 * padding);

    // Draw grid lines with much darker and thicker lines
    ctx.strokeStyle = '#FFFFFF'; // White lines for better visibility
    ctx.lineWidth = 3; // Thicker lines

    // Draw outer border
    ctx.strokeRect(padding, padding, width - 2 * padding, height - 2 * padding);

    // Vertical lines (creates 3 columns)
    for (let i = 1; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(padding + i * cellWidth, padding);
      ctx.lineTo(padding + i * cellWidth, height - padding);
      ctx.stroke();
    }

    // Horizontal lines (creates 3 rows)
    for (let i = 1; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(padding, padding + i * cellHeight);
      ctx.lineTo(width - padding, padding + i * cellHeight);
      ctx.stroke();
    }

    // Draw quadrant labels for debugging
    ctx.fillStyle = '#000000'; // Black text
    ctx.font = 'bold 12px var(--font-inter)'; // Bold font for better visibility
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Label each quadrant (1-9)
    let quadrantNumber = 1;
    for (let row = 0; row < 3; row++) {
      for (let col = 0; col < 3; col++) {
        const x = padding + col * cellWidth + cellWidth / 2;
        const y = padding + row * cellHeight + cellHeight / 2;
        ctx.fillText(`Q${quadrantNumber}`, x, y);
        quadrantNumber++;
      }
    }

    const likelihoodLabels = ['Low', 'Medium', 'High'];
    const impactLabels = ['High', 'Medium', 'Low']; // Inverted for Y-axis (High at top)

    // X-axis (Likelihood) labels
    for (let i = 0; i < 3; i++) {
      ctx.fillText(likelihoodLabels[i], padding + i * cellWidth + cellWidth / 2, height - padding / 2);
    }
    ctx.fillText('Likelihood', width / 2, height - padding / 4);

    // Y-axis (Impact) labels
    ctx.save();
    ctx.translate(padding / 2, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Impact', 0, 0);
    ctx.restore();

    for (let i = 0; i < 3; i++) {
      ctx.fillText(impactLabels[i], padding / 2, padding + i * cellHeight + cellHeight / 2);
    }

    // Draw data points with hover effect
    let drawnCount = 0;
    data.forEach((sde, index) => {
      let xPos, yPos;

      // Normalize likelihood value and map to position
      const likelihood = sde.likelihood ? sde.likelihood.toString() : '';
      switch (likelihood) {
        case 'Low': xPos = padding + cellWidth / 2; break;
        case 'Medium': xPos = padding + cellWidth + cellWidth / 2; break;
        case 'High': xPos = padding + 2 * cellWidth + cellWidth / 2; break;
        default:
          console.warn(`Unknown likelihood value: ${likelihood} for SDE:`, sde);
          xPos = 0;
      }

      // Normalize impact value and map to position
      const impact = sde.impact ? sde.impact.toString() : '';
      switch (impact) {
        case 'High': yPos = padding + cellHeight / 2; break;
        case 'Medium': yPos = padding + cellHeight + cellHeight / 2; break;
        case 'Low': yPos = padding + 2 * cellHeight + cellHeight / 2; break;
        default:
          console.warn(`Unknown impact value: ${impact} for SDE:`, sde);
          yPos = 0;
      }

      // Only draw if we have valid positions
      if (xPos > 0 && yPos > 0) {
        // Check for overlapping circles and adjust position slightly
        const baseRadius = 8;
        let adjustedX = xPos;
        let adjustedY = yPos;
        
        // Check if this position already has a circle (simple overlap detection)
        const existingCircles = data.slice(0, index).filter(item => item.x && item.y);
        for (const existing of existingCircles) {
          const distance = Math.sqrt((adjustedX - existing.x) ** 2 + (adjustedY - existing.y) ** 2);
          if (distance < 20) { // If circles are too close
            // Move this circle slightly
            adjustedX += (Math.random() - 0.5) * 10;
            adjustedY += (Math.random() - 0.5) * 10;
          }
        }

        ctx.beginPath();
        const radius = baseRadius;
        ctx.arc(adjustedX, adjustedY, radius, 0, Math.PI * 2);
        ctx.fillStyle = sde.color || '#800080'; // Default to purple if no color
        ctx.fill();
        ctx.strokeStyle = '#FFFFFF'; // White outline for better visibility
        ctx.lineWidth = 2;
        ctx.stroke();

        // Add label inside circle if space allows
        ctx.fillStyle = '#FFFFFF'; // White text for contrast
        ctx.font = 'bold 8px var(--font-inter)'; // Smaller font
        ctx.textAlign = 'center';
        ctx.fillText(sde.name.slice(0, 2), adjustedX, adjustedY + 1); // Even shorter name

        // Store position and details
        sde.x = adjustedX;
        sde.y = adjustedY;
        sde.radius = radius;
        sde.id = sde.id || Math.random().toString(36).substr(2, 9); // Unique ID if not provided
        drawnCount++;
      }
    });
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Set canvas dimensions for high-DPI displays
    const dpi = window.devicePixelRatio || 1;
    const styleWidth = getComputedStyle(canvas).getPropertyValue('width').slice(0, -2);
    const styleHeight = getComputedStyle(canvas).getPropertyValue('height').slice(0, -2);
    
    canvas.width = styleWidth * dpi;
    canvas.height = styleHeight * dpi;
    
    ctx.scale(dpi, dpi);

    drawMatrix(ctx, canvas, riskMatrixData);

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width) / dpi;
      const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height) / dpi;

      let hoveredSDE = null;
      for (const sde of riskMatrixData) {
        const distance = Math.sqrt((mouseX - sde.x) ** 2 + (mouseY - sde.y) ** 2);
        if (distance < sde.radius) {
          hoveredSDE = sde;
          break;
        }
      }

      if (hoveredSDE) {
        // Calculate tooltip position to ensure it's always visible
        const tooltipWidth = 200; // Approximate tooltip width
        const tooltipHeight = 60; // Approximate tooltip height
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let tooltipX = e.clientX + 10;
        let tooltipY = e.clientY + 10;
        
        // Adjust X position if tooltip would go off-screen
        if (tooltipX + tooltipWidth > viewportWidth) {
          tooltipX = e.clientX - tooltipWidth - 10;
        }
        
        // Adjust Y position if tooltip would go off-screen
        if (tooltipY + tooltipHeight > viewportHeight) {
          tooltipY = e.clientY - tooltipHeight - 10;
        }
        
        // Ensure tooltip doesn't go above or left of viewport
        tooltipX = Math.max(10, tooltipX);
        tooltipY = Math.max(10, tooltipY);

        setTooltip({
          visible: true,
          x: tooltipX,
          y: tooltipY,
          content: `${hoveredSDE.name}: ${hoveredSDE.details}`,
          id: hoveredSDE.id
        });
      } else {
        setTooltip(prev => ({ ...prev, visible: false }));
      }
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick); // Add click listener here

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('click', handleClick); // Clean up click listener
    };
  }, [riskMatrixData, tooltip.visible, handleClick]); // handleClick is now a stable dependency

  return (
    <div className="dashboard-card risk-matrix-widget">
      <div className="card-header">
        <span className="card-icon"><BowArrow className='lucide-icon' /></span>
        <h3 className="card-title">Interactive Risk Matrix</h3>
      </div>
      <div className="card-content">
        <canvas ref={canvasRef} className="risk-matrix-canvas"></canvas>
        {tooltip.visible && (
          <div
            className="risk-matrix-tooltip visible"
            style={{ 
              left: tooltip.x, 
              top: tooltip.y,
              maxWidth: '200px',
              zIndex: 1000
            }}
            onClick={handleClick}
          >
            {tooltip.content} <span style={{ color: '#800080' }}>[Click for Details]</span>
          </div>
        )}
        {clickMessage && (
          <div className="risk-matrix-click-message">
            {clickMessage}
          </div>
        )}
      </div>
    </div>
  );
}

export default RiskMatrix;
