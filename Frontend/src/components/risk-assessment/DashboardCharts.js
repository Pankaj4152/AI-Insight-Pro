// src/components/risk-assessment/DashboardCharts.js
import React from 'react';
import { Pie, Line } from 'react-chartjs-2';
import { formatChartData, chartOptions } from '../../utils/riskAssessmentAPI';

const DashboardCharts = ({ chartData, loading }) => {
  if (loading) {
    return (
      <div className="dashboard-charts">
        <h3>Data Visualization</h3>
        <div className="charts-grid">
          <div className="chart-container loading">
            <div className="chart-skeleton"></div>
            <div className="chart-title skeleton"></div>
          </div>
          <div className="chart-container loading">
            <div className="chart-skeleton"></div>
            <div className="chart-title skeleton"></div>
          </div>
          <div className="chart-container loading">
            <div className="chart-skeleton"></div>
            <div className="chart-title skeleton"></div>
          </div>
        </div>
      </div>
    );
  }

  // Format data for charts
  const dataStoreTypesChart = formatChartData.pieChart(
    chartData.dataStoreTypes || [], 
    'store_type', 
    'count'
  );

  const riskTrendChart = formatChartData.lineChart(
    chartData.trendAnalysis || [], 
    'date', 
    'risk_score',
    { 
      label: 'Risk Score',
      borderColor: '#FF6384',
      backgroundColor: 'rgba(255, 99, 132, 0.1)'
    }
  );

  const scanActivityChart = formatChartData.lineChart(
    chartData.scanActivity || [], 
    'date', 
    'scan_count',
    { 
      label: 'Scans',
      borderColor: '#36A2EB',
      backgroundColor: 'rgba(54, 162, 235, 0.1)'
    }
  );

  return (
    <div className="dashboard-charts">
      <h3>Data Visualization</h3>
      <div className="charts-grid">
        {/* Data Store Types Distribution */}
        <div className="chart-container">
          <h4>Data Store Types</h4>
          <div className="chart-wrapper">
            {chartData.dataStoreTypes && chartData.dataStoreTypes.length > 0 ? (
              <Pie 
                data={dataStoreTypesChart} 
                options={{
                  ...chartOptions.withLegend,
                  plugins: {
                    ...chartOptions.withLegend.plugins,
                    title: {
                      display: false
                    }
                  }
                }}
              />
            ) : (
              <div className="no-data">No data store information available</div>
            )}
          </div>
        </div>

        {/* Risk Score Trend */}
        <div className="chart-container">
          <h4>Risk Score Trend (30 Days)</h4>
          <div className="chart-wrapper">
            {chartData.trendAnalysis && chartData.trendAnalysis.length > 0 ? (
              <Line 
                data={riskTrendChart} 
                options={{
                  ...chartOptions.responsive,
                  scales: {
                    y: {
                      beginAtZero: true,
                      max: 10,
                      title: {
                        display: true,
                        text: 'Risk Score'
                      }
                    },
                    x: {
                      title: {
                        display: true,
                        text: 'Date'
                      }
                    }
                  },
                  plugins: {
                    legend: {
                      display: false
                    }
                  }
                }}
              />
            ) : (
              <div className="no-data">No trend data available</div>
            )}
          </div>
        </div>

        {/* Scan Activity Timeline */}
        <div className="chart-container">
          <h4>Scan Activity Timeline</h4>
          <div className="chart-wrapper">
            {chartData.scanActivity && chartData.scanActivity.length > 0 ? (
              <Line 
                data={scanActivityChart} 
                options={{
                  ...chartOptions.responsive,
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: {
                        display: true,
                        text: 'Number of Scans'
                      }
                    },
                    x: {
                      title: {
                        display: true,
                        text: 'Date'
                      }
                    }
                  },
                  plugins: {
                    legend: {
                      display: false
                    }
                  }
                }}
              />
            ) : (
              <div className="no-data">No scan activity data available</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardCharts;
