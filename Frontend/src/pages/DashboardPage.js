import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../Css/Dashboard.css';
import '../Css/RiskDashboardTheme.css';
import SummaryCard from '../components/dashboard/SummaryCard';
import ScanActivityWidget from '../components/dashboard/ScanActivityWidget';
import DataSourcePieChart from '../components/dashboard/DataSourcePieChart';
import SecurityInsightsWidget from '../components/dashboard/RiskDistributionDonut';

import DataSourceInventoryTable from '../components/dashboard/DataSourceInventoryTable';
import RiskSummaryWidget from '../components/dashboard/RiskSummaryWidget';
// import NotificationsWidget from '../components/dashboard/NotificationsWidget';
import { Unplug, CheckCheck, ChartSplineIcon, TriangleAlert} from 'lucide-react'
import { API_BASE_URL } from '../apiConfig';
import { getCurrentClientId, getCurrentUser } from '../utils/clientUtils';

// Remove the local getCurrentUser function as we're importing it from utils

function DashboardPage() {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataLoaded, setDataLoaded] = useState(false); // Track if data has been loaded

  // Function to trigger risk assessment
  const performRiskAssessment = async (clientId) => {
    try {
      console.log('Triggering risk assessment for client:', clientId);
      const response = await fetch(`${API_BASE_URL}/risk/risk-assessment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId })
      });
      
      if (response.ok) {
        console.log(' Risk assessment triggered successfully');
      } else {
        console.warn('⚠️ Risk assessment trigger failed:', response.status);
      }
    } catch (error) {
      console.error('❌ Error triggering risk assessment:', error);
    }
  };

  // Function to fetch comprehensive dashboard data using new endpoints
  const fetchDashboardMetrics = async (clientId) => {
    try {
      console.log('Fetching comprehensive dashboard data for client:', clientId);
      
      // Use the comprehensive dashboard endpoint
      const response = await fetch(`${API_BASE_URL}/risk/comprehensive-dashboard/${clientId}`);
      console.log('Comprehensive dashboard response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch comprehensive dashboard: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Comprehensive dashboard data:', data);
      
      // Also fetch individual metrics for backward compatibility
      const individualEndpoints = [
        { key: 'total_data_sources', url: `/risk/total-data-sources/${clientId}` },
        { key: 'total_sdes', url: `/risk/total-sdes/${clientId}` },
        { key: 'total_scans', url: `/risk/total-scans/${clientId}` },
        { key: 'last_scan_time', url: `/risk/last-scan-time/${clientId}` },
        { key: 'next_scheduled_scan', url: `/risk/next-scheduled-scan/${clientId}` },
        { key: 'high_risk_sdes', url: `/risk/high-risk-sdes/${clientId}` },
        { key: 'total_sensitive_records', url: `/risk/total-sensitive-records/${clientId}` },
        { key: 'risk_score', url: `/risk/risk-score/${clientId}` },
      ];

      const results = {};
      
      // Fetch all individual metrics in parallel
      const promises = individualEndpoints.map(async (endpoint) => {
        try {
          console.log(`Fetching ${endpoint.key} from ${endpoint.url}`);
          const response = await fetch(`${API_BASE_URL}${endpoint.url}`);
          console.log(`Response status for ${endpoint.key}:`, response.status);
          
          if (!response.ok) {
            throw new Error(`Failed to fetch ${endpoint.key}: ${response.statusText}`);
          }
          const data = await response.json();
          console.log(`Data for ${endpoint.key}:`, data);
          return { key: endpoint.key, data };
        } catch (error) {
          console.error(`❌ ERROR fetching ${endpoint.key}:`, error);
          console.error(`❌ ERROR ${endpoint.key} message:`, error.message);
          return { key: endpoint.key, data: { [endpoint.key]: 0, error: error.message } };
        }
      });

      const responses = await Promise.all(promises);
      
      // Combine all results
      responses.forEach(({ key, data }) => {
        console.log(`Processing ${key}:`, data);
        
        // Extract the correct field from each response
        if (key === 'total_data_sources') results[key] = data.total_data_sources || 0;
        else if (key === 'total_sdes') results[key] = data.total_sdes || 0;
        else if (key === 'total_scans') results[key] = data.total_scans || 0;
        else if (key === 'last_scan_time') results[key] = data.last_scan_time || '';
        else if (key === 'next_scheduled_scan') results[key] = data.next_scheduled_scan || '';
        else if (key === 'high_risk_sdes') results[key] = data.high_risk_sdes || 0;
        else if (key === 'total_sensitive_records') results[key] = data.total_sensitive_records || 0;
        else if (key === 'risk_score') results[key] = data.risk_score || 0;
      });

      // Add comprehensive dashboard data
      results.comprehensive_data = data;
      
      console.log('Final dashboard results:', results);
      return results;
    } catch (error) {
      console.error('Error fetching dashboard metrics:', error);
      throw error;
    }
  };

  // Function to fetch scan activity data
  const fetchScanActivity = async (clientId) => {
    try {
      console.log('🔍 DEBUG: Starting fetchScanActivity for clientId:', clientId);
      console.log('🔍 DEBUG: Full URL:', `${API_BASE_URL}/risk/scan-activity/${clientId}`);
      const response = await fetch(`${API_BASE_URL}/risk/scan-activity/${clientId}`);
      
      console.log('🔍 DEBUG: Response status:', response.status);
      console.log('🔍 DEBUG: Response ok:', response.ok);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch scan activity: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('🔍 DEBUG: Raw scan activity data:', data);
      console.log('🔍 DEBUG: recent_scans length:', data.recent_scans?.length || 0);
      console.log('🔍 DEBUG: daily_scans length:', data.daily_scans?.length || 0);
      console.log('🔍 DEBUG: data_stores length:', data.data_stores?.length || 0);
      

      
      // Log sample data
      if (data.recent_scans && data.recent_scans.length > 0) {
        console.log('🔍 DEBUG: Sample recent scan:', data.recent_scans[0]);
      }
      if (data.daily_scans && data.daily_scans.length > 0) {
        console.log('🔍 DEBUG: Sample daily scan:', data.daily_scans[0]);
      }
      if (data.data_stores && data.data_stores.length > 0) {
        console.log('🔍 DEBUG: Sample data store:', data.data_stores[0]);
      }
      
      return data;
    } catch (error) {
      console.error('❌ ERROR: Error fetching scan activity:', error);
      // Return default data if API fails
      const fallbackData = {
        recent_scans: [],
        daily_scans: [],
        total_scans: 0,
        data_stores: []
      };
      console.log('🔍 DEBUG: Returning fallback data:', fallbackData);
      return fallbackData;
    }
  };

  useEffect(() => {
    // Add fade-in class to the container on mount
    const dashboardContainer = document.getElementById('dashboard-container');
    if (dashboardContainer) {
      dashboardContainer.classList.add('fade-in');
    }

    // Fetch real dashboard data
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        const clientId = getCurrentClientId();

        // Trigger risk assessment first
        await performRiskAssessment(clientId);

        const metrics = await fetchDashboardMetrics(clientId);
        const scanActivity = await fetchScanActivity(clientId);
        
        // Format last scan time - use scan activity data if available
        let lastScanTime = 'Never';
        if (scanActivity.recent_scans && scanActivity.recent_scans.length > 0) {
          // Use the most recent scan
          const mostRecentScan = scanActivity.recent_scans[0];
          lastScanTime = 'Recently'; // Since we don't have actual timestamp, use "Recently"
        } else if (metrics.last_scan_time) {
          try {
            const date = new Date(metrics.last_scan_time);
            lastScanTime = date.toLocaleString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });
          } catch (e) {
            console.error('Error formatting last scan time:', e);
            lastScanTime = 'Recently';
          }
        }

        // Format next scheduled scan
        let nextScanTime = 'Not scheduled';
        if (metrics.next_scheduled_scan) {
          try {
            const date = new Date(metrics.next_scheduled_scan);
            nextScanTime = date.toLocaleString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });
          } catch (e) {
            console.error('Error formatting next scan time:', e);
            nextScanTime = 'Soon';
          }
        }


        

        
        const mappedDailyScans = scanActivity.daily_scans.map(day => ({
          day: day.day,
          scans: day.scans
        }));
        
        const mappedRecentScans = scanActivity.recent_scans.map(scan => ({
          id: scan.scan_id,
          source: scan.store_name,
          time: 'Recently', // Use a simple time since scan_id might not be a timestamp
          status: scan.status,
          findings: scan.findings || 'N/A',
          type: scan.store_type,
          location: scan.location
        }));
        
        console.log('🔍 DEBUG: Original scan data:', scanActivity.recent_scans);
        console.log('🔍 DEBUG: Mapped scan data:', mappedRecentScans);
        
        console.log('🔍 DEBUG: Mapped recent scans:', mappedRecentScans);
        
        const mappedDataStores = scanActivity.data_stores.map(store => ({
          id: store.store_id,
          name: store.store_name,
          type: store.store_type,
          region: store.location,
          lastScanned: store.discovery_timestamp ? new Date(store.discovery_timestamp).toLocaleDateString() : 'Unknown',
          status: 'Active'
        }));
        
        const realData = {
          kpis: [
            { title: 'Total Data Sources Connected', value: metrics.total_data_sources || 0, icon: <Unplug  className='lucide-icon' /> },
            { title: 'Sensitive Data Elements(SDEs)', value: metrics.total_sdes || 0, icon: <ChartSplineIcon className='lucide-icon' /> },
            { title: 'Scans Completed', value: metrics.total_scans || 0, icon: <CheckCheck className='lucide-icon' /> },
            // { title: 'Total Risks Identified', value: metrics.high_risk_sdes || 0, icon: <TriangleAlert className='lucide-icon' /> },
          ],
          scanActivity: {
            dailyScans: mappedDailyScans,
            recentScans: mappedRecentScans,
            totalScans: scanActivity.total_scans || 0,
          },
          // Chart data using comprehensive dashboard data
          chartData: {
                      dataSources: scanActivity.data_stores?.map(store => ({
            type: store.store_type,
            count: 1
          })) || [
            { type: 'Database', count: 0 },
            { type: 'File Storage', count: 0 },
            { type: 'Cloud Storage', count: 0 }
          ],
            sdeCount: metrics.comprehensive_data?.risk_distribution || [
              { level: 'Low', count: 0 },
              { level: 'Medium', count: 0 },
              { level: 'High', count: 0 }
            ],
            totalSdes: metrics.total_sdes || 0,
            highRiskSdes: metrics.high_risk_sdes || 0,
            riskScore: metrics.risk_score || 0,
            totalSensitiveRecords: metrics.total_sensitive_records || 0,
            sensitivityCategories: metrics.comprehensive_data?.sensitivity_categories || [
              { category: 'Personal', count: 0 },
              { category: 'Financial', count: 0 },
              { category: 'Health', count: 0 }
            ],
            protectionCoverage: metrics.comprehensive_data?.protection_coverage || [
              { method: 'Encryption', count: 0 },
              { method: 'Access Control', count: 0 },
              { method: 'Monitoring', count: 0 }
            ],
          },
          dataSourceInventory: mappedDataStores,
                  riskSummary: {
          totalScans: metrics.total_scans || 0,
          lastScan: lastScanTime,
          activeSources: metrics.total_data_sources || 0,
        },
          notifications: [],
        };
        
        setDashboardData(realData);
        setDataLoaded(true); // Mark data as loaded
        
        // Debug: Show the scan activity data being passed

    } catch (error) {
      console.error('❌ ERROR: Error fetching dashboard data:', error);
      console.error('❌ ERROR: Error message:', error.message);
      console.error('❌ ERROR: Error stack:', error.stack);
      setError(`Failed to load dashboard data: ${error.message}`);
    } finally {
      setLoading(false);
    }
    };

    // Only fetch if data is not already loaded
    if (!dataLoaded) {
      fetchDashboardData();
    }
  }, []);

  useEffect(() => {
    const clientId = getCurrentClientId();
    fetch(`${API_BASE_URL}/risk/total-data-sources/${clientId}`)
      .then(res => res.json())
      .then(data => {
        // setHasConnections((data.total_data_sources || 0) > 0); // This line was removed
        // setCheckedConnections(true); // This line was removed
      })
      .catch(() => {
        // setHasConnections(false); // This line was removed
        // setCheckedConnections(true); // This line was removed
      });
  }, []);

  // if (checkedConnections && !hasConnections) {
  //   return (
  //     <div id="dashboard-container" className="dashboard-container">
  //       <h1 className="page-title">Upload data sources for analysis</h1>
  //       {/* Optionally, add a button to go to the upload/connect page */}
  //     </div>
  //   );
  // }

  const handleViewFullRiskAssessment = () => {
    navigate('/risk-assessment'); // Navigate to the Risk Assessment page
  };



  if (loading) {
    return (
      <div id="dashboard-container" className="dashboard-container">
        <div className="loading-message">Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="dashboard-container" className="dashboard-container">
        <div className="error-message-display">{error}</div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div id="dashboard-container" className="dashboard-container">
        <div className="loading-message">Failed to load dashboard data</div>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // Safety check for chartData
  if (!dashboardData.chartData) {
    console.error('❌ ERROR: chartData is undefined!');
    return (
      <div id="dashboard-container" className="dashboard-container">
        <div className="error-message-display">Dashboard data structure is invalid</div>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, hsl(210 40% 98%) 0%, hsl(210 40% 96%) 100%)',
      padding: '1.5rem'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        {/* Modern Dashboard Header - More Compact */}
        <div style={{
          background: 'linear-gradient(135deg, hsl(198 88% 32%), hsl(172 76% 47%))',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          color: 'hsl(0 0% 98%)',
          boxShadow: '0 4px 20px hsl(198 88% 32% / 0.25)',
          border: '1px solid hsl(198 88% 35%)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem'
          }}>
            <div>
              <h1 style={{
                fontSize: '2.25rem',
                fontWeight: '700',
                margin: '0 0 0.25rem 0',
                color: 'hsl(0 0% 98%)',
                textShadow: '0 2px 4px hsl(198 88% 20% / 0.3)'
              }}>
                Dashboard
              </h1>
              <p style={{
                fontSize: '1rem',
                margin: 0,
                opacity: '0.9'
              }}>
                Comprehensive overview of your data security landscape
              </p>
            </div>
          </div>
        </div>

        {/* Summary Cards Grid - Compact Design */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '0.75rem',
          marginBottom: '1.5rem'
        }}>
          {dashboardData.kpis.map((kpi, index) => (
            <div
              key={index}
              style={{
                background: 'hsl(0 0% 100%)',
                borderRadius: '0.5rem',
                padding: '0.75rem',
                border: '1px solid hsl(220 13% 91%)',
                transition: 'all 0.2s ease',
                position: 'relative',
                overflow: 'hidden',
                minHeight: '80px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.borderColor = 'hsl(198 88% 32%)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.borderColor = 'hsl(220 13% 91%)';
              }}
            >
              {/* Subtle background accent */}
              <div style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: '40px',
                height: '40px',
                background: 'linear-gradient(135deg, hsl(198 88% 32% / 0.05), hsl(172 76% 47% / 0.05))',
                borderRadius: '0 0 0 100%',
                zIndex: 0
              }} />
              
              <div style={{ 
                position: 'relative', 
                zIndex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <div style={{
                  fontSize: '1.2rem',
                  color: 'hsl(198 88% 32%)',
                  display: 'flex',
                  alignItems: 'center',
                  flexShrink: 0
                }}>
                  {kpi.icon}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: '1.5rem',
                    fontWeight: '700',
                    color: 'hsl(198 88% 32%)',
                    lineHeight: '1.2',
                    marginBottom: '0.125rem'
                  }}>
                    {kpi.value}
                  </div>
                  <div style={{
                    fontSize: '0.75rem',
                    color: 'hsl(220 9% 46%)',
                    lineHeight: '1.2',
                    fontWeight: '500',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {kpi.title}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Combined Scan Activity and Data Source Distribution - Side by Side Layout */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
          gap: '1.25rem',
          marginBottom: '1.5rem'
        }}>
          {/* Scan Activity Widget */}
          <div style={{
            background: 'hsl(0 0% 100%)',
            borderRadius: '0.75rem',
            padding: '1.25rem',
            border: '1px solid hsl(220 13% 91%)',
            transition: 'all 0.2s ease',
            position: 'relative'
          }}
          onMouseEnter={(e) => {
            e.target.style.borderColor = 'hsl(220 13% 85%)';
          }}
          onMouseLeave={(e) => {
            e.target.style.borderColor = 'hsl(220 13% 91%)';
          }}
          >
            {/* Header accent */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '3px',
              background: 'linear-gradient(90deg, hsl(172 76% 47%), hsl(198 88% 32%))',
              borderRadius: '0.75rem 0.75rem 0 0'
            }} />
            <ScanActivityWidget scanActivity={dashboardData.scanActivity} />
          </div>

          {/* Data Source Distribution */}
          <div style={{
            background: 'hsl(0 0% 100%)',
            borderRadius: '0.75rem',
            padding: '1.25rem',
            border: '1px solid hsl(220 13% 91%)',
            transition: 'all 0.2s ease',
            position: 'relative'
          }}
          onMouseEnter={(e) => {
            e.target.style.borderColor = 'hsl(220 13% 85%)';
          }}
          onMouseLeave={(e) => {
            e.target.style.borderColor = 'hsl(220 13% 91%)';
          }}
          >
            {/* Header accent */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '3px',
              background: 'linear-gradient(90deg, hsl(198 88% 32%), hsl(172 76% 47%))',
              borderRadius: '0.75rem 0.75rem 0 0'
            }} />
            <DataSourcePieChart dataSources={dashboardData.chartData?.dataSources || []} />
          </div>
        </div>

        {/* Data Source Inventory Table - Enhanced Design */}
        <div style={{
          background: 'hsl(0 0% 100%)',
          borderRadius: '0.75rem',
          padding: '1.25rem',
          border: '1px solid hsl(220 13% 91%)',
          marginBottom: '1.5rem',
          position: 'relative',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.target.style.borderColor = 'hsl(220 13% 85%)';
        }}
        onMouseLeave={(e) => {
          e.target.style.borderColor = 'hsl(220 13% 91%)';
        }}
        >
          {/* Header accent */}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, hsl(172 76% 47%), hsl(198 88% 32%))',
            borderRadius: '0.75rem 0.75rem 0 0'
          }} />
          <DataSourceInventoryTable inventory={dashboardData.dataSourceInventory} />
        </div>

        {/* Notifications Widget */}
        {/* <div style={{
          background: 'hsl(0 0% 100%)',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          border: '1px solid hsl(220 13% 91%)',
          boxShadow: '0 4px 6px -1px hsl(215 25% 15% / 0.1), 0 2px 4px -1px hsl(215 25% 15% / 0.06)'
        }}>
          <NotificationsWidget notifications={dashboardData.notifications} />
        </div> */}
      </div>
    </div>
  );
}

export default DashboardPage;