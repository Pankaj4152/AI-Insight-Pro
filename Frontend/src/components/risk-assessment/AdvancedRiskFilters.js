import React, { useState } from 'react';
import { 
  Filter, 
  Search, 
  RotateCcw, 
  Database, 
  AlertTriangle, 
  Shield, 
  Activity,
  ChevronDown
} from 'lucide-react';

function AdvancedRiskFilters({ filters, onFilterChange, onApplyFilters, onClearFilters, loading, dataSources }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeFilters, setActiveFilters] = useState(0);

  React.useEffect(() => {
    const count = Object.values(filters).filter(value => value && value.trim() !== '').length;
    setActiveFilters(count);
  }, [filters]);

  const handleFilterChange = (filterName, value) => {
    onFilterChange(filterName, value);
  };

  const filterOptions = {
    riskLevel: [
      { value: '', label: 'All Risk Levels' },
      { value: 'High', label: 'High Risk', color: '#EF4444' },
      { value: 'Medium', label: 'Medium Risk', color: '#F59E0B' },
      { value: 'Low', label: 'Low Risk', color: '#10B981' }
    ],
    sensitivity: [
      { value: '', label: 'All Sensitivity Levels' },
      { value: 'Highly Sensitive', label: 'Highly Sensitive', color: '#DC2626' },
      { value: 'Sensitive', label: 'Sensitive', color: '#EA580C' },
      { value: 'Medium', label: 'Medium Sensitivity', color: '#D97706' },
      { value: 'Low', label: 'Low Sensitivity', color: '#65A30D' }
    ],
    findingType: [
      { value: '', label: 'All Finding Types' },
      { value: 'Email', label: 'Email Addresses' },
      { value: 'Phone', label: 'Phone Numbers' },
      { value: 'SSN', label: 'Social Security Numbers' },
      { value: 'Credit Card', label: 'Credit Card Numbers' },
      { value: 'Address', label: 'Physical Addresses' },
      { value: 'Name', label: 'Personal Names' },
      { value: 'Date of Birth', label: 'Date of Birth' },
      { value: 'API Key', label: 'API Keys' },
      { value: 'Password', label: 'Passwords' }
    ]
  };

  return (
    <div className="advanced-risk-filters">
      <div className="filters-header">
        <div className="header-left">
          <Filter className="header-icon" />
          <h3 className="filters-title">Risk Filters</h3>
          {activeFilters > 0 && (
            <span className="active-filters-badge">
              {activeFilters} active
            </span>
          )}
        </div>
        <div className="header-actions">
          <button 
            className="expand-button"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
          >
            <ChevronDown 
              className={`expand-icon ${isExpanded ? 'rotated' : ''}`} 
            />
          </button>
        </div>
      </div>

      <div className={`filters-content ${isExpanded ? 'expanded' : 'collapsed'}`}>
        <div className="filters-grid">
          {/* Data Source Filter */}
          <div className="filter-group">
            <label className="filter-label">
              <Database className="label-icon" />
              Data Source
            </label>
            <select 
              className="filter-select"
              value={filters.dataSource || ''}
              onChange={(e) => handleFilterChange('dataSource', e.target.value)}
            >
              <option value="">All Data Sources</option>
              {dataSources.map((source, index) => (
                <option key={index} value={source.name}>
                  {source.name} ({source.type})
                </option>
              ))}
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="filter-group">
            <label className="filter-label">
              <AlertTriangle className="label-icon" />
              Risk Level
            </label>
            <select 
              className="filter-select"
              value={filters.riskLevel || ''}
              onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
            >
              {filterOptions.riskLevel.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Sensitivity Filter */}
          <div className="filter-group">
            <label className="filter-label">
              <Shield className="label-icon" />
              Sensitivity Level
            </label>
            <select 
              className="filter-select"
              value={filters.sensitivity || ''}
              onChange={(e) => handleFilterChange('sensitivity', e.target.value)}
            >
              {filterOptions.sensitivity.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Finding Type Filter */}
          <div className="filter-group">
            <label className="filter-label">
              <Activity className="label-icon" />
              Finding Type
            </label>
            <select 
              className="filter-select"
              value={filters.findingType || ''}
              onChange={(e) => handleFilterChange('findingType', e.target.value)}
            >
              {filterOptions.findingType.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Search Filter */}
          <div className="filter-group search-group">
            <label className="filter-label">
              <Search className="label-icon" />
              Search
            </label>
            <input
              type="text"
              className="filter-input"
              placeholder="Search findings..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          {/* Date Range Filter */}
          <div className="filter-group">
            <label className="filter-label">
              Scan Date Range
            </label>
            <div className="date-range-inputs">
              <input
                type="date"
                className="filter-input date-input"
                value={filters.startDate || ''}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
              />
              <span className="date-separator">to</span>
              <input
                type="date"
                className="filter-input date-input"
                value={filters.endDate || ''}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="filters-actions">
          <button 
            className="apply-filters-btn"
            onClick={onApplyFilters}
            disabled={loading}
          >
            <Search className="button-icon" />
            {loading ? 'Applying...' : 'Apply Filters'}
          </button>
          <button 
            className="clear-filters-btn"
            onClick={onClearFilters}
            disabled={loading || activeFilters === 0}
          >
            <RotateCcw className="button-icon" />
            Clear All
          </button>
        </div>

        {activeFilters > 0 && (
          <div className="active-filters-summary">
            <h4>Active Filters:</h4>
            <div className="filter-tags">
              {Object.entries(filters).map(([key, value]) => {
                if (!value || value.trim() === '') return null;
                return (
                  <span key={key} className="filter-tag">
                    {getFilterDisplayName(key)}: {value}
                    <button 
                      className="remove-filter"
                      onClick={() => handleFilterChange(key, '')}
                    >
                      ×
                    </button>
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getFilterDisplayName(key) {
  const displayNames = {
    dataSource: 'Data Source',
    riskLevel: 'Risk Level',
    sensitivity: 'Sensitivity',
    findingType: 'Finding Type',
    search: 'Search',
    startDate: 'Start Date',
    endDate: 'End Date'
  };
  return displayNames[key] || key;
}

export default AdvancedRiskFilters;
