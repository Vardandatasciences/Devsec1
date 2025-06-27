<template>
  <div class="risk-scoring-container">
    <!-- Page Heading -->
    <div class="page-heading">
      <h1>Risk Scoring</h1>
    </div>
    
    <!-- Search and Filter Bar -->
    <div class="filters-wrapper">
      <input 
        type="text" 
        v-model="searchQuery" 
        class="search-input" 
        placeholder="Search..."
        @input="validateSearchInput"
        :class="{'input-error': validationErrors.searchQuery}"
      />
      <div class="filter-dropdowns">
        <select v-model="statusFilter" class="filter-select" @change="validateFilterInput('statusFilter')">
          <option value="">All Status</option>
          <option v-for="status in uniqueStatuses" :key="status">{{ status }}</option>
        </select>
        <select v-model="categoryFilter" class="filter-select" @change="validateFilterInput('categoryFilter')">
          <option value="">All Categories</option>
          <option v-for="category in uniqueCategories" :key="category">{{ category }}</option>
        </select>
      </div>
    </div>
    
    <!-- Error message for validation errors -->
    <div v-if="hasValidationErrors" class="validation-error-summary">
      <p><i class="fas fa-exclamation-triangle"></i> Invalid input detected. Please correct the highlighted fields.</p>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Loading risk data...</span>
    </div>
    
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-else-if="filteredRiskInstances.length === 0" class="no-data">
      <p>No risk instances found.</p>
    </div>
    
    <div v-else class="table-responsive">
      <table class="risk-table">
        <thead>
          <tr>
            <th class="col-risk-id">Risk Instance ID</th>
            <th class="col-incident-id">Incident ID</th>
            <th class="col-compliance-id">Compliance ID</th>
            <th class="col-risk-title">Risk Title</th>
            <th class="col-category">Category</th>
            <th class="col-description">Risk Description</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="risk in filteredRiskInstances" :key="risk.RiskInstanceId">
            <td class="0">{{ risk.RiskInstanceId }}</td>
            <td class="col-incident-id">{{ risk.IncidentId || 'N/A' }}</td>
            <td class="col-compliance-id">{{ risk.ComplianceId || 'N/A' }}</td>
            <td class="col-risk-title">{{ risk.RiskTitle || 'No title' }}</td>
            <td class="col-category">{{ risk.Category || 'N/A' }}</td>
            <td class="col-description">{{ truncateText(risk.RiskDescription, 50) || 'N/A' }}</td>
            <td class="col-actions">
              <div v-if="isScoringCompleted(risk)" class="scoring-completed" @click="viewScoringDetails(risk.RiskInstanceId)">
                <span class="scoring-completed-text">Scoring Completed</span>
                <span class="icon view-icon" title="View Scoring Details">
                  <i class="fas fa-eye"></i>
                </span>
              </div>
              <div v-else-if="isRiskRejected(risk)" class="risk-rejected" @click="viewScoringDetails(risk.RiskInstanceId)">
                <span class="risk-rejected-text">Instance Rejected</span>
                <span class="icon view-icon" title="View Scoring Details">
                  <i class="fas fa-eye"></i>
                </span>
              </div>
              <div v-else-if="!showActionButtons[risk.RiskInstanceId]" class="action-icons">
                <span class="icon accept-icon" title="Accept Risk" @click="toggleActionButtons(risk.RiskInstanceId)">
                  <i class="fas fa-check-circle"></i>
                </span>
                <span class="icon reject-icon" title="Reject Risk" @click="rejectRisk(risk.RiskInstanceId)">
                  <i class="fas fa-times-circle"></i>
                </span>
              </div>
              <div v-else class="action-buttons">
                <button class="map-risk-btn map-risk-btn-full" @click="mapScoringRisk(risk.RiskInstanceId)">MAP SCORING RISK</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import './RiskScoring.css';
import { reactive } from 'vue';
import { validateField, sanitizeString } from './validation.js';

