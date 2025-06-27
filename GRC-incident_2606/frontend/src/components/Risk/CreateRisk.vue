<template>
  <div class="risk-register-container create-risk">
    <div class="risk-register-header-row">
      <h2 class="risk-register-title"><i class="fas fa-plus risk-register-icon"></i> Create New Risk</h2>
      <div v-if="sourceRiskId" class="source-risk-badge">
        <span v-if="isLoadingSourceRisk">
          <i class="fas fa-spinner fa-spin"></i> Loading source risk data...
        </span>
        <span v-else>
          <i class="fas fa-link"></i> Creating from Risk #{{ sourceRiskId }}
        </span>
      </div>
    </div>
    
    <!-- Creation Mode Toggle -->
    <div class="creation-mode-toggle">
      <div class="toggle-container">
        <div 
          class="toggle-option" 
          :class="{ active: !isAiMode }" 
          @click="setCreationMode(false)"
        >
          <i class="fas fa-user"></i> Manual Creation
        </div>
        <div 
          class="toggle-option" 
          :class="{ active: isAiMode }" 
          @click="setCreationMode(true)"
        >
          <i class="fas fa-robot"></i> AI Suggested
        </div>
        <div class="toggle-slider" :class="{ 'slide-right': isAiMode }"></div>
      </div>
    </div>
    
    <!-- AI Input Form (shown only in AI mode) -->
    <div v-if="isAiMode && !aiSuggestionGenerated" class="ai-input-form">
      <div class="ai-input-container">
        <h3><i class="fas fa-robot"></i> AI Risk Analysis</h3>
        
        <!-- Loading state -->
        <div v-if="isGeneratingAi" class="ai-loading-state">
          <div class="ai-spinner">
            <i class="fas fa-spinner fa-spin"></i>
          </div>
          <p>Analyzing incident data with AI...</p>
        </div>
        
        <!-- Incident data display/input -->
        <div v-else>
          <div v-if="incidentId" class="incident-info">
            <div class="incident-badge">
              <i class="fas fa-exclamation-triangle"></i> 
              Incident #{{ incidentId }}
            </div>
          </div>
          
          <div class="ai-form-group">
            <label>Title</label>
            <div v-if="incidentId" class="incident-data-box">{{ aiInput.title || 'No title available' }}</div>
            <input v-else type="text" v-model="aiInput.title" placeholder="Enter incident title for AI analysis" class="ai-input-field" />
          </div>
          
          <div class="ai-form-group">
            <label>Description</label>
            <div v-if="incidentId" class="incident-data-box description">{{ aiInput.description || 'No description available' }}</div>
            <textarea v-else v-model="aiInput.description" placeholder="Enter incident description for AI analysis" class="ai-input-field description" rows="4"></textarea>
          </div>
          
          <div class="ai-form-actions">
            <button 
              class="generate-btn" 
              @click="generateAiSuggestion" 
              :disabled="isGeneratingAi || (!aiInput.title && !aiInput.description)"
            >
              <i class="fas fa-magic"></i>
              Generate Risk Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add Risk Form -->
    <div class="risk-register-add-form" v-if="!isAiMode || aiSuggestionGenerated">
      <form @submit.prevent="submitRisk" class="risk-register-form-grid" novalidate>
        <!-- Compliance ID - Centered at top -->
        <div class="risk-register-form-group compliance-id-container">
          <label>
            <span><i class="fas fa-hashtag"></i> Compliance ID</span>
          </label>
          <div class="compliance-dropdown-container">
            <input 
              type="text" 
              v-model="selectedComplianceIdText" 
              placeholder="Enter or select compliance ID"
              @focus="showComplianceDropdown = true"
              @mouseenter="handleMouseEnter('compliance')"
              @mouseleave="handleMouseLeave"
              readonly
              :class="{'input-error': validationErrors.ComplianceId}"
            />
            <button type="button" class="dropdown-toggle" @click="toggleComplianceDropdown">
              <i class="fas fa-chevron-down"></i>
            </button>
            
            <div v-if="showComplianceDropdown" class="compliance-dropdown">
              <div class="compliance-dropdown-search">
                <input 
                  type="text" 
                  v-model="complianceSearchQuery" 
                  placeholder="Search compliances..." 
                  @input="filterCompliances"
                  @click.stop
                >
              </div>
              <div class="compliance-dropdown-list" v-if="loadingCompliances">
                <div class="loading-spinner">Loading compliances...</div>
              </div>
              <div class="compliance-dropdown-list" v-else-if="filteredCompliances.length === 0">
                <div class="no-results">No compliances found</div>
              </div>
              <div class="compliance-dropdown-list" v-else>
                <div 
                  v-for="compliance in filteredCompliances" 
                  :key="compliance.ComplianceId" 
                  class="compliance-item"
                  @click="selectCompliance(compliance)"
                >
                  <div class="compliance-item-checkbox">
                    <input 
                      type="checkbox" 
                      :id="'compliance-' + compliance.ComplianceId" 
                      :checked="newRisk.ComplianceId === compliance.ComplianceId"
                      @click.stop="selectCompliance(compliance)"
                    >
                  </div>
                  <div class="compliance-item-content">
                    <div class="compliance-item-header">
                      <span class="compliance-id">ID: {{ compliance.ComplianceId }}</span>
                      <span :class="'compliance-criticality ' + (compliance.Criticality ? compliance.Criticality.toLowerCase() : '')">{{ compliance.Criticality || 'No Criticality' }}</span>
                    </div>
                    <div class="compliance-item-description">{{ truncateText(compliance.ComplianceItemDescription, 100) || 'No description available' }}</div>
                    <div v-if="compliance.PossibleDamage" class="compliance-item-damage">
                      <strong>Possible Damage:</strong> {{ truncateText(compliance.PossibleDamage, 80) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="validationErrors.ComplianceId" class="validation-error">
            {{ validationErrors.ComplianceId }}
          </div>
          <div v-if="showTooltip === 'compliance' && !focusedFields.compliance" class="custom-tooltip">
            Select the compliance identifier for this risk
            <span class="custom-tooltip-arrow"></span>
          </div>
        </div>
        
        <!-- First Row -->
        <div class="form-row">
          <!-- Criticality -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-exclamation-triangle"></i> Criticality</span>
            </label>
            <select 
              v-model="newRisk.Criticality" 
              required
              @mouseenter="handleMouseEnter('criticality')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('criticality')"
              @blur="handleBlur('criticality')"
              @change="validateField('Criticality')"
              :class="{'input-error': validationErrors.Criticality}"
            >
              <option value="">Select Criticality</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <div v-if="validationErrors.Criticality" class="validation-error">
              {{ validationErrors.Criticality }}
            </div>
            <div v-if="showTooltip === 'criticality' && !focusedFields.criticality" class="custom-tooltip">
              Select the level of criticality for this risk (Critical, High, Medium, Low)
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <!-- Category -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-tags"></i> Category</span>
            </label>
            <select 
              v-model="newRisk.Category" 
              required
              @mouseenter="handleMouseEnter('category')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('category')"
              @blur="handleBlur('category')"
              @change="validateField('Category')"
              :class="{'input-error': validationErrors.Category}"
            >
              <option value="">Select Category</option>
              <option value="IT Security">IT Security</option>
              <option value="Operational">Operational</option>
              <option value="Compliance">Compliance</option>
              <option value="Financial">Financial</option>
              <option value="Strategic">Strategic</option>
            </select>
            <div v-if="validationErrors.Category" class="validation-error">
              {{ validationErrors.Category }}
            </div>
            <div v-if="showTooltip === 'category' && !focusedFields.category" class="custom-tooltip">
              Choose the category that best describes this risk (IT Security, Operational, Compliance, Financial, Strategic)
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <!-- Risk Priority -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-level-up-alt"></i> Risk Priority</span>
            </label>
            <select 
              v-model="newRisk.RiskPriority" 
              required
              @mouseenter="handleMouseEnter('priority')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('priority')"
              @blur="handleBlur('priority')"
              @change="validateField('RiskPriority')"
              :class="{'input-error': validationErrors.RiskPriority}"
            >
              <option value="">Select Priority</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <div v-if="validationErrors.RiskPriority" class="validation-error">
              {{ validationErrors.RiskPriority }}
            </div>
            <div v-if="showTooltip === 'priority' && !focusedFields.priority" class="custom-tooltip">
              Set the priority level for addressing this risk (Critical, High, Medium, Low)
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>

        <!-- Second Row -->
        <div class="form-row">
          <!-- Risk Likelihood -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-chart-line"></i> Risk Likelihood</span>
            </label>
            <input 
              type="number" 
              step="1" 
              min="1" 
              max="10" 
              v-model="newRisk.RiskLikelihood" 
              placeholder="Enter value (1-10)" 
              required 
              @mouseenter="handleMouseEnter('likelihood')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('likelihood')"
              @blur="handleBlur('likelihood'); validateField('RiskLikelihood')"
              @input="calculateRiskExposureRating"
              :class="{'input-error': validationErrors.RiskLikelihood}"
            />
            <div v-if="validationErrors.RiskLikelihood" class="validation-error">
              {{ validationErrors.RiskLikelihood }}
            </div>
            <div v-if="showTooltip === 'likelihood' && !focusedFields.likelihood" class="custom-tooltip">
              <div v-if="riskJustifications.likelihood" class="justification-tooltip">
                <strong>AI Justification:</strong><br>
                {{ riskJustifications.likelihood }}
              </div>
              <div v-else>
                Enter an integer between 1-10 indicating how likely this risk is to occur (1=Very Unlikely, 10=Almost Certain)
              </div>
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <!-- Risk Impact -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-chart-bar"></i> Risk Impact</span>
            </label>
            <input 
              type="number" 
              step="1" 
              min="1" 
              max="10" 
              v-model="newRisk.RiskImpact" 
              placeholder="Enter value (1-10)" 
              required 
              @mouseenter="handleMouseEnter('impact')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('impact')"
              @blur="handleBlur('impact'); validateField('RiskImpact')"
              @input="calculateRiskExposureRating"
              :class="{'input-error': validationErrors.RiskImpact}"
            />
            <div v-if="validationErrors.RiskImpact" class="validation-error">
              {{ validationErrors.RiskImpact }}
            </div>
            <div v-if="showTooltip === 'impact' && !focusedFields.impact" class="custom-tooltip">
              <div v-if="riskJustifications.impact" class="justification-tooltip">
                <strong>AI Justification:</strong><br>
                {{ riskJustifications.impact }}
              </div>
              <div v-else>
                Enter an integer between 1-10 indicating the potential impact if this risk occurs (1=Negligible, 10=Catastrophic)
              </div>
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <!-- Risk Exposure Rating -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-tachometer-alt"></i> Risk Exposure Rating (Likelihood × Impact)</span>
            </label>
            <input 
              type="number" 
              readonly 
              v-model.number="newRisk.RiskExposureRating" 
              class="readonly-input"
              @mouseenter="handleMouseEnter('exposure')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('exposure')"
              @blur="handleBlur('exposure')"
              :class="{'input-error': validationErrors.RiskExposureRating}"
            />
            <div v-if="validationErrors.RiskExposureRating" class="validation-error">
              {{ validationErrors.RiskExposureRating }}
            </div>
            <div v-if="showTooltip === 'exposure' && !focusedFields.exposure" class="custom-tooltip">
              Automatically calculated as Risk Likelihood × Risk Impact
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>

        <!-- Third Row -->
        <div class="form-row">
          <!-- Risk Type -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-cubes"></i> Risk Type</span>
            </label>
            <select 
              v-model="newRisk.RiskType" 
              @mouseenter="handleMouseEnter('riskType')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskType')"
              @blur="handleBlur('riskType')"
              @change="validateField('RiskType')"
              :class="{'input-error': validationErrors.RiskType}"
            >
              <option value="">Select Risk Type</option>
              <option value="Current">Current</option>
              <option value="Residual">Residual</option>
              <option value="Inherent">Inherent</option>
              <option value="Emerging">Emerging</option>
              <option value="Accepted">Accepted</option>
            </select>
            <div v-if="validationErrors.RiskType" class="validation-error">
              {{ validationErrors.RiskType }}
            </div>
            <div v-if="showTooltip === 'riskType' && !focusedFields.riskType" class="custom-tooltip">
              Select the type of risk from the available options
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <!-- Business Impact -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-briefcase"></i> Business Impact</span>
            </label>
            <input 
              type="text" 
              v-model="newRisk.BusinessImpact" 
              placeholder="Describe business impact"
              @mouseenter="handleMouseEnter('businessImpact')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('businessImpact')"
              @blur="handleBlur('businessImpact'); validateField('BusinessImpact')"
              :class="{'input-error': validationErrors.BusinessImpact}"
            />
            <div v-if="validationErrors.BusinessImpact" class="validation-error">
              {{ validationErrors.BusinessImpact }}
            </div>
            <div v-if="showTooltip === 'businessImpact' && !focusedFields.businessImpact" class="custom-tooltip">
              Describe how this risk could affect business operations, finances, or reputation
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <!-- Risk Title -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-heading"></i> Risk Title</span>
            </label>
            <input
              type="text"
              v-model="newRisk.RiskTitle"
              required
              @mouseenter="handleMouseEnter('title')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('title')"
              @blur="handleBlur('title'); validateField('RiskTitle')"
              :class="{'input-error': validationErrors.RiskTitle}"
            />
            <div v-if="validationErrors.RiskTitle" class="validation-error">
              {{ validationErrors.RiskTitle }}
            </div>
            <div v-if="showTooltip === 'title' && !focusedFields.title" class="custom-tooltip">
              Enter a clear and concise title that describes the risk
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>

        <!-- Full Width Fields -->
        <div class="form-row full-width">
          <!-- Risk Description -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-align-left"></i> Risk Description</span>
            </label>
            <textarea 
              v-model="newRisk.RiskDescription" 
              required
              @mouseenter="handleMouseEnter('desc')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('desc')"
              @blur="handleBlur('desc'); validateField('RiskDescription')"
              :class="{'input-error': validationErrors.RiskDescription}"
            ></textarea>
            <div v-if="validationErrors.RiskDescription" class="validation-error">
              {{ validationErrors.RiskDescription }}
            </div>
            <div v-if="showTooltip === 'desc' && !focusedFields.desc" class="custom-tooltip">
              Provide a detailed description of the risk, including its nature and context
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>

        <div class="form-row full-width">
          <!-- Possible Damage -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-bomb"></i> Possible Damage</span>
            </label>
            <textarea 
              v-model="newRisk.PossibleDamage"
              @mouseenter="handleMouseEnter('damage')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('damage')"
              @blur="handleBlur('damage'); validateField('PossibleDamage')"
              :class="{'input-error': validationErrors.PossibleDamage}"
            ></textarea>
            <div v-if="validationErrors.PossibleDamage" class="validation-error">
              {{ validationErrors.PossibleDamage }}
            </div>
            <div v-if="showTooltip === 'damage' && !focusedFields.damage" class="custom-tooltip">
              Describe the potential negative consequences or damage that could result from this risk
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>

        <div class="form-row full-width">
          <!-- Risk Mitigation -->
          <div class="risk-register-form-group tooltip-group">
            <label>
              <span><i class="fas fa-shield-alt"></i> Risk Mitigation</span>
            </label>
            <textarea 
              v-model="newRisk.RiskMitigation"
              @mouseenter="handleMouseEnter('mitigation')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('mitigation')"
              @blur="handleBlur('mitigation'); validateField('RiskMitigation')"
              :class="{'input-error': validationErrors.RiskMitigation}"
            ></textarea>
            <div v-if="validationErrors.RiskMitigation" class="validation-error">
              {{ validationErrors.RiskMitigation }}
            </div>
            <div v-if="showTooltip === 'mitigation' && !focusedFields.mitigation" class="custom-tooltip">
              Outline the strategies and actions planned to reduce or eliminate this risk
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>
        
        <!-- Form Actions -->
        <div class="risk-register-form-actions">
          <button type="button" @click="resetForm" class="risk-register-cancel-btn">
            <i class="fas fa-times"></i> Cancel
          </button>
          <button type="submit" class="risk-register-submit-btn">
            <i class="fas fa-save"></i> Create Risk
          </button>
        </div>
      </form>
    </div>
    
    <!-- Success Message -->
    <div v-if="showSuccessMessage" class="form-success-message">
      <i class="fas fa-check-circle"></i> Risk added successfully!
    </div>
  </div>
</template>

<script>
import './CreateRisk.css'
import axios from 'axios'
import { useRouter, useRoute } from 'vue-router'
import { validateForm,  riskFormValidationMap } from './validation.js'

export default {
  name: 'CreateRisk',
  data() {
    return {
      newRisk: {
        ComplianceId: null,
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        RiskDescription: '',
        RiskLikelihood: 1,
        RiskImpact: 1,
        RiskExposureRating: 1,
        RiskPriority: '',
        RiskMitigation: '',
        RiskTitle: '',
        RiskType: 'Current',
        BusinessImpact: ''
      },
      // New properties for validation
      validationErrors: {},
      formSubmitted: false,
      // New properties for compliance dropdown
      compliances: [],
      filteredCompliances: [],
      complianceSearchQuery: '',
      showComplianceDropdown: false,
      loadingCompliances: false,
      selectedComplianceIdText: '',
      
      showSuccessMessage: false,
      showTooltip: '',
      focusedFields: {
        compliance: false,
        criticality: false,
        category: false,
        priority: false,
        likelihood: false,
        impact: false,
        exposure: false,
        title: false,
        desc: false,
        damage: false,
        mitigation: false,
        riskType: false,
        businessImpact: false
      },
      sourceRiskId: null,
      isLoadingSourceRisk: false,
      isAiMode: false,
      aiInput: {
        title: '',
        description: ''
      },
      isGeneratingAi: false,
      aiSuggestionGenerated: false,
      incidentId: null,
      // Store justifications separately for tooltip display
      riskJustifications: {
        likelihood: '',
        impact: ''
      }
    }
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    return { router, route }
  },
  mounted() {
    // Initialize Risk Exposure Rating
    this.calculateRiskExposureRating();
    
    // Check if we have a source risk ID from the query parameters
    if (this.route.query.source_risk_id) {
      this.sourceRiskId = this.route.query.source_risk_id
      this.loadSourceRiskData()
    }
    
    // Check if AI mode is requested via query parameter
    if (this.route.query.mode === 'ai') {
      this.isAiMode = true
      // If we have a source risk ID, fetch incident data for AI analysis
      if (this.sourceRiskId) {
        this.fetchIncidentDataForAI()
      }
    }
    
    // Fetch compliances for dropdown
    this.fetchCompliances();
    
    // Add click event listener to close dropdown when clicking outside
    document.addEventListener('click', this.closeComplianceDropdown);
  },
  beforeUnmount() {
    // Remove event listener when component is unmounted
    document.removeEventListener('click', this.closeComplianceDropdown);
  },
  methods: {
    fetchCompliances() {
      this.loadingCompliances = true;
      
      // API endpoint for fetching compliances for dropdown
      const API_ENDPOINT = 'http://localhost:8000/api/compliances-for-dropdown/';
      
      axios.get(API_ENDPOINT)
        .then(response => {
          this.compliances = response.data;
          this.filteredCompliances = [...response.data];
          this.loadingCompliances = false;
          
          // If a compliance ID is already selected, update the text
          if (this.newRisk.ComplianceId) {
            this.updateSelectedComplianceIdText();
          }
        })
        .catch(error => {
          console.error('Error fetching compliances:', error);
          this.loadingCompliances = false;
          this.compliances = [];
          this.filteredCompliances = [];
        });
    },
    filterCompliances() {
      if (!this.complianceSearchQuery) {
        this.filteredCompliances = [...this.compliances];
        return;
      }
      
      const query = this.complianceSearchQuery.toLowerCase();
      this.filteredCompliances = this.compliances.filter(compliance => 
        (compliance.ComplianceId && compliance.ComplianceId.toString().includes(query)) ||
        (compliance.ComplianceItemDescription && compliance.ComplianceItemDescription.toLowerCase().includes(query)) ||
        (compliance.Criticality && compliance.Criticality.toLowerCase().includes(query)) ||
        (compliance.PossibleDamage && compliance.PossibleDamage.toLowerCase().includes(query))
      );
    },
    selectCompliance(compliance) {
      this.newRisk.ComplianceId = compliance.ComplianceId;
      this.selectedComplianceIdText = `Compliance ID: ${compliance.ComplianceId}`;
      this.showComplianceDropdown = false;
      
      // Optionally pre-fill other fields based on the selected compliance
      if (compliance.Criticality) this.newRisk.Criticality = compliance.Criticality;
      if (compliance.PossibleDamage) this.newRisk.PossibleDamage = compliance.PossibleDamage;
    },
    toggleComplianceDropdown() {
      this.showComplianceDropdown = !this.showComplianceDropdown;
      if (this.showComplianceDropdown) {
        this.complianceSearchQuery = '';
        this.filterCompliances();
      }
    },
    closeComplianceDropdown(event) {
      // Check if the click was outside the dropdown
      const dropdown = document.querySelector('.compliance-dropdown-container');
      if (dropdown && !dropdown.contains(event.target)) {
        this.showComplianceDropdown = false;
      }
    },
    updateSelectedComplianceIdText() {
      if (this.newRisk.ComplianceId) {
        const selectedCompliance = this.compliances.find(compliance => compliance.ComplianceId === parseInt(this.newRisk.ComplianceId));
        if (selectedCompliance) {
          this.selectedComplianceIdText = `Compliance ID: ${selectedCompliance.ComplianceId}`;
        } else {
          this.selectedComplianceIdText = `Compliance ID: ${this.newRisk.ComplianceId}`;
        }
      } else {
        this.selectedComplianceIdText = '';
      }
    },
    truncateText(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    calculateRiskExposureRating() {
      // Get the current values of RiskLikelihood and RiskImpact
      const likelihood = parseInt(this.newRisk.RiskLikelihood) || 1;
      const impact = parseInt(this.newRisk.RiskImpact) || 1;
      
      // Calculate the Risk Exposure Rating as the product
      this.newRisk.RiskExposureRating = likelihood * impact;
    },
    loadSourceRiskData() {
      if (!this.sourceRiskId) return
      
      this.isLoadingSourceRisk = true
      
      // Fetch the source risk instance data
      axios.get(`http://localhost:8000/api/risk-instances/${this.sourceRiskId}/`)
        .then(response => {
          console.log('Source risk data loaded:', response.data)
          // Pre-fill form with relevant data from the source risk
          const sourceRisk = response.data
          
          // Store the incident ID for later use
          this.incidentId = sourceRisk.IncidentId
          
          // Map the fields from source risk to the new risk form
          // Only copy over fields that make sense to share between risks
          if (sourceRisk.ComplianceId) this.newRisk.ComplianceId = sourceRisk.ComplianceId
          if (sourceRisk.Category) this.newRisk.Category = sourceRisk.Category
          if (sourceRisk.RiskTitle) this.newRisk.RiskTitle = sourceRisk.RiskTitle
          if (sourceRisk.RiskDescription) this.newRisk.RiskDescription = sourceRisk.RiskDescription
          
          // Don't copy over instance-specific fields like IDs, ratings, etc.
          
          this.isLoadingSourceRisk = false
          
          // If in AI mode, fetch incident data for AI analysis
          if (this.isAiMode && this.incidentId) {
            this.fetchIncidentDataForAI()
          }
        })
        .catch(error => {
          console.error('Error loading source risk data:', error)
          this.isLoadingSourceRisk = false
          // Show an error message or handle the error as needed
        })
    },
    fetchIncidentDataForAI() {
      if (!this.incidentId) {
        console.error('No incident ID available for AI analysis')
        return
      }
      
      this.isGeneratingAi = true
      console.log(`Fetching incident data for ID: ${this.incidentId}`)
      
      // Fetch the incident data
      axios.get(`http://localhost:8000/api/incidents/${this.incidentId}/`)
        .then(response => {
          const incident = response.data
          console.log('Incident data loaded:', incident)
          
          // Set the AI input fields with incident data
          this.aiInput.title = incident.Title || ''
          this.aiInput.description = incident.Description || ''
          
          // Automatically generate AI suggestion if we have the data
          if (this.aiInput.title || this.aiInput.description) {
            this.generateAiSuggestion()
          } else {
            this.isGeneratingAi = false
            console.warn('Incident data missing title or description')
          }
        })
        .catch(error => {
          console.error('Error fetching incident data:', error)
          this.isGeneratingAi = false
        })
    },
    setCreationMode(isAi) {
      this.isAiMode = isAi
      if (!isAi) {
        // Reset AI-related data when switching to manual mode
        this.aiSuggestionGenerated = false
      } else if (this.incidentId) {
        // If switching to AI mode and we have an incident ID, fetch the data
        this.fetchIncidentDataForAI()
      }
    },
    generateAiSuggestion() {
      if (!this.aiInput.title && !this.aiInput.description) {
        alert('Please provide either a title or description for AI analysis.')
        return
      }
      
      this.isGeneratingAi = true
      
      // Prepare the data for analysis - use at least one field if the other is missing
      const analysisData = {
        title: this.aiInput.title || 'Untitled Incident',
        description: this.aiInput.description || this.aiInput.title || 'No description available'
      }
      
      console.log('Sending to AI analysis:', analysisData)
      
      // Call the backend API to analyze the incident
      axios.post('http://localhost:8000/api/analyze-incident/', analysisData)
        .then(response => {
          console.log('AI Analysis Response:', response.data)
          
          // Check if the response contains an error
          if (response.data.error) {
            throw new Error(response.data.error)
          }
          
          // Validate that we received AI-generated content
          if (response.data.riskLikelihoodJustification || response.data.riskImpactJustification) {
            console.log('✅ Using AI-generated justifications')
          } else {
            console.log('⚠️ No AI justifications found, might be using fallback')
          }
          
          // Map the AI response to the risk form fields
          this.mapAnalysisToForm(response.data)
          
          // Mark as generated so we show the form
          this.aiSuggestionGenerated = true
          this.isGeneratingAi = false
        })
        .catch(error => {
          console.error('Error analyzing incident:', error.response || error)
          
          this.isGeneratingAi = false
          
          // Show a more detailed error message
          let errorMessage = 'Failed to generate AI suggestion.'
          
          if (error.message) {
            errorMessage = error.message
          } else if (error.response && error.response.data) {
            if (error.response.data.error) {
              errorMessage = error.response.data.error
            } else if (typeof error.response.data === 'object') {
              errorMessage += ' Error: ' + JSON.stringify(error.response.data)
            } else {
              errorMessage += ' Error: ' + error.response.data
            }
          }
          
          // Show error message with options
          const userChoice = confirm(
            errorMessage + '\n\nWould you like to:\n' +
            'OK - Try again with different input\n' +
            'Cancel - Switch to manual mode'
          )
          
          if (!userChoice) {
            // User chose to switch to manual mode
            this.isAiMode = false
            this.aiSuggestionGenerated = false
          }
          // If user chose OK, they can modify the input and try again
        })
    },
    mapAnalysisToForm(analysis) {
      console.log('Mapping analysis to form:', analysis)
      
      // Map criticality (convert from text to the dropdown values if needed)
      if (analysis.criticality) {
        const criticalityMap = {
          'Severe': 'Critical',
          'Significant': 'High',
          'Moderate': 'Medium',
          'Minor': 'Low'
        }
        this.newRisk.Criticality = criticalityMap[analysis.criticality] || analysis.criticality
        console.log('Mapped criticality:', this.newRisk.Criticality)
      }
      
      // Map possible damage
      this.newRisk.PossibleDamage = analysis.possibleDamage || ''
      
      // Map category
      this.newRisk.Category = analysis.category || ''
      
      // Map risk description
      this.newRisk.RiskDescription = analysis.riskDescription || ''
      
      // Map risk title from AI input title
      this.newRisk.RiskTitle = this.aiInput.title || ''
      
      // Map risk likelihood (now expects integer 1-10)
      if (analysis.riskLikelihood) {
        this.newRisk.RiskLikelihood = analysis.riskLikelihood.toString()
        this.riskJustifications.likelihood = analysis.riskLikelihoodJustification || ''
        console.log('Mapped likelihood:', this.newRisk.RiskLikelihood, 'with justification:', this.riskJustifications.likelihood)
      }
      
      // Map risk impact (now expects integer 1-10)
      if (analysis.riskImpact) {
        this.newRisk.RiskImpact = analysis.riskImpact.toString()
        this.riskJustifications.impact = analysis.riskImpactJustification || ''
        console.log('Mapped impact:', this.newRisk.RiskImpact, 'with justification:', this.riskJustifications.impact)
      }
      
      // Map risk exposure rating based on the exposure rating from AI
      if (analysis.riskExposureRating) {
        const exposureMap = {
          'Critical Exposure': '9.0',
          'High Exposure': '7.5',
          'Elevated Exposure': '5.5',
          'Low Exposure': '3.0'
        }
        this.newRisk.RiskExposureRating = exposureMap[analysis.riskExposureRating] || '6.0'
      } else {
        // Calculate exposure rating as likelihood * impact if not provided
        const likelihood = parseFloat(this.newRisk.RiskLikelihood) || 5.0
        const impact = parseFloat(this.newRisk.RiskImpact) || 5.0
        this.newRisk.RiskExposureRating = ((likelihood * impact) / 10).toFixed(1)
      }
      
      // Map risk priority
      if (analysis.riskPriority) {
        const priorityMap = {
          'P0': 'Critical',
          'P1': 'High',
          'P2': 'Medium',
          'P3': 'Low'
        }
        this.newRisk.RiskPriority = priorityMap[analysis.riskPriority] || 'Medium'
      }
      
      // Map risk mitigation
      if (analysis.riskMitigation && Array.isArray(analysis.riskMitigation)) {
        // Join but ensure it doesn't exceed reasonable length
        this.newRisk.RiskMitigation = analysis.riskMitigation.join('\n')
      }
      
      // Map business impact from the description
      this.newRisk.BusinessImpact = this.aiInput.description || ''
      
      // Map risk type based on category
      this.newRisk.RiskType = analysis.category || ''
      
      // Auto-generate a compliance ID if not already set
      if (!this.newRisk.ComplianceId && this.incidentId) {
        // Use incident ID as a base for compliance ID
        this.newRisk.ComplianceId = this.incidentId
      }
      
      console.log('Final risk justifications:', this.riskJustifications)
    },
    handleFocus(field) {
      this.focusedFields[field] = true;
      if (this.showTooltip === field) {
        this.showTooltip = '';
      }
    },
    handleBlur(field) {
      this.focusedFields[field] = false;
    },
    handleMouseEnter(field) {
      if (!this.focusedFields[field]) {
        this.showTooltip = field;
      }
    },
    handleMouseLeave() {
      this.showTooltip = '';
    },
    resetForm() {
      this.newRisk = {
        ComplianceId: null,
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        RiskDescription: '',
        RiskLikelihood: 1,
        RiskImpact: 1,
        RiskExposureRating: 1,
        RiskPriority: '',
        RiskMitigation: '',
        RiskTitle: '',
        RiskType: 'Current',
        BusinessImpact: ''
      }
      
      // Reset validation state
      this.validationErrors = {};
      this.formSubmitted = false;
      
      // Reset selected compliance ID text
      this.selectedComplianceIdText = '';
      
      // Calculate initial Risk Exposure Rating
      this.calculateRiskExposureRating();
      
      // Reset AI-related data
      this.aiSuggestionGenerated = false
      this.aiInput = {
        title: '',
        description: ''
      }
      
      // Reset justifications
      this.riskJustifications = {
        likelihood: '',
        impact: ''
      }
    },
    submitRisk() {
      // Mark form as submitted to show all validation errors
      this.formSubmitted = true;
      
      // Validate the entire form
      const { isValid, errors } = validateForm(this.newRisk, riskFormValidationMap);
      this.validationErrors = errors;
      
      // If validation fails, prevent submission
      if (!isValid) {
        console.error('Form validation failed:', errors);
        // Scroll to first error
        this.$nextTick(() => {
          const firstErrorField = document.querySelector('.validation-error');
          if (firstErrorField) {
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        });
        return;
      }
      
      // Sanitize the form data
      //const sanitizedData = sanitizeForm(this.newRisk);


      
      // Convert numeric string values to actual numbers
      const formData = {
        ...this.newRisk,
        ComplianceId: parseInt(this.newRisk.ComplianceId) || null,
        RiskLikelihood: parseInt(this.newRisk.RiskLikelihood) || 0,
        RiskImpact: parseInt(this.newRisk.RiskImpact) || 0,
        RiskExposureRating: this.newRisk.RiskExposureRating ? 
          parseFloat(this.newRisk.RiskExposureRating) : null
      }
      
      axios.post('http://localhost:8000/api/risks/', formData)
        .then(() => {
          // Reset the form
          this.resetForm()
          
          // Show success message
          this.showSuccessMessage = true
          setTimeout(() => {
            this.showSuccessMessage = false
          }, 3000)
          
          // Navigate to risk register list
          this.router.push('/risk/riskregister-list')
        })
        .catch(error => {
          console.error('Error adding risk:', error.response?.data || error.message)
          alert('Error adding risk. Please check your data and try again.')
        })
    },
    validateField(fieldName) {
      if (!this.formSubmitted) return;
      
      const fieldValue = this.newRisk[fieldName];
      const validationType = riskFormValidationMap[fieldName];
      
      if (!validationType) return;
      
      const { validateField } = require('./validation.js');
      const result = validateField(fieldValue, validationType);
      
      if (!result.isValid) {
        this.validationErrors[fieldName] = result.error;
      } else {
        delete this.validationErrors[fieldName];
      }
    }
  }
}
</script>
