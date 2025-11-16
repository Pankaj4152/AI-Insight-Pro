// src/components/risk-assessment/RiskAnalysisCharts.js
import React from 'react';
import { Pie, Bar, Doughnut } from 'react-chartjs-2';
import { formatChartData, chartOptions } from '../../utils/riskAssessmentAPI';

const RiskAnalysisCharts = ({ chartData, loading }) => {
  if (loading) {
    return (
      <div className="risk-analysis-charts">
        <h3>Risk Analysis</h3>
        <div className="analysis-grid">
          {[...Array(6)].map((_, index) => (
            <div key={index} className="chart-container loading">
              <div className="chart-skeleton"></div>
              <div className="chart-title skeleton"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Format data for risk analysis charts
  const riskDistributionChart = formatChartData.doughnutChart(
    chartData.riskDistribution || [], 
    'risk_level', 
    'count'
  );

  const sensitivityChart = formatChartData.pieChart(
    chartData.sensitivityDistribution || [], 
    'sensitivity', 
    'count'
  );

  const sdeCategoriesChart = formatChartData.pieChart(
    chartData.sdeCategories || [], 
    'category', 
    'count'
  );

  const detectionMethodsChart = formatChartData.barChart(
    chartData.detectionMethods || [], 
    'method', 
    'count',
    { 
      label: 'Detection Count',
      backgroundColor: '#4BC0C0',
      borderColor: '#4BC0C0'
    }
  );

  const confidenceChart = formatChartData.barChart(
    chartData.confidenceDistribution || [], 
    'confidence_level', 
    'count',
    { 
      label: 'Finding Count',
      backgroundColor: '#9966FF',
      borderColor: '#9966FF'
    }
  );

  const topLocationsChart = formatChartData.barChart(
    chartData.topRiskLocations || [], 
    'location', 
    'risk_score',
    { 
      label: 'Risk Score',
      backgroundColor: '#FF6384',
      borderColor: '#FF6384'
    }
  );

  const findingsByStoreChart = formatChartData.barChart(
    chartData.findingsByStore || [], 
    'store_name', 
    'finding_count',
    { 
      label: 'Findings',
      backgroundColor: '#FF9F40',
      borderColor: '#FF9F40'
    }
  );

  const findingTypesChart = formatChartData.pieChart(
    chartData.findingTypes || [], 
    'finding_type', 
    'count'
  );

  return (
    <div className="risk-analysis-charts">
      <h3>Risk Analysis</h3>
      <div className="analysis-grid">
        {/* Risk Level Distribution */}
        <div className="chart-container">
          <h4>Risk Level Distribution</h4>
          <div className="chart-wrapper">
            {chartData.riskDistribution && chartData.riskDistribution.length > 0 ? (
              <Doughnut 
                data={riskDistributionChart} 
                options={{
                  ...chartOptions.withLegend,
                  plugins: {
                    ...chartOptions.withLegend.plugins,
                    legend: {
                      position: 'right',
                      labels: {
                        padding: 15,
                        usePointStyle: true,
                      }
                    }
                  }
                }}
              />
            ) : (
              <div className="no-data">No risk distribution data available</div>
            )}
          </div>
        </div>

        {/* Sensitivity Distribution */}
        <div className="chart-container">
          <h4>Sensitivity Categories</h4>
          <div className="chart-wrapper">
            {chartData.sensitivityDistribution && chartData.sensitivityDistribution.length > 0 ? (
              <Pie 
                data={sensitivityChart} 
                options={chartOptions.withLegend}
              />
            ) : (
              <div className="no-data">No sensitivity data available</div>
            )}
          </div>
        </div>

        {/* SDE Categories */}
        <div className="chart-container">
          <h4>SDE Categories Distribution</h4>
          <div className="chart-wrapper">
            {chartData.sdeCategories && chartData.sdeCategories.length > 0 ? (
              <Pie 
                data={sdeCategoriesChart} 
                options={chartOptions.withLegend}
              />
            ) : (
              <div className="no-data">No SDE category data available</div>
            )}
          </div>
        </div>

        {/* Detection Methods */}
        <div className="chart-container">
          <h4>Detection Methods</h4>
          <div className="chart-wrapper">
            {chartData.detectionMethods && chartData.detectionMethods.length > 0 ? (
              <Bar 
                data={detectionMethodsChart} 
                options={{
                  ...chartOptions.responsive,
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: {
                        display: true,
                        text: 'Number of Detections'
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
              <div className="no-data">No detection method data available</div>
            )}
          </div>
        </div>

        {/* Confidence Score Distribution */}
        <div className="chart-container">
          <h4>Confidence Score Distribution</h4>
          <div className="chart-wrapper">
            {chartData.confidenceDistribution && chartData.confidenceDistribution.length > 0 ? (
              <Bar 
                data={confidenceChart} 
                options={{
                  ...chartOptions.responsive,
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: {
                        display: true,
                        text: 'Number of Findings'
                      }
                    },
                    x: {
                      ticks: {
                        maxRotation: 45,
                        minRotation: 45
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
              <div className="no-data">No confidence data available</div>
            )}
          </div>
        </div>

        {/* Top Risk Locations */}
        <div className="chart-container">
          <h4>Top Risk Locations</h4>
          <div className="chart-wrapper">
            {chartData.topRiskLocations && chartData.topRiskLocations.length > 0 ? (
              <Bar 
                data={topLocationsChart} 
                options={{
                  ...chartOptions.responsive,
                  indexAxis: 'y',
                  scales: {
                    x: {
                      beginAtZero: true,
                      max: 10,
                      title: {
                        display: true,
                        text: 'Risk Score'
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
              <div className="no-data">No risk location data available</div>
            )}
          </div>
        </div>

        {/* Findings by Data Store */}
        <div className="chart-container">
          <h4>Findings by Data Store</h4>
          <div className="chart-wrapper">
            {chartData.findingsByStore && chartData.findingsByStore.length > 0 ? (
              <Bar 
                data={findingsByStoreChart} 
                options={{
                  ...chartOptions.responsive,
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: {
                        display: true,
                        text: 'Number of Findings'
                      }
                    },
                    x: {
                      ticks: {
                        maxRotation: 45,
                        minRotation: 45
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
              <div className="no-data">No findings by store data available</div>
            )}
          </div>
        </div>

        {/* Finding Types Breakdown */}
        <div className="chart-container">
          <h4>Finding Types Breakdown</h4>
          <div className="chart-wrapper">
            {chartData.findingTypes && chartData.findingTypes.length > 0 ? (
              <Pie 
                data={findingTypesChart} 
                options={chartOptions.withLegend}
              />
            ) : (
              <div className="no-data">No finding types data available</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskAnalysisCharts;
