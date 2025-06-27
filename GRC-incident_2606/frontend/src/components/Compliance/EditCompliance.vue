<template>
  <div class="create-compliance-container">
    <!-- Header section -->
    <div class="compliance-header">
      <h2><i class="fas fa-edit"></i> Edit Compliance Record</h2>
      <p>Update compliance item details - This will create a new version</p>
    </div>

    <!-- Message display -->
    <div v-if="error" class="message error-message">
      {{ error }}
    </div>
    <div v-if="successMessage" class="message success-message">
      {{ successMessage }}
    </div>

    <!-- Loading indicator -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <div class="loading-text">Loading data...</div>
    </div>

    <!-- Edit form -->
    <div v-if="compliance" class="compliance-item-form">
      <!-- Basic compliance information -->
      <div class="field-group">
        <div class="field-group-title"><i class="fas fa-info-circle"></i> Basic Information</div>
        
        <!-- Identifier and IsRisk in one row at the top -->
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-barcode"></i> Identifier</label>
            <input 
              v-model="compliance.Identifier" 
              class="compliance-input" 
              placeholder="Auto-generated if left empty"
              title="Unique identifier for this compliance item"
              disabled
            />
            <small>Current identifier (new one will be generated for new version)</small>
          </div>

          <div class="compliance-field checkbox-container">
            <label style="font-weight: 500; font-size: 1rem; display: flex; align-items: center; gap: 8px;" title="Check if this compliance item represents a risk">
              <i class="fas fa-exclamation-triangle" style="color: #ff6b35;"></i>
              <input type="checkbox" v-model="compliance.IsRisk" style="margin-right: 8px; width: auto;" />
              Is Risk
            </label>
          </div>
        </div>
        
        <!-- Compliance Title and Type in one row -->
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-heading"></i> Compliance Title <span class="required-asterisk">*</span></label>
            <input 
              v-model="compliance.ComplianceTitle" 
              class="compliance-input" 
              :class="{ 'error-input': validationErrors.ComplianceTitle }"
              placeholder="Enter compliance title"
              required 
              title="Enter the title of the compliance item"
              @blur="validateField('ComplianceTitle')"
            />
            <span v-if="validationErrors.ComplianceTitle" class="validation-error-message">
              {{ validationErrors.ComplianceTitle }}
            </span>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-tag"></i> Compliance Type <span class="required-asterisk">*</span></label>
            <input 
              v-model="compliance.ComplianceType" 
              class="compliance-input" 
              :class="{ 'error-input': validationErrors.ComplianceType }"
              placeholder="Enter compliance type"
              title="Type of compliance (e.g. Regulatory, Internal, Security)"
              @blur="validateField('ComplianceType')"
            />
            <span v-if="validationErrors.ComplianceType" class="validation-error-message">
              {{ validationErrors.ComplianceType }}
            </span>
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-align-left"></i> Compliance Description <span class="required-asterisk">*</span></label>
          <textarea
            v-model="compliance.ComplianceItemDescription" 
            class="compliance-input" 
            :class="{ 'error-input': validationErrors.ComplianceItemDescription }"
            placeholder="Compliance Description"
            required 
            rows="3"
            title="Detailed description of the compliance requirement"
            @blur="validateField('ComplianceItemDescription')"
          ></textarea>
          <span v-if="validationErrors.ComplianceItemDescription" class="validation-error-message">
            {{ validationErrors.ComplianceItemDescription }}
          </span>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-crosshairs"></i> Scope <span class="required-asterisk">*</span></label>
          <textarea 
            v-model="compliance.Scope" 
            class="compliance-input" 
            :class="{ 'error-input': validationErrors.Scope }"
            placeholder="Enter scope information"
            rows="3"
            title="Define the boundaries and extent of the compliance requirement"
            @blur="validateField('Scope')"
          ></textarea>
          <span v-if="validationErrors.Scope" class="validation-error-message">
            {{ validationErrors.Scope }}
          </span>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-bullseye"></i> Objective <span class="required-asterisk">*</span></label>
          <textarea 
            v-model="compliance.Objective" 
            class="compliance-input" 
            :class="{ 'error-input': validationErrors.Objective }"
            placeholder="Enter objective information"
            rows="3"
            title="The goal or purpose of this compliance requirement"
            @blur="validateField('Objective')"
          ></textarea>
          <span v-if="validationErrors.Objective" class="validation-error-message">
            {{ validationErrors.Objective }}
          </span>
        </div>
        
        <!-- Business Units -->
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-building"></i> Business Units Covered <span class="required-asterisk">*</span></label>
            <div class="dropdown-container">
            <input 
              v-model="compliance.BusinessUnitsCovered" 
                @input="onSearchCategory($event, 'BusinessUnitsCovered')"
                @focus="onFocusCategory('BusinessUnitsCovered')"
                @blur="onBlurCategoryAndValidate('BusinessUnitsCovered')"
                class="compliance-input dropdown-input" 
                :class="{ 'error-input': validationErrors.BusinessUnitsCovered }"
                placeholder="Type to search or add business units..."
              title="Departments or business units affected by this compliance"
            />
              <div v-if="showDropdown.BusinessUnitsCovered" 
                   class="dropdown-menu">
                <div v-if="filteredCategories.BusinessUnitsCovered.length === 0" 
                     class="dropdown-item no-results">
                  No results found
                </div>
                <div v-else>
                  <div v-for="item in filteredCategories.BusinessUnitsCovered" 
                       :key="item" 
                       class="dropdown-item"
                       @mousedown="selectCategory(item, 'BusinessUnitsCovered')">
                    {{ item }}
                  </div>
                </div>
                <div v-if="compliance.BusinessUnitsCovered && compliance.BusinessUnitsCovered.trim() && !categoryExists('BusinessUnitsCovered', compliance.BusinessUnitsCovered)" 
                     class="dropdown-item add-new"
                     @mousedown="addNewCategory('BusinessUnitsCovered', compliance.BusinessUnitsCovered)">
                  <i class="fas fa-plus"></i> Add "{{ compliance.BusinessUnitsCovered }}"
                </div>
              </div>
            </div>
            <span v-if="validationErrors.BusinessUnitsCovered" class="validation-error-message">
              {{ validationErrors.BusinessUnitsCovered }}
            </span>
          </div>
        </div>
      </div>

      <!-- Risk related fields - grouped together -->
      <div class="field-group risk-fields">
        <div class="field-group-title">
          <i class="fas fa-shield-alt"></i> Risk Information
          <span v-if="!compliance.IsRisk" class="optional-indicator">(Optional - Only required if marked as Risk)</span>
        </div>
        <div class="compliance-field full-width">
          <label><i class="fas fa-bomb"></i> Possible Damage <span v-if="compliance.IsRisk" class="required-asterisk">*</span></label>
          <textarea
            v-model="compliance.PossibleDamage" 
            class="compliance-input" 
            :class="{ 'error-input': validationErrors.PossibleDamage }"
            placeholder="Possible Damage"
            rows="3"
            :required="compliance.IsRisk"
            title="Potential damage that could occur if this risk materializes" 
            @blur="validateField('PossibleDamage')"
          ></textarea>
          <span v-if="validationErrors.PossibleDamage" class="validation-error-message">
            {{ validationErrors.PossibleDamage }}
          </span>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-first-aid"></i> Mitigation <span v-if="compliance.IsRisk" class="required-asterisk">*</span></label>
          <textarea
            v-model="compliance.mitigation" 
            class="compliance-input" 
            :class="{ 'error-input': validationErrors.mitigation }"
            placeholder="Mitigation"
            rows="3"
            title="Actions taken to reduce the risk or its impact" 
            @blur="validateField('mitigation')"
          ></textarea>
          <span v-if="validationErrors.mitigation" class="validation-error-message">
            {{ validationErrors.mitigation }}
          </span>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-chess"></i> Potential Risk Scenarios <span v-if="compliance.IsRisk" class="required-asterisk">*</span></label>
          <textarea 
            v-model="compliance.PotentialRiskScenarios" 
            class="compliance-input" 
            :class="{ 'error-input': validationErrors.PotentialRiskScenarios }"
            placeholder="Describe potential risk scenarios"
            rows="3"
            title="Describe scenarios where this risk could materialize"
            @blur="validateField('PotentialRiskScenarios')"
          ></textarea>
          <span v-if="validationErrors.PotentialRiskScenarios" class="validation-error-message">
            {{ validationErrors.PotentialRiskScenarios }}
          </span>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-exclamation-circle"></i> Risk Type</label>
            <div class="dropdown-container">
              <input 
              v-model="compliance.RiskType" 
                @input="onSearchCategory($event, 'RiskType')"
                @focus="onFocusCategory('RiskType')"
                @blur="onBlurCategory('RiskType')"
                class="compliance-input dropdown-input" 
                placeholder="Type to search or add risk type..."
              title="Type of risk (e.g. Operational, Financial, Strategic, Compliance, Reputational)"
              />
              <div v-if="showDropdown.RiskType" 
                   class="dropdown-menu">
                <div v-if="filteredCategories.RiskType.length === 0" 
                     class="dropdown-item no-results">
                  No results found
                </div>
                <div v-else>
                  <div v-for="item in filteredCategories.RiskType" 
                       :key="item" 
                       class="dropdown-item"
                       @mousedown="selectCategory(item, 'RiskType')">
                    {{ item }}
                  </div>
                </div>
                <div v-if="compliance.RiskType && compliance.RiskType.trim() && !categoryExists('RiskType', compliance.RiskType)" 
                     class="dropdown-item add-new"
                     @mousedown="addNewCategory('RiskType', compliance.RiskType)">
                  <i class="fas fa-plus"></i> Add "{{ compliance.RiskType }}"
                </div>
              </div>
            </div>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-list-alt"></i> Risk Category</label>
            <div class="dropdown-container">
              <input 
              v-model="compliance.RiskCategory" 
                @input="onSearchCategory($event, 'RiskCategory')"
                @focus="onFocusCategory('RiskCategory')"
                @blur="onBlurCategory('RiskCategory')"
                class="compliance-input dropdown-input" 
                placeholder="Type to search or add risk category..."
              title="Category of risk (e.g. People, Process, Technology, External)"
              />
              <div v-if="showDropdown.RiskCategory" 
                   class="dropdown-menu">
                <div v-if="filteredCategories.RiskCategory.length === 0" 
                     class="dropdown-item no-results">
                  No results found
                </div>
                <div v-else>
                  <div v-for="item in filteredCategories.RiskCategory" 
                       :key="item" 
                       class="dropdown-item"
                       @mousedown="selectCategory(item, 'RiskCategory')">
                    {{ item }}
                  </div>
                </div>
                <div v-if="compliance.RiskCategory && compliance.RiskCategory.trim() && !categoryExists('RiskCategory', compliance.RiskCategory)" 
                     class="dropdown-item add-new"
                     @mousedown="addNewCategory('RiskCategory', compliance.RiskCategory)">
                  <i class="fas fa-plus"></i> Add "{{ compliance.RiskCategory }}"
                </div>
              </div>
            </div>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-chart-line"></i> Risk Business Impact</label>
            <div class="dropdown-container">
              <input 
              v-model="compliance.RiskBusinessImpact" 
                @input="onSearchCategory($event, 'RiskBusinessImpact')"
                @focus="onFocusCategory('RiskBusinessImpact')"
                @blur="onBlurCategory('RiskBusinessImpact')"
                class="compliance-input dropdown-input" 
                placeholder="Type to search or add business impact..."
              title="How this risk impacts business operations"
              />
              <div v-if="showDropdown.RiskBusinessImpact" 
                   class="dropdown-menu">
                <div v-if="filteredCategories.RiskBusinessImpact.length === 0" 
                     class="dropdown-item no-results">
                  No results found
                </div>
                <div v-else>
                  <div v-for="item in filteredCategories.RiskBusinessImpact" 
                       :key="item" 
                       class="dropdown-item"
                       @mousedown="selectCategory(item, 'RiskBusinessImpact')">
                    {{ item }}
                  </div>
                </div>
                <div v-if="compliance.RiskBusinessImpact && compliance.RiskBusinessImpact.trim() && !categoryExists('RiskBusinessImpact', compliance.RiskBusinessImpact)" 
                     class="dropdown-item add-new"
                     @mousedown="addNewCategory('RiskBusinessImpact', compliance.RiskBusinessImpact)">
                  <i class="fas fa-plus"></i> Add "{{ compliance.RiskBusinessImpact }}"
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Compliance classification fields - grouped together -->
      <div class="field-group classification-fields">
        <div class="field-group-title"><i class="fas fa-tasks"></i> Classification</div>
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-exclamation"></i> Criticality <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.Criticality" 
              class="compliance-select" 
              :class="{ 'error-input': validationErrors.Criticality }"
              required
              title="How critical this compliance item is to the organization"
              @blur="validateField('Criticality')"
            >
              <option value="">Select Criticality</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <span v-if="validationErrors.Criticality" class="validation-error-message">
              {{ validationErrors.Criticality }}
            </span>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-gavel"></i> Mandatory/Optional <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.MandatoryOptional" 
              class="compliance-select" 
              :class="{ 'error-input': validationErrors.MandatoryOptional }"
              required
              title="Whether this compliance item is mandatory or optional"
              @blur="validateField('MandatoryOptional')"
            >
              <option value="">Select Option</option>
              <option value="Mandatory">Mandatory</option>
              <option value="Optional">Optional</option>
            </select>
            <span v-if="validationErrors.MandatoryOptional" class="validation-error-message">
              {{ validationErrors.MandatoryOptional }}
            </span>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-cogs"></i> Manual/Automatic <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.ManualAutomatic" 
              class="compliance-select" 
              :class="{ 'error-input': validationErrors.ManualAutomatic }"
              required
              title="Whether this compliance is checked manually or automatically"
              @blur="validateField('ManualAutomatic')"
            >
              <option value="">Select Type</option>
              <option value="Manual">Manual</option>
              <option value="Automatic">Automatic</option>
            </select>
            <span v-if="validationErrors.ManualAutomatic" class="validation-error-message">
              {{ validationErrors.ManualAutomatic }}
            </span>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-check-circle"></i> Applicability</label>
            <input 
              v-model="compliance.Applicability" 
              class="compliance-input" 
              placeholder="Applicability from policy"
              title="Describes where this compliance item applies"
            />
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-thermometer-half"></i> Severity Rating (1-10) <span class="required-asterisk">*</span></label>
            <input 
              type="number" 
              v-model.number="compliance.Impact" 
              @input="validateImpact"
              @blur="validateField('Impact')"
              class="compliance-input" 
              :class="{ 'error-input': validationErrors.Impact }"
              step="0.1" 
              min="1" 
              max="10"
              required
              title="Rate the Severity Rating from 1 (lowest) to 10 (highest)"
            />
            <span v-if="validationErrors.Impact" class="validation-error-message">
              {{ validationErrors.Impact }}
            </span>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-percentage"></i> Probability (1-10) <span class="required-asterisk">*</span></label>
            <input 
              type="number" 
              v-model.number="compliance.Probability" 
              @input="validateProbability"
              @blur="validateField('Probability')"
              class="compliance-input" 
              :class="{ 'error-input': validationErrors.Probability }"
              step="0.1" 
              min="1" 
              max="10"
              required
              title="Rate the probability from 1 (lowest) to 10 (highest)"
            />
            <span v-if="validationErrors.Probability" class="validation-error-message">
              {{ validationErrors.Probability }}
            </span>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-chart-bar"></i> Maturity Level <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.MaturityLevel" 
              class="compliance-select"
              :class="{ 'error-input': validationErrors.MaturityLevel }"
              title="Current maturity level of this compliance item"
              @blur="validateField('MaturityLevel')"
            >
              <option value="">Select Maturity Level</option>
              <option value="Initial">Initial</option>
              <option value="Developing">Developing</option>
              <option value="Defined">Defined</option>
              <option value="Managed">Managed</option>
              <option value="Optimizing">Optimizing</option>
            </select>
            <span v-if="validationErrors.MaturityLevel" class="validation-error-message">
              {{ validationErrors.MaturityLevel }}
            </span>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-clock"></i> Permanent/Temporary <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.PermanentTemporary" 
              class="compliance-select"
              :class="{ 'error-input': validationErrors.PermanentTemporary }"
              title="Whether this compliance requirement is permanent or temporary"
              @blur="validateField('PermanentTemporary')"
            >
              <option value="">Select Duration</option>
              <option value="Permanent">Permanent</option>
              <option value="Temporary">Temporary</option>
            </select>
            <span v-if="validationErrors.PermanentTemporary" class="validation-error-message">
              {{ validationErrors.PermanentTemporary }}
            </span>
          </div>
        </div>
      </div>

      <!-- Current Status fields - read-only display -->
      <div class="field-group">
        <div class="field-group-title"><i class="fas fa-info"></i> Current Status Information</div>
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-flag"></i> Current Status</label>
            <input 
              :value="compliance.Status" 
              class="compliance-input" 
              readonly
              title="Current status of the compliance item"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-toggle-on"></i> Active/Inactive</label>
            <input 
              :value="compliance.ActiveInactive" 
              class="compliance-input" 
              readonly
              title="Current active status"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-user"></i> Created By</label>
            <input 
              :value="compliance.CreatedByName || 'System'" 
              class="compliance-input" 
              readonly
              title="Person who created this compliance item"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-calendar"></i> Created Date</label>
            <input 
              :value="compliance.CreatedByDate || 'Not specified'" 
              class="compliance-input" 
              readonly
              title="Date when this compliance item was created"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
        </div>
      </div>
      
      <!-- Approval section -->
      <div class="field-group approval-fields">
        <div class="field-group-title"><i class="fas fa-check-square"></i> Approval Information</div>
        <!-- Approver and Approval Due Date in the same row -->
        <div class="row-fields">
          <!-- Assign Reviewer -->
          <div class="compliance-field">
            <label><i class="fas fa-user-check"></i> Assign Reviewer <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.reviewer_id" 
              class="compliance-select" 
              :class="{ 'error-input': validationErrors.reviewer_id }"
              required
              title="Person responsible for reviewing this compliance item"
              @blur="validateField('reviewer_id')"
            >
              <option value="" disabled>Select Reviewer</option>
              <option v-for="user in users" :key="user.UserId" :value="user.UserId">
                {{ user.UserName }} {{ user.email ? `(${user.email})` : '' }}
              </option>
            </select>
            <span v-if="validationErrors.reviewer_id" class="validation-error-message">
              {{ validationErrors.reviewer_id }}
            </span>
            <span v-else-if="!users.length" class="validation-error-message">No reviewers available</span>
          </div>
          <!-- Approval Due Date -->
          <div class="compliance-field">
            <label><i class="fas fa-calendar-check"></i> Approval Due Date <span class="required-asterisk">*</span></label>
            <input 
              type="date" 
              v-model="compliance.ApprovalDueDate" 
              class="compliance-input" 
              :class="{ 'error-input': validationErrors.ApprovalDueDate }"
              required
              :min="minDate"
              title="Deadline for reviewing this compliance item" 
              @blur="validateField('ApprovalDueDate')"
            />
            <span v-if="validationErrors.ApprovalDueDate" class="validation-error-message">
              {{ validationErrors.ApprovalDueDate }}
            </span>
          </div>
        </div>
        
        <!-- Versioning Type Row -->
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-code-branch"></i> Versioning Type <span class="required-asterisk">*</span></label>
            <select 
              v-model="compliance.VersioningType" 
              class="compliance-select" 
              :class="{ 'error-input': validationErrors.VersioningType }"
              required
              title="Select whether this is a minor or major version change"
              @blur="validateField('VersioningType')"
            >
              <option value="">Select Version Type</option>
              <option value="Minor">Minor (e.g., 2.3 → 2.4)</option>
              <option value="Major">Major (e.g., 2.3 → 3.0)</option>
            </select>
            <span v-if="validationErrors.VersioningType" class="validation-error-message">
              {{ validationErrors.VersioningType }}
            </span>
          </div>
          <div class="compliance-field">
            <label><i class="fas fa-code-branch"></i> Current Version</label>
            <input 
              :value="compliance.ComplianceVersion || '1.0'" 
              class="compliance-input" 
              readonly
              title="Current version of the compliance item"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
            <small>New version will be calculated automatically</small>
          </div>
        </div>
      </div>
    </div>
    
    <div class="compliance-submit-container">
      <button 
        class="compliance-submit-btn" 
        @click="submitEdit"
        :disabled="loading"
      >
        <span v-if="loading">Saving...</span>
        <span v-else><i class="fas fa-save"></i> Save as New Version</span>
      </button>
      <button 
        class="compliance-cancel-btn" 
        @click="cancelEdit"
        :disabled="loading"
      >
        <i class="fas fa-times"></i> Cancel
      </button>
    </div>
  </div>
