import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  RadialLinearScale
} from 'chart.js';
import { Bar, Doughnut, Pie } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  RadialLinearScale
);

const ChartTest = () => {
  // Simple test data
  const testBarData = {
    labels: ['Low', 'Medium', 'High', 'Critical'],
    datasets: [{
      label: 'Risk Count',
      data: [12, 19, 8, 5],
      backgroundColor: ['#10B981', '#F59E0B', '#EF4444', '#DC2626'],
      borderColor: ['#059669', '#D97706', '#DC2626', '#B91C1C'],
      borderWidth: 2
    }]
  };

  const testPieData = {
    labels: ['PII', 'Financial', 'Health', 'Other'],
    datasets: [{
      data: [25, 30, 20, 25],
      backgroundColor: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B'],
      borderWidth: 2
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: 'Test Chart'
      }
    }
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      }
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Chart.js Test Components</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
        <div style={{ height: '300px', border: '1px solid #ccc', padding: '10px' }}>
          <h3>Bar Chart Test</h3>
          <div style={{ height: '250px' }}>
            <Bar data={testBarData} options={chartOptions} />
          </div>
        </div>

        <div style={{ height: '300px', border: '1px solid #ccc', padding: '10px' }}>
          <h3>Pie Chart Test</h3>
          <div style={{ height: '250px' }}>
            <Pie data={testPieData} options={pieOptions} />
          </div>
        </div>

        <div style={{ height: '300px', border: '1px solid #ccc', padding: '10px' }}>
          <h3>Doughnut Chart Test</h3>
          <div style={{ height: '250px' }}>
            <Doughnut data={testPieData} options={pieOptions} />
          </div>
        </div>

        <div style={{ height: '300px', border: '1px solid #ccc', padding: '10px' }}>
          <h3>Debug Info</h3>
          <div>
            <p>Chart.js Version: {ChartJS.version}</p>
            <p>Test Data Valid: {testBarData ? 'Yes' : 'No'}</p>
            <p>Components Registered: {ChartJS.registry ? 'Yes' : 'No'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartTest;
