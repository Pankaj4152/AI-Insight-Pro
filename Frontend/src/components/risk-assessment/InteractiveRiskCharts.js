import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp } from 'lucide-react';

function InteractiveRiskCharts({ data, loading }) {
  if (loading || !data) {
    return (
      <div className="interactive-charts loading">
        <div className="charts-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="chart-card skeleton">
              <div className="chart-header skeleton">
                <div className="skeleton-text"></div>
              </div>
              <div className="chart-content skeleton-chart"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Transform data for charts - using direct risk distribution API response
  console.log('Chart data received:', data);
  console.log('Risk distribution data:', data.riskDistribution);
  
  const riskDistributionData = (data.riskDistribution || []).map(item => ({
    name: `${item.level} Risk`,
    count: item.count,
    color: item.level === 'LOW' ? '#10B981' : item.level === 'MEDIUM' ? '#F59E0B' : '#EF4444'
  }));
  
  console.log('Transformed risk distribution data:', riskDistributionData);

  const sensitivityData = Object.entries(data.sensitivityBySource || {}).map(([source, count]) => ({
    name: source,
    value: count,
    color: getRandomColor()
  }));

  const sdeTypeData = data.sdeCategories || [];
  const detectionMethodData = data.detectionMethods || [];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'];

  return (
    <div className="interactive-charts">
      <div className="charts-header">
        <h3 className="charts-title">
          <TrendingUp className="title-icon" />
          Risk Analysis Charts
        </h3>
      </div>

      <div className="charts-grid">
        {/* Risk Distribution Bar Chart */}
        <div className="chart-card">
          <div className="chart-header">
            <h4 className="chart-title">Risk Distribution Analysis</h4>
            <div className="chart-subtitle">Findings by Risk Level</div>
          </div>
          <div className="chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={riskDistributionData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                <XAxis 
                  dataKey="name" 
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
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sensitivity by Source Pie Chart */}
        <div className="chart-card">
          <div className="chart-header">
            <h4 className="chart-title">Sensitivity by Data Source</h4>
            <div className="chart-subtitle">High sensitivity findings distribution</div>
          </div>
          <div className="chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sensitivityData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {sensitivityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SDE Categories */}
        <div className="chart-card">
          <div className="chart-header">
            <h4 className="chart-title">SDE Categories</h4>
            <div className="chart-subtitle">Types of sensitive data elements found</div>
          </div>
          <div className="chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sdeTypeData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                <XAxis 
                  dataKey="category" 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
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
                <Bar dataKey="count" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detection Methods */}
        <div className="chart-card">
          <div className="chart-header">
            <h4 className="chart-title">Detection Methods</h4>
            <div className="chart-subtitle">How sensitive data was identified</div>
          </div>
          <div className="chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={detectionMethodData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                <XAxis 
                  dataKey="method" 
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
                <Bar dataKey="count" fill="#06B6D4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function getRandomColor() {
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'];
  return colors[Math.floor(Math.random() * colors.length)];
}

export default InteractiveRiskCharts;