export default {
  name: 'RiskScoring',
  data() {
    return {
      riskInstances: [],
      filteredRiskInstances: [],
      loading: true,
      error: null,
      showActionButtons: reactive({}),
      searchQuery: '',
      statusFilter: '',
      categoryFilter: '',
      validationErrors: {} // Store validation errors
    }
  },
  computed: {
    uniqueStatuses() {
      return [...new Set(this.riskInstances
        .map(risk => risk.RiskStatus)
        .filter(status => status && status.trim() !== '')
      )];
    },
    uniqueCategories() {
      return [...new Set(this.riskInstances
        .map(risk => risk.Category)
        .filter(category => category && category.trim() !== '')
      )];
    },
    hasValidationErrors() {
      return Object.keys(this.validationErrors).length > 0;
    }
  },
  mounted() {
    this.fetchRiskInstances();
    
    // Add event listener for sidebar toggle to adjust container margin
    window.addEventListener('resize', this.handleResize);
    
    // Initial check for sidebar state
    this.handleResize();
    
    // Add Font Awesome if not already present
    if (!document.querySelector('link[href*="font-awesome"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
      document.head.appendChild(link);
    }
  },
  // Refresh data when component is activated (coming back from another route)
  activated() {
    console.log('RiskScoring component activated - refreshing data');
    this.fetchRiskInstances();
  },
  beforeUnmount() {
    // Clean up event listener
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    // Validate search input
    validateSearchInput() {
      const result = validateField(this.searchQuery, 'text');
      if (!result.isValid) {
        this.validationErrors.searchQuery = result.error;
      } else {
        delete this.validationErrors.searchQuery;
        this.filterRiskInstances();
      }
    },
    
    // Validate filter inputs
    validateFilterInput(field) {
      let value = this[field];
      let validationType;
      
      switch(field) {
        case 'statusFilter':
          validationType = 'riskStatus';
          break;
        case 'categoryFilter':
          validationType = 'category';
          break;
        default:
          validationType = 'text';
      }
      
      const result = validateField(value, validationType);
      if (!result.isValid) {
        this.validationErrors[field] = result.error;
      } else {
        delete this.validationErrors[field];
        this.filterRiskInstances();
      }
    },
    
    filterRiskInstances() {
      // If there are validation errors, don't apply filters
      if (this.hasValidationErrors) {
        return;
      }
      
      this.filteredRiskInstances = this.riskInstances.filter(risk => {
        // Search query filter
        const searchLower = this.searchQuery.toLowerCase();
        const matchesSearch = !this.searchQuery || 
          (risk.RiskInstanceId && risk.RiskInstanceId.toString().toLowerCase().includes(searchLower)) ||
          (risk.RiskTitle && risk.RiskTitle.toLowerCase().includes(searchLower)) ||
          (risk.Category && risk.Category.toLowerCase().includes(searchLower)) ||
          (risk.RiskStatus && risk.RiskStatus.toLowerCase().includes(searchLower)) ||
          (risk.RiskDescription && risk.RiskDescription.toLowerCase().includes(searchLower));
        
        // Status filter
        const matchesStatus = !this.statusFilter || risk.RiskStatus === this.statusFilter;
        
        // Category filter
        const matchesCategory = !this.categoryFilter || risk.Category === this.categoryFilter;
        
        return matchesSearch && matchesStatus && matchesCategory;
      });
    },
    
    // Validate and sanitize response data
    validateResponseData(data) {
      if (!Array.isArray(data)) {
        console.error('Expected array response, got:', typeof data);
        return [];
      }
      
      return data.map(item => {
        const sanitized = {};
        
        // Define expected fields and their types
        const expectedFields = {
          RiskInstanceId: 'id',
          IncidentId: 'id',
          ComplianceId: 'id',
          RiskTitle: 'text',
          Category: 'category',
          RiskDescription: 'longText',
          RiskStatus: 'riskStatus',
          RiskLikelihood: 'riskRating',
          RiskImpact: 'riskRating',
          RiskExposureRating: 'number',
          Appetite: 'appetite'
        };
        
        // Validate and sanitize each field
        for (const [field, validationType] of Object.entries(expectedFields)) {
          if (item[field] !== undefined) {
            const result = validateField(item[field], validationType);
            if (result.isValid) {
              sanitized[field] = typeof item[field] === 'string' ? 
                sanitizeString(item[field]) : item[field];
            } else {
              // If invalid, use a safe default value
              switch(validationType) {
                case 'id':
                  sanitized[field] = null;
                  break;
                case 'category':
                case 'riskStatus':
                case 'appetite':
                  sanitized[field] = '';
                  break;
                case 'text':
                case 'longText':
                  sanitized[field] = 'Invalid content';
                  break;
                case 'riskRating':
                case 'number':
                  sanitized[field] = 0;
                  break;
                default:
                  sanitized[field] = null;
              }
              console.warn(`Invalid ${field} value:`, item[field], result.error);
            }
          } else {
            // Field is missing, use default value
            switch(validationType) {
              case 'id':
                sanitized[field] = null;
                break;
              case 'category':
              case 'riskStatus':
              case 'appetite':
              case 'text':
              case 'longText':
                sanitized[field] = '';
                break;
              case 'riskRating':
              case 'number':
                sanitized[field] = 0;
                break;
              default:
                sanitized[field] = null;
            }
          }
        }
        
        return sanitized;
      });
    },
    
    isScoringCompleted(risk) {
      // Check if risk has RiskLikelihood, RiskImpact, and RiskExposureRating values
      // AND Appetite is 'Yes' (not rejected)
      const hasScoring = (
        risk.RiskLikelihood !== undefined && 
        risk.RiskLikelihood !== null && 
        risk.RiskImpact !== undefined && 
        risk.RiskImpact !== null && 
        risk.RiskExposureRating !== undefined && 
        risk.RiskExposureRating !== null
      );
      
      // Only show "Scoring Completed" if it has scoring AND is not rejected
      // Use case-insensitive comparison for Appetite and RiskStatus
      const appetite = (risk.Appetite || '').toLowerCase();
      const status = (risk.RiskStatus || '').toLowerCase();
      
      return hasScoring && appetite === 'yes' && status !== 'rejected';
    },
    isRiskRejected(risk) {
      // Check if risk has been rejected (Appetite is 'No' or RiskStatus is 'Rejected')
      // AND has scoring completed
      // Note: Rejected risks will not appear in the Risk Resolution screen
      const hasScoring = (
        risk.RiskLikelihood !== undefined && 
        risk.RiskLikelihood !== null && 
        risk.RiskImpact !== undefined && 
        risk.RiskImpact !== null && 
        risk.RiskExposureRating !== undefined && 
        risk.RiskExposureRating !== null
      );
      
      // Use case-insensitive comparison for Appetite and RiskStatus
      const appetite = (risk.Appetite || '').toLowerCase();
      const status = (risk.RiskStatus || '').toLowerCase();
      
      return hasScoring && (appetite === 'no' || status === 'rejected');
    },
    viewScoringDetails(riskId) {
      // Validate riskId before navigation
      const result = validateField(riskId, 'id');
      if (!result.isValid) {
        console.error('Invalid risk instance ID:', riskId, result.error);
        this.error = `Invalid risk instance ID: ${riskId}`;
        return;
      }
      
      // Find the risk instance
      const risk = this.riskInstances.find(r => r.RiskInstanceId === riskId);
      
      console.log(`Viewing scoring details for Risk ${riskId}`);
      console.log(`Risk details: Status=${risk.RiskStatus}, Appetite=${risk.Appetite}`);
      console.log(`Display logic: isScoringCompleted=${this.isScoringCompleted(risk)}, isRiskRejected=${this.isRiskRejected(risk)}`);
      
      // Navigate to the scoring details page with the risk ID and action=view
      this.$router.push({
        path: `/risk/scoring-details/${riskId}`,
        query: { action: 'view' }
      });
    },
    fetchRiskInstances() {
      axios.get('http://localhost:8000/api/risk-instances/')
        .then(response => {
          console.log('Risk instances data received:', response.data);
          
          // Validate and sanitize the response data
          const validatedData = this.validateResponseData(response.data);
          this.riskInstances = validatedData;
          this.filteredRiskInstances = [...this.riskInstances]; // Initialize filtered risks
          
          // Log risk status and appetite for debugging
          this.riskInstances.forEach(risk => {
            console.log(`Risk #${risk.RiskInstanceId}: Status=${risk.RiskStatus}, Appetite=${risk.Appetite}, Likelihood=${risk.RiskLikelihood}, Impact=${risk.RiskImpact}`);
            
            // Initialize showActionButtons for each risk instance
            this.showActionButtons[risk.RiskInstanceId] = false;
          });
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching risk instances:', error);
          this.error = `Failed to fetch risk instances: ${error.message}`;
          this.loading = false;
        });
    },
    handleResize() {
      // This method can be used to dynamically adjust the container based on sidebar state
      const container = document.querySelector('.risk-scoring-container');
      if (container) {
        // Adjust container based on window size
        if (window.innerWidth < 1200) {
          container.style.maxWidth = 'calc(100% - 60px)';
        } else {
          container.style.maxWidth = 'calc(100% - 200px)';
        }
      }
    },
    truncateText(text, maxLength) {
      if (!text) return '';
      
      // Sanitize the text before truncating
      const sanitizedText = sanitizeString(text);
      return sanitizedText.length > maxLength ? sanitizedText.substring(0, maxLength) + '...' : sanitizedText;
    },
    toggleActionButtons(riskId) {
      // Validate riskId before toggling
      const result = validateField(riskId, 'id');
      if (!result.isValid) {
        console.error('Invalid risk instance ID:', riskId, result.error);
        return;
      }
      
      this.showActionButtons[riskId] = !this.showActionButtons[riskId];
    },
    rejectRisk(riskId) {
      // Validate riskId before navigation
      const result = validateField(riskId, 'id');
      if (!result.isValid) {
        console.error('Invalid risk instance ID:', riskId, result.error);
        this.error = `Invalid risk instance ID: ${riskId}`;
        return;
      }
      
      console.log(`Navigating to Scoring Details for Risk ${riskId} (rejected)`);
      // Navigate to the scoring details page with the risk ID and action=reject
      this.$router.push({
        path: `/risk/scoring-details/${riskId}`,
        query: { action: 'reject' }
      });
    },
    mapScoringRisk(riskId) {
      // Validate riskId before navigation
      const result = validateField(riskId, 'id');
      if (!result.isValid) {
        console.error('Invalid risk instance ID:', riskId, result.error);
        this.error = `Invalid risk instance ID: ${riskId}`;
        return;
      }
      
      console.log(`Navigating to Scoring Details for Risk ${riskId} (accepted)`);
      // Navigate to the scoring details page with the risk ID and action=accept
      this.$router.push({
        path: `/risk/scoring-details/${riskId}`,
        query: { action: 'accept' }
      });
    }
  }
}
</script>

<style scoped>
@import './RiskScoring.css';
</style> 