<template>
  <div class="compliance-versioning-container">
    <div class="compliance-heading">
      <h1>Compliance Tailoring & Templating</h1>
      <div class="heading-underline"></div>
    </div>
    <div class="selection-row">
      <div class="selection-group">
        <select v-model="selectedFramework" class="select">
          <option disabled value="">Select Framework</option>
          <option v-for="fw in frameworks" :key="fw.id" :value="fw">{{ fw.name }}</option>
        </select>
      </div>
      <div class="selection-group">
        <select v-model="selectedPolicy" class="select" :disabled="!selectedFramework">
          <option disabled value="">Select Policy</option>
          <option v-for="p in policies" :key="p.id" :value="p">{{ p.name }}</option>
        </select>
      </div>
      <div class="selection-group">
        <select v-model="selectedSubPolicy" class="select" :disabled="!selectedPolicy">
          <option disabled value="">Select Sub Policy</option>
          <option v-for="sp in subPolicies" :key="sp.id" :value="sp">{{ sp.name }}</option>
        </select>
      </div>
      <button @click="refreshCurrentData" class="refresh-btn" title="Refresh Data">
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
      </button>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <div class="loading-text">Loading data...</div>
    </div>
    
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i> {{ error }}
      <button @click="refreshCurrentData" class="retry-btn">Retry</button>
    </div>

    <div v-if="selectedSubPolicy" class="compliance-table-container">
      <h3>Compliances for Selected Subpolicy</h3>
      <div v-if="loading" class="loading">Loading compliances...</div>
      <div v-else-if="subPolicyCompliances.length === 0" class="no-compliances">No compliances found for this subpolicy.</div>
      <table v-else class="compliance-table">
        <thead>
          <tr>
            <th>Description</th>
            <th>Possible Damage</th>
            <th>Mitigation</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(compliance, idx) in subPolicyCompliances" :key="compliance.ComplianceId">
            <!-- If in edit mode, show the full form -->
            <template v-if="editIdx === idx">
              <td colspan="4">
                <form @submit.prevent="saveEdit(compliance)" class="edit-form-grid">
                  <div class="form-row">
                    <div class="form-group">
                      <label>Description <span class="required-asterisk">*</span></label>
                      <input 
                        v-model="editRow.ComplianceItemDescription" 
                        class="compliance-input"
                        :class="{ 'error-input': validationErrors.ComplianceItemDescription }"
                        @blur="validateField('ComplianceItemDescription')"
                      />
                      <span v-if="validationErrors.ComplianceItemDescription" class="validation-error-message">
                        {{ validationErrors.ComplianceItemDescription }}
                      </span>
                    </div>
                    <div class="form-group">
                      <label>Is Risk</label>
                      <select v-model="editRow.IsRisk" class="compliance-select">
                        <option :value="true">Yes</option>
                        <option :value="false">No</option>
                      </select>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Possible Damage <span class="required-asterisk">*</span></label>
                      <input 
                        v-model="editRow.PossibleDamage" 
                        class="compliance-input"
                        :class="{ 'error-input': validationErrors.PossibleDamage }"
                        @blur="validateField('PossibleDamage')"
                      />
                      <span v-if="validationErrors.PossibleDamage" class="validation-error-message">
                        {{ validationErrors.PossibleDamage }}
                      </span>
                    </div>
                    <div class="form-group">
                      <label>Mitigation <span class="required-asterisk">*</span></label>
                      <input 
                        v-model="editRow.mitigation" 
                        class="compliance-input"
                        :class="{ 'error-input': validationErrors.mitigation }"
                        @blur="validateField('mitigation')"
                      />
                      <span v-if="validationErrors.mitigation" class="validation-error-message">
                        {{ validationErrors.mitigation }}
                      </span>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Criticality <span class="required-asterisk">*</span></label>
                      <select 
                        v-model="editRow.Criticality" 
                        class="compliance-select"
                        :class="{ 'error-input': validationErrors.Criticality }"
                        @blur="validateField('Criticality')"
                      >
                        <option value="">Select Criticality</option>
                        <option>High</option>
                        <option>Medium</option>
                        <option>Low</option>
                      </select>
                      <span v-if="validationErrors.Criticality" class="validation-error-message">
                        {{ validationErrors.Criticality }}
                      </span>
                    </div>
                    <div class="form-group">
                      <label>Mandatory/Optional <span class="required-asterisk">*</span></label>
                      <select 
                        v-model="editRow.MandatoryOptional" 
                        class="compliance-select"
                        :class="{ 'error-input': validationErrors.MandatoryOptional }"
                        @blur="validateField('MandatoryOptional')"
                      >
                        <option value="">Select Option</option>
                        <option>Mandatory</option>
                        <option>Optional</option>
                      </select>
                      <span v-if="validationErrors.MandatoryOptional" class="validation-error-message">
                        {{ validationErrors.MandatoryOptional }}
                      </span>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Manual/Automatic</label>
                      <select v-model="editRow.ManualAutomatic" class="compliance-select">
                        <option>Manual</option>
                        <option>Automatic</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Impact (1-10)</label>
                      <input type="number" v-model.number="editRow.Impact" min="1" max="10" step="0.1" class="compliance-input" />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Probability (1-10)</label>
                      <input type="number" v-model.number="editRow.Probability" min="1" max="10" step="0.1" class="compliance-input" />
                    </div>
                    <div class="form-group">
                      <label>Maturity Level</label>
                      <select v-model="editRow.MaturityLevel">
                        <option>Initial</option>
                        <option>Developing</option>
                        <option>Defined</option>
                        <option>Managed</option>
                        <option>Optimizing</option>
                      </select>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Potential Risk Scenarios</label>
                      <textarea v-model="editRow.PotentialRiskScenarios" class="compliance-input" placeholder="Describe potential risk scenarios" rows="3"></textarea>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Risk Type</label>
                      <div class="dropdown-container">
                        <input 
                          v-model="editRow.RiskType" 
                          @input="onSearchCategory($event, 'RiskType')"
                          @focus="onFocusCategory('RiskType')"
                          @blur="onBlurCategory('RiskType')"
                          class="compliance-input dropdown-input" 
                          placeholder="Type to search or add risk type..." 
                        />
                        <div v-if="showDropdown.RiskType" class="dropdown-menu">
                          <div v-if="filteredCategories.RiskType.length === 0" class="dropdown-item no-results">
                            No results found
                          </div>
                          <div v-else>
                            <div v-for="item in filteredCategories.RiskType" :key="item" 
                                 class="dropdown-item" @mousedown="selectCategoryEdit(item, 'RiskType')">
                              {{ item }}
                            </div>
                          </div>
                          <div v-if="editRow.RiskType && editRow.RiskType.trim() && !categoryExists('RiskType', editRow.RiskType)" 
                               class="dropdown-item add-new" @mousedown="addNewCategoryEdit('RiskType', editRow.RiskType)">
                            <i class="fas fa-plus"></i> Add "{{ editRow.RiskType }}"
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="form-group">
                      <label>Risk Category</label>
                      <div class="dropdown-container">
                        <input 
                          v-model="editRow.RiskCategory" 
                          @input="onSearchCategory($event, 'RiskCategory')"
                          @focus="onFocusCategory('RiskCategory')"
                          @blur="onBlurCategory('RiskCategory')"
                          class="compliance-input dropdown-input" 
                          placeholder="Type to search or add risk category..." 
                        />
                        <div v-if="showDropdown.RiskCategory" class="dropdown-menu">
                          <div v-if="filteredCategories.RiskCategory.length === 0" class="dropdown-item no-results">
                            No results found
                          </div>
                          <div v-else>
                            <div v-for="item in filteredCategories.RiskCategory" :key="item" 
                                 class="dropdown-item" @mousedown="selectCategoryEdit(item, 'RiskCategory')">
                              {{ item }}
                            </div>
                          </div>
                          <div v-if="editRow.RiskCategory && editRow.RiskCategory.trim() && !categoryExists('RiskCategory', editRow.RiskCategory)" 
                               class="dropdown-item add-new" @mousedown="addNewCategoryEdit('RiskCategory', editRow.RiskCategory)">
                            <i class="fas fa-plus"></i> Add "{{ editRow.RiskCategory }}"
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Risk Business Impact</label>
                      <div class="dropdown-container">
                        <input 
                          v-model="editRow.RiskBusinessImpact" 
                          @input="onSearchCategory($event, 'RiskBusinessImpact')"
                          @focus="onFocusCategory('RiskBusinessImpact')"
                          @blur="onBlurCategory('RiskBusinessImpact')"
                          class="compliance-input dropdown-input" 
                          placeholder="Type to search or add business impact..." 
                        />
                        <div v-if="showDropdown.RiskBusinessImpact" class="dropdown-menu">
                          <div v-if="filteredCategories.RiskBusinessImpact.length === 0" class="dropdown-item no-results">
                            No results found
                          </div>
                          <div v-else>
                            <div v-for="item in filteredCategories.RiskBusinessImpact" :key="item" 
                                 class="dropdown-item" @mousedown="selectCategoryEdit(item, 'RiskBusinessImpact')">
                              {{ item }}
                            </div>
                          </div>
                          <div v-if="editRow.RiskBusinessImpact && editRow.RiskBusinessImpact.trim() && !categoryExists('RiskBusinessImpact', editRow.RiskBusinessImpact)" 
                               class="dropdown-item add-new" @mousedown="addNewCategoryEdit('RiskBusinessImpact', editRow.RiskBusinessImpact)">
                            <i class="fas fa-plus"></i> Add "{{ editRow.RiskBusinessImpact }}"
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="form-group">
                      <label>Applicability</label>
                      <input v-model="editRow.Applicability" class="compliance-input" placeholder="Applicability" />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Approver</label>
                      <select v-model="editRow.reviewer_id" class="compliance-select" required>
                        <option disabled value="">Select Approver</option>
                        <option v-for="user in users" :key="user.UserId" :value="user.UserId">{{ user.UserName }}</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Approval Due Date</label>
                      <input type="date" v-model="editRow.ApprovalDueDate" class="compliance-input" required />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Versioning Type</label>
                      <select v-model="editRow.VersioningType" class="compliance-select" required>
                        <option value="Minor">Minor (e.g., 2.3 → 2.4)</option>
                        <option value="Major">Major (e.g., 2.3 → 3.0)</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Current Version</label>
                      <input :value="compliance.ComplianceVersion || '1.0'" class="compliance-input" readonly style="background-color: #f8f9fa; color: #6c757d;" />
                    </div>
                  </div>
                  <div class="form-actions">
                    <button type="submit">Save as New Version</button>
                    <button type="button" @click="cancelEdit">Cancel</button>
                  </div>
                </form>
              </td>
            </template>
            <!-- If in copy mode, show the copy form inline -->
            <template v-else-if="copyIdx === idx">
              <td colspan="4">
                <form @submit.prevent="confirmCopy" class="edit-form-grid">
                  <div class="form-row">
                    <div class="form-group">
                      <label>Description</label>
                      <input v-model="copyRow.ComplianceItemDescription" class="compliance-input" />
                    </div>
                    <div class="form-group">
                      <label>Is Risk</label>
                      <select v-model="copyRow.IsRisk" class="compliance-select">
                        <option :value="true">Yes</option>
                        <option :value="false">No</option>
                      </select>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Possible Damage</label>
                      <input v-model="copyRow.PossibleDamage" class="compliance-input" />
                    </div>
                    <div class="form-group">
                      <label>Mitigation</label>
                      <input v-model="copyRow.mitigation" class="compliance-input" />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Criticality</label>
                      <select v-model="copyRow.Criticality" class="compliance-select">
                        <option>High</option>
                        <option>Medium</option>
                        <option>Low</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Mandatory/Optional</label>
                      <select v-model="copyRow.MandatoryOptional" class="compliance-select">
                        <option>Mandatory</option>
                        <option>Optional</option>
                      </select>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Manual/Automatic</label>
                      <select v-model="copyRow.ManualAutomatic" class="compliance-select">
                        <option>Manual</option>
                        <option>Automatic</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Impact (1-10)</label>
                      <input type="number" v-model.number="copyRow.Impact" min="1" max="10" step="0.1" class="compliance-input" />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Probability (1-10)</label>
                      <input type="number" v-model.number="copyRow.Probability" min="1" max="10" step="0.1" class="compliance-input" />
                    </div>
                    <div class="form-group">
                      <label>Maturity Level</label>
                      <select v-model="copyRow.MaturityLevel">
                        <option>Initial</option>
                        <option>Developing</option>
                        <option>Defined</option>
                        <option>Managed</option>
                        <option>Optimizing</option>
                      </select>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Potential Risk Scenarios</label>
                      <textarea v-model="copyRow.PotentialRiskScenarios" class="compliance-input" placeholder="Describe potential risk scenarios" rows="3"></textarea>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Risk Type</label>
                      <div class="dropdown-container">
                        <input 
                          v-model="copyRow.RiskType" 
                          @input="onSearchCategoryC($event, 'RiskType')"
                          @focus="onFocusCategoryC('RiskType')"
                          @blur="onBlurCategoryC('RiskType')"
                          class="compliance-input dropdown-input" 
                          placeholder="Type to search or add risk type..." 
                        />
                        <div v-if="showDropdownC.RiskType" class="dropdown-menu">
                          <div v-if="filteredCategoriesC.RiskType.length === 0" class="dropdown-item no-results">
                            No results found
                          </div>
                          <div v-else>
                            <div v-for="item in filteredCategoriesC.RiskType" :key="item" 
                                 class="dropdown-item" @mousedown="selectCategoryCopy(item, 'RiskType')">
                              {{ item }}
                            </div>
                          </div>
                          <div v-if="copyRow.RiskType && copyRow.RiskType.trim() && !categoryExists('RiskType', copyRow.RiskType)" 
                               class="dropdown-item add-new" @mousedown="addNewCategoryCopy('RiskType', copyRow.RiskType)">
                            <i class="fas fa-plus"></i> Add "{{ copyRow.RiskType }}"
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="form-group">
                      <label>Risk Category</label>
                      <div class="dropdown-container">
                        <input 
                          v-model="copyRow.RiskCategory" 
                          @input="onSearchCategoryC($event, 'RiskCategory')"
                          @focus="onFocusCategoryC('RiskCategory')"
                          @blur="onBlurCategoryC('RiskCategory')"
                          class="compliance-input dropdown-input" 
                          placeholder="Type to search or add risk category..." 
                        />
                        <div v-if="showDropdownC.RiskCategory" class="dropdown-menu">
                          <div v-if="filteredCategoriesC.RiskCategory.length === 0" class="dropdown-item no-results">
                            No results found
                          </div>
                          <div v-else>
                            <div v-for="item in filteredCategoriesC.RiskCategory" :key="item" 
                                 class="dropdown-item" @mousedown="selectCategoryCopy(item, 'RiskCategory')">
                              {{ item }}
                            </div>
                          </div>
                          <div v-if="copyRow.RiskCategory && copyRow.RiskCategory.trim() && !categoryExists('RiskCategory', copyRow.RiskCategory)" 
                               class="dropdown-item add-new" @mousedown="addNewCategoryCopy('RiskCategory', copyRow.RiskCategory)">
                            <i class="fas fa-plus"></i> Add "{{ copyRow.RiskCategory }}"
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Risk Business Impact</label>
                      <div class="dropdown-container">
                        <input 
                          v-model="copyRow.RiskBusinessImpact" 
                          @input="onSearchCategoryC($event, 'RiskBusinessImpact')"
                          @focus="onFocusCategoryC('RiskBusinessImpact')"
                          @blur="onBlurCategoryC('RiskBusinessImpact')"
                          class="compliance-input dropdown-input" 
                          placeholder="Type to search or add business impact..." 
                        />
                        <div v-if="showDropdownC.RiskBusinessImpact" class="dropdown-menu">
                          <div v-if="filteredCategoriesC.RiskBusinessImpact.length === 0" class="dropdown-item no-results">
                            No results found
                          </div>
                          <div v-else>
                            <div v-for="item in filteredCategoriesC.RiskBusinessImpact" :key="item" 
                                 class="dropdown-item" @mousedown="selectCategoryCopy(item, 'RiskBusinessImpact')">
                              {{ item }}
                            </div>
                          </div>
                          <div v-if="copyRow.RiskBusinessImpact && copyRow.RiskBusinessImpact.trim() && !categoryExists('RiskBusinessImpact', copyRow.RiskBusinessImpact)" 
                               class="dropdown-item add-new" @mousedown="addNewCategoryCopy('RiskBusinessImpact', copyRow.RiskBusinessImpact)">
                            <i class="fas fa-plus"></i> Add "{{ copyRow.RiskBusinessImpact }}"
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="form-group">
                      <label>Applicability</label>
                      <input v-model="copyRow.Applicability" class="compliance-input" placeholder="Applicability" />
                    </div>
                  </div>
                  <div class="form-row framework-policy-row">
                    <div class="form-group">
                      <label>Framework</label>
                      <select v-model="copyTarget.frameworkId" disabled>
                        <option disabled value="">Select Framework</option>
                        <option v-for="fw in frameworks" :key="fw.id" :value="fw.id">{{ fw.name }}</option>
                      </select>
                      <small class="framework-locked-message">
                        <i class="fas fa-lock"></i> Framework is locked to match the source compliance
                      </small>
                    </div>
                    <div class="form-group">
                      <label>Policy</label>
                      <select v-model="copyTarget.policyId" :disabled="!copyTarget.frameworkId">
                        <option disabled value="">Select Policy</option>
                        <option v-for="p in copyPolicies" :key="p.id" :value="p.id">{{ p.name }}</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Sub Policy</label>
                      <select v-model="copyTarget.subPolicyId" :disabled="!copyTarget.policyId">
                        <option disabled value="">Select Sub Policy</option>
                        <option v-for="sp in filteredCopySubPolicies" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
                      </select>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>Approver</label>
                      <select v-model="copyRow.reviewer_id" class="compliance-select" required>
                        <option disabled value="">Select Approver</option>
                        <option v-for="user in users" :key="user.UserId" :value="user.UserId">{{ user.UserName }}</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>Approval Due Date</label>
                      <input type="date" v-model="copyRow.ApprovalDueDate" class="compliance-input" required />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>&nbsp;</label>
                      <div>
                        <button type="submit" :disabled="!canSaveCopy">Save Copy</button>
                        <button type="button" @click="cancelCopy">Cancel</button>
                      </div>
                    </div>
                    <div v-if="copyError" class="copy-error">{{ copyError }}</div>
                  </div>
                </form>
              </td>
            </template>
            <!-- Normal view: only 3 fields + actions -->
            <template v-else>
              <td>{{ compliance.ComplianceItemDescription || 'No description available' }}</td>
              <td>{{ compliance.PossibleDamage || 'No damage information' }}</td>
              <td>{{ formatMitigation(compliance.mitigation) }}</td>
              <td>
                <div class="action-btn-group">
                  <button @click="navigateToEdit(compliance)" title="Edit" class="action-btn edit-btn"><i class="fas fa-edit"></i></button>
                  <button @click="navigateToCopy(compliance)" title="Copy" class="action-btn copy-btn"><i class="fas fa-copy"></i></button>
                </div>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add PopupModal component at the end -->
    <PopupModal />
  </div>
