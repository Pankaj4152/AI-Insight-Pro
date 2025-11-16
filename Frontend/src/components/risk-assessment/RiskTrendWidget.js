import React, { useMemo, useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { TrendingUp, TrendingDown, Calendar, Activity } from 'lucide-react';
import { API_BASE_URL } from '../../apiConfig';

const RiskTrendWidget = ({ trendData, timeRange = '30', clientId }) => {
  const [totalFindings, setTotalFindings] = useState(0);
  const [highRiskFindings, setHighRiskFindings] = useState(0);
  const [scanActivityData, setScanActivityData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch accurate total findings, high risk data, and scan activity
  useEffect(() => {
    const fetchAccurateData = async () => {
      console.log('RiskTrendWidget clientId:', clientId);
      if (!clientId) {
        console.log('No clientId provided');
        return;
      }
      
      try {
        setLoading(true);
        
        // Fetch total sensitive records (total findings)
        const totalFindingsResponse = await fetch(`${API_BASE_URL}/risk/total-sensitive-records/${clientId}`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Fetch high risk records
        const highRiskResponse = await fetch(`${API_BASE_URL}/risk/high-risk-records/${clientId}`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Fetch scan activity data
        const scanActivityResponse = await fetch(`${API_BASE_URL}/risk/scan-activity/${clientId}`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (totalFindingsResponse.ok) {
          const totalData = await totalFindingsResponse.json();
          setTotalFindings(totalData.total_sensitive_records || 0);
        }
        
        if (highRiskResponse.ok) {
          const highRiskData = await highRiskResponse.json();
          setHighRiskFindings(highRiskData.high_risk_records || 0);
        }
        
        if (scanActivityResponse.ok) {
          const scanData = await scanActivityResponse.json();
          console.log('Scan activity data fetched:', scanData);
          setScanActivityData(scanData);
        } else {
          console.error('Scan activity response not ok:', scanActivityResponse.status);
        }
      } catch (error) {
        console.error('Error fetching accurate risk data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAccurateData();
  }, [clientId]);

  // Process trend data for charts
  const processedData = useMemo(() => {
    if (!trendData || !Array.isArray(trendData)) return null;

    const labels = trendData.map(item => 
      new Date(item.date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    );

    const totalFindings = trendData.map(item => item.total_findings || 0);
    const highRiskFindings = trendData.map(item => item.high_risk || 0);
    const mediumRiskFindings = trendData.map(item => item.medium_risk || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Total Findings',
          data: totalFindings,
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'High Risk',
          data: highRiskFindings,
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Medium Risk',
          data: mediumRiskFindings,
          borderColor: '#F59E0B',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    };
  }, [trendData]);

  // Process scan activity data
  const processedScanActivityData = useMemo(() => {
    console.log('Processing scan activity data:', scanActivityData);
    if (!scanActivityData || !scanActivityData.daily_scans) {
      console.log('No scan activity data or daily_scans array');
      return null;
    }

    const labels = scanActivityData.daily_scans.map(item => 
      new Date(item.day).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    );

    const scans = scanActivityData.daily_scans.map(item => item.scans || 0);

    console.log('Processed scan activity data:', { labels, scans });

    return {
      labels,
      datasets: [{
        label: 'Daily Scans',
        data: scans,
        backgroundColor: '#10B981',
        borderColor: '#059669',
        borderWidth: 1
      }]
    };
  }, [scanActivityData]);

  // Calculate trend metrics
  const trendMetrics = useMemo(() => {
    if (!trendData || trendData.length < 2) return null;

    const latest = trendData[trendData.length - 1];
    const previous = trendData[trendData.length - 2];

    const totalChange = ((latest.total_findings - previous.total_findings) / previous.total_findings) * 100;
    const highRiskChange = ((latest.high_risk - previous.high_risk) / previous.high_risk) * 100;

    return {
      totalChange: isFinite(totalChange) ? totalChange.toFixed(1) : '0',
      highRiskChange: isFinite(highRiskChange) ? highRiskChange.toFixed(1) : '0',
      isIncreasing: totalChange > 0,
      isHighRiskIncreasing: highRiskChange > 0
    };
  }, [trendData]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: { size: 12 },
          padding: 15
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: { size: 12 },
        bodyFont: { size: 12 },
        padding: 10
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    }
  };

  const barChartOptions = {
    ...chartOptions,
    scales: {
      ...chartOptions.scales,
      y: {
        ...chartOptions.scales.y,
        title: {
          display: true,
          text: 'Number of Findings'
        }
      }
    }
  };

  // Debug logging
  console.log('RiskTrendWidget - processedData:', processedData);
  console.log('RiskTrendWidget - processedScanActivityData:', processedScanActivityData);
  console.log('RiskTrendWidget - trendData:', trendData);
  console.log('RiskTrendWidget - scanActivityData:', scanActivityData);

  if (!processedData || !processedScanActivityData) {
    console.log('Showing "not enough data to analyse" message');
    return (
      <div className="risk-trend-widget">
        <div className="widget-header">
          <h3>Risk Trends</h3>
          <Calendar size={20} />
        </div>
        <div className="no-data">
          <p>not enough data to analyse</p>
        </div>
      </div>
    );
  }

  return (
    <div className="risk-trend-widget">
      <div className="widget-header">
        <div>
          <h3>Risk Trends</h3>
          <p className="widget-subtitle">Last {timeRange} days</p>
        </div>
        <div className="trend-metrics">
          {/* Display accurate current values */}
          <div className="trend-metric">
            <div className="metric-label">Total Findings</div>
            <div className="metric-value current">
              {loading ? 'Loading...' : totalFindings.toLocaleString()}
            </div>
          </div>
          <div className="trend-metric">
            <div className="metric-label">High Risk</div>
            <div className="metric-value current high-risk">
              {loading ? 'Loading...' : highRiskFindings.toLocaleString()}
            </div>
          </div>

        </div>
      </div>

      <div className="charts-container">
        <div className="chart-section full-width">
          <h4>Trend Analysis</h4>
          <div className="chart-wrapper long-rectangle">
            <p>not enough data to analyse</p>
          </div>
        </div>

        <div className="charts-row">
          <div className="chart-section">
            <h4>Risk Findings Trend</h4>
            <div className="chart-wrapper">
              {processedData ? (
                <Line data={processedData} options={chartOptions} />
              ) : (
                <p>No trend data available</p>
              )}
            </div>
          </div>

          <div className="chart-section">
            <h4>Scan Activity</h4>
            <div className="chart-wrapper">
              {processedScanActivityData ? (
                <Bar data={processedScanActivityData} options={barChartOptions} />
              ) : (
                <p>No scan activity data available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskTrendWidget;
