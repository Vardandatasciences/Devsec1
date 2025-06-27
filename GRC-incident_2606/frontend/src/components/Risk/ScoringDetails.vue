<template>
  <div class="scoring-details-container">
    <h1>Scoring Details</h1>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Loading risk instance data...</span>
    </div>
    
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-else-if="!riskInstance" class="no-data">
      <p>No risk instance found.</p>
    </div>
    
    <div v-else class="risk-details">
      <div class="detail-header">
        <h2>Risk Instance #{{ editedRiskInstance.RiskInstanceId }}</h2>
        <div v-if="isCreateAction" class="action-header-buttons">
          <button class="map-scoring-risk-btn" @click="mapScoringRisk">MAP SCORING RISK</button>
        </div>
      </div>
      
      <div v-if="hasValidationErrors && formSubmitted" class="validation-error-summary">
        <p><i class="fas fa-exclamation-triangle"></i> Please correct the highlighted fields before submitting.</p>
      </div>
      
      <form @submit.prevent="submitForm" class="detail-grid-container">
        <!-- First section - Basic Risk Information -->
        <h3 class="section-title">Basic Risk Information</h3>
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Risk Instance Id</div>
            <div class="detail-value">{{ editedRiskInstance.RiskInstanceId }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Incident Id</div>
            <input type="text" v-model="editedRiskInstance.IncidentId" class="form-input" :readonly="isReadOnly" @blur="validateField('IncidentId', 'id')" :class="{'has-error': validationErrors.IncidentId}">
            <div v-if="validationErrors.IncidentId" class="field-error">{{ validationErrors.IncidentId }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Compliance Id</div>
            <input type="text" v-model="editedRiskInstance.ComplianceId" class="form-input" :readonly="isReadOnly" @blur="validateField('ComplianceId', 'id')" :class="{'has-error': validationErrors.ComplianceId}">
            <div v-if="validationErrors.ComplianceId" class="field-error">{{ validationErrors.ComplianceId }}</div>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Risk Title</div>
            <input type="text" v-model="editedRiskInstance.RiskTitle" class="form-input" :readonly="isReadOnly" @blur="validateField('RiskTitle', 'text')" :class="{'has-error': validationErrors.RiskTitle}">
            <div v-if="validationErrors.RiskTitle" class="field-error">{{ validationErrors.RiskTitle }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Criticality</div>
            <select v-model="editedRiskInstance.Criticality" class="form-select" :disabled="isReadOnly" @change="validateField('Criticality', 'criticality')" :class="{'has-error': validationErrors.Criticality}">
              <option value="">Select Criticality</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <div v-if="validationErrors.Criticality" class="field-error">{{ validationErrors.Criticality }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Possible Damage</div>
            <input type="text" v-model="editedRiskInstance.PossibleDamage" class="form-input" :readonly="isReadOnly" @blur="validateField('PossibleDamage', 'longText')" :class="{'has-error': validationErrors.PossibleDamage}">
            <div v-if="validationErrors.PossibleDamage" class="field-error">{{ validationErrors.PossibleDamage }}</div>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Category</div>
            <select v-model="editedRiskInstance.Category" class="form-select" :disabled="isReadOnly" @change="validateField('Category', 'category')" :class="{'has-error': validationErrors.Category}">
              <option value="">Select Category</option>
              <option value="Security">Security</option>
              <option value="Operational">Operational</option>
              <option value="Financial">Financial</option>
              <option value="Compliance">Compliance</option>
              <option value="Strategic">Strategic</option>
              <option value="Strategic">IT</option>
            </select>
            <div v-if="validationErrors.Category" class="field-error">{{ validationErrors.Category }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Description</div>
            <textarea v-model="editedRiskInstance.RiskDescription" class="form-textarea" :readonly="isReadOnly" @blur="validateField('RiskDescription', 'longText')" :class="{'has-error': validationErrors.RiskDescription}"></textarea>
            <div v-if="validationErrors.RiskDescription" class="field-error">{{ validationErrors.RiskDescription }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Priority</div>
            <select v-model="editedRiskInstance.RiskPriority" class="form-select" :disabled="isReadOnly" @change="validateField('RiskPriority', 'riskPriority')" :class="{'has-error': validationErrors.RiskPriority}">
              <option value="">Select Priority</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <div v-if="validationErrors.RiskPriority" class="field-error">{{ validationErrors.RiskPriority }}</div>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Reported By</div>
            <input type="text" v-model="editedRiskInstance.ReportedBy" class="form-input" :readonly="isReadOnly" @blur="validateField('ReportedBy', 'text')" :class="{'has-error': validationErrors.ReportedBy}">
            <div v-if="validationErrors.ReportedBy" class="field-error">{{ validationErrors.ReportedBy }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Origin</div>
            <input type="text" v-model="editedRiskInstance.Origin" class="form-input" :readonly="isReadOnly" @blur="validateField('Origin', 'text')" :class="{'has-error': validationErrors.Origin}">
            <div v-if="validationErrors.Origin" class="field-error">{{ validationErrors.Origin }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Status</div>
            <select v-model="editedRiskInstance.RiskStatus" class="form-select" :disabled="isReadOnly" @change="validateField('RiskStatus', 'riskStatus')" :class="{'has-error': validationErrors.RiskStatus}">
              <option value="Not Assigned" selected>Not Assigned</option>
              <option value="Assigned">Assigned</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
            </select>
            <div v-if="validationErrors.RiskStatus" class="field-error">{{ validationErrors.RiskStatus }}</div>
          </div>
        </div>
        
        
        
        <!-- Mapping Risks Section -->
        <h3 class="section-title">Mapped Risks</h3>
        <div class="mapping-risks-section">
          <p class="mapping-description">Select risks from Risk Register with matching Compliance ID: {{ editedRiskInstance.ComplianceId || 'None' }}</p>
          
          <div v-if="loadingMatchingRisks" class="loading">
            <div class="spinner"></div>
            <span>Loading matching risks...</span>
          </div>
          
          <div v-else-if="matchingRisks.length > 0" class="mapping-risks-table">
            <table>
              <thead>
                <tr>
                  <th>Select</th>
                  <th>Risk ID</th>
                  <th>Compliance ID</th>
                  <th>Risk Title</th>
                  <th>Criticality</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="risk in matchingRisks" :key="risk.RiskId">
                  <td>
                    <input 
                      type="checkbox" 
                      :id="'risk-' + risk.RiskId" 
                      :value="risk.RiskId" 
                      v-model="selectedRisks"
                      class="risk-checkbox"
                    >
                  </td>
                  <td>{{ risk.RiskId }}</td>
                  <td>{{ risk.ComplianceId }}</td>
                  <td>{{ risk.RiskTitle }}</td>
                  <td>{{ risk.Criticality }}</td>
                  <td>{{ risk.Category }}</td>
                </tr>
              </tbody>
            </table>
            
            <div class="selected-risks-actions">
              <div class="selected-risks-info">
                <div v-if="selectedRisks.length > 0" class="selected-risks-count">
                  {{ selectedRisks.length }} risk(s) selected
                </div>
                <button 
                  v-if="selectedRisks.length > 0" 
                  type="button" 
                  class="fill-scoring-button" 
                  @click="fillScoringFromSelectedRisk"
                >
                  Fill Scoring
                </button>
              </div>
              <button type="button" class="create-risk-btn" @click="createRisk">Create Risk</button>
            </div>
          </div>
          
          <div v-else class="no-matching-risks">
            <p>No matching risks found with Compliance ID: {{ editedRiskInstance.ComplianceId || 'None' }}</p>
            <button type="button" class="create-risk-btn" @click="createRisk">Create Risk</button>
          </div>
        </div>
        
        <!-- Risk Assessment Section -->
        <h3 class="section-title">Risk Assessment</h3>
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Risk Id</div>
            <input type="text" v-model="editedRiskInstance.RiskId" class="form-input" :readonly="isReadOnly" @blur="validateField('RiskId', 'id')" :class="{'has-error': validationErrors.RiskId}">
            <div v-if="validationErrors.RiskId" class="field-error">{{ validationErrors.RiskId }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Likelihood</div>
            <input type="number" step="1" min="1" max="10" v-model.number="editedRiskInstance.RiskLikelihood" class="form-input" @input="calculateRiskExposureRating" :readonly="isReadOnly" @blur="validateField('RiskLikelihood', 'riskRating')" :class="{'has-error': validationErrors.RiskLikelihood}">
            <div v-if="validationErrors.RiskLikelihood" class="field-error">{{ validationErrors.RiskLikelihood }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Impact</div>
            <input type="number" step="1" min="1" max="10" v-model.number="editedRiskInstance.RiskImpact" class="form-input" @input="calculateRiskExposureRating" :readonly="isReadOnly" @blur="validateField('RiskImpact', 'riskRating')" :class="{'has-error': validationErrors.RiskImpact}">
            <div v-if="validationErrors.RiskImpact" class="field-error">{{ validationErrors.RiskImpact }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Exposure Rating (Likelihood × Impact)</div>
            <input type="number" readonly v-model.number="editedRiskInstance.RiskExposureRating" class="form-input readonly-input" @blur="validateField('RiskExposureRating', 'number')" :class="{'has-error': validationErrors.RiskExposureRating}">
            <div v-if="validationErrors.RiskExposureRating" class="field-error">{{ validationErrors.RiskExposureRating }}</div>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Risk Type</div>
            <select v-model="editedRiskInstance.RiskType" class="form-select" :disabled="isReadOnly" @change="validateField('RiskType', 'text')" :class="{'has-error': validationErrors.RiskType}">
              <option value="Current">Current</option>
              <option value="Residual">Residual</option>
              <option value="Inherent">Inherent</option>
              <option value="Emerging">Emerging</option>
              <option value="Accepted">Accepted</option>
            </select>
            <div v-if="validationErrors.RiskType" class="field-error">{{ validationErrors.RiskType }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Business Impact</div>
            <textarea v-model="editedRiskInstance.BusinessImpact" class="form-textarea" :readonly="isReadOnly" @blur="validateField('BusinessImpact', 'longText')" :class="{'has-error': validationErrors.BusinessImpact}"></textarea>
            <div v-if="validationErrors.BusinessImpact" class="field-error">{{ validationErrors.BusinessImpact }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Appetite</div>
            <select 
              v-model="editedRiskInstance.Appetite" 
              :class="['form-select', { 'rejected-appetite': isRejectedAction || editedRiskInstance.Appetite === 'No' }, {'has-error': validationErrors.Appetite}]"
              :disabled="isReadOnly"
              @change="onAppetiteChange"
              @blur="validateField('Appetite', 'appetite')"
            >
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
            <div v-if="validationErrors.Appetite" class="field-error">{{ validationErrors.Appetite }}</div>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">Risk Response Type</div>
            <select v-model="editedRiskInstance.RiskResponseType" class="form-select" :disabled="isReadOnly" @change="validateField('RiskResponseType', 'riskResponseType')" :class="{'has-error': validationErrors.RiskResponseType}">
              <option value="Mitigation">Mitigation</option>
              <option value="Avoidance">Avoidance</option>
              <option value="Transfer">Transfer</option>
              <option value="Acceptance">Acceptance</option>
            </select>
            <div v-if="validationErrors.RiskResponseType" class="field-error">{{ validationErrors.RiskResponseType }}</div>
          </div>
          
          <div class="detail-item">
            <div class="detail-label">Risk Response Description</div>
            <textarea v-model="editedRiskInstance.RiskResponseDescription" class="form-textarea" :readonly="isReadOnly" @blur="validateField('RiskResponseDescription', 'longText')" :class="{'has-error': validationErrors.RiskResponseDescription}"></textarea>
            <div v-if="validationErrors.RiskResponseDescription" class="field-error">{{ validationErrors.RiskResponseDescription }}</div>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item full-width">
            <div class="detail-label">Risk Mitigation</div>
            <textarea v-model="riskMitigationJson" class="form-textarea json-textarea" placeholder="Enter JSON data" :readonly="isReadOnly" @blur="validateField('RiskMitigation', 'json')" :class="{'has-error': validationErrors.RiskMitigation}"></textarea>
            <div v-if="validationErrors.RiskMitigation" class="field-error">{{ validationErrors.RiskMitigation }}</div>
          </div>
        </div>
        
        <div class="form-footer">
          <button type="submit" class="submit-button" :disabled="submitting">
            <span v-if="submitting">Saving...</span>
            <span v-else>Save Changes</span>
          </button>
          <button type="button" class="back-button" @click="goBack">Back to Risk Scoring</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import './ScoringDetails.css';
import { validateField, validateForm, sanitizeString } from './validation.js';

export default {
  name: 'ScoringDetails',
  props: {
    riskId: {
      type: [String, Number],
      required: true
    },
    action: {
      type: String,
      default: 'view'
    }
  },
  data() {
    return {
      riskInstance: null,
      editedRiskInstance: {
        RiskStatus: 'Not Assigned',
        RiskType: 'Current'
      },
      riskMitigationJson: '',
      loading: true,
      error: null,
      submitting: false,
      submitSuccess: false,
      submitError: null,
      matchingRisks: [],
      selectedRisks: [],
      loadingMatchingRisks: false,
      defaultAppetite: "No",
      isReadOnly: false,
      validationErrors: {},
      formSubmitted: false
    }
  },
  computed: {
    isRejectedAction() {
      return this.$route.query.action === 'reject';
    },
    isViewAction() {
      return this.$route.query.action === 'view';
    },
    isCreateAction() {
      return this.$route.query.action === 'create';
    },
    hasValidationErrors() {
      return Object.keys(this.validationErrors).length > 0;
    }
  },
  mounted() {
    this.fetchRiskInstance();
    
    // Add Font Awesome if not already present
    if (!document.querySelector('link[href*="font-awesome"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
      document.head.appendChild(link);
    }
    
    // Log the action taken (accept or reject or view or create)
    const action = this.$route.query.action;
    if (action) {
      console.log(`Risk ${this.riskId} action: ${action}`);
      
      // If action is reject, set default Appetite to "NO"
      if (action === 'reject') {
        this.defaultAppetite = "NO";
      }
      
      // If action is view, set form to read-only mode
      if (action === 'view') {
        this.setReadOnlyMode();
      }
      
      // If action is create, we'll handle it in the fetchRiskInstance method
      if (action === 'create') {
        console.log('Create action detected - will prepare for risk creation');
      }
    }
  },
  methods: {
    setReadOnlyMode() {
      this.isReadOnly = true;
      
      // Add a class to the container to indicate read-only mode
      setTimeout(() => {
        const container = document.querySelector('.scoring-details-container');
        if (container) {
          container.classList.add('read-only-mode');
        }
      }, 100);
    },
    calculateRiskExposureRating() {
      // Get the current values of RiskLikelihood and RiskImpact
      const likelihood = parseInt(this.editedRiskInstance.RiskLikelihood) || 1;
      const impact = parseInt(this.editedRiskInstance.RiskImpact) || 1;
      
      // Calculate the Risk Exposure Rating as the product
      this.editedRiskInstance.RiskExposureRating = likelihood * impact;
    },
    fetchRiskInstance() {
      axios.get(`http://localhost:8000/api/risk-instances/${this.riskId}/`)
        .then(response => {
          console.log('Risk instance data received:', response.data);
          this.riskInstance = response.data;
          // Create a deep copy of the risk instance for editing
          this.editedRiskInstance = JSON.parse(JSON.stringify(this.riskInstance));
          
          // Set default values if not present
          if (!this.editedRiskInstance.RiskStatus) {
            this.editedRiskInstance.RiskStatus = 'Not Assigned';
          }
          
          if (!this.editedRiskInstance.RiskType) {
            this.editedRiskInstance.RiskType = 'Current';
          }
          
          if (!this.editedRiskInstance.Appetite) {
            this.editedRiskInstance.Appetite = this.isRejectedAction ? 'No' : 'Yes';
          }
          
          if (!this.editedRiskInstance.RiskResponseType) {
            this.editedRiskInstance.RiskResponseType = 'Mitigation';
          }
          
          // Handle JSON fields
          if (this.editedRiskInstance.RiskMitigation) {
            this.riskMitigationJson = JSON.stringify(this.editedRiskInstance.RiskMitigation, null, 2);
          } else {
            this.riskMitigationJson = '';
          }
          
          // Set default Appetite and RiskStatus for rejected actions
          if (this.isRejectedAction) {
            this.editedRiskInstance.Appetite = 'No';
            this.editedRiskInstance.RiskStatus = 'Rejected';
            console.log('Risk rejected: Setting Appetite to No and RiskStatus to Rejected');
          }
          
          // Double-check: If RiskStatus is 'Rejected', ensure Appetite is 'No'
          // Use case-insensitive comparison
          const status = (this.editedRiskInstance.RiskStatus || '').toLowerCase();
          const appetite = (this.editedRiskInstance.Appetite || '').toLowerCase();
          
          if (status === 'rejected' && appetite !== 'no') {
            console.log('Correcting inconsistency: RiskStatus is Rejected but Appetite was not No');
            this.editedRiskInstance.Appetite = 'No';
          }
          
          // Calculate Risk Exposure Rating based on initial values
          this.calculateRiskExposureRating();
          
          this.loading = false;
          
          // Fetch matching risks from Risk Register after getting the Compliance ID
          if (this.editedRiskInstance.ComplianceId) {
            this.fetchMatchingRisks(this.editedRiskInstance.ComplianceId);
          }
        })
        .catch(error => {
          console.error('Error fetching risk instance:', error);
          this.error = `Failed to fetch risk instance: ${error.message}`;
          this.loading = false;
        });
    },
    fetchMatchingRisks(complianceId) {
      // Validate complianceId before fetching
      const result = validateField(complianceId, 'id');
      if (!result.isValid) {
        console.error('Invalid compliance ID:', complianceId, result.error);
        return;
      }
      
      if (!complianceId) return;
      
      this.loadingMatchingRisks = true;
      
      // Fetch risks from Risk Register with matching Compliance ID
      axios.get(`http://localhost:8000/api/risks/`)
      .then(response => {
        console.log('All risks data received:', response.data);
        // Filter risks to only include those with matching Compliance ID
        this.matchingRisks = response.data.filter(risk => 
          risk.ComplianceId && risk.ComplianceId.toString() === complianceId.toString()
        );
        console.log('Filtered matching risks:', this.matchingRisks);
        this.loadingMatchingRisks = false;
      })
      .catch(error => {
        console.error('Error fetching matching risks:', error);
        this.loadingMatchingRisks = false;
      });
    },
    submitForm() {
      this.formSubmitted = true;
      
      // Validate all fields before submission
      if (!this.validateAllFields()) {
        console.error('Validation failed:', this.validationErrors);
        // Scroll to the first error
        this.$nextTick(() => {
          const firstError = document.querySelector('.has-error');
          if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
          }
        });
        return;
      }
      
      this.submitting = true;
      this.submitError = null;
      
      try {
        // Create a clean copy of the edited risk instance
        const updatedRiskInstance = {};
        
        // Only include fields that are actually part of the model
        const validFields = [
          'RiskInstanceId', 'RiskId', 'IncidentId', 'ComplianceId', 'RiskTitle', 
          'Criticality', 'PossibleDamage', 'Category', 'RiskDescription', 
          'RiskLikelihood', 'RiskImpact', 'RiskExposureRating', 'RiskPriority', 
          'RiskResponseType', 'RiskResponseDescription', 'RiskType', 'ReportedBy', 
          'BusinessImpact', 'Origin', 'UserId', 'Appetite', 'RiskStatus'
        ];
        
        // Copy only valid fields
        for (const field of validFields) {
          if (this.editedRiskInstance[field] !== undefined) {
            updatedRiskInstance[field] = this.editedRiskInstance[field];
          }
        }
        
        // Ensure RiskStatus has a valid value
        if (!updatedRiskInstance.RiskStatus || 
            !['Not Assigned', 'Assigned', 'Approved', 'Rejected'].includes(updatedRiskInstance.RiskStatus)) {
          updatedRiskInstance.RiskStatus = 'Not Assigned';
        }
        
        // If this is a rejection action, ensure the proper values are set
        if (this.isRejectedAction) {
          updatedRiskInstance.Appetite = 'No';
          updatedRiskInstance.RiskStatus = 'Rejected';
        }
        
        // Ensure consistency between RiskStatus and Appetite
        // Use case-insensitive comparison but store with proper casing
        const status = (updatedRiskInstance.RiskStatus || '').toLowerCase();
        const appetite = (updatedRiskInstance.Appetite || '').toLowerCase();
        
        if (status === 'rejected') {
          updatedRiskInstance.Appetite = 'No';
          updatedRiskInstance.RiskStatus = 'Rejected'; // Ensure consistent casing
        }
        
        // If Appetite is 'No', set RiskStatus to 'Rejected'
        if (appetite === 'no') {
          updatedRiskInstance.RiskStatus = 'Rejected';
          updatedRiskInstance.Appetite = 'No'; // Ensure consistent casing
        }
        
        // Parse JSON fields
        if (this.riskMitigationJson.trim()) {
          try {
            // Try to parse as JSON first
            updatedRiskInstance.RiskMitigation = JSON.parse(this.riskMitigationJson);
          } catch (e) {
            // If parsing fails, use as string
            console.warn('JSON parsing failed, using raw string:', e);
            updatedRiskInstance.RiskMitigation = this.riskMitigationJson;
          }
        } else {
          updatedRiskInstance.RiskMitigation = {};
        }
        
        // Add selected risks to the risk instance
        updatedRiskInstance.MappedRisks = this.selectedRisks;
        
        // Validate required fields
        const requiredFields = ['RiskTitle', 'Category', 'RiskStatus'];
        const missingFields = requiredFields.filter(field => !updatedRiskInstance[field]);
        
        if (missingFields.length > 0) {
          this.submitError = `Please fill in the following required fields: ${missingFields.join(', ')}`;
          this.submitting = false;
          alert(this.submitError);
          return;
        }
        
        // Convert numeric fields to integers
        ['RiskLikelihood', 'RiskImpact'].forEach(field => {
          if (updatedRiskInstance[field] !== undefined && updatedRiskInstance[field] !== null) {
            updatedRiskInstance[field] = parseInt(updatedRiskInstance[field]);
            
            // Enforce limits for RiskLikelihood and RiskImpact (1-10)
            if (updatedRiskInstance[field] < 1 || updatedRiskInstance[field] > 10) {
              updatedRiskInstance[field] = Math.max(1, Math.min(10, updatedRiskInstance[field]));
            }
          }
        });
        
        // Calculate the Risk Exposure Rating one final time before submission
        updatedRiskInstance.RiskExposureRating = 
          (updatedRiskInstance.RiskLikelihood || 1) * (updatedRiskInstance.RiskImpact || 1);
        
        console.log('Submitting updated risk instance:', updatedRiskInstance);
        
        // Send the update request with proper headers
        axios.put(`http://localhost:8000/api/risk-instances/${this.riskId}/`, updatedRiskInstance, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
          .then(response => {
            console.log('Risk instance updated:', response.data);
            this.submitSuccess = true;
            this.submitting = false;
            
            // Update the original data with the response
            this.riskInstance = response.data;
            
            // Update the edited instance to match the response
            this.editedRiskInstance = JSON.parse(JSON.stringify(response.data));
            
            // Update the JSON representation of RiskMitigation
            if (this.editedRiskInstance.RiskMitigation) {
              this.riskMitigationJson = JSON.stringify(this.editedRiskInstance.RiskMitigation, null, 2);
            } else {
              this.riskMitigationJson = '';
            }
            
            // Show success message
            if (this.isRejectedAction) {
              alert('Risk instance rejected successfully!');
            } else {
              alert('Risk instance updated successfully!');
            }
          })
          .catch(error => {
            console.error('Error updating risk instance:', error);
            
            // More detailed error handling
            let errorMessage = 'Failed to update risk instance';
            
            if (error.response) {
              // The request was made and the server responded with a status code
              // that falls out of the range of 2xx
              console.error('Error response data:', error.response.data);
              console.error('Error response status:', error.response.status);
              console.error('Error response headers:', error.response.headers);
              
              if (error.response.data && typeof error.response.data === 'object') {
                errorMessage = JSON.stringify(error.response.data);
              } else if (error.response.data) {
                errorMessage = error.response.data;
              } else {
                errorMessage = `Server returned status ${error.response.status}`;
              }
            } else if (error.request) {
              // The request was made but no response was received
              errorMessage = 'No response received from server';
            } else {
              // Something happened in setting up the request that triggered an Error
              errorMessage = error.message;
            }
            
            this.submitError = errorMessage;
            this.submitting = false;
            alert(`Error: ${this.submitError}`);
          });
      } catch (e) {
        console.error('Error in form submission:', e);
        this.submitError = `An unexpected error occurred: ${e.message}`;
        this.submitting = false;
        alert(`Error: ${this.submitError}`);
      }
    },
    formatLabel(key) {
      // Convert camelCase or PascalCase to space-separated words
      return key.replace(/([A-Z])/g, ' $1').trim();
    },
    onAppetiteChange() {
      // When Appetite changes, update RiskStatus accordingly
      // Use case-insensitive comparison
      const appetite = (this.editedRiskInstance.Appetite || '').toLowerCase();
      
      if (appetite === 'no') {
        this.editedRiskInstance.RiskStatus = 'Rejected';
        this.editedRiskInstance.Appetite = 'No'; // Ensure consistent casing
        console.log('Appetite set to No: Updated RiskStatus to Rejected');
      } else if (this.isRejectedAction && appetite === 'yes') {
        // If this was originally a rejection but user changed to Yes
        console.log('Warning: Appetite changed from No to Yes in a rejection action');
        // Still allow the change but make sure casing is consistent
        this.editedRiskInstance.Appetite = 'Yes';
      }
    },
    goBack() {
      // Navigate back to the risk scoring page
      this.$router.push('/risk/scoring');
      
      // If this was a rejection action, log it
      if (this.isRejectedAction) {
        console.log(`Returning to Risk Scoring after rejecting risk ${this.riskId}`);
      }
    },
    createRisk() {
      console.log(`Navigating to Create Risk page from risk ${this.riskId}`);
      // Navigate to Create Risk page with the current risk instance ID
      this.$router.push({
        path: '/risk/create-risk',
        query: { 
          source_risk_id: this.riskId,
          return_to: 'scoring-details',
          action: 'accept'
        }
      });
    },
    mapScoringRisk() {
      console.log(`Mapping scoring risk for risk ${this.riskId}`);
      // This method will be used to map scoring risk
      // For now, we'll just show an alert
      alert('Mapping scoring risk functionality will be implemented here.');
    },
    fillScoringFromSelectedRisk() {
      if (this.selectedRisks.length > 0) {
        // Get the first selected risk ID (in case multiple are selected)
        const selectedRiskId = this.selectedRisks[0];
        
        // Find the corresponding risk from the matching risks array
        const selectedRisk = this.matchingRisks.find(risk => risk.RiskId === selectedRiskId);
        
        if (selectedRisk) {
          // Fill the form fields with data from the selected risk
          this.editedRiskInstance.RiskId = selectedRisk.RiskId;
          this.editedRiskInstance.RiskLikelihood = selectedRisk.RiskLikelihood ? parseInt(selectedRisk.RiskLikelihood) || 1 : 1;
          this.editedRiskInstance.RiskImpact = selectedRisk.RiskImpact ? parseInt(selectedRisk.RiskImpact) || 1 : 1;
          
          // Calculate Risk Exposure Rating based on the filled values
          this.calculateRiskExposureRating();
          
          // Show success message
          alert('Risk scoring data has been filled from the selected risk.');
        } else {
          alert('Could not find the selected risk data.');
        }
      } else {
        alert('Please select a risk first.');
      }
    },
    validateField(field, type) {
      const value = this.editedRiskInstance[field];
      const result = validateField(value, type);
      
      if (!result.isValid) {
        this.validationErrors[field] = result.error;
        return false;
      } else {
        delete this.validationErrors[field];
        return true;
      }
    },
    validateAllFields() {
      // Define validation map for all fields
      const validationMap = {
        RiskId: 'id',
        IncidentId: 'id',
        ComplianceId: 'id',
        RiskTitle: 'text',
        Criticality: 'criticality',
        PossibleDamage: 'longText',
        Category: 'category',
        RiskDescription: 'longText',
        RiskPriority: 'riskPriority',
        ReportedBy: 'text',
        Origin: 'text',
        RiskStatus: 'riskStatus',
        RiskLikelihood: 'riskRating',
        RiskImpact: 'riskRating',
        RiskExposureRating: 'number',
        RiskType: 'text',
        BusinessImpact: 'longText',
        Appetite: 'appetite',
        RiskResponseType: 'riskResponseType',
        RiskResponseDescription: 'longText'
      };
      
      const result = validateForm(this.editedRiskInstance, validationMap);
      this.validationErrors = result.errors;
      return result.isValid;
    },
    validateResponseData(data) {
      if (!Array.isArray(data)) {
        console.error('Expected array response, got:', typeof data);
        return [];
      }
      
      return data.map(item => {
        const sanitized = {};
        
        // Define expected fields and their types
        const expectedFields = {
          RiskId: 'id',
          ComplianceId: 'id',
          RiskTitle: 'text',
          Criticality: 'criticality',
          Category: 'category'
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
                case 'text':
                case 'category':
                case 'criticality':
                  sanitized[field] = '';
                  break;
                default:
                  sanitized[field] = null;
              }
              console.warn(`Invalid ${field} value:`, item[field], result.error);
            }
          } else {
            // Field is missing, use default value
            sanitized[field] = validationType === 'id' ? null : '';
          }
        }
        
        return sanitized;
      });
    }
  },
  watch: {
    'editedRiskInstance.ComplianceId': function(newValue) {
      // When Compliance ID changes, fetch matching risks
      console.log('ComplianceId changed to:', newValue);
      this.selectedRisks = []; // Reset selected risks when Compliance ID changes
      if (newValue) {
        this.fetchMatchingRisks(newValue);
      } else {
        this.matchingRisks = [];
      }
    }
  }
}
</script> 