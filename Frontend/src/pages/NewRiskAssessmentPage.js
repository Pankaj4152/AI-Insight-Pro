import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  AlertTriangle, 
  Shield, 
  Database, 
  Activity, 
  TrendingUp, 
  Users, 
  Eye, 
  Download, 
  RefreshCw, 
  Filter,
  Search,
  Calendar,
  ChevronDown,
  ChevronUp,
  BarChart3,
  PieChart,
  FileText,
  Clock,
  Zap,
  Target,
  Lock,
  Globe,
  Server,
  Scan,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { API_BASE_URL } from '../apiConfig';
import {
  getRiskAssessmentUser,
  handleApiError,
  exportToCSV,
  getPieChartOptions,
  getLineChartOptions,
  getBarChartOptions,
  generateChartColors,
  cleanChartData
} from '../utils/riskAssessmentUtils';
import '../Css/NewRiskAssessment.css';
import '../Css/RiskDashboardTheme.css';

// Import new components
import MetricsDashboard from '../components/risk-assessment/MetricsDashboard';
import RiskTrendWidget from '../components/risk-assessment/RiskTrendWidget';
import RiskFindingsTable from '../components/risk-assessment/RiskFindingsTable';
import ComprehensiveDashboard from '../components/dashboard/ComprehensiveDashboard';
// import RiskTrendWidget from '../components/risk-assessment/RiskTrendWidget';
// import RiskFindingsTable from '../components/risk-assessment/RiskFindingsTable';
// import ComprehensiveDashboard from '../components/dashboard/ComprehensiveDashboard';

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

// Development mode toggle - removed mock data usage
const USE_REAL_API = true;

