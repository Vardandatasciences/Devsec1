<template>
  <div class="create-risk-instance-container">
    <div class="create-risk-instance-card">
      <div class="create-risk-instance-header">
        <h2>Create Risk Instance</h2>
      </div>
      
      <!-- Add form error summary if there are validation errors -->
      <div v-if="formSubmitted && Object.keys(validationErrors).length > 0" class="form-error-summary">
        <h4>Please correct the following errors:</h4>
        <ul>
          <li v-for="(error, field) in validationErrors" :key="field">
            {{ field }}: {{ error }}
          </li>
        </ul>
      </div>
      
      <form @submit.prevent="submitInstance" class="create-risk-instance-form">
        <div class="form-group field-full tooltip-group">
          <label for="riskId"><i class="fas fa-id-badge"></i> Risk ID</label>
          <div class="risk-dropdown-container">
            <input 
              type="text" 
              id="riskId" 
              v-model="selectedRiskIdText" 
              placeholder="Enter or select risk ID"
              @focus="showRiskDropdown = true"
              @mouseenter="handleMouseEnter('riskId')"
              @mouseleave="handleMouseLeave"
              readonly
              :class="{'input-error': validationErrors.RiskId}"
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
                  @input="filterRisks"
                  @click.stop
                >
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
                      :checked="newInstance.RiskId === risk.RiskId"
                      @click.stop="selectRisk(risk)"
                    >
                  </div>
                  <div class="risk-item-content">
                    <div class="risk-item-header">
                      <span class="risk-id">ID: {{ risk.RiskId }}</span>
                      <span :class="'risk-criticality ' + risk.Criticality.toLowerCase()">{{ risk.Criticality }}</span>
                      <span class="risk-category">{{ risk.Category }}</span>
                    </div>
                    <div class="risk-item-title">{{ risk.RiskTitle || 'No Title' }}</div>
                    <div class="risk-item-description">{{ truncateText(risk.RiskDescription, 100) }}</div>
                    <div v-if="risk.PossibleDamage" class="risk-item-damage">
                      <strong>Possible Damage:</strong> {{ truncateText(risk.PossibleDamage, 80) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="validationErrors.RiskId" class="validation-error">
            {{ validationErrors.RiskId }}
          </div>
          <div v-if="showTooltip === 'riskId' && !focusedFields.riskId" class="custom-tooltip">
            Select the risk ID this instance is related to
            <span class="custom-tooltip-arrow"></span>
          </div>
        </div>
        
        <div class="form-section">
          <div class="form-group tooltip-group">
            <label for="criticality"><i class="fas fa-exclamation-triangle"></i> Criticality</label>
            <select 
              id="criticality" 
              class="priority-select" 
              v-model="newInstance.Criticality"
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
              Select the level of criticality for this risk instance (Critical, High, Medium, Low)
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="category"><i class="fas fa-tag"></i> Category</label>
            <select 
              id="category" 
              class="category-select" 
              v-model="newInstance.Category"
              @mouseenter="handleMouseEnter('category')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('category')"
              @blur="handleBlur('category')"
              @change="validateField('Category')"
              :class="{'input-error': validationErrors.Category}"
            >
              <option value="">Select Category</option>
              <option value="IT Security">IT Security</option>
              <option value="IT Security, Compliance">IT Security, Compliance</option>
              <option value="Operational">Operational</option>
              <option value="Compliance">Compliance</option>
              <option value="Financial">Financial</option>
              <option value="Strategic">Strategic</option>
            </select>
            <div v-if="validationErrors.Category" class="validation-error">
              {{ validationErrors.Category }}
            </div>
            <div v-if="showTooltip === 'category' && !focusedFields.category" class="custom-tooltip">
              Choose the category that best describes this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="appetite"><i class="fas fa-balance-scale"></i> Appetite</label>
            <select 
              id="appetite" 
              v-model="newInstance.Appetite"
              :class="[
                {'input-error': validationErrors.Appetite}, 
                {'rejected-appetite': newInstance.Appetite === 'No'}
              ]"
              @mouseenter="handleMouseEnter('appetite')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('appetite')"
              @blur="handleBlur('appetite')"
              @change="onAppetiteChange(); validateField('Appetite')"
            >
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
            <div v-if="validationErrors.Appetite" class="validation-error">
              {{ validationErrors.Appetite }}
            </div>
            <div v-if="showTooltip === 'appetite' && !focusedFields.appetite" class="custom-tooltip">
              Select whether this risk is within the organization's risk appetite
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskLikelihood"><i class="fas fa-chart-line"></i> Risk Likelihood</label>
            <input 
              type="number" 
              step="1" 
              min="1" 
              max="10" 
              id="riskLikelihood" 
              v-model.number="newInstance.RiskLikelihood" 
              placeholder="Enter value (1-10)"
              @mouseenter="handleMouseEnter('riskLikelihood')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskLikelihood')"
              @blur="handleBlur('riskLikelihood'); validateField('RiskLikelihood')"
              @input="calculateRiskExposureRating"
              :class="{'input-error': validationErrors.RiskLikelihood}"
            >
            <div v-if="validationErrors.RiskLikelihood" class="validation-error">
              {{ validationErrors.RiskLikelihood }}
            </div>
            <div v-if="showTooltip === 'riskLikelihood' && !focusedFields.riskLikelihood" class="custom-tooltip">
              Enter a number between 1-10 indicating how likely this risk instance is to occur
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskImpact"><i class="fas fa-bolt"></i> Risk Impact</label>
            <input 
              type="number" 
              step="1" 
              min="1" 
              max="10" 
              id="riskImpact" 
              v-model.number="newInstance.RiskImpact" 
              placeholder="Enter value (1-10)"
              @mouseenter="handleMouseEnter('riskImpact')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskImpact')"
              @blur="handleBlur('riskImpact'); validateField('RiskImpact')"
              @input="calculateRiskExposureRating"
              :class="{'input-error': validationErrors.RiskImpact}"
            >
            <div v-if="validationErrors.RiskImpact" class="validation-error">
              {{ validationErrors.RiskImpact }}
            </div>
            <div v-if="showTooltip === 'riskImpact' && !focusedFields.riskImpact" class="custom-tooltip">
              Enter a number between 1-10 indicating the potential impact if this risk instance occurs
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskExposureRating"><i class="fas fa-thermometer-half"></i> Risk Exposure Rating (Likelihood × Impact)</label>
            <input type="number" readonly id="riskExposureRating" v-model.number="newInstance.RiskExposureRating" class="readonly-input"
              @mouseenter="handleMouseEnter('riskExposureRating')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskExposureRating')"
              @blur="handleBlur('riskExposureRating')"
            >
            <div v-if="showTooltip === 'riskExposureRating' && !focusedFields.riskExposureRating" class="custom-tooltip">
              Automatically calculated as Risk Likelihood × Risk Impact
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskPriority"><i class="fas fa-flag"></i> Risk Priority</label>
            <select id="riskPriority" class="priority-select" v-model="newInstance.RiskPriority"
              @mouseenter="handleMouseEnter('riskPriority')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskPriority')"
              @blur="handleBlur('riskPriority')"
            >
              <option value="">Select Priority</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <div v-if="showTooltip === 'riskPriority' && !focusedFields.riskPriority" class="custom-tooltip">
              Set the priority level for addressing this risk instance (Critical, High, Medium, Low)
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskResponseType"><i class="fas fa-shield-alt"></i> Response Type</label>
            <select id="riskResponseType" v-model="newInstance.RiskResponseType"
              @mouseenter="handleMouseEnter('riskResponseType')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskResponseType')"
              @blur="handleBlur('riskResponseType')"
            >
              <option value="">Select Response Type</option>
              <option value="Avoidance">Avoidance</option>
              <option value="Mitigation">Mitigation</option>
              <option value="Transfer">Transfer</option>
              <option value="Acceptance">Acceptance</option>
            </select>
            <div v-if="showTooltip === 'riskResponseType' && !focusedFields.riskResponseType" class="custom-tooltip">
              Select the response strategy for this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskOwner"><i class="fas fa-user"></i> Risk Owner</label>
            <div class="user-dropdown-container">
              <input 
                type="text" 
                id="riskOwner" 
                v-model="selectedOwnerText" 
                placeholder="Select risk owner"
                @focus="showUserDropdown = true"
                @mouseenter="handleMouseEnter('riskOwner')"
                @mouseleave="handleMouseLeave"
                readonly
              >
              <button type="button" class="dropdown-toggle" @click="toggleUserDropdown">
                <i class="fas fa-chevron-down"></i>
              </button>
              
              <div v-if="showUserDropdown" class="user-dropdown">
                <div class="user-dropdown-search">
                  <input 
                    type="text" 
                    v-model="userSearchQuery" 
                    placeholder="Search users..." 
                    @input="filterUsers"
                    @click.stop
                  >
                </div>
                <div class="user-dropdown-list" v-if="loadingUsers">
                  <div class="loading-spinner">Loading users...</div>
                </div>
                <div class="user-dropdown-list" v-else-if="filteredUsers.length === 0">
                  <div class="no-results">No users found</div>
                </div>
                <div class="user-dropdown-list" v-else>
                  <div 
                    v-for="user in filteredUsers" 
                    :key="user.user_id" 
                    class="user-item"
                    @click="selectUser(user)"
                  >
                    <div class="user-item-checkbox">
                      <input 
                        type="checkbox" 
                        :id="'user-' + user.user_id" 
                        :checked="newInstance.UserId === user.user_id"
                        @click.stop="selectUser(user)"
                      >
                    </div>
                    <div class="user-item-content">
                      <div class="user-item-name">{{ user.user_name }}</div>
                      <div class="user-item-details">
                        <span v-if="user.department" class="user-department">{{ user.department }}</span>
                        <span v-if="user.designation" class="user-designation">{{ user.designation }}</span>
                        <span v-if="user.email" class="user-email">{{ user.email }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="showTooltip === 'riskOwner' && !focusedFields.riskOwner" class="custom-tooltip">
              Enter the name of the person responsible for this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskStatus"><i class="fas fa-info-circle"></i> Risk Status</label>
            <select id="riskStatus" v-model="newInstance.RiskStatus"
              @mouseenter="handleMouseEnter('riskStatus')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskStatus')"
              @blur="handleBlur('riskStatus')"
            >
              <option value="Not Assigned">Not Assigned</option>
              <option value="Assigned">Assigned</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
            </select>
            <div v-if="showTooltip === 'riskStatus' && !focusedFields.riskStatus" class="custom-tooltip">
              Set the current status of this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskTitle"><i class="fas fa-heading"></i> Risk Title</label>
            <input type="text" id="riskTitle" v-model="newInstance.RiskTitle" placeholder="Enter risk title"
              @mouseenter="handleMouseEnter('riskTitle')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskTitle')"
              @blur="handleBlur('riskTitle')"
            >
            <div v-if="showTooltip === 'riskTitle' && !focusedFields.riskTitle" class="custom-tooltip">
              Enter a clear and concise title for this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="businessImpact"><i class="fas fa-briefcase"></i> Business Impact</label>
            <input type="text" id="businessImpact" v-model="newInstance.BusinessImpact" placeholder="Describe business impact"
              @mouseenter="handleMouseEnter('businessImpact')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('businessImpact')"
              @blur="handleBlur('businessImpact')"
            >
            <div v-if="showTooltip === 'businessImpact' && !focusedFields.businessImpact" class="custom-tooltip">
              Describe how this risk could affect business operations, finances, or reputation
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="origin"><i class="fas fa-globe"></i> Origin</label>
            <input type="text" id="origin" v-model="newInstance.Origin" placeholder="Enter origin (optional)"
              @mouseenter="handleMouseEnter('origin')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('origin')"
              @blur="handleBlur('origin')"
            >
            <div v-if="showTooltip === 'origin' && !focusedFields.origin" class="custom-tooltip">
              Specify the origin of this risk instance (if applicable)
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="complianceId"><i class="fas fa-hashtag"></i> Compliance ID</label>
            <div class="compliance-dropdown-container">
              <input 
                type="text" 
                id="complianceId" 
                v-model="selectedComplianceIdText" 
                placeholder="Enter or select compliance ID"
                @focus="showComplianceDropdown = true"
                @mouseenter="handleMouseEnter('complianceId')"
                @mouseleave="handleMouseLeave"
                readonly
              >
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
                        :checked="newInstance.ComplianceId === compliance.ComplianceId"
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
            <div v-if="showTooltip === 'complianceId' && !focusedFields.complianceId" class="custom-tooltip">
              Enter the compliance ID associated with this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group tooltip-group">
            <label for="riskType"><i class="fas fa-cubes"></i> Risk Type</label>
            <select id="riskType" v-model="newInstance.RiskType"
              @mouseenter="handleMouseEnter('riskType')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskType')"
              @blur="handleBlur('riskType')"
            >
              <option value="Current">Current</option>
              <option value="Residual">Residual</option>
              <option value="Inherent">Inherent</option>
              <option value="Emerging">Emerging</option>
              <option value="Accepted">Accepted</option>
            </select>
            <div v-if="showTooltip === 'riskType' && !focusedFields.riskType" class="custom-tooltip">
              Select the type of risk from the available options
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>
        
        <div class="form-section text-areas-section">
          <div class="form-group field-full tooltip-group">
            <label for="riskDescription"><i class="fas fa-align-left"></i> Risk Description</label>
            <textarea 
              id="riskDescription" 
              v-model="newInstance.RiskDescription" 
              placeholder="Describe the risk..."
              rows="3"
              @mouseenter="handleMouseEnter('riskDescription')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskDescription')"
              @blur="handleBlur('riskDescription'); validateField('RiskDescription')"
              :class="{'input-error': validationErrors.RiskDescription}"
            ></textarea>
            <div v-if="validationErrors.RiskDescription" class="validation-error">
              {{ validationErrors.RiskDescription }}
            </div>
            <div v-if="showTooltip === 'riskDescription' && !focusedFields.riskDescription" class="custom-tooltip">
              Provide a detailed description of the risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group field-full tooltip-group">
            <label for="possibleDamage"><i class="fas fa-exclamation-circle"></i> Possible Damage</label>
            <textarea 
              id="possibleDamage" 
              v-model="newInstance.PossibleDamage" 
              placeholder="Describe possible damage..."
              rows="2"
              @mouseenter="handleMouseEnter('possibleDamage')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('possibleDamage')"
              @blur="handleBlur('possibleDamage')"
            ></textarea>
            <div v-if="showTooltip === 'possibleDamage' && !focusedFields.possibleDamage" class="custom-tooltip">
              Describe the potential negative consequences or damage for this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group field-full tooltip-group">
            <label for="riskResponseDescription"><i class="fas fa-reply"></i> Response Description</label>
            <textarea 
              id="riskResponseDescription" 
              v-model="newInstance.RiskResponseDescription" 
              placeholder="Describe the response strategy..."
              rows="2"
              @mouseenter="handleMouseEnter('riskResponseDescription')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskResponseDescription')"
              @blur="handleBlur('riskResponseDescription')"
            ></textarea>
            <div v-if="showTooltip === 'riskResponseDescription' && !focusedFields.riskResponseDescription" class="custom-tooltip">
              Describe the planned response for this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
          
          <div class="form-group field-full tooltip-group">
            <label for="riskMitigation"><i class="fas fa-shield-virus"></i> Risk Mitigation</label>
            <textarea 
              id="riskMitigation" 
              v-model="newInstance.RiskMitigation" 
              placeholder="Describe mitigation actions..."
              rows="2"
              @mouseenter="handleMouseEnter('riskMitigation')"
              @mouseleave="handleMouseLeave"
              @focus="handleFocus('riskMitigation')"
              @blur="handleBlur('riskMitigation')"
            ></textarea>
            <div v-if="showTooltip === 'riskMitigation' && !focusedFields.riskMitigation" class="custom-tooltip">
              Outline the strategies and actions planned to reduce or eliminate this risk instance
              <span class="custom-tooltip-arrow"></span>
            </div>
          </div>
        </div>
        
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="resetForm">Clear</button>
          <button type="submit" class="btn-submit">Create</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import './CreateRiskInstance.css'
import { validateForm, sanitizeForm, riskInstanceFormValidationMap } from './validation.js'

export default {
  name: 'CreateRiskInstance',
  props: {
    riskId: {
      type: [String, Number],
      default: null
    },
    incidentId: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      newInstance: {
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        Appetite: 'Yes',
        RiskDescription: '',
        RiskLikelihood: 1,
        RiskImpact: 1,
        RiskExposureRating: 1,
        RiskPriority: '',
        RiskResponseType: 'Mitigation',
        RiskResponseDescription: '',
        RiskMitigation: '',
        RiskOwner: '',
        RiskStatus: 'Not Assigned',
        UserId: 1,
        RiskId: null,
        IncidentId: null,
        RiskTitle: '',
        BusinessImpact: '',
        Origin: '',
        MitigationDueDate: '',
        MitigationStatus: '',
        MitigationCompletedDate: '',
        ReviewerCount: '',
        RecurrenceCount: 1,
        RiskFormDetails: '',
        ModifiedMitigations: '',
        ComplianceId: '',
        RiskType: 'Current'
      },
      // New validation properties
      validationErrors: {},
      formSubmitted: false,
      // Existing properties
      risks: [],
      filteredRisks: [],
      riskSearchQuery: '',
      showRiskDropdown: false,
      loadingRisks: false,
      selectedRiskIdText: '',
      
      isDebugging: false,
      testResults: [],
      showTooltip: '',
      focusedFields: {
        criticality: false,
        category: false,
        appetite: false,
        riskDescription: false,
        possibleDamage: false,
        riskLikelihood: false,
        riskImpact: false,
        riskExposureRating: false,
        riskPriority: false,
        riskResponseType: false,
        riskOwner: false,
        riskResponseDescription: false,
        riskMitigation: false,
        riskStatus: false,
        userId: false,
        riskTitle: false,
        businessImpact: false,
        origin: false,
        mitigationDueDate: false,
        mitigationStatus: false,
        mitigationCompletedDate: false,
        reviewerCount: false,
        recurrenceCount: false,
        riskFormDetails: false,
        modifiedMitigations: false,
        complianceId: false,
        riskType: false,
        riskId: false
      },
      selectedOwnerText: '',
      showUserDropdown: false,
      loadingUsers: false,
      userSearchQuery: '',
      filteredUsers: [],
      users: [],
      selectedComplianceIdText: '',
      showComplianceDropdown: false,
      loadingCompliances: false,
      complianceSearchQuery: '',
      filteredCompliances: [],
      compliances: []
    }
  },
  mounted() {
    // Initialize Risk Exposure Rating
    this.calculateRiskExposureRating();
    
    // Always prefer props, but fallback to route query if not set
    if (this.riskId !== null && this.riskId !== undefined) {
      this.newInstance.RiskId = this.riskId;
      this.updateSelectedRiskIdText();
    } else if (this.$route.query.riskId) {
      this.newInstance.RiskId = this.$route.query.riskId;
      this.updateSelectedRiskIdText();
    }

    if (this.incidentId !== null && this.incidentId !== undefined) {
      this.newInstance.IncidentId = this.incidentId;
    } else if (this.$route.query.incidentId) {
      this.newInstance.IncidentId = this.$route.query.incidentId;
    }

    // Fetch data from API
    this.fetchRisks();
    this.fetchUsers();
    this.fetchCompliances();

    // Add click event listener to close dropdowns when clicking outside
    document.addEventListener('click', this.closeRiskDropdown);
    document.addEventListener('click', this.closeUserDropdown);
    document.addEventListener('click', this.closeComplianceDropdown);

    // Optionally, log for debugging
    console.log('CreateRiskInstance mounted with:', {
      riskId: this.newInstance.RiskId,
      incidentId: this.newInstance.IncidentId
    });
  },
  beforeUnmount() {
    // Remove event listeners when component is unmounted
    document.removeEventListener('click', this.closeRiskDropdown);
    document.removeEventListener('click', this.closeUserDropdown);
    document.removeEventListener('click', this.closeComplianceDropdown);
  },
  methods: {
    fetchRisks() {
      this.loadingRisks = true;
      
      // API endpoint for fetching risks for dropdown
      const API_ENDPOINT = 'http://127.0.0.1:8000/api/risks-for-dropdown/';
      
      fetch(API_ENDPOINT)
        .then(response => {
          if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          this.risks = data;
          this.filteredRisks = [...data];
          this.loadingRisks = false;
          
          // If a risk ID is already selected, update the text
          if (this.newInstance.RiskId) {
            this.updateSelectedRiskIdText();
          }
        })
        .catch(error => {
          console.error('Error fetching risks:', error);
          this.loadingRisks = false;
          this.risks = [];
          this.filteredRisks = [];
        });
    },
    filterRisks() {
      if (!this.riskSearchQuery) {
        this.filteredRisks = [...this.risks];
        return;
      }
      
      const query = this.riskSearchQuery.toLowerCase();
      this.filteredRisks = this.risks.filter(risk => 
        (risk.RiskId && risk.RiskId.toString().includes(query)) ||
        (risk.RiskTitle && risk.RiskTitle.toLowerCase().includes(query)) ||
        (risk.Category && risk.Category.toLowerCase().includes(query)) ||
        (risk.RiskDescription && risk.RiskDescription.toLowerCase().includes(query))
      );
    },
    selectRisk(risk) {
      this.newInstance.RiskId = risk.RiskId;
      this.selectedRiskIdText = `Risk ID: ${risk.RiskId}`;
      this.showRiskDropdown = false;
      
      // Optionally pre-fill other fields based on the selected risk
      if (risk.RiskTitle) this.newInstance.RiskTitle = risk.RiskTitle;
      if (risk.Criticality) this.newInstance.Criticality = risk.Criticality;
      if (risk.Category) this.newInstance.Category = risk.Category;
      if (risk.PossibleDamage) this.newInstance.PossibleDamage = risk.PossibleDamage;
      if (risk.RiskDescription) this.newInstance.RiskDescription = risk.RiskDescription;
    },
    toggleRiskDropdown() {
      this.showRiskDropdown = !this.showRiskDropdown;
      if (this.showRiskDropdown) {
        this.riskSearchQuery = '';
        this.filterRisks();
      }
    },
    closeRiskDropdown(event) {
      // Check if the click was outside the dropdown
      const dropdown = document.querySelector('.risk-dropdown-container');
      if (dropdown && !dropdown.contains(event.target)) {
        this.showRiskDropdown = false;
      }
    },
    updateSelectedRiskIdText() {
      if (this.newInstance.RiskId) {
        const selectedRisk = this.risks.find(risk => risk.RiskId === parseInt(this.newInstance.RiskId));
        if (selectedRisk) {
          this.selectedRiskIdText = `Risk ID: ${selectedRisk.RiskId}`;
        } else {
          this.selectedRiskIdText = `Risk ID: ${this.newInstance.RiskId}`;
        }
      } else {
        this.selectedRiskIdText = '';
      }
    },
    truncateText(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    calculateRiskExposureRating() {
      // Get the current values of RiskLikelihood and RiskImpact
      const likelihood = parseInt(this.newInstance.RiskLikelihood) || 0;
      const impact = parseInt(this.newInstance.RiskImpact) || 0;
      
      // Calculate the Risk Exposure Rating as the product
      // Only set a value if both likelihood and impact are provided
      if (likelihood > 0 && impact > 0) {
        this.newInstance.RiskExposureRating = likelihood * impact;
      } else {
        this.newInstance.RiskExposureRating = null;
      }
    },
    onAppetiteChange() {
      // When Appetite changes to No, update RiskStatus to Rejected
      if (this.newInstance.Appetite === 'No') {
        this.newInstance.RiskStatus = 'Rejected';
        console.log('Appetite set to No: Updated RiskStatus to Rejected');
      }
    },
    testBackendConnection() {
      this.isDebugging = true;
      this.testResults = [];
      
      const endpoints = [
        'http://127.0.0.1:8000/api/risk-instances/', // Confirmed working endpoint (highest priority)
        'http://localhost:8000/api/risk-instances/',
        'http://localhost:8080/api/risk-instances/',
        'http://localhost:8080/risk-instances/',
        'http://127.0.0.1:8000/risk-instances/',
        'http://localhost:8000/risk-instances/'
      ];
      
      this.testResults.push('Testing API endpoints in order of priority...');
      this.testResults.push(`Primary endpoint: ${endpoints[0]} (confirmed working in browser)`);
      
      const testEndpoint = (index) => {
        if (index >= endpoints.length) {
          // Testing complete
          this.testResults.push('All tests completed.');
          return;
        }
        
        const endpoint = endpoints[index];
        this.testResults.push(`Testing: ${endpoint}`);
        
        fetch(endpoint, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        })
        .then(response => {
          if (!response.ok) {
            return response.text().then(() => {
              this.testResults.push(`❌ ${endpoint} - Status: ${response.status}`);
              // Continue testing the next endpoint
              testEndpoint(index + 1);
            });
          }
          return response.json().then((data) => {
            this.testResults.push(`✅ ${endpoint} - Connected successfully`);
            this.testResults.push(`Found ${data.length || 0} risk instances in the database`);
            testEndpoint(index + 1);
          });
        })
        .catch(error => {
          this.testResults.push(`❌ ${endpoint} - Error: ${error.message}`);
          testEndpoint(index + 1);
        });
      };
      
      // Start testing endpoints
      testEndpoint(0);
    },
    submitInstance() {
      // Mark form as submitted to show all validation errors
      this.formSubmitted = true;
      
      // Validate the entire form
      const { isValid, errors } = validateForm(this.newInstance, riskInstanceFormValidationMap);
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
      
      // Debug logs for troubleshooting
      console.log('newInstance before submit:', this.newInstance);
      
      // Sanitize the form data
      const sanitizedData = sanitizeForm(this.newInstance);
      
      // Create form data object for submission with no field validation
      const formData = {
        ...sanitizedData,
        RiskId: sanitizedData.RiskId || null,
        IncidentId: sanitizedData.IncidentId || null,
        RiskLikelihood: parseFloat(sanitizedData.RiskLikelihood) || null,
        RiskImpact: parseFloat(sanitizedData.RiskImpact) || null,
        RiskExposureRating: sanitizedData.RiskExposureRating ? parseFloat(sanitizedData.RiskExposureRating) : null,
        UserId: parseInt(sanitizedData.UserId) || null,
        ReviewerCount: sanitizedData.ReviewerCount ? parseInt(sanitizedData.ReviewerCount) : null,
        RecurrenceCount: sanitizedData.RecurrenceCount ? parseInt(sanitizedData.RecurrenceCount) : 1
      }

      // Validate MitigationStatus field
      const validMitigationStatuses = ["Yet to Start", "Work In Progress", "Revision Required by Reviewer", "Revision Required by User", "Completed", ""];
      if (!validMitigationStatuses.includes(formData.MitigationStatus)) {
        formData.MitigationStatus = null;
      }
      
      // Handle RiskMitigation field - ensure it's a valid JSON object
      if (formData.RiskMitigation && typeof formData.RiskMitigation === 'string' && formData.RiskMitigation.trim() !== '') {
        // Convert string to JSON object with numbered keys
        const mitigationText = formData.RiskMitigation.trim();
        formData.RiskMitigation = { "1": mitigationText };
      } else if (!formData.RiskMitigation || formData.RiskMitigation === '') {
        formData.RiskMitigation = null;
      }
      
      // Handle ModifiedMitigations field - ensure it's a valid JSON
      if (formData.ModifiedMitigations && typeof formData.ModifiedMitigations === 'string' && formData.ModifiedMitigations.trim() !== '') {
        try {
          // Try to parse if it's a JSON string
          formData.ModifiedMitigations = JSON.parse(formData.ModifiedMitigations);
        } catch (e) {
          // If not valid JSON, create a simple object
          formData.ModifiedMitigations = { "1": formData.ModifiedMitigations };
        }
      } else {
        formData.ModifiedMitigations = null;
      }
      
      // Handle RiskFormDetails field - ensure it's a valid JSON
      if (formData.RiskFormDetails && typeof formData.RiskFormDetails === 'string' && formData.RiskFormDetails.trim() !== '') {
        try {
          // Try to parse if it's a JSON string
          formData.RiskFormDetails = JSON.parse(formData.RiskFormDetails);
        } catch (e) {
          // If not valid JSON, create a simple object
          formData.RiskFormDetails = { "details": formData.RiskFormDetails };
        }
      } else {
        formData.RiskFormDetails = null;
      }

      // Handle date fields - either format them properly or set to null
      if (formData.MitigationDueDate) {
        // Ensure date is in YYYY-MM-DD format
        formData.MitigationDueDate = formData.MitigationDueDate.split('T')[0];
      } else {
        formData.MitigationDueDate = null;
      }
      
      if (formData.MitigationCompletedDate) {
        // Ensure date is in YYYY-MM-DD format
        formData.MitigationCompletedDate = formData.MitigationCompletedDate.split('T')[0];
      } else {
        formData.MitigationCompletedDate = null;
      }
      
      // Set empty strings to null for all fields
      Object.keys(formData).forEach(key => {
        if (formData[key] === '') {
          formData[key] = null;
        }
      });
      
      // Debug log
      console.log('Submitting data:', formData);

      // Use the confirmed working endpoint
      const API_ENDPOINT = 'http://127.0.0.1:8000/api/risk-instances/';
      
      // Show debugging info
      this.isDebugging = true;
      this.testResults = [`Submitting to confirmed API endpoint: ${API_ENDPOINT}`];
      
      fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })
      .then(response => {
        if (!response.ok) {
          return response.text().then((errorText) => {
            this.testResults.push(`❌ API Error: ${response.status} ${response.statusText}`);
            this.testResults.push(`Response: ${errorText}`);
            console.error(`API Error: ${response.status}`, errorText);
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
          });
        }
        return response.json();
      })
      .then(data => {
        console.log('Success response:', data);
        this.testResults.push('✅ Success! Risk instance created successfully');
        
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'form-success-message';
        successMessage.innerText = 'Risk instance created successfully!';
        document.body.appendChild(successMessage);
        
        // Remove success message after animation completes
        setTimeout(() => {
          if (document.body.contains(successMessage)) {
            document.body.removeChild(successMessage);
          }
        }, 3000);
        
        this.resetForm();
      })
      .catch(error => {
        this.testResults.push(`❌ Error: ${error.message}`);
        alert(`Error creating risk instance: ${error.message}`);
      });
    },
    resetForm() {
      this.newInstance = {
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        Appetite: 'Yes',
        RiskDescription: '',
        RiskLikelihood: 1,
        RiskImpact: 1,
        RiskExposureRating: 1,
        RiskPriority: '',
        RiskResponseType: 'Mitigation',
        RiskResponseDescription: '',
        RiskMitigation: '',
        RiskOwner: '',
        RiskStatus: 'Not Assigned',
        UserId: 1,
        RiskId: null,
        IncidentId: null,
        RiskTitle: '',
        BusinessImpact: '',
        Origin: '',
        MitigationDueDate: '',
        MitigationStatus: '',
        MitigationCompletedDate: '',
        ReviewerCount: '',
        RecurrenceCount: 1,
        RiskFormDetails: '',
        ModifiedMitigations: '',
        ComplianceId: '',
        RiskType: 'Current'
      }
      
      // Reset validation state
      this.validationErrors = {};
      this.formSubmitted = false;
      
      // Reset selected text fields
      this.selectedRiskIdText = '';
      this.selectedOwnerText = '';
      this.selectedComplianceIdText = '';
      
      // Calculate initial Risk Exposure Rating
      this.calculateRiskExposureRating();
    },
    // Tooltip/focus methods
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
    fetchUsers() {
      this.loadingUsers = true;
      
      // API endpoint for fetching users for dropdown
      const API_ENDPOINT = 'http://127.0.0.1:8000/api/users-for-dropdown/';
      
      fetch(API_ENDPOINT)
        .then(response => {
          if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          this.users = data;
          this.filteredUsers = [...data];
          this.loadingUsers = false;
        })
        .catch(error => {
          console.error('Error fetching users:', error);
          this.loadingUsers = false;
          this.filteredUsers = [];
        });
    },
    filterUsers() {
      if (!this.userSearchQuery) {
        this.filteredUsers = [...this.users];
        return;
      }
      
      const query = this.userSearchQuery.toLowerCase();
      this.filteredUsers = this.users.filter(user => 
        (user.user_name && user.user_name.toLowerCase().includes(query)) ||
        (user.department && user.department.toLowerCase().includes(query)) ||
        (user.designation && user.designation.toLowerCase().includes(query)) ||
        (user.email && user.email.toLowerCase().includes(query))
      );
    },
    selectUser(user) {
      this.selectedOwnerText = user.user_name;
      this.newInstance.RiskOwner = user.user_name;
      this.showUserDropdown = false;
      
      // Set the UserId field
      if (user.user_id) this.newInstance.UserId = user.user_id;
    },
    toggleUserDropdown() {
      this.showUserDropdown = !this.showUserDropdown;
      if (this.showUserDropdown) {
        this.userSearchQuery = '';
        this.fetchUsers();
      }
    },
    closeUserDropdown(event) {
      // Check if the click was outside the dropdown
      const dropdown = document.querySelector('.user-dropdown-container');
      if (dropdown && !dropdown.contains(event.target)) {
        this.showUserDropdown = false;
      }
    },
    fetchCompliances() {
      this.loadingCompliances = true;
      
      // API endpoint for fetching compliances for dropdown
      const API_ENDPOINT = 'http://127.0.0.1:8000/api/compliances-for-dropdown/';
      
      fetch(API_ENDPOINT)
        .then(response => {
          if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          this.compliances = data;
          this.filteredCompliances = [...data];
          this.loadingCompliances = false;
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
        (compliance.ComplianceItemDescription && compliance.ComplianceItemDescription.toLowerCase().includes(query))
      );
    },
    selectCompliance(compliance) {
      this.selectedComplianceIdText = `Compliance ID: ${compliance.ComplianceId}`;
      this.showComplianceDropdown = false;
      
      // Optionally pre-fill other fields based on the selected compliance
      if (compliance.ComplianceItemDescription) this.newInstance.RiskDescription = compliance.ComplianceItemDescription;
      if (compliance.PossibleDamage) this.newInstance.PossibleDamage = compliance.PossibleDamage;
      if (compliance.ComplianceId) this.newInstance.ComplianceId = compliance.ComplianceId;
    },
    toggleComplianceDropdown() {
      this.showComplianceDropdown = !this.showComplianceDropdown;
      if (this.showComplianceDropdown) {
        this.complianceSearchQuery = '';
        this.fetchCompliances();
      }
    },
    closeComplianceDropdown(event) {
      // Check if the click was outside the dropdown
      const dropdown = document.querySelector('.compliance-dropdown-container');
      if (dropdown && !dropdown.contains(event.target)) {
        this.showComplianceDropdown = false;
      }
    },
    // Add new validation method
    validateField(fieldName) {
      if (!this.formSubmitted) return;
      
      const fieldValue = this.newInstance[fieldName];
      const validationType = riskInstanceFormValidationMap[fieldName];
      
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

