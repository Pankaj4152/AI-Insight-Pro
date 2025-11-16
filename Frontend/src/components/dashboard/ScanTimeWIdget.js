import React from 'react';
import { CalendarCheckIcon, CalendarArrowUpIcon } from 'lucide-react'; // Icons for current/next scan

function ScanTimelineWidget({ lastScanTime, nextScheduledScan }) {
  return (
    <div className="dashboard-card scan-timeline-widget">
      <div className="card-header">
        <span className="card-icon">⏳</span> {/* Generic icon for timeline */}
        <h3 className="card-title">Scan Timeline</h3>
      </div>
      <div className="card-content scan-timeline-content">
        <div className="timeline-info current-scan">
          <CalendarCheckIcon className="timeline-icon" />
          <div className="timeline-text">
            <span className="timeline-label">Last Scan:</span>
            <span className="timeline-date">{lastScanTime}</span>
          </div>
        </div>

        <div className="wavy-road-container">
          <svg className="wavy-road-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
            {/* Wavy path */}
            <path
              d="M0,10 C20,0 30,20 50,10 C70,0 80,20 100,10"
              fill="none"
              stroke="url(#timelineGradient)"
              strokeWidth="3"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
            {/* Gradient definition */}
            <defs>
              <linearGradient id="timelineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--primary-color)" />
                <stop offset="100%" stopColor="var(--secondary-color)" />
              </linearGradient>
            </defs>
            {/* Current scan marker (top) */}
            <circle cx="0" cy="10" r="4" fill="var(--primary-color)" />
            {/* Next scan marker (bottom) */}
            <circle cx="100" cy="10" r="4" fill="var(--secondary-color)" />
          </svg>
        </div>

        <div className="timeline-info next-scan">
          <CalendarArrowUpIcon className="timeline-icon" />
          <div className="timeline-text">
            <span className="timeline-label">Next Scan:</span>
            <span className="timeline-date">{nextScheduledScan}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ScanTimelineWidget;
