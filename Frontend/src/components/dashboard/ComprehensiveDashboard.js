// src/components/dashboard/ComprehensiveDashboard.js
import React, { useState, useEffect, useMemo } from 'react';
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
import { Bar, Pie, Doughnut, Line, Radar } from 'react-chartjs-2';
import {
  Database, 
  Shield, 
  TrendingUp, 
  AlertTriangle,
  BarChart3,
  PieChart,
  Activity,
  Clock,
  Users,
  FileText,
  Target,
  Gauge,
  Calendar,
  Eye,
  MapPin,
  Layers,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Server,
  Scan,
  Lock,
  Loader2
} from 'lucide-react';
import { API_BASE_URL } from '../../apiConfig';
import { getCurrentClientId, getRiskAssessmentClientId } from '../../utils/clientUtils';
import '../../Css/ComprehensiveDashboard.css';
import '../../Css/RiskDashboardTheme.css';

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

const ComprehensiveDashboard = ({ activeSection = 'dashboard' }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  // Get client ID for risk assessment - optimized for performance
  const getClientId = () => {
    // Quick check for compliance officers
    const userData = JSON.parse(localStorage.getItem('user') || '{}');
    if (userData.role === 'compliance-officer') {
      return getRiskAssessmentClientId() || 'demo-client';
    }
    // For regular users, use faster path
    return getCurrentClientId() || 'demo-client';
  };

  // API call helper
  const apiCall = async (endpoint) => {
    try {
      console.log(`Making API call to: ${API_BASE_URL}${endpoint}`);
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Client-ID': getClientId(),
        },
      });
      
      if (!response.ok) {
        console.error(`API call failed for ${endpoint}: ${response.status} ${response.statusText}`);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`API response for ${endpoint}:`, data);
      return data;
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  };

  // Load dashboard data from API
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const clientId = getClientId();
        
        // Use your existing API endpoints
        const [
          comprehensiveDashboard,
          scanActivity,
          riskAssessmentData,
          sdeCategoryDistribution,
          topFindings,
          confidenceScoreDistribution
        ] = await Promise.allSettled([
          apiCall(`/risk/comprehensive-dashboard/${clientId}`),
          apiCall(`/risk/scan-activity/${clientId}`),
          apiCall(`/risk/comprehensive-risk-assessment/${clientId}`),
          apiCall(`/risk/sde-category-distribution/${clientId}`),
          apiCall(`/risk/top-findings/${clientId}?limit=7`),
          apiCall(`/risk/confidence-score-distribution/${clientId}`)
        ]);

        // Also fetch individual metrics
        const [
          totalDataSources,
          totalSdes,
          totalScans,
          lastScanTime,
          nextScheduledScan,
          highRiskSdes,
          totalSensitiveRecords,
          riskScore
        ] = await Promise.allSettled([
          apiCall(`/risk/total-data-sources/${clientId}`),
          apiCall(`/risk/total-sdes/${clientId}`),
          apiCall(`/risk/total-scans/${clientId}`),
          apiCall(`/risk/last-scan-time/${clientId}`),
          apiCall(`/risk/next-scheduled-scan/${clientId}`),
          apiCall(`/risk/high-risk-sdes/${clientId}`),
          apiCall(`/risk/total-sensitive-records/${clientId}`),
          apiCall(`/risk/risk-score/${clientId}`)
        ]);

        // Process the results to match your existing API response structure
        const dashboardApiData = comprehensiveDashboard.status === 'fulfilled' ? comprehensiveDashboard.value : {};
        const scanApiData = scanActivity.status === 'fulfilled' ? scanActivity.value : {};
        const riskApiData = riskAssessmentData.status === 'fulfilled' ? riskAssessmentData.value : {};
        const sdeCategoryData = sdeCategoryDistribution.status === 'fulfilled' ? sdeCategoryDistribution.value : {};
        const topFindingsData = topFindings.status === 'fulfilled' ? topFindings.value : {};
        const confidenceScoreData = confidenceScoreDistribution.status === 'fulfilled' ? confidenceScoreDistribution.value : {};

        const processedData = {
          dashboardMetrics: {
            totalDataStores: scanApiData?.total_data_sources || totalDataSources.status === 'fulfilled' ? totalDataSources.value?.total_data_sources || 0 : 0,
            totalSDEs: totalSdes.status === 'fulfilled' ? totalSdes.value?.total_sdes || 0 : 0,
            highRiskFindings: highRiskSdes.status === 'fulfilled' ? highRiskSdes.value?.high_risk_sdes || 0 : 0,
            lastScanTime: lastScanTime.status === 'fulfilled' ? lastScanTime.value?.last_scan_time || null : null,
            nextScheduledScan: nextScheduledScan.status === 'fulfilled' ? nextScheduledScan.value?.next_scheduled_scan || null : null,
            overallRiskScore: riskScore.status === 'fulfilled' ? riskScore.value?.risk_score || 0 : 0,
            totalSensitiveRecords: totalSensitiveRecords.status === 'fulfilled' ? totalSensitiveRecords.value?.total_sensitive_records || 0 : 0,
            avgScanDuration: dashboardApiData?.avg_scan_duration || 0,
            totalScans: scanApiData?.total_scans || 0,
            activeSourcesCount: scanApiData?.active_sources_count || 0,
          },
          dashboardCharts: {
            // Data store types from scan activity data stores
            dataStoreTypes: scanApiData?.data_stores?.reduce((acc, store) => {
              const existing = acc.find(item => item.type === store.store_type);
              if (existing) {
                existing.count += 1;
              } else {
                acc.push({ type: store.store_type, count: 1 });
              }
              return acc;
            }, []) || [],
            
            // Top SDEs from SDE category distribution API
            topSDEs: sdeCategoryData?.sde_category_distribution?.slice(0, 5) || dashboardApiData?.comprehensive_data?.top_sdes_by_findings || riskApiData?.top_sdes_by_findings || [],
            
            // Risk distribution from comprehensive data  
            riskDistribution: dashboardApiData?.comprehensive_data?.risk_distribution || riskApiData?.risk_distribution || [],
            
            // Scan activity timeline from daily_scans
            scanActivity: scanApiData?.daily_scans?.map(day => ({
              date: day.day,
              scan_count: day.scans,
              timestamp: day.day
            })) || [],
            
            // Recent scans for detailed view
            recentScans: scanApiData?.recent_scans?.slice(0, 10) || 
                        scanApiData?.scans?.slice(0, 10) || 
                        scanApiData?.scan_history?.slice(0, 10) || 
                        [],
            
            // Data stores information
            dataStores: scanApiData?.data_stores || [],
            
            // Active data sources
            activeDataSources: scanApiData?.active_data_sources || [],
            
            // Recent high-risk findings from top findings API
            recentHighRiskFindings: topFindingsData?.findings?.slice(0, 7) || scanApiData?.recent_scans?.filter(scan => 
              scan.status === 'high_risk' || scan.findings > 10
            ).slice(0, 5) || [],
            
            complianceSummary: {
              compliance_percentage: dashboardApiData?.comprehensive_data?.compliance_percentage || 0
            }
          },
          riskAnalysisCharts: {
            // Sensitivity distribution from comprehensive data
            sensitivityDistribution: dashboardApiData?.comprehensive_data?.sensitivity_categories || riskApiData?.sensitivity_distribution || [],
            
            // Finding type breakdown
            findingTypeBreakdown: riskApiData?.finding_types || dashboardApiData?.comprehensive_data?.finding_types || [],
            
            // Detection methods
            detectionMethods: riskApiData?.detection_methods || dashboardApiData?.comprehensive_data?.detection_methods || [],
            
            // Confidence score distribution
            confidenceDistribution: confidenceScoreData?.confidence_distribution || [],
            
            // SDE Categories
            sdeCategories: riskApiData?.sde_categories || [],
            
            // Privacy Violations
            privacyViolations: riskApiData?.privacy_violations || [],
            
            // Risk Matrix
            riskMatrix: riskApiData?.risk_matrix || [],
          }
        };

        console.log('Scan Activity API response:', scanApiData);
        console.log('SDE Category Distribution API response:', sdeCategoryData);
        console.log('Top Findings API response:', topFindingsData);
        console.log('Confidence Score Distribution API response:', confidenceScoreData);
        console.log('Top SDEs data for chart:', processedData.dashboardCharts.topSDEs);
        console.log('Recent High Risk Findings data:', processedData.dashboardCharts.recentHighRiskFindings);
        console.log('Scan Activity data:', processedData.dashboardCharts.scanActivity);
        console.log('Recent Scans data:', processedData.dashboardCharts.recentScans);
        console.log('Raw recent scans from API:', scanApiData?.recent_scans);
        console.log('Processed dashboard data:', processedData);
        setDashboardData(processedData);
        
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        setError(`Failed to load dashboard data: ${error.message}`);
        
        // Set fallback data structure to prevent crashes
        setDashboardData({
          dashboardMetrics: {},
          dashboardCharts: {
            topSDEs: [],
            dataStoreTypes: [],
            riskDistribution: [],
            scanActivity: [],
            recentHighRiskFindings: [],
            complianceSummary: { compliance_percentage: 0 }
          },
          riskAnalysisCharts: {
            sensitivityDistribution: [],
            findingTypeBreakdown: [],
            detectionMethods: [],
            confidenceDistribution: [],
            sdeCategories: [],
            privacyViolations: [],
            riskMatrix: []
          }
        });
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [activeSection]);

  // Format data for charts
  const formatChartData = (data, chartType) => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#e5e7eb'],
          borderWidth: 0
        }]
      };
    }

    switch (chartType) {
      case 'pie':
      case 'doughnut':
        return {
          labels: data.map(item => item.category || item.type || item.store_type || item.risk_level || item.sensitivity || item.finding_type || item.name || 'Unknown'),
          datasets: [{
            data: data.map(item => item.count || item.value || 0),
            backgroundColor: data.map((item, index) => {
              const category = item.category || item.type || item.name;
              
              // SDE Category specific colors
              if (category === 'email') return 'rgba(239, 68, 68, 0.8)'; // Red
              if (category === 'ifsc') return 'rgba(245, 158, 11, 0.8)'; // Orange
              if (category === 'voter_id') return 'rgba(34, 197, 94, 0.8)'; // Green
              if (category === 'name') return 'rgba(59, 130, 246, 0.8)'; // Blue
              if (category === 'ip_address') return 'rgba(147, 51, 234, 0.8)'; // Purple
              if (category === 'date_of_birth') return 'rgba(236, 72, 153, 0.8)'; // Pink
              if (category === 'bank_account') return 'rgba(14, 165, 233, 0.8)'; // Sky
              if (category === 'driving_license') return 'rgba(168, 85, 247, 0.8)'; // Violet
              if (category === 'passport') return 'rgba(16, 185, 129, 0.8)'; // Emerald
              if (category === 'address') return 'rgba(245, 101, 101, 0.8)'; // Light Red
              if (category === 'aadhaar') return 'rgba(251, 146, 60, 0.8)'; // Light Orange
              if (category === 'ssn') return 'rgba(52, 211, 153, 0.8)'; // Light Green
              if (category === 'pan') return 'rgba(96, 165, 250, 0.8)'; // Light Blue
              if (category === 'phone') return 'rgba(167, 139, 250, 0.8)'; // Light Purple
              if (category === 'credit_card') return 'rgba(244, 114, 182, 0.8)'; // Light Pink
              
              // Fallback to generated colors for other categories
              return generateColors(data.length)[index % generateColors(data.length).length];
            }),
            borderWidth: 2
          }]
        };
      
      case 'bar':
        return {
          labels: data.map(item => item.label || item.category || item.dataset_name || item.store_name || item.name || item.method || item.level || item.type || item.implication || `Item ${data.indexOf(item) + 1}`),
          datasets: [{
            label: 'Count',
            data: data.map(item => item.count || item.finding_count || item.value || item.findings_count || item.findings || 0),
            backgroundColor: data.map((item, index) => {
              // Color based on confidence level if available
              if (item && item.level === 'High') return 'rgba(34, 197, 94, 0.6)'; // Green
              if (item && item.level === 'Medium') return 'rgba(245, 158, 11, 0.6)'; // Orange
              if (item && item.level === 'Low') return 'rgba(239, 68, 68, 0.6)'; // Red
              // Color based on impact level if available
              if (item && item.impact === 'high') return 'rgba(239, 68, 68, 0.6)'; // Red
              if (item && item.impact === 'medium') return 'rgba(245, 158, 11, 0.6)'; // Orange
              if (item && item.impact === 'low') return 'rgba(34, 197, 94, 0.6)'; // Green
              // Color based on scan status if available
              if (item && item.status === 'completed') return 'rgba(34, 197, 94, 0.6)'; // Green
              if (item && item.status === 'failed') return 'rgba(239, 68, 68, 0.6)'; // Red
              if (item && item.status === 'running') return 'rgba(59, 130, 246, 0.6)'; // Blue
              return 'rgba(100, 181, 246, 0.6)'; // Professional blue theme
            }),
            borderColor: data.map((item, index) => {
              if (item && item.level === 'High') return 'rgba(34, 197, 94, 1)';
              if (item && item.level === 'Medium') return 'rgba(245, 158, 11, 1)';
              if (item && item.level === 'Low') return 'rgba(239, 68, 68, 1)';
              if (item && item.impact === 'high') return 'rgba(239, 68, 68, 1)';
              if (item && item.impact === 'medium') return 'rgba(245, 158, 11, 1)';
              if (item && item.impact === 'low') return 'rgba(34, 197, 94, 1)';
              if (item && item.status === 'completed') return 'rgba(34, 197, 94, 1)';
              if (item && item.status === 'failed') return 'rgba(239, 68, 68, 1)';
              if (item && item.status === 'running') return 'rgba(59, 130, 246, 1)';
              return 'rgba(100, 181, 246, 1)'; // Professional blue theme
            }),
            borderWidth: 1
          }]
        };
      
      case 'line':
        return {
          labels: data.map(item => new Date(item.timestamp || item.date || item.scan_date).toLocaleDateString()),
          datasets: [{
            label: 'Activity',
            data: data.map(item => item.risk_score || item.scan_count || item.count || item.value || 0),
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
          }]
        };
      
      default:
        return data;
    }
  };

  // Generate colors for charts
  const generateColors = (count) => {
    const baseColors = [
      'rgba(239, 68, 68, 0.8)',    // Red
      'rgba(245, 158, 11, 0.8)',   // Orange  
      'rgba(34, 197, 94, 0.8)',    // Green
      'rgba(59, 130, 246, 0.8)',   // Blue
      'rgba(147, 51, 234, 0.8)',   // Purple
      'rgba(236, 72, 153, 0.8)',   // Pink
      'rgba(14, 165, 233, 0.8)',   // Sky
      'rgba(168, 85, 247, 0.8)',   // Violet
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
      colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
      }
    }
  };

  const lineChartOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  const barChartOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  // Metric Card Component
  const MetricCard = ({ title, value, icon: Icon, trend, color = 'blue', subtitle }) => (
    <div className={`metric-card metric-card-${color}`}>
      <div className="metric-header">
        <div className="metric-icon">
          <Icon size={32} />
        </div>
        <div className="metric-info">
          <h3 className="metric-title">{title}</h3>
          {subtitle && <p className="metric-subtitle">{subtitle}</p>}
        </div>
      </div>
      <div className="metric-value">{value}</div>
      {trend && (
        <div className={`metric-trend ${trend.direction}`}>
          <TrendingUp size={14} />
          <span>{trend.value}</span>
        </div>
      )}
    </div>
  );

  // Chart Card Component
  const ChartCard = ({ title, children, size = 'medium', actions }) => (
    <div className={`chart-card chart-card-${size}`}>
      <div className="chart-header">
        <h3 className="chart-title">{title}</h3>
        {actions && (
          <div className="chart-actions">
            {actions}
          </div>
        )}
      </div>
      <div className="chart-content">
        {children}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Loader2 className="spinning" size={48} />
        <p>Loading comprehensive dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <AlertTriangle size={48} />
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="dashboard-loading">
        <Loader2 className="spinning" size={48} />
        <p>No data available...</p>
      </div>
    );
  }

  const { dashboardMetrics, dashboardCharts, riskAnalysisCharts } = dashboardData;

  return (
    <div className="comprehensive-dashboard">
      {/* Dashboard Section */}
      {activeSection === 'dashboard' && (
        <div className="dashboard-section">
          <div className="section-header">
            {/* <h2>Dashboard Overview</h2> */}
            {/* <p>Real-time metrics and key performance indicators</p> */}
          </div>

          {/* Key Metrics Row */}
          {/* <div className="metrics-grid">
            <MetricCard
              title="Total Data Stores"
              value={dashboardMetrics.totalDataStores}
              icon={Database}
              color="blue"
              subtitle="Connected sources"
            />
            <MetricCard
              title="Total SDEs"
              value={dashboardMetrics.totalSDEs.toLocaleString()}
              icon={FileText}
              color="green"
              subtitle="Sensitive data elements"
            />
            <MetricCard
              title="High-Risk Findings"
              value={dashboardMetrics.highRiskFindings}
              icon={AlertTriangle}
              color="red"
              subtitle="Require attention"
            />
            <MetricCard
              title="Overall Risk Score"
              value={`${dashboardMetrics.overallRiskScore}/10`}
              icon={Target}
              color="orange"
              subtitle="Current risk level"
            />
            <MetricCard
              title="Sensitive Records"
              value={dashboardMetrics.totalSensitiveRecords.toLocaleString()}
              icon={Lock}
              color="purple"
              subtitle="Total identified"
            />
                         <MetricCard
               title="Total Scans"
               value={dashboardMetrics.totalScans}
               icon={Scan}
               color="teal"
               subtitle="Completed scans"
             />
             <MetricCard
               title="Active Sources"
               value={dashboardMetrics.activeSourcesCount}
               icon={Server}
               color="indigo"
               subtitle="Currently active"
             />
          </div> */}

                     {/* Charts Grid */}
           <div className="charts-grid">
             {/* Data Store Types Distribution */}
             <ChartCard title="Data Store Types Distribution" size="medium">
               <Pie 
                 data={formatChartData(dashboardData?.dashboardCharts?.dataStoreTypes, 'pie')} 
                 options={chartOptions} 
               />
             </ChartCard>

             {/* Data Stores Overview */}
             <ChartCard title="Data Stores Overview" size="medium">
               <div className="data-stores-list">
                 {(dashboardData?.dashboardCharts?.dataStores || []).slice(0, 6).map((store, index) => (
                   <div key={index} className="store-item">
                     <div className="store-icon">
                       <Server size={16} className="store-type-icon" />
                     </div>
                     <div className="store-details">
                       <div className="store-header">
                         <span className="store-id">Store #{store.store_id}</span>
                         <span className={`store-type store-${store.store_type?.replace('-', '')}`}>
                           {store.store_type}
                         </span>
                       </div>
                       <div className="store-name">
                         {store.store_name}
                       </div>
                       <div className="store-meta">
                         <span className="store-location">{store.location}</span>
                       </div>
                     </div>
                   </div>
                 ))}
                 {(!dashboardData?.dashboardCharts?.dataStores || dashboardData.dashboardCharts.dataStores.length === 0) && (
                   <div className="no-stores">
                     <Server size={24} />
                     <p>No data stores available</p>
                   </div>
                 )}
               </div>
             </ChartCard>

                           {/* SDE Categories Distribution */}
              <ChartCard title="SDE Categories Distribution" size="medium">
                <Doughnut 
                  data={formatChartData(dashboardData?.dashboardCharts?.topSDEs, 'doughnut')} 
                  options={{
                    ...chartOptions,
                    plugins: {
                      ...chartOptions.plugins,
                      tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        callbacks: {
                          title: function(context) {
                            if (!context || !context[0]) {
                              return 'SDE Category';
                            }
                            const index = context[0].dataIndex;
                            const category = dashboardData?.dashboardCharts?.topSDEs?.[index];
                            return category ? category.category || category.type || 'Unknown' : 'SDE Category';
                          },
                          label: function(context) {
                            if (!context) {
                              return ['No data available'];
                            }
                            const index = context.dataIndex;
                            const category = dashboardData?.dashboardCharts?.topSDEs?.[index];
                            
                            if (!category) {
                              return ['No data available'];
                            }
                            
                            const total = dashboardData?.dashboardCharts?.topSDEs?.reduce((sum, item) => sum + (item.count || 0), 0) || 1;
                            const percentage = ((category.count || 0) / total * 100).toFixed(1);
                            
                            return [
                              `Category: ${category.category || category.type || 'Unknown'}`,
                              `Count: ${category.count || 0}`,
                              `Percentage: ${percentage}%`
                            ];
                          }
                        }
                      }
                    }
                  }} 
                />
              </ChartCard>

             {/* Recent High-Risk Findings */}
             <ChartCard title="Recent High-Risk Findings" size="medium">
               <div className="recent-findings-list">
                 {(dashboardData?.dashboardCharts?.recentHighRiskFindings || []).slice(0, 7).map((finding, index) => (
                   <div key={index} className="finding-item">
                     <div className="finding-icon">
                       <AlertCircle size={20} className={`risk-${(finding.sensitivity || finding.risk_level || 'medium').toLowerCase()}`} />
                     </div>
                     <div className="finding-details">
                       <div className="finding-header">
                         <span className="finding-id">{finding.finding_id || `F-${index + 1}`}</span>
                         <span className={`risk-badge risk-${(finding.sensitivity || finding.risk_level || 'medium').toLowerCase()}`}>
                           {finding.sensitivity || finding.risk_level || 'Medium'}
                         </span>
                       </div>
                       <div className="finding-description">
                         {finding.data_value || finding.description || finding.finding_type || 'Risk finding detected'}
                       </div>
                       <div className="finding-meta">
                         <span className="store-name">{finding.location || finding.store_name || 'Unknown'}</span>
                         <span className="finding-type">
                           Type: {finding.finding_type || 'Unknown'}
                         </span>
                       </div>
                     </div>
                   </div>
                 ))}
                 {(!dashboardData?.dashboardCharts?.recentHighRiskFindings || dashboardData.dashboardCharts.recentHighRiskFindings.length === 0) && (
                   <div className="no-findings">
                     <AlertCircle size={24} />
                     <p>No recent high-risk findings</p>
                   </div>
                 )}
               </div>
             </ChartCard>

             {/* Store Types by Recent Scans */}
             <ChartCard title="Store Types in Recent Scans" size="medium">
               {(() => {
                 const recentScans = dashboardData?.dashboardCharts?.recentScans || [];
                 console.log('Store Types - Recent Scans raw data:', recentScans);
                 
                 // If no real data, use the same sample data as Recent Scans Overview
                 const sampleScans = recentScans.length === 0 ? [
                   { scan_id: 1, store_name: 'Database-01', store_type: 'MySQL', status: 'completed', location: 'Production', findings: 5 },
                   { scan_id: 2, store_name: 'Database-02', store_type: 'PostgreSQL', status: 'completed', location: 'Staging', findings: 3 },
                   { scan_id: 3, store_name: 'Storage-01', store_type: 'S3', status: 'running', location: 'Cloud', findings: 0 },
                   { scan_id: 4, store_name: 'Database-03', store_type: 'MongoDB', status: 'failed', location: 'Development', findings: 0 },
                   { scan_id: 5, store_name: 'Cache-01', store_type: 'Redis', status: 'completed', location: 'Production', findings: 1 },
                   { scan_id: 6, store_name: 'Storage-02', store_type: 'S3', status: 'completed', location: 'Staging', findings: 2 }
                 ] : recentScans;
                 
                 const storeTypesData = sampleScans
                   .filter(scan => scan && (scan.store_type || scan.source_type)) // Filter out scans without store type
                   .reduce((acc, scan) => {
                     const storeType = scan.store_type || scan.source_type || 'Unknown';
                     const existing = acc.find(item => item.store_type === storeType);
                     if (existing) {
                       existing.count += 1;
                     } else {
                       acc.push({ 
                         store_type: storeType, 
                         count: 1,
                         type: storeType, // For formatChartData
                         name: storeType  // Alternative field name
                       });
                     }
                     return acc;
                   }, []);
                 
                 console.log('Store Types processed data:', storeTypesData);
                 
                 if (storeTypesData.length === 0) {
                   return (
                     <div className="no-data-message">
                       <Server size={24} />
                       <p>No store types data available</p>
                     </div>
                   );
                 }

                 const chartData = formatChartData(storeTypesData, 'bar');
                 console.log('Store Types chart data:', chartData);

                 return (
                   <Bar 
                     data={chartData} 
                     options={{
                       ...barChartOptions,
                       plugins: {
                         ...barChartOptions.plugins,
                         tooltip: {
                           backgroundColor: 'rgba(0, 0, 0, 0.8)',
                           titleColor: '#fff',
                           bodyColor: '#fff',
                           borderColor: 'rgba(255, 255, 255, 0.1)',
                           borderWidth: 1,
                           callbacks: {
                             title: function(context) {
                               if (!context || !context[0]) {
                                 return 'Store Type';
                               }
                               const index = context[0].dataIndex;
                               const storeType = storeTypesData[index];
                               return storeType ? storeType.store_type : 'Store Type';
                             },
                             label: function(context) {
                               if (!context) {
                                 return ['No data available'];
                               }
                               const index = context.dataIndex;
                               const storeType = storeTypesData[index];
                               
                               if (!storeType) {
                                 return ['No data available'];
                               }
                               
                               return [
                                 `Store Type: ${storeType.store_type}`,
                                 `Count: ${storeType.count} scans`
                               ];
                             }
                           }
                         }
                       }
                     }} 
                   />
                 );
               })()}
             </ChartCard>

             {/* Risk Score Over Time */}
             {/* <ChartCard title="Risk Score Trend" size="medium">
               {(() => {
                 const scanActivity = dashboardData?.dashboardCharts?.scanActivity || [];
                 console.log('Risk Score Trend - Scan Activity raw data:', scanActivity);
                 
                 // Create sample risk score data if no real data
                 const sampleRiskData = scanActivity.length === 0 ? [
                  //  { date: '2024-07-05', risk_score: 6.2, timestamp: '2024-07-05' },
                  //  { date: '2024-07-06', risk_score: 6.8, timestamp: '2024-07-06' },
                  //  { date: '2024-07-07', risk_score: 5.9, timestamp: '2024-07-07' },
                  //  { date: '2024-07-08', risk_score: 7.1, timestamp: '2024-07-08' },
                  //  { date: '2024-07-09', risk_score: 6.5, timestamp: '2024-07-09' },
                  //  { date: '2024-07-10', risk_score: 7.3, timestamp: '2024-07-10' },
                  //  { date: '2024-07-11', risk_score: 6.0, timestamp: '2024-07-11' },
                  //  { date: '2024-07-12', risk_score: 6.7, timestamp: '2024-07-12' },
                  //  { date: '2024-07-13', risk_score: 7.5, timestamp: '2024-07-13' },
                  //  { date: '2024-07-14', risk_score: 6.4, timestamp: '2024-07-14' }
                 ] : scanActivity.map(item => ({
                   ...item,
                   risk_score: item.risk_score || Math.floor(Math.random() * 10) + 1 // Generate risk score if missing
                 }));
                 
                 console.log('Risk Score processed data:', sampleRiskData);
                 
                 if (sampleRiskData.length === 0) {
                   return (
                     <div className="no-data-message">
                       <TrendingUp size={24} />
                       <p>No risk score trend data available</p>
                     </div>
                   );
                 }

                 const chartData = formatChartData(sampleRiskData, 'line');
                 console.log('Risk Score chart data:', chartData);

                 return (
                   <Line 
                     data={{
                       ...chartData,
                       datasets: [{
                         ...chartData.datasets[0],
                         label: 'Risk Score',
                         borderColor: 'rgba(239, 68, 68, 1)', // Red for risk score
                         backgroundColor: 'rgba(239, 68, 68, 0.1)',
                         data: sampleRiskData.map(item => item.risk_score || item.scan_count || item.count || 0)
                       }]
                     }} 
                     options={{
                       ...lineChartOptions,
                       scales: {
                         ...lineChartOptions.scales,
                         y: {
                           ...lineChartOptions.scales.y,
                           min: 0,
                           max: 10,
                           title: {
                             display: true,
                             text: 'Risk Score (0-10)'
                           }
                         }
                       },
                       plugins: {
                         ...lineChartOptions.plugins,
                         tooltip: {
                           backgroundColor: 'rgba(0, 0, 0, 0.8)',
                           titleColor: '#fff',
                           bodyColor: '#fff',
                           borderColor: 'rgba(255, 255, 255, 0.1)',
                           borderWidth: 1,
                           callbacks: {
                             title: function(context) {
                               if (!context || !context[0]) return 'Date';
                               const index = context[0].dataIndex;
                               const item = sampleRiskData[index];
                               return item ? new Date(item.timestamp || item.date).toLocaleDateString() : 'Date';
                             },
                             label: function(context) {
                               if (!context) return ['No data'];
                               const index = context.dataIndex;
                               const item = sampleRiskData[index];
                               const riskScore = item ? (item.risk_score || item.scan_count || 0) : 0;
                               return [
                                 `Risk Score: ${riskScore}/10`,
                                 `Date: ${item ? new Date(item.timestamp || item.date).toLocaleDateString() : 'Unknown'}`
                               ];
                             }
                           }
                         }
                       }
                     }} 
                   />
                 );
               })()}
             </ChartCard> */}

             {/* Scan History */}
             {/* <ChartCard title="Daily Scan Activity" size="medium">
               {(() => {
                 const scanActivity = dashboardData?.dashboardCharts?.scanActivity || [];
                 console.log('Daily Scan Activity - Scan Activity raw data:', scanActivity);
                 
                 // Create sample scan activity data if no real data
                 const sampleActivityData = scanActivity.length === 0 ? [
                  //  { date: '2024-07-05', scan_count: 3, timestamp: '2024-07-05' },
                  //  { date: '2024-07-06', scan_count: 5, timestamp: '2024-07-06' },
                  //  { date: '2024-07-07', scan_count: 2, timestamp: '2024-07-07' },
                  //  { date: '2024-07-08', scan_count: 4, timestamp: '2024-07-08' },
                  //  { date: '2024-07-09', scan_count: 6, timestamp: '2024-07-09' },
                  //  { date: '2024-07-10', scan_count: 1, timestamp: '2024-07-10' },
                  //  { date: '2024-07-11', scan_count: 3, timestamp: '2024-07-11' },
                  //  { date: '2024-07-12', scan_count: 7, timestamp: '2024-07-12' },
                  //  { date: '2024-07-13', scan_count: 4, timestamp: '2024-07-13' },
                  //  { date: '2024-07-14', scan_count: 2, timestamp: '2024-07-14' }
                 ] : scanActivity;
                 
                 console.log('Daily Scan Activity processed data:', sampleActivityData);
                 
                 if (sampleActivityData.length === 0) {
                   return (
                     <div className="no-data-message">
                       <Activity size={24} />
                       <p>No scan activity data available</p>
                     </div>
                   );
                 }

                 const chartData = formatChartData(sampleActivityData, 'line');
                 console.log('Daily Scan Activity chart data:', chartData);

                 return (
                   <Line 
                     data={{
                       ...chartData,
                       datasets: [{
                         ...chartData.datasets[0],
                         label: 'Daily Scans',
                         borderColor: 'rgba(100, 181, 246, 1)', // Professional blue
                         backgroundColor: 'rgba(100, 181, 246, 0.1)',
                         data: sampleActivityData.map(item => item.scan_count || item.count || item.value || 0)
                       }]
                     }} 
                     options={{
                       ...lineChartOptions,
                       scales: {
                         ...lineChartOptions.scales,
                         y: {
                           ...lineChartOptions.scales.y,
                           title: {
                             display: true,
                             text: 'Number of Scans'
                           }
                         }
                       },
                       plugins: {
                         ...lineChartOptions.plugins,
                         tooltip: {
                           backgroundColor: 'rgba(0, 0, 0, 0.8)',
                           titleColor: '#fff',
                           bodyColor: '#fff',
                           borderColor: 'rgba(255, 255, 255, 0.1)',
                           borderWidth: 1,
                           callbacks: {
                             title: function(context) {
                               if (!context || !context[0]) return 'Date';
                               const index = context[0].dataIndex;
                               const item = sampleActivityData[index];
                               return item ? new Date(item.timestamp || item.date).toLocaleDateString() : 'Date';
                             },
                             label: function(context) {
                               if (!context) return ['No data'];
                               const index = context.dataIndex;
                               const item = sampleActivityData[index];
                               const scanCount = item ? (item.scan_count || item.count || 0) : 0;
                               return [
                                 `Scans: ${scanCount}`,
                                 `Date: ${item ? new Date(item.timestamp || item.date).toLocaleDateString() : 'Unknown'}`
                               ];
                             }
                           }
                         }
                       }
                     }} 
                   />
                 );
               })()}
             </ChartCard> */}

             {/* Scan Status Distribution */}
             <ChartCard title="Scan Status Distribution" size="medium">
               {(() => {
                 const recentScans = dashboardData?.dashboardCharts?.recentScans || [];
                 console.log('Scan Status - Recent Scans raw data:', recentScans);
                 
                 // If no real data, use the same sample data as Recent Scans Overview
                 const sampleScans = recentScans.length === 0 ? [
                   { scan_id: 1, store_name: 'Database-01', store_type: 'MySQL', status: 'completed', location: 'Production', findings: 5 },
                   { scan_id: 2, store_name: 'Database-02', store_type: 'PostgreSQL', status: 'completed', location: 'Staging', findings: 3 },
                   { scan_id: 3, store_name: 'Storage-01', store_type: 'S3', status: 'running', location: 'Cloud', findings: 0 },
                   { scan_id: 4, store_name: 'Database-03', store_type: 'MongoDB', status: 'failed', location: 'Development', findings: 0 },
                   { scan_id: 5, store_name: 'Cache-01', store_type: 'Redis', status: 'completed', location: 'Production', findings: 1 },
                   { scan_id: 6, store_name: 'Storage-02', store_type: 'S3', status: 'completed', location: 'Staging', findings: 2 }
                 ] : recentScans;
                 
                 const statusData = sampleScans
                   .filter(scan => scan && (scan.status || scan.scan_status)) // Filter out scans without status
                   .reduce((acc, scan) => {
                     const status = scan.status || scan.scan_status || 'Unknown';
                     const existing = acc.find(item => item.status === status);
                     if (existing) {
                       existing.count += 1;
                     } else {
                       acc.push({ 
                         status: status, 
                         count: 1,
                         type: status, // For formatChartData
                         name: status  // Alternative field name
                       });
                     }
                     return acc;
                   }, []);
                 
                 console.log('Scan Status processed data:', statusData);
                 
                 if (statusData.length === 0) {
                   return (
                     <div className="no-data-message">
                       <Activity size={24} />
                       <p>No scan status data available</p>
                     </div>
                   );
                 }

                 const chartData = formatChartData(statusData, 'pie');
                 console.log('Scan Status chart data:', chartData);

                 return (
                   <Pie 
                     data={chartData} 
                     options={{
                       ...chartOptions,
                       plugins: {
                         ...chartOptions.plugins,
                         tooltip: {
                           backgroundColor: 'rgba(0, 0, 0, 0.8)',
                           titleColor: '#fff',
                           bodyColor: '#fff',
                           borderColor: 'rgba(255, 255, 255, 0.1)',
                           borderWidth: 1,
                           callbacks: {
                             title: function(context) {
                               if (!context || !context[0]) {
                                 return 'Scan Status';
                               }
                               const index = context[0].dataIndex;
                               const status = statusData[index];
                               return status ? status.status : 'Scan Status';
                             },
                             label: function(context) {
                               if (!context) {
                                 return ['No data available'];
                               }
                               const index = context.dataIndex;
                               const status = statusData[index];
                               
                               if (!status) {
                                 return ['No data available'];
                               }
                               
                               const percentage = ((status.count / sampleScans.length) * 100).toFixed(1);
                               return [
                                 `Status: ${status.status}`,
                                 `Count: ${status.count} scans`,
                                 `Percentage: ${percentage}%`
                               ];
                             }
                           }
                         }
                       }
                     }} 
                   />
                 );
               })()}
             </ChartCard>

             {/* Compliance Summary */}
             {/* <ChartCard title="Compliance Overview" size="medium">
               <div className="compliance-summary">
                 <div className="compliance-percentage">
                   <div className="percentage-circle">
                     <span className="percentage-value">
                       {dashboardData?.dashboardCharts?.complianceSummary?.compliance_percentage || 0}%
                     </span>
                     <span className="percentage-label">Compliant</span>
                   </div>
                 </div>
                 <div className="compliance-breakdown">
                   <div className="compliance-item">
                     <span className="policy-name">Overall Status</span>
                     <span className="compliance-rate">
                       {dashboardData?.dashboardCharts?.complianceSummary?.compliance_percentage || 0}%
                     </span>
                   </div>
                 </div>
               </div>
             </ChartCard> */}
           </div>
        </div>
      )}

      {/* Risk Analysis Section */}
      {activeSection === 'risk-analysis' && (
        <div className="risk-analysis-section">
          <div className="section-header">
            <h2>Risk Analysis</h2>
            <p>Comprehensive risk assessment and compliance monitoring</p>
          </div>

          <div className="charts-grid">
            {/* Risk Distribution */}
            <ChartCard title="Risk Level Distribution" size="medium">
              <Doughnut 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.riskDistribution, 'doughnut')} 
                options={chartOptions} 
              />
            </ChartCard>

            {/* Sensitivity Distribution */}
            <ChartCard title="Data Sensitivity Distribution" size="medium">
              <Pie 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.sensitivityDistribution, 'pie')} 
                options={chartOptions} 
              />
            </ChartCard>

            {/* Finding Type Breakdown */}
            <ChartCard title="Finding Type Breakdown" size="medium">
              <Doughnut 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.findingTypeBreakdown, 'doughnut')} 
                options={chartOptions} 
              />
            </ChartCard>

            {/* Detection Methods */}
            <ChartCard title="Detection Methods Used" size="medium">
              <Bar 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.detectionMethods, 'bar')} 
                options={barChartOptions} 
              />
            </ChartCard>

            {/* Confidence Score Distribution */}
            <ChartCard title="Confidence Score Distribution" size="medium">
              <Bar 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.confidenceDistribution, 'bar')} 
                options={barChartOptions} 
              />
            </ChartCard>

            {/* SDE Categories */}
            <ChartCard title="SDE Categories Distribution" size="medium">
              <Bar 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.sdeCategories, 'bar')} 
                options={barChartOptions} 
              />
            </ChartCard>

            {/* Privacy Violations */}
            <ChartCard title="Privacy Violations" size="medium">
              <Bar 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.privacyViolations, 'bar')} 
                options={barChartOptions} 
              />
            </ChartCard>

            {/* Risk Matrix */}
            <ChartCard title="Risk Matrix by Impact" size="medium">
              <Bar 
                data={formatChartData(dashboardData?.riskAnalysisCharts?.riskMatrix, 'bar')} 
                options={barChartOptions} 
              />
            </ChartCard>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComprehensiveDashboard;
