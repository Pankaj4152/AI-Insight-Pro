import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../apiConfig';
import { getRiskAssessmentUser } from '../utils/riskAssessmentUtils';
import '../Css/RiskAssessment.css';
import '../Css/EnhancedRiskAssessment.css';
import '../Css/Dashboard.css';
import '../Css/RiskDashboardTheme.css';
import SkeletonLoader from '../components/common/SkeletonLoader';
import ErrorBoundary from '../components/common/ErrorBoundary';

// Enhanced Components
import RiskOverviewDashboard from '../components/risk-assessment/RiskOverviewDashboard';
import AdvancedRiskFilters from '../components/risk-assessment/AdvancedRiskFilters';
import InteractiveRiskCharts from '../components/risk-assessment/InteractiveRiskCharts';
import EnhancedTopRiskFindings from '../components/risk-assessment/EnhancedTopRiskFindings';
import RiskTrendAnalysis from '../components/risk-assessment/RiskTrendAnalysis';

// Legacy Components (as fallback)
import SummaryCard from '../components/dashboard/SummaryCard';
import RiskDistributionChart from '../components/risk-assessment/RiskDistributionChart';
import SensitivityLevelChart from '../components/risk-assessment/SensitivityLevelChart';
import RiskMatrix from '../components/risk-assessment/RiskMatrix';
import TopRiskFindingsTable from '../components/risk-assessment/TopRiskFindingsTable';
import RecommendationsWidget from '../components/risk-assessment/RecommendationsWidget';

import { 
  DatabaseIcon, 
  ShieldIcon, 
  ActivityIcon, 
  FlameIcon, 
  LockIcon, 
  BarChartIcon,
  RefreshCw,
  Play,
  Download,
  Settings,
  AlertTriangle,
  TrendingUp,
  Eye
} from 'lucide-react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);



