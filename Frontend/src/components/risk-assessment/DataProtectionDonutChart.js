import React from 'react';
import { Shield } from 'lucide-react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

function DataProtectionDonutChart({ data }) {
  const chartData = {
    labels: ['Masked', 'Encrypted', 'Not Protected'],
    datasets: [
      {
        data: [data.masked || 0, data.encrypted || 0, data.notProtected || 0],
        backgroundColor: [
          'rgba(37, 179, 101, 0.8)',   // Green for masked
          'rgba(22, 227, 175, 0.8)',    // Teal for encrypted
          'rgba(255, 77, 77, 0.8)',     // Red for not protected
        ],
        borderColor: [
          'rgba(37, 179, 101, 1)',
          'rgba(22, 227, 175, 1)',
          'rgba(255, 77, 77, 1)',
        ],
        borderWidth: 2,
        hoverOffset: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: 'var(--text-color)',
          font: {
            size: 12,
          },
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: { size: 12 },
        bodyFont: { size: 12 },
        padding: 10,
        callbacks: {
          label: function(context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((context.parsed / total) * 100).toFixed(1);
            return `${context.label}: ${context.parsed} (${percentage}%)`;
          },
        },
      },
    },
    cutout: '60%', // Makes it a donut chart
  };

  const total = (data.masked || 0) + (data.encrypted || 0) + (data.notProtected || 0);
  const protectedPercentage = total > 0 ? (((data.masked || 0) + (data.encrypted || 0)) / total * 100).toFixed(1) : 0;

  return (
    <div className="dashboard-card data-protection-donut-widget">
      <div className="card-header">
        <Shield className="card-icon" />
        <h3 className="card-title">Data Protection Status</h3>
      </div>
      <div className="card-content">
        <div style={{ height: '300px', position: 'relative' }}>
          <Doughnut data={chartData} options={options} />
          {total > 0 && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--text-color)' }}>
                {protectedPercentage}%
              </div>
              <div style={{ fontSize: '12px', color: 'var(--description-color)' }}>
                Protected
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DataProtectionDonutChart; 