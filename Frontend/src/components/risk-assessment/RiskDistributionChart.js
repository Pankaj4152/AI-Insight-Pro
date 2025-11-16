import React from 'react';
import { BarChart3 } from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function RiskDistributionChart({ data }) {
  const chartData = {
    labels: ['Low Risk', 'Medium Risk', 'High Risk'],
    datasets: [
      {
        label: 'SDEs',
        data: [data.sdes?.low || 0, data.sdes?.medium || 0, data.sdes?.high || 0],
        backgroundColor: 'rgba(37, 179, 101, 0.8)',
        borderColor: 'rgba(37, 179, 101, 1)',
        borderWidth: 1,
      },
      {
        label: 'Findings',
        data: [data.findings?.low || 0, data.findings?.medium || 0, data.findings?.high || 0],
        backgroundColor: 'rgba(255, 165, 0, 0.8)',
        borderColor: 'rgba(255, 165, 0, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'var(--text-color)',
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: true,
        text: 'Risk Distribution by Category',
        color: 'var(--text-color)',
        font: {
          size: 14,
          weight: 'bold',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: { size: 12 },
        bodyFont: { size: 12 },
        padding: 10,
      },
    },
    scales: {
      x: {
        ticks: {
          color: 'var(--text-color)',
          font: {
            size: 12,
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      y: {
        ticks: {
          color: 'var(--text-color)',
          font: {
            size: 12,
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
  };

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <BarChart3 className="card-icon" />
        <h3 className="card-title">Risk Distribution Analysis</h3>
      </div>
      <div className="chart-container">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}

export default RiskDistributionChart; 