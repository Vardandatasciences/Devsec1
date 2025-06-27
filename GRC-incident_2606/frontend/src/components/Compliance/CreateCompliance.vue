<template>
  <div class="create-compliance-container">
    <!-- Header section -->
    <div class="compliance-header">
      <h2><i class="fas fa-plus-circle"></i> Create Compliance Record</h2>
      <p>Add new compliance items to track in your GRC system</p>
    </div>

    <!-- Popup Modal -->
    <PopupModal />

    <!-- Selection controls -->
    <div class="field-group selection-fields">
      <div class="field-group-title"><i class="fas fa-sitemap"></i> Select Policy Framework</div>
      <div class="row-fields">
        <div class="compliance-field">
          <label for="framework"><i class="fas fa-layer-group"></i> Framework <span class="required">*</span></label>
          <select id="framework" v-model="selectedFramework" class="compliance-select" required title="Select the governance framework">
            <option value="" disabled>Select Framework</option>
            <option v-for="fw in frameworks" :key="fw.id" :value="fw">{{ fw.name }}</option>
          </select>
        </div>
        
        <div class="compliance-field">
          <label for="policy"><i class="fas fa-file-contract"></i> Policy <span class="required">*</span></label>
          <select id="policy" v-model="selectedPolicy" class="compliance-select" required title="Select the policy within the framework">
            <option value="" disabled>Select Policy</option>
            <option v-for="p in policies" :key="p.id" :value="p">{{ p.name }}</option>
          </select>
        </div>
        
        <div class="compliance-field">
          <label for="subpolicy"><i class="fas fa-file-alt"></i> Sub Policy <span class="required">*</span></label>
          <select id="subpolicy" v-model="selectedSubPolicy" class="compliance-select" required title="Select the sub-policy within the policy">
            <option value="" disabled>Select Sub Policy</option>
            <option v-for="sp in subPolicies" :key="sp.id" :value="sp">{{ sp.name }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Compliance items list with tabs -->
    <div class="compliance-list">
      <!-- Tabs navigation -->
      <div class="compliance-tabs">
        <div 
          v-for="(compliance, idx) in complianceList" 
          :key="idx" 
          class="compliance-tab" 
          :class="{ 'active-tab': activeTab === idx }"
          @click="activeTab = idx"
        >
          <span>Item #{{ idx + 1 }}</span>
          <button 
            v-if="complianceList.length > 1" 
            class="tab-remove-btn" 
            @click.stop="removeCompliance(idx)" 
            title="Remove this compliance item"
          >
            <span class="btn-icon">×</span>
          </button>
        </div>
        <button 
          class="add-tab-btn" 
          @click="addCompliance" 
          title="Add new compliance item"
        >
          <span class="btn-icon">+</span>
        </button>
      </div>

      <!-- Tab content - only show active tab -->
      <div 
        v-for="(compliance, idx) in complianceList" 
        :key="idx" 
        class="compliance-item-form"
        v-show="activeTab === idx"
      >
        <!-- Header for each compliance item -->
        <div class="item-header">
          <span class="item-number"><i class="fas fa-clipboard-check"></i> Compliance Item #{{ idx + 1 }}</span>
        </div>

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
                title="Unique identifier for this compliance item (auto-generated if left blank)"
              />
              <small>Leave empty for auto-generated identifier</small>
            </div>

            <div class="compliance-field checkbox-container">
              <label style="font-weight: 500; font-size: 1rem; display: flex; align-items: center; gap: 8px;" title="Check if this compliance item represents a risk">
                <i class="fas fa-exclamation-triangle" style="color: #ff6b35;"></i>
                <input type="checkbox" v-model="compliance.IsRisk" @change="onFieldChange(idx, 'IsRisk', $event)" style="margin-right: 8px; width: auto;" />
                Is Risk
              </label>
            </div>
          </div>
          
          <!-- Compliance Title and Type in one row -->
          <div class="row-fields">
            <div class="compliance-field">
              <label><i class="fas fa-heading"></i> Compliance Title <span class="required">*</span></label>
              <input 
                v-model="compliance.ComplianceTitle" 
                @input="onFieldChange(idx, 'ComplianceTitle', $event)"
                class="compliance-input" 
                placeholder="Enter compliance title"
                required 
                :maxlength="validationRules.maxLengths.ComplianceTitle"
                title="Enter the title of the compliance item"
              />
              <div v-if="compliance.validationErrors && compliance.validationErrors.ComplianceTitle" 
                   class="validation-error">
                {{ compliance.validationErrors.ComplianceTitle.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label><i class="fas fa-tag"></i> Compliance Type <span class="required">*</span></label>
              <input 
                v-model="compliance.ComplianceType" 
                @input="onFieldChange(idx, 'ComplianceType', $event)"
                class="compliance-input" 
                placeholder="Enter compliance type"
                required
                :maxlength="validationRules.maxLengths.ComplianceType"
                title="Type of compliance (e.g. Regulatory, Internal, Security)"
              />
              <div v-if="compliance.validationErrors && compliance.validationErrors.ComplianceType" 
                   class="validation-error">
                {{ compliance.validationErrors.ComplianceType.join(', ') }}
              </div>
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label><i class="fas fa-align-left"></i> Compliance Description <span class="required">*</span></label>
            <textarea
              v-model="compliance.ComplianceItemDescription" 
              @input="onFieldChange(idx, 'ComplianceItemDescription', $event)"
              class="compliance-input" 
              :placeholder="`Compliance Description ${idx+1}`"
              required 
              rows="3"
              :maxlength="validationRules.maxLengths.ComplianceItemDescription"
              title="Detailed description of the compliance requirement"
            ></textarea>
            <div v-if="compliance.validationErrors && compliance.validationErrors.ComplianceItemDescription" 
                 class="validation-error">
              {{ compliance.validationErrors.ComplianceItemDescription.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label><i class="fas fa-crosshairs"></i> Scope <span class="required">*</span></label>
            <textarea 
              v-model="compliance.Scope" 
              @input="onFieldChange(idx, 'Scope', $event)"
              class="compliance-input" 
              placeholder="Enter scope information"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.Scope"
              title="Define the boundaries and extent of the compliance requirement"
            ></textarea>
            <div v-if="compliance.validationErrors && compliance.validationErrors.Scope" 
                 class="validation-error">
              {{ compliance.validationErrors.Scope.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label><i class="fas fa-bullseye"></i> Objective <span class="required">*</span></label>
            <textarea 
              v-model="compliance.Objective" 
              @input="onFieldChange(idx, 'Objective', $event)"
              class="compliance-input" 
              placeholder="Enter objective information"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.Objective"
              title="The goal or purpose of this compliance requirement"
            ></textarea>
            <div v-if="compliance.validationErrors && compliance.validationErrors.Objective" 
                 class="validation-error">
              {{ compliance.validationErrors.Objective.join(', ') }}
            </div>
          </div>
          
          <!-- Business Units -->
          <div class="row-fields">
            <div class="compliance-field">
              <label><i class="fas fa-building"></i> Business Units Covered <span class="required">*</span></label>
              <div class="dropdown-container">
              <!-- Business Units are loaded from database (categoryunit table) -->
              <input 
                v-model="compliance.BusinessUnitsCovered" 
                  @input="onSearchCategory($event, 'BusinessUnitsCovered', idx)"
                  @focus="onFocusCategory('BusinessUnitsCovered', idx)"
                  @blur="onBlurCategory('BusinessUnitsCovered')"
                  class="compliance-input dropdown-input" 
                  placeholder="Type to search existing units or add new ones..."
                title="Departments or business units affected by this compliance (loaded from database)"
              />
                <div v-if="showDropdown.BusinessUnitsCovered && activeComplianceIndex === idx" 
                     class="dropdown-menu">
                  <div v-if="filteredCategories.BusinessUnitsCovered.length === 0 && categories.BusinessUnitsCovered.length === 0" 
                       class="dropdown-item no-results">
                    No business units found in database
                  </div>
                  <div v-else-if="filteredCategories.BusinessUnitsCovered.length === 0" 
                       class="dropdown-item no-results">
                    No matching business units found
                  </div>
                  <div v-else>
                    <div v-for="item in filteredCategories.BusinessUnitsCovered" 
                         :key="item" 
                         class="dropdown-item"
                         @mousedown="selectCategory(item, 'BusinessUnitsCovered', idx)">
                      {{ item }}
                    </div>
                  </div>
                  <div v-if="compliance.BusinessUnitsCovered && compliance.BusinessUnitsCovered.trim() && !categoryExists('BusinessUnitsCovered', compliance.BusinessUnitsCovered)" 
                       class="dropdown-item add-new"
                       @mousedown="addNewCategory('BusinessUnitsCovered', compliance.BusinessUnitsCovered, idx)">
                    <i class="fas fa-plus"></i> Add "{{ compliance.BusinessUnitsCovered }}"
                  </div>
                </div>
              </div>
              <div v-if="compliance.validationErrors && compliance.validationErrors.BusinessUnitsCovered" 
                   class="validation-error">
                {{ compliance.validationErrors.BusinessUnitsCovered.join(', ') }}
              </div>
            </div>
          </div>
        </div>

        <!-- Risk related fields - grouped together -->
        <div class="field-group risk-fields">
          <div class="field-group-title"><i class="fas fa-shield-alt"></i> Risk Information</div>
          <div class="compliance-field full-width">
            <label><i class="fas fa-bomb"></i> Possible Damage <span class="required">*</span></label>
            <textarea
              v-model="compliance.PossibleDamage" 
              @input="onFieldChange(idx, 'PossibleDamage', $event)"
              class="compliance-input" 
              placeholder="Possible Damage"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.PossibleDamage"
              title="Potential damage that could occur if this risk materializes" 
            ></textarea>
            <div v-if="compliance.validationErrors && compliance.validationErrors.PossibleDamage" 
                 class="validation-error">
              {{ compliance.validationErrors.PossibleDamage.join(', ') }}
            </div>
          </div>
          
          <!-- Updated Mitigation field with step-by-step JSON structure -->
          <div class="compliance-field full-width">
            <label><i class="fas fa-first-aid"></i> Mitigation Steps <span class="required">*</span></label>
            <div class="mitigation-steps-container">
              <div 
                v-for="(step, stepIndex) in compliance.mitigationSteps" 
                :key="stepIndex" 
                class="mitigation-step"
              >
                <div class="step-header">
                  <span class="step-number">Step {{ stepIndex + 1 }}</span>
                  <button 
                    v-if="compliance.mitigationSteps.length > 1"
                    type="button"
                    class="remove-step-btn" 
                    @click="removeMitigationStep(idx, stepIndex)"
                    title="Remove this step"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
                <div class="step-content">
                  <div class="step-field">
                    <label>Description <span class="required">*</span></label>
                    <textarea
                      v-model="step.description"
                      @input="onMitigationStepChange(idx, stepIndex, 'description', $event)"
                      class="compliance-input step-textarea"
                      placeholder="Describe the mitigation action to be taken..."
                      rows="3"
                      required
                      maxlength="500"
                    ></textarea>
                  </div>
                </div>
              </div>
              
              <button 
                type="button"
                class="add-step-btn" 
                @click="addMitigationStep(idx)"
                title="Add a new mitigation step"
              >
                <i class="fas fa-plus"></i> Add Mitigation Step
              </button>
            </div>
            <div v-if="compliance.validationErrors && compliance.validationErrors.mitigation" 
                 class="validation-error">
              {{ compliance.validationErrors.mitigation.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label><i class="fas fa-chess"></i> Potential Risk Scenarios <span class="required">*</span></label>
            <textarea 
              v-model="compliance.PotentialRiskScenarios" 
              @input="onFieldChange(idx, 'PotentialRiskScenarios', $event)"
              class="compliance-input" 
              placeholder="Describe potential risk scenarios"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.PotentialRiskScenarios"
              title="Describe scenarios where this risk could materialize"
            ></textarea>
            <div v-if="compliance.validationErrors && compliance.validationErrors.PotentialRiskScenarios" 
                 class="validation-error">
              {{ compliance.validationErrors.PotentialRiskScenarios.join(', ') }}
            </div>
          </div>
          
          <div class="row-fields">
            <div class="compliance-field">
              <label><i class="fas fa-exclamation-circle"></i> Risk Type <span class="required">*</span></label>
              <div class="dropdown-container">
                <input 
                v-model="compliance.RiskType" 
                  @input="onSearchCategory($event, 'RiskType', idx)"
                  @focus="onFocusCategory('RiskType', idx)"
                  @blur="onBlurCategory('RiskType')"
                  class="compliance-input dropdown-input" 
                  placeholder="Type to search or add risk type..."
                required
                title="Type of risk (e.g. Operational, Financial, Strategic, Compliance, Reputational)"
                />
                <div v-if="showDropdown.RiskType && activeComplianceIndex === idx" 
                     class="dropdown-menu">
                  <div v-if="filteredCategories.RiskType.length === 0" 
                       class="dropdown-item no-results">
                    No results found
                  </div>
                  <div v-else>
                    <div v-for="item in filteredCategories.RiskType" 
                         :key="item" 
                         class="dropdown-item"
                         @mousedown="selectCategory(item, 'RiskType', idx)">
                      {{ item }}
                    </div>
                  </div>
                  <div v-if="compliance.RiskType && compliance.RiskType.trim() && !categoryExists('RiskType', compliance.RiskType)" 
                       class="dropdown-item add-new"
                       @mousedown="addNewCategory('RiskType', compliance.RiskType, idx)">
                    <i class="fas fa-plus"></i> Add "{{ compliance.RiskType }}"
                  </div>
                </div>
              </div>
              <div v-if="compliance.validationErrors && compliance.validationErrors.RiskType" 
                   class="validation-error">
                {{ compliance.validationErrors.RiskType.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label><i class="fas fa-list-alt"></i> Risk Category <span class="required">*</span></label>
              <div class="dropdown-container">
                <input 
                v-model="compliance.RiskCategory" 
                  @input="onSearchCategory($event, 'RiskCategory', idx)"
                  @focus="onFocusCategory('RiskCategory', idx)"
                  @blur="onBlurCategory('RiskCategory')"
                  class="compliance-input dropdown-input" 
                  placeholder="Type to search or add risk category..."
                required
                title="Category of risk (e.g. People, Process, Technology, External)"
                />
                <div v-if="showDropdown.RiskCategory && activeComplianceIndex === idx" 
                     class="dropdown-menu">
                  <div v-if="filteredCategories.RiskCategory.length === 0" 
                       class="dropdown-item no-results">
                    No results found
                  </div>
                  <div v-else>
                    <div v-for="item in filteredCategories.RiskCategory" 
                         :key="item" 
                         class="dropdown-item"
                         @mousedown="selectCategory(item, 'RiskCategory', idx)">
                      {{ item }}
                    </div>
                  </div>
                  <div v-if="compliance.RiskCategory && compliance.RiskCategory.trim() && !categoryExists('RiskCategory', compliance.RiskCategory)" 
                       class="dropdown-item add-new"
                       @mousedown="addNewCategory('RiskCategory', compliance.RiskCategory, idx)">
                    <i class="fas fa-plus"></i> Add "{{ compliance.RiskCategory }}"
                  </div>
                </div>
              </div>
              <div v-if="compliance.validationErrors && compliance.validationErrors.RiskCategory" 
                   class="validation-error">
                {{ compliance.validationErrors.RiskCategory.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label><i class="fas fa-chart-line"></i> Risk Business Impact <span class="required">*</span></label>
              <div class="dropdown-container">
                <input 
                v-model="compliance.RiskBusinessImpact" 
                  @input="onSearchCategory($event, 'RiskBusinessImpact', idx)"
                  @focus="onFocusCategory('RiskBusinessImpact', idx)"
                  @blur="onBlurCategory('RiskBusinessImpact')"
                  class="compliance-input dropdown-input" 
                  placeholder="Type to search or add business impact..."
                required
                title="How this risk impacts business operations"
                />
                <div v-if="showDropdown.RiskBusinessImpact && activeComplianceIndex === idx" 
                     class="dropdown-menu">
                  <div v-if="filteredCategories.RiskBusinessImpact.length === 0" 
                       class="dropdown-item no-results">
                    No results found
                  </div>
                  <div v-else>
                    <div v-for="item in filteredCategories.RiskBusinessImpact" 
                         :key="item" 
                         class="dropdown-item"
                         @mousedown="selectCategory(item, 'RiskBusinessImpact', idx)">
                      {{ item }}
                    </div>
                  </div>
                  <div v-if="compliance.RiskBusinessImpact && compliance.RiskBusinessImpact.trim() && !categoryExists('RiskBusinessImpact', compliance.RiskBusinessImpact)" 
                       class="dropdown-item add-new"
                       @mousedown="addNewCategory('RiskBusinessImpact', compliance.RiskBusinessImpact, idx)">
                    <i class="fas fa-plus"></i> Add "{{ compliance.RiskBusinessImpact }}"
                  </div>
                </div>
              </div>
              <div v-if="compliance.validationErrors && compliance.validationErrors.RiskBusinessImpact" 
                   class="validation-error">
                {{ compliance.validationErrors.RiskBusinessImpact.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Compliance classification fields - grouped together -->
        <div class="field-group classification-fields">
          <div class="field-group-title"><i class="fas fa-tasks"></i> Classification</div>
          <div class="row-fields">
            <div class="compliance-field">
              <label><i class="fas fa-exclamation"></i> Criticality <span class="required">*</span></label>
              <select 
                v-model="compliance.Criticality" 
                class="compliance-select" 
                required
                title="How critical this compliance item is to the organization"
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
            
            <div class="compliance-field">
              <label><i class="fas fa-gavel"></i> Mandatory/Optional <span class="required">*</span></label>
              <select 
                v-model="compliance.MandatoryOptional" 
                class="compliance-select" 
                required
                title="Whether this compliance item is mandatory or optional"
              >
                <option value="Mandatory">Mandatory</option>
                <option value="Optional">Optional</option>
              </select>
            </div>
          </div>
          
          <div class="row-fields">
            <div class="compliance-field">
              <label><i class="fas fa-cogs"></i> Manual/Automatic <span class="required">*</span></label>
              <select 
                v-model="compliance.ManualAutomatic" 
                class="compliance-select" 
                required
                title="Whether this compliance is checked manually or automatically"
              >
                <option value="Manual">Manual</option>
                <option value="Automatic">Automatic</option>
              </select>
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
              <label><i class="fas fa-thermometer-half"></i> Severity Rating (1-10) <span class="required">*</span></label>
              <input 
                type="number" 
                v-model.number="compliance.Impact" 
                @input="onFieldChange(idx, 'Impact', $event)"
                class="compliance-input" 
                step="0.1" 
                min="1" 
                max="10"
                required
                title="Rate the Severity Rating from 1 (lowest) to 10 (highest)"
              />
              <div v-if="compliance.validationErrors && compliance.validationErrors.Impact" 
                   class="validation-error">
                {{ compliance.validationErrors.Impact.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label><i class="fas fa-percentage"></i> Probability (1-10) <span class="required">*</span></label>
              <input 
                type="number" 
                v-model.number="compliance.Probability" 
                @input="onFieldChange(idx, 'Probability', $event)"
                class="compliance-input" 
                step="0.1" 
                min="1" 
                max="10"
                required
                title="Rate the probability from 1 (lowest) to 10 (highest)"
              />
              <div v-if="compliance.validationErrors && compliance.validationErrors.Probability" 
                   class="validation-error">
                {{ compliance.validationErrors.Probability.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Approval section -->
        <div class="field-group approval-fields">
          <div class="field-group-title"><i class="fas fa-user-check"></i> Approval Information</div>
          <!-- Approver and Approval Due Date in the same row -->
          <div class="row-fields">
            <!-- Assign Reviewer -->
            <div class="compliance-field">
              <label><i class="fas fa-user-cog"></i> Assign Reviewer <span class="required">*</span></label>
              <select 
                v-model="compliance.reviewer" 
                class="compliance-select" 
                required
                title="Person responsible for reviewing this compliance item"
              >
                <option value="" disabled>Select Reviewer</option>
                <option v-for="user in users" :key="user.UserId" :value="user.UserId">
                  {{ user.UserName }} {{ user.email ? `(${user.email})` : '' }}
                </option>
              </select>
              <span v-if="!users.length" class="validation-error">No reviewers available</span>
            </div>
            <!-- Approval Due Date -->
            <div class="compliance-field">
              <label for="ApprovalDueDate"><i class="fas fa-calendar-alt"></i> Approval Due Date <span class="required">*</span></label>
              <input 
                type="date" 
                v-model="compliance.ApprovalDueDate" 
                @input="onFieldChange(idx, 'ApprovalDueDate', $event)"
                class="compliance-input" 
                required
                :min="minDate"
                title="Deadline for reviewing this compliance item (must be a future date)" 
              />
              <div v-if="compliance.validationErrors && compliance.validationErrors.ApprovalDueDate" 
                   class="validation-error">
                {{ compliance.validationErrors.ApprovalDueDate.join(', ') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="compliance-submit-container">
      <button 
        class="compliance-submit-btn" 
        @click="submitCompliance"
        :disabled="loading"
      >
        <span v-if="loading">Saving...</span>
        <span v-else>Submit Compliance</span>
      </button>
    </div>
  </div>
</template>

<script>
import { complianceService } from '@/services/api';
import { PopupService, PopupModal } from '@/modules/popup';

export default {
  name: 'CreateCompliance',
  components: {
    PopupModal
  },
  data() {
    return {
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      frameworks: [],
      policies: [],
      subPolicies: [],
      users: [],
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
      },
      activeComplianceIndex: -1,
      complianceList: [
        {
          ComplianceTitle: '',
          ComplianceItemDescription: '',
          ComplianceType: '',
          Scope: '',
          Objective: '',
          BusinessUnitsCovered: '',
          Identifier: '',
          IsRisk: false,
          PossibleDamage: '',
          mitigation: '',
          mitigationSteps: [
            {
              description: ''
            }
          ],
          PotentialRiskScenarios: '',
          RiskType: '',
          RiskCategory: '',
          RiskBusinessImpact: '',
          Criticality: 'Medium',
          MandatoryOptional: 'Mandatory',
          ManualAutomatic: 'Manual',
          Impact: 5.0,
          Probability: 5.0,
          Status: 'Under Review',
          reviewer: 2, // Default reviewer
          ApprovalDueDate: '',
          Applicability: '',
          // Validation errors for each field
          validationErrors: {}
        }
      ],
      loading: false,
      activeTab: 0,
      // Centralized validation patterns (allow-list approach)
      validationRules: {
        // Character set patterns
        textPattern: /^[a-zA-Z0-9\s.,!?\-_()[\]{}:;'"&%$#@+=\n\r\t]*$/,
        alphanumericPattern: /^[a-zA-Z0-9\s.\-_]*$/,
        identifierPattern: /^[a-zA-Z0-9\-_]*$/,
        
        // Field length limits
        maxLengths: {
          ComplianceTitle: 145,
          ComplianceItemDescription: 5000,
          ComplianceType: 100,
          Scope: 5000,
          Objective: 5000,
          BusinessUnitsCovered: 225,
          Identifier: 45,
          PossibleDamage: 5000,
          mitigation: 5000,
          PotentialRiskScenarios: 5000,
          RiskType: 45,
          RiskCategory: 45,
          RiskBusinessImpact: 45,
          Applicability: 45
        },
        
        // Field minimum length requirements
        minLengths: {
          ComplianceTitle: 3,
          ComplianceItemDescription: 10,
          ComplianceType: 3,
          Scope: 10,
          Objective: 10,
          BusinessUnitsCovered: 3,
          mitigation: 10,
          PossibleDamage: 10,
          PotentialRiskScenarios: 10,
          RiskType: 3,
          RiskCategory: 3,
          RiskBusinessImpact: 3
        },
        
        // Allowed choice values
        allowedChoices: {
          Criticality: ['High', 'Medium', 'Low'],
          MandatoryOptional: ['Mandatory', 'Optional'],
          ManualAutomatic: ['Manual', 'Automatic']
        },
        
        // Numeric field ranges
        numericRanges: {
          Impact: { min: 1, max: 10 },
          Probability: { min: 1, max: 10 }
        }
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
        const searchTerm = (this.searchTerms[key] || '').toLowerCase();
        const categoryItems = this.categories[key] || [];
        filtered[key] = categoryItems.filter(item => 
          item.toLowerCase().includes(searchTerm)
        );
        console.log(`Filtered ${key}: ${filtered[key].length} items from ${categoryItems.length} total`);
      });
      return filtered;
    }
  },
  async created() {
    console.log('CreateCompliance component created - loading data...');
    await this.loadFrameworks();
    await this.loadUsers();
    await this.loadAllCategories();
    
    // Initialize mitigation JSON for all compliance items
    this.complianceList.forEach((compliance, index) => {
      this.updateMitigationJson(index);
    });
    
    console.log('CreateCompliance component data loaded');
  },
  watch: {
    selectedFramework(newValue) {
      if (newValue && newValue.id) {
        this.loadPolicies(newValue.id);
        this.selectedPolicy = '';
        this.selectedSubPolicy = '';
        this.policies = [];
        this.subPolicies = [];
      }
    },
    selectedPolicy(newValue) {
      if (newValue && newValue.id) {
        this.loadSubPolicies(newValue.id);
        this.selectedSubPolicy = '';
        this.subPolicies = [];
        
        // Set the applicability for all compliance items from the selected policy
        if (newValue.applicability) {
          this.complianceList.forEach(compliance => {
            compliance.Applicability = newValue.applicability;
          });
        }
      }
    }
  },
  methods: {
    // Centralized validation methods using allow-list approach
    sanitizeString(value) {
      if (typeof value !== 'string') return String(value || '');
      // Remove control characters except newline, tab, carriage return
      // eslint-disable-next-line no-control-regex
      return value.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
    },
    
    sanitizeStringForSubmission(value) {
      if (typeof value !== 'string') return String(value || '');
      // Remove control characters and trim for final submission
      // eslint-disable-next-line no-control-regex
      return value.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '').trim();
    },
    
    validateRequiredString(value, fieldName, maxLength = null, minLength = null, pattern = null) {
      const sanitized = this.sanitizeString(value);
      const trimmedValue = sanitized.trim();
      const errors = [];
      
      if (!trimmedValue || trimmedValue.length === 0) {
        errors.push(`${fieldName} is required and cannot be empty`);
      }
      
      if (minLength && trimmedValue.length > 0 && trimmedValue.length < minLength) {
        errors.push(`${fieldName} must be at least ${minLength} characters long`);
      }
      
      if (maxLength && sanitized.length > maxLength) {
        errors.push(`${fieldName} must not exceed ${maxLength} characters`);
      }
      
      if (pattern && sanitized && !pattern.test(sanitized)) {
        errors.push(`${fieldName} contains invalid characters`);
      }
      
      return { value: sanitized, errors };
    },
    
    validateOptionalString(value, fieldName, maxLength = null, pattern = null) {
      const sanitized = this.sanitizeString(value);
      const errors = [];
      
      if (maxLength && sanitized.length > maxLength) {
        errors.push(`${fieldName} must not exceed ${maxLength} characters`);
      }
      
      if (pattern && sanitized && !pattern.test(sanitized)) {
        errors.push(`${fieldName} contains invalid characters`);
      }
      
      return { value: sanitized, errors };
    },
    
    validateChoiceField(value, fieldName, allowedChoices) {
      const errors = [];
      
      if (!value || value === '') {
        errors.push(`${fieldName} is required`);
      } else if (!allowedChoices.includes(value)) {
        errors.push(`${fieldName} must be one of: ${allowedChoices.join(', ')}`);
      }
      
      return { value, errors };
    },
    
    validateNumericField(value, fieldName, min = null, max = null) {
      const errors = [];
      const numValue = parseFloat(value);
      
      if (isNaN(numValue)) {
        errors.push(`${fieldName} must be a valid number`);
      } else {
        if (min !== null && numValue < min) {
          errors.push(`${fieldName} must be at least ${min}`);
        }
        if (max !== null && numValue > max) {
          errors.push(`${fieldName} must not exceed ${max}`);
        }
      }
      
      return { value: numValue, errors };
    },
    
    validateDateField(value, fieldName) {
      const errors = [];
      
      if (!value || value === '') {
        errors.push(`${fieldName} is required`);
      } else {
        const datePattern = /^\d{4}-\d{2}-\d{2}$/;
        if (!datePattern.test(value)) {
          errors.push(`${fieldName} must be in YYYY-MM-DD format`);
        } else {
          const date = new Date(value);
          if (isNaN(date.getTime())) {
            errors.push(`${fieldName} must be a valid date`);
          } else {
            // Check if date is in the future (for approval due dates)
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Reset time to compare only dates
            if (date < today) {
              errors.push(`${fieldName} must be a future date`);
            }
          }
        }
      }
      
      return { value, errors };
    },
    
    validateComplianceField(compliance, fieldName, value) {
      const rules = this.validationRules;
      let result = { value, errors: [] };
      
      switch (fieldName) {
        case 'ComplianceTitle':
          result = this.validateRequiredString(
            value, 'Compliance Title', 
            rules.maxLengths.ComplianceTitle,
            rules.minLengths.ComplianceTitle,
            rules.textPattern
          );
          break;
          
        case 'ComplianceItemDescription':
          result = this.validateRequiredString(
            value, 'Compliance Description', 
            rules.maxLengths.ComplianceItemDescription,
            rules.minLengths.ComplianceItemDescription,
            rules.textPattern
          );
          break;
          
        case 'ComplianceType':
          result = this.validateRequiredString(
            value, 'Compliance Type', 
            rules.maxLengths.ComplianceType,
            rules.minLengths.ComplianceType,
            rules.textPattern
          );
          break;
          
        case 'Scope':
          result = this.validateRequiredString(
            value, 'Scope', 
            rules.maxLengths.Scope,
            rules.minLengths.Scope,
            rules.textPattern
          );
          break;
          
        case 'Objective':
          result = this.validateRequiredString(
            value, 'Objective', 
            rules.maxLengths.Objective,
            rules.minLengths.Objective,
            rules.textPattern
          );
          break;
          
        case 'BusinessUnitsCovered':
          result = this.validateRequiredString(
            value, 'Business Units Covered', 
            rules.maxLengths.BusinessUnitsCovered,
            rules.minLengths.BusinessUnitsCovered,
            rules.textPattern
          );
          break;
          
        case 'Identifier':
          if (value && value.trim()) {
            result = this.validateOptionalString(
              value, 'Identifier', 
              rules.maxLengths.Identifier, 
              rules.identifierPattern
            );
          }
          break;
          
        case 'PossibleDamage':
          result = this.validateRequiredString(
            value, 'Possible Damage', 
            rules.maxLengths.PossibleDamage,
            rules.minLengths.PossibleDamage,
            rules.textPattern
          );
          break;
          
        case 'PotentialRiskScenarios':
          result = this.validateRequiredString(
            value, 'Potential Risk Scenarios', 
            rules.maxLengths.PotentialRiskScenarios,
            rules.minLengths.PotentialRiskScenarios,
            rules.textPattern
          );
          break;
          
        case 'RiskType':
          result = this.validateRequiredString(
            value, 'Risk Type', 
            rules.maxLengths.RiskType,
            rules.minLengths.RiskType,
            rules.textPattern
          );
          break;
          
        case 'RiskCategory':
          result = this.validateRequiredString(
            value, 'Risk Category', 
            rules.maxLengths.RiskCategory,
            rules.minLengths.RiskCategory,
            rules.textPattern
          );
          break;
          
        case 'RiskBusinessImpact':
          result = this.validateRequiredString(
            value, 'Risk Business Impact', 
            rules.maxLengths.RiskBusinessImpact,
            rules.minLengths.RiskBusinessImpact,
            rules.textPattern
          );
          break;
          
        case 'mitigation':
          result = this.validateRequiredString(
            value, 'Mitigation', 
            rules.maxLengths.mitigation,
            rules.minLengths.mitigation,
            rules.textPattern
          );
          break;
          
        case 'Applicability':
          result = this.validateOptionalString(
            value, 'Applicability', 
            rules.maxLengths.Applicability, 
            rules.textPattern
          );
          break;
          
        case 'Criticality':
          result = this.validateChoiceField(
            value, 'Criticality', 
            rules.allowedChoices.Criticality
          );
          break;
          
        case 'MandatoryOptional':
          result = this.validateChoiceField(
            value, 'Mandatory/Optional', 
            rules.allowedChoices.MandatoryOptional
          );
          break;
          
        case 'ManualAutomatic':
          result = this.validateChoiceField(
            value, 'Manual/Automatic', 
            rules.allowedChoices.ManualAutomatic
          );
          break;
          
        case 'Impact':
          result = this.validateNumericField(
            value, 'Severity Rating', 
            rules.numericRanges.Impact.min, 
            rules.numericRanges.Impact.max
          );
          break;
          
        case 'Probability':
          result = this.validateNumericField(
            value, 'Probability', 
            rules.numericRanges.Probability.min, 
            rules.numericRanges.Probability.max
          );
          break;
          
        case 'ApprovalDueDate':
          result = this.validateDateField(value, 'Approval Due Date');
          break;
      }
      
      // Update validation errors for the field
      if (!compliance.validationErrors) {
        compliance.validationErrors = {};
      }
      
      if (result.errors.length > 0) {
        compliance.validationErrors[fieldName] = result.errors;
      } else {
        delete compliance.validationErrors[fieldName];
      }
      
      return result;
    },
    
    // Real-time validation on input
    onFieldChange(complianceIndex, fieldName, event) {
      const compliance = this.complianceList[complianceIndex];
      let value;
      
      // Handle different input types
      if (fieldName === 'IsRisk') {
        value = event.target.checked;
        compliance[fieldName] = value;
      } else {
        value = event.target.value;
        // Update the field value directly without sanitization during typing
        compliance[fieldName] = value;
        
        // Only validate for error display, don't replace the value
        this.validateComplianceField(compliance, fieldName, value);
      }
      
      // Force reactivity update
      this.$forceUpdate();
    },
    
    // Comprehensive form validation before submission
    validateAllFields() {
      let isValid = true;
      const errors = [];
      
      // Validate framework selection
      if (!this.selectedFramework || !this.selectedFramework.id) {
        errors.push('Please select a framework');
        isValid = false;
      }
      
      // Validate policy selection
      if (!this.selectedPolicy || !this.selectedPolicy.id) {
        errors.push('Please select a policy');
        isValid = false;
      }
      
      // Validate sub-policy selection
      if (!this.selectedSubPolicy || !this.selectedSubPolicy.id) {
        errors.push('Please select a sub-policy');
        isValid = false;
      }
      
      // Validate each compliance item
      this.complianceList.forEach((compliance, index) => {
        // Reset validation errors
        compliance.validationErrors = {};
        
        // Validate reviewer selection
        if (!compliance.reviewer || compliance.reviewer === '') {
          compliance.validationErrors.reviewer = ['Please select a reviewer'];
          errors.push(`Please select a reviewer for item ${index + 1}`);
          isValid = false;
        }
        
        // Validate mitigation steps separately
        if (!this.validateMitigationSteps(index)) {
          isValid = false;
          errors.push(`Item ${index + 1}: Mitigation steps validation failed`);
        }
        
        // Update mitigation JSON before validation
        this.updateMitigationJson(index);
        
        // Required fields validation - all fields are mandatory including risk fields
        const requiredFields = [
          'ComplianceTitle',
          'ComplianceItemDescription', 
          'ComplianceType',
          'Scope',
          'Objective',
          'BusinessUnitsCovered',
          'PossibleDamage',
          'PotentialRiskScenarios',
          'RiskType',
          'RiskCategory',
          'RiskBusinessImpact',
          'Criticality',
          'MandatoryOptional',
          'ManualAutomatic',
          'Impact',
          'Probability',
          'ApprovalDueDate'
        ];
        
        // Validate all required fields
        requiredFields.forEach(fieldName => {
          const result = this.validateComplianceField(compliance, fieldName, compliance[fieldName]);
          if (result.errors.length > 0) {
            errors.push(`Item ${index + 1}: ${result.errors.join(', ')}`);
            isValid = false;
          }
        });
        
        // Validate optional fields that have values
        const optionalFields = ['Identifier', 'Applicability'];
        optionalFields.forEach(fieldName => {
          if (compliance[fieldName] && compliance[fieldName].trim()) {
            const result = this.validateComplianceField(compliance, fieldName, compliance[fieldName]);
            if (result.errors.length > 0) {
              errors.push(`Item ${index + 1}: ${result.errors.join(', ')}`);
              isValid = false;
            }
          }
        });
      });
      
      return { isValid, errors };
    },

    async loadFrameworks() {
      try {
        this.loading = true;
        const response = await complianceService.getFrameworks();
        this.frameworks = response.data.data.map(fw => ({
          id: fw.FrameworkId,
          name: fw.FrameworkName
        }));
      } catch (error) {
        PopupService.error('Failed to load frameworks. Please refresh the page and try again.');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async loadPolicies(frameworkId) {
      try {
        this.loading = true;
        const response = await complianceService.getPolicies(frameworkId);
        this.policies = response.data.data.map(p => ({
          id: p.PolicyId,
          name: p.PolicyName,
          applicability: p.Applicability || ''
        }));
      } catch (error) {
        PopupService.error('Failed to load policies. Please try selecting a different framework.');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async loadSubPolicies(policyId) {
      try {
        this.loading = true;
        const response = await complianceService.getSubPolicies(policyId);
        this.subPolicies = response.data.data.map(sp => ({
          id: sp.SubPolicyId,
          name: sp.SubPolicyName
        }));
      } catch (error) {
        PopupService.error('Failed to load sub-policies. Please try selecting a different policy.');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        console.log('Users API response:', response); // Debug log
        
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users.map(user => ({
            UserId: user.UserId,
            UserName: user.UserName || `User ${user.UserId}`,
            email: user.email || ''
          }));
          
          // Set default reviewer if users exist
          if (this.users.length > 0 && this.complianceList.length > 0) {
            this.complianceList[0].reviewer = this.users[0].UserId;
          }
          
          console.log('Loaded users:', this.users);
        } else {
          throw new Error('Invalid users data received');
        }
      } catch (error) {
        console.error('Failed to load users:', error);
        PopupService.error('Failed to load reviewers. Please refresh the page and try again.');
      } finally {
        this.loading = false;
      }
    },
    addCompliance() {
      // Get applicability from the selected policy
      const policyApplicability = this.selectedPolicy ? this.selectedPolicy.applicability || '' : '';
      
      this.complianceList.push({
        ComplianceTitle: '',
        ComplianceItemDescription: '',
        ComplianceType: '',
        Scope: '',
        Objective: '',
        BusinessUnitsCovered: '',
        Identifier: '',
        IsRisk: false,
        PossibleDamage: '',
        mitigation: '',
        mitigationSteps: [
          {
            description: ''
          }
        ],
        PotentialRiskScenarios: '',
        RiskType: '',
        RiskCategory: '',
        RiskBusinessImpact: '',
        Criticality: 'Medium',
        MandatoryOptional: 'Mandatory',
        ManualAutomatic: 'Manual',
        Impact: 5.0,
        Probability: 5.0,
        Status: 'Under Review',
        reviewer: 2, // Default reviewer
        ApprovalDueDate: '',
        Applicability: policyApplicability, // Set Applicability from policy
        validationErrors: {}
      });
      
      // Switch to the newly added tab
      this.activeTab = this.complianceList.length - 1;
      
      // Show success popup
      PopupService.success(`New compliance item ${this.complianceList.length} added successfully!`, 'Item Added');
    },
    removeCompliance(idx) {
      if (this.complianceList.length > 1) {
        PopupService.confirm(
          `Are you sure you want to remove compliance item ${idx + 1}? This action cannot be undone.`,
          'Remove Compliance Item',
          () => {
            // If removing the active tab or a tab before it, adjust the active tab
            if (idx <= this.activeTab) {
              // If removing the last tab and it's active, go to previous tab
              if (idx === this.complianceList.length - 1 && idx === this.activeTab) {
                this.activeTab = Math.max(0, idx - 1);
              } 
              // If removing a tab before the active one, decrement active tab index
              else if (idx < this.activeTab) {
                this.activeTab--;
              }
            }
            
            this.complianceList.splice(idx, 1);
            PopupService.success('Compliance item removed successfully.', 'Item Removed');
          }
        );
      } else {
        PopupService.warning('Cannot remove the last compliance item. At least one item is required.', 'Cannot Remove');
      }
    },

    async submitCompliance() {
      // Comprehensive validation using allow-list approach
      const validation = this.validateAllFields();
      
      if (!validation.isValid) {
        PopupService.error(validation.errors.join('\n'), 'Validation Error');
        return;
      }

      try {
        this.loading = true;
        
        // First, save any new BusinessUnitsCovered values that were typed but not saved yet
        for (let i = 0; i < this.complianceList.length; i++) {
          const compliance = this.complianceList[i];
          if (compliance.BusinessUnitsCovered && 
              !this.categoryExists('BusinessUnitsCovered', compliance.BusinessUnitsCovered)) {
            console.log(`Saving new BusinessUnitsCovered: ${compliance.BusinessUnitsCovered}`);
            try {
              await this.addNewCategory('BusinessUnitsCovered', compliance.BusinessUnitsCovered, i);
            } catch (error) {
              console.warn(`Could not save BusinessUnitsCovered "${compliance.BusinessUnitsCovered}" to database:`, error);
              // Continue anyway - the value will still be submitted with the compliance
            }
          }
        }
        
        const complianceData = this.complianceList.map(compliance => ({
          SubPolicy: this.selectedSubPolicy.id,
          ComplianceTitle: this.sanitizeStringForSubmission(compliance.ComplianceTitle),
          ComplianceItemDescription: this.sanitizeStringForSubmission(compliance.ComplianceItemDescription),
          ComplianceType: this.sanitizeStringForSubmission(compliance.ComplianceType),
          Scope: this.sanitizeStringForSubmission(compliance.Scope),
          Objective: this.sanitizeStringForSubmission(compliance.Objective),
          BusinessUnitsCovered: this.sanitizeStringForSubmission(compliance.BusinessUnitsCovered),
          Identifier: this.sanitizeStringForSubmission(compliance.Identifier) || '',
          IsRisk: Boolean(compliance.IsRisk),
          PossibleDamage: this.sanitizeStringForSubmission(compliance.PossibleDamage),
          mitigation: this.sanitizeStringForSubmission(compliance.mitigation),
          PotentialRiskScenarios: this.sanitizeStringForSubmission(compliance.PotentialRiskScenarios),
          RiskType: this.sanitizeStringForSubmission(compliance.RiskType),
          RiskCategory: this.sanitizeStringForSubmission(compliance.RiskCategory),
          RiskBusinessImpact: this.sanitizeStringForSubmission(compliance.RiskBusinessImpact),
          Criticality: compliance.Criticality,
          MandatoryOptional: compliance.MandatoryOptional,
          ManualAutomatic: compliance.ManualAutomatic,
          Impact: compliance.Impact,
          Probability: compliance.Probability,
          Status: compliance.Status,
          ComplianceVersion: "1.0",
          reviewer: compliance.reviewer,
          ApprovalDueDate: compliance.ApprovalDueDate,
          Applicability: this.sanitizeStringForSubmission(compliance.Applicability)
        }));

        // Submit all compliance items and collect created IDs
        const createdComplianceIds = [];
        for (const data of complianceData) {
          console.log('Submitting compliance data:', data);
          const response = await complianceService.createCompliance(data);
          console.log('Response:', response);
          
          if (!response.data.success) {
            console.error('Validation errors:', response.data.errors);
            throw new Error(JSON.stringify(response.data.errors) || 'Failed to create compliance');
          }
          
          // Extract compliance ID from response
          if (response.data.compliance && response.data.compliance.ComplianceId) {
            createdComplianceIds.push(response.data.compliance.ComplianceId);
          } else if (response.data.ComplianceId) {
            createdComplianceIds.push(response.data.ComplianceId);
          }
        }

        // Show success popup with compliance IDs
        let successMessage = 'All compliance items have been successfully saved and submitted for review!';
        if (createdComplianceIds.length > 0) {
          if (createdComplianceIds.length === 1) {
            successMessage = `Compliance item has been successfully created with ID: ${createdComplianceIds[0]} and submitted for review!`;
          } else {
            successMessage = `${createdComplianceIds.length} compliance items have been successfully created with IDs: ${createdComplianceIds.join(', ')} and submitted for review!`;
          }
        }
        PopupService.success(successMessage, 'Success');
        
        // Reset form
        this.$emit('compliance-created');
        this.complianceList = [
          {
            ComplianceTitle: '',
            ComplianceItemDescription: '',
            ComplianceType: '',
            Scope: '',
            Objective: '',
            BusinessUnitsCovered: '',
            Identifier: '',
            IsRisk: false,
            PossibleDamage: '',
            mitigation: '',
            mitigationSteps: [
              {
                description: ''
              }
            ],
            PotentialRiskScenarios: '',
            RiskType: '',
            RiskCategory: '',
            RiskBusinessImpact: '',
            Criticality: 'Medium',
            MandatoryOptional: 'Mandatory',
            ManualAutomatic: 'Manual',
            Impact: 5.0,
            Probability: 5.0,
            Status: 'Under Review',
            reviewer: 2, // Default reviewer
            ApprovalDueDate: '',
            Applicability: '',
            validationErrors: {}
          }
        ];
        
        // Reset active tab
        this.activeTab = 0;

        // Clear selections
        this.selectedSubPolicy = '';
        this.selectedPolicy = '';
        this.selectedFramework = '';
      } catch (error) {
        console.error('Error submitting compliance:', error);
        let errorMessage = 'Failed to submit compliance. Please check your data and try again.';
        if (error.response?.data?.errors) {
          errorMessage = Object.entries(error.response.data.errors)
            .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
            .join('\n');
        } else if (error.message) {
          try {
            const parsedError = JSON.parse(error.message);
            errorMessage = Object.entries(parsedError)
              .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
              .join('\n');
          } catch {
            errorMessage = error.message;
          }
        }
        PopupService.error(errorMessage, 'Submission Failed');
      } finally {
        this.loading = false;
      }
    },

    // Category management methods
    async loadAllCategories() {
      console.log('Loading all categories...');
      
      // Initialize default categories first
      try {
        console.log('Initializing default categories...');
        const initResponse = await complianceService.initializeCategories();
        console.log('Initialize response:', initResponse.data);
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
        
        const response = await complianceService.getCategoryValues(source);
        console.log(`${source} response data:`, response.data);
        
        if (response.data.success) {
          this.categories[source] = response.data.data || [];
          console.log(`${source} loaded ${this.categories[source].length} items:`, this.categories[source]);
          
          // For BusinessUnitsCovered, ONLY use database values - NEVER use defaults
          if (this.categories[source].length === 0 && source !== 'BusinessUnitsCovered') {
            console.log(`No data found for ${source}, using defaults`);
            this.categories[source] = this.getDefaultCategoryValues(source);
          } else if (source === 'BusinessUnitsCovered' && this.categories[source].length === 0) {
            console.warn(`No BusinessUnitsCovered found in database! Check categoryunit table.`);
          }
        } else {
          console.error(`Failed to load ${source} categories:`, response.data.message);
          if (source === 'BusinessUnitsCovered') {
            // For BusinessUnitsCovered, NEVER use defaults - keep empty if API fails
            this.categories[source] = [];
            console.error(`${source} API failed - will only show database values when available`);
          } else {
            // Use default values if API fails for other categories
            this.categories[source] = this.getDefaultCategoryValues(source);
          }
        }
      } catch (error) {
        console.error(`Error loading ${source} categories:`, error);
        if (source === 'BusinessUnitsCovered') {
          // For BusinessUnitsCovered, NEVER use defaults - only database values
          this.categories[source] = [];
          console.error(`${source} network error - will only show database values when connection restored`);
        } else {
          // Use default values if network error for other categories
          this.categories[source] = this.getDefaultCategoryValues(source);
        }
      }
    },

    getDefaultCategoryValues(source) {
      const defaults = {
        'BusinessUnitsCovered': [], // BusinessUnitsCovered ONLY comes from database
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

    onSearchCategory(event, source, complianceIndex) {
      const value = event.target.value;
      this.searchTerms[source] = value;
      this.activeComplianceIndex = complianceIndex;
      this.showDropdown[source] = true;
    },

    onFocusCategory(source, complianceIndex) {
      this.activeComplianceIndex = complianceIndex;
      const currentValue = this.complianceList[complianceIndex][source];
      this.searchTerms[source] = currentValue || '';
      this.showDropdown[source] = true;
    },

    onBlurCategory(source) {
      // Delay hiding the dropdown to allow for item selection
      setTimeout(() => {
        this.showDropdown[source] = false;
      }, 200);
    },

    selectCategory(value, source, complianceIndex) {
      this.complianceList[complianceIndex][source] = value;
      this.searchTerms[source] = value;
      this.showDropdown[source] = false;
      this.onFieldChange(complianceIndex, source, { target: { value } });
    },

    async addNewCategory(source, value, complianceIndex) {
      try {
        console.log(`Adding new category: ${source} = ${value}`);
        
        // Always add to local array first for immediate UI update
        if (!this.categories[source].includes(value.trim())) {
          this.categories[source].push(value.trim());
          this.categories[source].sort(); // Keep sorted
          console.log(`Added "${value.trim()}" to local ${source} array`);
        }
        
        // Set the value in the compliance item immediately
        this.complianceList[complianceIndex][source] = value.trim();
        this.searchTerms[source] = value.trim();
        this.showDropdown[source] = false;
        
        // Try to save to database
        try {
          console.log('Attempting to add category to database:', { source, value: value.trim() });
          
          const response = await complianceService.addCategoryValue({
            source: source,
            value: value.trim()
          });

          console.log('Add category response data:', response.data);
          
          if (response.data.success) {
            const displayName = source === 'BusinessUnitsCovered' ? 'Business Units' : source.replace(/([A-Z])/g, ' $1').trim();
            PopupService.success(`Successfully added "${value.trim()}" to ${displayName}`, 'Category Added');
            
            // Reload the categories to ensure we have the latest data
            await this.loadCategoryValues(source);
          } else {
            console.warn('Category added locally but API returned:', response.data.message);
            PopupService.success(`Added "${value.trim()}" locally (database save issue: ${response.data.message})`, 'Category Added');
          }
        } catch (apiError) {
          console.warn('Category added locally but API call failed:', apiError);
          PopupService.success(`Added "${value.trim()}" locally (will sync when database is available)`, 'Category Added');
        }
        
      } catch (error) {
        console.error('Error adding category:', error);
        PopupService.error(`Error adding new category: ${error.message}`, 'Error');
      }
    },

    categoryExists(source, value) {
      return this.categories[source].some(item => 
        item.toLowerCase() === value.toLowerCase()
      );
    },

    // Mitigation steps management methods
    addMitigationStep(complianceIndex) {
      const compliance = this.complianceList[complianceIndex];
      compliance.mitigationSteps.push({
        description: ''
      });
      
      this.updateMitigationJson(complianceIndex);
      PopupService.success('New mitigation step added successfully!', 'Step Added');
    },

    removeMitigationStep(complianceIndex, stepIndex) {
      const compliance = this.complianceList[complianceIndex];
      if (compliance.mitigationSteps.length > 1) {
        PopupService.confirm(
          `Are you sure you want to remove mitigation step ${stepIndex + 1}? This action cannot be undone.`,
          'Remove Mitigation Step',
          () => {
            compliance.mitigationSteps.splice(stepIndex, 1);
            this.updateMitigationJson(complianceIndex);
            PopupService.success('Mitigation step removed successfully.', 'Step Removed');
          }
        );
      } else {
        PopupService.warning('Cannot remove the last mitigation step. At least one step is required.', 'Cannot Remove');
      }
    },

    onMitigationStepChange(complianceIndex, stepIndex, field, event) {
      const compliance = this.complianceList[complianceIndex];
      const value = event.target.value;
      
      compliance.mitigationSteps[stepIndex][field] = value;
      this.updateMitigationJson(complianceIndex);
      
      // Validate mitigation steps
      this.validateMitigationSteps(complianceIndex);
    },

    updateMitigationJson(complianceIndex) {
      const compliance = this.complianceList[complianceIndex];
      
      // Convert mitigation steps to JSON string for backend storage
      const mitigationData = {
        steps: compliance.mitigationSteps.map((step, index) => ({
          stepNumber: index + 1,
          description: step.description.trim()
        })).filter(step => step.description), // Only include steps with descriptions
        totalSteps: compliance.mitigationSteps.length,
        lastUpdated: new Date().toISOString()
      };
      
      compliance.mitigation = JSON.stringify(mitigationData);
    },

    validateMitigationSteps(complianceIndex) {
      const compliance = this.complianceList[complianceIndex];
      const errors = [];
      
      // Check if at least one step has a description
      const hasValidStep = compliance.mitigationSteps.some(step => 
        step.description && step.description.trim()
      );
      
      if (!hasValidStep) {
        errors.push('At least one mitigation step with a description is required');
      }
      
      // Check individual step validation
      compliance.mitigationSteps.forEach((step, index) => {
        if (step.description && step.description.trim()) {
          if (step.description.length > 500) {
            errors.push(`Step ${index + 1} description cannot exceed 500 characters`);
          }
        }
      });
      
      // Update validation errors
      if (!compliance.validationErrors) {
        compliance.validationErrors = {};
      }
      
      if (errors.length > 0) {
        compliance.validationErrors.mitigation = errors;
      } else {
        delete compliance.validationErrors.mitigation;
      }
      
      return errors.length === 0;
    }
  }
}
</script>

<style scoped>
@import './CreateCompliance.css';

.create-compliance-container {
  font-size: 14px;  /* Base font size for the component */
}

.compliance-header h2 {
  font-size: 1.5rem;
}

.compliance-header p {
  font-size: 0.9rem;
}

.compliance-field label {
  font-size: 0.85rem;
}

.compliance-input,
.compliance-select {
  font-size: 0.9rem !important;
}

.item-number {
  font-size: 1.5rem;
}

.compliance-submit-btn {
  font-size: 0.9rem;
}

.validation-error {
  font-size: 0.75rem;
}

.compliance-field small {
  font-size: 0.75rem;
}

.required {
  color: red;
  font-weight: bold;
}

</style> 