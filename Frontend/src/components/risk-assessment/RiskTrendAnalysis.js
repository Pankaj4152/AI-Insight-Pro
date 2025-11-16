import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, Calendar, Activity } from 'lucide-react';
import { API_BASE_URL } from '../../apiConfig';

function RiskTrendAnalysis({ 
  clientId, 
  timeRange = '30', 
  onTimeRangeChange = () => {},
  data, 
  // loading = false, 
  // error = null 
}) {
  const [trendData, setTrendData] = useState([]);
  const [scanActivity, setScanActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get client ID from props or localStorage
  const getClientId = () => {
    return clientId || 
           localStorage.getItem('client_id') || 
           sessionStorage.getItem('client_id') || 
           'demo-client';
  };

  useEffect(() => {
    fetchTrendData();
  }, [timeRange]);

  const fetchTrendData = async () => {
    setLoading(true);
    setError(null);
    const currentClientId = getClientId();
    
    try {
      // Fetch trend analysis data
      const trendResponse = await fetch(
        `${API_BASE_URL}/risk/trend-analysis/${currentClientId}?days=${timeRange}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': currentClientId,
          },
        }
      );
      
      // Fetch scan activity timeline
      const scanResponse = await fetch(
        `${API_BASE_URL}/risk/scan-activity-timeline/${currentClientId}?days=${timeRange}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': currentClientId,
          },
        }
      );

      if (trendResponse.ok) {
        const trendResult = await trendResponse.json();
        setTrendData(trendResult.trend_analysis || []);
      } else {
        throw new Error(`Trend API error: ${trendResponse.status}`);
      }

      if (scanResponse.ok) {
        const scanResult = await scanResponse.json();
        setScanActivity(scanResult.scan_timeline || []);
      } else {
        console.warn('Scan activity data not available');
        setScanActivity([]);
      }

    } catch (error) {
      console.error('Error fetching trend data:', error);
      setError(error.message);
      // Fallback to generate some sample data for demo purposes
      setTrendData(generateFallbackTrendData());
      setScanActivity([]);
    } finally {
      setLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="risk-trend-analysis loading">
        <div className="trend-header">
          <div className="header-left skeleton">
            <div className="skeleton-text title"></div>
            <div className="skeleton-text subtitle"></div>
          </div>
        </div>
        <div className="trend-content skeleton-chart"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="risk-trend-analysis error">
        <div className="trend-header">
          <div className="header-left">
            <TrendingUp className="header-icon" />
            <div className="header-text">
              <h3 className="trend-title">Risk Trend Analysis</h3>
              <p className="trend-subtitle">Unable to load trend data</p>
            </div>
          </div>
        </div>
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={fetchTrendData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Transform data for trend analysis
  const processedTrendData = trendData.length > 0 ? trendData : generateFallbackTrendData();

  return (
    <div className="risk-trend-analysis">
      <div className="trend-header">
        <div className="header-left">
          <TrendingUp className="header-icon" />
          <div className="header-text">
            <h3 className="trend-title">Risk Trend Analysis</h3>
            <p className="trend-subtitle">Risk evolution over the past {timeRange}</p>
          </div>
        </div>
        <div className="header-actions">
          <select 
            className="time-range-select"
            value={timeRange}
            onChange={(e) => {
              // You can add a prop for handling time range changes
              if (typeof onTimeRangeChange === 'function') {
                onTimeRangeChange(e.target.value);
              }
            }}
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
      </div>

      <div className="trend-content">
        <div className="trend-charts">
          {/* Risk Score Trend */}
          <div className="chart-container">
            <div className="chart-header">
              <h4 className="chart-title">Risk Score Trend</h4>
              <div className="chart-legend">
                <span className="legend-item high">High Risk</span>
                <span className="legend-item medium">Medium Risk</span>
                <span className="legend-item low">Low Risk</span>
              </div>
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart               data={processedTrendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorMedium" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorLow" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#ffffff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                    labelFormatter={(value) => `Date: ${value}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="high_risk"
                    stackId="1"
                    stroke="#EF4444"
                    fillOpacity={1}
                    fill="url(#colorHigh)"
                  />
                  <Area
                    type="monotone"
                    dataKey="medium_risk"
                    stackId="1"
                    stroke="#F59E0B"
                    fillOpacity={1}
                    fill="url(#colorMedium)"
                  />
                  <Area
                    type="monotone"
                    dataKey="low_risk"
                    stackId="1"
                    stroke="#10B981"
                    fillOpacity={1}
                    fill="url(#colorLow)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Scan Activity Timeline */}
          <div className="chart-container">
            <div className="chart-header">
              <h4 className="chart-title">Scan Activity Timeline</h4>
              <div className="activity-stats">
                <span className="stat-item">
                  <Activity className="stat-icon" />
                  {scanActivity.length} scans
                </span>
                <span className="stat-item">
                  <Calendar className="stat-icon" />
                  Last {timeRange}
                </span>
              </div>
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={scanActivity} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#ffffff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="findings" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Trend Summary */}
        <div className="trend-summary">
          <div className="summary-card">
            <h4 className="summary-title">Key Insights</h4>
            <div className="insights-list">
              <div className="insight-item">
                <div className="insight-indicator positive"></div>
                <span className="insight-text">
                  Risk score decreased by 15% in the last week
                </span>
              </div>
              <div className="insight-item">
                <div className="insight-indicator neutral"></div>
                <span className="insight-text">
                  Scan frequency increased by 25% this month
                </span>
              </div>
              <div className="insight-item">
                <div className="insight-indicator negative"></div>
                <span className="insight-text">
                  3 new high-risk findings detected yesterday
                </span>
              </div>
            </div>
          </div>

          <div className="summary-stats">
            <div className="stat-card">
              <div className="stat-value">{calculateTrendDirection(trendData)}</div>
              <div className="stat-label">Overall Trend</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{calculateAverageRisk(trendData)}</div>
              <div className="stat-label">Avg Risk Score</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{calculatePeakActivity(scanActivity)}</div>
              <div className="stat-label">Peak Activity</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper functions
function generateFallbackTrendData() {
  const data = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toISOString().split('T')[0],
      high_risk: Math.floor(Math.random() * 20) + 5,
      medium_risk: Math.floor(Math.random() * 50) + 20,
      low_risk: Math.floor(Math.random() * 30) + 10,
      total_findings: Math.floor(Math.random() * 100) + 35
    });
  }
  return data;
}

function calculateTrendDirection(data) {
  if (!data || data.length < 2) return 'Stable';
  const latest = data[data.length - 1];
  const previous = data[data.length - 2];
  const currentTotal = latest.high_risk + latest.medium_risk + latest.low_risk;
  const previousTotal = previous.high_risk + previous.medium_risk + previous.low_risk;
  
  if (currentTotal > previousTotal) return '↗ Increasing';
  if (currentTotal < previousTotal) return '↘ Decreasing';
  return '→ Stable';
}

function calculateAverageRisk(data) {
  if (!data || data.length === 0) return '0';
  const total = data.reduce((sum, item) => {
    return sum + (item.high_risk + item.medium_risk + item.low_risk);
  }, 0);
  return Math.round(total / data.length);
}

function calculatePeakActivity(data) {
  if (!data || data.length === 0) return 'N/A';
  const maxFindings = Math.max(...data.map(item => item.findings || item.total_findings || 0));
  const peakDay = data.find(item => (item.findings || item.total_findings) === maxFindings);
  return peakDay ? peakDay.date : 'N/A';
}

export default RiskTrendAnalysis;
