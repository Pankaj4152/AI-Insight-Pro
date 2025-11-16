import React from 'react';
import { ClipboardList } from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function ComplianceImpactChart({ data }) {
  // Transform compliance data for chart
  const complianceData = data || [];
  const labels = complianceData.map(item => item.policy || 'Unknown Policy');
  const impactScores = complianceData.map(item => item.impact_score || 0);
  const riskLevels = complianceData.map(item => item.risk_level || 'Medium');

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: 'Impact Score',
        data: impactScores,
        backgroundColor: impactScores.map((score, index) => {
          const riskLevel = riskLevels[index];
          if (riskLevel === 'High') return 'rgba(255, 77, 77, 0.8)';
          if (riskLevel === 'Medium') return 'rgba(255, 165, 0, 0.8)';
          return 'rgba(37, 179, 101, 0.8)';
        }),
        borderColor: impactScores.map((score, index) => {
          const riskLevel = riskLevels[index];
          if (riskLevel === 'High') return 'rgba(255, 77, 77, 1)';
          if (riskLevel === 'Medium') return 'rgba(255, 165, 0, 1)';
          return 'rgba(37, 179, 101, 1)';
        }),
        borderWidth: 1,
      },
    ],
  };

  const options = {
    indexAxis: 'y', // Makes it horizontal
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false, // Hide legend since we only have one dataset
      },
      title: {
        display: true,
        text: 'Compliance Impact by Policy',
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
        callbacks: {
          afterLabel: function(context) {
            const index = context.dataIndex;
            const riskLevel = riskLevels[index];
            return `Risk Level: ${riskLevel}`;
          },
        },
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
        title: {
          display: true,
          text: 'Impact Score',
          color: 'var(--text-color)',
          font: {
            size: 12,
          },
        },
      },
      y: {
        ticks: {
          color: 'var(--text-color)',
          font: {
            size: 11,
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
        <ClipboardList className="card-icon" />
        <h3 className="card-title">Compliance Impact Analysis</h3>
      </div>
      <div className="chart-container">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}

export default ComplianceImpactChart; 