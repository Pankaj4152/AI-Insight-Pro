// src/pages/SDECataloguePage.js
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import '../Css/SDECatalogue.css';
import { useNavigate } from 'react-router-dom';
import { Lightbulb, CheckSquare, Plus, Trash2 } from 'lucide-react'; // Import the Trash2 icon for the delete button
import { api } from '../utils/apiIntegration';
import { API_BASE_URL } from '../apiConfig';
import { getCurrentClientId } from '../utils/clientUtils';

function SDECataloguePage() {
  const navigate = useNavigate();
  const [sdeUserIndustry, setSdeUserIndustry] = useState('');
  const [sdeSelectedIndustryFilter, setSdeSelectedIndustryFilter] = useState('none');
  const [industryOptions, setIndustryOptions] = useState([]); // For dropdown
  const [sdes, setSDEs] = useState([]); // SDEs fetched from API
  const [selectedSDEIds, setSelectedSDEIds] = useState(new Set());
  const [allSelectedSDEs, setAllSelectedSDEs] = useState([]); // All selected SDEs from driver API
  const [submissionMessage, setSubmissionMessage] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('industry'); // 'industry' or 'all'
  const [showAddModal, setShowAddModal] = useState(false);
  const [addSDEForm, setAddSDEForm] = useState({
    name: '',
    data_type: '',
    sensitivity: '',
    regex: '',
    classification: '',
    selected_industry: '',
  });
  const [addSDEError, setAddSDEError] = useState('');
  const [addSDELoading, setAddSDELoading] = useState(false);
  const [isSignupFlow, setIsSignupFlow] = useState(false);
  const [clientId, setClientId] = useState('');
  const [showDebugInfo, setShowDebugInfo] = useState(false);
  const [activeView, setActiveView] = useState('selection'); // 'selection' or 'selected'
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewSDE, setPreviewSDE] = useState(null);
  const [showSavePreviewModal, setShowSavePreviewModal] = useState(false);
  const [savePreviewSDEs, setSavePreviewSDEs] = useState([]);
  const [justSavedSDEs, setJustSavedSDEs] = useState(false);

  // Helper function to get client ID
  const getClientId = () => {
    return getCurrentClientId();
  };

  // Helper function to show toast messages
  const showToastMessage = useCallback((message, duration = 2000) => {
    setSubmissionMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), duration);
  }, []);

  // Load existing SDE selections from backend
  const loadExistingSdeSelections = useCallback(async () => {
    const currentClientId = getClientId();
    if (!currentClientId || currentClientId === 'demo-client') return;

    try {
      // Use the driver API to get client selected SDEs
      console.log('Loading existing SDE selections for client:', currentClientId);
      const result = await api.sde.getClientSDEs(currentClientId);
      console.log('Driver API response:', result);

      if (result.success && result.data.selected_sdes && result.data.selected_sdes.length > 0) {
        console.log('Selected SDEs from driver API:', result.data.selected_sdes);
        console.log('Available SDEs from connector API:', sdes);

        // Map SDE names back to IDs from the current SDEs list
        const selectedIds = new Set();
        const unmatchedSDEs = [];

        result.data.selected_sdes.forEach(selectedSde => {
          const matchingSde = sdes.find(sde => sde.name === selectedSde.pattern_name);
          if (matchingSde) {
            selectedIds.add(matchingSde.id);
            console.log(`Matched SDE: ${selectedSde.pattern_name} -> ID: ${matchingSde.id}`);
          } else {
            unmatchedSDEs.push(selectedSde.pattern_name);
            console.log(`Unmatched SDE: ${selectedSde.pattern_name}`);
          }
        });

        console.log('Final selected IDs:', Array.from(selectedIds));
        console.log('Unmatched SDEs:', unmatchedSDEs);

        setSelectedSDEIds(selectedIds);
        // Store all selected SDEs from driver API for display
        setAllSelectedSDEs(result.data.selected_sdes);

        // Show detailed toast message
        const totalFromAPI = result.data.selected_sdes.length;
        const matchedCount = selectedIds.size;
        const unmatchedCount = unmatchedSDEs.length;

        if (matchedCount > 0) {
          let message = `Loaded ${matchedCount} of ${totalFromAPI} selected SDEs`;
          if (unmatchedCount > 0) {
            message += ` (${unmatchedCount} not available in current industry)`;
          }
          showToastMessage(message, 4000);
        }

        if (unmatchedCount > 0) {
          console.warn('Some selected SDEs are not available in current industry filter:', unmatchedSDEs);
        }
      } else {
        console.log('No selected SDEs found or API call failed');
      }
    } catch (error) {
      console.error('Error loading existing SDE selections:', error);
      showToastMessage('Failed to load previously selected SDEs', 3000);
    }
  }, [sdes, showToastMessage]);

  // Consolidated initialization effect - runs only once on mount
  useEffect(() => {
    const initializeComponent = async () => {
      // Initialize client ID
      setClientId(getClientId());
      
      // Check if we're in signup flow
      const signupFlow = localStorage.getItem('signup_flow');
      const signupStep = localStorage.getItem('signup_step');
      setIsSignupFlow(signupFlow === 'in_progress' && signupStep === 'sde_catalogue');
      
      // Get industry from storage
      const industryFromStorage = localStorage.getItem('profile_industry') || 'NONE';
      setSdeUserIndustry(industryFromStorage);
      
      // Load previously selected SDEs from localStorage if available (fallback)
      const savedSelectedSDEs = localStorage.getItem('sdeCatalogueSelectedSDEs');
      if (savedSelectedSDEs) {
        try {
          setSelectedSDEIds(new Set(JSON.parse(savedSelectedSDEs)));
        } catch (e) {
          console.error('Error parsing saved SDEs:', e);
        }
      }
      
      // Fetch industry options first
      try {
        const result = await api.sde.getIndustryClassifications();
        if (result.success && result.data.industries) {
          setIndustryOptions(result.data.industries);
          
          // Set initial filter and fetch SDEs only once
          const initialFilter = industryFromStorage;
          setSdeSelectedIndustryFilter(initialFilter);
          
          // Only fetch SDEs if we have a valid industry
          if (initialFilter && initialFilter !== 'NONE') {
            setLoading(true);
            try {
              // Normalize industry to match available options
              let matchedIndustry = initialFilter;
              const norm = str => str.toLowerCase().replace(/s$/, '');
              const industryNorm = norm(initialFilter);
              let found = result.data.industries.find(opt => norm(opt) === industryNorm);
              if (!found) {
                found = result.data.industries.find(opt => norm(opt).includes(industryNorm) || industryNorm.includes(norm(opt)));
              }
              if (found) matchedIndustry = found;
              
              const sdeResult = await api.sde.getSDEsByIndustry(matchedIndustry);
              if (sdeResult.success && sdeResult.data.sdes) {
                setSDEs(sdeResult.data.sdes);
              } else {
                setSDEs([]);
                if (sdeResult.data && sdeResult.data.message) {
                  showToastMessage(`${sdeResult.data.message}`, 3000);
                }
              }
            } catch (error) {
              console.error('Error fetching SDEs:', error);
              setSDEs([]);
              showToastMessage('Failed to fetch SDEs. Please check your connection and try again.', 4000);
            } finally {
              setLoading(false);
            }
          }
        } else {
          setIndustryOptions([]);
        }
      } catch (error) {
        console.error('Error fetching industries:', error);
        setIndustryOptions([]);
      }
      
      // Add fade-in animation
      const container = document.getElementById('sde-catalogue-container');
      if (container) {
        container.classList.add('fade-in');
      }
    };
    
    initializeComponent();
  }, []); // Empty dependency array - runs only once

  // Optimized fetchSDEs function for dropdown changes only
  const fetchSDEs = useCallback(async (industry) => {
    if (!industry || industry === 'NONE') return;
    
    setLoading(true);
    try {
      // Normalize industry to match available options (case-insensitive, ignore plural/singular)
      let matchedIndustry = industry;
      if (industryOptions && industryOptions.length > 0) {
        const norm = str => str.toLowerCase().replace(/s$/, ''); // remove trailing 's'
        const industryNorm = norm(industry);
        // Try exact match (ignoring plural)
        let found = industryOptions.find(opt => norm(opt) === industryNorm);
        // If not found, try substring match
        if (!found) {
          found = industryOptions.find(opt => norm(opt).includes(industryNorm) || industryNorm.includes(norm(opt)));
        }
        if (found) matchedIndustry = found;
      }
      
      const result = await api.sde.getSDEsByIndustry(matchedIndustry);
      if (result.success && result.data.sdes) {
        setSDEs(result.data.sdes);
      } else if (result.data && result.data.message) {
        setSDEs([]);
        showToastMessage(`${result.data.message}`, 3000);
      } else {
        setSDEs([]);
        showToastMessage('Failed to fetch SDEs', 3000);
      }
    } catch (error) {
      console.error('Error fetching SDEs:', error);
      setSDEs([]);
      showToastMessage('Failed to fetch SDEs. Please check your connection and try again.', 4000);
    } finally {
      setLoading(false);
    }
  }, [industryOptions, showToastMessage]);

  // Load existing SDE selections from backend when SDEs are loaded
  useEffect(() => {
    if (sdes.length > 0) {
      loadExistingSdeSelections();
    }
  }, [sdes, loadExistingSdeSelections]);

  // Update localStorage when selected SDEs change
  useEffect(() => {
    if (sdeSelectedIndustryFilter) {
      localStorage.setItem('sdeCatalogueSelectedIndustry', sdeSelectedIndustryFilter);
    }
    localStorage.setItem('sdeCatalogueSelectedSDEs', JSON.stringify(Array.from(selectedSDEIds)));
  }, [sdeSelectedIndustryFilter, selectedSDEIds]);

  // Debounced fetchSDEs function to prevent rapid API calls
  const debouncedFetchSDEs = useCallback(
    (() => {
      let timeout;
      return (industry) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fetchSDEs(industry), 300); // 300ms debounce
      };
    })(),
    [fetchSDEs]
  );

  // Handle dropdown changes - only fetch when user manually changes dropdown
  const handleSdeIndustryFilterChange = (e) => {
    const newFilter = e.target.value;
    setSdeSelectedIndustryFilter(newFilter);
    setSubmissionMessage('');
    // Only fetch if it's different from current selection
    if (newFilter !== sdeSelectedIndustryFilter) {
      debouncedFetchSDEs(newFilter);
    }
  };


  const handleSDECheckboxChange = (sdeId, sdeName) => {
    const sde = sdes.find(s => s.id === sdeId);

    setSelectedSDEIds((prevSelected) => {
      const newSelected = new Set(prevSelected);
      if (newSelected.has(sdeId)) {
        newSelected.delete(sdeId);
        // Remove from allSelectedSDEs as well
        setAllSelectedSDEs(prevAll => prevAll.filter(selectedSde => selectedSde.pattern_name !== sdeName));
        showToastMessage(`"${sdeName}" removed from selection`, 2000);
      } else {
        newSelected.add(sdeId);
        // Add to allSelectedSDEs as well
        if (sde) {
          const newSelectedSde = {
            pattern_name: sde.name,
            sensitivity: sde.sensitivity,
            protection_method: null // Will be set when saved
          };
          setAllSelectedSDEs(prevAll => {
            // Check if already exists to avoid duplicates
            const exists = prevAll.some(selectedSde => selectedSde.pattern_name === sdeName);
            if (!exists) {
              return [...prevAll, newSelectedSde];
            }
            return prevAll;
          });
        }
        showToastMessage(`"${sdeName}" added to selection`, 2000);
      }
      return newSelected;
    });
  };

  // NEW: Handler for removing a single SDE from the selected list
  const handleRemoveSDE = useCallback(async (sdeId, sdeName) => {
    const currentClientId = getClientId();
    if (!currentClientId || currentClientId === 'demo-client') {
      // For demo client, just update local state
      setSelectedSDEIds(prevSelected => {
        const newSelected = new Set(prevSelected);
        newSelected.delete(sdeId);
        return newSelected;
      });
      setAllSelectedSDEs(prevAll => prevAll.filter(sde => sde.pattern_name !== sdeName));
      showToastMessage(`"${sdeName}" removed from selection (demo mode)`, 2000);
      return;
    }

    try {
      // Call API to remove SDE from backend
      const response = await fetch(`${API_BASE_URL}/sdes/remove`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: currentClientId,
          pattern_name: sdeName
        })
      });

      const result = await response.json();

      if (response.ok && result.status === 'success') {
        // Update local state only after successful API call
        setSelectedSDEIds(prevSelected => {
          const newSelected = new Set(prevSelected);
          newSelected.delete(sdeId);
          return newSelected;
        });
        setAllSelectedSDEs(prevAll => prevAll.filter(sde => sde.pattern_name !== sdeName));
        showToastMessage(`${sdeName} removed from selection successfully`, 3000);
      } else {
        console.error('API returned error:', result);

        // Handle different error responses with detailed messages
        if (response.status === 409) {
          const errorDetail = result.detail;
          if (typeof errorDetail === 'object' && errorDetail.error === 'constraint_violation') {
            const message = `Cannot remove "${sdeName}": This SDE is referenced by scan findings. Please delete the scan findings first or contact your administrator.`;
            showToastMessage(message, 8000);
          } else if (typeof errorDetail === 'string') {
            showToastMessage(`Cannot remove "${sdeName}": ${errorDetail}`, 6000);
          } else {
            showToastMessage(`Cannot remove "${sdeName}": This SDE is referenced by existing scan findings. Please contact your administrator.`, 6000);
          }
        } else if (response.status === 404) {
          showToastMessage(`SDE "${sdeName}" not found. It may have already been removed.`, 4000);
        } else if (response.status === 403) {
          showToastMessage(`Access denied: You don't have permission to remove "${sdeName}".`, 4000);
        } else {
          const errorMessage = result.message || result.detail || result.error || 'Unknown error occurred';
          showToastMessage(`Error removing "${sdeName}": ${errorMessage}`, 5000);
        }
      }
    } catch (error) {
      console.error('Error removing SDE:', error);
      showToastMessage(`Connection Error: Could not connect to server to remove "${sdeName}". Please check your internet connection and try again.`, 5000);
    }
  }, [showToastMessage]);

  // NEW: Handler for clearing all selected SDEs
  const handleClearAllSelectedSDEs = useCallback(async () => {
    const currentClientId = getClientId();
    if (!currentClientId || currentClientId === 'demo-client') {
      // For demo client, just clear local state
      setSelectedSDEIds(new Set());
      setAllSelectedSDEs([]);
      showToastMessage('All selected SDEs cleared (demo mode)', 2000);
      return;
    }

    try {
      // Call API to clear all SDEs from backend
      const response = await fetch(`${API_BASE_URL}/sdes/clear-all`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: currentClientId
        })
      });

      const result = await response.json();

      if (response.ok && result.status === 'success') {
        // Update local state only after successful API call
        setSelectedSDEIds(new Set());
        setAllSelectedSDEs([]);
        showToastMessage(`Successfully cleared ${result.cleared_count} selected SDEs`, 3000);
      } else {
        console.error('API returned error:', result);

        // Handle different error responses with detailed messages
        if (response.status === 409) {
          const errorDetail = result.detail;
          if (typeof errorDetail === 'object' && errorDetail.error === 'constraint_violation') {
            const message = `Cannot clear SDEs: ${errorDetail.affected_sdes} SDEs are referenced by ${errorDetail.finding_count} scan findings. Please delete the scan findings first or contact your administrator.`;
            showToastMessage(message, 8000);
          } else if (typeof errorDetail === 'string') {
            showToastMessage(`Cannot clear SDEs: ${errorDetail}`, 6000);
          } else {
            showToastMessage(`Cannot clear SDEs: Some SDEs are referenced by existing scan findings. Please contact your administrator.`, 6000);
          }
        } else if (response.status === 403) {
          showToastMessage(`Access denied: You don't have permission to clear selected SDEs.`, 4000);
        } else {
          const errorMessage = result.message || result.detail || result.error || 'Unknown error occurred';
          showToastMessage(`Error clearing SDEs: ${errorMessage}`, 5000);
        }
      }
    } catch (error) {
      console.error('Error clearing all SDEs:', error);
      showToastMessage('Connection Error: Could not connect to server to clear SDEs. Please check your internet connection and try again.', 5000);
    }
  }, [showToastMessage]);

  const handleSelectAllSDEs = () => {
    const currentTabSDEs = activeTab === 'industry' ? industrySpecificSDEs : allIndustrySDEs;
    const allIds = new Set([...selectedSDEIds, ...currentTabSDEs.map(sde => sde.id)]);
    setSelectedSDEIds(allIds);
    showToastMessage(`All ${currentTabSDEs.length} SDEs from current tab selected`, 2000);
  };

  const handleDeselectAllCurrentTab = () => {
    const currentTabSDEs = activeTab === 'industry' ? industrySpecificSDEs : allIndustrySDEs;
    const currentTabIds = new Set(currentTabSDEs.map(sde => sde.id));
    const newSelected = new Set([...selectedSDEIds].filter(id => !currentTabIds.has(id)));
    setSelectedSDEIds(newSelected);
    showToastMessage(`All SDEs from current tab deselected`, 2000);
  };

  // Save SDEs to backend - now shows preview first
  const saveSDEs = async () => {
    const currentClientId = getClientId();

    if (selectedSDEIds.size === 0) {
      showToastMessage('Please select at least one SDE to save.', 3000);
      return false;
    }

    // Get SDE objects from selected IDs with required fields
    const selectedSDEs = Array.from(selectedSDEIds)
      .map(sdeId => {
        const sde = sdes.find(s => s.id === sdeId);
        if (!sde) return null;
        return {
          id: sde.id,
          name: sde.name,
          sensitivity: sde.sensitivity,
          classification_level: sde.classification,
          data_type: sde.data_type || 'Not specified',
          industry_classification: sde.industry_classification,
          regex: sde.regex || 'Not specified'
        };
      })
      .filter(sde => sde !== null);

    console.log('Selected SDEs:', selectedSDEs.map(s => s.name));

    try {
      // Fetch the latest saved SDEs from API to compare using the correct endpoint
      console.log('Fetching latest saved SDEs from API...');
      const result = await api.sde.getClientSDEs(currentClientId);
      
      let alreadySavedSDEs = [];
      if (result.success && result.data?.selected_sdes) {
        alreadySavedSDEs = result.data.selected_sdes;
        console.log('Already saved SDEs from API:', alreadySavedSDEs.map(s => s.pattern_name || s.name));
      } else {
        console.log('No saved SDEs found or API call failed, treating all as new');
      }

      // Filter out SDEs that are already saved (compare against API data)
      const newSDEs = selectedSDEs.filter(sde => {
        const isAlreadySaved = alreadySavedSDEs.some(savedSde => 
          (savedSde.pattern_name === sde.name) || (savedSde.name === sde.name)
        );
        console.log(`SDE "${sde.name}" - Already saved: ${isAlreadySaved}`);
        return !isAlreadySaved;
      });
      
      console.log('New SDEs to preview:', newSDEs.map(s => s.name));
      console.log('New SDEs count:', newSDEs.length);

      // Show preview modal - will handle both cases (new SDEs or no new SDEs)
      setSavePreviewSDEs(newSDEs);
      setShowSavePreviewModal(true);
      console.log('Preview modal showing with:', newSDEs.length, 'new SDEs');

      // Scroll to top when preview modal opens - ensure it's at the very top
      setTimeout(() => {
        window.scrollTo({
          top: 0,
          left: 0,
          behavior: 'smooth'
        });
        // Also scroll the document element for better compatibility
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }, 150);

    } catch (error) {
      console.error('Error fetching saved SDEs:', error);
      // If API call fails, show all selected SDEs as potentially new
      console.log('API error, showing all selected SDEs as new');
      setSavePreviewSDEs(selectedSDEs);
      setShowSavePreviewModal(true);
      
      // Scroll to top even on error - ensure it's at the very top
      setTimeout(() => {
        window.scrollTo({
          top: 0,
          left: 0,
          behavior: 'smooth'
        });
        // Also scroll the document element for better compatibility
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }, 150);
    }

    return false; // Don't proceed with save yet
  };

  // New function to handle the actual save after preview confirmation
  const handleConfirmSaveSDEs = async () => {
    const currentClientId = getClientId();
    setShowSavePreviewModal(false);
    setLoading(true);

    try {
      // Prepare payload with just the required fields for the API
      const apiSDEs = savePreviewSDEs.map(sde => ({
        name: sde.name,
        sensitivity: sde.sensitivity,
        classification_level: sde.classification_level
      }));

      const payload = {
        client_id: currentClientId,
        sdes: apiSDEs
      };

      console.log('Saving SDEs with payload:', payload);
      console.log('API URL:', `${API_BASE_URL}/store-client-sdes`);

      const response = await fetch(`${API_BASE_URL}/store-client-sdes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      const result = await response.json();
      console.log('Response result:', result);

      if (response.ok && result.status === 'success') {
        showToastMessage(`Successfully saved ${apiSDEs.length} SDE selections! Redirecting to your selected SDEs...`, 4000);
        setSavePreviewSDEs([]); // Clear preview data
        
        // Small delay to let the user see the success message, but keep loading state
        setTimeout(async () => {
          try {
            // Reload existing SDE selections to show the updated list
            await loadExistingSdeSelections();
            
            // Set flag to show success banner in selected view
            setJustSavedSDEs(true);
            
            // Redirect to the "Selected SDEs" view
            setActiveView('selected');
            
            // Clear the success banner after 5 seconds
            setTimeout(() => setJustSavedSDEs(false), 5000);
          } finally {
            // Ensure loading state is cleared after redirect
            setLoading(false);
          }
        }, 1500);
        
        return true;
      } else {
        console.error('API returned error:', result);
        const errorMessage = result.message || result.detail || result.error || `Status: ${response.status}`;
        showToastMessage(`Warning: Could not save SDE selections to server. ${errorMessage}`, 5000);
        setLoading(false);
        return false;
      }
    } catch (error) {
      console.error('Error saving SDEs:', error);
      showToastMessage('Connection Error: Could not connect to server. Please check your internet connection and try again.', 5000);
      setLoading(false);
      return false;
    }
  };

  // Function to close save preview modal
  const handleCloseSavePreview = () => {
    setShowSavePreviewModal(false);
    setSavePreviewSDEs([]);
  };

  const handleSdeCatalogueSaveAndContinue = async () => {
    const isSignupFlow = localStorage.getItem('signup_flow') === 'in_progress';
    
    if (isSignupFlow) {
      // Update signup step
      localStorage.setItem('signup_step', 'model_registry');
      showToastMessage('Proceeding to Model Registry...', 3000);
      setTimeout(() => navigate('/model-inventory'), 1500);
    } else {
      // Normal flow - just navigate to dashboard
      showToastMessage('Returning to Dashboard...', 3000);
      setTimeout(() => navigate('/dashboard'), 1500);
    }
  };

  // Add SDE handler
  const handleAddSDEChange = (e) => {
    const { name, value } = e.target;
    setAddSDEForm({ ...addSDEForm, [name]: value });
    // Check for duplicate name in the same industry
    if (name === 'name' || name === 'selected_industry') {
      const checkName = name === 'name' ? value : addSDEForm.name;
      const checkIndustry = name === 'selected_industry' ? value : addSDEForm.selected_industry;
      if (checkName && checkIndustry) {
        const exists = sdes.some(
          sde => sde.name.trim().toLowerCase() === checkName.trim().toLowerCase() &&
                  sde.industry_classification === checkIndustry
        );
        if (exists) {
          setAddSDEError('An SDE with this name already exists for the selected industry.');
        } else {
          setAddSDEError('');
        }
      }
    }
  };

  const handleOpenAddModal = () => {
    setAddSDEForm({
      name: '',
      data_type: '',
      sensitivity: '',
      regex: '',
      classification: '',
      selected_industry: sdeSelectedIndustryFilter || '',
    });
    setAddSDEError('');
    setShowAddModal(true);
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
    setAddSDEError('');
  };

  const handleAddSDESubmit = async (e) => {
    e.preventDefault();
    setAddSDEError('');
    // Basic validation
    if (!addSDEForm.name || !addSDEForm.data_type || !addSDEForm.sensitivity || !addSDEForm.regex || !addSDEForm.classification || !addSDEForm.selected_industry) {
      setAddSDEError('All fields are required.');
      return;
    }
    // Regex validation
    try {
      // Try to create a RegExp object
      // (wrap in try/catch to catch invalid patterns)
      // Only test if not empty
      if (addSDEForm.regex) {
        new RegExp(addSDEForm.regex);
      }
    } catch (err) {
      setAddSDEError('Regex pattern is invalid. Please enter a valid regular expression.');
      return;
    }
    // Check for duplicate name in the same industry before submit
    const exists = sdes.some(
      sde => sde.name.trim().toLowerCase() === addSDEForm.name.trim().toLowerCase() &&
              sde.industry_classification === addSDEForm.selected_industry
    );
    if (exists) {
      setAddSDEError('An SDE with this name already exists for the selected industry.');
      return;
    }
    
    // Show preview modal instead of immediately submitting
    setPreviewSDE({ ...addSDEForm });
    setShowAddModal(false);  // Close the add modal first
    setShowPreviewModal(true);  // Then show the preview modal
    
    // Scroll to top when preview modal opens - ensure it's at the very top
    setTimeout(() => {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'smooth'
      });
      // Also scroll the document element for better compatibility
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    }, 150);
  };

  // New function to handle the actual SDE submission after preview confirmation
  const handleConfirmAddSDE = async () => {
    setAddSDELoading(true);
    setShowPreviewModal(false);
    
    const result = await api.sde.addSDE(addSDEForm);
    
    if (result.success && result.data.status === 'success') {
      setShowAddModal(false);
      showToastMessage(`SDE "${addSDEForm.name}" added successfully`, 3000);
      fetchSDEs(sdeSelectedIndustryFilter); // Refresh list
      setPreviewSDE(null);
    } else {
      setAddSDEError(result.data?.detail || result.error || 'Failed to add SDE.');
      setShowAddModal(true); // Show the form again with error
    }
    setAddSDELoading(false);
  };

  // Function to close preview and go back to form
  const handleClosePreview = () => {
    setShowPreviewModal(false);
    setPreviewSDE(null);
    setShowAddModal(true);  // Show the add form again
  };

  // Memoized expensive calculations to prevent unnecessary re-renders
  const { industrySpecificSDEs, allIndustrySDEs } = useMemo(() => {
    return {
      industrySpecificSDEs: sdes.filter(sde => sde.industry_classification === sdeSelectedIndustryFilter),
      allIndustrySDEs: sdes.filter(sde => sde.industry_classification === 'all_industries')
    };
  }, [sdes, sdeSelectedIndustryFilter]);

  // Set default tab on SDEs change
  useEffect(() => {
    if (industrySpecificSDEs.length > 0) {
      setActiveTab('industry');
    } else if (allIndustrySDEs.length > 0) {
      setActiveTab('all');
    }
  }, [industrySpecificSDEs.length, allIndustrySDEs.length]);

  return (
    <div id="sde-catalogue-container" className="sde-catalogue-container dashboard-container">
      {/* Signup Flow Banner */}
      {isSignupFlow && (
        <div style={{
          backgroundColor: 'var(--primary)',
          color: 'white',
          padding: '1rem',
          marginBottom: '2rem',
          borderRadius: '8px',
          textAlign: 'center',
          width: '100%',
          maxWidth: '1200px'
        }}>
          {/* <h2 style={{ margin: '0 0 0.5rem 0' }}>Step 2 of 3: Configure Your Data Elements (Optional)</h2> */}
          <p style={{ margin: 0 }}>
            Select the Sensitive Data Entities (SDEs) that are relevant to your industry to help us protect your data better. You can skip this step and configure later.
          </p>
        </div>
      )}
      
      
      {/* Header Section - Title and Description */}
      <div style={{
        textAlign: 'center',
        marginBottom: '2rem',
        width: '100%',
        maxWidth: '1200px'
      }}>
        <h1 className="page-title dashboard-title" style={{ 
          margin: '0 0 1rem 0',
          color: 'hsl(198 88% 32%)', // Primary blue from employment-edge-ui
          fontSize: '2.5rem',
          fontWeight: '700'
        }}>
          SDE Catalogue
        </h1>
        <p className="connect-description" style={{ 
          margin: '0 0 2rem 0',
          color: 'hsl(215 16% 47%)', // Muted foreground
          fontSize: '1.1rem',
          maxWidth: '600px',
          marginLeft: 'auto',
          marginRight: 'auto'
        }}>
          Select the Sensitive Data Entities (SDEs) provided by our side based on your industry type.
        </p>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '3rem'
        }}>
          <div style={{
            background: 'hsl(0 0% 100%)',
            borderRadius: '8px',
            padding: '4px',
            border: '1px solid hsl(214.3 31.8% 91.4%)',
            display: 'flex'
          }}>
            <button
              onClick={() => setActiveView('selection')}
              style={{
                padding: '12px 24px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: activeView === 'selection' ? 'hsl(198 88% 32%)' : 'transparent',
                color: activeView === 'selection' ? 'hsl(0 0% 98%)' : 'hsl(215 25% 15%)',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontSize: '14px'
              }}
            >
              Select SDEs
            </button>
            <button
              onClick={() => setActiveView('selected')}
              style={{
                padding: '12px 24px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: activeView === 'selected' ? 'hsl(198 88% 32%)' : 'transparent',
                color: activeView === 'selected' ? 'hsl(0 0% 98%)' : 'hsl(215 25% 15%)',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontSize: '14px'
              }}
            >
              Selected SDEs ({allSelectedSDEs.length})
            </button>
          </div>
        </div>        {/* Company & Industry Information Cards - Show for both views */}
        <div className="sde-info-cards" style={{ 
          display: 'grid', 
          gridTemplateColumns: activeView === 'selection' ? 'repeat(auto-fit, minmax(320px, 1fr))' : '1fr', 
          gap: '1.5rem',
          maxWidth: '1200px',
          margin: '0 auto 3rem auto',
          justifyContent: 'center',
          width: '100%',
          padding: '0 1rem'
        }}>
          <div className="card company-info-card" style={{ 
            background: 'linear-gradient(135deg, hsl(198 88% 32%), hsl(172 76% 47%))', // Employment-edge gradient
            color: 'hsl(0 0% 98%)',
            border: '1px solid hsl(220 13% 91%)',
            borderRadius: '0.75rem', // 12px
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px hsl(215 25% 15% / 0.1), 0 2px 4px -1px hsl(215 25% 15% / 0.06)', // Professional shadow
            minHeight: '120px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            width: '100%',
            boxSizing: 'border-box'
          }}>
            <h3 className="card-title" style={{ 
              color: 'hsl(0 0% 98%)', 
              margin: '0 0 0.5rem 0', 
              fontSize: '1.1rem',
              fontWeight: '600',
              textAlign: 'center'
            }}>
              Your Registered Company
            </h3>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', letterSpacing: '0.3px', textAlign: 'center' }}>
              {sdeUserIndustry ? sdeUserIndustry.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'Loading...'}
            </div>
            <div style={{ fontSize: '0.85rem', opacity: '0.9', marginTop: '0.3rem', textAlign: 'center' }}>
              Industry Classification
            </div>
          </div>

          {/* Industry Filter - Only show in selection view */}
          {activeView === 'selection' && (
            <div className="card industry-filter-card" style={{ 
              background: 'hsl(0 0% 100%)', // Clean white background
              color: 'hsl(215 25% 15%)',
              border: '1px solid hsl(220 13% 91%)',
              borderRadius: '0.75rem',
              padding: '1.5rem',
              boxShadow: '0 4px 6px -1px hsl(215 25% 15% / 0.1), 0 2px 4px -1px hsl(215 25% 15% / 0.06)',
              minHeight: '120px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              width: '100%',
              boxSizing: 'border-box'
            }}>
              <h3 className="card-title" style={{ 
                color: 'hsl(198 88% 32%)', 
                margin: '0 0 0.75rem 0', 
                fontSize: '1.1rem',
                fontWeight: '600',
                textAlign: 'center'
              }}>
                Filter SDEs by Industry
              </h3>
              <div className="form-group" style={{ margin: 0, width: '100%' }}>
                <select
                  id="sdeIndustryFilter"
                  value={sdeSelectedIndustryFilter}
                  onChange={handleSdeIndustryFilterChange}
                  className="dropdown-style"
                  style={{ 
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    border: '1px solid hsl(220 13% 91%)',
                    fontSize: '0.95rem',
                    backgroundColor: 'hsl(0 0% 100%)',
                    color: 'hsl(215 25% 15%)',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    boxSizing: 'border-box'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                >
                  {industryOptions.map(industry => (
                    <option key={industry} value={industry}>
                      {industry.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tab Content - Conditional rendering based on activeView */}
      {activeView === 'selection' && (
      <div className="sde-main-layout" style={{ 
        display: 'flex', 
        flexDirection: 'column',
        gap: '2rem',
        width: '100%',
        maxWidth: '1200px',
        margin: '0 auto 3rem auto',
        padding: '0 1rem'
      }}>
        
        {/* Left Side - SDE Selection */}
        <div className="sde-selection-section" style={{ 
          width: '100%',
          overflow: 'hidden' 
        }}>
          <div className="card" style={{ 
            position: 'relative',
            background: 'hsl(0 0% 100%)',
            border: '1px solid hsl(220 13% 91%)',
            borderRadius: '0.75rem',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px hsl(215 25% 15% / 0.1), 0 2px 4px -1px hsl(215 25% 15% / 0.06)',
            width: '100%',
            boxSizing: 'border-box'
          }}>
            {/* Header with Title and Tabs in same line - Compact Layout */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              margin: '0 0 1.5rem 0',
              flexWrap: 'wrap',
              minHeight: '2.5rem'
            }}>
              <h3 className="card-title" style={{
                color: 'hsl(198 88% 32%)',
                fontSize: '1.5rem',
                fontWeight: '600',
                margin: '0',
                display: 'flex',
                alignItems: 'center',
                flex: '1 1 auto',
                minWidth: '250px'
              }}>
                <Lightbulb size={22} style={{ marginRight: '10px', flexShrink: 0 }} />
                <span style={{ 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  Available SDEs: {sdeSelectedIndustryFilter.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
              </h3>
              
              {/* Tabs for SDE groups - Inline with title */}
              <div style={{ display: 'flex', gap: '0.75rem', flexShrink: 0, flexWrap: 'wrap' }}>
                <button
                  className={activeTab === 'industry' ? 'tab-active' : 'tab-inactive'}
                  style={{
                    fontWeight: activeTab === 'industry' ? '600' : '500',
                    border: '1px solid hsl(220 13% 91%)',
                    background: activeTab === 'industry' ? 'hsl(198 88% 32%)' : 'hsl(0 0% 100%)',
                    color: activeTab === 'industry' ? 'hsl(0 0% 98%)' : 'hsl(215 25% 15%)',
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    cursor: industrySpecificSDEs.length > 0 ? 'pointer' : 'not-allowed',
                    opacity: industrySpecificSDEs.length > 0 ? 1 : 0.5,
                    transition: 'all 0.2s ease',
                    fontSize: '0.9rem',
                    whiteSpace: 'nowrap',
                    minWidth: 'fit-content'
                  }}
                  onClick={() => industrySpecificSDEs.length > 0 && setActiveTab('industry')}
                  disabled={industrySpecificSDEs.length === 0}
                  onMouseEnter={(e) => {
                    if (industrySpecificSDEs.length > 0 && activeTab !== 'industry') {
                      e.target.style.backgroundColor = 'hsl(210 40% 96%)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (activeTab !== 'industry') {
                      e.target.style.backgroundColor = 'hsl(0 0% 100%)';
                    }
                  }}
                >
                  Industry ({industrySpecificSDEs.length})
                </button>
                <button
                  className={activeTab === 'all' ? 'tab-active' : 'tab-inactive'}
                  style={{
                    fontWeight: activeTab === 'all' ? '600' : '500',
                    border: '1px solid hsl(220 13% 91%)',
                    background: activeTab === 'all' ? 'hsl(198 88% 32%)' : 'hsl(0 0% 100%)',
                    color: activeTab === 'all' ? 'hsl(0 0% 98%)' : 'hsl(215 25% 15%)',
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    cursor: allIndustrySDEs.length > 0 ? 'pointer' : 'not-allowed',
                    opacity: allIndustrySDEs.length > 0 ? 1 : 0.5,
                    transition: 'all 0.2s ease',
                    fontSize: '0.9rem',
                    whiteSpace: 'nowrap',
                    minWidth: 'fit-content'
                  }}
                  onClick={() => allIndustrySDEs.length > 0 && setActiveTab('all')}
                  disabled={allIndustrySDEs.length === 0}
                  onMouseEnter={(e) => {
                    if (allIndustrySDEs.length > 0 && activeTab !== 'all') {
                      e.target.style.backgroundColor = 'hsl(210 40% 96%)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (activeTab !== 'all') {
                      e.target.style.backgroundColor = 'hsl(0 0% 100%)';
                    }
                  }}
                >
                  All-Purpose ({allIndustrySDEs.length})
                </button>
              </div>
            </div>

            {/* Select All Controls */}
            {((activeTab === 'industry' && industrySpecificSDEs.length > 0) || 
              (activeTab === 'all' && allIndustrySDEs.length > 0)) && (
              <div style={{ 
                display: 'flex', 
                gap: '0.75rem', 
                marginBottom: '1rem',
                padding: '0.75rem',
                backgroundColor: 'hsl(210 40% 96%)',
                borderRadius: '0.5rem',
                border: '1px solid hsl(220 13% 91%)',
                boxShadow: '0 1px 2px 0 hsl(215 25% 15% / 0.05)'
              }}>
                <button
                  onClick={handleSelectAllSDEs}
                  style={{ 
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    fontWeight: '600',
                    backgroundColor: 'hsl(198 88% 32%)', // Primary blue to match employment-edge-ui
                    color: 'hsl(0 0% 98%)',
                    border: 'none',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: '0 1px 2px 0 hsl(215 25% 15% / 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'hsl(198 88% 28%)';
                    e.target.style.transform = 'translateY(-1px)';
                    e.target.style.boxShadow = '0 4px 6px -1px hsl(215 25% 15% / 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'hsl(198 88% 32%)';
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 1px 2px 0 hsl(215 25% 15% / 0.05)';
                  }}
                >
                  ✓ Select All
                </button>
                <button
                  onClick={handleDeselectAllCurrentTab}
                  style={{ 
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    fontWeight: '600',
                    backgroundColor: 'hsl(24 96% 53%)', // Orange accent to match employment-edge-ui
                    color: 'hsl(0 0% 98%)',
                    border: 'none',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: '0 1px 2px 0 hsl(215 25% 15% / 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'hsl(24 96% 49%)';
                    e.target.style.transform = 'translateY(-1px)';
                    e.target.style.boxShadow = '0 4px 6px -1px hsl(215 25% 15% / 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'hsl(24 96% 53%)';
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 1px 2px 0 hsl(215 25% 15% / 0.05)';
                  }}
                >
                  ✗ Deselect All
                </button>
              </div>
            )}

            {/* SDE Grid Container with Fixed Height and Scroll */}
            <div style={{
              maxHeight: '350px',
              overflowY: 'auto',
              paddingRight: '0.5rem',
              marginBottom: '1rem',
              width: '100%'
            }}>
              <div className="sde-checkbox-grid" style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', 
                gap: '1rem',
                width: '100%'
              }}>
              {loading ? (
                <div style={{ 
                  gridColumn: '1 / -1', 
                  display: 'flex', 
                  flexDirection: 'column',
                  alignItems: 'center', 
                  justifyContent: 'center',
                  padding: '3rem',
                  color: 'hsl(215 16% 47%)'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    border: '4px solid hsl(220 13% 91%)',
                    borderTop: '4px solid hsl(198 88% 32%)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    marginBottom: '1rem'
                  }}></div>
                  <p style={{ margin: 0, fontSize: '1rem', fontWeight: '500' }}>Loading SDEs...</p>
                </div>
              ) : (
                <>
                  {activeTab === 'industry' && industrySpecificSDEs.length > 0 && (
                    <>
                      {industrySpecificSDEs.map((sde) => (
                        <div key={sde.id} className="sde-checkbox-item" style={{
                          padding: '1rem',
                          border: `1px solid ${selectedSDEIds.has(sde.id) ? 'hsl(198 88% 32%)' : 'hsl(220 13% 91%)'}`,
                          borderRadius: '0.5rem',
                          backgroundColor: selectedSDEIds.has(sde.id) ? 'hsl(198 88% 97%)' : 'hsl(0 0% 100%)',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          boxShadow: selectedSDEIds.has(sde.id) ? 
                            '0 0 20px hsl(198 88% 32% / 0.2)' : 
                            '0 1px 2px 0 hsl(215 25% 15% / 0.05)'
                        }}
                        onClick={() => handleSDECheckboxChange(sde.id, sde.name)}
                        onMouseEnter={(e) => {
                          if (!selectedSDEIds.has(sde.id)) {
                            e.target.style.borderColor = 'hsl(198 88% 32%)';
                            e.target.style.backgroundColor = 'hsl(210 40% 98%)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!selectedSDEIds.has(sde.id)) {
                            e.target.style.borderColor = 'hsl(220 13% 91%)';
                            e.target.style.backgroundColor = 'hsl(0 0% 100%)';
                          }
                        }}
                        >
                          <input
                            type="checkbox"
                            id={`sde-${sde.id}`}
                            checked={selectedSDEIds.has(sde.id)}
                            onChange={() => handleSDECheckboxChange(sde.id, sde.name)}
                            style={{ 
                              cursor: 'pointer', 
                              transform: 'scale(1.2)',
                              accentColor: 'hsl(198 88% 32%)'
                            }}
                          />
                          <label htmlFor={`sde-${sde.id}`} style={{ 
                            cursor: 'pointer', 
                            fontWeight: '500',
                            margin: 0,
                            flex: 1,
                            color: 'hsl(215 25% 15%)'
                          }}>
                            {sde.name}
                          </label>
                        </div>
                      ))}
                    </>
                  )}
                  {activeTab === 'all' && allIndustrySDEs.length > 0 && (
                    <>
                      {allIndustrySDEs.map((sde) => (
                        <div key={sde.id} className="sde-checkbox-item" style={{
                          padding: '1rem',
                          border: `1px solid ${selectedSDEIds.has(sde.id) ? 'hsl(198 88% 32%)' : 'hsl(220 13% 91%)'}`,
                          borderRadius: '0.5rem',
                          backgroundColor: selectedSDEIds.has(sde.id) ? 'hsl(198 88% 97%)' : 'hsl(0 0% 100%)',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          boxShadow: selectedSDEIds.has(sde.id) ? 
                            '0 0 20px hsl(198 88% 32% / 0.2)' : 
                            '0 1px 2px 0 hsl(215 25% 15% / 0.05)'
                        }}
                        onClick={() => handleSDECheckboxChange(sde.id, sde.name)}
                        onMouseEnter={(e) => {
                          if (!selectedSDEIds.has(sde.id)) {
                            e.target.style.borderColor = 'hsl(198 88% 32%)';
                            e.target.style.backgroundColor = 'hsl(210 40% 98%)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!selectedSDEIds.has(sde.id)) {
                            e.target.style.borderColor = 'hsl(220 13% 91%)';
                            e.target.style.backgroundColor = 'hsl(0 0% 100%)';
                          }
                        }}
                        >
                          <input
                            type="checkbox"
                            id={`sde-${sde.id}`}
                            checked={selectedSDEIds.has(sde.id)}
                            onChange={() => handleSDECheckboxChange(sde.id, sde.name)}
                            style={{ 
                              cursor: 'pointer', 
                              transform: 'scale(1.2)',
                              accentColor: 'hsl(198 88% 32%)'
                            }}
                          />
                          <label htmlFor={`sde-${sde.id}`} style={{ 
                            cursor: 'pointer', 
                            fontWeight: '500',
                            margin: 0,
                            flex: 1,
                            color: 'hsl(215 25% 15%)'
                          }}>
                            {sde.name}
                          </label>
                        </div>
                      ))}
                    </>
                  )}
                  {industrySpecificSDEs.length === 0 && allIndustrySDEs.length === 0 && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <p className="info-text">No SDEs found for the selected industry. Please check your backend server or SDE definitions.</p>
                    </div>
                  )}
                </>
              )}
            </div>
            </div>

            {/* Professional Add SDE button */}
            <button
              className="add-sde-fab"
              onClick={handleOpenAddModal}
              title="Add new SDE"
              style={{
                position: 'absolute',
                bottom: '1rem',
                right: '1rem',
                backgroundColor: 'hsl(172 76% 47%)', // Accent color from employment-edge-ui
                color: 'hsl(0 0% 98%)',
                border: 'none',
                borderRadius: '0.75rem',
                width: '56px',
                height: '56px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 10px 15px -3px hsl(215 25% 15% / 0.1), 0 4px 6px -2px hsl(215 25% 15% / 0.05)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                zIndex: 10,
                fontSize: '1.2rem',
                fontWeight: 'bold'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'scale(1.05) translateY(-2px)';
                e.target.style.boxShadow = '0 0 20px hsl(172 76% 47% / 0.4)';
                e.target.style.backgroundColor = 'hsl(172 76% 43%)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'scale(1) translateY(0)';
                e.target.style.boxShadow = '0 10px 15px -3px hsl(215 25% 15% / 0.1), 0 4px 6px -2px hsl(215 25% 15% / 0.05)';
                e.target.style.backgroundColor = 'hsl(172 76% 47%)';
              }}
            >
              <Plus size={24} />
            </button>
          </div>
        </div>

        {/* Right Side - Selected SDEs */}
        <div className="selected-sdes-section" style={{ 
          minHeight: 'fit-content',
          width: '100%',
          overflow: 'hidden' 
        }}>
          <div className="card" style={{ 
            position: 'sticky', 
            top: '2rem',
            background: 'hsl(0 0% 100%)',
            border: '1px solid hsl(220 13% 91%)',
            borderRadius: '0.75rem',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px hsl(215 25% 15% / 0.1), 0 2px 4px -1px hsl(215 25% 15% / 0.06)',
            marginBottom: 0,
            width: '100%',
            boxSizing: 'border-box'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
              <h3 className="card-title" style={{
                color: 'hsl(198 88% 32%)',
                fontSize: '1.5rem',
                fontWeight: '600',
                margin: '0',
                display: 'flex',
                alignItems: 'center',
                flex: '1 1 auto',
                minWidth: '200px'
              }}>
                <CheckSquare size={26} style={{ marginRight: '12px', verticalAlign: 'middle', flexShrink: 0 }} />
                Selected SDEs ({allSelectedSDEs.length})
              </h3>
              {/* <button
                onClick={() => setShowDebugInfo(!showDebugInfo)}
                style={{
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.75rem',
                  backgroundColor: 'hsl(210 40% 96%)',
                  border: '1px solid hsl(220 13% 91%)',
                  borderRadius: '0.25rem',
                  cursor: 'pointer',
                  color: 'hsl(215 25% 15%)'
                }}
              >
                {showDebugInfo ? 'Hide Debug' : 'Show Debug'}
              </button> */}
            </div>

            {/* Debug Information Panel */}
            {showDebugInfo && (
              <div style={{
                marginBottom: '1rem',
                padding: '1rem',
                backgroundColor: 'hsl(210 40% 98%)',
                border: '1px solid hsl(220 13% 91%)',
                borderRadius: '0.5rem',
                fontSize: '0.8rem'
              }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: 'hsl(198 88% 32%)' }}>Debug Info:</h4>
                <div><strong>Client ID:</strong> {getClientId()}</div>
                <div><strong>Available SDEs Count:</strong> {sdes.length}</div>
                <div><strong>Selected IDs Count:</strong> {selectedSDEIds.size}</div>
                <div><strong>All Selected SDEs Count:</strong> {allSelectedSDEs.length}</div>
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Raw Driver API Response</summary>
                  <pre style={{
                    marginTop: '0.5rem',
                    padding: '0.5rem',
                    backgroundColor: 'hsl(0 0% 100%)',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.25rem',
                    fontSize: '0.7rem',
                    overflow: 'auto',
                    maxHeight: '200px'
                  }}>
                    {JSON.stringify(allSelectedSDEs, null, 2)}
                  </pre>
                </details>
              </div>
            )}
            
            <div className="selected-sdes-container" style={{ 
              maxHeight: '400px', 
              overflowY: 'auto',
              marginBottom: '2rem',
              width: '100%'
            }}>
              {allSelectedSDEs.length > 0 ? (
                <div className="selected-sdes-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {allSelectedSDEs.map((selectedSde, index) => {
                    // Try to find matching SDE in current available SDEs for additional info
                    const matchingSde = sdes.find(sde => sde.name === selectedSde.pattern_name);
                    const isAvailableInCurrentIndustry = !!matchingSde;

                    return (
                      <div key={`${selectedSde.pattern_name}-${index}`} className="selected-sde-item" style={{
                        padding: '1.25rem',
                        backgroundColor: isAvailableInCurrentIndustry ? 'hsl(210 40% 96%)' : 'hsl(45 100% 96%)',
                        borderRadius: '0.5rem',
                        border: `1px solid ${isAvailableInCurrentIndustry ? 'hsl(220 13% 91%)' : 'hsl(45 100% 85%)'}`,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                        transition: 'all 0.2s ease'
                      }}>
                        <div>
                          <div style={{ fontWeight: '600', color: 'hsl(215 25% 15%)', fontSize: '1.1rem' }}>
                            {selectedSde.pattern_name}
                            {!isAvailableInCurrentIndustry && (
                              <span style={{
                                fontSize: '0.85rem',
                                color: 'hsl(45 100% 40%)',
                                marginLeft: '0.5rem',
                                fontWeight: '500'
                              }}>
                                (Different Industry)
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.9rem', color: 'hsl(215 16% 47%)', marginTop: '0.5rem' }}>
                            Sensitivity: {selectedSde.sensitivity || 'N/A'}
                            {selectedSde.protection_method && (
                              <span style={{ marginLeft: '0.75rem' }}>
                                | Protection: {selectedSde.protection_method}
                              </span>
                            )}
                          </div>
                          {matchingSde && (
                            <div style={{ fontSize: '0.85rem', color: 'hsl(215 16% 47%)', marginTop: '0.5rem' }}>
                              Industry: {matchingSde.industry_classification === 'all_industries' ? 'All Industries' : matchingSde.industry_classification}
                            </div>
                          )}
                        </div>
                        {/* Remove button */}
                        <button
                          className="small-button"
                          onClick={() => handleRemoveSDE(matchingSde?.id || selectedSde.pattern_name, selectedSde.pattern_name)}
                          style={{
                            alignSelf: 'flex-end',
                            marginTop: '0.5rem',
                            padding: '0.4rem 0.8rem',
                            fontSize: '0.85rem',
                            borderRadius: '0.3rem',
                            backgroundColor: 'hsl(0 84% 60%)',
                            color: 'white',
                            border: 'none',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease'
                          }}
                          onMouseEnter={(e) => e.target.style.backgroundColor = 'hsl(0 84% 50%)'}
                          onMouseLeave={(e) => e.target.style.backgroundColor = 'hsl(0 84% 60%)'}
                        >
                          <Trash2 size={16} style={{ verticalAlign: 'middle', marginRight: '0.2rem' }} /> Remove
                        </button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '2rem',
                  color: 'hsl(215 16% 47%)',
                  backgroundColor: 'hsl(210 40% 96%)',
                  borderRadius: '0.5rem',
                  border: '2px dashed hsl(220 13% 91%)'
                }}>
                  <CheckSquare size={48} style={{ opacity: 0.4, marginBottom: '1rem' }} />
                  <p style={{ margin: 0, fontSize: '1rem' }}>
                    No SDEs selected yet.<br />
                    Select SDEs from the left panel or check if you have SDEs selected in other industries.
                  </p>
                </div>
              )}
            </div>

            {/* Clear All Selected SDEs Button */}
            {allSelectedSDEs.length > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginTop: '1rem',
                paddingTop: '1rem',
                borderTop: '1px solid hsl(220 13% 91%)'
              }}>
                <button
                  onClick={handleClearAllSelectedSDEs}
                  style={{
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: '600',
                    backgroundColor: 'hsl(0 84% 60%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    boxShadow: '0 2px 4px 0 hsl(215 25% 15% / 0.1)'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'hsl(0 84% 50%)';
                    e.target.style.transform = 'translateY(-1px)';
                    e.target.style.boxShadow = '0 4px 8px 0 hsl(215 25% 15% / 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'hsl(0 84% 60%)';
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 2px 4px 0 hsl(215 25% 15% / 0.1)';
                  }}
                >
                  <Trash2 size={18} />
                  Clear All Selected SDEs
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      )} {/* End of selection view */}

      {/* Selected SDEs View */}
      {activeView === 'selected' && (
        <div style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
          {/* Success Banner - Shows after successful save */}
          {justSavedSDEs && (
            <div style={{
              background: 'linear-gradient(135deg, hsl(142 76% 47%), hsl(142 76% 43%))',
              color: 'white',
              padding: '1.5rem',
              borderRadius: '12px',
              marginBottom: '2rem',
              textAlign: 'center',
              boxShadow: '0 4px 12px hsl(142 76% 47% / 0.3)',
              border: '1px solid hsl(142 76% 43%)',
              animation: 'slideInFromTop 0.5s ease-out'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.75rem',
                marginBottom: '0.5rem'
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '700' }}>
                  SDEs Successfully Saved!
                </h3>
              </div>
              <p style={{ 
                margin: 0, 
                fontSize: '1rem',
                opacity: 0.9,
                fontWeight: '500'
              }}>
                Your SDE selections have been saved and are now displayed below. You can continue to modify your selections at any time.
              </p>
            </div>
          )}
          
          {/* Info Section for Selected View */}
          <div style={{ 
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(10px)',
            padding: '1.5rem', 
            borderRadius: '12px', 
            marginBottom: '2rem',
            textAlign: 'center',
            border: '1px solid rgba(226, 232, 240, 0.5)',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
          }}>
            <p style={{ 
              margin: 0, 
              color: '#475569',
              fontSize: '1.1rem'
            }}>
              <strong style={{ color: 'hsl(198 88% 32%)' }}>Selected SDEs Overview</strong> - View and manage your selected Sensitive Data Entities with detailed information and options to add or remove.
            </p>
          </div>

          {/* Selected SDEs Analytics & Management */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '2.5rem',
            borderRadius: '16px',
            border: '1px solid rgba(226, 232, 240, 0.5)',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            marginBottom: '2rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h2 style={{
                fontSize: '1.875rem',
                fontWeight: '700',
                color: '#1f2937',
                margin: '0',
                display: 'flex',
                alignItems: 'center'
              }}>
                <CheckSquare size={32} style={{ marginRight: '12px', color: 'hsl(198 88% 32%)' }} />
                Selected SDEs ({allSelectedSDEs.length})
              </h2>
              {/* <button
                onClick={() => setShowDebugInfo(!showDebugInfo)}
                style={{
                  padding: '0.5rem 1rem',
                  fontSize: '0.875rem',
                  backgroundColor: 'hsl(210 40% 96%)',
                  border: '1px solid hsl(220 13% 91%)',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  color: 'hsl(215 25% 15%)',
                  fontWeight: '500'
                }}
              >
                {showDebugInfo ? 'Hide Debug' : 'Show Debug'}
              </button> */}
            </div>

            {/* Debug Information Panel */}
            {showDebugInfo && (
              <div style={{
                marginBottom: '2rem',
                padding: '1rem',
                backgroundColor: 'hsl(210 40% 98%)',
                border: '1px solid hsl(220 13% 91%)',
                borderRadius: '0.5rem',
                fontSize: '0.85rem'
              }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: 'hsl(198 88% 32%)' }}>Debug Info:</h4>
                <div><strong>Client ID:</strong> {getClientId()}</div>
                <div><strong>Available SDEs Count:</strong> {sdes.length}</div>
                <div><strong>Selected IDs Count:</strong> {selectedSDEIds.size}</div>
                <div><strong>All Selected SDEs Count:</strong> {allSelectedSDEs.length}</div>
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Raw Driver API Response</summary>
                  <pre style={{
                    marginTop: '0.5rem',
                    padding: '0.5rem',
                    backgroundColor: 'hsl(0 0% 100%)',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    maxHeight: '200px'
                  }}>
                    {JSON.stringify(allSelectedSDEs, null, 2)}
                  </pre>
                </details>
              </div>
            )}

            {/* Selected SDEs Table */}
            {allSelectedSDEs.length > 0 ? (
              <div style={{
                overflowX: 'auto',
                borderRadius: '12px',
                border: '1px solid #e5e7eb',
                marginBottom: '2rem'
              }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  background: 'white'
                }}>
                  <thead>
                    <tr style={{
                      background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)'
                    }}>
                      <th style={{
                        padding: '1rem',
                        textAlign: 'left',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '2px solid #e5e7eb'
                      }}>SDE Name</th>
                      <th style={{
                        padding: '1rem',
                        textAlign: 'left',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '2px solid #e5e7eb'
                      }}>Sensitivity</th>
                      <th style={{
                        padding: '1rem',
                        textAlign: 'left',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '2px solid #e5e7eb'
                      }}>Industry</th>
                      <th style={{
                        padding: '1rem',
                        textAlign: 'left',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '2px solid #e5e7eb'
                      }}>Protection Method</th>
                      <th style={{
                        padding: '1rem',
                        textAlign: 'center',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '2px solid #e5e7eb'
                      }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allSelectedSDEs.map((selectedSde, index) => {
                      // Try to find matching SDE in current available SDEs for additional info
                      const matchingSde = sdes.find(sde => sde.name === selectedSde.pattern_name);
                      const isAvailableInCurrentIndustry = !!matchingSde;

                      return (
                        <tr key={`${selectedSde.pattern_name}-${index}`} style={{
                          background: index % 2 === 0 ? 'white' : '#f9fafb',
                          transition: 'all 0.2s'
                        }}>
                          <td style={{
                            padding: '1rem',
                            borderBottom: '1px solid #e5e7eb',
                            fontWeight: '500'
                          }}>
                            {selectedSde.pattern_name}
                            {!isAvailableInCurrentIndustry && (
                              <span style={{
                                fontSize: '0.75rem',
                                color: 'hsl(45 100% 40%)',
                                marginLeft: '0.5rem',
                                fontWeight: '500',
                                backgroundColor: 'hsl(45 100% 96%)',
                                padding: '0.125rem 0.375rem',
                                borderRadius: '0.25rem'
                              }}>
                                Different Industry
                              </span>
                            )}
                          </td>
                          <td style={{
                            padding: '1rem',
                            borderBottom: '1px solid #e5e7eb',
                            color: '#6b7280'
                          }}>
                            <span style={{
                              background: selectedSde.sensitivity === 'High' ? '#fee2e2' : 
                                          selectedSde.sensitivity === 'Medium' ? '#fef3c7' : '#dcfce7',
                              color: selectedSde.sensitivity === 'High' ? '#dc2626' : 
                                     selectedSde.sensitivity === 'Medium' ? '#d97706' : '#16a34a',
                              padding: '0.25rem 0.75rem',
                              borderRadius: '20px',
                              fontSize: '0.875rem',
                              fontWeight: '500'
                            }}>
                              {selectedSde.sensitivity || 'N/A'}
                            </span>
                          </td>
                          <td style={{
                            padding: '1rem',
                            borderBottom: '1px solid #e5e7eb',
                            color: '#6b7280',
                            fontSize: '0.875rem'
                          }}>
                            {matchingSde ? (
                              <span style={{
                                background: matchingSde.industry_classification === 'all_industries' ? '#f0f9ff' : '#dbeafe',
                                color: matchingSde.industry_classification === 'all_industries' ? '#0369a1' : '#1e40af',
                                padding: '0.25rem 0.75rem',
                                borderRadius: '20px',
                                fontSize: '0.875rem',
                                fontWeight: '500'
                              }}>
                                {matchingSde.industry_classification === 'all_industries' ? 'All Industries' : matchingSde.industry_classification}
                              </span>
                            ) : (
                              <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>Unknown</span>
                            )}
                          </td>
                          <td style={{
                            padding: '1rem',
                            borderBottom: '1px solid #e5e7eb',
                            color: '#6b7280',
                            fontSize: '0.875rem'
                          }}>
                            {selectedSde.protection_method ? (
                              <span style={{
                                background: '#f0fdf4',
                                color: '#15803d',
                                padding: '0.25rem 0.75rem',
                                borderRadius: '20px',
                                fontSize: '0.875rem',
                                fontWeight: '500'
                              }}>
                                {selectedSde.protection_method}
                              </span>
                            ) : (
                              <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>Not Set</span>
                            )}
                          </td>
                          <td style={{
                            padding: '1rem',
                            borderBottom: '1px solid #e5e7eb',
                            textAlign: 'center'
                          }}>
                            <button
                              onClick={() => handleRemoveSDE(matchingSde?.id || selectedSde.pattern_name, selectedSde.pattern_name)}
                              style={{
                                padding: '0.5rem 1rem',
                                background: 'hsl(0 84% 60%)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontSize: '0.875rem',
                                fontWeight: '500',
                                transition: 'all 0.2s',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                margin: '0 auto'
                              }}
                              onMouseEnter={(e) => {
                                e.target.style.backgroundColor = 'hsl(0 84% 50%)';
                                e.target.style.transform = 'scale(1.05)';
                              }}
                              onMouseLeave={(e) => {
                                e.target.style.backgroundColor = 'hsl(0 84% 60%)';
                                e.target.style.transform = 'scale(1)';
                              }}
                            >
                              <Trash2 size={16} />
                              Remove
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '3rem',
                color: 'hsl(215 16% 47%)',
                backgroundColor: 'hsl(210 40% 96%)',
                borderRadius: '12px',
                border: '2px dashed hsl(220 13% 91%)',
                marginBottom: '2rem'
              }}>
                <CheckSquare size={64} style={{ opacity: 0.4, marginBottom: '1rem' }} />
                <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: '600' }}>
                  No SDEs Selected
                </h3>
                <p style={{ margin: '0 0 1.5rem 0', fontSize: '1rem' }}>
                  You haven't selected any Sensitive Data Entities yet.
                </p>
                <button
                  onClick={() => setActiveView('selection')}
                  style={{
                    padding: '0.75rem 1.5rem',
                    backgroundColor: 'hsl(198 88% 32%)',
                    color: 'hsl(0 0% 98%)',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = 'hsl(198 88% 28%)'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'hsl(198 88% 32%)'}
                >
                  Go to Select SDEs
                </button>
              </div>
            )}

            {/* Clear All Selected SDEs Button */}
            {allSelectedSDEs.length > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginTop: '1rem',
                paddingTop: '1rem',
                borderTop: '1px solid hsl(220 13% 91%)'
              }}>
                <button
                  onClick={handleClearAllSelectedSDEs}
                  style={{
                    padding: '0.75rem 2rem',
                    fontSize: '1rem',
                    fontWeight: '600',
                    backgroundColor: 'hsl(0 84% 60%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    boxShadow: '0 2px 4px 0 hsl(215 25% 15% / 0.1)'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'hsl(0 84% 50%)';
                    e.target.style.transform = 'translateY(-1px)';
                    e.target.style.boxShadow = '0 4px 8px 0 hsl(215 25% 15% / 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'hsl(0 84% 60%)';
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 2px 4px 0 hsl(215 25% 15% / 0.1)';
                  }}
                >
                  <Trash2 size={18} />
                  Clear All Selected SDEs
                </button>
              </div>
            )}
          </div>
        </div>
      )} {/* End of selected view */}

      {/* Responsive Add SDE Modal */}
      {showAddModal && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 99999,
            padding: '1rem'
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              handleCloseAddModal();
            }
          }}
        >
          <div style={{
            backgroundColor: 'hsl(0 0% 100%)',
            borderRadius: '0.75rem',
            padding: '2rem',
            width: '100%',
            maxWidth: '500px',
            maxHeight: '90vh',
            overflowY: 'auto',
            boxShadow: '0 25px 50px -12px hsl(215 25% 15% / 0.4)',
            border: '1px solid hsl(220 13% 91%)',
            position: 'relative',
            zIndex: 100000
          }}>
            <h2 style={{
              color: 'hsl(198 88% 32%)',
              fontSize: '1.5rem',
              fontWeight: '600',
              margin: '0 0 1.5rem 0',
              textAlign: 'center'
            }}>Add New SDE</h2>
            
            <form onSubmit={handleAddSDESubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ 
                  fontWeight: '500', 
                  color: 'hsl(215 25% 15%)',
                  fontSize: '0.9rem'
                }}>Name</label>
                <input 
                  name="name" 
                  value={addSDEForm.name} 
                  onChange={handleAddSDEChange}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                />
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ 
                  fontWeight: '500', 
                  color: 'hsl(215 25% 15%)',
                  fontSize: '0.9rem'
                }}>Data Type</label>
                <input 
                  name="data_type" 
                  value={addSDEForm.data_type} 
                  onChange={handleAddSDEChange}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                />
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ 
                  fontWeight: '500', 
                  color: 'hsl(215 25% 15%)',
                  fontSize: '0.9rem'
                }}>Sensitivity</label>
                <select 
                  name="sensitivity" 
                  value={addSDEForm.sensitivity} 
                  onChange={handleAddSDEChange}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    backgroundColor: 'hsl(0 0% 100%)'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                >
                  <option value="">Select Sensitivity</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ 
                  fontWeight: '500', 
                  color: 'hsl(215 25% 15%)',
                  fontSize: '0.9rem'
                }}>Regex</label>
                <input 
                  name="regex" 
                  value={addSDEForm.regex} 
                  onChange={handleAddSDEChange}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                />
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ 
                  fontWeight: '500', 
                  color: 'hsl(215 25% 15%)',
                  fontSize: '0.9rem'
                }}>Classification</label>
                <select 
                  name="classification" 
                  value={addSDEForm.classification} 
                  onChange={handleAddSDEChange}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    backgroundColor: 'hsl(0 0% 100%)'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                >
                  <option value="">Select Classification</option>
                  <option value="Confidential">Confidential</option>
                  <option value="Restricted">Restricted</option>
                  <option value="Normal">Normal</option>
                </select>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ 
                  fontWeight: '500', 
                  color: 'hsl(215 25% 15%)',
                  fontSize: '0.9rem'
                }}>Industry</label>
                <select 
                  name="selected_industry" 
                  value={addSDEForm.selected_industry} 
                  onChange={handleAddSDEChange}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    backgroundColor: 'hsl(0 0% 100%)'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'hsl(198 88% 32%)'}
                  onBlur={(e) => e.target.style.borderColor = 'hsl(220 13% 91%)'}
                >
                  <option value="">Select Industry</option>
                  {industryOptions.map(opt => (
                    <option key={opt} value={opt}>{opt.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
                  ))}
                </select>
              </div>
              
              {addSDEError && (
                <div style={{
                  padding: '0.75rem',
                  backgroundColor: 'hsl(0 84% 60% / 0.1)',
                  borderRadius: '0.5rem',
                  border: '1px solid hsl(0 84% 60%)',
                  color: 'hsl(0 84% 60%)',
                  fontSize: '0.9rem'
                }}>
                  {addSDEError}
                </div>
              )}
              
              <div style={{ 
                display: 'flex', 
                gap: '1rem', 
                marginTop: '1rem',
                flexWrap: 'wrap'
              }}>
                <button 
                  type="button" 
                  onClick={handleCloseAddModal}
                  style={{
                    flex: '1',
                    minWidth: '120px',
                    padding: '0.75rem 1.5rem',
                    backgroundColor: 'hsl(210 40% 96%)',
                    color: 'hsl(215 25% 15%)',
                    border: '1px solid hsl(220 13% 91%)',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'hsl(210 40% 92%)';
                    e.target.style.borderColor = 'hsl(220 13% 87%)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'hsl(210 40% 96%)';
                    e.target.style.borderColor = 'hsl(220 13% 91%)';
                  }}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={addSDELoading}
                  style={{
                    flex: '1',
                    minWidth: '120px',
                    padding: '0.75rem 1.5rem',
                    backgroundColor: addSDELoading ? 'hsl(220 13% 91%)' : 'hsl(198 88% 32%)',
                    color: 'hsl(0 0% 98%)',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    fontWeight: '600',
                    cursor: addSDELoading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    opacity: addSDELoading ? 0.7 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (!addSDELoading) {
                      e.target.style.backgroundColor = 'hsl(198 88% 28%)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!addSDELoading) {
                      e.target.style.backgroundColor = 'hsl(198 88% 32%)';
                    }
                  }}
                >
                  {addSDELoading ? 'Adding...' : 'Preview SDE'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SDE Preview Confirmation Modal */}
      {showPreviewModal && previewSDE && Object.keys(previewSDE).length > 0 && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            zIndex: 999999,
            padding: '2rem 1rem 1rem 1rem',
            paddingTop: '2rem'
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              handleClosePreview();
            }
          }}
        >
          <div style={{
            backgroundColor: 'hsl(0 0% 100%)',
            borderRadius: '0.75rem',
            padding: '2.5rem',
            width: '100%',
            maxWidth: '600px',
            maxHeight: '90vh',
            overflowY: 'auto',
            boxShadow: '0 25px 50px -12px hsl(215 25% 15% / 0.4)',
            border: '1px solid hsl(220 13% 91%)',
            position: 'relative',
            zIndex: 100000
          }}>
            {/* Header */}
            <div style={{
              textAlign: 'center',
              marginBottom: '2rem',
              paddingBottom: '1.5rem',
              borderBottom: '1px solid hsl(220 13% 91%)'
            }}>
              <div style={{
                width: '64px',
                height: '64px',
                backgroundColor: 'hsl(142 76% 47%)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem auto',
                boxShadow: '0 4px 12px hsl(142 76% 47% / 0.3)'
              }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
              </div>
              <h2 style={{
                color: 'hsl(198 88% 32%)',
                fontSize: '1.875rem',
                fontWeight: '700',
                margin: '0 0 0.5rem 0'
              }}>
                Confirm New SDE
              </h2>
              <p style={{
                color: 'hsl(215 16% 47%)',
                fontSize: '1rem',
                margin: '0',
                maxWidth: '400px',
                marginLeft: 'auto',
                marginRight: 'auto'
              }}>
                Please review the details of the new Sensitive Data Entity before adding it to your catalogue.
              </p>
            </div>

            {/* SDE Preview Card */}
            <div style={{
              background: 'linear-gradient(135deg, hsl(210 40% 98%) 0%, hsl(220 69% 98%) 100%)',
              border: '2px solid hsl(198 88% 32%)',
              borderRadius: '12px',
              padding: '2rem',
              marginBottom: '2rem',
              position: 'relative',
              overflow: 'hidden'
            }}>
              {/* Background decoration */}
              <div style={{
                position: 'absolute',
                top: '-50px',
                right: '-50px',
                width: '100px',
                height: '100px',
                background: 'hsl(198 88% 32% / 0.05)',
                borderRadius: '50%'
              }}></div>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1.5rem',
                position: 'relative',
                zIndex: 1
              }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'hsl(198 88% 32%)',
                    marginBottom: '0.5rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    SDE Name
                  </label>
                  <div style={{
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    color: 'hsl(215 25% 15%)',
                    backgroundColor: 'hsl(0 0% 100%)',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    border: '1px solid hsl(220 13% 91%)'
                  }}>
                    {previewSDE.name}
                  </div>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'hsl(198 88% 32%)',
                    marginBottom: '0.5rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Data Type
                  </label>
                  <div style={{
                    fontSize: '1.125rem',
                    fontWeight: '500',
                    color: 'hsl(215 25% 15%)',
                    backgroundColor: 'hsl(0 0% 100%)',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    border: '1px solid hsl(220 13% 91%)'
                  }}>
                    {previewSDE.data_type}
                  </div>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'hsl(198 88% 32%)',
                    marginBottom: '0.5rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Sensitivity Level
                  </label>
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    fontSize: '1rem',
                    fontWeight: '600',
                    color: 'hsl(0 0% 100%)',
                    backgroundColor: previewSDE.sensitivity === 'High' ? 'hsl(0 84% 60%)' : 
                                   previewSDE.sensitivity === 'Medium' ? 'hsl(45 93% 47%)' : 
                                   'hsl(142 76% 47%)',
                    padding: '0.75rem 1rem',
                    borderRadius: '2rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    {previewSDE.sensitivity}
                  </div>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'hsl(198 88% 32%)',
                    marginBottom: '0.5rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Classification
                  </label>
                  <div style={{
                    fontSize: '1.125rem',
                    fontWeight: '500',
                    color: 'hsl(215 25% 15%)',
                    backgroundColor: 'hsl(0 0% 100%)',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    border: '1px solid hsl(220 13% 91%)'
                  }}>
                    {previewSDE.classification}
                  </div>
                </div>

                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'hsl(198 88% 32%)',
                    marginBottom: '0.5rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Industry
                  </label>
                  <div style={{
                    fontSize: '1.125rem',
                    fontWeight: '500',
                    color: 'hsl(215 25% 15%)',
                    backgroundColor: 'hsl(0 0% 100%)',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    border: '1px solid hsl(220 13% 91%)'
                  }}>
                    {previewSDE.selected_industry.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </div>
                </div>

                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'hsl(198 88% 32%)',
                    marginBottom: '0.5rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Detection Pattern (Regex)
                  </label>
                  <div style={{
                    fontSize: '0.95rem',
                    fontWeight: '400',
                    color: 'hsl(215 25% 15%)',
                    backgroundColor: 'hsl(210 40% 96%)',
                    padding: '1rem',
                    borderRadius: '0.5rem',
                    border: '1px solid hsl(220 13% 91%)',
                    fontFamily: 'Monaco, "Lucida Console", monospace',
                    wordBreak: 'break-all',
                    lineHeight: '1.5'
                  }}>
                    {previewSDE.regex}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ 
              display: 'flex', 
              gap: '1rem', 
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button 
                type="button" 
                onClick={handleClosePreview}
                style={{
                  flex: '1',
                  minWidth: '140px',
                  maxWidth: '200px',
                  padding: '0.875rem 1.5rem',
                  backgroundColor: 'hsl(210 40% 96%)',
                  color: 'hsl(215 25% 15%)',
                  border: '1px solid hsl(220 13% 91%)',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'hsl(210 40% 92%)';
                  e.target.style.borderColor = 'hsl(220 13% 85%)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'hsl(210 40% 96%)';
                  e.target.style.borderColor = 'hsl(220 13% 91%)';
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M11 17l-5-5 1.5-1.5L11 14l7-7 1.5 1.5L11 17z"/>
                </svg>
                Edit Details
              </button>
              
              <button 
                type="button" 
                onClick={handleConfirmAddSDE}
                disabled={addSDELoading}
                style={{
                  flex: '1',
                  minWidth: '140px',
                  maxWidth: '200px',
                  padding: '0.875rem 1.5rem',
                  backgroundColor: addSDELoading ? 'hsl(220 13% 91%)' : 'hsl(142 76% 47%)',
                  color: 'hsl(0 0% 98%)',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  fontWeight: '700',
                  cursor: addSDELoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  opacity: addSDELoading ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  boxShadow: addSDELoading ? 'none' : '0 4px 12px hsl(142 76% 47% / 0.3)'
                }}
                onMouseEnter={(e) => {
                  if (!addSDELoading) {
                    e.target.style.backgroundColor = 'hsl(142 76% 43%)';
                    e.target.style.transform = 'translateY(-1px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!addSDELoading) {
                    e.target.style.backgroundColor = 'hsl(142 76% 47%)';
                    e.target.style.transform = 'translateY(0)';
                  }
                }}
              >
                {addSDELoading ? (
                  <>
                    <div style={{
                      width: '16px',
                      height: '16px',
                      border: '2px solid transparent',
                      borderTop: '2px solid white',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></div>
                    Adding...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 6L9 17l-5-5"/>
                    </svg>
                    Confirm & Add SDE
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Save SDEs Preview Confirmation Modal */}
      {showSavePreviewModal && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            zIndex: 999999,
            padding: '2rem 1rem 1rem 1rem',
            paddingTop: '2rem'
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              handleCloseSavePreview();
            }
          }}
        >
          <div style={{
            backgroundColor: 'hsl(0 0% 100%)',
            borderRadius: '0.75rem',
            padding: '2.5rem',
            width: '100%',
            maxWidth: '800px',
            maxHeight: '90vh',
            overflowY: 'auto',
            boxShadow: '0 25px 50px -12px hsl(215 25% 15% / 0.4)',
            border: '1px solid hsl(220 13% 91%)',
            position: 'relative',
            zIndex: 100000
          }}>
            {/* Header */}
            <div style={{
              textAlign: 'center',
              marginBottom: '2rem',
              paddingBottom: '1.5rem',
              borderBottom: '1px solid hsl(220 13% 91%)'
            }}>
              <div style={{
                width: '64px',
                height: '64px',
                backgroundColor: 'hsl(198 88% 32%)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem auto',
                boxShadow: '0 4px 12px hsl(198 88% 32% / 0.3)'
              }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                  <polyline points="17,21 17,13 7,13 7,21"/>
                  <polyline points="7,3 7,8 15,8"/>
                </svg>
              </div>
              <h2 style={{
                color: 'hsl(198 88% 32%)',
                fontSize: '1.875rem',
                fontWeight: '700',
                margin: '0 0 0.5rem 0'
              }}>
                Confirm SDE Selection Save
              </h2>
              <p style={{
                color: 'hsl(215 16% 47%)',
                fontSize: '1rem',
                margin: '0',
                maxWidth: '500px',
                marginLeft: 'auto',
                marginRight: 'auto'
              }}>
                {savePreviewSDEs.length > 0 
                  ? `You are about to save ${savePreviewSDEs.length} new SDE${savePreviewSDEs.length !== 1 ? 's' : ''} to your profile. Please review your selection below before confirming.`
                  : 'All selected SDEs are already saved to your profile.'
                }
              </p>
            </div>

            {/* Conditional Content */}
            {savePreviewSDEs.length > 0 ? (
              <>
                {/* Summary Stats - Only show total count */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  marginBottom: '2rem',
                  padding: '1.5rem',
                  backgroundColor: 'hsl(210 40% 98%)',
                  borderRadius: '12px',
                  border: '1px solid hsl(220 13% 91%)'
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', fontWeight: '700', color: 'hsl(198 88% 32%)' }}>
                      {savePreviewSDEs.length}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'hsl(215 16% 47%)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '500' }}>
                      New SDEs to Save
                    </div>
                  </div>
                </div>

            {/* SDEs Table */}
            <div style={{
              overflowX: 'auto',
              borderRadius: '12px',
              border: '1px solid #e5e7eb',
              marginBottom: '2rem',
              maxHeight: '400px',
              overflowY: 'auto'
            }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                background: 'white'
              }}>
                <thead>
                  <tr style={{
                    background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)',
                    position: 'sticky',
                    top: 0,
                    zIndex: 1
                  }}>
                    <th style={{
                      padding: '1rem',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>SDE Name</th>
                    <th style={{
                      padding: '1rem',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>Industry</th>
                    <th style={{
                      padding: '1rem',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>Data Type</th>
                  </tr>
                </thead>
                <tbody>
                  {savePreviewSDEs.map((sde, index) => (
                    <tr key={sde.id || index} style={{
                      backgroundColor: index % 2 === 0 ? 'white' : '#f9fafb',
                      borderBottom: '1px solid #e5e7eb'
                    }}>
                      <td style={{
                        padding: '1rem',
                        fontWeight: '500',
                        color: '#1f2937'
                      }}>
                        {sde.name}
                      </td>
                      <td style={{
                        padding: '1rem',
                        color: '#6b7280',
                        fontSize: '0.9rem'
                      }}>
                        {sde.industry_classification?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Not specified'}
                      </td>
                      <td style={{
                        padding: '1rem',
                        color: '#6b7280',
                        fontSize: '0.9rem'
                      }}>
                        {sde.data_type || 'Not specified'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </> // End of conditional content for new SDEs
            ) : (
              // Content when no new SDEs
              <div style={{
                textAlign: 'center',
                padding: '2rem',
                color: 'hsl(215 16% 47%)'
              }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
                <p style={{ fontSize: '1.1rem', margin: '0' }}>
                  All your selected SDEs are already saved to your profile. No new SDEs to add!
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ 
              display: 'flex', 
              gap: '1rem', 
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button 
                type="button" 
                onClick={handleCloseSavePreview}
                style={{
                  flex: '1',
                  minWidth: '140px',
                  maxWidth: '200px',
                  padding: '0.875rem 1.5rem',
                  backgroundColor: 'hsl(210 40% 96%)',
                  color: 'hsl(215 25% 15%)',
                  border: '1px solid hsl(220 13% 91%)',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'hsl(210 40% 92%)';
                  e.target.style.borderColor = 'hsl(220 13% 85%)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'hsl(210 40% 96%)';
                  e.target.style.borderColor = 'hsl(220 13% 91%)';
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M15 18l-6-6 6-6"/>
                </svg>
                Cancel
              </button>
              
              {savePreviewSDEs.length > 0 && (
                <button 
                  type="button" 
                  onClick={handleConfirmSaveSDEs}
                  disabled={loading}
                  style={{
                    flex: '1',
                    minWidth: '140px',
                    maxWidth: '200px',
                    padding: '0.875rem 1.5rem',
                    backgroundColor: loading ? 'hsl(220 13% 91%)' : 'hsl(198 88% 32%)',
                    color: 'hsl(0 0% 98%)',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontSize: '1rem',
                    fontWeight: '700',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    opacity: loading ? 0.7 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    boxShadow: loading ? 'none' : '0 4px 12px hsl(198 88% 32% / 0.3)'
                  }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.target.style.backgroundColor = 'hsl(198 88% 28%)';
                    e.target.style.transform = 'translateY(-1px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading) {
                    e.target.style.backgroundColor = 'hsl(198 88% 32%)';
                    e.target.style.transform = 'translateY(0)';
                  }
                }}
              >
                {loading ? (
                  <>
                    <div style={{
                      width: '16px',
                      height: '16px',
                      border: '2px solid transparent',
                      borderTop: '2px solid white',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                      <polyline points="17,21 17,13 7,13 7,21"/>
                      <polyline points="7,3 7,8 15,8"/>
                    </svg>
                    Confirm & Save {savePreviewSDEs.length} SDE{savePreviewSDEs.length !== 1 ? 's' : ''}
                  </>
                )}
              </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="card" style={{ 
        maxWidth: '800px', 
        alignItems: 'center',
        margin: '3rem auto 2rem auto',
        width: '100%'
      }}>
        {isSignupFlow && (
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', width: '100%', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate('/signup')}
              className="enhanced-button enhanced-button-secondary"
              style={{ 
                flex: '1 1 200px', 
                maxWidth: '220px',
                minWidth: '180px'
              }}
            >
              ← Back to Signup
            </button>
            <button
              onClick={saveSDEs}
              className="enhanced-button enhanced-button-secondary"
              disabled={selectedSDEIds.size === 0 || loading}
              style={{
                flex: '1 1 200px',
                maxWidth: '220px',
                minWidth: '180px'
              }}
            >
              {loading ? 'Saving...' : 'Preview & Save SDEs'}
            </button>
            <button
              onClick={handleSdeCatalogueSaveAndContinue}
              className="enhanced-button enhanced-button-primary"
              style={{ 
                flex: '1 1 200px', 
                maxWidth: '220px',
                minWidth: '180px'
              }}
            >
              Continue to Model Registry →
            </button>
          </div>
        )}
        {!isSignupFlow && (
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', width: '100%', flexWrap: 'wrap' }}>
            <button
              onClick={saveSDEs}
              className="enhanced-button enhanced-button-secondary"
              disabled={selectedSDEIds.size === 0 || loading}
              style={{
                flex: '1 1 200px',
                maxWidth: '220px',
                minWidth: '180px'
              }}
            >
              {loading ? 'Saving...' : 'Preview & Save SDEs'}
            </button>
            <button
              onClick={handleSdeCatalogueSaveAndContinue}
              className="enhanced-button enhanced-button-primary"
              style={{ 
                flex: '1 1 200px', 
                maxWidth: '220px',
                minWidth: '180px'
              }}
            >
              Return to Dashboard
            </button>
          </div>
        )}
      </div>

      {showToast && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 9999,
          pointerEvents: 'none',
        }}>
          <div
            className={
              submissionMessage.toLowerCase().includes('success') || submissionMessage.toLowerCase().includes('added')
                ? 'toast-success'
                : submissionMessage.toLowerCase().includes('error') || submissionMessage.toLowerCase().includes('fail') || submissionMessage.toLowerCase().includes('required') || submissionMessage.toLowerCase().includes('invalid')
                  ? 'toast-error'
                  : 'toast-info'
            }
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              fontWeight: 500,
              fontSize: '0.9rem',
              pointerEvents: 'auto',
              maxWidth: '300px',
              wordWrap: 'break-word'
            }}
          >
            {submissionMessage}
          </div>
        </div>
      )}
    </div>
  );
}

export default SDECataloguePage;