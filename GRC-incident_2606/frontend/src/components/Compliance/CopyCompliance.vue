<template>
  <div class="create-compliance-container">
    <!-- Header section -->
    <div class="compliance-header">
      <h2><i class="fas fa-copy"></i> Template Compliance Record</h2>
      <p>Create a new compliance item based on an existing one</p>
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

    <!-- Target selection -->
    <div class="field-group selection-fields">
      <div class="field-group-title"><i class="fas fa-crosshairs"></i> Select Target Location</div>
      <div class="row-fields">
        <div class="compliance-field">
          <label for="framework"><i class="fas fa-layer-group"></i> Framework</label>
          <select 
            id="framework" 
            v-model="targetFrameworkId" 
            class="compliance-select" 
            required 
            disabled
            title="Framework is locked to the source compliance framework"
          >
            <option value="" disabled>Select Framework</option>
            <option v-for="fw in frameworks" :key="fw.id" :value="fw.id">{{ fw.name }}</option>
          </select>
          <small class="framework-locked-message">
            <i class="fas fa-lock"></i> Framework is locked to match the source compliance
          </small>
        </div>
        
        <div class="compliance-field">
          <label for="policy"><i class="fas fa-file-contract"></i> Policy</label>
          <select 
            id="policy" 
            v-model="targetPolicyId" 
            class="compliance-select" 
            required 
            :disabled="!targetFrameworkId"
            title="Select the target policy"
          >
            <option value="" disabled>Select Policy</option>
            <option v-for="p in policies" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        
        <div class="compliance-field">
          <label for="subpolicy"><i class="fas fa-file-alt"></i> Sub Policy</label>
          <select 
            id="subpolicy" 
            v-model="targetSubPolicyId" 
            class="compliance-select" 
            required 
            :disabled="!targetPolicyId"
            title="Select the target sub-policy"
          >
            <option value="" disabled>Select Sub Policy</option>
            <option v-for="sp in subPolicies" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Copy form -->
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
              title="A new identifier will be generated"
              disabled
            />
            <small>A new identifier will be generated</small>
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
            <label><i class="fas fa-heading"></i> Compliance Title</label>
            <input 
              v-model="compliance.ComplianceTitle" 
              class="compliance-input" 
              placeholder="Enter compliance title"
              required 
              title="Enter the title of the compliance item"
            />
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-tag"></i> Compliance Type</label>
            <input 
              v-model="compliance.ComplianceType" 
              class="compliance-input" 
              placeholder="Enter compliance type"
              title="Type of compliance (e.g. Regulatory, Internal, Security)"
            />
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-align-left"></i> Compliance Description</label>
          <textarea
            v-model="compliance.ComplianceItemDescription" 
            class="compliance-input" 
            placeholder="Compliance Description"
            required 
            rows="3"
            title="Detailed description of the compliance requirement"
          ></textarea>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-crosshairs"></i> Scope</label>
          <textarea 
            v-model="compliance.Scope" 
            class="compliance-input" 
            placeholder="Enter scope information"
            rows="3"
            title="Define the boundaries and extent of the compliance requirement"
          ></textarea>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-bullseye"></i> Objective</label>
          <textarea 
            v-model="compliance.Objective" 
            class="compliance-input" 
            placeholder="Enter objective information"
            rows="3"
            title="The goal or purpose of this compliance requirement"
          ></textarea>
        </div>
        
        <!-- Business Units -->
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-building"></i> Business Units Covered</label>
            <input 
              v-model="compliance.BusinessUnitsCovered" 
              class="compliance-input" 
              placeholder="Enter business units covered"
              title="Departments or business units affected by this compliance"
            />
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
          <label><i class="fas fa-bomb"></i> Possible Damage</label>
          <textarea
            v-model="compliance.PossibleDamage" 
            class="compliance-input" 
            placeholder="Possible Damage"
            rows="3"
            :required="compliance.IsRisk"
            title="Potential damage that could occur if this risk materializes" 
          ></textarea>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-first-aid"></i> Mitigation</label>
          <textarea
            v-model="compliance.mitigation" 
            class="compliance-input" 
            placeholder="Mitigation"
            rows="3"
            title="Actions taken to reduce the risk or its impact" 
          ></textarea>
        </div>
        
        <div class="compliance-field full-width">
          <label><i class="fas fa-chess"></i> Potential Risk Scenarios</label>
          <textarea 
            v-model="compliance.PotentialRiskScenarios" 
            class="compliance-input" 
            placeholder="Describe potential risk scenarios"
            rows="3"
            title="Describe scenarios where this risk could materialize"
          ></textarea>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-exclamation-circle"></i> Risk Type</label>
            <select 
              v-model="compliance.RiskType" 
              class="compliance-select" 
              title="Type of risk (e.g. Operational, Financial, Strategic, Compliance, Reputational)"
            >
              <option value="" disabled>Select Risk Type</option>
              <option value="Operational Risk">Operational Risk</option>
              <option value="Financial Risk">Financial Risk</option>
              <option value="Strategic Risk">Strategic Risk</option>
              <option value="Compliance Risk">Compliance Risk</option>
              <option value="Reputational Risk">Reputational Risk</option>
              <option value="Technology Risk">Technology Risk</option>
              <option value="Market Risk">Market Risk</option>
              <option value="Credit Risk">Credit Risk</option>
              <option value="Legal Risk">Legal Risk</option>
              <option value="Environmental Risk">Environmental Risk</option>
            </select>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-list-alt"></i> Risk Category</label>
            <select 
              v-model="compliance.RiskCategory" 
              class="compliance-select" 
              title="Category of risk (e.g. People, Process, Technology, External)"
            >
              <option value="" disabled>Select Risk Category</option>
              <option value="People Risk">People Risk</option>
              <option value="Process Risk">Process Risk</option>
              <option value="Technology Risk">Technology Risk</option>
              <option value="External Risk">External Risk</option>
              <option value="Information Risk">Information Risk</option>
              <option value="Physical Risk">Physical Risk</option>
              <option value="Systems Risk">Systems Risk</option>
              <option value="Vendor Risk">Vendor Risk</option>
              <option value="Regulatory Risk">Regulatory Risk</option>
              <option value="Fraud Risk">Fraud Risk</option>
            </select>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-chart-line"></i> Risk Business Impact</label>
            <select 
              v-model="compliance.RiskBusinessImpact" 
              class="compliance-select" 
              title="How this risk impacts business operations"
            >
              <option value="" disabled>Select Business Impact</option>
              <option value="Revenue Loss">Revenue Loss</option>
              <option value="Customer Impact">Customer Impact</option>
              <option value="Operational Disruption">Operational Disruption</option>
              <option value="Brand Damage">Brand Damage</option>
              <option value="Regulatory Penalties">Regulatory Penalties</option>
              <option value="Legal Costs">Legal Costs</option>
              <option value="Data Loss">Data Loss</option>
              <option value="Service Downtime">Service Downtime</option>
              <option value="Productivity Loss">Productivity Loss</option>
              <option value="Compliance Violations">Compliance Violations</option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- Compliance classification fields - grouped together -->
      <div class="field-group classification-fields">
        <div class="field-group-title"><i class="fas fa-tasks"></i> Classification</div>
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-exclamation"></i> Criticality</label>
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
            <label><i class="fas fa-gavel"></i> Mandatory/Optional</label>
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
            <label><i class="fas fa-cogs"></i> Manual/Automatic</label>
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
            <label><i class="fas fa-thermometer-half"></i> Severity Rating (1-10)</label>
            <input 
              type="number" 
              v-model.number="compliance.Impact" 
              @input="validateImpact"
              class="compliance-input" 
              step="0.1" 
              min="1" 
              max="10"
              required
              title="Rate the Severity Rating from 1 (lowest) to 10 (highest)"
            />
            <span v-if="impactError" class="validation-error">
              Severity Rating must be between 1 and 10
            </span>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-percentage"></i> Probability (1-10)</label>
            <input 
              type="number" 
              v-model.number="compliance.Probability" 
              @input="validateProbability"
              class="compliance-input" 
              step="0.1" 
              min="1" 
              max="10"
              required
              title="Rate the probability from 1 (lowest) to 10 (highest)"
            />
            <span v-if="probabilityError" class="validation-error">
              Probability must be between 1 and 10
            </span>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-chart-bar"></i> Maturity Level</label>
            <select 
              v-model="compliance.MaturityLevel" 
              class="compliance-select"
              title="Current maturity level of this compliance item"
            >
              <option value="Initial">Initial</option>
              <option value="Developing">Developing</option>
              <option value="Defined">Defined</option>
              <option value="Managed">Managed</option>
              <option value="Optimizing">Optimizing</option>
            </select>
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-clock"></i> Permanent/Temporary</label>
            <select 
              v-model="compliance.PermanentTemporary" 
              class="compliance-select"
              title="Whether this compliance requirement is permanent or temporary"
            >
              <option value="Permanent">Permanent</option>
              <option value="Temporary">Temporary</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Source Information fields - read-only display -->
      <div class="field-group">
        <div class="field-group-title"><i class="fas fa-info"></i> Source Compliance Information</div>
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-flag"></i> Source Status</label>
            <input 
              :value="compliance.Status" 
              class="compliance-input" 
              readonly
              title="Status of the source compliance item"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-code-branch"></i> Source Version</label>
            <input 
              :value="compliance.ComplianceVersion || '1.0'" 
              class="compliance-input" 
              readonly
              title="Version of the source compliance item"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label><i class="fas fa-user"></i> Source Created By</label>
            <input 
              :value="compliance.CreatedByName || 'System'" 
              class="compliance-input" 
              readonly
              title="Person who created the source compliance item"
              style="background-color: #f8f9fa; color: #6c757d;"
            />
          </div>
          
          <div class="compliance-field">
            <label><i class="fas fa-calendar"></i> Source Created Date</label>
            <input 
              :value="compliance.CreatedByDate || 'Not specified'" 
              class="compliance-input" 
              readonly
              title="Date when the source compliance item was created"
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
            <label><i class="fas fa-user-check"></i> Assign Reviewer</label>
            <select 
              v-model="compliance.reviewer_id" 
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
            <label><i class="fas fa-calendar-check"></i> Approval Due Date</label>
            <input 
              type="date" 
              v-model="compliance.ApprovalDueDate" 
              class="compliance-input" 
              required
              :min="minDate"
              title="Deadline for reviewing this compliance item" 
            />
          </div>
        </div>
      </div>
    </div>
    
    <div class="compliance-submit-container">
      <button 
        class="compliance-submit-btn" 
        @click="submitCopy"
        :disabled="loading || !canSaveCopy"
      >
        <span v-if="loading">Saving...</span>
        <span v-else><i class="fas fa-copy"></i> Save Copy</span>
      </button>
      <button 
        class="compliance-cancel-btn" 
        @click="cancelCopy"
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
  name: 'CopyCompliance',
  data() {
    return {
      compliance: null,
      users: [],
      frameworks: [],
      policies: [],
      subPolicies: [],
      targetFrameworkId: '',
      targetPolicyId: '',
      targetSubPolicyId: '',
      loading: false,
      error: null,
      successMessage: null,
      impactError: false,
      probabilityError: false,
      originalComplianceId: null,
      sourceSubPolicyId: null,
      sourceFrameworkInfo: null
    }
  },
  computed: {
    minDate() {
      // Get today's date in YYYY-MM-DD format for setting minimum date
      const today = new Date();
      return today.toISOString().split('T')[0];
    },
    canSaveCopy() {
      // Comprehensive validation for all required fields
      const requiredBasicFields = 
        this.compliance && 
        this.compliance.ComplianceTitle &&
        this.compliance.ComplianceItemDescription &&
        this.compliance.ComplianceType &&
        this.compliance.Scope &&
        this.compliance.Objective &&
        this.compliance.BusinessUnitsCovered &&
        this.targetFrameworkId &&
        this.targetPolicyId &&
        this.targetSubPolicyId &&
        this.targetSubPolicyId !== this.sourceSubPolicyId && // Must be different subpolicy
        this.compliance.Criticality &&
        this.compliance.MandatoryOptional &&
        this.compliance.ManualAutomatic &&
        this.compliance.Impact && 
        this.compliance.Probability && 
        this.compliance.MaturityLevel &&
        this.compliance.PermanentTemporary &&
        this.compliance.ApprovalDueDate &&
        this.compliance.reviewer_id;

      // Additional validation for risk fields if IsRisk is true
      const riskFieldsValid = !this.compliance || !this.compliance.IsRisk || (
        this.compliance.PossibleDamage &&
        this.compliance.mitigation &&
        this.compliance.PotentialRiskScenarios &&
        this.compliance.RiskType &&
        this.compliance.RiskCategory &&
        this.compliance.RiskBusinessImpact
      );

      return requiredBasicFields && riskFieldsValid;
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
    await Promise.all([
      this.loadUsers(),
      this.loadComplianceFrameworkInfo(complianceId),
      this.loadComplianceData(complianceId)
    ]);
    await this.loadFrameworks();
  },
  watch: {
    targetPolicyId(newValue) {
      if (newValue) {
        this.loadSubPolicies(newValue);
        this.targetSubPolicyId = '';
        
        // Set the applicability from the selected policy
        const selectedPolicy = this.policies.find(p => p.id === newValue);
        if (selectedPolicy && selectedPolicy.applicability && this.compliance) {
          this.compliance.Applicability = selectedPolicy.applicability;
        }
      }
    }
  },
  methods: {
    // Validation functions with proper regex patterns
    validateTextInput(value) {
      // Fixed regex pattern without unnecessary escapes
      const TEXT_PATTERN = /^[a-zA-Z0-9\s.,!?()[\]:;'"&%$#@+=\n\r\t_-]+$/;
      return TEXT_PATTERN.test(value);
    },
    
    validateAlphanumericInput(value) {
      // Fixed regex pattern without unnecessary escapes  
      const ALPHANUMERIC_PATTERN = /^[a-zA-Z0-9\s._-]+$/;
      return ALPHANUMERIC_PATTERN.test(value);
    },
    
    async loadComplianceData(complianceId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceById(complianceId);
        
        if (response.data && response.data.success) {
          this.compliance = response.data.data;
          this.sourceSubPolicyId = this.compliance.SubPolicy;
          
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

          // Set default values for fields that might be missing
          if (!this.compliance.MaturityLevel) {
            this.compliance.MaturityLevel = 'Initial';
          }
          
          if (!this.compliance.PermanentTemporary) {
            this.compliance.PermanentTemporary = 'Permanent';
          }
          
          // Clear identifier since a new one will be generated
          this.compliance.Identifier = '';
        } else {
          this.error = 'Failed to load compliance data';
        }
      } catch (error) {
        console.error('Error loading compliance data:', error);
        this.error = 'Failed to load compliance data. Please try again.';
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
          this.error = 'Failed to load approvers';
        }
      } catch (error) {
        console.error('Failed to load users:', error);
        this.error = 'Failed to load approvers. Please try again.';
        PopupService.error('Failed to load approvers. Please refresh the page and try again.', 'Loading Error');
      } finally {
        this.loading = false;
      }
    },
    async loadComplianceFrameworkInfo(complianceId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceFrameworkInfo(complianceId);
        
        if (response.data && response.data.success) {
          this.sourceFrameworkInfo = response.data.data;
          // Set the target framework to the source framework (locked)
          this.targetFrameworkId = this.sourceFrameworkInfo.framework_id;
          console.log('Source framework info loaded:', this.sourceFrameworkInfo);
        } else {
          throw new Error(response.data?.message || 'Failed to load framework info');
        }
      } catch (error) {
        this.error = 'Failed to load compliance framework information';
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadFrameworks() {
      try {
        this.loading = true;
        const response = await complianceService.getFrameworks();
        this.frameworks = response.data.data.map(fw => ({
          id: fw.FrameworkId,
          name: fw.FrameworkName
        }));
        
        // After loading frameworks, automatically load policies for the locked framework
        if (this.targetFrameworkId) {
          await this.loadPolicies(this.targetFrameworkId);
        }
      } catch (error) {
        this.error = 'Failed to load frameworks';
        console.error(error);
        PopupService.error('Failed to load frameworks. Please refresh the page and try again.', 'Loading Error');
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
        this.subPolicies = response.data.data
          .map(sp => ({
            id: sp.SubPolicyId,
            name: sp.SubPolicyName
          }))
          // Filter out the source subpolicy to prevent copying to same subpolicy
          .filter(sp => sp.id !== this.sourceSubPolicyId);
      } catch (error) {
        this.error = 'Failed to load sub-policies';
        console.error(error);
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
    async submitCopy() {
      if (!this.canSaveCopy) {
        let validationMessage = 'Please fill all required fields and select a destination.';
        
        // More detailed validation messages
        if (this.compliance && this.compliance.IsRisk) {
          const missingRiskFields = [];
          if (!this.compliance.PossibleDamage) missingRiskFields.push('Possible Damage');
          if (!this.compliance.mitigation) missingRiskFields.push('Mitigation');
          if (!this.compliance.PotentialRiskScenarios) missingRiskFields.push('Potential Risk Scenarios');
          if (!this.compliance.RiskType) missingRiskFields.push('Risk Type');
          if (!this.compliance.RiskCategory) missingRiskFields.push('Risk Category');
          if (!this.compliance.RiskBusinessImpact) missingRiskFields.push('Risk Business Impact');
          
          if (missingRiskFields.length > 0) {
            validationMessage += ` Missing risk fields: ${missingRiskFields.join(', ')}.`;
          }
        }
        
        PopupService.warning(validationMessage, 'Copy Validation');
        return;
      }
      
      // Show confirmation popup
      PopupService.confirm(
        'Are you sure you want to create a copy of this compliance item? This will create a new compliance item with version 1.0.',
        'Confirm Copy',
        async () => {
          try {
            this.loading = true;
            this.error = null;
            this.successMessage = null;
            
            const cloneData = {
              ...this.compliance,
              Impact: String(this.compliance.Impact),
              Probability: String(this.compliance.Probability),
              target_subpolicy_id: this.targetSubPolicyId,
              Status: 'Under Review',
              ActiveInactive: 'Inactive',
              PermanentTemporary: this.compliance.PermanentTemporary || 'Permanent',
              ComplianceVersion: '1.0',
              ApprovalDueDate: this.compliance.ApprovalDueDate,
              reviewer_id: this.compliance.reviewer_id,
              Applicability: this.compliance.Applicability
            };

            const response = await complianceService.cloneCompliance(
              this.originalComplianceId,
              cloneData
            );

            if (response.data.success) {
              PopupService.success(
                `Compliance copied successfully! New compliance ID: ${response.data.compliance_id}. It has been submitted for review.`,
                'Copy Complete'
              );
              
              // Navigate back to the tailoring page after a short delay
              setTimeout(() => {
                this.$router.push('/compliance/tailoring');
              }, 2000);
            } else {
              this.error = response.data.message || 'Failed to copy compliance';
              PopupService.error(this.error, 'Copy Failed');
            }
          } catch (error) {
            console.error('Copy error:', error);
            const errorMessage = 'Failed to copy compliance: ' + (error.response?.data?.message || error.message);
            this.error = errorMessage;
            PopupService.error(errorMessage, 'Copy Error');
          } finally {
            this.loading = false;
          }
        },
        () => {
          PopupService.success('Copy operation cancelled', 'Cancelled');
        }
      );
    },
    cancelCopy() {
      // Navigate back to the tailoring page
      this.$router.push('/compliance/tailoring');
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

.framework-locked-message {
  font-size: 0.8rem;
  color: #6c757d;
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.optional-indicator {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 400;
  font-style: italic;
  margin-left: 0.5rem;
}
</style> 