</template>

<script>
import { complianceService } from '@/services/api';
import { PopupService } from '@/modules/popup';

export default {
  name: 'EditCompliance',
  data() {
    return {
      compliance: null,
      users: [],
      loading: false,
      error: null,
      successMessage: null,
      impactError: false,
      probabilityError: false,
      originalComplianceId: null,
      // Validation errors
      validationErrors: {},
      // Category dropdown data
      categories: {
        BusinessUnitsCovered: [],
        RiskType: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      searchTerms: {
        BusinessUnitsCovered: '',
        RiskType: '',
        RiskCategory: '',
        RiskBusinessImpact: ''
      },
      showDropdown: {
        BusinessUnitsCovered: false,
        RiskType: false,
        RiskCategory: false,
        RiskBusinessImpact: false
      }
    }
  },
  computed: {
    minDate() {
      // Get today's date in YYYY-MM-DD format for setting minimum date
      const today = new Date();
      return today.toISOString().split('T')[0];
    },
    filteredCategories() {
      const filtered = {};
      Object.keys(this.categories).forEach(key => {
        const searchTerm = this.searchTerms[key].toLowerCase();
        filtered[key] = this.categories[key].filter(item => 
          item.toLowerCase().includes(searchTerm)
        );
      });
      return filtered;
    }
  },
  async created() {
    // Get the compliance ID from the route params
    const complianceId = this.$route.params.id;
    if (!complianceId) {
      this.error = 'No compliance ID provided';
      return;
    }
    
    this.originalComplianceId = complianceId;
    await this.loadUsers();
    await this.loadAllCategories();
    await this.loadComplianceData(complianceId);
  },
  methods: {
    // Comprehensive validation functions
    validateTextInput(value) {
      const TEXT_PATTERN = /^[a-zA-Z0-9\s.,!?()[\]:;'"&%$#@+=\n\r\t_-]+$/;
      return TEXT_PATTERN.test(value);
    },
    
    validateAlphanumericInput(value) {
      const ALPHANUMERIC_PATTERN = /^[a-zA-Z0-9\s._-]+$/;
      return ALPHANUMERIC_PATTERN.test(value);
    },

    // Individual field validation
    validateField(fieldName) {
      this.validationErrors = { ...this.validationErrors };
      delete this.validationErrors[fieldName];

      const value = this.compliance[fieldName];

      switch (fieldName) {
        case 'ComplianceTitle':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Compliance Title is required';
          } else if (value.length > 500) {
            this.validationErrors[fieldName] = 'Compliance Title must be less than 500 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Compliance Title contains invalid characters';
          }
          break;

        case 'ComplianceType':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Compliance Type is required';
          } else if (value.length > 255) {
            this.validationErrors[fieldName] = 'Compliance Type must be less than 255 characters';
          } else if (!this.validateAlphanumericInput(value)) {
            this.validationErrors[fieldName] = 'Compliance Type contains invalid characters';
          }
          break;

        case 'ComplianceItemDescription':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Compliance Description is required';
          } else if (value.length > 2000) {
            this.validationErrors[fieldName] = 'Compliance Description must be less than 2000 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Compliance Description contains invalid characters';
          }
          break;

        case 'Scope':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Scope is required';
          } else if (value.length > 1000) {
            this.validationErrors[fieldName] = 'Scope must be less than 1000 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Scope contains invalid characters';
          }
          break;

        case 'Objective':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Objective is required';
          } else if (value.length > 1000) {
            this.validationErrors[fieldName] = 'Objective must be less than 1000 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Objective contains invalid characters';
          }
          break;

        case 'BusinessUnitsCovered':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Business Units Covered is required';
          } else if (value.length > 500) {
            this.validationErrors[fieldName] = 'Business Units Covered must be less than 500 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Business Units Covered contains invalid characters';
          }
          break;

        case 'Impact':
          if (value === null || value === undefined || value === '') {
            this.validationErrors[fieldName] = 'Severity Rating is required';
          } else if (isNaN(value) || value < 1 || value > 10) {
            this.validationErrors[fieldName] = 'Severity Rating must be between 1 and 10';
          }
          break;

        case 'Probability':
          if (value === null || value === undefined || value === '') {
            this.validationErrors[fieldName] = 'Probability is required';
          } else if (isNaN(value) || value < 1 || value > 10) {
            this.validationErrors[fieldName] = 'Probability must be between 1 and 10';
          }
          break;

        case 'ApprovalDueDate':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Approval Due Date is required';
          } else {
            const selectedDate = new Date(value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (selectedDate < today) {
              this.validationErrors[fieldName] = 'Approval Due Date cannot be in the past';
            }
          }
          break;

        case 'reviewer_id':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Reviewer is required';
          }
          break;

        case 'Criticality':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Criticality is required';
          } else if (!['High', 'Medium', 'Low'].includes(value)) {
            this.validationErrors[fieldName] = 'Please select a valid criticality level';
          }
          break;

        case 'MandatoryOptional':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Mandatory/Optional selection is required';
          } else if (!['Mandatory', 'Optional'].includes(value)) {
            this.validationErrors[fieldName] = 'Please select a valid option';
          }
          break;

        case 'ManualAutomatic':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Manual/Automatic selection is required';
          } else if (!['Manual', 'Automatic'].includes(value)) {
            this.validationErrors[fieldName] = 'Please select a valid option';
          }
          break;

        case 'MaturityLevel':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Maturity Level is required';
          } else if (!['Initial', 'Developing', 'Defined', 'Managed', 'Optimizing'].includes(value)) {
            this.validationErrors[fieldName] = 'Please select a valid maturity level';
          }
          break;

        case 'PermanentTemporary':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Permanent/Temporary selection is required';
          } else if (!['Permanent', 'Temporary'].includes(value)) {
            this.validationErrors[fieldName] = 'Please select a valid option';
          }
          break;

        case 'VersioningType':
          if (!value || value === '') {
            this.validationErrors[fieldName] = 'Versioning Type is required';
          } else if (!['Minor', 'Major'].includes(value)) {
            this.validationErrors[fieldName] = 'Please select a valid versioning type';
          }
          break;

        // Risk-specific validations
        case 'PossibleDamage':
          if (this.compliance.IsRisk && (!value || value.trim() === '')) {
            this.validationErrors[fieldName] = 'Possible Damage is required for risk items';
          } else if (value && value.length > 2000) {
            this.validationErrors[fieldName] = 'Possible Damage must be less than 2000 characters';
          } else if (value && !this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Possible Damage contains invalid characters';
          }
          break;

        case 'mitigation':
          if (this.compliance.IsRisk && (!value || value.trim() === '')) {
            this.validationErrors[fieldName] = 'Mitigation is required for risk items';
          } else if (value && value.length > 2000) {
            this.validationErrors[fieldName] = 'Mitigation must be less than 2000 characters';
          } else if (value && !this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Mitigation contains invalid characters';
          }
          break;

        case 'PotentialRiskScenarios':
          if (this.compliance.IsRisk && (!value || value.trim() === '')) {
            this.validationErrors[fieldName] = 'Potential Risk Scenarios is required for risk items';
          } else if (value && value.length > 2000) {
            this.validationErrors[fieldName] = 'Potential Risk Scenarios must be less than 2000 characters';
          } else if (value && !this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Potential Risk Scenarios contains invalid characters';
          }
          break;

        case 'RiskType':
          if (this.compliance.IsRisk && (!value || value.trim() === '')) {
            this.validationErrors[fieldName] = 'Risk Type is required for risk items';
          } else if (value && value.length > 255) {
            this.validationErrors[fieldName] = 'Risk Type must be less than 255 characters';
          } else if (value && !this.validateAlphanumericInput(value)) {
            this.validationErrors[fieldName] = 'Risk Type contains invalid characters';
          }
          break;

        case 'RiskCategory':
          if (this.compliance.IsRisk && (!value || value.trim() === '')) {
            this.validationErrors[fieldName] = 'Risk Category is required for risk items';
          } else if (value && value.length > 255) {
            this.validationErrors[fieldName] = 'Risk Category must be less than 255 characters';
          } else if (value && !this.validateAlphanumericInput(value)) {
            this.validationErrors[fieldName] = 'Risk Category contains invalid characters';
          }
          break;

        case 'RiskBusinessImpact':
          if (this.compliance.IsRisk && (!value || value.trim() === '')) {
            this.validationErrors[fieldName] = 'Risk Business Impact is required for risk items';
          } else if (value && value.length > 255) {
            this.validationErrors[fieldName] = 'Risk Business Impact must be less than 255 characters';
          } else if (value && !this.validateAlphanumericInput(value)) {
            this.validationErrors[fieldName] = 'Risk Business Impact contains invalid characters';
          }
          break;
      }

      // Force reactivity update
      this.$forceUpdate();
    },

    // Validate all fields
    validateAllFields() {
      const requiredFields = [
        'ComplianceTitle', 'ComplianceType', 'ComplianceItemDescription', 
        'Scope', 'Objective', 'BusinessUnitsCovered', 'Impact', 'Probability',
        'ApprovalDueDate', 'reviewer_id', 'Criticality', 'MandatoryOptional',
        'ManualAutomatic', 'MaturityLevel', 'PermanentTemporary', 'VersioningType'
      ];

      // Add risk-specific required fields if IsRisk is true
      if (this.compliance.IsRisk) {
        requiredFields.push(
          'PossibleDamage', 'mitigation', 'PotentialRiskScenarios',
          'RiskType', 'RiskCategory', 'RiskBusinessImpact'
        );
      }

      this.validationErrors = {};

      // Validate each required field
      requiredFields.forEach(field => {
        this.validateField(field);
      });

      // Return true if no validation errors
      return Object.keys(this.validationErrors).length === 0;
    },
    async loadComplianceData(complianceId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceById(complianceId);
        
        if (response.data && response.data.success) {
          this.compliance = response.data.data;
          
          // Parse mitigation for proper display in editing
          if (this.compliance.mitigation) {
            this.compliance.mitigation = this.parseMitigationForEdit(this.compliance.mitigation);
          }
          
          // Ensure ApprovalDueDate is in the right format
          if (this.compliance.ApprovalDueDate) {
            // Convert to YYYY-MM-DD format if needed
            if (typeof this.compliance.ApprovalDueDate === 'string' && this.compliance.ApprovalDueDate.includes('T')) {
              this.compliance.ApprovalDueDate = this.compliance.ApprovalDueDate.split('T')[0];
            }
          } else {
            // Set default due date if not present
            this.compliance.ApprovalDueDate = this.getDefaultDueDate();
          }
          
          // Set default reviewer if not present
          if (!this.compliance.reviewer_id && this.users.length > 0) {
            this.compliance.reviewer_id = this.users[0].UserId;
          }
          
          // Set default versioning type if not present
          if (!this.compliance.VersioningType) {
            this.compliance.VersioningType = 'Major';
          }

          // Set default values for fields that might be missing
          if (!this.compliance.MaturityLevel) {
            this.compliance.MaturityLevel = 'Initial';
          }
          
          if (!this.compliance.PermanentTemporary) {
            this.compliance.PermanentTemporary = 'Permanent';
          }
        } else {
          PopupService.error('Failed to load compliance data', 'Loading Error');
        }
      } catch (error) {
        console.error('Error loading compliance data:', error);
        PopupService.error('Failed to load compliance data. Please try again.', 'Loading Error');
      } finally {
        this.loading = false;
      }
    },
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users;
        } else {
          console.error('Invalid users data received:', response.data);
          PopupService.error('Failed to load approvers', 'Loading Error');
        }
      } catch (error) {
        console.error('Failed to load users:', error);
        PopupService.error('Failed to load approvers. Please try again.', 'Loading Error');
      } finally {
        this.loading = false;
      }
    },
    validateImpact(event) {
      const value = parseFloat(event.target.value);
      this.impactError = value < 1 || value > 10;
    },
    validateProbability(event) {
      const value = parseFloat(event.target.value);
      this.probabilityError = value < 1 || value > 10;
    },
    getDefaultDueDate() {
      const date = new Date();
      date.setDate(date.getDate() + 7);
      return date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
    },
    async submitEdit() {
      // Reset messages
      this.error = null;
      this.successMessage = null;

      // Validate all fields using the new comprehensive validation
      if (!this.validateAllFields()) {
        PopupService.warning('Please correct the errors in the form before submitting', 'Validation Error');
        return;
      }

      // Show confirmation popup before submitting
      PopupService.confirm(
        `Are you sure you want to update this compliance item? This will create a new ${this.compliance.VersioningType.toLowerCase()} version that requires approval.`,
        'Confirm Update',
        async () => {
          try {
            this.loading = true;
            
            // Always set new versions to Under Review and Inactive
            // The backend will calculate the new version based on VersioningType
            console.log('=== FRONTEND VERSION DEBUG ===');
            console.log('Current compliance version:', this.compliance.ComplianceVersion);
            console.log('Selected versioning type:', this.compliance.VersioningType);
            
            const editData = {
              ...this.compliance,
              Status: 'Under Review',
              ActiveInactive: 'Inactive',
              PreviousComplianceVersionId: this.originalComplianceId,
              VersioningType: this.compliance.VersioningType
            };
            
            // Remove ComplianceVersion from the data so backend calculates it
            delete editData.ComplianceVersion;
            
            console.log('Edit data being sent:', editData);
            console.log('=== END FRONTEND DEBUG ===');
            
            // Use the complianceService to save the edit
            const response = await complianceService.editCompliance(this.originalComplianceId, editData);
            
            if (response.data && response.data.success) {
              const newVersion = response.data.new_version || 'updated';
              PopupService.success(
                `Compliance updated successfully! New version ${newVersion} has been created and sent for approval.`,
                'Update Successful'
              );
              
              // Navigate back to the tailoring page after a short delay
              setTimeout(() => {
                this.$router.push('/compliance/tailoring');
              }, 2000);
            } else {
              const errorMessage = response.data.message || 'Failed to update compliance';
              PopupService.error(errorMessage, 'Update Failed');
            }
          } catch (error) {
            console.error('Error updating compliance:', error);
            const errorMessage = error.response?.data?.message || error.message || 'Failed to update compliance. Please try again.';
            PopupService.error(errorMessage, 'Update Error');
          } finally {
            this.loading = false;
          }
        },
        () => {
          PopupService.success('Update cancelled', 'Cancelled');
        }
      );
    },
    cancelEdit() {
      PopupService.confirm(
        'Are you sure you want to cancel editing? Any unsaved changes will be lost.',
        'Confirm Cancel',
        () => {
          // Navigate back to the tailoring page
          this.$router.push('/compliance/tailoring');
        },
        () => {
          PopupService.success('Continue editing', 'Cancelled');
        }
      );
    },

    // Category management methods
    async loadAllCategories() {
      console.log('Loading all categories...');
      
      // Initialize default categories first
      try {
        console.log('Initializing default categories...');
        const initResponse = await fetch('/api/categories/initialize/');
        const initData = await initResponse.json();
        console.log('Initialize response:', initData);
      } catch (error) {
        console.error('Error initializing categories:', error);
      }
      
      const sources = ['BusinessUnitsCovered', 'RiskType', 'RiskCategory', 'RiskBusinessImpact'];
      for (const source of sources) {
        await this.loadCategoryValues(source);
      }
      
      console.log('All categories loaded:', this.categories);
    },

    async loadCategoryValues(source) {
      try {
        console.log(`Loading ${source} categories...`);
        const response = await fetch(`/api/categories/${source}/`);
        
        if (!response.ok) {
          console.error(`HTTP ${response.status} error for ${source}`);
          this.categories[source] = this.getDefaultCategoryValues(source);
          return;
        }
        
        const data = await response.json();
        console.log(`${source} response:`, data);
        
        if (data.success) {
          this.categories[source] = data.data || [];
          // If no data returned, use default values
          if (this.categories[source].length === 0) {
            console.log(`No data found for ${source}, using defaults`);
            this.categories[source] = this.getDefaultCategoryValues(source);
          }
          console.log(`${source} loaded:`, this.categories[source]);
        } else {
          console.error(`Failed to load ${source} categories:`, data.message);
          // Use default values if API fails
          this.categories[source] = this.getDefaultCategoryValues(source);
        }
      } catch (error) {
        console.error(`Error loading ${source} categories:`, error);
        // Use default values if network error
        this.categories[source] = this.getDefaultCategoryValues(source);
      }
    },

    getDefaultCategoryValues(source) {
      const defaults = {
        'BusinessUnitsCovered': [
          'Sales & Marketing',
          'Finance & Accounting',
          'Human Resources',
          'Information Technology',
          'Operations',
          'Legal & Compliance',
          'Customer Service',
          'Research & Development',
          'Procurement',
          'Risk Management'
        ],
        'RiskType': [
          'Operational Risk',
          'Financial Risk',
          'Strategic Risk',
          'Compliance Risk',
          'Reputational Risk',
          'Technology Risk',
          'Market Risk',
          'Credit Risk',
          'Legal Risk',
          'Environmental Risk'
        ],
        'RiskCategory': [
          'People Risk',
          'Process Risk',
          'Technology Risk',
          'External Risk',
          'Information Risk',
          'Physical Risk',
          'Systems Risk',
          'Vendor Risk',
          'Regulatory Risk',
          'Fraud Risk'
        ],
        'RiskBusinessImpact': [
          'Revenue Loss',
          'Customer Impact',
          'Operational Disruption',
          'Brand Damage',
          'Regulatory Penalties',
          'Legal Costs',
          'Data Loss',
          'Service Downtime',
          'Productivity Loss',
          'Compliance Violations'
        ]
      };
      
      return defaults[source] || [];
    },

    onSearchCategory(event, source) {
      const value = event.target.value;
      this.searchTerms[source] = value;
      this.showDropdown[source] = true;
    },

    onFocusCategory(source) {
      const currentValue = this.compliance[source];
      this.searchTerms[source] = currentValue || '';
      this.showDropdown[source] = true;
    },

    onBlurCategory(source) {
      // Delay hiding the dropdown to allow for item selection
      setTimeout(() => {
        this.showDropdown[source] = false;
      }, 200);
    },

    onBlurCategoryAndValidate(source) {
      this.onBlurCategory(source);
      // Validate the field after blur
      setTimeout(() => {
        this.validateField(source);
      }, 250);
    },

    selectCategory(value, source) {
      this.compliance[source] = value;
      this.searchTerms[source] = value;
      this.showDropdown[source] = false;
    },

    async addNewCategory(source, value) {
      try {
        const response = await fetch('/grc/api/categories/add/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            source: source,
            value: value.trim()
          })
        });

        const data = await response.json();
        if (data.success) {
          // Add to local categories array if not already present
          if (!this.categories[source].includes(value.trim())) {
            this.categories[source].push(value.trim());
            this.categories[source].sort(); // Keep sorted
          }
          
          // Set the value in the compliance item
          this.compliance[source] = value.trim();
          this.searchTerms[source] = value.trim();
          this.showDropdown[source] = false;
          
          PopupService.success(`Successfully added "${value.trim()}" to ${source.replace(/([A-Z])/g, ' $1').trim()}`, 'Category Added');
        } else {
          PopupService.error(`Failed to add category: ${data.message}`, 'Error');
        }
      } catch (error) {
        console.error('Error adding category:', error);
        PopupService.error('Error adding new category. Please try again.', 'Error');
      }
    },

    categoryExists(source, value) {
      return this.categories[source].some(item => 
        item.toLowerCase() === value.toLowerCase()
      );
    },

    // Add method to parse mitigation for editing
    parseMitigationForEdit(mitigation) {
      if (!mitigation) {
        return '';
      }
      
      // Check if it's JSON format
      if (typeof mitigation === 'string' && (mitigation.startsWith('[') || mitigation.startsWith('{'))) {
        try {
          const parsed = JSON.parse(mitigation);
          
          // If it's an array of steps, convert to numbered list
          if (Array.isArray(parsed)) {
            return parsed.map((step, index) => `${index + 1}. ${step}`).join('\n');
          }
          
          // If it's an object, extract meaningful values
          if (typeof parsed === 'object') {
            if (parsed.steps && Array.isArray(parsed.steps)) {
              return parsed.steps.map((step, index) => `${index + 1}. ${step}`).join('\n');
            }
            if (parsed.description) {
              return parsed.description;
            }
            // Convert object to readable format
            return Object.entries(parsed)
              .map(([key, value]) => `${key}: ${value}`)
              .join('\n');
          }
          
          return String(parsed);
        } catch (e) {
          // If JSON parsing fails, treat as plain text
          return mitigation;
        }
      }
      
      // Return as plain text
      return mitigation;
    }
  }
}
</script>

<style scoped>
@import './CreateCompliance.css';

.compliance-cancel-btn {
  width: auto;
  min-width: 120px;
  padding: 0.875rem 1.75rem;
  background-color: #f1f5f9;
  color: #64748b;
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin: 2rem 0.5rem;
}

.compliance-cancel-btn:hover {
  background-color: #e2e8f0;
  color: #475569;
}

.compliance-submit-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  margin-top: 2rem;
}

.optional-indicator {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 400;
  font-style: italic;
  margin-left: 0.5rem;
}

/* Validation styles */
.required-asterisk {
  color: #dc2626;
  font-weight: bold;
  margin-left: 0.25rem;
}

.error-input {
  border-color: #dc2626 !important;
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.15) !important;
  background-color: #fef2f2 !important;
}

.validation-error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
  font-weight: 500;
}

.compliance-field {
  position: relative;
}

.validation-error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  font-weight: 500;
}
</style> 