</template>

<script>
import { PopupModal } from '../../modules/popup';
import PopupMixin from './mixins/PopupMixin';
import { CompliancePopups } from './utils/popupUtils';
import { complianceService } from '@/services/api';

export default {
  name: 'ComplianceTailoring',
  components: {
    PopupModal
  },
  mixins: [PopupMixin],
  data() {
    return {
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      frameworks: [],
      policies: [],
      subPolicies: [],
      subPolicyCompliances: [],
      loading: false,
      error: null,
      editIdx: null,
      editRow: {},
      // Copy inline state
      copyIdx: null,
      copyRow: {},
      copyTarget: { frameworkId: '', policyId: '', subPolicyId: '' },
      copyPolicies: [],
      copySubPolicies: [],
      copyError: '',
      sourceSubPolicyId: null, // Track source subpolicy
      users: [], // Add users array for storing the list of users
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
      searchTermsC: {
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
      showDropdownC: {
        BusinessUnitsCovered: false,
        RiskType: false,
        RiskCategory: false,
        RiskBusinessImpact: false
      }
    }
  },
  async created() {
    await this.loadFrameworks();
    await this.loadUsers(); // Load users when component is created
    await this.loadAllCategories(); // Load categories for dropdowns
  },
  watch: {
    selectedFramework(newValue) {
      if (newValue && newValue.id) {
        this.loadPolicies(newValue.id);
        this.selectedPolicy = '';
        this.selectedSubPolicy = '';
        this.policies = [];
        this.subPolicies = [];
        this.subPolicyCompliances = [];
      }
    },
    selectedPolicy(newValue) {
      if (newValue && newValue.id) {
        this.loadSubPolicies(newValue.id);
        this.selectedSubPolicy = '';
        this.subPolicies = [];
        this.subPolicyCompliances = [];
        
        // If editing or cloning, update the applicability from the selected policy
        if (this.editIdx !== null && this.editRow) {
          this.editRow.Applicability = newValue.applicability || '';
        }
        if (this.copyIdx !== null && this.copyRow) {
          this.copyRow.Applicability = newValue.applicability || '';
        }
      }
    },
    selectedSubPolicy: {
      handler: async function(newValue) {
        if (newValue && newValue.id) {
          await this.loadCompliances();
        } else {
          this.subPolicyCompliances = [];
        }
      },
      immediate: true
    },
    'copyTarget.frameworkId': 'copyTarget_frameworkId',
    'copyTarget.policyId': 'copyTarget_policyId'
  },
  computed: {
    canSaveCopy() {
      // Validate all required fields are filled and subpolicy is different from source
      return this.copyRow.ComplianceItemDescription &&
        this.copyTarget.frameworkId &&
        this.copyTarget.policyId &&
        this.copyTarget.subPolicyId &&
        this.copyTarget.subPolicyId !== this.sourceSubPolicyId && // Must be different subpolicy
        this.copyRow.Criticality &&
        this.copyRow.MandatoryOptional &&
        this.copyRow.ManualAutomatic &&
        this.copyRow.Impact && 
        this.copyRow.Probability && 
        this.copyRow.MaturityLevel &&
        this.copyRow.ApprovalDueDate &&
        this.copyRow.reviewer_id; // Add reviewer validation
      // Note: PotentialRiskScenarios, RiskType, RiskCategory, and RiskBusinessImpact are optional fields
    },
    filteredCopySubPolicies() {
      // Filter out the source subpolicy from the dropdown to prevent copying to same subpolicy
      if (!this.copySubPolicies || !this.sourceSubPolicyId) {
        return this.copySubPolicies || [];
      }
      
      return this.copySubPolicies.filter(sp => {
        return sp.id !== this.sourceSubPolicyId;
      });
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
    },
    filteredCategoriesC() {
      const filtered = {};
      Object.keys(this.categories).forEach(key => {
        const searchTerm = this.searchTermsC[key].toLowerCase();
        filtered[key] = this.categories[key].filter(item => 
          item.toLowerCase().includes(searchTerm)
        );
      });
      return filtered;
    }
  },
  methods: {
    // Validation functions
    validateTextInput(value) {
      const TEXT_PATTERN = /^[a-zA-Z0-9\s.,!?()[\]:;'"&%$#@+=\n\r\t_-]+$/;
      return TEXT_PATTERN.test(value);
    },
    
    validateAlphanumericInput(value) {
      const ALPHANUMERIC_PATTERN = /^[a-zA-Z0-9\s._-]+$/;
      return ALPHANUMERIC_PATTERN.test(value);
    },

    // Individual field validation
    validateField(fieldName, editData = this.editRow) {
      this.validationErrors = { ...this.validationErrors };
      delete this.validationErrors[fieldName];

      const value = editData[fieldName];

      switch (fieldName) {
        case 'ComplianceItemDescription':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Compliance Description is required';
          } else if (value.length > 2000) {
            this.validationErrors[fieldName] = 'Compliance Description must be less than 2000 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Compliance Description contains invalid characters';
          }
          break;

        case 'PossibleDamage':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Possible Damage is required';
          } else if (value.length > 2000) {
            this.validationErrors[fieldName] = 'Possible Damage must be less than 2000 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Possible Damage contains invalid characters';
          }
          break;

        case 'mitigation':
          if (!value || value.trim() === '') {
            this.validationErrors[fieldName] = 'Mitigation is required';
          } else if (value.length > 2000) {
            this.validationErrors[fieldName] = 'Mitigation must be less than 2000 characters';
          } else if (!this.validateTextInput(value)) {
            this.validationErrors[fieldName] = 'Mitigation contains invalid characters';
          }
          break;

        case 'Impact':
          if (value === null || value === undefined || value === '') {
            this.validationErrors[fieldName] = 'Impact is required';
          } else if (isNaN(value) || value < 1 || value > 10) {
            this.validationErrors[fieldName] = 'Impact must be between 1 and 10';
          }
          break;

        case 'Probability':
          if (value === null || value === undefined || value === '') {
            this.validationErrors[fieldName] = 'Probability is required';
          } else if (isNaN(value) || value < 1 || value > 10) {
            this.validationErrors[fieldName] = 'Probability must be between 1 and 10';
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
      }

      // Force reactivity update
      this.$forceUpdate();
    },

    // Validate all fields for edit form
    validateEditForm() {
      const requiredFields = [
        'ComplianceItemDescription', 'PossibleDamage', 'mitigation', 
        'Criticality', 'MandatoryOptional', 'ManualAutomatic',
        'Impact', 'Probability', 'MaturityLevel', 'ApprovalDueDate', 'reviewer_id'
      ];

      this.validationErrors = {};

      // Validate each required field
      requiredFields.forEach(field => {
        this.validateField(field);
      });

      // Return true if no validation errors
      return Object.keys(this.validationErrors).length === 0;
    },

    // Validate all fields for copy form
    validateCopyForm() {
      const requiredFields = [
        'ComplianceItemDescription', 'PossibleDamage', 'mitigation', 
        'Criticality', 'MandatoryOptional', 'ManualAutomatic',
        'Impact', 'Probability', 'MaturityLevel', 'ApprovalDueDate', 'reviewer_id'
      ];

      this.validationErrors = {};

      // Validate each required field
      requiredFields.forEach(field => {
        this.validateField(field, this.copyRow);
      });

      // Return true if no validation errors
      return Object.keys(this.validationErrors).length === 0;
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
        this.error = 'Failed to load frameworks';
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
          applicability: p.Applicability || '' // Store the Applicability field
        }));
      } catch (error) {
        this.error = 'Failed to load policies';
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
        this.error = 'Failed to load sub-policies';
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        console.log('Users API response:', response);
        
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users;
          console.log('Loaded users:', this.users);
        } else {
          console.error('Invalid users data received:', response.data);
          this.error = 'Failed to load approvers';
        }
      } catch (error) {
        console.error('Failed to load users:', error);
        this.error = 'Failed to load approvers. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    startEdit(idx, compliance) {
      this.editIdx = idx;
      
      // Get the policy's applicability if available
      const policyApplicability = this.selectedPolicy ? this.selectedPolicy.applicability : '';
      
      this.editRow = { 
        ...compliance,
        // Set default approval due date if not present
        ApprovalDueDate: compliance.ApprovalDueDate || this.getDefaultDueDate(),
        reviewer_id: compliance.reviewer_id || (this.users.length > 0 ? this.users[0].UserId : ''), // Set default reviewer
        // Set applicability from compliance or use policy's applicability as default
        Applicability: compliance.Applicability || policyApplicability || '',
        // Initialize new risk fields
        PotentialRiskScenarios: compliance.PotentialRiskScenarios || '',
        RiskType: compliance.RiskType || '',
        RiskCategory: compliance.RiskCategory || '',
        RiskBusinessImpact: compliance.RiskBusinessImpact || '',
        // Set default versioning type
        VersioningType: compliance.VersioningType || 'Major'
      };
    },
    cancelEdit() {
      this.editIdx = null;
      this.editRow = {};
    },
    async saveEdit(compliance) {
      // Validate all fields before proceeding
      if (!this.validateEditForm()) {
        this.showErrorPopup('Please correct the errors in the form before submitting');
        return;
      }

      try {
        this.loading = true;
        await this.$nextTick();
        
        // Use the popup confirmation instead of the confirm dialog
        this.confirmEditCompliance(compliance, async () => {
        // Always set new versions to Under Review and Inactive
        // The backend will calculate the new version based on VersioningType
        console.log('=== TAILORING VERSION DEBUG ===');
        console.log('Original compliance version:', compliance.ComplianceVersion);
        console.log('Selected versioning type:', this.editRow.VersioningType);
        
        this.editRow = {
          ...this.editRow,
          Status: 'Under Review',
          ActiveInactive: 'Inactive',
          PreviousComplianceVersionId: compliance.ComplianceId,
          ApprovalDueDate: this.editRow.ApprovalDueDate, // Ensure ApprovalDueDate is included
          reviewer_id: this.editRow.reviewer_id, // Include the selected reviewer ID
          VersioningType: this.editRow.VersioningType // Include the versioning type
        };
        
        // Remove ComplianceVersion from the data so backend calculates it
        delete this.editRow.ComplianceVersion;
        
        console.log('Edit row data being sent:', this.editRow);
        console.log('=== END TAILORING DEBUG ===');
        
        console.log("Creating new compliance version:", this.editRow);
        
        // Use the complianceService instead of direct axios
        const response = await complianceService.editCompliance(compliance.ComplianceId, this.editRow);
        console.log("Edited compliance response:", response);
        
        if (response.data && response.data.success) {
            // Show success popup instead of alert
            CompliancePopups.complianceUpdated({
              ComplianceId: response.data.compliance_id || compliance.ComplianceId,
              ComplianceVersion: response.data.version || 'New Version'
            });
        }
        
        this.editIdx = null;
        this.editRow = {};
        
        // Refresh compliances
        await this.refreshCurrentData();
        });
        this.loading = false;
      } catch (error) {
        console.error('Edit error:', error);
        this.showErrorPopup('Failed to save new version: ' + (error.response?.data?.message || error.message));
        this.loading = false;
      }
    },
    // Copy modal logic
    async     openCopyInline(idx, compliance) {
      this.editIdx = null; // Cancel edit mode if active
      this.copyIdx = idx;
      
      // Get the policy's applicability if available
      const policyApplicability = this.selectedPolicy ? this.selectedPolicy.applicability : '';
      
      this.copyRow = { 
        ...compliance,
        // Set default approval due date if not present
        ApprovalDueDate: compliance.ApprovalDueDate || this.getDefaultDueDate(),
        reviewer_id: compliance.reviewer_id || (this.users.length > 0 ? this.users[0].UserId : ''), // Set default reviewer
        // Set applicability from compliance or use policy's applicability as default
        Applicability: compliance.Applicability || policyApplicability || '',
        // Initialize new risk fields
        PotentialRiskScenarios: compliance.PotentialRiskScenarios || '',
        RiskType: compliance.RiskType || '',
        RiskCategory: compliance.RiskCategory || '',
        RiskBusinessImpact: compliance.RiskBusinessImpact || ''
      };
      this.sourceSubPolicyId = this.selectedSubPolicy.id; // Store the source subpolicy ID
      
      // Initialize the target with current framework (locked) and reset policy/subpolicy selection
      this.copyTarget = { 
        frameworkId: this.selectedFramework.id, 
        policyId: '', 
        subPolicyId: '' 
      };
      
      // Pre-load policies for the selected framework
      if (this.copyTarget.frameworkId) {
        await this.copyTarget_frameworkId(this.copyTarget.frameworkId);
      }
      
      // Pre-load subpolicies for the selected policy
      if (this.copyTarget.policyId) {
        await this.copyTarget_policyId(this.copyTarget.policyId);
      }
      
      this.copyError = '';
    },
    cancelCopy() {
      this.copyIdx = null;
      this.copyRow = {};
      this.sourceSubPolicyId = null; // Reset source subpolicy ID
      this.copyTarget = { frameworkId: '', policyId: '', subPolicyId: '' };
      this.copyPolicies = [];
      this.copySubPolicies = [];
      this.copyError = '';
    },
    async confirmCopy() {
      if (!this.canSaveCopy) {
        this.copyError = 'Please fill all required fields and select a destination.';
        return;
      }

      // Validate all fields before proceeding
      if (!this.validateCopyForm()) {
        this.copyError = 'Please correct the errors in the form before submitting.';
        return;
      }
      
      try {
        this.loading = true;
        this.copyError = '';
        await this.$nextTick();

        const cloneData = {
          ...this.copyRow,
          Impact: String(this.copyRow.Impact),
          Probability: String(this.copyRow.Probability),
          target_subpolicy_id: this.copyTarget.subPolicyId,
          Status: 'Under Review',
          ActiveInactive: 'Inactive',
          PermanentTemporary: this.copyRow.PermanentTemporary || 'Permanent',
          ComplianceVersion: '1.0',
          ApprovalDueDate: this.copyRow.ApprovalDueDate, // Ensure ApprovalDueDate is included
          reviewer_id: this.copyRow.reviewer_id, // Include reviewer_id
          Applicability: this.copyRow.Applicability // Include Applicability
        };

        // Use confirm popup for cloning
        this.confirmCloneCompliance({
          ComplianceItemDescription: this.copyRow.ComplianceItemDescription
        }, async () => {
        const response = await complianceService.cloneCompliance(
          this.subPolicyCompliances[this.copyIdx].ComplianceId,
          cloneData
        );

        if (response.data.success) {
          this.cancelCopy();
            // Show success popup instead of alert
            CompliancePopups.complianceCloned({
              ComplianceId: response.data.compliance_id,
              ComplianceVersion: '1.0'
            });
          // Refresh compliances
          await this.refreshCurrentData();
        } else {
          this.copyError = response.data.message || 'Failed to copy compliance';
            this.showErrorPopup(this.copyError);
        }
        });
      } catch (error) {
        console.error('Copy error:', error);
        this.copyError = 'Failed to copy compliance: ' + (error.response?.data?.message || error.message);
        this.showErrorPopup(this.copyError);
      } finally {
        this.loading = false;
      }
    },
    // Watchers for copy dropdowns
    async copyTarget_frameworkId(newValue) {
      if (newValue) {
        try {
          const response = await complianceService.getPolicies(newValue);
          if (response.data && response.data.data) {
            this.copyPolicies = response.data.data.map(p => ({ 
              id: p.PolicyId, 
              name: p.PolicyName,
              applicability: p.Applicability || '' // Store the Applicability field
            }));
          } else {
            console.error("Unexpected response format from getPolicies:", response);
            this.copyPolicies = [];
          }
          this.copyTarget.policyId = '';
          this.copyTarget.subPolicyId = '';
          this.copySubPolicies = [];
        } catch (error) {
          console.error("Error fetching policies for framework:", error);
          this.copyError = "Failed to load policies for the selected framework";
          this.copyPolicies = [];
        }
      }
    },
    async copyTarget_policyId(newValue) {
      if (newValue) {
        try {
          // Load subpolicies for the selected policy
          const response = await complianceService.getSubPolicies(newValue);
          if (response.data && response.data.data) {
            this.copySubPolicies = response.data.data.map(sp => ({ id: sp.SubPolicyId, name: sp.SubPolicyName }));
          } else {
            console.error("Unexpected response format from getSubPolicies:", response);
            this.copySubPolicies = [];
          }
          this.copyTarget.subPolicyId = '';
          
          // Find the selected policy to get its applicability
          const selectedPolicy = this.copyPolicies.find(p => p.id === newValue);
          if (selectedPolicy && selectedPolicy.applicability) {
            // Update the applicability in the copy form
            this.copyRow.Applicability = selectedPolicy.applicability;
          }
        } catch (error) {
          console.error("Error fetching subpolicies for policy:", error);
          this.copyError = "Failed to load subpolicies for the selected policy";
          this.copySubPolicies = [];
        }
      }
    },
    async refreshCurrentData() {
      try {
        this.loading = true;
        this.error = null;
        
        await this.loadFrameworks();
        await this.loadUsers(); // Also refresh users list
        
        if (this.selectedFramework && this.selectedFramework.id) {
          await this.loadPolicies(this.selectedFramework.id);
          
          if (this.selectedPolicy && this.selectedPolicy.id) {
            await this.loadSubPolicies(this.selectedPolicy.id);
            
            if (this.selectedSubPolicy && this.selectedSubPolicy.id) {
              await this.loadCompliances();
            }
          }
        }
      } catch (error) {
        this.error = 'Failed to refresh data';
        console.error('Error refreshing data:', error);
      } finally {
        this.loading = false;
      }
    },
    async loadCompliances() {
      try {
        this.loading = true;
        this.subPolicyCompliances = [];
        if (this.selectedSubPolicy && this.selectedSubPolicy.id) {
          console.log('Loading compliances for subpolicy ID:', this.selectedSubPolicy.id);
          
          // Use the compliance service to get the data
          const response = await complianceService.getCompliancesBySubPolicy(this.selectedSubPolicy.id);
          console.log('Compliances API response:', response);
          
          // Process the response data based on its structure
          if (response.data && response.data.success && Array.isArray(response.data.data)) {
            // Handle nested array structure
            const flattenedCompliances = [];
            
            // Check if we have a nested array or a flat array
            if (response.data.data.length > 0 && Array.isArray(response.data.data[0])) {
              // It's a nested array structure - flatten it
              response.data.data.forEach(group => {
                if (Array.isArray(group) && group.length > 0) {
                  flattenedCompliances.push(group[0]); // Take the most recent version
                }
              });
              this.subPolicyCompliances = flattenedCompliances;
            } else {
              // It's already a flat array
              this.subPolicyCompliances = response.data.data;
            }
          } else if (response.data && Array.isArray(response.data)) {
            // Direct array in response
            this.subPolicyCompliances = response.data;
          } else if (response.data && typeof response.data === 'object') {
            // Try to extract data from response object
            if (response.data.data && Array.isArray(response.data.data)) {
              this.subPolicyCompliances = response.data.data;
            } else if (response.data.compliances && Array.isArray(response.data.compliances)) {
              this.subPolicyCompliances = response.data.compliances;
            } else {
              // Try to extract compliances from object values
              const extractedData = Object.values(response.data).filter(
                item => item && typeof item === 'object' && item.ComplianceId
              );
              
              if (extractedData.length > 0) {
                this.subPolicyCompliances = extractedData;
              } else {
                console.warn('Could not extract compliances from response:', response.data);
                this.subPolicyCompliances = [];
              }
            }
          } else {
            console.warn('Unexpected response format:', response);
            this.subPolicyCompliances = [];
          }
          
          console.log('Processed compliances:', this.subPolicyCompliances);
        }
      } catch (error) {
        this.error = 'Failed to load compliances';
        // Show error popup
        this.showErrorPopup('Failed to load compliances: ' + (error.response?.data?.message || error.message));
        console.error('Error loading compliances:', error);
      } finally {
        this.loading = false;
      }
    },
    // Format date
    formatDate(dateString) {
      if (!dateString) return '';
      
      try {
        // Handle different date formats
        let date;
        if (typeof dateString === 'string') {
          // Try different date formats
          if (dateString.includes('T')) {
            // ISO format
            date = new Date(dateString);
          } else if (dateString.includes('-')) {
            // YYYY-MM-DD format
            const parts = dateString.split(' ')[0].split('-');
            date = new Date(parts[0], parts[1] - 1, parts[2]);
          } else if (dateString.includes('/')) {
            // MM/DD/YYYY format
            const parts = dateString.split(' ')[0].split('/');
            date = new Date(parts[2], parts[0] - 1, parts[1]);
          } else {
            date = new Date(dateString);
          }
        } else {
          date = new Date(dateString);
        }
        
        // Format the date
        return date.toLocaleString();
      } catch (e) {
        console.error('Error formatting date:', e);
        return dateString; // Return the original string if parsing fails
      }
    },
    // Add a new method to view compliance details in a popup
    viewComplianceDetails(compliance) {
      CompliancePopups.showComplianceInfo(compliance);
    },
    // Helper method to generate a default due date (7 days from now)
    getDefaultDueDate() {
      const date = new Date();
      date.setDate(date.getDate() + 7);
      return date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
    },
    navigateToEdit(compliance) {
      // Navigate to the edit page with the compliance ID
      this.$router.push(`/compliance/edit/${compliance.ComplianceId}`);
    },
    navigateToCopy(compliance) {
      // Navigate to the copy page with the compliance ID
      this.$router.push(`/compliance/copy/${compliance.ComplianceId}`);
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

    // Edit form category methods
    onSearchCategory(event, source) {
      const value = event.target.value;
      this.searchTerms[source] = value;
      this.showDropdown[source] = true;
    },

    onFocusCategory(source) {
      const currentValue = this.editRow[source];
      this.searchTerms[source] = currentValue || '';
      this.showDropdown[source] = true;
    },

    onBlurCategory(source) {
      setTimeout(() => {
        this.showDropdown[source] = false;
      }, 200);
    },

    selectCategoryEdit(value, source) {
      this.editRow[source] = value;
      this.searchTerms[source] = value;
      this.showDropdown[source] = false;
    },

    async addNewCategoryEdit(source, value) {
      try {
        const response = await fetch('/api/categories/add/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: source, value: value.trim() })
        });

        const data = await response.json();
        if (data.success) {
          if (!this.categories[source].includes(value.trim())) {
            this.categories[source].push(value.trim());
            this.categories[source].sort();
          }
          this.editRow[source] = value.trim();
          this.searchTerms[source] = value.trim();
          this.showDropdown[source] = false;
          this.showSuccessPopup(`Successfully added "${value.trim()}" to ${source.replace(/([A-Z])/g, ' $1').trim()}`);
        } else {
          this.showErrorPopup(`Failed to add category: ${data.message}`);
        }
      } catch (error) {
        console.error('Error adding category:', error);
        this.showErrorPopup('Error adding new category. Please try again.');
      }
    },

    // Copy form category methods
    onSearchCategoryC(event, source) {
      const value = event.target.value;
      this.searchTermsC[source] = value;
      this.showDropdownC[source] = true;
    },

    onFocusCategoryC(source) {
      const currentValue = this.copyRow[source];
      this.searchTermsC[source] = currentValue || '';
      this.showDropdownC[source] = true;
    },

    onBlurCategoryC(source) {
      setTimeout(() => {
        this.showDropdownC[source] = false;
      }, 200);
    },

    selectCategoryCopy(value, source) {
      this.copyRow[source] = value;
      this.searchTermsC[source] = value;
      this.showDropdownC[source] = false;
    },

    async addNewCategoryCopy(source, value) {
      try {
        const response = await fetch('/api/categories/add/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: source, value: value.trim() })
        });

        const data = await response.json();
        if (data.success) {
          if (!this.categories[source].includes(value.trim())) {
            this.categories[source].push(value.trim());
            this.categories[source].sort();
          }
          this.copyRow[source] = value.trim();
          this.searchTermsC[source] = value.trim();
          this.showDropdownC[source] = false;
          this.showSuccessPopup(`Successfully added "${value.trim()}" to ${source.replace(/([A-Z])/g, ' $1').trim()}`);
        } else {
          this.showErrorPopup(`Failed to add category: ${data.message}`);
        }
      } catch (error) {
        console.error('Error adding category:', error);
        this.showErrorPopup('Error adding new category. Please try again.');
      }
    },

    categoryExists(source, value) {
      return this.categories[source].some(item => 
        item.toLowerCase() === value.toLowerCase()
      );
    },

    // Add method to format mitigation display
    formatMitigation(mitigation) {
      if (!mitigation) {
        return 'No mitigation details';
      }
      
      // Check if it's JSON format
      if (typeof mitigation === 'string' && (mitigation.startsWith('[') || mitigation.startsWith('{'))) {
        try {
          const parsed = JSON.parse(mitigation);
          
          // If it's an array of steps
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
@import './ComplianceTailoring.css';

.rejected-compliances-section {
  margin: 2rem 24px;
  background-color: #fff8f8;
  padding: 1.5rem;
  border-radius: 8px;
  border: 2px solid #e6d0d0;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.1);
  position: relative;
}

.rejected-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #e6d0d0;
}

.rejected-header h3 {
  color: #c00;
  font-size: 1.2rem;
  font-weight: 600;
}

.refresh-rejected-btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid #dc3545;
  background-color: #fff;
  color: #dc3545;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.refresh-rejected-btn:hover {
  background-color: #dc3545;
  color: white;
}

.rejected-loading {
  margin-top: 1rem;
  text-align: center;
  color: #666;
}

.no-rejected {
  text-align: center;
  color: #666;
}

.rejected-compliances-list {
  margin-top: 1rem;
}

.rejected-compliance-item {
  background-color: white;
  border: 1px solid #e0e0e0;
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 4px;
  position: relative;
}

.rejected-item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.badge.rejected {
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.rejected-item-details {
  padding-left: 0.5rem;
  border-left: 2px solid #f0f0f0;
}

.meta-info {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.criticality {
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-weight: 500;
}

.criticality.high {
  background: #fee;
  color: #c00;
}

.criticality.medium {
  background: #ffd;
  color: #960;
}

.criticality.low {
  background: #efe;
  color: #060;
}

.rejected-date {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #d32f2f;
}

.rejection-reason {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #fff0f0;
  border-left: 3px solid #ff3333;
  border-radius: 0 4px 4px 0;
  color: #c00;
  font-size: 0.9rem;
}

.edit-rejected-btn {
  margin-top: 1rem;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.edit-rejected-btn:hover {
  background-color: #eeeeee;
  border-color: #ccc;
}

.edit-rejected-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.edit-rejected-content {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.resubmit-btn {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1rem;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.framework-locked-message {
  display: block;
  margin-top: 0.5rem;
  color: #64748b;
  font-size: 0.875rem;
  font-style: italic;
}

.framework-locked-message i {
  margin-right: 0.5rem;
  color: #f59e0b;
}
</style> 