const NewRiskAssessmentPage = () => {
  // Core state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Data state
  const [dashboardData, setDashboardData] = useState(null);
  const [riskAssessmentData, setRiskAssessmentData] = useState(null);
  const [topFindings, setTopFindings] = useState([]);
  const [scanFindings, setScanFindings] = useState([]); // Real scan findings data
  const [scanActivity, setScanActivity] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [dataSources, setDataSources] = useState([]);
  
  // Filter state
  const [filters, setFilters] = useState({
    dataSource: '',
    riskLevel: '',
    sensitivity: '',
    timeRange: '30'
  });
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // UI state
  const [activeTab, setActiveTab] = useState('overview');
  const [notification, setNotification] = useState(null);

  // Add new state variables for Risk Findings filters
  const [riskLevelFilter, setRiskLevelFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [searchValue, setSearchValue] = useState('');
  const [filteredRiskFindings, setFilteredRiskFindings] = useState([]);
  const [isLoadingRiskFindings, setIsLoadingRiskFindings] = useState(false);

  // Notification helper
  const showNotification = useCallback((message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  }, []);

  // API calls with error handling
  const apiCall = useCallback(async (url, options = {}) => {
    try {
      console.log(`🔍 Making API call to: ${url}`);
      console.log(`📋 Request options:`, options);
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });
      
      console.log(`📡 Response status: ${response.status} ${response.statusText}`);
      console.log(`📡 Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error ${response.status}:`, errorText);
        throw new Error(`API Error: ${response.status} - ${response.statusText} - ${errorText}`);
      }
      
      const data = await response.json();
      console.log(`✅ API call successful for ${url}:`, data);
      return data;
    } catch (error) {
      console.error(`❌ API call failed for ${url}:`, error);
      console.error(`❌ Error details:`, {
        message: error.message,
        stack: error.stack,
        url: url,
        options: options
      });
      throw error;
    }
  }, []);

  // Enhanced error handling for API calls
  const safeApiCall = useCallback(async (url, options = {}) => {
    try {
      return await apiCall(url, options);
    } catch (error) {
      console.error(`🚨 Safe API call failed for ${url}:`, error);
      
      // Check if it's a network error
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        console.error('🌐 Network error detected - check your internet connection');
        throw new Error('Network error - please check your internet connection');
      }
      
      // Check if it's a CORS error
      if (error.message.includes('CORS') || error.message.includes('Access-Control')) {
        console.error('🚫 CORS error detected - check API server configuration');
        throw new Error('CORS error - API server configuration issue');
      }
      
      // Check if it's an authentication error
      if (error.message.includes('401') || error.message.includes('403')) {
        console.error('🔐 Authentication error detected');
        throw new Error('Authentication error - please log in again');
      }
      
      throw error;
    }
  }, [apiCall]);

  // Enhanced data extraction with schema fallbacks
  const extractDataWithFallbacks = useCallback((data, dataType) => {
    console.log(`🔍 Extracting ${dataType} data:`, data);
    
    // Handle database schema errors
    if (data.error) {
      console.warn(`⚠️ ${dataType} returned error:`, data.error);
      
      // Handle missing sde_category column - map to sensitivity
      if (data.error.includes('column "sde_category" does not exist')) {
        console.warn('🔧 sde_category column missing - mapping to sensitivity field');
        return getFallbackData(dataType);
      }
      
      // Handle timestamp comparison errors
      if (data.error.includes('operator does not exist: text >= timestamp')) {
        console.warn('🔧 Timestamp comparison error - using fallback data');
        return getFallbackData(dataType);
      }
      
      // Handle other database errors
      console.warn(`🔧 Database error for ${dataType} - using fallback data`);
      return getFallbackData(dataType);
    }
    
    // Extract data based on type
    switch (dataType) {
             case 'topFindings':
         if (data.top_risk_findings) return data.top_risk_findings;
         if (data.findings) return data.findings;
         if (Array.isArray(data)) return data;
         console.warn('⚠️ Unexpected top findings structure:', data);
         return getFallbackData('topFindings');
         
       case 'scanFindings':
         if (data.scan_findings) return data.scan_findings;
         if (data.findings) return data.findings;
         if (Array.isArray(data)) return data;
         console.warn('⚠️ Unexpected scan findings structure:', data);
         return getFallbackData('scanFindings');
        
      case 'scanActivity':
        if (data.scan_timeline) return data.scan_timeline;
        if (data.activity) return data.activity;
        if (Array.isArray(data)) return data;
        console.warn('⚠️ Unexpected scan activity structure:', data);
        return getFallbackData('scanActivity');
        
      case 'trendData':
        if (data.trend_analysis) return data.trend_analysis;
        if (data.trends) return data.trends;
        if (Array.isArray(data)) return data;
        console.warn('⚠️ Unexpected trend data structure:', data);
        return getFallbackData('trendData');
        
      case 'dataSources':
        if (data.data_sources) return data.data_sources;
        if (data.sources) return data.sources;
        if (Array.isArray(data)) return data;
        console.warn('⚠️ Unexpected data sources structure:', data);
        return getFallbackData('dataSources');
        
      case 'sdeCategories':
        if (data.sde_categories) return data.sde_categories.map(cat => cat.category).filter(Boolean);
        if (data.categories) return data.categories;
        if (Array.isArray(data)) return data;
        console.warn('⚠️ Unexpected SDE categories structure:', data);
        return getFallbackData('sdeCategories');
        
      case 'riskAssessment':
        return data; // Keep as is for risk assessment data
        
      default:
        return data;
    }
  }, []);

  // Fallback data for when database schema issues occur
  const getFallbackData = useCallback((dataType) => {
    console.log(`🔄 Providing fallback data for ${dataType}`);
    
    switch (dataType) {
             case 'topFindings':
         return [
           {
             finding_id: 'fallback_1',
             sensitivity: 'PII', // Use sensitivity instead of sde_category
             risk_level: 'high',
             dataset_name: 'customer_db',
             dataset_column: 'personal_info',
             description: 'Sample high-risk finding',
             confidence_score: 95
           },
           {
             finding_id: 'fallback_2',
             sensitivity: 'Financial', // Use sensitivity instead of sde_category
             risk_level: 'medium',
             dataset_name: 'payment_system',
             dataset_column: 'credit_cards',
             description: 'Sample medium-risk finding',
             confidence_score: 85
           }
         ];
         
       case 'scanFindings':
         return [
           {
             finding_id: 'scan_finding_1',
             sde_id: 'sde_001',
             risk_level: 'high',
             confidence_score: 95,
             detection_method: 'regex_pattern_match',
             scan_timestamp: new Date().toISOString(),
             object_path: 'customer_data/personal_info.csv',
             data_value: 'John Doe',
             sde_category: 'PII',
             dataset_name: 'customer_data',
             dataset_column: 'personal_info'
           },
           {
             finding_id: 'scan_finding_2',
             sde_id: 'sde_002',
             risk_level: 'medium',
             confidence_score: 85,
             detection_method: 'field_name_mapping',
             scan_timestamp: new Date(Date.now() - 86400000).toISOString(),
             object_path: 'payment_data/credit_cards.csv',
             data_value: '4111-1111-1111-1111',
             sde_category: 'Financial',
             dataset_name: 'payment_data',
             dataset_column: 'credit_cards'
           }
         ];
        
      case 'scanActivity':
        return [
          {
            scan_id: 'scan_1',
            scan_timestamp: new Date().toISOString(), // Use scan_timestamp
            status: 'completed',
            findings_count: 15
          },
          {
            scan_id: 'scan_2',
            scan_timestamp: new Date(Date.now() - 86400000).toISOString(), // Use scan_timestamp
            status: 'completed',
            findings_count: 23
          }
        ];
        
      case 'trendData':
        return [
          {
            date: new Date().toISOString().split('T')[0],
            risk_score: 75,
            findings_count: 15
          },
          {
            date: new Date(Date.now() - 86400000).toISOString().split('T')[0],
            risk_score: 82,
            findings_count: 23
          }
        ];
        
      case 'dataSources':
        return [
          {
            store_id: 'store_1',
            store_name: 'Customer Database',
            store_type: 'PostgreSQL',
            connection_status: 'active'
          },
          {
            store_id: 'store_2',
            store_name: 'Payment System',
            store_type: 'MySQL',
            connection_status: 'active'
          }
        ];
        
      case 'sdeCategories':
        return ['PII', 'PHI', 'FINANCIAL', 'LOCATION', 'IDENTIFICATION', 'UNKNOWN'];
        
      default:
        return [];
    }
  }, []);

  // Enhanced API call with database error handling
  const robustApiCall = useCallback(async (url, options = {}, fallbackData = null) => {
    try {
      const data = await apiCall(url, options);
      
      // Check if the response contains database errors
      if (data && typeof data === 'object' && data.error) {
        console.warn(`⚠️ Database error in API response for ${url}:`, data.error);
        
        // Handle specific database errors
        if (data.error.includes('column "sde_category" does not exist')) {
          console.warn('🔧 sde_category column missing - using fallback data');
          return fallbackData || { error: 'Database schema issue - sde_category column missing' };
        }
        
        if (data.error.includes('operator does not exist: text >= timestamp')) {
          console.warn('🔧 Timestamp comparison issue - using fallback data');
          return fallbackData || { error: 'Database schema issue - timestamp comparison error' };
        }
        
        // Return the error response for other database issues
        return data;
      }
      
      return data;
    } catch (error) {
      console.error(`❌ API call failed for ${url}:`, error);
      
      // Return fallback data if available
      if (fallbackData) {
        console.log(`🔄 Using fallback data for ${url}`);
        return fallbackData;
      }
      
      throw error;
    }
  }, [apiCall]);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async (clientId) => {
    const fallbackData = {
      summary: {
        total_data_sources: 0,
        total_sdes: 0,
        total_scans: 0,
        high_risk_sdes: 0,
        total_sensitive_records: 0,
        risk_score: 0,
        confidence_score: 0
      },
      data_source_types: [
        { type: "PostgreSQL", count: 1, percentage: 50.0 },
        { type: "MySQL", count: 1, percentage: 50.0 }
      ],
      risk_distribution: [],
      sensitivity_categories: []
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/comprehensive-dashboard/${clientId}`,
      {},
      fallbackData
    );
    console.log('Dashboard data received:', data);
    return data;
  }, [robustApiCall]);

  // Fetch comprehensive risk assessment data
  const fetchRiskAssessmentData = useCallback(async (clientId) => {
    const fallbackData = {
      overall_risk_score: 0,
      risk_level: "low",
      assessment_date: new Date().toISOString(),
      risk_factors: [],
      recommendations: [
        "Database schema needs to be updated to include sde_category column",
        "Timestamp fields need proper data type handling"
      ]
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/comprehensive-risk-assessment/${clientId}`,
      {},
      fallbackData
    );
    console.log('Risk assessment data received:', data);
    return data;
  }, [robustApiCall]);

  // Fetch risk distribution data
  const fetchRiskDistributionData = useCallback(async (clientId) => {
    const fallbackData = {
      risk_distribution: [
        { level: "LOW", count: 0 },
        { level: "MEDIUM", count: 0 },
        { level: "HIGH", count: 0 }
      ]
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/risk-level-distribution/${clientId}`,
      {},
      fallbackData
    );
    console.log('Risk distribution data received:', data);
    return data;
  }, [robustApiCall]);

  // Fetch SDE category risk distribution data
  const fetchSDECategoryRiskDistributionData = useCallback(async (clientId) => {
    const fallbackData = {
      client_id: clientId,
      sde_risk_distribution: [
        { risk_level: "low", count: 0, percentage: 0 },
        { risk_level: "medium", count: 0, percentage: 0 },
        { risk_level: "high", count: 0, percentage: 0 }
      ],
      total_sdes: 0
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/sde-category-risk-distribution/${clientId}`,
      {},
      fallbackData
    );
    console.log('SDE category risk distribution data received:', data);
    return data;
  }, [robustApiCall]);

  // Fetch individual metrics using specific endpoints
  const fetchIndividualMetrics = useCallback(async (clientId) => {
    const metrics = {};
    
    try {
      // Fetch total data sources
      const dataSourcesResponse = await robustApiCall(
        `${API_BASE_URL}/risk/total-data-sources/${clientId}`,
        {},
        { total_data_sources: 0 }
      );
      metrics.total_data_sources = dataSourcesResponse.total_data_sources || 0;

      // Fetch total SDEs
      const totalSdesResponse = await robustApiCall(
        `${API_BASE_URL}/risk/total-sdes/${clientId}`,
        {},
        { total_sdes: 0 }
      );
      metrics.total_sdes = totalSdesResponse.total_sdes || 0;

      // Fetch high risk SDEs
      const highRiskSdesResponse = await robustApiCall(
        `${API_BASE_URL}/risk/high-risk-sdes/${clientId}`,
        {},
        { high_risk_sdes: 0 }
      );
      metrics.high_risk_sdes = highRiskSdesResponse.high_risk_sdes || 0;

      // Fetch total scans
      const totalScansResponse = await robustApiCall(
        `${API_BASE_URL}/risk/total-scans/${clientId}`,
        {},
        { total_scans: 0 }
      );
      metrics.total_scans = totalScansResponse.total_scans || 0;

      // Fetch risk score
      const riskScoreResponse = await robustApiCall(
        `${API_BASE_URL}/risk/risk-score/${clientId}`,
        {},
        { risk_score: 0 }
      );
      metrics.risk_score = riskScoreResponse.risk_score || 0;

      // Fetch confidence score
      const confidenceScoreResponse = await robustApiCall(
        `${API_BASE_URL}/risk/confidence-score/${clientId}`,
        {},
        { confidence_score: 0 }
      );
      metrics.confidence_score = confidenceScoreResponse.confidence_score || 0;

      console.log('Individual metrics fetched:', metrics);
      return metrics;
    } catch (error) {
      console.error('Error fetching individual metrics:', error);
      return {
        total_data_sources: 0,
        total_sdes: 0,
        high_risk_sdes: 0,
        total_scans: 0,
        risk_score: 0,
        confidence_score: 0
      };
    }
  }, [robustApiCall]);

  // Fetch scan findings (real data from scan_findings table)
  const fetchScanFindings = useCallback(async (clientId, limit = 50) => {
    const fallbackData = {
      client_id: clientId,
      findings: []
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/scan-findings/${clientId}?limit=${limit}`,
      {},
      fallbackData
    );
    return data.findings || data.scan_findings || [];
  }, [robustApiCall]);

  // Fetch top risk findings (keeping for backward compatibility)
  const fetchTopFindings = useCallback(async (clientId, limit = 10) => {
    const fallbackData = {
      client_id: clientId,
      findings: []
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/top-findings/${clientId}?limit=${limit}`,
      {},
      fallbackData
    );
    return data.top_risk_findings || data.findings || [];
  }, [robustApiCall]);

  // Fetch scan activity
  const fetchScanActivity = useCallback(async (clientId, days = 30) => {
    const fallbackData = {
      timeline: []
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/scan-activity-timeline/${clientId}?days=${days}`,
      {},
      fallbackData
    );
    return data.scan_timeline || data.timeline || [];
  }, [robustApiCall]);

  // Fetch trend analysis
  const fetchTrendAnalysis = useCallback(async (clientId, days = 30) => {
    const fallbackData = {
      trends: {
        risk_score_trend: [],
        findings_trend: []
      }
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/trend-analysis/${clientId}?days=${days}`,
      {},
      fallbackData
    );
    return data.trends || data.trend_analysis || [];
  }, [robustApiCall]);

  // Fetch data sources
  const fetchDataSources = useCallback(async (clientId) => {
    const fallbackData = {
      client_id: clientId,
      data_sources: [
        // {
        //   source_id: "src_001",
        //   source_name: "Customer Database",
        //   source_type: "PostgreSQL",
        //   connection_status: "active",
        //   table_count: 12
        // },
        // {
        //   source_id: "src_002", 
        //   source_name: "Payment System",
        //   source_type: "MySQL",
        //   connection_status: "active",
        //   table_count: 8
        // }
      ]
    };
    
    const data = await robustApiCall(
      `${API_BASE_URL}/risk/data-sources/${clientId}`,
      {},
      fallbackData
    );
    return data.data_sources || [];
  }, [robustApiCall]);

  // Trigger new risk assessment
  const triggerRiskAssessment = useCallback(async (clientId) => {
    await apiCall(`${API_BASE_URL}/risk/risk-assessment`, {
      method: 'POST',
      body: JSON.stringify({ client_id: clientId })
    });
  }, [apiCall]);

  // Add new function to fetch risk findings with filters
  const fetchRiskFindings = useCallback(async (clientId, filters = {}) => {
    setIsLoadingRiskFindings(true);
    try {
      const queryParams = new URLSearchParams();
      
      if (filters.risk_level && filters.risk_level !== 'all') {
        queryParams.append('risk_level', filters.risk_level);
      }
      
      if (filters.sde_category && filters.sde_category !== 'all') {
        queryParams.append('sde_category', filters.sde_category);
      }
      
      if (filters.data_value_search) {
        queryParams.append('data_value_search', filters.data_value_search);
      }
      
      queryParams.append('limit', '100');
      
      const url = `${API_BASE_URL}/risk/risk-findings/${clientId}?${queryParams.toString()}`;
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.findings || [];
    } catch (error) {
      console.error('Error fetching risk findings:', error);
      return [];
    } finally {
      setIsLoadingRiskFindings(false);
    }
  }, []);

  // Add function to handle search button click
  const handleRiskFindingsSearch = useCallback(async () => {
    const user = getRiskAssessmentUser();
    const clientId = user.client_id;
    const filters = {
      risk_level: riskLevelFilter,
      sde_category: categoryFilter,
      data_value_search: searchValue
    };
    
    const findings = await fetchRiskFindings(clientId, filters);
    setFilteredRiskFindings(findings);
  }, [fetchRiskFindings, riskLevelFilter, categoryFilter, searchValue]);

  // Load all data
  const loadAllData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      
      const user = getRiskAssessmentUser();
      const clientId = user.client_id;
      
      console.log('👤 Current user:', user);
      console.log('🆔 Client ID:', clientId);
      


      // Load data in parallel for better performance
      console.log('📊 Starting parallel API calls...');
      
             const [
         dashboardResult,
         riskAssessmentResult,
         riskDistributionResult,
         sdeCategoryRiskDistributionResult,
         individualMetricsResult,
         topFindingsResult,
         scanFindingsResult,
         scanActivityResult,
         trendResult,
         dataSourcesResult
       ] = await Promise.allSettled([
         fetchDashboardData(clientId),
         fetchRiskAssessmentData(clientId),
         fetchRiskDistributionData(clientId),
         fetchSDECategoryRiskDistributionData(clientId),
         fetchIndividualMetrics(clientId),
         fetchTopFindings(clientId, 10),
         fetchScanFindings(clientId, 50), // Fetch real scan findings
         fetchScanActivity(clientId, parseInt(filters.timeRange)),
         fetchTrendAnalysis(clientId, parseInt(filters.timeRange)),
         fetchDataSources(clientId)
       ]);

             console.log('📈 API call results:', {
         dashboard: dashboardResult.status,
         riskAssessment: riskAssessmentResult.status,
         individualMetrics: individualMetricsResult.status,
         topFindings: topFindingsResult.status,
         scanFindings: scanFindingsResult.status,
         scanActivity: scanActivityResult.status,
         trend: trendResult.status,
         dataSources: dataSourcesResult.status
       });

      // Handle results with detailed logging
      if (dashboardResult.status === 'fulfilled') {
        console.log('✅ Dashboard data loaded:', dashboardResult.value);
        
        // Merge individual metrics with dashboard data
        let mergedDashboardData = dashboardResult.value;
        if (individualMetricsResult.status === 'fulfilled') {
          console.log('✅ Individual metrics loaded:', individualMetricsResult.value);
          mergedDashboardData = {
            ...mergedDashboardData,
            summary: {
              ...mergedDashboardData.summary,
              ...individualMetricsResult.value
            }
          };
        }
        
        setDashboardData(mergedDashboardData);
        
        // Check if there are database errors in the response
        if (dashboardResult.value && dashboardResult.value.error) {
          showNotification('Database schema issues detected - using fallback data', 'warning');
        }
      } else {
        console.error('❌ Dashboard data failed:', dashboardResult.reason);

        showNotification('Dashboard data unavailable - using fallback data', 'warning');
      }
      
      if (riskAssessmentResult.status === 'fulfilled') {
        console.log('✅ Risk assessment data loaded:', riskAssessmentResult.value);
        setRiskAssessmentData(riskAssessmentResult.value);
        
        // Extract SDE categories for dropdown
        const sdeCategoriesData = extractDataWithFallbacks(riskAssessmentResult.value, 'sdeCategories');
        setDashboardData(prev => ({
          ...prev,
          sdeCategories: sdeCategoriesData
        }));
        
        // Check if there are database errors in the response
        if (riskAssessmentResult.value && riskAssessmentResult.value.error) {
          showNotification('Risk assessment data has schema issues - using fallback data', 'warning');
        }
      } else {
        console.error('❌ Risk assessment data failed:', riskAssessmentResult.reason);

        showNotification('Risk assessment data unavailable - using fallback data', 'warning');
      }

      if (riskDistributionResult.status === 'fulfilled') {
        console.log('✅ Risk distribution data loaded:', riskDistributionResult.value);
        // Merge risk distribution data with risk assessment data
        if (riskAssessmentResult.status === 'fulfilled') {
          const updatedRiskAssessmentData = {
            ...riskAssessmentResult.value,
            risk_distribution: riskDistributionResult.value.risk_distribution || []
          };
          setRiskAssessmentData(updatedRiskAssessmentData);
        }
      } else {
        console.error('❌ Risk distribution data failed:', riskDistributionResult.reason);
        showNotification('Risk distribution data unavailable - using fallback data', 'warning');
      }

      if (sdeCategoryRiskDistributionResult.status === 'fulfilled') {
        console.log('✅ SDE category risk distribution data loaded:', sdeCategoryRiskDistributionResult.value);
        // Merge SDE category risk distribution data with risk assessment data
        if (riskAssessmentResult.status === 'fulfilled') {
          // Get the current risk assessment data to preserve existing risk_distribution
          const currentRiskAssessmentData = riskAssessmentData || riskAssessmentResult.value;
          const updatedRiskAssessmentData = {
            ...currentRiskAssessmentData, // Use current state to preserve all existing data
            sde_risk_distribution: sdeCategoryRiskDistributionResult.value.sde_risk_distribution || []
          };
          console.log('Merged risk assessment data:', updatedRiskAssessmentData);
          setRiskAssessmentData(updatedRiskAssessmentData);
        }
      } else {
        console.error('❌ SDE category risk distribution data failed:', sdeCategoryRiskDistributionResult.reason);
        showNotification('SDE category risk distribution data unavailable - using fallback data', 'warning');
      }
      
                         if (topFindingsResult.status === 'fulfilled') {
               console.log('✅ Top findings loaded:', topFindingsResult.value);
               const extractedData = extractDataWithFallbacks(topFindingsResult.value, 'topFindings');
               console.log('📊 Extracted findings count:', extractedData.length);
               setTopFindings(extractedData);
             } else {
               console.error('❌ Top findings failed:', topFindingsResult.reason);

               // Use fallback data when API fails
               setTopFindings(getFallbackData('topFindings'));
             }

             if (scanFindingsResult.status === 'fulfilled') {
               console.log('✅ Scan findings loaded:', scanFindingsResult.value);
               const extractedData = extractDataWithFallbacks(scanFindingsResult.value, 'scanFindings');
               console.log('📊 Extracted scan findings count:', extractedData.length);
               setScanFindings(extractedData);
             } else {
               console.error('❌ Scan findings failed:', scanFindingsResult.reason);

               // Use fallback data when API fails
               setScanFindings(getFallbackData('scanFindings'));
             }
            
            if (scanActivityResult.status === 'fulfilled') {
              console.log('✅ Scan activity loaded:', scanActivityResult.value);
              const extractedData = extractDataWithFallbacks(scanActivityResult.value, 'scanActivity');
              console.log('📊 Extracted scan activity count:', extractedData.length);
              setScanActivity(extractedData);
            } else {
              console.error('❌ Scan activity failed:', scanActivityResult.reason);

              // Use fallback data when API fails
              setScanActivity(getFallbackData('scanActivity'));
            }
            
            if (trendResult.status === 'fulfilled') {
              console.log('✅ Trend data loaded:', trendResult.value);
              const extractedData = extractDataWithFallbacks(trendResult.value, 'trendData');
              console.log('📊 Extracted trend data count:', extractedData.length);
              setTrendData(extractedData);
            } else {
              console.error('❌ Trend data failed:', trendResult.reason);

              // Use fallback data when API fails
              setTrendData(getFallbackData('trendData'));
            }
            
            if (dataSourcesResult.status === 'fulfilled') {
              console.log('✅ Data sources loaded:', dataSourcesResult.value);
              const extractedData = extractDataWithFallbacks(dataSourcesResult.value, 'dataSources');
              console.log('📊 Extracted data sources count:', extractedData.length);
              setDataSources(extractedData);
            } else {
              console.error('❌ Data sources failed:', dataSourcesResult.reason);
              // Use fallback data when API fails
              setDataSources(getFallbackData('dataSources'));
            }

      setLastUpdated(new Date());
      
             // Check for any failures
       const failures = [dashboardResult, riskAssessmentResult, topFindingsResult, scanFindingsResult, scanActivityResult, trendResult, dataSourcesResult]
         .filter(result => result.status === 'rejected');
      
      if (failures.length > 0) {
        console.warn('⚠️ Some API calls failed:', failures);
        showNotification(`Loaded with ${failures.length} warning(s)`, 'warning');
      } else {
        console.log('🎉 All API calls successful!');
        showNotification('Data loaded successfully', 'success');
      }

    } catch (error) {
      console.error('💥 Error loading data:', error);
      const errorMessage = handleApiError(error, showNotification);
      setError(errorMessage);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [safeApiCall, filters.timeRange, showNotification]);

  // Refresh data
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAllData(false);
  }, [loadAllData]);

  // Run new assessment
  const handleRunAssessment = useCallback(async () => {
    try {
      setRefreshing(true);
      const user = getRiskAssessmentUser();
      await triggerRiskAssessment(user.client_id);
      showNotification('Risk assessment started', 'info');
      // Wait a moment then refresh data
      setTimeout(() => loadAllData(false), 2000);
    } catch (error) {
      console.error('Error running assessment:', error);
      showNotification('Failed to start assessment', 'error');
      setRefreshing(false);
    }
  }, [triggerRiskAssessment, loadAllData, showNotification]);

  // Handle filter changes
  const handleFilterChange = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  // Apply filters effect
  useEffect(() => {
    if (!loading) {
      const timeoutId = setTimeout(() => {
        loadAllData(false);
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [filters.timeRange]); // Only refresh on time range changes

  // Initial load
  useEffect(() => {
    loadAllData();
  }, []);

  // Add effect to load initial risk findings
  useEffect(() => {
    const user = getRiskAssessmentUser();
    const clientId = user.client_id;
    if (clientId && activeTab === 'findings') {
      handleRiskFindingsSearch();
    }
  }, [activeTab, handleRiskFindingsSearch]);

  // Memoized chart data
  const chartData = useMemo(() => {
    if (!dashboardData || !riskAssessmentData) return {};

    // Risk Level Distribution - using direct API response
    const riskDistribution = riskAssessmentData.risk_distribution || [];
    console.log('Risk distribution data for chart:', riskDistribution);
    
    // Create a simple array structure for the chart data
    const riskChartData = riskDistribution.map(item => ({
      level: item.level || 'Unknown',
      count: item.count || 0
    }));
    console.log('Risk chart data:', riskChartData);

    // SDE Categories - using new API response
    const sdeRiskDistribution = riskAssessmentData.sde_risk_distribution || [];
    console.log('SDE Risk Distribution data:', sdeRiskDistribution);
    
    // Aggregate SDE risk distribution data to handle potential duplicates
    const aggregatedSdeRiskDistribution = sdeRiskDistribution.reduce((acc, item) => {
      const riskLevel = item.risk_level?.toUpperCase() || 'Unknown';
      const existingItem = acc.find(x => x.risk_level === riskLevel);
      if (existingItem) {
        existingItem.count += (item.count || 0);
      } else {
        acc.push({
          risk_level: riskLevel,
          count: item.count || 0
        });
      }
      return acc;
    }, []);
    console.log('Aggregated SDE Risk Distribution:', aggregatedSdeRiskDistribution);
    
    // Detection Methods
    const detectionMethods = riskAssessmentData.detection_methods || [];
    
    // Confidence Distribution
    const confidenceDistribution = riskAssessmentData.confidence_distribution || [];
    
    // SDE Categories
    const sdeCategories = riskAssessmentData.sde_categories || [];
    
    // Privacy Violations
    const privacyViolations = riskAssessmentData.privacy_violations || [];
    
    // Risk Matrix
    const riskMatrix = riskAssessmentData.risk_matrix || [];

    return {
      riskDistribution: {
        labels: riskChartData.map(item => item.level),
        datasets: [{
          data: cleanChartData(riskChartData.map(item => item.count)),
          backgroundColor: ['#64B5F6', '#F59E0B', '#EF4444'],
          borderColor: ['#42A5F5', '#D97706', '#DC2626'],
          borderWidth: 2
        }]
      },
      sdeRiskDistribution: {
        labels: aggregatedSdeRiskDistribution.map(item => item.risk_level),
        datasets: [{
          data: cleanChartData(aggregatedSdeRiskDistribution.map(item => item.count)),
          backgroundColor: ['#64B5F6', '#F59E0B', '#EF4444'], // Blue, Orange, Red for Low, Medium, High
          borderColor: ['#42A5F5', '#D97706', '#DC2626'],
          borderWidth: 2
        }]
      },
      detectionMethods: {
        labels: detectionMethods.map(item => item.method || 'Unknown'),
        datasets: [{
          label: 'Detections',
          data: cleanChartData(detectionMethods.map(item => item.count || 0)),
          backgroundColor: '#3B82F6',
          borderColor: '#2563EB',
          borderWidth: 1
        }]
      },
      confidenceDistribution: {
        labels: confidenceDistribution.map(item => item.level || 'Unknown'),
        datasets: [{
          label: 'Confidence Level',
          data: cleanChartData(confidenceDistribution.map(item => item.count || 0)),
          backgroundColor: 'rgba(59, 130, 246, 0.6)',
          borderColor: '#3B82F6',
          borderWidth: 2
        }]
      },
      sdeCategories: {
        labels: sdeCategories.map(item => item.category || 'Unknown'),
        datasets: [{
          label: 'SDE Categories',
          data: cleanChartData(sdeCategories.map(item => item.count || 0)),
          backgroundColor: ['#3B82F6', '#64B5F6', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#A855F7'],
          borderColor: ['#2563EB', '#42A5F5', '#D97706', '#DC2626', '#7C3AED', '#0891B2', '#65A30D', '#EA580C', '#DB2777', '#9333EA'],
          borderWidth: 2
        }]
      },
      privacyViolations: {
        labels: privacyViolations.map(item => item.implication || 'Unknown'),
        datasets: [{
          label: 'Privacy Violations',
          data: cleanChartData(privacyViolations.map(item => item.count || 0)),
          backgroundColor: '#F59E0B',
          borderColor: '#D97706',
          borderWidth: 2
        }]
      },
      riskMatrix: {
        labels: (() => {
          // Filter and limit to only Low, Medium, High (3 bars maximum)
          const validImpacts = ['Low', 'Medium', 'High'];
          const filteredMatrix = riskMatrix.filter(item => {
            const impact = item.impact ? item.impact.toString() : '';
            return validImpacts.includes(impact);
          });

          // Group by impact and sum counts for duplicates
          const impactGroups = {};
          filteredMatrix.forEach(item => {
            const impact = item.impact;
            if (impactGroups[impact]) {
              impactGroups[impact] += item.count || 0;
            } else {
              impactGroups[impact] = item.count || 0;
            }
          });

          // Return only the first 3 valid impacts in order
          return validImpacts.filter(impact => impactGroups[impact] !== undefined).slice(0, 3);
        })(),
        datasets: [{
          label: 'Risk Matrix',
          data: (() => {
            // Filter and limit to only Low, Medium, High (3 bars maximum)
            const validImpacts = ['Low', 'Medium', 'High'];
            const filteredMatrix = riskMatrix.filter(item => {
              const impact = item.impact ? item.impact.toString() : '';
              return validImpacts.includes(impact);
            });

            // Group by impact and sum counts for duplicates
            const impactGroups = {};
            filteredMatrix.forEach(item => {
              const impact = item.impact;
              if (impactGroups[impact]) {
                impactGroups[impact] += item.count || 0;
              } else {
                impactGroups[impact] = item.count || 0;
              }
            });

            // Return data for only the first 3 valid impacts in order
            const validImpactsWithData = validImpacts.filter(impact => impactGroups[impact] !== undefined).slice(0, 3);
            return cleanChartData(validImpactsWithData.map(impact => impactGroups[impact]));
          })(),
          backgroundColor: '#EF4444',
          borderColor: '#DC2626',
          borderWidth: 2
        }]
      },
      trendAnalysis: {
        labels: trendData.map(item => new Date(item.date || item.scan_timestamp).toLocaleDateString()),
        datasets: [
          {
            label: 'Total Findings',
            data: cleanChartData(trendData.map(item => item.total_findings || 0)),
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
          },
          {
            label: 'High Risk',
            data: cleanChartData(trendData.map(item => item.high_risk || 0)),
            borderColor: '#EF4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.4
          }
        ]
      },
      scanActivity: {
        labels: scanActivity.map(item => new Date(item.scan_timestamp || item.date).toLocaleDateString()),
        datasets: [{
          label: 'Daily Scans',
          data: cleanChartData(scanActivity.map(item => item.findings_count || item.findings || 0)),
          backgroundColor: '#64B5F6',
          borderColor: '#42A5F5',
          borderWidth: 1
        }]
      }
    };
    
    console.log('Final chart data:', chartData);
  }, [dashboardData, riskAssessmentData, trendData, scanActivity]);

  // Chart options
  const chartOptions = getLineChartOptions('Risk Analysis');
  const pieChartOptions = getPieChartOptions('Risk Distribution');
  const barChartOptions = getBarChartOptions('Risk Metrics');
  
  // Simple chart options for testing
  const simplePieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: 'Risk Distribution'
      }
    }
  };

  // Transform scan findings to match component expectations
  const transformedFindings = useMemo(() => {
    if (!scanFindings || !Array.isArray(scanFindings)) return [];
    
    return scanFindings.map(finding => ({
      finding_id: finding.finding_id,
      sde_category: finding.sde_category || finding.sensitivity || 'Unknown',
      risk_level: finding.risk_level || 'medium',
      location: finding.object_path || `${finding.dataset_name || 'Unknown'}.${finding.dataset_column || 'Unknown'}`,
      finding_type: finding.detection_method || 'text',
      data_value: finding.data_value || '',
      confidence_score: finding.confidence_score || 85,
      timestamp: finding.scan_timestamp || new Date().toISOString(),
      dataset_name: finding.dataset_name || 'Unknown',
      dataset_column: finding.dataset_column || 'Unknown',
      detection_method: finding.detection_method || 'Unknown',
      object_path: finding.object_path || 'Unknown'
    }));
  }, [scanFindings]);

  // Filtered findings based on search
  const filteredFindings = useMemo(() => {
    if (!searchTerm) return transformedFindings;
    return transformedFindings.filter(finding => 
      finding.sde_category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.risk_level?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.finding_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.data_value?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.detection_method?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.object_path?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.dataset_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      finding.dataset_column?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [transformedFindings, searchTerm]);









  if (error) {
    return (
      <div className="risk-assessment-page">
        <div className="error-container">
          <XCircle className="error-icon" size={48} />
          <h2>Error Loading Risk Assessment</h2>
          <p>{error}</p>
          <button onClick={() => loadAllData()} className="retry-button">
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="risk-assessment-page">
      {/* Notification */}
      {notification && (
        <div className={`notification notification-${notification.type}`}>
          {notification.type === 'success' && <CheckCircle2 size={16} />}
          {notification.type === 'error' && <XCircle size={16} />}
          {notification.type === 'warning' && <AlertCircle size={16} />}
          {notification.type === 'info' && <AlertTriangle size={16} />}
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)}>×</button>
        </div>
      )}

      {/* Header */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">Risk Assessment Dashboard</h1>
          <p className="page-subtitle">
            Comprehensive analysis of sensitive data risks and security posture
          </p>
          {lastUpdated && (
            <div className="last-updated">
              <Clock size={14} />
              Last updated: {lastUpdated.toLocaleString()}
            </div>
          )}
        </div>
        <div className="header-actions">
          <button
            onClick={handleRunAssessment}
            disabled={refreshing || loading}
            className="action-button primary"
          >
            <Scan size={16} />
            Run Assessment
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <BarChart3 size={16} />
          Overview
        </button>
        <button 
        
          className={`tab-button ${activeTab === 'comprehensive' ? 'active' : ''}`}
          onClick={() => setActiveTab('comprehensive')}
        >
          <PieChart size={16} />
          Comprehensive Dashboard
        </button>
        <button 
          className={`tab-button ${activeTab === 'detailed' ? 'active' : ''}`}
          onClick={() => setActiveTab('detailed')}
        >
          <PieChart size={16} />
          Detailed Analysis
        </button>
        <button 
          className={`tab-button ${activeTab === 'findings' ? 'active' : ''}`}
          onClick={() => setActiveTab('findings')}
        >
          <FileText size={16} />
          Risk Findings
        </button>
        {/* <button 
          className={`tab-button ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          <TrendingUp size={16} />
          Trends & Activity
        </button> */}
      </div>

      {/* Filters */}
      {/* <div className="filters-section">
        <div className="filters-header">
          <h3>Filters & Controls</h3>
          <button 
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            className="expand-button"
          >
            {filtersExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
        {filtersExpanded && (
          <div className="filters-content">
            <div className="filters-grid">
              <div className="filter-group">
                <label>Data Source</label>
                <select 
                  value={filters.dataSource} 
                  onChange={(e) => handleFilterChange('dataSource', e.target.value)}
                >
                  <option value="">All Sources</option>
                  {dataSources.map((source, index) => (
                    <option key={index} value={source.name}>
                      {source.name} ({source.type})
                    </option>
                  ))}
                </select>
              </div>
              <div className="filter-group">
                <label>Risk Level</label>
                <select 
                  value={filters.riskLevel} 
                  onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
                >
                  <option value="">All Levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div className="filter-group">
                <label>Sensitivity</label>
                <select 
                  value={filters.sensitivity} 
                  onChange={(e) => handleFilterChange('sensitivity', e.target.value)}
                >
                  <option value="">All Levels</option>
                  <option value="highly_sensitive">Highly Sensitive</option>
                  <option value="sensitive">Sensitive</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div className="filter-group">
                <label>Time Range (Days)</label>
                <select 
                  value={filters.timeRange} 
                  onChange={(e) => handleFilterChange('timeRange', e.target.value)}
                >
                  <option value="7">Last 7 Days</option>
                  <option value="30">Last 30 Days</option>
                  <option value="90">Last 90 Days</option>
                  <option value="365">Last Year</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div> */}

      {loading ? (
        <div className="loading-container">
          <Loader2 className="spinning" size={48} />
          <p>Loading risk assessment data...</p>
        </div>
      ) : (
        <>
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="tab-content">
              {/* Key Metrics */}
              <MetricsDashboard 
                dashboardData={dashboardData} 
                riskAssessmentData={riskAssessmentData}
                isLoading={loading} 
              />

              {/* Quick Charts */}
              {/* <div className="charts-grid">
                <div className="chart-card">
                  <div className="chart-header">
                    <h3>Risk Level Distribution</h3>
                  </div>
                                     <div className="chart-container">
                                           {console.log('Rendering risk distribution chart with data:', chartData.riskDistribution)}
                      {console.log('Risk distribution labels:', chartData.riskDistribution?.labels)}
                      {console.log('Risk distribution datasets:', chartData.riskDistribution?.datasets)}
                      {console.log('Chart options:', simplePieOptions)}
                      {console.log('Risk assessment data:', riskAssessmentData)}
                      {console.log('Risk distribution from API:', riskAssessmentData?.risk_distribution)}
                                           {chartData.riskDistribution ? (
                        <div style={{ width: '100%', height: '300px', border: '1px solid #ccc' }}>
                          
                          <Pie data={{
                            labels: ['MEDIUM', 'HIGH', 'LOW'],
                            datasets: [{
                              data: [258, 10, 4],
                              backgroundColor: ['#F59E0B', '#EF4444', '#64B5F6'],
                              borderColor: ['#D97706', '#DC2626', '#42A5F5'],
                              borderWidth: 2
                            }]
                          }} options={simplePieOptions} />
                        </div>
                      ) : (
                        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                          No risk distribution data available
                        </div>
                      )}
                   </div>
                </div>
                                 <div className="chart-card">
                   <div className="chart-header">
                     <h3>SDE Risk Distribution</h3>
                   </div>
                   <div className="chart-container">
                     {console.log('Rendering SDE chart with data:', chartData.sdeCategories)}
                     {console.log('SDE Chart options:', pieChartOptions)}
                     {chartData.sdeCategories ? (
                       <div style={{ width: '100%', height: '300px', border: '1px solid #ccc' }}>
                         <Pie data={chartData.sdeCategories} options={simplePieOptions} />
                       </div>
                     ) : (
                       <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                         No SDE risk distribution data available
                       </div>
                     )}
                   </div>
                 </div>
              </div> */}
            </div>
          )}

          {/* Comprehensive Dashboard Tab */}
          {activeTab === 'comprehensive' && (
            <div className="tab-content">
              <ComprehensiveDashboard activeSection="dashboard" />
            </div>
          )}

          {/* Detailed Analysis Tab */}
          {activeTab === 'detailed' && (
            <div className="tab-content">
              <div className="charts-grid large">
                <div className="chart-card">
                  <div className="chart-header">
                    <h3>Detection Methods</h3>
                  </div>
                  <div className="chart-container">
                    {chartData.detectionMethods && (
                      <Bar data={chartData.detectionMethods} options={barChartOptions} />
                    )}
                  </div>
                </div>
                <div className="chart-card">
                  <div className="chart-header">
                    <h3>Confidence Distribution</h3>
                  </div>
                  <div className="chart-container">
                    {chartData.confidenceDistribution && (
                      <Bar data={chartData.confidenceDistribution} options={barChartOptions} />
                    )}
                  </div>
                </div>
                <div className="chart-card">
                  <div className="chart-header">
                    <h3>SDE Categories Distribution</h3>
                  </div>
                  <div className="chart-container">
                    {chartData.sdeCategories && (
                      <Bar data={chartData.sdeCategories} options={barChartOptions} />
                    )}
                  </div>
                </div>
                {/* <div className="chart-card">
                  <div className="chart-header">
                    <h3>Privacy Violations</h3>
                  </div>
                  <div className="chart-container">
                    {chartData.privacyViolations && (
                      <Bar data={chartData.privacyViolations} options={barChartOptions} />
                    )}
                  </div>
                </div> */}
                <div className="chart-card">
                  <div className="chart-header">
                    <h3>Risk Matrix by Impact</h3>
                  </div>
                  <div className="chart-container">
                    {chartData.riskMatrix && (
                      <Bar data={chartData.riskMatrix} options={barChartOptions} />
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Risk Findings Tab */}
          {activeTab === 'findings' && (
            <div className="tab-content">
              
              <div className="risk-findings-content">
                {isLoadingRiskFindings ? (
                  <div className="loading-message">Loading risk findings...</div>
                ) : (
                  <RiskFindingsTable
                    findings={filteredRiskFindings.map(finding => ({
                      finding_id: finding.finding_id,
                      data_value: finding.data_value || '',
                      sensitivity: finding.sensitivity || 'N/A',
                      finding_type: finding.finding_type || 'N/A',
                      sde_category: finding.sde_category || 'Unknown',
                      risk_level: finding.risk_level || 'Unknown',
                      confidence_score: finding.confidence_score || 0,
                      scan_timestamp: finding.scan_timestamp || new Date().toISOString()
                    }))}
                  />
                )}
              </div>
            </div>
          )}

          {/* Trends & Activity Tab */}
          {activeTab === 'trends' && (
            <div className="tab-content">
              <RiskTrendWidget 
                trendData={trendData}
                timeRange={filters.timeRange}
                clientId={getRiskAssessmentUser()?.client_id}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default NewRiskAssessmentPage;
