<template>
  <div class="tailoring-container">
    <h2 class="page-title">Versioning</h2>
    <div class="version-info">
      <p>Create new versions of frameworks or policies. New versions go through the same approval process as the original items.</p>
    </div>
    
    <!-- Framework Dropdown -->
    <div class="dropdown-container">
      <div v-if="!showPolicyDropdown" class="filter-group">
        <label for="frameworkSelect">SELECT FRAMEWORK</label>
        <div class="select-wrapper" title="Choose an existing framework to create a new version with modifications">
          <select id="frameworkSelect" v-model="selectedFramework" @change="onFrameworkDropdown" title="Select a framework to create a new version of">
            <option value="" disabled selected>Select a framework</option>
            <option v-for="framework in frameworks" :key="framework.id" :value="framework.id">
              {{ framework.name }}
            </option>
          </select>
        </div>
        <button class="switch-btn" @click="switchToPolicy" title="Switch to creating new versions of individual policies instead of entire frameworks">Switch to Policy Versioning</button>
      </div>
    </div>
    
    <!-- Policy Dropdown -->
    <div v-if="showPolicyDropdown" class="filter-group">
      <label for="policySelect">Select Policy</label>
      <div class="select-wrapper" title="Choose an approved and active policy to create a new version of">
        <select id="policySelect" v-model="selectedPolicy" @change="onPolicyDropdown" title="Select a policy to create a new version of">
          <option value="" disabled selected>Select a policy</option>
          <option v-for="(policy, idx) in policyOptions" :key="idx" :value="idx">
            {{ policy.title }}
          </option>
        </select>
      </div>
      <button v-if="selectedPolicy === ''" class="switch-btn" @click="switchToFramework" title="Switch back to creating new versions of entire frameworks">Switch to Framework Versioning</button>
    </div>

    <div v-if="showStepper" class="stepper-container">
      <div class="stepper-scroll">
      <div class="stepper">
        <div
          v-for="(tab, idx) in stepTabs"
          :key="tab.key"
          :class="['step', { active: stepIndex === idx }]"
          @click="stepIndex = idx"
          :title="`Navigate to ${tab.label} section`"
        >
          {{ tab.label }}
          <span v-if="stepIndex === idx && idx !== 0 && !showPolicyDropdown" class="tab-close" @click.stop="closeTab(idx)" title="Close this policy tab">X</span>
        </div>
        <button v-if="stepTabs.length > 1 && !showPolicyDropdown" class="add-btn add-policy-btn" @click="addPolicy" title="Add a new policy to this framework version">+ Add Policy to Version</button>
        </div>
      </div>
      <div class="step-content">
        <!-- Framework Form - Only show when not in policy mode -->
        <div v-if="stepIndex === 0 && !showPolicyDropdown">
          <form class="form-section" @submit.prevent="submitFrameworkForm">
            <div class="form-row">
              <div class="form-group">
                <label>Title:</label>
                <input type="text" v-model="frameworkData.title" required title="Enter a descriptive name for your new framework version" />
              </div>
              <div class="form-group">
                <label>Description:</label>
                <textarea v-model="frameworkData.description" required title="Provide a detailed description of the framework's purpose and what's new in this version"></textarea>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>Category:</label>
                <input type="text" v-model="frameworkData.category" required title="Specify the category or domain this framework belongs to (e.g., Cybersecurity, Financial)" />
              </div>
              <div class="form-group">
                <label>Start Date:</label>
                <input type="date" v-model="frameworkData.startDate" required title="Select when this new framework version becomes effective" />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>End Date:</label>
                <input type="date" v-model="frameworkData.endDate" required title="Select when this framework version expires or needs review" />
              </div>
              <div class="form-group">
                <label>Document URL:</label>
                <div class="input-with-icon" title="Upload a supporting document for this framework version">
                  <input
                    type="url"
                    v-model="frameworkData.docURL"
                    placeholder="URL will appear here"
                    readonly
                    title="The document URL will appear here after upload"
                  />
                  <button type="button" class="browse-btn" @click="browseFrameworkFile" title="Browse and upload a framework document">Browse</button>
                  <input type="file" ref="frameworkFileInput" style="display:none" @change="onFrameworkFileChange" />
                </div>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>Identifier:</label>
                <input type="text" v-model="frameworkData.identifier" required title="Enter a unique identifier or code for this framework version" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Created By</label>
                <select v-model="frameworkData.createdByName" required title="Select the person responsible for creating this framework version">
                  <option value="">Select Creator</option>
                  <option v-for="user in users" :key="user.UserId" :value="user.UserName">
                    {{ user.UserName }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Reviewer</label>
                <select v-model="frameworkData.reviewer" required title="Select the person who will review and approve this framework version">
                  <option value="">Select Reviewer</option>
                  <option v-for="user in users" :key="user.UserId" :value="user.UserName">
                    {{ user.UserName }}
                  </option>
                </select>
              </div>
            </div>
          </form>
        </div>
        
        <!-- Policy Form: Only show the selected policy in the stepper -->
        <div v-else-if="!showPolicyDropdown && stepIndex > 0">
          <form class="form-section policy-form" @submit.prevent="submitFrameworkForm">
            <h3 class="form-title">Policy Details</h3>
            <div v-if="policiesData[stepIndex - 1]" class="policy-form-container">
              <div class="policy-header">
                <h4>Policy Details</h4>
                <span v-if="!policiesData[stepIndex - 1].id" class="policy-badge new-badge" title="This is a new policy being added to the framework version">New Policy</span>
                <span v-else class="policy-badge existing-badge" title="This is an existing policy being modified in the new version">Existing Policy</span>
                <button
                  v-if="policiesData[stepIndex - 1].id"
                  type="button"
                  class="exclude-btn"
                  @click="excludePolicy(stepIndex - 1)"
                  :class="{ 'excluded': policiesData[stepIndex - 1].exclude }"
                  style="margin-left: 16px;"
                  :title="policiesData[stepIndex - 1].exclude ? 'Click to include this policy in the new framework version' : 'Click to exclude this policy from the new framework version'"
                >
                  {{ policiesData[stepIndex - 1].exclude ? 'Excluded' : 'Exclude' }}
                </button>
              </div>
              <div v-if="!policiesData[stepIndex - 1].exclude">
                <div class="form-row">
                  <div class="form-group">
                    <label>Title <span class="required-field">*</span></label>
                    <input 
                      type="text" 
                      v-model="policiesData[stepIndex - 1].title" 
                      required 
                      placeholder="Enter policy title" 
                      :class="{ 'field-error': isSubmitting && !policiesData[stepIndex - 1].title }"
                      title="Enter a clear and descriptive name for this policy version"
                    />
                    <span v-if="isSubmitting && !policiesData[stepIndex - 1].title" class="error-text">Title is required</span>
                  </div>
                  <div class="form-group">
                    <label>Description <span class="required-field">*</span></label>
                    <textarea 
                      v-model="policiesData[stepIndex - 1].description" 
                      required 
                      placeholder="Enter policy description"
                      :class="{ 'field-error': isSubmitting && !policiesData[stepIndex - 1].description }"
                      title="Provide a comprehensive description of what this policy covers and what's new in this version"
                    ></textarea>
                    <span v-if="isSubmitting && !policiesData[stepIndex - 1].description" class="error-text">Description is required</span>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Objective</label>
                    <textarea v-model="policiesData[stepIndex - 1].objective" required placeholder="Enter policy objective" title="Describe the main goals and objectives this policy aims to achieve"></textarea>
                  </div>
                  <div class="form-group">
                    <label>Scope</label>
                    <textarea v-model="policiesData[stepIndex - 1].scope" required placeholder="Enter policy scope" title="Define the boundaries and areas covered by this policy"></textarea>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Department</label>
                    <input type="text" v-model="policiesData[stepIndex - 1].department" required placeholder="Enter department" title="Specify the department or business unit responsible for this policy" />
                  </div>
                  <div class="form-group">
                    <label>Applicability</label>
                    <input type="text" v-model="policiesData[stepIndex - 1].applicability" required placeholder="Enter applicability" title="Define who or what this policy applies to (e.g., all employees, specific roles, systems)" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" v-model="policiesData[stepIndex - 1].startDate" required title="Select when this policy version becomes effective" />
                  </div>
                  <div class="form-group">
                    <label>End Date</label>
                    <input type="date" v-model="policiesData[stepIndex - 1].endDate" required title="Select when this policy version expires or needs review" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Document URL</label>
                    <div class="input-with-icon" title="Upload a supporting document for this policy version">
                      <input
                        type="url"
                        v-model="policiesData[stepIndex - 1].docURL"
                        placeholder="URL will appear here"
                        readonly
                        title="The document URL will appear here after upload"
                      />
                      <button type="button" class="browse-btn" @click="() => browsePolicyFile(stepIndex - 1)" title="Browse and upload a policy document">Browse</button>
                      <input type="file" ref="policyFileInputs" style="display:none" @change="e => onPolicyFileChange(e, stepIndex - 1)" />
                    </div>
                  </div>
                  <div class="form-group">
                    <label>Identifier <span class="required-field">*</span></label>
                    <input 
                      type="text" 
                      v-model="policiesData[stepIndex - 1].identifier" 
                      required 
                      placeholder="Enter identifier"
                      :class="{ 'field-error': isSubmitting && !policiesData[stepIndex - 1].identifier }"
                      title="Enter a unique identifier or code for this policy version"
                    />
                    <span v-if="isSubmitting && !policiesData[stepIndex - 1].identifier" class="error-text">Identifier is required</span>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Coverage Rate (%)</label>
                    <input 
                      type="number" 
                      v-model="policiesData[stepIndex - 1].coverageRate" 
                      min="0" 
                      max="100" 
                      step="0.01" 
                      placeholder="Enter coverage rate"
                      title="Enter the percentage of coverage this policy provides (0-100%)"
                    />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Policy Type</label>
                    <div class="searchable-select">
                      <input
                        type="text"
                        placeholder="Search or enter new policy type"
                        v-model="policiesData[stepIndex - 1].PolicyType"
                        @input="handlePolicyTypeChange(stepIndex - 1, $event.target.value)"
                        list="policyTypes"
                        :disabled="policiesData[stepIndex - 1].exclude"
                        title="Select or enter the type/category of this policy (e.g., Security, Operational, Financial)"
                      />
                      <datalist id="policyTypes">
                        <option v-for="type in policyTypes" :key="type" :value="type">{{ type }}</option>
                      </datalist>
                    </div>
                  </div>
                  <div class="form-group">
                    <label>Policy Category</label>
                    <div class="searchable-select">
                      <input
                        type="text"
                        placeholder="Search or enter new category"
                        v-model="policiesData[stepIndex - 1].PolicyCategory"
                        @input="handlePolicyCategoryChange(stepIndex - 1, $event.target.value)"
                        list="policyCategories"
                        :disabled="!policiesData[stepIndex - 1].PolicyType || policiesData[stepIndex - 1].exclude"
                        title="Select or enter a more specific category within the policy type"
                      />
                      <datalist id="policyCategories">
                        <option v-for="cat in getCategoriesForType(policiesData[stepIndex - 1].PolicyType)" :key="cat" :value="cat">{{ cat }}</option>
                      </datalist>
                    </div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Policy Sub Category</label>
                    <div class="searchable-select">
                      <input
                        type="text"
                        placeholder="Search or enter new sub category"
                        v-model="policiesData[stepIndex - 1].PolicySubCategory"
                        @input="handlePolicySubCategoryChange(stepIndex - 1, $event.target.value)"
                        list="policySubCategories"
                        :disabled="!policiesData[stepIndex - 1].PolicyCategory || policiesData[stepIndex - 1].exclude"
                        title="Select or enter a detailed sub-category for precise policy classification"
                      />
                      <datalist id="policySubCategories">
                        <option v-for="sub in getSubCategoriesForCategory(policiesData[stepIndex - 1].PolicyType, policiesData[stepIndex - 1].PolicyCategory)" :key="sub" :value="sub">{{ sub }}</option>
                      </datalist>
                    </div>
                  </div>
                </div>
                <div v-if="showPolicyDropdown" class="form-row">
                  <div class="form-group">
                    <label>Created By</label>
                    <select v-model="policiesData[stepIndex - 1].createdByName" required title="Select the person responsible for creating this policy version">
                      <option value="">Select Creator</option>
                      <option v-for="user in users" :key="user.UserId" :value="user.UserName">
                        {{ user.UserName }}
                      </option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Reviewer</label>
                    <select v-model="policiesData[stepIndex - 1].reviewer" required title="Select the person who will review and approve this policy version">
                      <option value="">Select Reviewer</option>
                      <option v-for="user in users" :key="user.UserId" :value="user.UserName">
                        {{ user.UserName }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="subpolicies-section">
                  <div class="subpolicies-header">
                    <h4>Sub Policies</h4>
                    <div>
                      <span class="subpolicy-counter" title="Number of active sub-policies in this policy version">{{ policiesData[stepIndex - 1].subPolicies.filter(sp => !sp.exclude).length }} sub-policies</span>
                      <button 
                        type="button" 
                        class="debug-btn" 
                        @click="debugSubpolicies(stepIndex - 1)"
                        title="Debug sub-policy data for troubleshooting"
                      >
                        Debug
                      </button>
                    </div>
                  </div>
                  <div v-for="(sub, subIdx) in policiesData[stepIndex - 1].subPolicies" :key="subIdx" class="subpolicy-card" :class="{ 'collapsed': sub.collapsed }">
                    <div class="subpolicy-header">
                      <div class="subpolicy-header-left">
                        <span class="subpolicy-title">Sub Policy {{ subIdx + 1 }}</span>
                        <button 
                          type="button" 
                          class="collapse-btn"
                          @click="toggleSubPolicyCollapse(stepIndex - 1, subIdx)"
                          :title="sub.collapsed ? 'Expand to show sub-policy details' : 'Collapse to hide sub-policy details'"
                        >
                          {{ sub.collapsed ? 'Expand' : 'Collapse' }}
                        </button>
                      </div>
                      <div class="subpolicy-actions">
                        <button 
                          type="button" 
                          class="exclude-btn" 
                          :class="{ 'excluded': sub.exclude }"
                          @click="toggleSubPolicyExclusion(stepIndex - 1, subIdx)"
                          :title="sub.exclude ? 'Click to include this sub-policy in the policy version' : 'Click to exclude this sub-policy from the policy version'"
                        >
                          {{ sub.exclude ? 'Excluded' : 'Exclude' }}
                        </button>
                        <button 
                          type="button" 
                          class="remove-btn"
                          @click="removeSubPolicy(stepIndex - 1, subIdx)"
                          title="Remove this sub-policy completely from the policy version"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <div v-if="!sub.collapsed" class="subpolicy-content">
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Title <span class="required-field">*</span></label>
                        <input 
                          type="text" 
                          v-model="sub.title" 
                          required 
                          :disabled="sub.exclude" 
                          placeholder="Enter sub-policy title"
                          :class="{ 'field-error': isSubmitting && !sub.exclude && !sub.title }"
                          title="Enter a descriptive name for this sub-policy version"
                        />
                        <span v-if="isSubmitting && !sub.exclude && !sub.title" class="error-text">Title is required</span>
                      </div>
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Description <span class="required-field">*</span></label>
                        <textarea 
                          v-model="sub.description" 
                          required 
                          :disabled="sub.exclude" 
                          placeholder="Enter sub-policy description"
                          :class="{ 'field-error': isSubmitting && !sub.exclude && !sub.description }"
                          title="Provide a detailed description of this sub-policy and what's new in this version"
                        ></textarea>
                        <span v-if="isSubmitting && !sub.exclude && !sub.description" class="error-text">Description is required</span>
                      </div>
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Control</label>
                        <textarea v-model="sub.control" required :disabled="sub.exclude" placeholder="Enter control details" title="Describe the specific controls or measures implemented by this sub-policy"></textarea>
                      </div>
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Identifier <span class="required-field">*</span></label>
                        <input 
                          type="text" 
                          v-model="sub.identifier" 
                          required 
                          :disabled="sub.exclude" 
                          placeholder="Enter identifier"
                          :class="{ 'field-error': isSubmitting && !sub.exclude && !sub.identifier }"
                          title="Enter a unique identifier or code for this sub-policy version"
                        />
                        <span v-if="isSubmitting && !sub.exclude && !sub.identifier" class="error-text">Identifier is required</span>
                      </div>
                    </div>
                    <div v-if="sub.collapsed" class="subpolicy-summary">
                      <strong>{{ sub.title || 'Untitled Subpolicy' }}</strong>
                      <span v-if="sub.identifier">({{ sub.identifier }})</span>
                    </div>
                  </div>
                  <div class="add-subpolicy-container">
                    <button 
                      type="button" 
                      class="add-btn add-subpolicy-btn prominent-btn" 
                      @click="addSubPolicy(stepIndex - 1)"
                      title="Add a new sub-policy to this policy version"
                    >
                      + Add Sub Policy (Count: {{ getSubpolicyCount(stepIndex - 1) }})
                    </button>
                    <button 
                      type="button" 
                      class="reset-btn" 
                      @click="resetSubPolicies(stepIndex - 1)"
                      v-if="policiesData[stepIndex - 1].subPolicies.length > 0"
                      title="Remove all sub-policies from this policy version (cannot be undone)"
                    >
                      Clear All Sub Policies
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <button class="create-btn" type="submit" :title="showPolicyDropdown ? 'Create a new version of the selected policy' : 'Create a new version of the selected framework'">
              {{ showPolicyDropdown ? 'Create Policy Version' : 'Create New Version' }}
            </button>
          </form>
        </div>
        <!-- Policy Form for Policy Versioning Mode (showPolicyDropdown) -->
        <div v-else>
          <form class="form-section policy-form" @submit.prevent="submitFrameworkForm">
            <h3 class="form-title">Policy Details</h3>
            <div v-for="(policy, policyIndex) in policiesData" :key="policyIndex" class="policy-form-container">
              <div class="policy-header">
                <h4>Policy Details</h4>
                <span v-if="!policy.id" class="policy-badge new-badge" title="This is a new policy being added">New Policy</span>
                <span v-else class="policy-badge existing-badge" title="This is an existing policy being versioned">Existing Policy</span>
                <button
                  v-if="policy.id"
                  type="button"
                  class="exclude-btn"
                  @click="excludePolicy(policyIndex)"
                  :class="{ 'excluded': policy.exclude }"
                  style="margin-left: 16px;"
                  :title="policy.exclude ? 'Click to include this policy' : 'Click to exclude this policy'"
                >
                  {{ policy.exclude ? 'Excluded' : 'Exclude' }}
                </button>
              </div>
              <div v-if="!policy.exclude">
                <div class="form-row">
                  <div class="form-group">
                    <label>Title <span class="required-field">*</span></label>
                    <input 
                      type="text" 
                      v-model="policy.title" 
                      required 
                      placeholder="Enter policy title" 
                      :class="{ 'field-error': isSubmitting && !policy.title }"
                      title="Enter a clear and descriptive name for this policy version"
                    />
                    <span v-if="isSubmitting && !policy.title" class="error-text">Title is required</span>
                  </div>
                  <div class="form-group">
                    <label>Description <span class="required-field">*</span></label>
                    <textarea 
                      v-model="policy.description" 
                      required 
                      placeholder="Enter policy description"
                      :class="{ 'field-error': isSubmitting && !policy.description }"
                      title="Provide a comprehensive description of what this policy covers and what's new in this version"
                    ></textarea>
                    <span v-if="isSubmitting && !policy.description" class="error-text">Description is required</span>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Objective</label>
                    <textarea v-model="policy.objective" required placeholder="Enter policy objective" title="Describe the main goals and objectives this policy aims to achieve"></textarea>
                  </div>
                  <div class="form-group">
                    <label>Scope</label>
                    <textarea v-model="policy.scope" required placeholder="Enter policy scope" title="Define the boundaries and areas covered by this policy"></textarea>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Department</label>
                    <input type="text" v-model="policy.department" required placeholder="Enter department" title="Specify the department or business unit responsible for this policy" />
                  </div>
                  <div class="form-group">
                    <label>Applicability</label>
                    <input type="text" v-model="policy.applicability" required placeholder="Enter applicability" title="Define who or what this policy applies to (e.g., all employees, specific roles, systems)" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" v-model="policy.startDate" required title="Select when this policy version becomes effective" />
                  </div>
                  <div class="form-group">
                    <label>End Date</label>
                    <input type="date" v-model="policy.endDate" required title="Select when this policy version expires or needs review" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Document URL</label>
                    <div class="input-with-icon" title="Upload a supporting document for this policy version">
                      <input
                        type="url"
                        v-model="policy.docURL"
                        placeholder="URL will appear here"
                        readonly
                        title="The document URL will appear here after upload"
                      />
                      <button type="button" class="browse-btn" @click="() => browsePolicyFile(policyIndex)" title="Browse and upload a policy document">Browse</button>
                      <input type="file" ref="policyFileInputs" style="display:none" @change="e => onPolicyFileChange(e, policyIndex)" />
                    </div>
                  </div>
                  <div class="form-group">
                    <label>Identifier <span class="required-field">*</span></label>
                    <input 
                      type="text" 
                      v-model="policy.identifier" 
                      required 
                      placeholder="Enter identifier"
                      :class="{ 'field-error': isSubmitting && !policy.identifier }"
                      title="Enter a unique identifier or code for this policy version"
                    />
                    <span v-if="isSubmitting && !policy.identifier" class="error-text">Identifier is required</span>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Coverage Rate (%)</label>
                    <input 
                      type="number" 
                      v-model="policy.coverageRate" 
                      min="0" 
                      max="100" 
                      step="0.01" 
                      placeholder="Enter coverage rate"
                      title="Enter the percentage of coverage this policy provides (0-100%)"
                    />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Policy Type</label>
                    <div class="searchable-select">
                      <input
                        type="text"
                        placeholder="Search or enter new policy type"
                        v-model="policy.PolicyType"
                        @input="handlePolicyTypeChange(policyIndex, $event.target.value)"
                        list="policyTypes"
                        :disabled="policy.exclude"
                        title="Select or enter the type/category of this policy (e.g., Security, Operational, Financial)"
                      />
                      <datalist id="policyTypes">
                        <option v-for="type in policyTypes" :key="type" :value="type">{{ type }}</option>
                      </datalist>
                    </div>
                  </div>
                  <div class="form-group">
                    <label>Policy Category</label>
                    <div class="searchable-select">
                      <input
                        type="text"
                        placeholder="Search or enter new category"
                        v-model="policy.PolicyCategory"
                        @input="handlePolicyCategoryChange(policyIndex, $event.target.value)"
                        list="policyCategories"
                        :disabled="!policy.PolicyType || policy.exclude"
                        title="Select or enter a more specific category within the policy type"
                      />
                      <datalist id="policyCategories">
                        <option v-for="cat in getCategoriesForType(policy.PolicyType)" :key="cat" :value="cat">{{ cat }}</option>
                      </datalist>
                    </div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Policy Sub Category</label>
                    <div class="searchable-select">
                      <input
                        type="text"
                        placeholder="Search or enter new sub category"
                        v-model="policy.PolicySubCategory"
                        @input="handlePolicySubCategoryChange(policyIndex, $event.target.value)"
                        list="policySubCategories"
                        :disabled="!policy.PolicyCategory || policy.exclude"
                        title="Select or enter a detailed sub-category for precise policy classification"
                      />
                      <datalist id="policySubCategories">
                        <option v-for="sub in getSubCategoriesForCategory(policy.PolicyType, policy.PolicyCategory)" :key="sub" :value="sub">{{ sub }}</option>
                      </datalist>
                    </div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Created By</label>
                    <select v-model="policy.createdByName" required title="Select the person responsible for creating this policy version">
                      <option value="">Select Creator</option>
                      <option v-for="user in users" :key="user.UserId" :value="user.UserName">
                        {{ user.UserName }}
                      </option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Reviewer</label>
                    <select v-model="policy.reviewer" required title="Select the person who will review and approve this policy version">
                      <option value="">Select Reviewer</option>
                      <option v-for="user in users" :key="user.UserId" :value="user.UserName">
                        {{ user.UserName }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="subpolicies-section">
                  <div class="subpolicies-header">
                    <h4>Sub Policies</h4>
                    <div>
                      <span class="subpolicy-counter" title="Number of active sub-policies in this policy version">{{ policy.subPolicies.filter(sp => !sp.exclude).length }} sub-policies</span>
                      <button 
                        type="button" 
                        class="debug-btn" 
                        @click="debugSubpolicies(policyIndex)"
                        title="Debug sub-policy data for troubleshooting"
                      >
                        Debug
                      </button>
                    </div>
                  </div>
                  <div v-for="(sub, subIdx) in policy.subPolicies" :key="subIdx" class="subpolicy-card" :class="{ 'collapsed': sub.collapsed }">
                    <div class="subpolicy-header">
                      <div class="subpolicy-header-left">
                        <span class="subpolicy-title">Sub Policy {{ subIdx + 1 }}</span>
                        <button 
                          type="button" 
                          class="collapse-btn"
                          @click="toggleSubPolicyCollapse(policyIndex, subIdx)"
                          :title="sub.collapsed ? 'Expand to show sub-policy details' : 'Collapse to hide sub-policy details'"
                        >
                          {{ sub.collapsed ? 'Expand' : 'Collapse' }}
                        </button>
                      </div>
                      <div class="subpolicy-actions">
                        <button 
                          type="button" 
                          class="exclude-btn" 
                          :class="{ 'excluded': sub.exclude }"
                          @click="toggleSubPolicyExclusion(policyIndex, subIdx)"
                          :title="sub.exclude ? 'Click to include this sub-policy in the policy version' : 'Click to exclude this sub-policy from the policy version'"
                        >
                          {{ sub.exclude ? 'Excluded' : 'Exclude' }}
                        </button>
                        <button 
                          type="button" 
                          class="remove-btn"
                          @click="removeSubPolicy(policyIndex, subIdx)"
                          title="Remove this sub-policy completely from the policy version"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <div v-if="!sub.collapsed" class="subpolicy-content">
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Title <span class="required-field">*</span></label>
                        <input 
                          type="text" 
                          v-model="sub.title" 
                          required 
                          :disabled="sub.exclude" 
                          placeholder="Enter sub-policy title"
                          :class="{ 'field-error': isSubmitting && !sub.exclude && !sub.title }"
                          title="Enter a descriptive name for this sub-policy version"
                        />
                        <span v-if="isSubmitting && !sub.exclude && !sub.title" class="error-text">Title is required</span>
                      </div>
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Description <span class="required-field">*</span></label>
                        <textarea 
                          v-model="sub.description" 
                          required 
                          :disabled="sub.exclude" 
                          placeholder="Enter sub-policy description"
                          :class="{ 'field-error': isSubmitting && !sub.exclude && !sub.description }"
                          title="Provide a detailed description of this sub-policy and what's new in this version"
                        ></textarea>
                        <span v-if="isSubmitting && !sub.exclude && !sub.description" class="error-text">Description is required</span>
                      </div>
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Control</label>
                        <textarea v-model="sub.control" required :disabled="sub.exclude" placeholder="Enter control details" title="Describe the specific controls or measures implemented by this sub-policy"></textarea>
                      </div>
                      <div class="form-group" :class="{ 'excluded': sub.exclude }">
                        <label>Identifier <span class="required-field">*</span></label>
                        <input 
                          type="text" 
                          v-model="sub.identifier" 
                          required 
                          :disabled="sub.exclude" 
                          placeholder="Enter identifier"
                          :class="{ 'field-error': isSubmitting && !sub.exclude && !sub.identifier }"
                          title="Enter a unique identifier or code for this sub-policy version"
                        />
                        <span v-if="isSubmitting && !sub.exclude && !sub.identifier" class="error-text">Identifier is required</span>
                      </div>
                    </div>
                    <div v-if="sub.collapsed" class="subpolicy-summary">
                      <strong>{{ sub.title || 'Untitled Subpolicy' }}</strong>
                      <span v-if="sub.identifier">({{ sub.identifier }})</span>
                    </div>
                  </div>
                  <div class="add-subpolicy-container">
                    <button 
                      type="button" 
                      class="add-btn add-subpolicy-btn prominent-btn" 
                      @click="addSubPolicy(policyIndex)"
                      title="Add a new sub-policy to this policy version"
                    >
                      + Add Sub Policy (Count: {{ getSubpolicyCount(policyIndex) }})
                    </button>
                    <button 
                      type="button" 
                      class="reset-btn" 
                      @click="resetSubPolicies(policyIndex)"
                      v-if="policy.subPolicies.length > 0"
                      title="Remove all sub-policies from this policy version (cannot be undone)"
                    >
                      Clear All Sub Policies
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <button class="create-btn" type="submit" :title="showPolicyDropdown ? 'Create a new version of the selected policy' : 'Create a new version of the selected framework'">
              {{ showPolicyDropdown ? 'Create Policy Version' : 'Create New Version' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Add loading overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>Processing your request...</p>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { PopupService, PopupModal } from '@/modules/popup'

const API_BASE_URL = 'http://localhost:8000/api'

export default {
  name: 'PolicyVersioning',
  components: {
    PopupModal
  },
  setup() {
    const { proxy } = getCurrentInstance()
    const selectedFramework = ref('')
    const selectedPolicy = ref('')
    const showStepper = ref(false)
    const showPolicyDropdown = ref(false)
    const stepIndex = ref(0)
    const loading = ref(false)
    const error = ref(null)
    const isSubmitting = ref(false)

    const frameworks = ref([])
    const policyOptions = ref([])
    const users = ref([])

    const frameworkData = ref({
      title: '',
      description: '',
      category: '',
      startDate: '',
      endDate: '',
      docURL: '',
      identifier: '',
      createdByName: '',
      reviewer: ''
    })

    const policiesData = ref([{
      title: '',
      description: '',
      objective: '',
      scope: '',
      department: '',
      applicability: '',
      startDate: '',
      endDate: '',
      docURL: '',
      identifier: '',
      createdByName: '',
      reviewer: '',
      coverageRate: null,
      subPolicies: [],
      exclude: false,
      PolicyType: '',
      PolicyCategory: '',
      PolicySubCategory: ''
    }])

    const frameworkFileName = ref('')
    const frameworkFileInput = ref(null)
    const browseFrameworkFile = () => {
      proxy.$refs.frameworkFileInput.click()
    }
    const onFrameworkFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      const formData = new FormData()
      formData.append('file', file)
      formData.append('type', 'framework')
      formData.append('fileName', file.name)
      try {
        const res = await axios.post('http://localhost:3000/api/upload', formData)
        // Support both { url: ... } and { file: { url: ... } }
        frameworkData.value.docURL = res.data.url || (res.data.file && res.data.file.url) || ''
      } catch (err) {
        PopupService.error('Failed to upload framework document', 'Upload Error')
      }
    }

    // Fetch frameworks for dropdown
    const fetchFrameworks = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/frameworks/`)
        frameworks.value = response.data.map(fw => ({
          id: fw.FrameworkId,
          name: fw.FrameworkName
        }))
      } catch (err) {
        console.error('Error fetching frameworks:', err)
        PopupService.error('Failed to fetch frameworks', 'Loading Error')
      }
    }

    // Fetch framework details when selected
    const onFrameworkDropdown = async () => {
      if (!selectedFramework.value) return
      
      try {
        loading.value = true
        const response = await axios.get(`${API_BASE_URL}/frameworks/${selectedFramework.value}/`)
        
        // Populate framework data
        frameworkData.value = {
          title: response.data.FrameworkName,
          description: response.data.FrameworkDescription,
          category: response.data.Category,
          startDate: response.data.StartDate,
          endDate: response.data.EndDate,
          docURL: response.data.DocURL,
          identifier: response.data.Identifier,
          createdByName: response.data.CreatedByName,
          reviewer: response.data.Reviewer
        }

        // Populate policies data with framework's CreatedByName and Reviewer
        policiesData.value = response.data.policies.map(p => ({
          id: p.PolicyId,
          title: p.PolicyName,
          description: p.PolicyDescription,
          objective: p.Objective || '',
          scope: p.Scope || '',
          department: p.Department || '',
          applicability: p.Applicability || '',
          startDate: p.StartDate || '',
          endDate: p.EndDate || '',
          docURL: p.DocURL || '',
          identifier: p.Identifier || '',
          createdByName: response.data.CreatedByName, // Use framework's CreatedByName
          reviewer: response.data.Reviewer, // Use framework's Reviewer
          coverageRate: p.CoverageRate || null,
          exclude: false,
          subPolicies: Array.isArray(p.subpolicies) 
            ? p.subpolicies.map(sp => ({
            id: sp.SubPolicyId,
                title: sp.SubPolicyName || '',
                description: sp.Description || '',
                control: sp.Control || '',
                identifier: sp.Identifier || '',
                exclude: false,
                collapsed: false,
                Status: sp.Status || 'Under Review',
                PermanentTemporary: sp.PermanentTemporary || ''
          }))
            : [],
          PolicyType: p.PolicyType || '',
          PolicyCategory: p.PolicyCategory || '',
          PolicySubCategory: p.PolicySubCategory || ''
        }))

        showStepper.value = true
        stepIndex.value = 0
        showPolicyDropdown.value = false
        selectedPolicy.value = ''
      } catch (err) {
        console.error('Error fetching framework details:', err)
        PopupService.error('Failed to fetch framework details', 'Loading Error')
      } finally {
        loading.value = false
      }
    }

    // Fetch policies for dropdown
    const fetchPolicies = async () => {
      try {
        loading.value = true
        const response = await axios.get(`${API_BASE_URL}/policies/`)
        // Check if response.data has a policies property and filter for Approved and Active policies
        const policiesData = response.data.policies || response.data
        policyOptions.value = policiesData
          .filter(p => p.Status === 'Approved' && p.ActiveInactive === 'Active')
          .map(p => ({
            id: p.PolicyId,
            title: p.PolicyName,
            description: p.PolicyDescription
          }))
      } catch (err) {
        console.error('Error fetching policies:', err)
        PopupService.error('Failed to fetch policies', 'Loading Error')
      } finally {
        loading.value = false
      }
    }

    // Fetch policy details when selected
    const onPolicyDropdown = async () => {
      if (selectedPolicy.value === '') return
      
      try {
        loading.value = true
        const selectedPolicyData = policyOptions.value[selectedPolicy.value]
        if (!selectedPolicyData?.id) {
          throw new Error('Invalid policy selection')
        }

        const response = await axios.get(`${API_BASE_URL}/policies/${selectedPolicyData.id}/`)
        
        // Verify policy is Approved and Active
        if (response.data.Status !== 'Approved' || response.data.ActiveInactive !== 'Active') {
          throw new Error('Only Approved and Active policies can be versioned')
        }
        
        // Reset framework selection since it's not needed for policy versioning
        selectedFramework.value = ''
        
        // Populate single policy data
        policiesData.value = [{
          id: response.data.PolicyId,
          title: response.data.PolicyName,
          description: response.data.PolicyDescription,
          objective: response.data.Objective || '',
          scope: response.data.Scope || '',
          department: response.data.Department || '',
          applicability: response.data.Applicability || '',
          startDate: response.data.StartDate || '',
          endDate: response.data.EndDate || '',
          docURL: response.data.DocURL || '',
          identifier: response.data.Identifier || '',
          createdByName: response.data.CreatedByName || '',
          reviewer: response.data.Reviewer || '',
          // Filter for only Approved and Active subpolicies
          subPolicies: (response.data.subpolicies || [])
            .filter(sp => sp.Status === 'Approved')
            .map(sp => ({
              id: sp.SubPolicyId,
              title: sp.SubPolicyName,
              description: sp.Description,
              control: sp.Control || '',
              identifier: sp.Identifier || ''
            })),
          PolicyType: response.data.PolicyType || '',
          PolicyCategory: response.data.PolicyCategory || '',
          PolicySubCategory: response.data.PolicySubCategory || ''
        }]

      showStepper.value = true
        stepIndex.value = 0 // Show policy details immediately
      showPolicyDropdown.value = true
      } catch (err) {
        console.error('Error fetching policy details:', err)
        PopupService.error(err.message || 'Failed to fetch policy details', 'Loading Error')
        policiesData.value = []
      } finally {
        loading.value = false
      }
    }

    const switchToPolicy = () => {
      showPolicyDropdown.value = true
      selectedFramework.value = ''
      showStepper.value = false
      stepIndex.value = 0
      policiesData.value = [{
        title: '',
        description: '',
        objective: '',
        scope: '',
        department: '',
        applicability: '',
        startDate: '',
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: '',
        reviewer: '',
        coverageRate: null,
        subPolicies: []
      }]
      frameworkData.value = {
        title: '',
        description: '',
        category: '',
        startDate: '',
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: '',
        reviewer: ''
      }
      fetchPolicies() // Fetch policies when switching to policy view
    }

    const switchToFramework = () => {
      showPolicyDropdown.value = false
      selectedPolicy.value = ''
      showStepper.value = false
      stepIndex.value = 0
      policiesData.value = [{
        title: '',
        description: '',
        objective: '',
        scope: '',
        department: '',
        applicability: '',
        startDate: '',
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: '',
        reviewer: '',
        coverageRate: null,
        subPolicies: []
      }]
      frameworkData.value = {
        title: '',
        description: '',
        category: '',
        startDate: '',
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: '',
        reviewer: ''
      }
      fetchFrameworks()
    }

    const addPolicy = () => {
      policiesData.value.push({
        title: '',
        description: '',
        objective: '',
        scope: '',
        department: '',
        applicability: '',
        startDate: new Date().toISOString().split('T')[0], // Default to today
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: frameworkData.value.createdByName || '', // Inherit from framework
        reviewer: frameworkData.value.reviewer || '', // Inherit from framework
        coverageRate: null,
        subPolicies: [], // Initialize as empty array
        exclude: false,
        PolicyType: '',
        PolicyCategory: '',
        PolicySubCategory: ''
      })
      console.log('Added new policy. Policy count:', policiesData.value.length)
      console.log('New policy has subPolicies array:', Array.isArray(policiesData.value[policiesData.value.length-1].subPolicies))
      stepIndex.value = policiesData.value.length // Go to new policy tab
    }

    const removePolicy = (idx) => {
      // If this is an existing policy, mark it for exclusion in the API request
      if (policiesData.value[idx].id) {
        policiesData.value[idx].exclude = true
      } else {
        // If it's a new policy, remove it from the array
      policiesData.value.splice(idx, 1)
      }
      if (stepIndex.value > idx) stepIndex.value--
      if (stepIndex.value >= stepTabs.value.length) stepIndex.value = stepTabs.value.length - 1
    }

    const toggleSubPolicyExclusion = (policyIdx, subIdx) => {
      // Create a temp copy of the entire policies array
      const policiesCopy = JSON.parse(JSON.stringify(policiesData.value));
      
      // Toggle the exclude state in the copy
      policiesCopy[policyIdx].subPolicies[subIdx].exclude = 
        !policiesCopy[policyIdx].subPolicies[subIdx].exclude;
      
      // Replace the entire array to trigger reactivity
      policiesData.value = policiesCopy;
    }

    const removeSubPolicy = (policyIdx, subIdx) => {
      console.log('Removing subpolicy at index', subIdx, 'from policy', policyIdx);
      
      // Create a temp copy of the entire policies array
      const policiesCopy = JSON.parse(JSON.stringify(policiesData.value));
      
      // Remove the subpolicy from the copy
      policiesCopy[policyIdx].subPolicies.splice(subIdx, 1);
      
      // Replace the entire array to trigger reactivity
      policiesData.value = policiesCopy;
      
      console.log('Subpolicy removed. Total count:', policiesData.value[policyIdx].subPolicies.length);
    };

    const addSubPolicy = (policyIdx) => {
      console.log('Adding subpolicy to policy index:', policyIdx);
      
      // Create a temp copy of the entire policies array
      const policiesCopy = JSON.parse(JSON.stringify(policiesData.value));
      
      // Create the new subpolicy
      const newSubPolicy = {
        title: '',
        description: '',
        control: '',
        identifier: '',
        exclude: false,
        collapsed: false,
        Status: 'Under Review',
        PermanentTemporary: ''
      };
      
      // Ensure the subPolicies array exists
      if (!Array.isArray(policiesCopy[policyIdx].subPolicies)) {
        policiesCopy[policyIdx].subPolicies = [];
      }
      
      // Add the new subpolicy to the copy
      policiesCopy[policyIdx].subPolicies.push(newSubPolicy);
      
      // Replace the entire array to trigger reactivity
      policiesData.value = policiesCopy;
      
      console.log('New subpolicy added. Total count:', policiesData.value[policyIdx].subPolicies.length);
    };

    const closeTab = (idx) => {
      if (idx === 0) return // Don't close framework tab
      removePolicy(idx - 1)
    }

    // Add a function to check and repair subpolicies array if needed
    const ensureSubPoliciesArray = () => {
      for (let i = 0; i < policiesData.value.length; i++) {
        const policy = policiesData.value[i];
        if (!Array.isArray(policy.subPolicies)) {
          console.warn(`Policy at index ${i} has invalid subPolicies. Fixing...`);
          policy.subPolicies = [];
        }
      }
    }

    // Modify the submitFrameworkForm function to handle policy versioning correctly
    const submitFrameworkForm = async () => {
      try {
        isSubmitting.value = true;
        error.value = null;
        
        // Save any new policy categories before form submission
        await saveNewPolicyCategories();
        
        // Ensure all policies have a valid subPolicies array
        ensureSubPoliciesArray();
        
        // Validate framework data in framework mode
        if (!showPolicyDropdown.value && stepIndex.value === 0) {
          if (!frameworkData.value.title) {
            PopupService.error('Framework title is required', 'Validation Error');
            return;
          }
          if (!frameworkData.value.description) {
            PopupService.error('Framework description is required', 'Validation Error');
            return;
          }
          if (!frameworkData.value.identifier) {
            PopupService.error('Framework identifier is required', 'Validation Error');
            return;
          }
          if (!frameworkData.value.createdByName) {
            PopupService.error('Created By is required', 'Validation Error');
            return;
          }
          if (!frameworkData.value.reviewer) {
            PopupService.error('Reviewer is required', 'Validation Error');
            return;
          }
        }
        
        // Validate policies in both modes
          for (const policy of policiesData.value) {
          if (policy.exclude) continue;
          
          if (!policy.title) {
            PopupService.error('Policy title is required', 'Validation Error');
            return;
          }
          if (!policy.description) {
            PopupService.error('Policy description is required', 'Validation Error');
            return;
          }
          if (!policy.identifier) {
            PopupService.error('Policy identifier is required', 'Validation Error');
            return;
          }
          
          // Validate subpolicies
          for (const subpolicy of policy.subPolicies) {
            if (subpolicy.exclude) continue;
            
            if (!subpolicy.title) {
              PopupService.error('Subpolicy title is required', 'Validation Error');
              return;
            }
            if (!subpolicy.description) {
              PopupService.error('Subpolicy description is required', 'Validation Error');
              return;
            }
            if (!subpolicy.identifier) {
              PopupService.error('Subpolicy identifier is required', 'Validation Error');
              return;
            }
          }
        }
        
        // If validation passes, proceed with API calls
        loading.value = true;

        if (showPolicyDropdown.value) {
          // Create new policy version - should only have one policy
          if (policiesData.value.length === 0 || policiesData.value[0].exclude) {
            throw new Error('No policy data to submit')
          }
          
          const policy = policiesData.value[0] // Get the first (and only) policy

          // Separate existing and new subpolicies
          const existingSubpolicies = [];
          const newSubpolicies = [];
          for (const sp of policy.subPolicies) {
            if (sp.id) {
              // Existing subpolicy
              if (sp.exclude) {
                existingSubpolicies.push({ original_subpolicy_id: sp.id, exclude: true });
              } else {
                existingSubpolicies.push({
                  original_subpolicy_id: sp.id,
                  SubPolicyName: sp.title,
                  Description: sp.description,
                  Control: sp.control,
                  Identifier: sp.identifier,
                  PermanentTemporary: ''
                });
              }
            } else if (!sp.exclude) {
              // New subpolicy (no id, not excluded)
              newSubpolicies.push({
                SubPolicyName: sp.title,
                Description: sp.description,
                Control: sp.control,
                Identifier: sp.identifier,
                PermanentTemporary: ''
              });
            }
          }

            const policyData = {
              PolicyName: policy.title,
              PolicyDescription: policy.description,
              StartDate: policy.startDate,
              EndDate: policy.endDate,
              Department: policy.department,
              Applicability: policy.applicability,
              DocURL: policy.docURL,
              Scope: policy.scope,
              Objective: policy.objective,
              Identifier: policy.identifier,
              CreatedByName: policy.createdByName,
              Reviewer: users.value.find(u => u.UserName === policy.reviewer)?.UserId || null,
              CoverageRate: policy.coverageRate || 0,
              CreatedByDate: new Date().toISOString().split('T')[0],
              PermanentTemporary: '',
              subpolicies: existingSubpolicies,
              new_subpolicies: newSubpolicies,
              PolicyType: policy.PolicyType,
              PolicyCategory: policy.PolicyCategory,
              PolicySubCategory: policy.PolicySubCategory
            };

            console.log('Submitting policy version with data:', policyData);

            try {
              await axios.post(`${API_BASE_URL}/policies/${policy.id}/create-version/`, policyData);
              PopupService.success(`Successfully created new version for policy "${policy.title}"`, 'Policy Version Created');
            } catch (err) {
              console.error('Policy version creation error:', err.response?.data);
              PopupService.error(err.response?.data?.error || 'Failed to create policy version', 'Creation Error');
              return; // Stop execution on error
            }
        } else {
          // Create new framework version
          const existingPolicies = policiesData.value.filter(p => p.id); // include all existing policies
          const newPolicies = policiesData.value.filter(p => !p.id && !p.exclude);

          // Get both the reviewer ID and name for the framework
          const reviewerUser = users.value.find(u => u.UserName === frameworkData.value.reviewer);
          const reviewerId = reviewerUser?.UserId || null;
          const reviewerName = frameworkData.value.reviewer || '';
          
          const apiData = {
            FrameworkName: frameworkData.value.title,
            FrameworkDescription: frameworkData.value.description,
            Category: frameworkData.value.category,
            StartDate: frameworkData.value.startDate,
            EndDate: frameworkData.value.endDate,
            DocURL: frameworkData.value.docURL,
            Identifier: frameworkData.value.identifier,
            CreatedByName: frameworkData.value.createdByName,
            Reviewer: reviewerId,
            ReviewerName: reviewerName,
          };

                          // Add existing policies (with original_policy_id)
          if (existingPolicies.length > 0) {
            apiData.policies = existingPolicies.map(p => {
              if (p.exclude) {
                return {
                  original_policy_id: p.id,
                  exclude: true
                };
              } else {
                // Get both the reviewer ID and name
                const reviewerUser = users.value.find(u => u.UserName === frameworkData.value.reviewer);
                const reviewerId = reviewerUser?.UserId || null;
                const reviewerName = frameworkData.value.reviewer || '';
                
                const policyData = {
                  original_policy_id: p.id,
                  PolicyName: p.title,
                  PolicyDescription: p.description,
                  Objective: p.objective,
                  Scope: p.scope,
                  Department: p.department,
                  Applicability: p.applicability,
                  StartDate: p.startDate,
                  EndDate: p.endDate,
                  DocURL: p.docURL,
                  Identifier: p.identifier,
                  CreatedByName: frameworkData.value.createdByName,
                  Reviewer: reviewerId,
                  ReviewerName: reviewerName,
                  CoverageRate: p.coverageRate || 0,
                  PolicyType: p.PolicyType,
                  PolicyCategory: p.PolicyCategory,
                  PolicySubCategory: p.PolicySubCategory
                };
                
                // Ensure subpolicies array is properly added even for existing policies
                if (Array.isArray(p.subPolicies) && p.subPolicies.length > 0) {
                  policyData.subpolicies = p.subPolicies.map(sp => {
                    if (sp.exclude) {
                      return { original_subpolicy_id: sp.id, exclude: true };
                    } else if (sp.id) {
                      // Existing subpolicy
                      return {
                        original_subpolicy_id: sp.id,
                        SubPolicyName: sp.title,
                        Description: sp.description,
                        Control: sp.control,
                        Identifier: sp.identifier,
                        Status: 'Under Review'
                      };
                    } else {
                      // New subpolicy added to existing policy
                      return {
                        SubPolicyName: sp.title,
                        Description: sp.description,
                        Control: sp.control,
                        Identifier: sp.identifier,
                        Status: 'Under Review'
                      };
                    }
                  });
                } else {
                  policyData.subpolicies = [];
                }
                
                return policyData;
              }
            });
          }

          // Add new policies to new_policies array
          if (newPolicies.length > 0) {
            apiData.new_policies = newPolicies.map(p => {
              // Validate required fields for new policies
              if (!p.title || !p.description || !p.identifier) {
                error.value = `New policy missing required fields: ${!p.title ? 'Title, ' : ''}${!p.description ? 'Description, ' : ''}${!p.identifier ? 'Identifier' : ''}`;
                throw new Error(error.value);
              }
              
              // Get both the reviewer ID and name for the new policy
              const reviewerUser = users.value.find(u => u.UserName === frameworkData.value.reviewer);
              const reviewerId = reviewerUser?.UserId || null;
              const reviewerName = frameworkData.value.reviewer || '';
              
              return {
                PolicyName: p.title,
                PolicyDescription: p.description,
                Objective: p.objective,
                Scope: p.scope,
                Department: p.department,
                Applicability: p.applicability,
                StartDate: p.startDate,
                EndDate: p.endDate,
                DocURL: p.docURL,
                Identifier: p.identifier,
                CreatedByName: frameworkData.value.createdByName,
                Reviewer: reviewerId,
                ReviewerName: reviewerName,
                CoverageRate: p.coverageRate || 0,
                subpolicies: p.subPolicies.filter(sp => !sp.exclude).map(sp => {
                  // Validate required fields for subpolicies
                  if (!sp.title || !sp.description || !sp.identifier) {
                    error.value = `Subpolicy missing required fields: ${!sp.title ? 'Title, ' : ''}${!sp.description ? 'Description, ' : ''}${!sp.identifier ? 'Identifier' : ''}`;
                    throw new Error(error.value);
                  }
                  return {
                    SubPolicyName: sp.title,
                    Description: sp.description,
                    Control: sp.control,
                    Identifier: sp.identifier,
                    Status: 'Under Review',
                    PermanentTemporary: ''
                  };
                }),
                PolicyType: p.PolicyType,
                PolicyCategory: p.PolicyCategory,
                PolicySubCategory: p.PolicySubCategory
              };
            });
          }

          // Before the API call, add this debugging info
          console.log('Framework versioning - Existing policies:', existingPolicies.length);
          console.log('Framework versioning - New policies:', newPolicies.length);
          if (newPolicies.length > 0) {
            console.log('New policies details:', newPolicies.map(p => ({
              title: p.title,
              subPoliciesCount: p.subPolicies.filter(sp => !sp.exclude).length,
              coverageRate: p.coverageRate
            })));
          }
          console.log('Submitting framework version with data:', apiData);

          try {
            const result = await axios.post(`${API_BASE_URL}/frameworks/${selectedFramework.value}/create-version/`, apiData);
            PopupService.success(`Successfully created new framework version: ${result.data.FrameworkName} (Version ${result.data.NewVersion}.0)`, 'Framework Version Created');
          } catch (err) {
            console.error('Framework version creation error:', err.response?.data);
            PopupService.error(err.response?.data?.error || 'Failed to create framework version', 'Creation Error');
            return; // Stop execution on error
          }
        }

        // Reset form after successful submission
        resetForm()
      } catch (err) {
        handleError(err)
      } finally {
        loading.value = false
        // Keep isSubmitting true if there were validation errors
        if (!error.value) {
          isSubmitting.value = false;
        }
      }
    }

    // Add helper function to reset form
    const resetForm = () => {
      showStepper.value = false
      selectedFramework.value = ''
      selectedPolicy.value = ''
      policiesData.value = [{
        title: '',
        description: '',
        objective: '',
        scope: '',
        department: '',
        applicability: '',
        startDate: '',
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: '',
        reviewer: '',
        coverageRate: null,
        subPolicies: []
      }]
      frameworkData.value = {
        title: '',
        description: '',
        category: '',
        startDate: '',
        endDate: '',
        docURL: '',
        identifier: '',
        createdByName: '',
        reviewer: ''
      }
    }

    // Add helper function to handle errors
    const handleError = (err) => {
      console.error('Error submitting form:', err);
      const errorData = err.response?.data;
      let errorMessage = 'Failed to submit form';
      
      if (typeof errorData === 'object') {
        if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.details?.error) {
          errorMessage = errorData.details.error;
        } else {
          // Try to extract error message from the response object
          errorMessage = JSON.stringify(errorData);
        }
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      }
      
      PopupService.error(errorMessage, 'Submission Error');
      console.log('Full error details:', {
        error: errorData,
        status: err.response?.status,
        headers: err.response?.headers
      });
    }

    // Computed property for step tabs - show only policy tab in policy mode
    const stepTabs = computed(() => {
      if (showPolicyDropdown.value) {
        return [{ key: 'policy', label: 'Policy Details' }]
      }
      return [
        { key: 'framework', label: 'Framework' },
        ...policiesData.value.map((p, i) => ({ key: `policy${i+1}`, label: `Policy ${i+1}` }))
      ]
    })

    // Add function to fetch users
    const fetchUsers = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/users/`)
        users.value = response.data
      } catch (err) {
        console.error('Error fetching users:', err)
        PopupService.error('Failed to fetch users', 'Loading Error')
      }
    }

    // Modify onMounted to fetch users
    onMounted(() => {
      fetchFrameworks()
      fetchUsers()
      fetchPolicyCategories()
    })

    const toggleSubPolicyCollapse = (policyIdx, subIdx) => {
      // Create a temp copy of the entire policies array
      const policiesCopy = JSON.parse(JSON.stringify(policiesData.value));
      
      // Toggle the collapsed state in the copy
      policiesCopy[policyIdx].subPolicies[subIdx].collapsed = 
        !policiesCopy[policyIdx].subPolicies[subIdx].collapsed;
      
      // Replace the entire array to trigger reactivity
      policiesData.value = policiesCopy;
    };

    const debugSubpolicies = (policyIdx) => {
      console.log('DEBUG - Policy index:', policyIdx);
      console.log('DEBUG - Subpolicies count:', policiesData.value[policyIdx].subPolicies.length);
      console.log('DEBUG - Subpolicies array:', JSON.stringify(policiesData.value[policyIdx].subPolicies));
      
      // Show alert with count for immediate feedback
      alert(`This policy has ${policiesData.value[policyIdx].subPolicies.length} subpolicies. Check browser console for details.`);
    };

    // Update the resetSubPolicies function to use the same pattern
    const resetSubPolicies = (policyIdx) => {
      if (confirm('Are you sure you want to remove all subpolicies? This cannot be undone.')) {
        console.log('Resetting all subpolicies for policy at index', policyIdx);
        
        // Create a temp copy of the entire policies array
        const policiesCopy = JSON.parse(JSON.stringify(policiesData.value));
        
        // Reset the subpolicies to an empty array
        policiesCopy[policyIdx].subPolicies = [];
        
        // Replace the entire array to trigger reactivity
        policiesData.value = policiesCopy;
        
        console.log('All subpolicies removed. Current count:', policiesData.value[policyIdx].subPolicies.length);
      }
    };

    // Add a computed property to track subpolicy counts
    const getSubpolicyCount = (policyIndex) => {
      if (!policiesData.value[policyIndex] || 
          !Array.isArray(policiesData.value[policyIndex].subPolicies)) {
        return 0;
      }
      return policiesData.value[policyIndex].subPolicies.length;
    };

    // Add the excludePolicy method to setup()
    const excludePolicy = (policyIdx) => {
      // Create a deep copy to keep reactivity
      const policiesCopy = JSON.parse(JSON.stringify(policiesData.value));

      // Mark the policy as excluded instead of removing it
      policiesCopy[policyIdx].exclude = true;

      // Update the reactive array
      policiesData.value = policiesCopy;

      // Adjust stepIndex if needed
      if (stepIndex.value >= policiesData.value.length) {
        stepIndex.value = Math.max(0, policiesData.value.length - 1);
      }
    };

    // For policies
    const browsePolicyFile = (/* policyIndex */) => {
      // Use the $refs.policyFileInputs as an array of file inputs
      if (proxy.$refs.policyFileInputs) {
        // If it's an array, try to find an appropriate element to click
        if (Array.isArray(proxy.$refs.policyFileInputs)) {
          const fileInputs = proxy.$refs.policyFileInputs;
          if (fileInputs.length > 0) {
            // Just click the first available file input
            fileInputs[0].click();
            return;
          }
        } else {
          // If it's a single element, just click it
          proxy.$refs.policyFileInputs.click();
          return;
        }
      }
      
      console.error('File input reference not found');
      error.value = 'Could not access file upload control';
    }
    const onPolicyFileChange = async (event, policyIndex) => {
      const file = event.target.files[0]
      if (!file) return
      const formData = new FormData()
      formData.append('file', file)
      formData.append('type', 'policy')
      formData.append('fileName', file.name)
      try {
        const res = await axios.post('http://localhost:3000/api/upload', formData)
        // Support both { url: ... } and { file: { url: ... } }
        policiesData.value[policyIndex].docURL = res.data.url || (res.data.file && res.data.file.url) || ''
      } catch (err) {
        PopupService.error('Failed to upload policy document', 'Upload Error')
      }
    }

    // Add helper functions for policy approval/rejection
    const submitPolicyReview = async (approvalId, isApproved, remarks = '') => {
      try {
        loading.value = true;
        error.value = null;
        
        // Prepare the review data
        const reviewData = {
          ApprovedNot: isApproved,
          ExtractedData: {
            policy_approval: {
              approved: isApproved,
              remarks: remarks || (isApproved ? 'Approved' : 'Rejected'),
              review_date: new Date().toISOString().split('T')[0]
            }
          }
        };
        
        // Submit the review
        const endpoint = isApproved 
          ? `${API_BASE_URL}/api/policy-approvals/${approvalId}/review/` 
          : `${API_BASE_URL}/api/policy-approvals/${approvalId}/reject/`;
          
        const response = await axios.put(endpoint, reviewData);
        
        PopupService.success(`Policy has been ${isApproved ? 'approved' : 'rejected'} successfully!`, 'Review Complete');
        return response.data;
      } catch (err) {
        console.error('Error submitting policy review:', err);
        PopupService.error(err.response?.data?.error || `Failed to ${isApproved ? 'approve' : 'reject'} policy`, 'Review Error');
        throw err;
      } finally {
        loading.value = false;
      }
    };

    // New function to approve a policy version and deactivate previous versions
    const approvePolicyVersion = async (policyId, remarks = '') => {
      try {
        loading.value = true;
        error.value = null;
        
        console.log(`Approving policy version: ${policyId}`);
        
        // Use the new endpoint that handles both approval and deactivation of previous versions
        const response = await axios.put(
          `${API_BASE_URL}/policies/${policyId}/approve-version/`,
          {
            approved: true,
            remarks: remarks || 'Approved via versioning interface',
            approval_date: new Date().toISOString().split('T')[0]
          }
        );
        
        console.log('Policy version approval response:', response.data);
        
        // Show success message with information about deactivated versions
        const deactivatedCount = response.data.deactivated_previous_versions || 0;
        const message = deactivatedCount > 0 
          ? `Policy approved successfully! ${deactivatedCount} previous versions have been deactivated.`
          : 'Policy approved successfully!';
          
        PopupService.success(message, 'Policy Approved');
        
        return response.data;
      } catch (err) {
        console.error('Error approving policy version:', err);
        PopupService.error(err.response?.data?.error || 'Failed to approve policy version', 'Approval Error');
        PopupService.error(`Error approving policy: ${err.response?.data?.error || err.message}`, 'Approval Error');
        throw err;
      } finally {
        loading.value = false;
      }
    };
    
    const resubmitRejectedPolicy = async (policyId, updateData) => {
      try {
        loading.value = true;
        error.value = null;
        
        const response = await axios.put(
          `${API_BASE_URL}/policies/${policyId}/resubmit-approval/`, 
          updateData
        );
        
        PopupService.success('Policy has been resubmitted successfully!', 'Policy Resubmitted');
        return response.data;
      } catch (err) {
        console.error('Error resubmitting policy:', err);
        PopupService.error(err.response?.data?.error || 'Failed to resubmit policy', 'Resubmission Error');
        throw err;
      } finally {
        loading.value = false;
      }
    };
    
    // Load rejected policies for the current user
    const loadRejectedPolicies = async (userId = 1) => {
      try {
        loading.value = true;
        error.value = null;
        
        const response = await axios.get(`${API_BASE_URL}/policy-versions/rejected/${userId}/`);
        return response.data;
      } catch (err) {
        console.error('Error loading rejected policies:', err);
        PopupService.error(err.response?.data?.error || 'Failed to load rejected policies', 'Loading Error');
        return [];
      } finally {
        loading.value = false;
      }
    };

    // --- Fetch policy type/category/subcategory data from backend ---
    const policyTypes = ref([])
    const policyCategories = ref({})
    const policySubCategories = ref({})

    async function fetchPolicyCategories() {
      try {
        const response = await axios.get(`${API_BASE_URL}/policy-categories/`)
        const categories = response.data
        // Build unique types, categories, and subcategories
        const typesSet = new Set()
        const categoriesMap = {}
        const subCategoriesMap = {}
        categories.forEach(item => {
          typesSet.add(item.PolicyType)
          if (!categoriesMap[item.PolicyType]) {
            categoriesMap[item.PolicyType] = []
          }
          if (!categoriesMap[item.PolicyType].includes(item.PolicyCategory)) {
            categoriesMap[item.PolicyType].push(item.PolicyCategory)
          }
          if (!subCategoriesMap[item.PolicyType]) {
            subCategoriesMap[item.PolicyType] = {}
          }
          if (!subCategoriesMap[item.PolicyType][item.PolicyCategory]) {
            subCategoriesMap[item.PolicyType][item.PolicyCategory] = []
          }
          if (!subCategoriesMap[item.PolicyType][item.PolicyCategory].includes(item.PolicySubCategory)) {
            subCategoriesMap[item.PolicyType][item.PolicyCategory].push(item.PolicySubCategory)
          }
        })
        policyTypes.value = Array.from(typesSet)
        policyCategories.value = categoriesMap
        policySubCategories.value = subCategoriesMap
      } catch (err) {
        console.error('Error fetching policy categories:', err)
        PopupService.error('Failed to fetch policy categories', 'Loading Error')
      }
    }

    function getCategoriesForType(type) {
      return policyCategories.value[type] || []
    }
    function getSubCategoriesForCategory(type, category) {
      return (policySubCategories.value[type] && policySubCategories.value[type][category]) || []
    }

    // Add missing handler functions for policy type/category/subcategory changes
    async function handlePolicyTypeChange(policyIndex, value) {
      policiesData.value[policyIndex].PolicyType = value
      // Reset category and subcategory when type changes
      policiesData.value[policyIndex].PolicyCategory = ''
      policiesData.value[policyIndex].PolicySubCategory = ''
      
      // Add to local list for UI only - will save on form submission
      if (value && !policyTypes.value.includes(value)) {
        policyTypes.value.push(value)
      }
    }

    async function handlePolicyCategoryChange(policyIndex, value) {
      const policyType = policiesData.value[policyIndex].PolicyType
      policiesData.value[policyIndex].PolicyCategory = value
      // Reset subcategory when category changes
      policiesData.value[policyIndex].PolicySubCategory = ''
      
      // Add to local list for UI only - will save on form submission
      if (value && policyType && (!policyCategories.value[policyType] || 
          !policyCategories.value[policyType].includes(value))) {
        if (!policyCategories.value[policyType]) {
          policyCategories.value[policyType] = []
        }
        policyCategories.value[policyType].push(value)
      }
    }

    async function handlePolicySubCategoryChange(policyIndex, value) {
      const policyType = policiesData.value[policyIndex].PolicyType
      const policyCategory = policiesData.value[policyIndex].PolicyCategory
      policiesData.value[policyIndex].PolicySubCategory = value
      
      // Add to local list for UI only - will save on form submission
      if (value && policyType && policyCategory && 
          (!policySubCategories.value[policyType] || 
           !policySubCategories.value[policyType][policyCategory] || 
           !policySubCategories.value[policyType][policyCategory].includes(value))) {
        if (!policySubCategories.value[policyType]) {
          policySubCategories.value[policyType] = {}
        }
        if (!policySubCategories.value[policyType][policyCategory]) {
          policySubCategories.value[policyType][policyCategory] = []
        }
        policySubCategories.value[policyType][policyCategory].push(value)
      }
    }
    
    // Function to save new policy category to backend
    async function savePolicyCategory(policyType, policyCategory, policySubCategory) {
      try {
        const response = await axios.post(`${API_BASE_URL}/policy-categories/save/`, {
          PolicyType: policyType,
          PolicyCategory: policyCategory,
          PolicySubCategory: policySubCategory
        })
        console.log('Policy category saved:', response.data)
        return response.data
      } catch (err) {
        console.error('Error saving policy category:', err)
        PopupService.error('Failed to save policy category', 'Save Error')
        throw err
      }
    }

    // Add new function to save all new policy categories before form submission
    async function saveNewPolicyCategories() {
      console.log('Checking for new policy categories to save...');
      
      // Force refresh policy categories from backend first
      try {
        await fetchPolicyCategories();
        console.log('Refreshed policy categories from backend');
      } catch (err) {
        console.error('Error refreshing policy categories:', err);
      }
      
      // Debug: Print all existing combinations
      console.log('Current policy types:', policyTypes.value);
      console.log('Current policy categories structure:', JSON.stringify(policyCategories.value));
      console.log('Current policy subcategories structure:', JSON.stringify(policySubCategories.value));
      
      const newCombinations = [];
      
      // Process all policies to find new category combinations
      for (const policy of policiesData.value) {
        if (policy.exclude) {
          continue;
        }
        
        const type = policy.PolicyType?.trim();
        const category = policy.PolicyCategory?.trim();
        const subcategory = policy.PolicySubCategory?.trim();
        
        // Skip if any part of the combination is missing
        if (!type || !category || !subcategory) {
          console.log(`Skipping incomplete combination: ${type || 'empty'} > ${category || 'empty'} > ${subcategory || 'empty'}`);
          continue;
        }
        
        console.log(`Checking combination: "${type}" > "${category}" > "${subcategory}"`);
        
        // Check if this exact combination exists in our fetched data
        let combinationExists = false;
        
        // First check if the type exists (case-sensitive)
        const typeExists = policyTypes.value.some(t => t === type);
        console.log(`Type "${type}" exists in database: ${typeExists}`);
        
        if (typeExists) {
          // Then check if the category exists for this type (case-sensitive)
          const categoriesForType = policyCategories.value[type] || [];
          const categoryExists = categoriesForType.some(c => c === category);
          console.log(`Category "${category}" exists for type "${type}": ${categoryExists}`);
          
          if (categoryExists) {
            // Finally check if the subcategory exists for this type and category (case-sensitive)
            const subcategoriesForCategory = 
              (policySubCategories.value[type] && policySubCategories.value[type][category]) || [];
            const subcategoryExists = subcategoriesForCategory.some(s => s === subcategory);
            console.log(`Subcategory "${subcategory}" exists for type "${type}" and category "${category}": ${subcategoryExists}`);
            
            combinationExists = subcategoryExists;
          }
        }
        
        if (!combinationExists) {
          console.log(`Found new combination: "${type}" > "${category}" > "${subcategory}"`);
          newCombinations.push({ type, category, subcategory });
        } else {
          console.log(`Combination already exists: "${type}" > "${category}" > "${subcategory}"`);
        }
      }
      
      // Save all new combinations
      if (newCombinations.length > 0) {
        console.log(`Saving ${newCombinations.length} new policy categories...`);
        
        try {
          // Save each combination one by one
          for (const combo of newCombinations) {
            console.log(`Saving: "${combo.type}" > "${combo.category}" > "${combo.subcategory}"`);
            await savePolicyCategory(combo.type, combo.category, combo.subcategory);
          }
          
          console.log(`Successfully saved ${newCombinations.length} new policy categories`);
          
          // Refresh policy categories to get the updated data
          await fetchPolicyCategories();
        } catch (err) {
          console.error('Error saving policy categories:', err);
          PopupService.error(`Failed to save policy categories: ${err.message}`, 'Save Error');
          // Continue with form submission even if category saving fails
        }
      } else {
        console.log('No new policy categories to save');
      }
    }

    return {
      selectedFramework,
      selectedPolicy,
      frameworks,
      showStepper,
      showPolicyDropdown,
      stepIndex,
      stepTabs,
      frameworkData,
      policiesData,
      policyOptions,
      loading,
      error,
      onFrameworkDropdown,
      onPolicyDropdown,
      switchToPolicy,
      switchToFramework,
      addPolicy,
      removePolicy,
      addSubPolicy,
      removeSubPolicy,
      closeTab,
      submitFrameworkForm,
      toggleSubPolicyExclusion,
      users,
      isSubmitting,
      toggleSubPolicyCollapse,
      debugSubpolicies,
      resetSubPolicies,
      getSubpolicyCount,
      excludePolicy,
      frameworkFileName,
      frameworkFileInput,
      browseFrameworkFile,
      onFrameworkFileChange,
      browsePolicyFile,
      onPolicyFileChange,
      submitPolicyReview,
      approvePolicyVersion,
      resubmitRejectedPolicy,
      loadRejectedPolicies,
      // --- Add these to fix runtime error ---
      policyTypes,
      getCategoriesForType,
      getSubCategoriesForCategory,
      // Add the handler functions to the return object
      handlePolicyTypeChange,
      handlePolicyCategoryChange,
      handlePolicySubCategoryChange
    }
  }
}
</script>

<style scoped>
/* Add loading and error styles */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #ff4444;
  color: white;
  padding: 12px 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

/* Add new styles */
.framework-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 4px;
}