function EnhancedRiskAssessmentPage() {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [comprehensiveData, setComprehensiveData] = useState(null);
  const [riskFindings, setRiskFindings] = useState([]);
  const [dataSources, setDataSources] = useState([]);
  const [filteredResults, setFilteredResults] = useState(null);
  const [scanInProgress, setScanInProgress] = useState(false);
  const [lastScanTime, setLastScanTime] = useState(null);
  const [notification, setNotification] = useState(null);

  // Filter state
  const [filters, setFilters] = useState({
    dataSource: '',
    riskLevel: '',
    sensitivity: '',
    findingType: '',
    search: '',
    startDate: '',
    endDate: ''
  });

  // Enhanced data state
  const [chartData, setChartData] = useState({
    riskDistribution: [],
    sensitivityBySource: {},
    sdeCategories: [],
    detectionMethods: [],
    trendAnalysis: [],
    scanActivity: []
  });

  // Refs
  const scanProgressRef = useRef(null);

  // Fetch comprehensive risk assessment data
  const fetchComprehensiveRiskData = async (clientId) => {
    try {
      console.log('Fetching comprehensive risk data for client:', clientId);

      // Fetch all necessary data in parallel
      const [
        comprehensiveResponse,
        dashboardResponse,
        findingsResponse,
        dataSourcesResponse,
        trendResponse,
        riskDistributionResponse
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/risk/comprehensive-risk-assessment/${clientId}`),
        fetch(`${API_BASE_URL}/risk/comprehensive-dashboard/${clientId}`),
        fetch(`${API_BASE_URL}/risk/top-findings/${clientId}?limit=10`),
        fetch(`${API_BASE_URL}/risk/data-sources/${clientId}`),
        fetch(`${API_BASE_URL}/risk/trend-analysis/${clientId}?days=30`),
        fetch(`${API_BASE_URL}/risk/risk-level-distribution/${clientId}`)
      ]);

      if (!comprehensiveResponse.ok) {
        throw new Error('Failed to fetch comprehensive risk assessment');
      }

      const comprehensiveData = await comprehensiveResponse.json();
      console.log('Comprehensive risk data:', comprehensiveData);

      // Parse dashboard data
      let dashboardData = {};
      if (dashboardResponse.ok) {
        dashboardData = await dashboardResponse.json();
        console.log('Dashboard data:', dashboardData);
      }

      // Parse findings data
      let findingsData = [];
      if (findingsResponse.ok) {
        const findingsResult = await findingsResponse.json();
        findingsData = findingsResult.findings || [];
        console.log('Findings data:', findingsData);
      }

      // Parse data sources
      let sourcesData = [];
      if (dataSourcesResponse.ok) {
        const sourcesResult = await dataSourcesResponse.json();
        sourcesData = sourcesResult.data_sources || [];
        console.log('Data sources:', sourcesData);
      }

      // Parse trend data
      let trendData = [];
      if (trendResponse.ok) {
        const trendResult = await trendResponse.json();
        trendData = trendResult.trend_analysis || [];
        console.log('Trend data:', trendData);
      }

      // Parse risk distribution data
      let riskDistributionData = [];
      if (riskDistributionResponse.ok) {
        const riskDistributionResult = await riskDistributionResponse.json();
        riskDistributionData = riskDistributionResult.risk_distribution || [];
        console.log('Risk distribution data:', riskDistributionData);
      }

      // Combine all data
      const metrics = {
        total_data_sources: comprehensiveData.total_data_sources || dashboardData.total_data_sources || 0,
        total_sdes: comprehensiveData.total_sdes || dashboardData.total_sdes || 0,
        scanned_sdes: comprehensiveData.scanned_sdes || dashboardData.scanned_sdes || 0,
        high_risk_sdes: comprehensiveData.high_risk_sdes || dashboardData.high_risk_sdes || 0,
        total_sensitive_records: comprehensiveData.total_sensitive_records || dashboardData.total_sensitive_records || 0,
        total_scans: comprehensiveData.total_scans || dashboardData.total_scans || 0,
        risk_score: comprehensiveData.risk_score || dashboardData.risk_score || 0,
        confidence_score: comprehensiveData.confidence_score || dashboardData.confidence_score || 0,
        last_scan_time: comprehensiveData.last_scan_time || dashboardData.last_scan_time || null,
        llm_summary: comprehensiveData.llm_summary || dashboardData.llm_summary || 'No summary available'
      };

      setRiskMetrics(metrics);
      setComprehensiveData(comprehensiveData);
      setRiskFindings(findingsData);
      setDataSources(sourcesData);

      // Update chart data - using direct risk distribution API response
      console.log('Setting chart data with risk distribution:', riskDistributionData);
      setChartData({
        riskDistribution: riskDistributionData,
        sensitivityBySource: comprehensiveData.sensitivity_by_source || {},
        sdeCategories: comprehensiveData.sde_categories || [],
        detectionMethods: comprehensiveData.detection_methods || [],
        trendAnalysis: trendData,
        scanActivity: comprehensiveData.scan_timeline || []
      });

      setLastScanTime(new Date().toISOString());
      return metrics;

    } catch (error) {
      console.error('Error fetching comprehensive risk data:', error);
      throw error;
    }
  };

  // Trigger risk assessment scan
  const triggerRiskAssessment = async (clientId) => {
    try {
      console.log('Triggering risk assessment for client:', clientId);
      const response = await fetch(`${API_BASE_URL}/risk/risk-assessment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Risk assessment triggered successfully:', result);
        return result;
      } else {
        throw new Error('Failed to trigger risk assessment');
      }
    } catch (error) {
      console.error('Error triggering risk assessment:', error);
      throw error;
    }
  };

  // Apply filters
  const applyFilters = async () => {
    if (!riskMetrics) return;

    try {
      setLoading(true);
      const user = getRiskAssessmentUser();
      
      const params = new URLSearchParams({
        client_id: user.client_id,
        ...(filters.dataSource && { data_source: filters.dataSource }),
        ...(filters.riskLevel && { risk_level: filters.riskLevel }),
        ...(filters.sensitivity && { sensitivity: filters.sensitivity }),
      });

      const response = await fetch(`${API_BASE_URL}/risk/filtered-findings/?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch filtered results');
      }

      const data = await response.json();
      console.log('Filtered results:', data);
      
      setFilteredResults(data);
      
      // Update chart data with filtered results
      const filteredChartData = {
        ...chartData,
        riskDistribution: [
          { level: 'LOW', count: data.filtered_findings?.filter(finding => finding.risk_level === 'Low').length || 0 },
          { level: 'MEDIUM', count: data.filtered_findings?.filter(finding => finding.risk_level === 'Medium').length || 0 },
          { level: 'HIGH', count: data.filtered_findings?.filter(finding => finding.risk_level === 'High').length || 0 }
        ]
      };
      setChartData(filteredChartData);

      showNotification('Filters applied successfully', 'success');
    } catch (error) {
      console.error('Error applying filters:', error);
      showNotification('Failed to apply filters', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({
      dataSource: '',
      riskLevel: '',
      sensitivity: '',
      findingType: '',
      search: '',
      startDate: '',
      endDate: ''
    });
    setFilteredResults(null);
    
    // Reset chart data to original
    if (comprehensiveData) {
      setChartData({
        riskDistribution: comprehensiveData.risk_distribution || [],
        sensitivityBySource: comprehensiveData.sensitivity_by_source || {},
        sdeCategories: comprehensiveData.sde_categories || [],
        detectionMethods: comprehensiveData.detection_methods || [],
        trendAnalysis: chartData.trendAnalysis,
        scanActivity: comprehensiveData.scan_timeline || []
      });
    }
    
    showNotification('Filters cleared', 'info');
  };

  // Start scan
  const startScan = async () => {
    try {
      setScanInProgress(true);
      setLoading(true);
      setError(null);
      
      const user = getRiskAssessmentUser();
      console.log('Starting scan for user:', user);

      // Simulate scan progress
      scanProgressRef.current = { progress: 0 };
      
      // Step 1: Trigger risk assessment
      showNotification('Initializing scan...', 'info');
      await triggerRiskAssessment(user.client_id);
      scanProgressRef.current.progress = 25;

      // Step 2: Wait for processing
      showNotification('Analyzing data sources...', 'info');
      await new Promise(resolve => setTimeout(resolve, 2000));
      scanProgressRef.current.progress = 50;

      // Step 3: Fetch comprehensive data
      showNotification('Generating risk assessment...', 'info');
      await fetchComprehensiveRiskData(user.client_id);
      scanProgressRef.current.progress = 75;

      // Step 4: Complete
      showNotification('Finalizing results...', 'info');
      await new Promise(resolve => setTimeout(resolve, 1000));
      scanProgressRef.current.progress = 100;

      showNotification('Risk assessment completed successfully!', 'success');
      
    } catch (error) {
      console.error('Error during scan:', error);
      setError(error.message || 'Failed to complete risk assessment');
      showNotification('Scan failed: ' + (error.message || 'Unknown error'), 'error');
    } finally {
      setScanInProgress(false);
      setLoading(false);
    }
  };

  // Filter change handler
  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  // Show notification
  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Initial load
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        const user = getRiskAssessmentUser();
        await fetchComprehensiveRiskData(user.client_id);
      } catch (error) {
        console.error('Error loading initial data:', error);
        setError(error.message || 'Failed to load risk assessment data');
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // Error state
  if (error && !riskMetrics) {
    return (
      <div className="risk-assessment-container">
        <div className="error-state">
          <AlertTriangle className="error-icon" />
          <h2>Unable to Load Risk Assessment</h2>
          <p>{error}</p>
          <button className="retry-button" onClick={() => window.location.reload()}>
            <RefreshCw className="button-icon" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="risk-assessment-container">
      {/* Header */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">Risk Assessment Dashboard</h1>
          <p className="page-subtitle">
            Comprehensive analysis of sensitive data risks across your organization
          </p>
        </div>
        <div className="header-actions">
          <button
            className="action-button primary"
            onClick={startScan}
            disabled={scanInProgress || loading}
          >
            {scanInProgress ? (
              <>
                <RefreshCw className="button-icon spinning" />
                Scanning...
              </>
            ) : (
              <>
                <Play className="button-icon" />
                Start Scan
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)}>×</button>
        </div>
      )}

      {/* Main Content */}
      <div className="main-content">
        <ErrorBoundary>
          {/* Risk Overview Dashboard */}
          <RiskOverviewDashboard 
            metrics={riskMetrics} 
            loading={loading}
          />
        </ErrorBoundary>

        <ErrorBoundary>
          {/* Advanced Filters */}
          <AdvancedRiskFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onApplyFilters={applyFilters}
            onClearFilters={clearFilters}
            loading={loading}
            dataSources={dataSources}
          />
        </ErrorBoundary>

        {/* Results Summary */}
        {filteredResults && (
          <div className="results-summary">
            <h3>Filter Results</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Total SDEs:</span>
                <span className="summary-value">{filteredResults.summary?.total_sdes || 0}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Total Findings:</span>
                <span className="summary-value">{filteredResults.summary?.total_findings || 0}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">High Risk:</span>
                <span className="summary-value critical">{filteredResults.summary?.high_risk_findings || 0}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">High Sensitivity:</span>
                <span className="summary-value warning">{filteredResults.summary?.high_sensitivity_findings || 0}</span>
              </div>
            </div>
          </div>
        )}

        <ErrorBoundary>
          {/* Interactive Charts */}
          <InteractiveRiskCharts 
            data={chartData}
            loading={loading}
          />
        </ErrorBoundary>

        <ErrorBoundary>
          {/* Risk Trend Analysis */}
          <RiskTrendAnalysis 
            clientId={getRiskAssessmentUser()?.client_id}
            timeRange={filters.timeRange || '30'}
            onTimeRangeChange={(newTimeRange) => {
              setFilters(prev => ({ ...prev, timeRange: newTimeRange }));
            }}
          />
        </ErrorBoundary>

        <ErrorBoundary>
          {/* Enhanced Risk Findings */}
          <EnhancedTopRiskFindings 
            findings={riskFindings}
            loading={loading}
          />
        </ErrorBoundary>

        {/* Legacy Fallback Components */}
        {(!riskMetrics || loading) && (
          <div className="legacy-fallback">
            <ErrorBoundary>
              <section className="risk-overview-header">
                {loading ? (
                  <SkeletonLoader type="card" count={7} />
                ) : riskMetrics && (
                  [
                    { title: 'Total Data Sources', value: riskMetrics.total_data_sources || 0, icon: <DatabaseIcon className='lucide-icon' /> },
                    { title: 'Total SDEs', value: riskMetrics.total_sdes || 0, icon: <ShieldIcon className='lucide-icon' /> },
                    { title: 'Scanned SDEs', value: riskMetrics.scanned_sdes || 0, icon: <ActivityIcon className='lucide-icon' /> },
                    { title: 'High-Risk SDEs', value: riskMetrics.high_risk_sdes || 0, icon: <FlameIcon className='lucide-icon' /> },
                    { title: 'Total Sensitive Records', value: riskMetrics.total_sensitive_records || 0, icon: <LockIcon className='lucide-icon' /> },
                    { title: 'Risk Score', value: `${Math.round(riskMetrics.risk_score || 0)}/100`, icon: <BarChartIcon className='lucide-icon' /> },
                    { title: 'Confidence Score', value: `${Math.round(riskMetrics.confidence_score || 0)}/100`, icon: <BarChartIcon className='lucide-icon' /> },
                  ].map((kpi, index) => (
                    <SummaryCard key={index} title={kpi.title} value={kpi.value} icon={kpi.icon} />
                  ))
                )}
              </section>
            </ErrorBoundary>

            <ErrorBoundary>
              {loading || !chartData ? (
                <SkeletonLoader type="widget" />
              ) : (
                <RiskDistributionChart data={chartData.riskDistribution} />
              )}
            </ErrorBoundary>

            <ErrorBoundary>
              {loading || !riskFindings ? (
                <SkeletonLoader type="table" />
              ) : (
                <TopRiskFindingsTable findings={riskFindings} />
              )}
            </ErrorBoundary>
          </div>
        )}
      </div>
    </div>
  );
}

export default EnhancedRiskAssessmentPage;
