import React from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

function DataSourcePieChart({ dataSources }) {
  if (!dataSources || dataSources.length === 0) {
    return (
      <div className="dashboard-card data-source-pie-widget">
        <h3 className="card-title">Data Source Distribution</h3>
        <div className="error-message">
          <p>❌ No data sources found</p>
          <p className="error-details">Unable to load data source information from API</p>
        </div>
      </div>
    );
  }

  // Handle new data structure from comprehensive endpoint
  let sourceTypes = {};
  if (dataSources[0] && dataSources[0].type) {
    // New format: [{type: "S3", count: 5}, {type: "RDS", count: 3}]
    dataSources.forEach(source => {
      sourceTypes[source.type] = source.count;
    });
  } else {
    // Old format: [{store_type: "S3"}, {store_type: "RDS"}]
    dataSources.forEach(source => {
      const type = source.store_type || 'Unknown';
      sourceTypes[type] = (sourceTypes[type] || 0) + 1;
    });
  }

  const chartData = {
    labels: Object.keys(sourceTypes),
    datasets: [{
      data: Object.values(sourceTypes),
      backgroundColor: [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF',
        '#FF9F40',
        '#FF6384',
        '#C9CBCF'
      ],
      borderColor: [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF',
        '#FF9F40',
        '#FF6384',
        '#C9CBCF'
      ],
      borderWidth: 2,
    }],
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
        titleFont: { size: 14 },
        bodyFont: { size: 12 },
        padding: 10,
        callbacks: {
          label: function(context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((context.parsed / total) * 100).toFixed(1);
            return `${context.label}: ${context.parsed} (${percentage}%)`;
          }
        }
      },
    },
  };

  return (
    <div className="dashboard-card data-source-pie-widget">
      <h3 className="card-title">Data Source Distribution</h3>
      <div className="chart-container">
        <Pie data={chartData} options={options} />
      </div>
      <div className="chart-summary">
        <p>Total Sources: {dataSources.length}</p>
        <p>Types: {Object.keys(sourceTypes).length}</p>
      </div>
    </div>
  );
}

export default DataSourcePieChart; 