.framework-select:focus {
  border-color: #2196f3;
  outline: none;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
}

.helper-text {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  margin-bottom: 0;
}

/* Keep existing styles */
@import './versioning.css';

/* Import popup styles */
@import '@/modules/popup/styles.css';

/* Add new styles */
.policy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.subpolicy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.subpolicy-actions {
  display: flex;
  gap: 8px;
}

.exclude-btn {
  padding: 4px 8px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.exclude-btn.excluded {
  background-color: #ffebee;
  color: #d32f2f;
  border-color: #d32f2f;
}

.excluded {
  opacity: 0.6;
  background-color: #f5f5f5;
}

.remove-btn {
  padding: 4px 8px;
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #d32f2f;
  border-radius: 4px;
  cursor: pointer;
}

.remove-btn:hover {
  background-color: #d32f2f;
  color: white;
}

/* Add these styles */
select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 4px;
}

select:focus {
  border-color: #2196f3;
  outline: none;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
}

/* Policy form container specific styles */
.policy-form-container {
  background: #f8fafc;
  padding: 24px;
  border-radius: 12px;
  margin-top: 24px;
  border: 2px solid #e2e8f0;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

/* Form row inside policy container */
.policy-form-container .form-row {
  display: flex;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
  padding: 0 10px;
  flex-wrap: wrap;
}

/* Form group inside policy container */
.policy-form-container .form-group {
  flex: 1 1 0;
  min-width: 220px;
  margin-bottom: 15px;
  box-sizing: border-box;
}

/* Input fields inside policy container */
.policy-form-container .form-group input,
.policy-form-container .form-group textarea,
.policy-form-container .form-group select {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  font-size: 14px;
}

/* Remove policy button */
.policy-form-container .remove-btn {
  padding: 4px 12px;
  font-size: 12px;
  height: 28px;
  background: transparent;
  border: 1px solid #e74c3c;
  color: #e74c3c;
}

/* Add responsive styles */
@media screen and (max-width: 768px) {
  .policy-form-container .form-group {
    flex: 1 1 100%;
    max-width: 100%;
  }
  
  .policy-form-container .form-row {
    gap: 10px;
  }
}

/* Add styles for version-info section */
.version-info {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border-left: 4px solid #2196f3;
}

.version-info p {
  margin: 0;
  color: #333;
  font-size: 14px;
  line-height: 1.4;
}

/* Add badge styles */
.policy-badge {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.new-badge {
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.existing-badge {
  background-color: #e8f5e9;
  color: #388e3c;
  border: 1px solid #c8e6c9;
}

.required-field {
  color: #f44336;
  margin-left: 2px;
}

.field-error {
  border-color: #f44336 !important;
  background-color: rgba(244, 67, 54, 0.05);
}

.error-text {
  color: #f44336;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.add-subpolicy-container {
  margin-top: 16px;
  text-align: center;
}

.add-subpolicy-btn {
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
  padding: 8px 16px;
  font-weight: 500;
}

.add-subpolicy-btn:hover {
  background-color: #bbdefb;
}

.subpolicy-card {
  position: relative;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #fafafa;
}

.subpolicy-card:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.subpolicies-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.subpolicy-counter {
  background-color: #e8f5e9;
  color: #388e3c;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.subpolicy-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.subpolicy-card.collapsed {
  padding: 10px 16px;
}

.subpolicy-summary {
  padding: 4px 0;
  color: #555;
}

.subpolicy-content {
  margin-top: 10px;
}

.prominent-btn {
  background-color: #2196f3;
  color: white;
  font-weight: bold;
  padding: 10px 20px;
  border-radius: 8px;
  margin-top: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  transition: all 0.2s;
}

.prominent-btn:hover {
  background-color: #1976d2;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.prominent-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.debug-btn {
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 8px;
  cursor: pointer;
}

.debug-btn:hover {
  background-color: #e0e0e0;
}

.reset-btn {
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  padding: 8px 16px;
  border-radius: 8px;
  margin-top: 16px;
  margin-left: 16px;
  font-weight: 500;
  cursor: pointer;
}

.reset-btn:hover {
  background-color: #ffcdd2;
}

.file-name {
  margin-left: 10px;
  color: #888;
  font-size: 13px;
}

.searchable-select {
  position: relative;
}

.searchable-select input[type="text"] {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 4px;
}

.searchable-select input[type="text"]:focus {
  border-color: #2196f3;
  outline: none;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
}

.searchable-select input[type="text"]::placeholder {
  color: #999;
}

.searchable-select ul {
  list-style: none;
  padding: 0;
  margin: 0;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.searchable-select li {
  padding: 8px 12px;
  cursor: pointer;
}

.searchable-select li:hover {
  background-color: #f0f0f0;
}

.searchable-select li.selected {
  background-color: #e3f2fd;
}

.searchable-select ul.datalist {
  display: none;
}

.searchable-select ul.datalist.active {
  display: block;
}

.searchable-select ul.datalist li {
  padding: 8px 12px;
  cursor: pointer;
}

.searchable-select ul.datalist li:hover {
  background-color: #f0f0f0;
}

.searchable-select ul.datalist li.selected {
  background-color: #e3f2fd;
}
</style> 