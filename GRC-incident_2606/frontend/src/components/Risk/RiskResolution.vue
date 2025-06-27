<template>
  <div class="resolution-container">
    <!-- Toggle buttons for Risk Resolution and Risk Workflow -->
    <div class="toggle-buttons">
      <button 
        class="toggle-button active" 
        @click="navigateTo('resolution')"
      >
        Risk Resolution
      </button>
      <button 
        class="toggle-button" 
        @click="navigateTo('workflow')"
      >
        Risk Workflow
      </button>
    </div>
    
    <!-- Search and Filter Bar - without container -->
    <div class="filters-wrapper">
      <input 
        type="text" 
        v-model="searchQuery" 
        class="search-input" 
        placeholder="Search..."
        @input="filterRisks"
      />
      <div class="filter-dropdowns">
        <select v-model="criticalityFilter" class="filter-select" @change="filterRisks">
          <option value="">All Criticality</option>
          <option v-for="criticality in uniqueCriticalities" :key="criticality">{{ criticality }}</option>
        </select>
        <select v-model="statusFilter" class="filter-select" @change="filterRisks">
          <option value="">All Status</option>
          <option v-for="status in uniqueStatuses" :key="status">{{ status }}</option>
        </select>
        <select v-model="assignedToFilter" class="filter-select" @change="filterRisks">
          <option value="">All Assigned To</option>
          <option v-for="user in uniqueAssignedUsers" :key="user">{{ user }}</option>
        </select>
        <select v-model="reviewerFilter" class="filter-select" @change="filterRisks">
          <option value="">All Reviewers</option>
          <option v-for="reviewer in uniqueReviewers" :key="reviewer">{{ reviewer }}</option>
        </select>
      </div>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Loading risk data...</span>
    </div>
    
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-else-if="filteredRisks.length === 0" class="no-data">
      <p>No eligible risk instances found for resolution. Either there are no risks with completed scoring, or all scored risks have been rejected.</p>
      <p class="no-data-subtitle">Note: Rejected risks are not displayed in Risk Resolution as they don't require further processing.</p>
    </div>
    
    <!-- Show risk table if not in mitigation workflow -->
    <div v-else-if="!showMitigationModal" class="table-responsive">
      <table class="risk-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Risk Title</th>
            <th>Category</th>
            <th>Criticality</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Assigned To</th>
            <th>Reviewer</th>
            <th>Review Count</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="risk in risks" :key="risk.RiskInstanceId" :class="getRowClass(risk.RiskStatus)">
            <td>{{ risk.RiskInstanceId }}</td>
            <td>{{ risk.RiskTitle || 'No title' }}</td>
            <td>{{ risk.Category }}</td>
            <td><span class="criticality-badge" :class="getCriticalityClass(risk.Criticality)">{{ risk.Criticality }}</span></td>
            <td><span class="priority-badge" :class="getPriorityClass(risk.RiskPriority)">{{ risk.RiskPriority }}</span></td>
            <td class="status-column">{{ risk.RiskStatus }}</td>
            <td>
              <!-- Display assigned user name if exists -->
              <div class="assigned-to-cell">
                {{ risk.RiskOwner && risk.RiskOwner !== 'System Owner' && risk.RiskOwner !== 'System User' ? risk.RiskOwner : 'Not Assigned' }}
                <span v-if="risk.RiskMitigation" class="eye-icon" @click="viewQuestionnaire(risk)" title="View Mitigation Steps">
                  <i class="fas fa-eye"></i>
                </span>
              </div>
            </td>
            <td>
              <!-- Display reviewer name if exists -->
              <div class="reviewer-cell">
                <span v-if="risk.Reviewer || risk.ReviewerName" class="reviewer-badge">
                  {{ risk.Reviewer || risk.ReviewerName }}
                </span>
                <span v-else class="not-assigned">Not Assigned</span>
              </div>
            </td>
            <td class="review-count">{{ risk.ReviewerCount || 0 }}</td>
            <td>
              <button @click="openMitigationModal(risk)" class="assign-btn">
                Assign
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mitigation Workflow Section (not modal) -->
    <div v-if="showMitigationModal" class="mitigation-workflow-section">
      <div class="mitigation-header">
        <button class="back-btn" @click="closeMitigationModal">
          <i class="fas fa-arrow-left"></i> Back to Risks
        </button>
        <h2 v-if="viewOnlyMitigationModal">Viewing Mitigation Steps</h2>
        <h2 v-else>Assign Risk with Mitigation Steps</h2>
      </div>
      <div class="mitigation-body">
        <div v-if="loadingMitigations" class="loading">
          <div class="spinner"></div>
          <span>Loading mitigation steps...</span>
        </div>
        <div v-else>
          <div class="risk-summary">
            <h3>{{ selectedRisk.RiskTitle || 'Risk #' + selectedRisk.RiskInstanceId }}</h3>
            <div class="risk-details">
              <p><strong>ID:</strong> {{ selectedRisk.RiskInstanceId }}</p>
              <p><strong>Category:</strong> {{ selectedRisk.Category }}</p>
              <p><strong>Criticality:</strong> {{ selectedRisk.Criticality }}</p>
              <p><strong>Reviewer:</strong> <span class="reviewer-info">{{ selectedRisk.Reviewer || selectedRisk.ReviewerName || 'Not Assigned' }}</span></p>
            </div>
          </div>
          
          <!-- Add User and Reviewer Assignment Section -->
          <div v-if="!viewOnlyMitigationModal" class="assignment-section">
            <h3>Assign Risk</h3>
            <div class="assignment-fields">
              <div class="assignment-field">
                <label>Assign To:</label>
                <select v-model="selectedUsers[selectedRisk.RiskInstanceId]" class="assignment-dropdown">
                  <option value="">Select User</option>
                  <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                    {{ user.user_name }} {{ user.department && user.designation ? `(${user.department}, ${user.designation})` : user.department ? `(${user.department})` : user.designation ? `(${user.designation})` : '' }}
                  </option>
                </select>
              </div>
              <div class="assignment-field">
                <label>Reviewer:</label>
                <select v-model="selectedReviewers[selectedRisk.RiskInstanceId]" class="assignment-dropdown">
                  <option value="">Select Reviewer</option>
                  <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                    {{ user.user_name }} {{ user.department && user.designation ? `(${user.department}, ${user.designation})` : user.department ? `(${user.department})` : user.designation ? `(${user.designation})` : '' }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          
          <div class="mitigation-workflow">
            <h3>Mitigation Steps</h3>
            <!-- Existing Mitigation Steps -->
            <div v-if="mitigationSteps.length" class="workflow-timeline">
              <div v-for="(step, index) in mitigationSteps" :key="index" class="workflow-step">
                <div class="step-number">{{ index + 1 }}</div>
                <div class="step-content">
                  <textarea 
                    v-model="step.description" 
                    class="mitigation-textarea"
                    :readonly="viewOnlyMitigationModal"
                    placeholder="Enter mitigation step description"
                  ></textarea>
                  <div class="step-actions">
                    <button @click="removeMitigationStep(index)" class="remove-step-btn" :disabled="viewOnlyMitigationModal">
                      <i class="fas fa-trash"></i> Remove
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-mitigations">
              <p>No mitigation steps defined for this risk. Add steps below.</p>
            </div>
            <!-- Add New Mitigation Step -->
            <div class="add-mitigation">
              <textarea 
                v-model="newMitigationStep" 
                class="mitigation-textarea"
                :readonly="viewOnlyMitigationModal"
                placeholder="Enter a new mitigation step description"
              ></textarea>
              <button @click="addMitigationStep" class="add-step-btn" :disabled="viewOnlyMitigationModal || !newMitigationStep.trim()">
                <i class="fas fa-plus"></i> Add Mitigation Step
              </button>
            </div>
            <!-- Due Date Input -->
            <div class="due-date-section">
              <h4>Due Date for Mitigation Completion</h4>
              <input 
                type="date" 
                v-model="mitigationDueDate" 
                class="due-date-input" 
                :readonly="viewOnlyMitigationModal"
                :min="getTodayDate()"
              />
            </div>
            <!-- Risk Form Section -->
            <div class="risk-form-section" style="display: none;">
              <h4>Risk Mitigation Questionnaire</h4>
              <p class="form-note">Please complete these details about the risk mitigation:</p>
              <div class="form-field horizontal">
                <label for="cost-input">1. What is the cost for this mitigation?</label>
                <input 
                  id="cost-input" 
                  v-model="riskFormDetails.cost" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter the cost..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="impact-input">2. What is the impact for this mitigation?</label>
                <input 
                  id="impact-input" 
                  v-model="riskFormDetails.impact" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter the impact..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="financial-impact-input">3. What is the financial impact for this mitigation?</label>
                <input 
                  id="financial-impact-input" 
                  v-model="riskFormDetails.financialImpact" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter the financial impact..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="reputational-impact-input">4. What is the reputational impact for this mitigation?</label>
                <textarea 
                  id="reputational-impact-input" 
                  v-model="riskFormDetails.reputationalImpact" 
                  :readonly="viewOnlyMitigationModal"
                  placeholder="Describe the reputational impact..."
                  class="form-textarea"
                ></textarea>
              </div>
              <div class="form-field horizontal">
                <label for="operational-impact-input">5. What is the Operational Impact for this mitigation?</label>
                <input 
                  id="operational-impact-input" 
                  v-model="riskFormDetails.operationalImpact" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter the operational impact..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="financial-loss-input">6. What is the Financial Loss for this mitigation?</label>
                <input 
                  id="financial-loss-input" 
                  v-model="riskFormDetails.financialLoss" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter the financial loss..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="system-downtime-input">7. What is the expected system downtime (hrs) if this risk occurs?</label>
                <input 
                  id="system-downtime-input" 
                  v-model="riskFormDetails.systemDowntime" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter expected downtime in hours..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="recovery-time-input">8. How long did it take to recover last time (hrs)?</label>
                <input 
                  id="recovery-time-input" 
                  v-model="riskFormDetails.recoveryTime" 
                  type="number"
                  :readonly="viewOnlyMitigationModal"
                  min="0"
                  placeholder="Enter recovery time in hours..."
                  class="form-textarea"
                />
              </div>
              <div class="form-field horizontal">
                <label for="recurrence-possible-input">9. Is it possible that this risk will recur again?</label>
                <select 
                  id="recurrence-possible-input" 
                  v-model="riskFormDetails.recurrencePossible" 
                  :disabled="viewOnlyMitigationModal"
                  class="form-textarea"
                >
                  <option value="">Select</option>
                  <option value="Yes">Yes</option>
                  <option value="No">No</option>
                  <option value="Unknown">Unknown</option>
                </select>
              </div>
              <div class="form-field horizontal">
                <label for="improvement-initiative-input">10. Is this an Improvement Initiative which will prevent the future recurrence of said risk?</label>
                <select 
                  id="improvement-initiative-input" 
                  v-model="riskFormDetails.improvementInitiative" 
                  :disabled="viewOnlyMitigationModal"
                  class="form-textarea"
                >
                  <option value="">Select</option>
                  <option value="Yes">Yes</option>
                  <option value="No">No</option>
                  <option value="Unknown">Unknown</option>
                </select>
              </div>
            </div>
            <!-- Submit Section -->
            <div class="mitigation-actions">
              <button 
                @click="assignRiskWithMitigations" 
                class="submit-mitigations-btn"
                :disabled="viewOnlyMitigationModal || mitigationSteps.length === 0 || !mitigationDueDate || !selectedUsers[selectedRisk.RiskInstanceId] || !selectedReviewers[selectedRisk.RiskInstanceId]"
              >
                <i class="fas fa-user-plus"></i> Assign with Mitigations
              </button>
              <div v-if="viewOnlyMitigationModal && !isFormComplete()" class="form-warning" style="display: none;">
                <i class="fas fa-exclamation-circle"></i> Please complete all questionnaire fields
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add this at the end of the template, before </div></template> -->
    <div v-if="showQuestionnaireModal" class="questionnaire-modal-overlay">
      <div class="questionnaire-modal-content">
        <button class="close-modal-btn" @click="closeQuestionnaireModal"><i class="fas fa-times"></i></button>
        <h3>Risk Mitigation Questionnaire (View Only)</h3>
        <div v-if="selectedQuestionnaire">
          <div class="questionnaire-field"><strong>1. Cost:</strong> {{ selectedQuestionnaire.cost }}</div>
          <div class="questionnaire-field"><strong>2. Impact:</strong> {{ selectedQuestionnaire.impact }}</div>
          <div class="questionnaire-field"><strong>3. Financial Impact:</strong> {{ selectedQuestionnaire.financialImpact }}</div>
          <div class="questionnaire-field"><strong>4. Reputational Impact:</strong> {{ selectedQuestionnaire.reputationalImpact }}</div>
          <div class="questionnaire-field"><strong>5. Operational Impact:</strong> {{ selectedQuestionnaire.operationalImpact }}</div>
          <div class="questionnaire-field"><strong>6. Financial Loss:</strong> {{ selectedQuestionnaire.financialLoss }}</div>
          <div class="questionnaire-field"><strong>7. System Downtime (hrs):</strong> {{ selectedQuestionnaire.systemDowntime }}</div>
          <div class="questionnaire-field"><strong>8. Recovery Time (hrs):</strong> {{ selectedQuestionnaire.recoveryTime }}</div>
          <div class="questionnaire-field"><strong>9. Recurrence Possible:</strong> {{ selectedQuestionnaire.recurrencePossible }}</div>
          <div class="questionnaire-field"><strong>10. Improvement Initiative:</strong> {{ selectedQuestionnaire.improvementInitiative }}</div>
        </div>
        <div v-else>
          <p>No questionnaire data found for this risk.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'RiskResolution',
  data() {
    return {
      risks: [],
      filteredRisks: [],
      users: [],
      selectedUsers: {},
      selectedReviewers: {},
      loading: true,
      error: null,
      // New properties for mitigation modal
      showMitigationModal: false,
      selectedRisk: {},
      mitigationSteps: [],
      newMitigationStep: '',
      loadingMitigations: false,
      mitigationDueDate: '',
      riskFormDetails: {
        cost: '',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        systemDowntime: '',
        recoveryTime: '',
        recurrencePossible: '',
        improvementInitiative: ''
      },
      showQuestionnaireModal: false,
      selectedQuestionnaire: null,
      viewOnlyMitigationModal: false,
      // New properties for search and filtering
      searchQuery: '',
      criticalityFilter: '',
      statusFilter: '',
      assignedToFilter: '',
      reviewerFilter: ''
    }
  },
  computed: {
    uniqueCriticalities() {
      return [...new Set(this.risks.map(risk => risk.Criticality).filter(Boolean))];
    },
    uniqueStatuses() {
      return [...new Set(this.risks.map(risk => risk.RiskStatus).filter(Boolean))];
    },
    uniqueAssignedUsers() {
      return [...new Set(this.risks.map(risk => 
        risk.RiskOwner && risk.RiskOwner !== 'System Owner' && risk.RiskOwner !== 'System User' ? 
        risk.RiskOwner : 'Not Assigned'
      ))];
    },
    uniqueReviewers() {
      return [...new Set(this.risks.map(risk => risk.ReviewerName || 'Not Assigned'))];
    }
  },
  mounted() {
    this.fetchRisks();
    this.fetchUsers();
  },
  methods: {
    fetchRisks() {
      axios.get('http://localhost:8000/api/risk-instances/')
        .then(response => {
          console.log('Risk data received:', response.data);
          
          // Log reviewer information for debugging
          if (response.data && response.data.length > 0) {
            response.data.forEach(risk => {
              console.log(`Risk ID: ${risk.RiskInstanceId}, Reviewer: ${risk.Reviewer || risk.ReviewerName || 'None'}, ReviewerId: ${risk.ReviewerId || 'None'}`);
            });
          }
          
          this.risks = response.data;
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching risks:', error);
          this.error = `Failed to fetch risks: ${error.message}`;
          this.loading = false;
        });
    },
    fetchUsers() {
      axios.get('http://localhost:8000/api/custom-users/')
        .then(response => {
          console.log('User data received:', response.data);
          this.users = response.data;
        })
        .catch(error => {
          console.error('Error fetching users:', error);
        });
    },
    filterRisks() {
      this.filteredRisks = this.risks.filter(risk => {
        // Search query filter
        const searchLower = this.searchQuery.toLowerCase();
        const matchesSearch = !this.searchQuery || 
          (risk.RiskInstanceId && risk.RiskInstanceId.toString().toLowerCase().includes(searchLower)) ||
          (risk.RiskTitle && risk.RiskTitle.toLowerCase().includes(searchLower)) ||
          (risk.Category && risk.Category.toLowerCase().includes(searchLower)) ||
          (risk.Criticality && risk.Criticality.toLowerCase().includes(searchLower)) ||
          (risk.RiskStatus && risk.RiskStatus.toLowerCase().includes(searchLower)) ||
          (risk.RiskDescription && risk.RiskDescription.toLowerCase().includes(searchLower));
        
        // Dropdown filters
        const matchesCriticality = !this.criticalityFilter || risk.Criticality === this.criticalityFilter;
        const matchesStatus = !this.statusFilter || risk.RiskStatus === this.statusFilter;
        
        // Assigned to filter
        const assignedTo = risk.RiskOwner && risk.RiskOwner !== 'System Owner' && risk.RiskOwner !== 'System User' ? 
          risk.RiskOwner : 'Not Assigned';
        const matchesAssignedTo = !this.assignedToFilter || assignedTo === this.assignedToFilter;
        
        // Reviewer filter
        const reviewer = risk.ReviewerName || 'Not Assigned';
        const matchesReviewer = !this.reviewerFilter || reviewer === this.reviewerFilter;
        
        return matchesSearch && matchesCriticality && matchesStatus && matchesAssignedTo && matchesReviewer;
      });
    },
    openMitigationModal(risk) {
      this.selectedRisk = risk;
      this.showMitigationModal = true;
      this.loadingMitigations = true;
      
      // Initialize user and reviewer selections if they exist
      if (risk.UserId) {
        this.selectedUsers[risk.RiskInstanceId] = risk.UserId;
      }
      if (risk.ReviewerId) {
        this.selectedReviewers[risk.RiskInstanceId] = risk.ReviewerId;
      }
      
      // Fetch existing mitigations for this risk
      axios.get(`http://localhost:8000/api/risk-mitigations/${risk.RiskInstanceId}/`)
        .then(response => {
          console.log('Existing mitigations:', response.data);
          this.mitigationSteps = this.parseMitigations(response.data);
          this.loadingMitigations = false;
          
          // Set due date if it exists
          if (risk.MitigationDueDate) {
            this.mitigationDueDate = risk.MitigationDueDate;
          } else {
            // Set default due date to 7 days from today
            const date = new Date();
            date.setDate(date.getDate() + 7);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            this.mitigationDueDate = `${year}-${month}-${day}`;
          }
        })
        .catch(error => {
          console.error('Error fetching mitigations:', error);
          // Initialize with empty array if no mitigations exist
          this.mitigationSteps = [];
          this.loadingMitigations = false;
          
          // Set default due date to 7 days from today
          const date = new Date();
          date.setDate(date.getDate() + 7);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          this.mitigationDueDate = `${year}-${month}-${day}`;
        });
    },
    closeMitigationModal() {
      this.showMitigationModal = false;
      this.selectedRisk = {};
      this.mitigationSteps = [];
      this.newMitigationStep = '';
      this.mitigationDueDate = '';
      this.riskFormDetails = {
        cost: '',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        systemDowntime: '',
        recoveryTime: '',
        recurrencePossible: '',
        improvementInitiative: ''
      };
      this.viewOnlyMitigationModal = false;
    },
    parseMitigations(data) {
      // Convert different mitigation formats to our standard format
      if (!data || data.length === 0) {
        return [];
      }
      
      // If it's already an array of objects with descriptions
      if (Array.isArray(data) && data[0] && data[0].description) {
        return data.map(item => ({
          description: item.description || item.title || '',
          status: item.status || 'Not Started'
        }));
      }
      
      // If it's an array of strings or simple objects
      if (Array.isArray(data)) {
        return data.map((item, index) => ({
          description: typeof item === 'string' ? item : (item.description || item.title || `Step ${index + 1}`),
          status: item.status || 'Not Started'
        }));
      }
      
      // If it's an object with numbered keys (e.g., {"1": "Step 1", "2": "Step 2"})
      if (typeof data === 'object' && !Array.isArray(data)) {
        const steps = [];
        Object.keys(data).forEach(key => {
          const value = data[key];
          steps.push({
            description: typeof value === 'string' ? value : (value.description || value.title || `Step ${key}`),
            status: value.status || 'Not Started'
          });
        });
        return steps;
      }
      
      // Fallback: if it's a string, create a single step
      if (typeof data === 'string') {
        return [{
          description: data,
          status: 'Not Started'
        }];
      }
      
      return [];
    },
    addMitigationStep() {
      if (!this.newMitigationStep.trim()) return;
      
      this.mitigationSteps.push({
        description: this.newMitigationStep,
        status: 'Not Started'
      });
      
      this.newMitigationStep = '';
    },
    removeMitigationStep(index) {
      this.mitigationSteps.splice(index, 1);
    },
    assignRiskWithMitigations() {
      const riskId = this.selectedRisk.RiskInstanceId;
      const userId = this.selectedUsers[riskId];
      const reviewerId = this.selectedReviewers[riskId];
      
      console.log('Assigning risk with following IDs:', { riskId, userId, reviewerId });
      
      if (!userId || !reviewerId || this.mitigationSteps.length === 0 || !this.mitigationDueDate) {
        // Show validation error
        if (!userId) {
          alert('Please select a user to assign this risk to.');
          return;
        }
        if (!reviewerId) {
          alert('Please select a reviewer for this risk.');
          return;
        }
        if (this.mitigationSteps.length === 0) {
          alert('Please add at least one mitigation step.');
          return;
        }
        if (!this.mitigationDueDate) {
          alert('Please select a due date for mitigation completion.');
          return;
        }
        return;
      }
      
      this.loading = true;
      
      // Convert mitigations to the expected JSON format
      // Format: {"1": "Description 1", "2": "Description 2", ...}
      const mitigationsJson = {};
      this.mitigationSteps.forEach((step, index) => {
        mitigationsJson[index + 1] = step.description;
      });
      
      console.log('Sending mitigation data:', mitigationsJson);
      
      // First assign the risk to the user with mitigations
      axios.post('http://localhost:8000/api/risk-assign/', {
        risk_id: riskId,
        user_id: userId,
        mitigations: mitigationsJson,
        due_date: this.mitigationDueDate,
        risk_form_details: {} // Empty object instead of form details
      })
      .then(response => {
        console.log('Assignment response:', response.data);
        
        // Now assign the reviewer - explicitly set create_approval_record to false
        return axios.post('http://localhost:8000/api/assign-reviewer/', {
          risk_id: riskId,
          reviewer_id: reviewerId,
          user_id: userId,
          mitigations: mitigationsJson,
          risk_form_details: {}, // Empty object instead of form details
          create_approval_record: false // Explicitly set to false to prevent creating version entry
        });
      })
      .then(response => {
        console.log('Reviewer assignment response:', response.data);
        
        // Update the local risk data to show assignment
        const index = this.risks.findIndex(r => r.RiskInstanceId === riskId);
        if (index !== -1) {
          const assignedUser = this.users.find(u => u.user_id === userId);
          const assignedReviewer = this.users.find(u => u.user_id === reviewerId);
          
          // Make sure we have both user objects
          if (assignedUser && assignedReviewer) {
            this.risks[index].RiskOwner = assignedUser.user_name;
            this.risks[index].UserId = userId;
            
            // Update both Reviewer and ReviewerName fields to ensure compatibility
            this.risks[index].ReviewerId = Number(reviewerId);
            this.risks[index].ReviewerName = assignedReviewer.user_name;
            this.risks[index].Reviewer = assignedReviewer.user_name;
            
            this.risks[index].RiskStatus = 'Assigned';
            this.risks[index].RiskMitigation = mitigationsJson;
            this.risks[index].MitigationDueDate = this.mitigationDueDate;
            this.risks[index].MitigationStatus = 'Yet to Start';
            this.risks[index].RiskFormDetails = {}; // Empty object instead of form details
          } else {
            console.error('Could not find assigned user or reviewer:', { userId, reviewerId });
          }
        }
        
        this.loading = false;
        this.closeMitigationModal();
        
        // Show success message
        alert('Risk assigned successfully with mitigation steps and reviewer!');
      })
      .catch(error => {
        console.error('Error assigning risk:', error);
        this.loading = false;
        alert('Failed to assign risk. Please try again.');
      });
    },
    getCriticalityClass(criticality) {
      if (!criticality) return '';
      const level = criticality.toLowerCase();
      if (level.includes('high')) return 'high';
      if (level.includes('medium')) return 'medium';
      if (level.includes('low')) return 'low';
      if (level.includes('critical')) return 'critical';
      return '';
    },
    getPriorityClass(priority) {
      if (!priority) return '';
      const level = priority.toLowerCase();
      if (level.includes('high')) return 'high';
      if (level.includes('medium')) return 'medium';
      if (level.includes('low')) return 'low';
      return '';
    },
    getStatusClass(status) {
      if (!status) return '';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('approved')) return 'approved';
      if (statusLower.includes('review')) return 'review';
      if (statusLower.includes('progress')) return 'progress';
      if (statusLower.includes('assigned')) return 'assigned';
      if (statusLower.includes('revision')) return 'revision';
      if (statusLower.includes('open')) return 'open';
      return '';
    },
    getRowClass(status) {
      if (!status) return '';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('approved')) return 'row-approved';
      if (statusLower.includes('review')) return 'row-review';
      return '';
    },
    getTodayDate() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },
    isFormComplete() {
      // Always return true since we're not requiring questionnaire completion here anymore
      return true;
    },
    isRiskRejected(risk) {
      // Helper method to check if a risk is rejected
      // Used in filtering risks for the resolution screen
      if (!risk) return false;
      
      const appetite = (risk.Appetite || '').toLowerCase();
      const status = (risk.RiskStatus || '').toLowerCase();
      
      return appetite === 'no' || status === 'rejected';
    },
    viewQuestionnaire(risk) {
      console.log("Viewing mitigation steps for risk:", risk.RiskInstanceId);
      
      axios.get(`http://localhost:8000/api/risk-instances/${risk.RiskInstanceId}/`)
        .then(response => {
          const data = response.data;
          this.selectedRisk = data;
          
          // Fetch mitigation steps
          axios.get(`http://localhost:8000/api/risk-mitigations/${risk.RiskInstanceId}/`)
            .then(mitResp => {
              console.log("Mitigation steps:", mitResp.data);
              this.mitigationSteps = this.parseMitigations(mitResp.data);
              
              // Show the mitigation modal in view-only mode
              this.showMitigationModal = true;
              this.viewOnlyMitigationModal = true;
              this.mitigationDueDate = data.MitigationDueDate || '';
              
              // --- Parse RiskFormDetails if it's a string ---
              let formDetails = data.RiskFormDetails;
              if (typeof formDetails === 'string') {
                try {
                  formDetails = JSON.parse(formDetails);
                } catch (e) {
                  formDetails = {};
                }
              }
              this.riskFormDetails = this.mapRiskFormDetails(formDetails);
            })
            .catch(error => {
              console.error("Error fetching mitigation steps:", error);
              // Fallback to risk mitigation data from risk object
              this.mitigationSteps = this.parseMitigations(data.RiskMitigation || {});
              
              // Show the mitigation modal in view-only mode
              this.showMitigationModal = true;
              this.viewOnlyMitigationModal = true;
              this.mitigationDueDate = data.MitigationDueDate || '';
              
              // --- Parse RiskFormDetails if it's a string ---
              let formDetails = data.RiskFormDetails;
              if (typeof formDetails === 'string') {
                try {
                  formDetails = JSON.parse(formDetails);
                } catch (e) {
                  formDetails = {};
                }
              }
              this.riskFormDetails = this.mapRiskFormDetails(formDetails);
            });
        })
        .catch(error => {
          console.error("Error fetching risk details:", error);
          alert('Failed to fetch risk details');
        });
    },
    closeQuestionnaireModal() {
      this.showQuestionnaireModal = false;
      this.selectedQuestionnaire = null;
    },
    mapRiskFormDetails(details) {
      if (!details) return {
        cost: '', impact: '', financialImpact: '', reputationalImpact: '', operationalImpact: '', financialLoss: '', systemDowntime: '', recoveryTime: '', recurrencePossible: '', improvementInitiative: ''
      };
      // Normalize Yes/No/Unknown for selects
      function normalizeYN(val) {
        if (!val) return '';
        if (typeof val === 'string') {
          if (val.toLowerCase() === 'yes') return 'Yes';
          if (val.toLowerCase() === 'no') return 'No';
          if (val.toLowerCase() === 'unknown') return 'Unknown';
        }
        return val;
      }
      return {
        cost: details.cost ?? '',
        impact: details.impact ?? '',
        financialImpact: details.financialImpact ?? details.financialimpact ?? '',
        reputationalImpact: details.reputationalImpact ?? details.reputationalimpact ?? '',
        operationalImpact: details.operationalImpact ?? details.operationalimpact ?? '',
        financialLoss: details.financialLoss ?? details.financialloss ?? '',
        systemDowntime: details.systemDowntime ?? details.expecteddowntime ?? '',
        recoveryTime: details.recoveryTime ?? details.recoverytime ?? '',
        recurrencePossible: normalizeYN(details.recurrencePossible ?? details.riskrecurrence),
        improvementInitiative: normalizeYN(details.improvementInitiative ?? details.improvementinitiative)
      };
    },
    navigateTo(screen) {
      // Remove active class from all buttons
      const buttons = document.querySelectorAll('.toggle-button');
      buttons.forEach(button => button.classList.remove('active'));
      
      // Add active class to the clicked button
      const clickedButton = Array.from(buttons).find(button => 
        button.textContent.trim().toLowerCase().includes(screen)
      );
      if (clickedButton) clickedButton.classList.add('active');
      
      // Navigate to the appropriate screen
      switch(screen) {
        case 'resolution':
          // Already on resolution page
          break;
        case 'workflow':
          this.$router.push('/risk/workflow');
          break;
      }
    },
  }
}
</script>

<style scoped>
/* Import the CSS file */
@import './RiskResolution.css';

/* Add additional styles for the section title */
.section-title {
  margin: 20px 0;
  color: #333;
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
}

/* Enhance the toggle buttons styling */
.toggle-buttons {
  display: flex;
  background: #f8f9fa;
  border-radius: 50px;
  overflow: hidden;
  width: fit-content;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  margin: 30px auto;
}

.toggle-button {
  padding: 12px 30px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  color: #555;
  transition: all 0.3s ease;
  position: relative;
  outline: none;
  min-width: 180px;
  text-align: center;
}

.toggle-button:not(:last-child) {
  border-right: 1px solid #eee;
}

.toggle-button:hover {
  background-color: rgba(52, 152, 219, 0.1);
  color: #3498db;
}

.toggle-button.active {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  box-shadow: 0 2px 10px rgba(52, 152, 219, 0.3);
}
</style> 