import React from 'react';
import { Target } from 'lucide-react';
import { Radar } from 'react-chartjs-2';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

function SensitivityLevelChart({ data }) {
  // Transform sensitivity data for radar chart
  const sensitivityData = data || {};
  const categories = Object.keys(sensitivityData);
  const values = Object.values(sensitivityData);

  const chartData = {
    labels: categories.length > 0 ? categories : ['No Data'],
    datasets: [
      {
        label: 'Sensitivity Level',
        data: values.length > 0 ? values : [0],
        backgroundColor: 'rgba(22, 227, 175, 0.2)',
        borderColor: 'rgba(22, 227, 175, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(22, 227, 175, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(22, 227, 175, 1)',
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
        text: 'Sensitivity Levels by Category',
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
      r: {
        angleLines: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
        pointLabels: {
          color: 'var(--text-color)',
          font: {
            size: 11,
          },
        },
        ticks: {
          color: 'var(--text-color)',
          font: {
            size: 10,
          },
          backdropColor: 'transparent',
        },
      },
    },
  };

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <Target className="card-icon" />
        <h3 className="card-title">Sensitivity Level Analysis</h3>
      </div>
      <div className="chart-container">
        <Radar data={chartData} options={options} />
      </div>
    </div>
  );
}

export default SensitivityLevelChart; 