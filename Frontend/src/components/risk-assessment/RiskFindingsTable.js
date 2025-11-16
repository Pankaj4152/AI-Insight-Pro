import { useState, useMemo, useCallback } from 'react';
import {
  AlertTriangle,
  Shield,
  Globe,
  Clock,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { API_BASE_URL } from '../../apiConfig';
import { getCurrentUser } from '../../utils/riskAssessmentUtils';

const RiskFindingsTable = ({ 
  findings = [], 
  isLoading = false, 
  onViewDetails
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  
  // New state for enhanced filtering
  const [searchFilters, setSearchFilters] = useState({
    riskLevel: 'all',
    sensitivity: 'all'
  });
  const [filteredFindings, setFilteredFindings] = useState([]);
  const [showAllFindings, setShowAllFindings] = useState(false);





  // Helper function to fetch with custom parameters
  const fetchFilteredRiskFindingsWithParams = useCallback(async (params) => {
    try {
      const user = getCurrentUser();
      const clientId = user.client_id;

      // Add limit parameter to ensure we get enough results
      params.append('limit', '100');

      const url = `${API_BASE_URL}/risk/risk-findings/${clientId}?${params.toString()}`;
      console.log('Fetching filtered risk findings from:', url);
      console.log('Request parameters:', Object.fromEntries(params.entries()));

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Filtered risk findings response:', data);
      console.log('Number of findings received:', data.findings?.length || 0);
      console.log('Total count from API:', data.total_count);

      // Handle different possible response structures
      let findings = [];
      if (data.findings && Array.isArray(data.findings)) {
        findings = data.findings;
      } else if (data.risk_findings && Array.isArray(data.risk_findings)) {
        findings = data.risk_findings;
      } else if (Array.isArray(data)) {
        findings = data;
      }

      console.log('Processed findings:', findings.length, 'items');
      if (findings.length > 0) {
        console.log('Sample finding:', findings[0]);
      }

      setFilteredFindings(findings);

      // Force a re-render check
      setTimeout(() => {
        console.log('State after setting filteredFindings:', findings.length);
      }, 100);

      if (findings.length === 0) {
        console.log('No findings found for the selected filters');
        console.log('This might indicate:');
        console.log('1. No data matches the filter criteria');
        console.log('2. Backend API parameter mismatch');
        console.log('3. Database query issue');
      } else {
        console.log('Successfully loaded', findings.length, 'filtered findings');
      }
    } catch (error) {
      console.error('Error fetching filtered risk findings:', error);
      setFilteredFindings([]);
    }
  }, []);

  // New API call for filtered risk findings with fallback
  const fetchFilteredRiskFindings = useCallback(async () => {
    const params = new URLSearchParams();
    if (searchFilters.riskLevel && searchFilters.riskLevel !== 'all') {
      // Send lowercase to match API expectation
      params.append('risk_level', searchFilters.riskLevel.toLowerCase());
    }
    if (searchFilters.sensitivity && searchFilters.sensitivity !== 'all') {
      // Send sensitivity parameter to backend
      params.append('sensitivity', searchFilters.sensitivity.toLowerCase());
    }

    // Try the primary endpoint first
    await fetchFilteredRiskFindingsWithParams(params);

    // If no results and we have active filters, try alternative approaches
    setTimeout(async () => {
      if (filteredFindings.length === 0 && (searchFilters.riskLevel !== 'all' || searchFilters.sensitivity !== 'all')) {
        console.log('No results from primary endpoint, trying alternative approaches...');

        // Try the alternative filtered-findings endpoint
        try {
          const user = getCurrentUser();
          const clientId = user.client_id;

          let altUrl = `${API_BASE_URL}/risk/filtered-findings/?client_id=${clientId}`;
          if (searchFilters.riskLevel && searchFilters.riskLevel !== 'all') {
            altUrl += `&risk_level=${searchFilters.riskLevel.toLowerCase()}`;
          }
          if (searchFilters.sensitivity && searchFilters.sensitivity !== 'all') {
            altUrl += `&sensitivity=${searchFilters.sensitivity.toLowerCase()}`;
          }

          console.log('Trying alternative endpoint:', altUrl);
          const altResponse = await fetch(altUrl);

          if (altResponse.ok) {
            const altData = await altResponse.json();
            console.log('Alternative endpoint response:', altData);

            // Handle different response structures
            let altFindings = [];
            if (altData.filtered_findings && Array.isArray(altData.filtered_findings)) {
              altFindings = altData.filtered_findings;
            } else if (altData.findings && Array.isArray(altData.findings)) {
              altFindings = altData.findings;
            }

            if (altFindings.length > 0) {
              console.log('Found', altFindings.length, 'findings from alternative endpoint');
              setFilteredFindings(altFindings);
            }
          }
        } catch (altError) {
          console.error('Alternative endpoint also failed:', altError);
        }
      }
    }, 500);
  }, [searchFilters, fetchFilteredRiskFindingsWithParams, filteredFindings.length]);



  // Handle reset filters
  const handleResetFilters = useCallback(() => {
    setSearchFilters({
      riskLevel: 'all',
      sensitivity: 'all'
    });
    setFilteredFindings([]);
  }, []);

  // Handle filter changes with automatic search
  const handleFilterChange = useCallback((key, value) => {
    setSearchFilters(prev => {
      const newFilters = { ...prev, [key]: value };
      // Automatically trigger search when filters change
      setTimeout(() => {
        const params = new URLSearchParams();
        if (newFilters.riskLevel && newFilters.riskLevel !== 'all') {
          // Send lowercase to match API expectation
          params.append('risk_level', newFilters.riskLevel.toLowerCase());
        }
        if (newFilters.sensitivity && newFilters.sensitivity !== 'all') {
          params.append('sensitivity', newFilters.sensitivity.toLowerCase());
        }

        // Trigger the search with new filters
        fetchFilteredRiskFindingsWithParams(params);
      }, 100);

      return newFilters;
    });
  }, [fetchFilteredRiskFindingsWithParams]);



  // Determine which findings to display with fallback client-side filtering
  const hasActiveFilters = searchFilters.riskLevel !== 'all' || searchFilters.sensitivity !== 'all';

  let displayFindings = [];
  if (hasActiveFilters) {
    // Use server-side filtered results if available
    if (filteredFindings && filteredFindings.length > 0) {
      displayFindings = filteredFindings;
    } else if (findings && findings.length > 0) {
      // Fallback to client-side filtering if server-side filtering returns no results
      console.log('Falling back to client-side filtering...');
      displayFindings = findings.filter(finding => {
        let matchesRiskLevel = true;
        let matchesSensitivity = true;

        if (searchFilters.riskLevel !== 'all') {
          matchesRiskLevel = finding.risk_level?.toLowerCase() === searchFilters.riskLevel.toLowerCase();
        }

        if (searchFilters.sensitivity !== 'all') {
          matchesSensitivity = finding.sensitivity?.toLowerCase() === searchFilters.sensitivity.toLowerCase();
        }

        return matchesRiskLevel && matchesSensitivity;
      });
      console.log('Client-side filtering result:', displayFindings.length, 'findings');
    }
  } else {
    // No filters active, show original findings
    displayFindings = findings && findings.length > 0 ? findings : [];
  }

  // Debug logging to understand data flow
  console.log('RiskFindingsTable Debug:', {
    findingsLength: findings?.length || 0,
    filteredFindingsLength: filteredFindings?.length || 0,
    displayFindingsLength: displayFindings?.length || 0,
    hasActiveFilters,
    searchFilters,
    showAllFindings,
    shouldShowDropdown: displayFindings.length > 10,
    usingClientSideFiltering: hasActiveFilters && filteredFindings.length === 0 && findings.length > 0
  });
  


  // Filter and sort findings
  const processedFindings = useMemo(() => {
    let filtered = displayFindings;

    if (sortConfig.key) {
      filtered.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Handle different data types
        if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue?.toLowerCase() || '';
        }

        if (typeof aValue === 'number') {
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
        }

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    // Limit to 10 findings by default unless showAllFindings is true
    if (!showAllFindings && filtered.length > 10) {
      filtered = filtered.slice(0, 10);
    }

    return filtered;
  }, [displayFindings, sortConfig, showAllFindings]);

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const getRiskBadgeClass = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'critical': return 'risk-badge critical';
      case 'high': return 'risk-badge high';
      case 'medium': return 'risk-badge medium';
      case 'low': return 'risk-badge low';
      default: return 'risk-badge unknown';
    }
  };

  const formatConfidenceScore = (score) => {
    return score ? `${score.toFixed(1)}%` : 'N/A';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) {
        console.warn('Invalid timestamp:', timestamp);
        return 'N/A';
      }
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Error formatting timestamp:', timestamp, error);
      return 'N/A';
    }
  };

  if (isLoading) {
    return (
      <div className="risk-findings-table loading">
        <div className="table-header">
          <div className="skeleton-bar large"></div>
        </div>
        <div className="table-content">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="skeleton-row">
              <div className="skeleton-cell"></div>
              <div className="skeleton-cell"></div>
              <div className="skeleton-cell"></div>
              <div className="skeleton-cell"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="risk-findings-table">
      {/* Header and Controls */}
      <div className="table-header">
        <div className="header-content">
          <h3>Risk Findings</h3>
          <p className="findings-count">
            Showing {processedFindings.length} of {displayFindings.length} findings
            {filteredFindings.length > 0 && ' (filtered results)'}
          </p>
        </div>
        <div className="header-actions">
          {/* Header actions can be used for other controls if needed */}
        </div>
      </div>

      {/* Enhanced Filters Section */}
      <div className="enhanced-filters">
        {/* Risk Level Dropdown */}
        <div className="filter-group">
          <label>Risk Level:</label>
          <select
            value={searchFilters.riskLevel}
            onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
            className="filter-select"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Sensitivity Dropdown */}
        <div className="filter-group">
          <label>Sensitivity:</label>
          <select
            value={searchFilters.sensitivity}
            onChange={(e) => handleFilterChange('sensitivity', e.target.value)}
            className="filter-select"
          >
            <option value="all">All Sensitivity</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Show 10/100 Dropdown */}
        {displayFindings.length > 10 && (
          <div className="filter-group">
            <label>Show:</label>
            <select
              value={showAllFindings ? 'all' : '10'}
              onChange={(e) => setShowAllFindings(e.target.value === 'all')}
              className="show-more-select"
            >
              <option value="10">10</option>
              <option value="all">All ({displayFindings.length})</option>
            </select>
          </div>
        )}

        {/* Reset Button */}
        {hasActiveFilters && (
          <div className="filter-group">
            <button
              className="reset-button"
              onClick={handleResetFilters}
              style={{
                padding: '8px 16px',
                backgroundColor: '#f3f4f6',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                color: '#374151'
              }}
            >
              Reset Filters
            </button>
          </div>
        )}

      </div>

      

      {/* Table */}
      <div className="table-container">
        {processedFindings.length === 0 ? (
          <div className="no-findings">
            <AlertTriangle size={48} />
            <h4>No Risk Findings</h4>
            {hasActiveFilters ? (
              <p>No findings match the selected filters. Try adjusting your search criteria or reset filters to see all data.</p>
            ) : (
              <p>No findings available. Use the search filters above to fetch data from the API.</p>
            )}
          </div>
        ) : (
          <table className="findings-table">
            <thead>
              <tr>
                <th 
                  onClick={() => handleSort('finding_id')}
                  className="sortable"
                >
                  <span>Finding ID</span>
                  {sortConfig.key === 'finding_id' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('data_value')}
                  className="sortable"
                >
                  <span>Data Value</span>
                  {sortConfig.key === 'data_value' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('sensitivity')}
                  className="sortable"
                >
                  <span>Sensitivity</span>
                  {sortConfig.key === 'sensitivity' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('finding_type')}
                  className="sortable"
                >
                  <span>Finding Type</span>
                  {sortConfig.key === 'finding_type' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('sde_category')}
                  className="sortable"
                >
                  <span>SDE Category</span>
                  {sortConfig.key === 'sde_category' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('risk_level')}
                  className="sortable"
                >
                  <span>Risk Level</span>
                  {sortConfig.key === 'risk_level' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('confidence_score')}
                  className="sortable"
                >
                  <span>Confidence Score</span>
                  {sortConfig.key === 'confidence_score' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
                <th 
                  onClick={() => handleSort('scan_timestamp')}
                  className="sortable"
                >
                  <span>Scan Timestamp</span>
                  {sortConfig.key === 'scan_timestamp' && (
                    sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </th>
              </tr>
            </thead>
            <tbody>
              {processedFindings.map((finding, index) => (
                <tr key={finding.finding_id || index} className="finding-row">
                  <td className="finding-id-cell">
                    {finding.finding_id || 'N/A'}
                  </td>
                  <td className="data-value-cell">
                    <div className="data-value-content">
                      <Globe size={14} />
                      <span>{finding.data_value || 'No Data'}</span>
                    </div>
                  </td>
                  <td className="sensitivity-cell">
                    <span className={`sensitivity-badge ${(finding.sensitivity || '').toLowerCase()}`}>
                      {finding.sensitivity || 'N/A'}
                    </span>
                  </td>
                  <td className="finding-type-cell">
                    {finding.finding_type || 'N/A'}
                  </td>
                  <td className="sde-category-cell">
                    <div className="category-content">
                      <Shield size={16} className="category-icon" />
                      <span>{finding.sde_category || 'Unknown'}</span>
                    </div>
                  </td>
                  <td className="risk-cell">
                    <span className={getRiskBadgeClass(finding.risk_level)}>
                      {finding.risk_level || 'Unknown'}
                    </span>
                  </td>
                  <td className="confidence-cell">
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill"
                        style={{ 
                          width: `${(finding.confidence_score || 0) * 100}%`,
                          backgroundColor: (finding.confidence_score || 0) > 0.8 ? '#10B981' : 
                                         (finding.confidence_score || 0) > 0.6 ? '#F59E0B' : '#EF4444'
                        }}
                      ></div>
                      <span className="confidence-text">
                        {formatConfidenceScore((finding.confidence_score || 0) * 100)}
                      </span>
                    </div>
                  </td>
                  <td className="timestamp-cell">
                    <div className="timestamp-content">
                      <Clock size={14} />
                      <span>{formatTimestamp(finding.scan_timestamp)}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default RiskFindingsTable;
