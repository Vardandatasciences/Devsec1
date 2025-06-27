<template>
  <div class="tailoring-risk-container">
    <h1>Tailoring Existing Risk</h1>
    
    <form @submit.prevent="validateAndSubmit" class="risk-form">
      <!-- Risk ID Field - Centered at the top -->
      <div class="form-group risk-id-container">
        <label for="riskId"><i class="fas fa-hashtag"></i> Risk ID:</label>
        <div class="risk-dropdown-container">
          <input 
            type="text" 
            id="riskId" 
            v-model="selectedRiskIdText" 
            placeholder="Enter or select risk ID"
            @focus="showRiskDropdown = true"
            readonly
            :class="{'has-error': validationErrors.selectedRiskId}"
          >
          <button type="button" class="dropdown-toggle" @click="toggleRiskDropdown">
            <i class="fas fa-chevron-down"></i>
          </button>
          
          <div v-if="showRiskDropdown" class="risk-dropdown">
            <div class="risk-dropdown-search">
              <input 
                type="text" 
                v-model="riskSearchQuery" 
                placeholder="Search risks..." 
                @input="validateSearchQuery"
                @click.stop
                :class="{'has-error': validationErrors.searchQuery}"
              >
              <div v-if="validationErrors.searchQuery" class="field-error">{{ validationErrors.searchQuery }}</div>
            </div>
            <div class="risk-dropdown-list" v-if="loadingRisks">
              <div class="loading-spinner">Loading risks...</div>
            </div>
            <div class="risk-dropdown-list" v-else-if="filteredRisks.length === 0">
              <div class="no-results">No risks found</div>
            </div>
            <div class="risk-dropdown-list" v-else>
              <div 
                v-for="risk in filteredRisks" 
                :key="risk.RiskId" 
                class="risk-item"
                @click="selectRisk(risk)"
              >
                <div class="risk-item-checkbox">
                  <input 
                    type="checkbox" 
                    :id="'risk-' + risk.RiskId" 
                    :checked="selectedRiskId === risk.RiskId"
                    @click.stop="selectRisk(risk)"
                  >
                </div>
                <div class="risk-item-content">
                  <div class="risk-item-header">
                    <span class="risk-id">ID: {{ risk.RiskId }}</span>
                    <span :class="'risk-criticality ' + (risk.Criticality ? risk.Criticality.toLowerCase() : '')">{{ risk.Criticality || 'No Criticality' }}</span>
                    <span class="risk-category">{{ risk.Category || 'No Category' }}</span>
                  </div>
                  <div class="risk-item-title">{{ risk.RiskTitle || 'No Title' }}</div>
                  <div class="risk-item-description">{{ truncateText(risk.RiskDescription, 100) || 'No description available' }}</div>
                  <div v-if="risk.PossibleDamage" class="risk-item-damage">
                    <strong>Possible Damage:</strong> {{ truncateText(risk.PossibleDamage, 80) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="validationErrors.selectedRiskId" class="field-error">{{ validationErrors.selectedRiskId }}</div>
      </div>
      
      <!-- Row 1: Risk Title, Compliance Id, Criticality -->
      <div class="form-row">
        <div class="form-group">
          <label for="riskTitle"><i class="fas fa-heading"></i> Risk Title:</label>
          <input 
            type="text" 
            id="riskTitle" 
            v-model="risk.RiskTitle" 
            class="form-control" 
            required 
            @blur="validateField('RiskTitle', 'text')"
            :class="{'has-error': validationErrors.RiskTitle}"
          />
          <div v-if="validationErrors.RiskTitle" class="field-error">{{ validationErrors.RiskTitle }}</div>
        </div>
        
        <div class="form-group">
          <label for="compliance"><i class="fas fa-clipboard-check"></i> Compliance ID:</label>
          <input 
            type="number" 
            id="compliance" 
            v-model="risk.ComplianceId" 
            class="form-control"
            @blur="validateField('ComplianceId', 'id')"
            :class="{'has-error': validationErrors.ComplianceId}"
          >
          <div v-if="validationErrors.ComplianceId" class="field-error">{{ validationErrors.ComplianceId }}</div>
        </div>
        
        <div class="form-group">
          <label for="criticality"><i class="fas fa-exclamation-triangle"></i> Criticality:</label>
          <select 
            id="criticality" 
            v-model="risk.Criticality" 
            class="form-control"
            @change="validateField('Criticality', 'criticality')"
            :class="{'has-error': validationErrors.Criticality}"
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
          <div v-if="validationErrors.Criticality" class="field-error">{{ validationErrors.Criticality }}</div>
        </div>
      </div>
      
      <!-- Row 2: Category, Risk Type, Risk Priority -->
      <div class="form-row">
        <div class="form-group">
          <label for="category"><i class="fas fa-tag"></i> Category:</label>
          <input 
            type="text" 
            id="category" 
            v-model="risk.Category" 
            class="form-control"
            @blur="validateField('Category', 'category')"
            :class="{'has-error': validationErrors.Category}"
          >
          <div v-if="validationErrors.Category" class="field-error">{{ validationErrors.Category }}</div>
        </div>
        
        <div class="form-group">
          <label for="riskType"><i class="fas fa-list"></i> Risk Type:</label>
          <input 
            type="text" 
            id="riskType" 
            v-model="risk.RiskType" 
            class="form-control"
            @blur="validateField('RiskType', 'text')"
            :class="{'has-error': validationErrors.RiskType}"
          >
          <div v-if="validationErrors.RiskType" class="field-error">{{ validationErrors.RiskType }}</div>
        </div>
        
        <div class="form-group">
          <label for="priority"><i class="fas fa-flag"></i> Risk Priority:</label>
          <select 
            id="priority" 
            v-model="risk.RiskPriority" 
            class="form-control"
            @change="validateField('RiskPriority', 'riskPriority')"
            :class="{'has-error': validationErrors.RiskPriority}"
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
          <div v-if="validationErrors.RiskPriority" class="field-error">{{ validationErrors.RiskPriority }}</div>
        </div>
      </div>
      
      <!-- Row 3: Risk Impact, Risk Likelihood, Risk Exposure Rating -->
      <div class="form-row">
        <div class="form-group">
          <label for="impact"><i class="fas fa-bomb"></i> Risk Impact:</label>
          <input 
            type="number" 
            id="impact" 
            v-model.number="risk.RiskImpact" 
            class="form-control" 
            min="1" 
            max="10" 
            step="1"
            @blur="validateField('RiskImpact', 'riskRating')"
            :class="{'has-error': validationErrors.RiskImpact}"
          >
          <div v-if="validationErrors.RiskImpact" class="field-error">{{ validationErrors.RiskImpact }}</div>
        </div>
        
        <div class="form-group">
          <label for="likelihood"><i class="fas fa-chart-line"></i> Risk Likelihood:</label>
          <input 
            type="number" 
            id="likelihood" 
            v-model.number="risk.RiskLikelihood" 
            class="form-control" 
            min="1" 
            max="10" 
            step="1"
            @blur="validateField('RiskLikelihood', 'riskRating')"
            :class="{'has-error': validationErrors.RiskLikelihood}"
          >
          <div v-if="validationErrors.RiskLikelihood" class="field-error">{{ validationErrors.RiskLikelihood }}</div>
        </div>
        
        <div class="form-group">
          <label for="exposure"><i class="fas fa-chart-bar"></i> Risk Exposure Rating:</label>
          <input 
            type="number" 
            id="exposure" 
            v-model.number="risk.RiskExposureRating" 
            class="form-control" 
            step="0.1"
            @blur="validateField('RiskExposureRating', 'number')"
            :class="{'has-error': validationErrors.RiskExposureRating}"
          >
          <div v-if="validationErrors.RiskExposureRating" class="field-error">{{ validationErrors.RiskExposureRating }}</div>
        </div>
      </div>
      
      <!-- Row 4: Business Impact, Possible Damage -->
      <div class="form-row">
        <div class="form-group">
          <label for="businessImpact"><i class="fas fa-building"></i> Business Impact:</label>
          <textarea 
            id="businessImpact" 
            v-model="risk.BusinessImpact" 
            class="form-control"
            @blur="validateField('BusinessImpact', 'longText')"
            :class="{'has-error': validationErrors.BusinessImpact}"
          ></textarea>
          <div v-if="validationErrors.BusinessImpact" class="field-error">{{ validationErrors.BusinessImpact }}</div>
        </div>
        
        <div class="form-group">
          <label for="damage"><i class="fas fa-skull-crossbones"></i> Possible Damage:</label>
          <textarea 
            id="damage" 
            v-model="risk.PossibleDamage" 
            class="form-control"
            @blur="validateField('PossibleDamage', 'longText')"
            :class="{'has-error': validationErrors.PossibleDamage}"
          ></textarea>
          <div v-if="validationErrors.PossibleDamage" class="field-error">{{ validationErrors.PossibleDamage }}</div>
        </div>
      </div>
      
      <!-- Row 5: Risk Description, Risk Mitigation -->
      <div class="form-row">
        <div class="form-group">
          <label for="description"><i class="fas fa-align-left"></i> Risk Description:</label>
          <textarea 
            id="description" 
            v-model="risk.RiskDescription" 
            class="form-control"
            @blur="validateField('RiskDescription', 'longText')"
            :class="{'has-error': validationErrors.RiskDescription}"
          ></textarea>
          <div v-if="validationErrors.RiskDescription" class="field-error">{{ validationErrors.RiskDescription }}</div>
        </div>
        
        <div class="form-group">
          <label for="mitigation"><i class="fas fa-shield-alt"></i> Risk Mitigation:</label>
          <textarea 
            id="mitigation" 
            v-model="risk.RiskMitigation" 
            class="form-control"
            @blur="validateField('RiskMitigation', 'longText')"
            :class="{'has-error': validationErrors.RiskMitigation}"
          ></textarea>
          <div v-if="validationErrors.RiskMitigation" class="field-error">{{ validationErrors.RiskMitigation }}</div>
        </div>
      </div>
      
      <div v-if="formHasErrors" class="validation-summary">
        <div class="validation-summary-header">
          <i class="fas fa-exclamation-triangle"></i> Please fix the following errors:
        </div>
        <ul class="validation-error-list">
          <li v-for="(error, field) in validationErrors" :key="field">{{ error }}</li>
        </ul>
      </div>
      
      <div class="button-group">
        <button type="button" class="clear-btn" @click="clearForm">Clear</button>
        <button type="submit" class="submit-btn" :disabled="submitting || formHasErrors">
          <span v-if="submitting">SAVING...</span>
          <span v-else>CREATE</span>
        </button>
      </div>
    </form>
    
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import axios from 'axios';
import './TailoringRisk.css';
import { validateField as validateFieldFn, validateForm, sanitizeForm, sanitizeString, riskFormValidationMap } from './validation.js';

export default {
  name: 'TailoringRisk',
  setup() {
    const selectedRiskId = ref('');
    const selectedRiskIdText = ref('');
    const risk = ref({
      RiskId: '',
      ComplianceId: null,
      RiskTitle: '',
      Criticality: '',
      PossibleDamage: '',
      Category: '',
      RiskType: '',
      BusinessImpact: '',
      RiskDescription: '',
      RiskLikelihood: null,
      RiskImpact: null,
      RiskExposureRating: null,
      RiskPriority: '',
      RiskMitigation: ''
    });
    
    // Risk dropdown properties
    const risks = ref([]);
    const filteredRisks = ref([]);
    const riskSearchQuery = ref('');
    const showRiskDropdown = ref(false);
    const loadingRisks = ref(false);
    const riskIds = ref([]);
    
    const message = ref('');
    const messageType = ref('');
    const submitting = ref(false);
    
    // Validation state
    const validationErrors = ref({});
    const formHasErrors = computed(() => Object.keys(validationErrors.value).length > 0);
    
    // Fetch all risks on component mount
    onMounted(async () => {
      fetchRisks();
      
      // Add click event listener to close dropdown when clicking outside
      document.addEventListener('click', closeRiskDropdown);
    });
    
    // Clean up event listeners when component is unmounted
    onBeforeUnmount(() => {
      document.removeEventListener('click', closeRiskDropdown);
    });
    
    // Fetch risks from API
    const fetchRisks = async () => {
      loadingRisks.value = true;
      
      try {
        // Make API request to fetch all risks
        console.log('Fetching all risks from API...');
        const response = await axios.get('http://127.0.0.1:8000/api/risks-for-dropdown/');
        
        // Validate and sanitize the response data
        if (Array.isArray(response.data)) {
          // Sanitize each risk object in the array
          const sanitizedRisks = response.data.map(risk => {
            return sanitizeForm(risk);
          });
          
          risks.value = sanitizedRisks;
          filteredRisks.value = [...sanitizedRisks];
          riskIds.value = sanitizedRisks.map(risk => risk.RiskId);
          console.log('Extracted risk IDs:', riskIds.value);
        } else {
          console.error('Unexpected response format:', response.data);
          message.value = 'Error: Unexpected response format from server';
          messageType.value = 'error';
        }
      } catch (error) {
        console.error('Error fetching risks:', error);
        message.value = 'Error loading risks: ' + (error.response?.data?.detail || error.message);
        messageType.value = 'error';
      } finally {
        loadingRisks.value = false;
      }
    };
    
    // Validate search query
    const validateSearchQuery = () => {
      const result = validateFieldFn(riskSearchQuery.value, 'text');
      if (!result.isValid) {
        validationErrors.value.searchQuery = result.error;
      } else {
        delete validationErrors.value.searchQuery;
        filterRisks();
      }
    };
    
    // Filter risks based on search query
    const filterRisks = () => {
      if (!riskSearchQuery.value) {
        filteredRisks.value = [...risks.value];
        return;
      }
      
      // Sanitize the search query
      const query = sanitizeString(riskSearchQuery.value).toLowerCase();
      
      filteredRisks.value = risks.value.filter(risk => 
        (risk.RiskId && risk.RiskId.toString().includes(query)) ||
        (risk.RiskTitle && risk.RiskTitle.toLowerCase().includes(query)) ||
        (risk.Category && risk.Category.toLowerCase().includes(query)) ||
        (risk.RiskDescription && risk.RiskDescription.toLowerCase().includes(query))
      );
    };
    
    // Validate a specific field
    const validateField = (fieldName, validationType) => {
      const result = validateFieldFn(risk.value[fieldName], validationType);
      if (!result.isValid) {
        validationErrors.value[fieldName] = result.error;
      } else {
        delete validationErrors.value[fieldName];
      }
    };
    
    // Validate all form fields
    const validateAllFields = () => {
      const result = validateForm(risk.value, riskFormValidationMap);
      validationErrors.value = result.errors;
      
      // Validate risk ID selection
      if (!selectedRiskId.value) {
        validationErrors.value.selectedRiskId = 'Please select a risk template';
      } else {
        delete validationErrors.value.selectedRiskId;
      }
      
      return result.isValid && !validationErrors.value.selectedRiskId;
    };
    
    // Select a risk from the dropdown
    const selectRisk = (selectedRiskData) => {
      selectedRiskId.value = selectedRiskData.RiskId;
      selectedRiskIdText.value = `Risk ID: ${selectedRiskData.RiskId}`;
      showRiskDropdown.value = false;
      
      // Clear any validation error for risk ID
      delete validationErrors.value.selectedRiskId;
      
      loadRiskDetails();
    };
    
    // Toggle dropdown visibility
    const toggleRiskDropdown = () => {
      showRiskDropdown.value = !showRiskDropdown.value;
      if (showRiskDropdown.value) {
        riskSearchQuery.value = '';
        filterRisks();
      }
    };
    
    // Close dropdown when clicking outside
    const closeRiskDropdown = (event) => {
      // Check if the click was outside the dropdown
      const dropdown = document.querySelector('.risk-dropdown-container');
      if (dropdown && !dropdown.contains(event.target)) {
        showRiskDropdown.value = false;
      }
    };
    
    // Truncate text for display
    const truncateText = (text, maxLength) => {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // Parse numeric values from API response
    const parseNumericValue = (value) => {
      if (value === null || value === undefined) return null;
      
      // If it's already a number, return it
      if (typeof value === 'number') return value;
      
      // Try to parse string to number
      const parsed = parseFloat(value);
      return isNaN(parsed) ? null : parsed;
    };
    
    // Load risk details when a risk ID is selected
    const loadRiskDetails = async () => {
      if (!selectedRiskId.value) {
        // Reset form if no risk is selected
        clearForm();
        return;
      }
      
      try {
        console.log(`Loading details for risk ID: ${selectedRiskId.value}`);
        const response = await axios.get(`http://127.0.0.1:8000/api/risks/${selectedRiskId.value}/`);
        
        // Validate and sanitize the response data
        const riskData = sanitizeForm(response.data);
        
        // Update form fields with the selected risk data, ensuring numeric fields are parsed correctly
        risk.value = {
          RiskId: '', // We set this empty as we want to create a new risk on submit
          ComplianceId: parseNumericValue(riskData.ComplianceId),
          RiskTitle: riskData.RiskTitle || '',
          Criticality: riskData.Criticality || '',
          PossibleDamage: riskData.PossibleDamage || '',
          Category: riskData.Category || '',
          RiskType: riskData.RiskType || '',
          BusinessImpact: riskData.BusinessImpact || '',
          RiskDescription: riskData.RiskDescription || '',
          RiskLikelihood: parseNumericValue(riskData.RiskLikelihood),
          RiskImpact: parseNumericValue(riskData.RiskImpact),
          RiskExposureRating: parseNumericValue(riskData.RiskExposureRating),
          RiskPriority: riskData.RiskPriority || '',
          RiskMitigation: riskData.RiskMitigation || ''
        };
        
        // Validate all fields after loading
        Object.keys(riskFormValidationMap).forEach(field => {
          if (risk.value[field] !== undefined) {
            validateField(field, riskFormValidationMap[field]);
          }
        });
        
      } catch (error) {
        console.error('Error loading risk details:', error);
        message.value = 'Error loading risk details: ' + (error.response?.data?.detail || error.message);
        messageType.value = 'error';
      }
    };
    
    const clearForm = () => {
      risk.value = {
        RiskId: '',
        ComplianceId: null,
        RiskTitle: '',
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        RiskType: '',
        BusinessImpact: '',
        RiskDescription: '',
        RiskLikelihood: null,
        RiskImpact: null,
        RiskExposureRating: null,
        RiskPriority: '',
        RiskMitigation: ''
      };
      selectedRiskId.value = '';
      selectedRiskIdText.value = '';
      message.value = '';
      validationErrors.value = {};
    };
    
    const validateAndSubmit = async () => {
      // First validate all fields
      if (!validateAllFields()) {
        message.value = 'Please fix the validation errors before submitting';
        messageType.value = 'error';
        return;
      }
      
      await submitRisk();
    };
    
    const submitRisk = async () => {
      submitting.value = true;
      
      try {
        console.log('Submitting risk:', risk.value);
        
        // Create a copy of risk data for submission, ensuring numeric fields are converted properly
        const riskData = {
          ...risk.value,
          RiskLikelihood: parseNumericValue(risk.value.RiskLikelihood),
          RiskImpact: parseNumericValue(risk.value.RiskImpact),
          RiskExposureRating: parseNumericValue(risk.value.RiskExposureRating)
        };
        
        // Sanitize the data before submission
        const sanitizedRiskData = sanitizeForm(riskData);
        
        // Always create a new risk, never update an existing one
        console.log('Creating new risk based on selected template');
        const response = await axios.post('http://127.0.0.1:8000/api/risks/', sanitizedRiskData);
        
        // Validate and sanitize the response
        const responseData = sanitizeForm(response.data);
        const newRiskId = responseData.RiskId;
        
        message.value = `Risk successfully added with new ID: ${newRiskId}!`;
        messageType.value = 'success';
        
        // Reset form
        clearForm();
        
        // Refresh risks after submission
        fetchRisks();
      } catch (error) {
        console.error('Error submitting risk:', error);
        message.value = 'Error saving risk: ' + (error.response?.data?.detail || error.message);
        messageType.value = 'error';
      } finally {
        submitting.value = false;
      }
    };
    
    return {
      selectedRiskId,
      selectedRiskIdText,
      risk,
      riskIds,
      risks,
      filteredRisks,
      riskSearchQuery,
      showRiskDropdown,
      loadingRisks,
      submitting,
      validateAndSubmit,
      submitRisk,
      loadRiskDetails,
      clearForm,
      message,
      messageType,
      filterRisks,
      validateSearchQuery,
      selectRisk,
      toggleRiskDropdown,
      truncateText,
      validateField,
      validationErrors,
      formHasErrors
    };
  }
}
</script> 