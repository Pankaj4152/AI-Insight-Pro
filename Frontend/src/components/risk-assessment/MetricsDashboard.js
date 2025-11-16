import React from 'react';
import { 
  Database, 
  Shield, 
  AlertTriangle, 
  Activity, 
  Target, 
  Zap, 
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

const MetricsDashboard = ({ dashboardData, riskAssessmentData, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="metrics-dashboard loading">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="metric-card skeleton">
            <div className="skeleton-icon"></div>
            <div className="skeleton-content">
              <div className="skeleton-value"></div>
              <div className="skeleton-label"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!dashboardData || !dashboardData.summary) {
    return (
      <div className="metrics-dashboard">
        <div className="metric-card">
          <div className="no-data-message">
            <Database size={24} />
            <p>No metrics data available</p>
            <small>Please run a risk assessment to see metrics</small>
          </div>
        </div>
      </div>
    );
  }

  const { summary } = dashboardData;

  // Calculate medium and low risk SDE counts from sde_risk_distribution
  const calculateRiskSDECounts = () => {
    if (!riskAssessmentData || !riskAssessmentData.sde_risk_distribution) {
      return { mediumRiskSDEs: 0, lowRiskSDEs: 0 };
    }

    const sdeRiskDistribution = riskAssessmentData.sde_risk_distribution || [];
    let mediumRiskSDEs = 0;
    let lowRiskSDEs = 0;

    sdeRiskDistribution.forEach(item => {
      const riskLevel = item.risk_level?.toLowerCase();
      const count = item.count || 0;
      
      if (riskLevel === 'medium') {
        mediumRiskSDEs += count;
      } else if (riskLevel === 'low') {
        lowRiskSDEs += count;
      }
    });

    return { mediumRiskSDEs, lowRiskSDEs };
  };

  const { mediumRiskSDEs, lowRiskSDEs } = calculateRiskSDECounts();

  // Calculate trend indicators (can be enhanced with historical data)
  const getTrendIndicator = (current, previous = null) => {
    if (!previous) return null;
    const change = ((current - previous) / previous) * 100;
    if (change > 5) return { type: 'up', value: change.toFixed(1) };
    if (change < -5) return { type: 'down', value: Math.abs(change).toFixed(1) };
    return { type: 'stable', value: '0' };
  };

  const metrics = [
    {
      id: 'medium_risk_sdes',
      title: 'Medium Risk SDEs',
      value: mediumRiskSDEs,
      icon: AlertCircle,
      color: '#F59E0B',
      trend: getTrendIndicator(mediumRiskSDEs),
      description: 'Moderate security concerns'
    },
    {
      id: 'low_risk_sdes',
      title: 'Low Risk SDEs',
      value: lowRiskSDEs,
      icon: CheckCircle2,
      color: '#10B981',
      trend: getTrendIndicator(lowRiskSDEs),
      description: 'Minimal security concerns'
    },
    {
      id: 'high_risk_sdes',
      title: 'High Risk SDEs',
      value: summary.high_risk_sdes || 0,
      icon: AlertTriangle,
      color: '#EF4444',
      trend: getTrendIndicator(summary.high_risk_sdes),
      description: 'Critical security concerns'
    },
    {
      id: 'total_scans',
      title: 'Total Scans',
      value: summary.total_scans || 0,
      icon: Activity,
      color: '#8B5CF6',
      trend: getTrendIndicator(summary.total_scans),
      description: 'Security scans completed'
    },
    {
      id: 'risk_score',
      title: 'Risk Score',
      value: (summary.risk_score || 0).toFixed(1),
      icon: Target,
      color: summary.risk_score > 70 ? '#EF4444' : summary.risk_score > 40 ? '#F59E0B' : '#10B981',
      trend: getTrendIndicator(summary.risk_score),
      description: 'Overall risk assessment',
      isScore: true
    },
    {
      id: 'confidence_score',
      title: 'Confidence',
      value: `${(summary.confidence_score || 0).toFixed(1)}%`,
      icon: Zap,
      color: '#06B6D4',
      trend: getTrendIndicator(summary.confidence_score),
      description: 'Assessment accuracy',
      isPercentage: true
    }
  ];

  const TrendIcon = ({ trend }) => {
    if (!trend) return null;
    
    switch (trend.type) {
      case 'up':
        return <TrendingUp size={14} className="trend-up" />;
      case 'down':
        return <TrendingDown size={14} className="trend-down" />;
      default:
        return <Minus size={14} className="trend-stable" />;
    }
  };

  return (
    <div className="metrics-dashboard" style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginBottom: '1.5rem'
    }}>
      {metrics.map((metric) => {
        const IconComponent = metric.icon;
        
        return (
          <div key={metric.id} className="metric-card" data-metric={metric.id} style={{
            padding: '1rem',
            minHeight: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            <div className="metric-header" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              marginBottom: '0.5rem'
            }}>
              <div 
                className="metric-icon-container"
                style={{ 
                  backgroundColor: `${metric.color}15`, 
                  color: metric.color,
                  padding: '0.5rem',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <IconComponent className="metric-icon" size={18} />
              </div>
              <div className="metric-label" style={{
                fontSize: '0.875rem',
                fontWeight: '500',
                color: 'var(--text-primary)',
                lineHeight: '1.2'
              }}>
                {metric.title}
              </div>
            </div>
            
            <div className="metric-value" style={{ 
              color: metric.color,
              fontSize: '1.75rem',
              fontWeight: '700',
              lineHeight: '1',
              margin: '0'
            }}>
              {metric.value}
            </div>
            
            <div className="metric-content" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: 'auto'
            }}>
              <div className="metric-description" style={{
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                lineHeight: '1.2'
              }}>
                {metric.description}
              </div>
              {metric.trend && (
                <div className="trend-indicator" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  fontSize: '0.625rem',
                  fontWeight: '500'
                }}>
                  <TrendIcon trend={metric.trend} />
                  <span className="trend-value">{metric.trend.value}%</span>
                </div>
              )}
            </div>
            
            <div className="metric-footer" style={{ marginTop: '0.5rem' }}>
              <div 
                className="metric-progress-bar"
                style={{
                  width: '100%',
                  height: '4px',
                  borderRadius: '2px',
                  background: `linear-gradient(90deg, ${metric.color}20 0%, ${metric.color}40 100%)`,
                  overflow: 'hidden'
                }}
              >
                <div 
                  className="metric-progress-fill"
                  style={{
                    height: '100%',
                    width: metric.isScore ? `${(metric.value / 100) * 100}%` : 
                           metric.isPercentage ? metric.value : 
                           `${Math.min((metric.value / 100) * 100, 100)}%`,
                    backgroundColor: metric.color,
                    transition: 'width 0.3s ease'
                  }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MetricsDashboard;
