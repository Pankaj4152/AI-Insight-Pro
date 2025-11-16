import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/apiIntegration';
import '../Css/Discover.css';

function DiscoverPage() {
  const [discoveryResults, setDiscoveryResults] = useState(null);
  const [discoveredObjects, setDiscoveredObjects] = useState([]);
  const [selectedObjects, setSelectedObjects] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanResults, setScanResults] = useState(null);
  const [submissionMessage, setSubmissionMessage] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [groupByStore, setGroupByStore] = useState(true);
  const [filterByType, setFilterByType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedStores, setCollapsedStores] = useState(new Set());
  const navigate = useNavigate();

  const clientId = JSON.parse(localStorage.getItem('user') || '{}').client_id || localStorage.getItem('client_id');

  useEffect(() => {
    loadDiscoveryData();
  }, []);

  // Prevent body scroll when scanning modal is open
  useEffect(() => {
    if (scanning) {
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
    } else {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    }
    
    // Cleanup on unmount
    return () => {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    };
  }, [scanning]);

  const loadDiscoveryData = async () => {
    setLoading(true);
    try {
      // First check if we have discovery results from the connection process
      const storedResults = localStorage.getItem('discoveryResults');
      if (storedResults) {
        const results = JSON.parse(storedResults);
        setDiscoveryResults(results);
      }

      // Fetch discovered objects
      if (clientId) {
        await fetchDiscoveredObjects();
      }
    } catch (error) {
      console.error('Error loading discovery data:', error);
      setSubmissionMessage('Error loading discovery data');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    } finally {
      setLoading(false);
    }
  };

  // Add debug function to window for manual testing
  useEffect(() => {
    window.debugDiscover = {
      testSaveSelection: async () => {
        console.log('=== Manual Test Save Selection ===');
        console.log('Client ID:', clientId);
        console.log('Current selections:', Array.from(selectedObjects));
        console.log('Available objects:', discoveredObjects.length);

        // Create test data if no selections
        let testFiles;
        if (selectedObjects.size === 0 && discoveredObjects.length > 0) {
          // Use first available object for testing
          const testObj = discoveredObjects[0];
          testFiles = [{
            file_name: testObj.name,
            store_id: testObj.store_id,
            object_id: testObj.object_id
          }];
          console.log('Using test data:', testFiles);
        } else {
          // Use actual selections
          testFiles = Array.from(selectedObjects).map(objectId => {
            const obj = discoveredObjects.find(o => o.object_id === objectId);
            return obj ? {
              file_name: obj.name,
              store_id: obj.store_id,
              object_id: objectId
            } : null;
          }).filter(file => file !== null);
        }

        try {
          const result = await api.scan.saveSelection(testFiles, clientId);
          console.log('Test save selection result:', result);
          return result;
        } catch (error) {
          console.error('Test save selection error:', error);
          return { success: false, error: error.message };
        }
      },
      currentState: () => {
        console.log('=== Current Discover State ===');
        console.log('Client ID:', clientId);
        console.log('Selected objects:', Array.from(selectedObjects));
        console.log('Total discovered objects:', discoveredObjects.length);
        console.log('First few objects:', discoveredObjects.slice(0, 3));
      }
    };
  }, [selectedObjects, discoveredObjects, clientId]);

  const fetchDiscoveredObjects = async () => {
    try {
      const response = await fetch(`https://agents-1071432896229.asia-south2.run.app/discovered-objects/${clientId}`);
      if (response.ok) {
        const data = await response.json();
        setDiscoveredObjects(data.objects || []);
      } else {
        throw new Error('Failed to fetch discovered objects');
      }
    } catch (error) {
      console.error('Error fetching discovered objects:', error);
      setSubmissionMessage('Error fetching discovered objects');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    }
  };

  const handleObjectSelection = (objectId, checked) => {
    const newSelected = new Set(selectedObjects);
    if (checked) {
      newSelected.add(objectId);
    } else {
      newSelected.delete(objectId);
    }
    setSelectedObjects(newSelected);
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      const filteredObjects = getFilteredObjects();
      const allIds = new Set(filteredObjects.map(obj => obj.object_id));
      setSelectedObjects(allIds);
    } else {
      setSelectedObjects(new Set());
    }
  };

  const getFilteredObjects = () => {
    let filtered = discoveredObjects;

    // Filter by type
    if (filterByType !== 'all') {
      filtered = filtered.filter(obj => obj.type === filterByType);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(obj => 
        obj.name.toLowerCase().includes(query) ||
        obj.path.toLowerCase().includes(query)
      );
    }

    return filtered;
  };

  const groupObjectsByStore = (objects) => {
    const grouped = {};
    objects.forEach(obj => {
      const storeId = obj.store_id;
      if (!grouped[storeId]) {
        grouped[storeId] = [];
      }
      grouped[storeId].push(obj);
    });
    return grouped;
  };

  const runScan = async (scanType = 'selected') => {
    if (scanType === 'selected' && selectedObjects.size === 0) {
      setSubmissionMessage('Please select at least one object to scan');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
      return;
    }

    setScanning(true);
    setScanProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setScanProgress(prev => Math.min(prev + Math.random() * 15 + 5, 95));
    }, 500);

    try {
      let endpoint = '';
      let requestBody = { client_id: clientId };

      // If objects are selected, save them first then use scan-selected-only
      if (scanType === 'selected' && selectedObjects.size > 0) {
        // First, save the selected objects
        await saveSelectedObjects();
        endpoint = '/scan-selected-only';
      } else {
        switch (scanType) {
          case 'latest':
            endpoint = '/scan-latest';
            break;
          case 'all':
            endpoint = '/scan-all';
            break;
          default:
            endpoint = '/scan-latest';
        }
      }

      const response = await fetch(`https://agents-1071432896229.asia-south2.run.app${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      clearInterval(progressInterval);
      setScanProgress(100);

      if (response.ok) {
        const results = await response.json();
        setScanResults(results);
        setSubmissionMessage(`Scan completed successfully! Found ${results.results?.total_findings || 0} findings.`);
        
        // Store scan results for potential use in other pages
        localStorage.setItem('scanResults', JSON.stringify(results));
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Scan failed');
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Scan error:', error);
      setSubmissionMessage(`Scan failed: ${error.message}`);
    } finally {
      setScanning(false);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 4000);
    }
  };

  const saveSelectedObjects = async () => {
    try {
      if (selectedObjects.size === 0) {
        setSubmissionMessage('Please select at least one file to save');
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
        return;
      }

      // Convert selected object IDs to the format expected by the API
      const selectedFiles = Array.from(selectedObjects).map(objectId => {
        const obj = discoveredObjects.find(o => o.object_id === objectId);
        if (!obj) {
          console.warn(`Object with ID ${objectId} not found`);
          return null;
        }
        return {
          file_name: obj.name,  // Use 'file_name' as per API spec
          store_id: obj.store_id,
          object_id: objectId
        };
      }).filter(file => file !== null);

      console.log('=== Save Selection Debug Info ===');
      console.log('Client ID:', clientId);
      console.log('Selected files to save:', selectedFiles);
      console.log('Total files selected:', selectedFiles.length);

      // Call the new save-selection API endpoint
      const result = await api.scan.saveSelection(selectedFiles, clientId);
      
      console.log('=== Save Selection API Response ===');
      console.log('Full result:', result);
      console.log('Success:', result.success);
      console.log('Data:', result.data);

      if (result.success && result.data) {
        const { 
          saved_count = 0, 
          duplicate_count = 0, 
          error_count = 0,
          scan_session_id,
          message
        } = result.data;

        // Show detailed success message
        let successMessage = `Successfully saved ${saved_count} file selections`;
        if (duplicate_count > 0) {
          successMessage += ` (${duplicate_count} duplicates skipped)`;
        }
        if (error_count > 0) {
          successMessage += ` (${error_count} errors)`;
        }

        setSubmissionMessage(successMessage);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 4000);

        // Also store locally as backup
        localStorage.setItem('selectedObjects', JSON.stringify({
          client_id: clientId,
          selected_files: selectedFiles,
          scan_session_id: scan_session_id,
          selection_timestamp: new Date().toISOString(),
          saved_count: saved_count
        }));

        console.log('Selection saved successfully:', {
          scan_session_id,
          saved_count,
          duplicate_count,
          error_count
        });

      } else {
        // Handle API failure
        const errorMessage = result.data?.message || result.error || 'Failed to save file selections';
        console.error('Save selection API failed:', errorMessage);
        
        setSubmissionMessage(`Error: ${errorMessage}`);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 4000);

        // Still save locally as fallback
        localStorage.setItem('selectedObjects', JSON.stringify({
          client_id: clientId,
          selected_files: selectedFiles,
          selection_timestamp: new Date().toISOString(),
          status: 'local_fallback'
        }));
      }

    } catch (error) {
      console.error('Error saving selected objects:', error);
      setSubmissionMessage(`Error saving selections: ${error.message}`);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 4000);
      
      // Save locally as fallback
      try {
        const selectedFiles = Array.from(selectedObjects).map(objectId => {
          const obj = discoveredObjects.find(o => o.object_id === objectId);
          return obj ? {
            file_name: obj.name,
            store_id: obj.store_id,
            object_id: objectId
          } : null;
        }).filter(file => file !== null);

        localStorage.setItem('selectedObjects', JSON.stringify({
          client_id: clientId,
          selected_files: selectedFiles,
          selection_timestamp: new Date().toISOString(),
          status: 'error_fallback'
        }));
      } catch (fallbackError) {
        console.error('Even fallback save failed:', fallbackError);
      }
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getFileTypeIcon = (extension) => {
    switch (extension?.toLowerCase()) {
      case 'csv': return '📄';
      case 'json': return '📋';
      case 'xlsx': case 'xls': return '📊';
      case 'pdf': return '📕';
      case 'txt': return '📝';
      case 'sql': return '🗃️';
      default: return '📄';
    }
  };

  const toggleStoreCollapse = (storeId) => {
    const newCollapsed = new Set(collapsedStores);
    if (newCollapsed.has(storeId)) {
      newCollapsed.delete(storeId);
    } else {
      newCollapsed.add(storeId);
    }
    setCollapsedStores(newCollapsed);
  };

  const collapseAllStores = () => {
    const allStoreIds = new Set(Object.keys(groupObjectsByStore(filteredObjects)));
    setCollapsedStores(allStoreIds);
  };

  const expandAllStores = () => {
    setCollapsedStores(new Set());
  };

  const getStoreDisplayName = (storeId, objects) => {
    if (!objects || objects.length === 0) return `Store ${storeId}`;
    
    // Get the first object to determine store type and extract meaningful name
    const firstObject = objects[0];
    const path = firstObject.path || '';
    const storePath = firstObject.store_path || '';
    const objectType = firstObject.type || '';
    
    // Debug logging for PostgreSQL and database connections
    if (path.includes('postgresql') || path.includes('postgres') || 
        firstObject.dataset_id || objectType.toLowerCase().includes('postgres')) {
      console.log('Database Debug Info:', {
        storeId,
        path,
        storePath,
        objectType,
        objectName: firstObject.name,
        dataset_id: firstObject.dataset_id,
        dataset_id_parts: firstObject.dataset_id ? firstObject.dataset_id.split('.') : null,
        is_postgres_format: firstObject.dataset_id ? firstObject.dataset_id.includes('.public.') : false,
        allObjectFields: Object.keys(firstObject)
      });
    }
    
    // Try to extract meaningful names based on path patterns
    if (path.includes('gs://')) {
      // Google Cloud Storage bucket
      const bucketMatch = path.match(/gs:\/\/([^\/]+)/);
      if (bucketMatch) {
        return `GCS Bucket: ${bucketMatch[1]}`;
      }
    } 
    else if (path.includes('postgresql://') || path.includes('postgres://') || 
             (firstObject.dataset_id && firstObject.dataset_id.includes('.public.'))) {
      // PostgreSQL database - use dataset_id if available, otherwise parse URL
      if (firstObject.dataset_id) {
        // For PostgreSQL format: database.schema.table, extract just the database name
        const dbName = firstObject.dataset_id.split('.')[0];
        return `PostgreSQL DB: ${dbName}`;
      }
      // Extract database name from PostgreSQL URL: postgresql://user:pass@host:port/database
      const dbMatch = path.match(/postgresql:\/\/[^\/]+\/([^\/\?&]+)/) ||
                     path.match(/postgres:\/\/[^\/]+\/([^\/\?&]+)/) ||
                     path.match(/\/([^\/\?&]+)$/) ||  // Last part after final slash
                     path.match(/dbname=([^;&]+)/i) ||
                     path.match(/database=([^;&]+)/i);
      if (dbMatch) {
        return `PostgreSQL DB: ${dbMatch[1]}`;
      }
    } else if (path.includes('mssql://') || path.includes('sqlserver://') || 
               (objectType && objectType.includes('database')) ||
               (path.includes('.dbo.') && !path.includes('bigquery'))) {
      // SQL Server database - use dataset_id if available
      if (firstObject.dataset_id) {
        return `SQL Server DB: ${firstObject.dataset_id}`;
      }
      // Fallback to path parsing
      const dbMatch = path.match(/\/([^\/]+)$/) || 
                     path.match(/database=([^;]+)/i) ||
                     path.match(/\/([^\/]+)\.dbo\./) ||
                     storePath.match(/\/([^\/]+)$/);
      if (dbMatch) {
        return `SQL Server DB: ${dbMatch[1]}`;
      }
    } else if (path.includes('mysql://')) {
      // MySQL database - use dataset_id if available
      if (firstObject.dataset_id) {
        return `MySQL DB: ${firstObject.dataset_id}`;
      }
      // Fallback to path parsing
      const dbMatch = path.match(/\/([^\/\?]+)/) ||
                     path.match(/database=([^;]+)/i);
      if (dbMatch) {
        return `MySQL DB: ${dbMatch[1]}`;
      }
    } else if (path.includes('bigquery') || 
               (firstObject.dataset_id && firstObject.dataset_id.includes('.') && !firstObject.dataset_id.includes('.public.'))) {
      // BigQuery dataset - remove only the last segment (table name)
      if (firstObject.dataset_id) {
        const parts = firstObject.dataset_id.split('.');
        if (parts.length > 1) {
          // Remove only the last part (table name) and keep the rest
          const datasetName = parts.slice(0, -1).join('.');
          return `BigQuery Dataset: ${datasetName}`;
        }
        return `BigQuery Dataset: ${firstObject.dataset_id}`;
      }
      // Fallback to path parsing for BigQuery
      const bqMatch = path.match(/([^\/]+\.[^\/]+)(?:\.[^\/]+)?$/);
      if (bqMatch) {
        const parts = bqMatch[1].split('.');
        const datasetName = parts.length > 1 ? parts.slice(0, -1).join('.') : bqMatch[1];
        return `BigQuery Dataset: ${datasetName}`;
      }
    } else if (firstObject.dataset_id && 
               (firstObject.dataset_id.includes('bigquery') || 
                path.includes('bigquery') || 
                objectType.toLowerCase().includes('bigquery'))) {
      // BigQuery dataset - remove only the last segment (table name)
      const datasetPath = firstObject.dataset_id;
      const parts = datasetPath.split('.');
      if (parts.length > 2) {
        // Keep project.dataset, remove table name (last part)
        const projectDataset = parts.slice(0, -1).join('.');
        return `BigQuery Dataset: ${projectDataset}`;
      } else {
        return `BigQuery Dataset: ${datasetPath}`;
      }
    } else if (path.includes('s3://')) {
      // Amazon S3 bucket
      const bucketMatch = path.match(/s3:\/\/([^\/]+)/);
      if (bucketMatch) {
        return `S3 Bucket: ${bucketMatch[1]}`;
      }
    } else if (path.includes('azure://') || path.includes('blob.core.windows.net')) {
      // Azure Blob Storage
      const containerMatch = path.match(/\/([^\/]+)\//) ||
                           path.match(/blob\.core\.windows\.net\/([^\/]+)/);
      if (containerMatch) {
        return `Azure Container: ${containerMatch[1]}`;
      }
    } else if (path.startsWith('/') || path.includes('file://')) {
      // File system path
      const pathParts = path.replace('file://', '').split('/').filter(Boolean);
      if (pathParts.length > 0) {
        return `File System: ${pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2] || 'Root'}`;
      }
    }
    
    // Fallback: try to extract any meaningful identifier from the path
    const pathParts = path.split('/').filter(part => part && part !== '');
    if (pathParts.length > 0) {
      // Take the first meaningful part (skip protocols)
      const meaningfulPart = pathParts.find(part => 
        !part.includes('://') && 
        part.length > 1 && 
        !part.match(/^[a-f0-9-]{30,}$/i) // Skip long hash-like strings
      );
      if (meaningfulPart) {
        return `Data Store: ${meaningfulPart}`;
      }
    }
    
    // Final fallback: return store ID with prefix
    return `Store: ${storeId}`;
  };

  // Always show the header, only show loading state for content
  const renderLoadingContent = () => (
    <div className="loading-container">
      <div className="loading-content">
        <div className="loading-spinner-wrapper">
          <div className="professional-spinner">
            <div className="spinner-circle"></div>
            <div className="spinner-circle"></div>
            <div className="spinner-circle"></div>
          </div>
        </div>
        <div className="loading-text">
          <h3>Loading Discovery Data</h3>
          <p>Please wait while we gather your data source information...</p>
        </div>
      </div>
    </div>
  );

  const filteredObjects = getFilteredObjects();
  const groupedObjects = groupByStore ? groupObjectsByStore(filteredObjects) : null;
  const fileTypes = [...new Set(discoveredObjects.map(obj => obj.type))];

  return (
    <div className="discover-page">
      <div className="discover-container">
        {/* Header - Always visible */}
        <div className="discover-header">
          <h1 className="page-title">Data Discovery</h1>
          <p className="description-text">
            Review discovered data sources and select objects for security scanning.
          </p>
        </div>

        {/* Show loading state only for content, not the header */}
        {loading ? renderLoadingContent() : (
          <>
            {/* Discovery Summary */}
            {discoveryResults && (
              <div className="discovery-summary-container">
                <h2 className="container-title">Discovery Summary</h2>
                <div className="summary-grid">
                  <div className="summary-card">
                    <div className="summary-icon">🏢</div>
                    <div className="summary-content">
                      <h3>{discoveryResults.results?.total_sources || 0}</h3>
                      <p>Data Sources Found</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">📄</div>
                    <div className="summary-content">
                      <h3>{discoveredObjects.length}</h3>
                      <p>Objects Discovered</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">✅</div>
                    <div className="summary-content">
                      <h3>{selectedObjects.size}</h3>
                      <p>Objects Selected</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">💾</div>
                    <div className="summary-content">
                      <h3>{formatFileSize(discoveredObjects.reduce((sum, obj) => sum + (obj.size_bytes || 0), 0))}</h3>
                      <p>Total Size</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

        {/* Controls */}
        <div className="controls-container">
          <h2 className="container-title">Discovered Objects</h2>
          
          <div className="controls-row">
            <div className="search-controls">
              <input
                type="text"
                placeholder="Search by name or path..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <select
                value={filterByType}
                onChange={(e) => setFilterByType(e.target.value)}
                className="filter-select"
              >
                <option value="all">All Types</option>
                {fileTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="view-controls">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={groupByStore}
                  onChange={(e) => setGroupByStore(e.target.checked)}
                />
                Group by Store
              </label>
              {groupByStore && filteredObjects.length > 0 && (
                <div className="store-controls">
                  <button 
                    onClick={expandAllStores}
                    className="store-control-button"
                    title="Expand all stores"
                  >
                    Expand All
                  </button>
                  <button 
                    onClick={collapseAllStores}
                    className="store-control-button"
                    title="Collapse all stores"
                  >
                    Collapse All
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="selection-controls">
            <label className="select-all-label">
              <input
                type="checkbox"
                checked={filteredObjects.length > 0 && filteredObjects.every(obj => selectedObjects.has(obj.object_id))}
                onChange={(e) => handleSelectAll(e.target.checked)}
              />
              Select All ({filteredObjects.length} objects)
            </label>

            <div className="selection-actions">
              <button
                onClick={saveSelectedObjects}
                disabled={selectedObjects.size === 0}
                className="save-button"
              >
                Save Selection ({selectedObjects.size})
              </button>
              <div className="scan-buttons">
                <button
                  onClick={() => runScan('selected')}
                  disabled={scanning || selectedObjects.size === 0}
                  className="scan-button primary"
                  title="Scan only the selected objects"
                >
                  {scanning ? 'Scanning...' : `Scan Selected (${selectedObjects.size})`}
                </button>
                {/* <button
                  onClick={() => runScan('latest')}
                  disabled={scanning}
                  className="scan-button secondary"
                  title="Intelligent scan - uses selected objects if available, otherwise scans latest"
                >
                  Smart Scan
                </button> */}
                <button
                  onClick={() => runScan('all')}
                  disabled={scanning}
                  className="scan-button secondary"
                  title="Force full scan of all databases"
                >
                  Full Scan
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Objects List */}
        <div className="objects-container">
          {filteredObjects.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h3>No Objects Found</h3>
              <p>No objects match your current filters. Try adjusting your search criteria.</p>
            </div>
          ) : groupByStore ? (
            Object.entries(groupedObjects).map(([storeId, objects]) => {
              const isCollapsed = collapsedStores.has(storeId);
              const selectedInStore = objects.filter(obj => selectedObjects.has(obj.object_id)).length;
              
              return (
                <div key={storeId} className="store-group">
                  <div 
                    className="store-header" 
                    onClick={() => toggleStoreCollapse(storeId)}
                    title={`Click to ${isCollapsed ? 'expand' : 'collapse'} store. Path: ${objects[0]?.path || 'N/A'}`}
                  >
                    <h3 className="store-title">
                      <span className={`collapse-icon ${isCollapsed ? 'collapsed' : 'expanded'}`}>
                        {isCollapsed ? '▶' : '▼'}
                      </span>
                      <span className="store-name">{getStoreDisplayName(storeId, objects)}</span>
                      <span className="store-id">(ID: {storeId})</span>
                      <span className="store-stats">
                        - {objects.length} objects
                        {selectedInStore > 0 && `, ${selectedInStore} selected`}
                      </span>
                    </h3>
                  </div>
                  {!isCollapsed && (
                  <div className="objects-grid">
                    {objects.map(obj => (
                      <div key={obj.object_id} className={`object-card ${selectedObjects.has(obj.object_id) ? 'selected' : ''}`}>
                        <label className="object-label">
                          <input
                            type="checkbox"
                            checked={selectedObjects.has(obj.object_id)}
                            onChange={(e) => handleObjectSelection(obj.object_id, e.target.checked)}
                            className="object-checkbox"
                          />
                          <div className="object-content">
                            <div className="object-header">
                              <span className="file-icon">{getFileTypeIcon(obj.file_extension)}</span>
                              <span className="object-name" title={obj.name}>{obj.name}</span>
                            </div>
                            <div className="object-details">
                              <span className="object-size">{formatFileSize(obj.size_bytes || 0)}</span>
                              <span className="object-type">{obj.type}</span>
                              <span className={`object-status ${obj.is_accessible ? 'accessible' : 'inaccessible'}`}>
                                {obj.is_accessible ? '✅ Accessible' : '❌ Inaccessible'}
                              </span>
                            </div>
                            <div className="object-path" title={obj.path}>{obj.path}</div>
                            {obj.last_modified && (
                              <div className="object-modified">Modified: {formatDate(obj.last_modified)}</div>
                            )}
                          </div>
                        </label>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              );
            })
          ) : (
            <div className="objects-grid">
              {filteredObjects.map(obj => (
                <div key={obj.object_id} className={`object-card ${selectedObjects.has(obj.object_id) ? 'selected' : ''}`}>
                  <label className="object-label">
                    <input
                      type="checkbox"
                      checked={selectedObjects.has(obj.object_id)}
                      onChange={(e) => handleObjectSelection(obj.object_id, e.target.checked)}
                      className="object-checkbox"
                    />
                    <div className="object-content">
                      <div className="object-header">
                        <span className="file-icon">{getFileTypeIcon(obj.file_extension)}</span>
                        <span className="object-name" title={obj.name}>{obj.name}</span>
                      </div>
                      <div className="object-details">
                        <span className="object-size">{formatFileSize(obj.size_bytes || 0)}</span>
                        <span className="object-type">{obj.type}</span>
                        <span className={`object-status ${obj.is_accessible ? 'accessible' : 'inaccessible'}`}>
                          {obj.is_accessible ? '✅ Accessible' : '❌ Inaccessible'}
                        </span>
                      </div>
                      <div className="object-path" title={obj.path}>{obj.path}</div>
                      {obj.last_modified && (
                        <div className="object-modified">Modified: {formatDate(obj.last_modified)}</div>
                      )}
                    </div>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Scan Results */}
        {scanResults && (
          <div className="scan-results-container">
            <h2 className="container-title">
              Scan Results 
              <span className="scan-type-badge">{scanResults.scan_type.replace(/_/g, ' ').toUpperCase()}</span>
            </h2>
            <div className="scan-results-summary">
              {/* <div className="result-item">
                <strong>Client ID:</strong> {scanResults.client_id}
              </div> */}
              {/* <div className="result-item">
                <strong>Scan Type:</strong> {scanResults.scan_type}
              </div> */}
              <div className="result-item">
                <strong>Total Findings:</strong> 
                <span className={`findings-count ${scanResults.results?.total_findings > 0 ? 'has-findings' : 'no-findings'}`}>
                  {scanResults.results?.total_findings || 0}
                </span>
              </div>
              <div className="result-item">
                <strong>Scan Type Used: </strong> 
                <span className="scan-type">
                  {scanResults.scan_type === 'selected' ? 'Selected Objects' : scanResults.scan_type}

                </span>
              </div>
              <div className="result-item">
                <strong>Timestamp:</strong> {formatDate(scanResults.timestamp)}
              </div>
              {scanResults.selected_objects_count && (
                <div className="result-item">
                  <strong>Objects Scanned:</strong> {scanResults.selected_objects_count}
                </div>
              )}
            </div>
            {scanResults.results?.summary && (
              <div className="scan-summary">
                <h4>Summary:</h4>
                <p>{scanResults.results.summary}</p>
              </div>
            )}
            {scanResults.message && (
              <div className="scan-message">
                <h4>Details:</h4>
                <p>{scanResults.message}</p>
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="navigation-container">
          <button onClick={() => navigate('/connect')} className="nav-button secondary">
            Back to Connect
          </button>
          <button 
            onClick={() => navigate('/risk-assessment')} 
            className="nav-button primary"
          >
            Continue to Risk Assessment
          </button>
        </div>

        {/* Scan Progress */}
        {scanning && (
          <div 
            className="scan-progress-overlay"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              width: '100vw',
              height: '100vh',
              background: 'rgba(0, 0, 0, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 99999
            }}
          >
            <div className="scan-progress-modal">
              <div className="scan-progress-content">
                <div className="scan-icon">
                  <div className="scanning-animation">
                    <div className="scan-wave"></div>
                    <div className="scan-wave"></div>
                    <div className="scan-wave"></div>
                  </div>
                </div>
                <div className="scan-info">
                  <h3>Running Security Scan</h3>
                  <p>Analyzing your data sources for sensitive information...</p>
                </div>
                <div className="progress-container">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${scanProgress}%` }}></div>
                    <div className="progress-glow" style={{ left: `${scanProgress}%` }}></div>
                  </div>
                  <div className="progress-details">
                    <span className="progress-percentage">{Math.round(scanProgress)}%</span>
                    <span className="progress-status">
                      {scanProgress < 30 ? 'Initializing scan...' : 
                       scanProgress < 60 ? 'Analyzing data patterns...' : 
                       scanProgress < 90 ? 'Classifying sensitive data...' : 
                       'Finalizing results...'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Toast Notifications */}
        {showToast && (
          <div 
            className="toast-overlay"
            style={{
              position: 'fixed',
              top: '20px',
              left: '20px',
              right: 'auto',
              zIndex: 99998
            }}
          >
            <div className={`toast ${submissionMessage.toLowerCase().includes('success') ? 'toast-success' : 
              submissionMessage.toLowerCase().includes('error') || submissionMessage.toLowerCase().includes('fail') ? 'toast-error' : 'toast-info'}`}>
              {submissionMessage}
            </div>
          </div>
        )}
          </>
        )}
      </div>
    </div>
  );
}

export default DiscoverPage;
