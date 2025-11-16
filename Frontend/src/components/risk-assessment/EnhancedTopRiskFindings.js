// src/components/risk-assessment/EnhancedTopRiskFindings.js
import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  AlertTriangle, 
  Eye, 
  MapPin, 
  Clock,
  Shield,
  Database,
  FileText
} from 'lucide-react';

const EnhancedTopRiskFindings = ({ findings, loading }) => {
    const [sortConfig, setSortConfig] = useState({ key: 'risk_level', direction: 'desc' });
    const [filterConfig, setFilterConfig] = useState({
        risk_level: '',
        finding_type: '',
        status: '',
        data_store: ''
    });
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);

    // Get unique values for filter dropdowns
    const uniqueValues = useMemo(() => {
        if (!findings || findings.length === 0) return {};

        return {
            risk_levels: [...new Set(findings.map(f => f.risk_level))],
            finding_types: [...new Set(findings.map(f => f.finding_type))],
            statuses: [...new Set(findings.map(f => f.status))],
            data_stores: [...new Set(findings.map(f => f.data_store))]
        };
    }, [findings]);

    // Sort and filter data
    const processedFindings = useMemo(() => {
        if (!findings || findings.length === 0) return [];

        let filtered = findings.filter(finding => {
            return Object.entries(filterConfig).every(([key, value]) => {
                if (!value) return true;
                return finding[key] === value;
            });
        });

        // Sort data
        filtered.sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];

            if (sortConfig.key === 'risk_level') {
                const riskOrder = { 'High': 3, 'Medium': 2, 'Low': 1, 'Informational': 0 };
                const comparison = riskOrder[aValue] - riskOrder[bValue];
                return sortConfig.direction === 'asc' ? comparison : -comparison;
            }

            if (typeof aValue === 'number' && typeof bValue === 'number') {
                return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
            }

            const comparison = String(aValue).localeCompare(String(bValue));
            return sortConfig.direction === 'asc' ? comparison : -comparison;
        });

        return filtered;
    }, [findings, sortConfig, filterConfig]);

    // Pagination
    const paginatedFindings = useMemo(() => {
        const startIndex = (currentPage - 1) * itemsPerPage;
        return processedFindings.slice(startIndex, startIndex + itemsPerPage);
    }, [processedFindings, currentPage, itemsPerPage]);

    const totalPages = Math.ceil(processedFindings.length / itemsPerPage);

    const handleSort = (key) => {
        setSortConfig(current => ({
            key,
            direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const handleFilter = (key, value) => {
        setFilterConfig(current => ({ ...current, [key]: value }));
        setCurrentPage(1); // Reset to first page when filtering
    };

    const clearFilters = () => {
        setFilterConfig({
            risk_level: '',
            finding_type: '',
            status: '',
            data_store: ''
        });
        setCurrentPage(1);
    };

    const getRiskLevelClass = (riskLevel) => {
        switch (riskLevel?.toLowerCase()) {
            case 'high': return 'risk-high';
            case 'medium': return 'risk-medium';
            case 'low': return 'risk-low';
            default: return 'risk-info';
        }
    };

    const getStatusClass = (status) => {
        switch (status?.toLowerCase()) {
            case 'active': return 'status-active';
            case 'resolved': return 'status-resolved';
            case 'under review': return 'status-review';
            case 'acknowledged': return 'status-acknowledged';
            default: return 'status-info';
        }
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return 'N/A';
        return new Date(timestamp).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="enhanced-findings-table">
                <h3>Top Risk Findings</h3>
                <div className="table-loading">
                    <div className="table-skeleton">
                        {[...Array(5)].map((_, index) => (
                            <div key={index} className="table-row-skeleton">
                                <div className="cell-skeleton"></div>
                                <div className="cell-skeleton"></div>
                                <div className="cell-skeleton"></div>
                                <div className="cell-skeleton"></div>
                                <div className="cell-skeleton"></div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="enhanced-findings-table">
            <div className="table-header">
                <h3>Top Risk Findings</h3>
                <div className="table-summary">
                    Showing {paginatedFindings.length} of {processedFindings.length} findings
                    {processedFindings.length !== findings?.length && ` (filtered from ${findings?.length} total)`}
                </div>
            </div>

            {/* Filters */}
            <div className="table-filters">
                <div className="filter-group">
                    <label>Risk Level:</label>
                    <select
                        value={filterConfig.risk_level}
                        onChange={(e) => handleFilter('risk_level', e.target.value)}
                    >
                        <option value="">All</option>
                        {uniqueValues.risk_levels?.map(level => (
                            <option key={level} value={level}>{level}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label>Finding Type:</label>
                    <select
                        value={filterConfig.finding_type}
                        onChange={(e) => handleFilter('finding_type', e.target.value)}
                    >
                        <option value="">All</option>
                        {uniqueValues.finding_types?.map(type => (
                            <option key={type} value={type}>{type}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label>Status:</label>
                    <select
                        value={filterConfig.status}
                        onChange={(e) => handleFilter('status', e.target.value)}
                    >
                        <option value="">All</option>
                        {uniqueValues.statuses?.map(status => (
                            <option key={status} value={status}>{status}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label>Data Store:</label>
                    <select
                        value={filterConfig.data_store}
                        onChange={(e) => handleFilter('data_store', e.target.value)}
                    >
                        <option value="">All</option>
                        {uniqueValues.data_stores?.map(store => (
                            <option key={store} value={store}>{store}</option>
                        ))}
                    </select>
                </div>

                <button className="clear-filters-btn" onClick={clearFilters}>
                    Clear Filters
                </button>
            </div>

            {/* Table */}
            <div className="table-container">
                <table className="findings-table">
                    <thead>
                        <tr>
                            <th onClick={() => handleSort('finding_type')} className="sortable">
                                Finding Type
                                {sortConfig.key === 'finding_type' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                            <th onClick={() => handleSort('location')} className="sortable">
                                Location
                                {sortConfig.key === 'location' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                            <th onClick={() => handleSort('risk_level')} className="sortable">
                                Risk Level
                                {sortConfig.key === 'risk_level' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                            <th onClick={() => handleSort('confidence')} className="sortable">
                                Confidence
                                {sortConfig.key === 'confidence' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                            <th onClick={() => handleSort('count')} className="sortable">
                                Count
                                {sortConfig.key === 'count' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                            <th onClick={() => handleSort('last_detected')} className="sortable">
                                Last Detected
                                {sortConfig.key === 'last_detected' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                            <th onClick={() => handleSort('status')} className="sortable">
                                Status
                                {sortConfig.key === 'status' && (
                                    <span className={`sort-indicator ${sortConfig.direction}`}>
                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                )}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedFindings.length > 0 ? (
                            paginatedFindings.map((finding, index) => (
                                <tr key={finding.id || index}>
                                    <td className="finding-type">{finding.finding_type}</td>
                                    <td className="location" title={finding.location}>{finding.location}</td>
                                    <td>
                                        <span className={`risk-badge ${getRiskLevelClass(finding.risk_level)}`}>
                                            {finding.risk_level}
                                        </span>
                                    </td>
                                    <td className="confidence">{finding.confidence}%</td>
                                    <td className="count">{finding.count?.toLocaleString()}</td>
                                    <td className="date">{formatDate(finding.last_detected)}</td>
                                    <td>
                                        <span className={`status-badge ${getStatusClass(finding.status)}`}>
                                            {finding.status}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="7" className="no-data">
                                    {findings?.length === 0 ? 'No findings available' : 'No findings match the current filters'}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        className="pagination-btn"
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage(1)}
                    >
                        First
                    </button>
                    <button
                        className="pagination-btn"
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage(currentPage - 1)}
                    >
                        Previous
                    </button>

                    <div className="pagination-info">
                        Page {currentPage} of {totalPages}
                    </div>

                    <button
                        className="pagination-btn"
                        disabled={currentPage === totalPages}
                        onClick={() => setCurrentPage(currentPage + 1)}
                    >
                        Next
                    </button>
                    <button
                        className="pagination-btn"
                        disabled={currentPage === totalPages}
                        onClick={() => setCurrentPage(totalPages)}
                    >
                        Last
                    </button>
                </div>
            )}
        </div>
    );
}

// Helper functions
function getRiskClass(riskLevel) {
    if (!riskLevel) return 'unknown';
    const level = riskLevel.toLowerCase();
    if (level.includes('high') || level.includes('critical')) return 'critical';
    if (level.includes('medium') || level.includes('moderate')) return 'medium';
    if (level.includes('low')) return 'low';
    return 'unknown';
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    return 'Recently';
}

function truncateValue(value, maxLength = 30) {
    if (!value) return 'N/A';
    if (value.length <= maxLength) return value;
    return `${value.substring(0, maxLength)}...`;
}

function calculateAverageConfidence(findings) {
    const withConfidence = findings.filter(f => f.confidence_score);
    if (withConfidence.length === 0) return 0;
    const sum = withConfidence.reduce((acc, f) => acc + (f.confidence_score || 0), 0);
    return Math.round(sum / withConfidence.length);
}

function handleInvestigate(finding) {
    console.log('Investigating finding:', finding);
    // Add investigation logic here
}

function handleRemediate(finding) {
    console.log('Remediating finding:', finding);
    // Add remediation logic here
}

export default EnhancedTopRiskFindings;
