<template>
  <div class="compliance-view-container">
    <h1><i class="fas fa-clipboard-list"></i> {{ title }}</h1>

    <!-- Error Message -->
    <div v-if="error && errorType === 'error'" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Warning Message -->
    <div v-if="error && errorType === 'warning'" class="error-message warning">
      <i class="fas fa-exclamation-triangle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-spinner">
      <i class="fas fa-circle-notch fa-spin"></i>
      <span>Loading...</span>
    </div>

    <div class="content-wrapper">
      <div class="section-header">
        <span><i class="fas fa-list-check"></i> {{ title }}</span>
        <div class="section-actions">
          <!-- Filter Controls -->
          <button class="filter-btn" @click="toggleFilter">
            <i class="fas fa-filter"></i> 
            {{ showOnlyPermanent ? 'Show All Compliances' : 'Show Only Permanent' }}
          </button>
          <!-- Export Controls -->
          <div class="inline-export-controls">
            <select v-model="selectedFormat" class="format-select">
              <option value="xlsx">Excel (.xlsx)</option>
              <option value="csv">CSV (.csv)</option>
              <option value="pdf">PDF (.pdf)</option>
              <option value="json">JSON (.json)</option>
              <option value="xml">XML (.xml)</option>
            </select>
            <button class="export-btn" @click="handleExport(selectedFormat)">
              <i class="fas fa-download"></i> Export
            </button>
          </div>
          <button class="view-toggle-btn" @click="toggleViewMode">
            <i :class="viewMode === 'card' ? 'fas fa-list' : 'fas fa-th-large'"></i>
            {{ viewMode === 'card' ? 'List View' : 'Card View' }}
          </button>
          <button class="action-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> Back
          </button>
        </div>
      </div>
      
      <div v-if="loading" class="loading-spinner">
        <i class="fas fa-circle-notch fa-spin"></i>
        <span>Loading compliances...</span>
      </div>
      
      <div v-else-if="!compliances.length" class="no-data">
        <i class="fas fa-inbox"></i>
        <p>No compliances found</p>
      </div>
      
      <!-- Card View -->
      <div v-else-if="viewMode === 'card'" class="compliances-grid">
        <div v-for="compliance in compliances" 
             :key="compliance.ComplianceId" 
             class="compliance-card"
             @click="toggleExpand(compliance)">
          <div class="compliance-header">
            <span :class="['criticality-badge', 'criticality-' + compliance.Criticality.toLowerCase()]">
              <i class="fas fa-exclamation"></i> {{ compliance.Criticality }}
            </span>
          </div>
          
          <div class="compliance-body">
            <h3><i class="fas fa-clipboard-check"></i> {{ compliance.ComplianceItemDescription }}</h3>
            <div class="compliance-details">
              <div class="detail-row">
                <span class="label"><i class="fas fa-layer-group"></i> Maturity Level:</span>
                <span class="value">{{ compliance.MaturityLevel }}</span>
              </div>
              <div class="detail-row">
                <span class="label"><i class="fas fa-cogs"></i> Type:</span>
                <span class="value">{{ compliance.ManualAutomatic }}</span>
              </div>
              <div class="detail-row">
                <span class="label"><i class="fas fa-gavel"></i> Requirement:</span>
                <span class="value">{{ compliance.MandatoryOptional }}</span>
              </div>
              <div class="detail-row">
                <span class="label"><i class="fas fa-code-branch"></i> Version:</span>
                <span class="value">{{ compliance.ComplianceVersion }}</span>
              </div>
            </div>
            
            <!-- Expanded Details Section -->
            <div v-if="expandedCompliance === compliance.ComplianceId" class="expanded-details">
              <h4><i class="fas fa-info-circle"></i> Compliance Details</h4>

              <div v-if="loadingDetails[compliance.ComplianceId]" class="loading-details">
                <i class="fas fa-circle-notch fa-spin"></i>
                <span>Loading details...</span>
              </div>

              <div v-else class="expanded-content">
                <div class="detail-section">
                  <h5><i class="fas fa-align-left"></i> Description:</h5>
                  <div class="detail-value">
                    {{ compliance.ComplianceItemDescription || 'No description available' }}
                  </div>
                </div>

                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-heading"></i> Compliance Title:</span>
                    <span class="detail-content">{{ compliance.ComplianceTitle || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-first-aid"></i> Mitigation:</span>
                    <span class="detail-content">{{ compliance.mitigation || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-crosshairs"></i> Scope:</span>
                    <span class="detail-content">{{ compliance.Scope || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-bullseye"></i> Objective:</span>
                    <span class="detail-content">{{ compliance.Objective || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-tag"></i> Compliance Type:</span>
                    <span class="detail-content">{{ compliance.ComplianceType || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-bomb"></i> Possible Damage:</span>
                    <span class="detail-content">{{ compliance.PossibleDamage || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-gavel"></i> Mandatory/Optional:</span>
                    <span class="detail-content">{{ compliance.MandatoryOptional || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-cogs"></i> Manual/Automatic:</span>
                    <span class="detail-content">{{ compliance.ManualAutomatic || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-thermometer-half"></i> Severity Rating:</span>
                    <span class="detail-content">{{ compliance.Impact || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-percentage"></i> Probability:</span>
                    <span class="detail-content">{{ compliance.Probability || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-clock"></i> Duration:</span>
                    <span class="detail-content">{{ compliance.PermanentTemporary || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-exclamation-triangle"></i> Risk Status:</span>
                    <span class="detail-content">{{ compliance.IsRisk !== undefined ? (compliance.IsRisk ? 'Risk Identified' : 'No Risk') : 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-flag"></i> Status:</span>
                    <span class="detail-content">{{ compliance.Status || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-toggle-on"></i> Active/Inactive:</span>
                    <span class="detail-content">{{ compliance.ActiveInactive || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-check-circle"></i> Applicability:</span>
                    <span class="detail-content">{{ compliance.Applicability || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-building"></i> Business Units Covered:</span>
                    <span class="detail-content">{{ compliance.BusinessUnitsCovered || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-chess"></i> Potential Risk Scenarios:</span>
                    <span class="detail-content">{{ compliance.PotentialRiskScenarios || 'Not specified' }}</span>
                  </div>
                  
                  <div class="detail-item">
                    <span class="detail-label"><i class="fas fa-barcode"></i> Identifier:</span>
                    <span class="detail-content">{{ compliance.Identifier || 'Not specified' }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="compliance-footer">
              <div class="created-info">
                <span>Created by {{ compliance.CreatedByName }}</span>
                <span>{{ formatDate(compliance.CreatedByDate) }}</span>
              </div>
              <div class="identifier">ID: {{ compliance.Identifier }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- List View -->
      <div v-else class="compliances-list-view">
        <table class="compliances-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Compliance</th>
              <th>Status</th>
              <th>Criticality</th>
              <th>Maturity Level</th>
              <th>Version</th>
              <th>Created By</th>
              <th>Created Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="compliance in compliances" :key="compliance.ComplianceId">
              <tr @click="toggleExpand(compliance)" :class="{ 'expanded-row': expandedCompliance === compliance.ComplianceId }">
                <td class="compliance-id" data-label="ID">{{ compliance.Identifier }}</td>
                <td class="compliance-name" data-label="Compliance">{{ compliance.ComplianceItemDescription }}</td>
                <td data-label="Status">
                  <span :class="['status-badge', compliance.Status?.toLowerCase()]">
                    {{ compliance.Status }}
                  </span>
                </td>
                <td data-label="Criticality">
                  <span :class="['criticality-badge', 'criticality-' + compliance.Criticality?.toLowerCase()]">
                    {{ compliance.Criticality }}
                  </span>
                </td>
                <td data-label="Maturity Level">{{ compliance.MaturityLevel }}</td>
                <td data-label="Version">{{ compliance.ComplianceVersion }}</td>
                <td data-label="Created By">{{ compliance.CreatedByName }}</td>
                <td data-label="Created Date">{{ formatDate(compliance.CreatedByDate) }}</td>
                <td data-label="Actions">
                  <button class="expand-btn" @click.stop="toggleExpand(compliance)">
                    <i :class="expandedCompliance === compliance.ComplianceId ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                  </button>
                </td>
              </tr>
              <tr v-if="expandedCompliance === compliance.ComplianceId" class="details-row">
                <td colspan="9" class="expanded-content">
                  <!-- Complete details for list view -->
                  <div v-if="loadingDetails[compliance.ComplianceId]" class="loading-details">
                    <i class="fas fa-circle-notch fa-spin"></i>
                    <span>Loading details...</span>
                  </div>

                  <div v-else class="expanded-content">
                    <div class="detail-section">
                      <h5><i class="fas fa-align-left"></i> Description:</h5>
                      <div class="detail-value">
                        {{ compliance.ComplianceItemDescription || 'No description available' }}
                      </div>
                    </div>

                    <div class="detail-grid">
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-heading"></i> Compliance Title:</span>
                        <span class="detail-content">{{ compliance.ComplianceTitle || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-first-aid"></i> Mitigation:</span>
                        <span class="detail-content">{{ compliance.mitigation || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-crosshairs"></i> Scope:</span>
                        <span class="detail-content">{{ compliance.Scope || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-bullseye"></i> Objective:</span>
                        <span class="detail-content">{{ compliance.Objective || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-tag"></i> Compliance Type:</span>
                        <span class="detail-content">{{ compliance.ComplianceType || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-bomb"></i> Possible Damage:</span>
                        <span class="detail-content">{{ compliance.PossibleDamage || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-gavel"></i> Mandatory/Optional:</span>
                        <span class="detail-content">{{ compliance.MandatoryOptional || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-cogs"></i> Manual/Automatic:</span>
                        <span class="detail-content">{{ compliance.ManualAutomatic || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-thermometer-half"></i> Severity Rating:</span>
                        <span class="detail-content">{{ compliance.Impact || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-percentage"></i> Probability:</span>
                        <span class="detail-content">{{ compliance.Probability || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-clock"></i> Duration:</span>
                        <span class="detail-content">{{ compliance.PermanentTemporary || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-exclamation-triangle"></i> Risk Status:</span>
                        <span class="detail-content">{{ compliance.IsRisk !== undefined ? (compliance.IsRisk ? 'Risk Identified' : 'No Risk') : 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-flag"></i> Status:</span>
                        <span class="detail-content">{{ compliance.Status || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-toggle-on"></i> Active/Inactive:</span>
                        <span class="detail-content">{{ compliance.ActiveInactive || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-check-circle"></i> Applicability:</span>
                        <span class="detail-content">{{ compliance.Applicability || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-building"></i> Business Units Covered:</span>
                        <span class="detail-content">{{ compliance.BusinessUnitsCovered || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-chess"></i> Potential Risk Scenarios:</span>
                        <span class="detail-content">{{ compliance.PotentialRiskScenarios || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-exclamation-circle"></i> Risk Type:</span>
                        <span class="detail-content">{{ compliance.RiskType || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-list-alt"></i> Risk Category:</span>
                        <span class="detail-content">{{ compliance.RiskCategory || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-chart-line"></i> Risk Business Impact:</span>
                        <span class="detail-content">{{ compliance.RiskBusinessImpact || 'Not specified' }}</span>
                      </div>
                      
                      <div class="detail-item">
                        <span class="detail-label"><i class="fas fa-barcode"></i> Identifier:</span>
                        <span class="detail-content">{{ compliance.Identifier || 'Not specified' }}</span>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

// Get route parameters
const type = ref(route.params.type)
const id = ref(route.params.id)
const name = ref(decodeURIComponent(route.params.name))

// State
const compliances = ref([])
const allCompliances = ref([]) // Store all compliances
const loading = ref(false)
const error = ref(null)
const errorType = ref('error') // 'error' or 'warning'
const selectedFormat = ref('xlsx')
const isExporting = ref(false)
const exportError = ref(null)
const viewMode = ref('list') // Default to list view
const expandedCompliance = ref(null)
const loadingDetails = ref({}) // Track loading state for each compliance detail fetch
const showOnlyPermanent = ref(true) // Default to showing only permanent compliances

// Computed properties
const title = computed(() => {
  return `All Controls - ${name.value}`
})

// Fetch compliances on component mount
onMounted(async () => {
  await fetchCompliances()
})

// Methods
async function fetchCompliances() {
  try {
    loading.value = true
    error.value = null
    errorType.value = 'error'
    
    let endpoint = ''
    switch(type.value) {
      case 'framework':
        endpoint = `/api/compliances/framework/${id.value}/`
        break
      case 'policy':
        endpoint = `/api/compliances/policy/${id.value}/`
        break
      case 'subpolicy':
        endpoint = `/api/compliances/subpolicy/${id.value}/compliances/`
        break
      default:
        throw new Error('Invalid type specified')
    }
    
    const response = await axios.get(endpoint)
    console.log('API Response:', response.data)
    
    if (response.data && response.data.success) {
      // Store all compliances
      allCompliances.value = response.data.compliances
      
      // Debug: Check if PermanentTemporary field exists in the response
      if (allCompliances.value.length > 0) {
        const firstCompliance = allCompliances.value[0]
        console.log('First compliance object:', firstCompliance)
        console.log('PermanentTemporary field exists:', 'PermanentTemporary' in firstCompliance)
        
        // If PermanentTemporary field is missing, try to fetch detailed data for each compliance
        if (!('PermanentTemporary' in firstCompliance) && allCompliances.value.length > 0) {
          console.log('PermanentTemporary field missing, fetching detailed data...')
          
          // Show a loading message
          error.value = 'Loading detailed compliance data...'
          errorType.value = 'warning'
          
          // Fetch detailed data for first few compliances to check if they're permanent
          const detailedPromises = allCompliances.value.slice(0, 5).map(async (compliance) => {
            try {
              const detailResponse = await axios.get(`/compliance/${compliance.ComplianceId}/`)
              if (detailResponse.data && detailResponse.data.success) {
                const detailedData = detailResponse.data.data
                // Update the compliance object with detailed data
                return {
                  ...compliance,
                  PermanentTemporary: detailedData.PermanentTemporary || ''
                }
              }
              return compliance
            } catch (error) {
              console.error(`Error fetching details for compliance ${compliance.ComplianceId}:`, error)
              return compliance
            }
          })
          
          // Wait for all detailed data to be fetched
          const detailedCompliances = await Promise.all(detailedPromises)
          
          // Update the first few compliances with detailed data
          detailedCompliances.forEach((detailedCompliance, index) => {
            allCompliances.value[index] = detailedCompliance
          })
          
          console.log('Updated compliances with detailed data:', allCompliances.value.slice(0, 5))
        }
        
        // Check all compliances for PermanentTemporary values
        const permanentValues = allCompliances.value.map(c => c.PermanentTemporary).filter(Boolean)
        console.log('Available PermanentTemporary values:', permanentValues)
        console.log('Compliances with "Permanent" value:', 
          allCompliances.value.filter(c => 
            c.PermanentTemporary && 
            c.PermanentTemporary.toLowerCase().includes('permanent')
          ).length
        )
      }
      
      // Apply filter based on current setting
      applyFilter()
    } else {
      throw new Error(response.data.message || 'Failed to fetch compliances')
    }
  } catch (err) {
    console.error('Error fetching compliances:', err)
    error.value = 'Failed to fetch compliances. Please try again.'
    errorType.value = 'error'
    compliances.value = []
    allCompliances.value = []
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  if (showOnlyPermanent.value) {
    // Add debugging to see what values we're getting for PermanentTemporary
    console.log('All compliances:', allCompliances.value);
    
    // Check if PermanentTemporary field exists in any compliance
    const hasPermanentField = allCompliances.value.some(c => 'PermanentTemporary' in c);
    console.log('Has PermanentTemporary field:', hasPermanentField);
    
    if (!hasPermanentField) {
      // If PermanentTemporary field doesn't exist in the API response yet,
      // show all compliances and a warning
      compliances.value = [...allCompliances.value];
      error.value = 'PermanentTemporary field not found in API response. API may need to be updated.';
      errorType.value = 'warning';
      return;
    }
    
    // Filter to show only permanent compliances - case insensitive and handle null values
    compliances.value = allCompliances.value.filter(compliance => {
      const permanentValue = compliance.PermanentTemporary;
      console.log(`Compliance ID ${compliance.ComplianceId}, PermanentTemporary: ${permanentValue}`);
      
      // Check for "Permanent" value case-insensitively
      return permanentValue && 
        (permanentValue.toLowerCase() === "permanent" || 
         permanentValue.toLowerCase().includes("permanent"));
    });
    
    console.log('Filtered compliances:', compliances.value);
    
    // Show appropriate messages based on filter results
    if (compliances.value.length === 0 && allCompliances.value.length > 0) {
      error.value = 'No permanent compliances found. Click "Show All Compliances" to see all records.';
      errorType.value = 'warning';
    } else if (compliances.value.length < allCompliances.value.length) {
      error.value = `Showing ${compliances.value.length} permanent compliances out of ${allCompliances.value.length} total compliances.`;
      errorType.value = 'warning';
    } else {
      error.value = null;
    }
  } else {
    // Show all compliances
    compliances.value = [...allCompliances.value];
    error.value = null;
  }
}

function toggleFilter() {
  showOnlyPermanent.value = !showOnlyPermanent.value
  applyFilter()
  // Reset expanded state when toggling filter
  expandedCompliance.value = null
}

function toggleViewMode() {
  viewMode.value = viewMode.value === 'card' ? 'list' : 'card'
}

function toggleExpand(compliance) {
  if (expandedCompliance.value === compliance.ComplianceId) {
    expandedCompliance.value = null
  } else {
    expandedCompliance.value = compliance.ComplianceId
    // Fetch detailed compliance data when expanding
    fetchComplianceDetails(compliance.ComplianceId)
  }
}

// Add a new function to fetch detailed compliance data
async function fetchComplianceDetails(complianceId) {
  try {
    // Set loading state for this compliance
    loadingDetails.value[complianceId] = true
    
    const response = await axios.get(`/compliance/${complianceId}/`)
    if (response.data && response.data.success) {
      // Find the compliance in the array and enrich it with the detailed data
      const index = compliances.value.findIndex(c => c.ComplianceId === complianceId)
      if (index !== -1) {
        // Merge the detailed data with the existing compliance data
        const detailedData = response.data.data
        
        // Log the received data for debugging
        console.log('Received detailed compliance data:', detailedData)
        
        compliances.value[index] = {
          ...compliances.value[index],
          ...detailedData,
          // Ensure these fields are properly mapped
          ComplianceTitle: detailedData.ComplianceTitle || '',
          ComplianceItemDescription: detailedData.ComplianceItemDescription || '',
          Scope: detailedData.Scope || '',
          Objective: detailedData.Objective || '',
          ComplianceType: detailedData.ComplianceType || '',
          PossibleDamage: detailedData.PossibleDamage || '',
          mitigation: detailedData.mitigation || '',
          Impact: detailedData.Impact || '',
          Probability: detailedData.Probability || '',
          PermanentTemporary: detailedData.PermanentTemporary || '',
          IsRisk: detailedData.IsRisk,
          Status: detailedData.Status || '',
          ActiveInactive: detailedData.ActiveInactive || '',
          Applicability: detailedData.Applicability || '',
          BusinessUnitsCovered: detailedData.BusinessUnitsCovered || '',
          PotentialRiskScenarios: detailedData.PotentialRiskScenarios || '',
          RiskType: detailedData.RiskType || '',
          RiskCategory: detailedData.RiskCategory || '',
          RiskBusinessImpact: detailedData.RiskBusinessImpact || ''
        }
      }
    }
  } catch (error) {
    console.error(`Error fetching compliance details for ID ${complianceId}:`, error)
  } finally {
    // Clear loading state
    loadingDetails.value[complianceId] = false
  }
}

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString()
}

function goBack() {
  router.back()
}

async function handleExport(format) {
  try {
    isExporting.value = true
    exportError.value = null
    
    console.log(`Attempting export for ${type.value} ${id.value} in ${format} format`)
    
    // Update the API endpoint URL with path parameters
    const response = await axios({
      url: `/api/export/all-compliances/${format}/${type.value}/${id.value}/`,
      method: 'GET',
      responseType: 'blob',
      timeout: 30000,
      headers: {
        'Accept': 'application/json, application/pdf, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv, application/xml'
      }
    })

    // Handle successful download
    const contentType = response.headers['content-type']
    const blob = new Blob([response.data], { type: contentType })
    
    // Get filename from header or create default
    let filename = `compliances_${type.value}_${id.value}.${format}`
    const disposition = response.headers['content-disposition']
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    }
    
    // Trigger download
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    
    ElMessage({
      message: 'Export completed successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Export error:', error)
    const errorMessage = error.response?.data?.message || error.message || 'Failed to export compliances'
    exportError.value = errorMessage
    ElMessage({
      message: errorMessage,
      type: 'error',
      duration: 5000
    })
  } finally {
    isExporting.value = false
  }
}
</script>

<style>
.compliance-view-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  margin-left: 180px;
}

h1 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-weight: 600;
}

.error-message {
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  color: #b91c1c;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-message.warning {
  background-color: #fff3e0;
  border-color: #f57c00;
  color: #92400e;
}

.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #4b5563;
  margin: 20px 0;
}

.content-wrapper {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.5rem;
  color: #1f2937;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e5e7eb;
}

.section-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #4b5563;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.view-toggle-btn:hover {
  background-color: #e5e7eb;
  transform: translateY(-1px);
}

.view-toggle-btn i {
  color: #6b7280;
}

.compliances-list-view {
  background-color: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: auto;
  margin-top: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.compliances-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.compliances-table th {
  background-color: #f9fafb;
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  color: #4b5563;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.compliances-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}

.compliances-table tr:last-child td {
  border-bottom: none;
}

.compliances-table tr:hover {
  background-color: #f9fafb;
}

.compliance-name {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compliance-id {
  font-family: monospace;
  color: #6b7280;
}

.mini-fetch-btn {
  padding: 4px 8px;
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mini-fetch-btn:hover {
  background-color: #e5e7eb;
}

.mini-fetch-btn i {
  margin-right: 4px;
  font-size: 0.8rem;
}

.compliances-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.compliance-card {
  transition: all 0.25s ease;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.compliance-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-color: #d1d5db;
}

.compliance-header {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
}

.compliance-body {
  padding: 16px;
}

.compliance-body h3 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #1f2937;
  font-size: 1.1rem;
  line-height: 1.4;
}

.compliance-footer {
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid #e5e7eb;
  font-size: 0.85rem;
  color: #6b7280;
}

.inline-export-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.format-select {
  padding: 7px 10px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background-color: #f9fafb;
  color: #4b5563;
  font-size: 0.9rem;
  outline: none;
  min-width: 140px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.export-btn:hover {
  background-color: #2563eb;
  transform: translateY(-1px);
}

.export-btn i {
  font-size: 0.9rem;
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
  text-align: center;
}

.no-data i {
  font-size: 2rem;
  margin-bottom: 12px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.status-badge.approved { 
  background-color: #dcfce7; 
  color: #166534; 
}

.status-badge.under-review, 
.status-badge.pending { 
  background-color: #fff3e0; 
  color: #92400e; 
}

.status-badge.rejected { 
  background-color: #fee2e2; 
  color: #991b1b; 
}

.status-badge.active {
  background-color: #dcfce7;
  color: #166534;
}

.status-badge.inactive {
  background-color: #fee2e2;
  color: #991b1b;
}

.criticality-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.criticality-high { background-color: #ffebee; color: #d32f2f; }
.criticality-medium { background-color: #fff3e0; color: #f57c00; }
.criticality-low { background-color: #e8f5e9; color: #388e3c; }

.compliance-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9em;
}

.detail-row .label {
  color: #666;
}

.detail-row .value {
  font-weight: 500;
  color: #333;
}

.expanded-details {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #e5e7eb;
}

.expanded-details h4 {
  font-size: 1.1rem;
  color: #4b5563;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
}

.expanded-details h4:before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 20px;
  background-color: #3b82f6;
  border-radius: 2px;
}

.expanded-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.detail-section h5 {
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.detail-value {
  color: #1f2937;
  font-size: 0.95rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 160px);
  gap: 6px;
  background-color: #f8fafc;
  border-radius: 6px;
  padding: 10px;
  border: 1px solid #e2e8f0;
  max-height: 350px;
  overflow-y: auto;
  justify-content: start;
}

.detail-item {
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  height: 85px;
  width: 160px;
  overflow: hidden;
}

.detail-item:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.detail-label {
  font-weight: 700;
  color: #374151;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 3px;
  margin-bottom: 6px;
  flex-shrink: 0;
  line-height: 1.2;
}

.detail-content {
  color: #1f2937;
  font-size: 0.8rem;
  line-height: 1.3;
  word-break: break-word;
  flex-grow: 1;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-content:hover {
  -webkit-line-clamp: unset;
  overflow: visible;
  position: relative;
  z-index: 10;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.detail-content:empty::after {
  content: 'Not specified';
  color: #9ca3af;
  font-style: italic;
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f3f4f6;
  border: 1px dashed #cbd5e1;
}

.expanded-row {
  background-color: #f8fafc !important;
}

.details-row {
  background-color: #f1f5f9;
}

.details-row td {
  padding: 20px !important;
  border-bottom: 1px solid #e2e8f0;
}

.expand-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.expand-btn:hover {
  background-color: #e5e7eb;
  color: #4b5563;
}

.expand-btn i {
  font-size: 0.9rem;
}

/* Responsive breakpoints for multi-row grid layout */
@media (min-width: 1200px) {
  .detail-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }
}

@media (min-width: 900px) and (max-width: 1199px) {
  .detail-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
  }
  
  .detail-item {
    padding: 10px;
  }
  
  .detail-label {
    font-size: 0.8rem;
  }
  
  .detail-content {
    font-size: 0.85rem;
  }
}

@media (min-width: 768px) and (max-width: 899px) {
  .detail-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    padding: 12px;
  }
  
  .detail-item {
    padding: 10px;
  }
  
  .detail-label {
    font-size: 0.8rem;
  }
  
  .detail-content {
    font-size: 0.85rem;
  }
}

@media (max-width: 767px) {
  .section-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  .inline-export-controls {
    order: 1;
    width: 100%;
    margin-bottom: 8px;
    justify-content: flex-end;
  }
  
  .detail-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    padding: 12px;
  }
  
  .detail-item {
    padding: 8px;
  }
  
  .detail-label {
    font-size: 0.75rem;
  }
  
  .detail-content {
    font-size: 0.8rem;
  }
}

@media (max-width: 479px) {
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 10px;
  }
  
  .detail-item {
    padding: 8px;
  }
  
  .detail-label {
    font-size: 0.75rem;
  }
  
  .detail-content {
    font-size: 0.8rem;
  }
}

@media (max-width: 1200px) {
  .compliances-table {
    /* Remove min-width that forces horizontal scroll */
    width: 100%;
  }
  
  .compliances-list-view {
    /* Allow natural responsive behavior */
    width: 100%;
  }

  .compliances-table th,
  .compliances-table td {
    padding: 8px 6px;
    font-size: 0.85rem;
  }
}

/* Convert table to card layout on mobile for better UX */
@media (max-width: 768px) {
  .compliances-table,
  .compliances-table thead,
  .compliances-table tbody,
  .compliances-table th,
  .compliances-table td,
  .compliances-table tr {
    display: block;
  }

  .compliances-table thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }

  .compliances-table tr {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 10px;
    padding: 10px;
    background-color: white;
  }

  .compliances-table td {
    border: none;
    position: relative;
    padding: 8px 10px;
    padding-left: 40%;
    border-bottom: 1px solid #f3f4f6;
    word-wrap: break-word;
  }

  .compliances-table td:before {
    content: attr(data-label) ": ";
    position: absolute;
    left: 6px;
    width: 35%;
    padding-right: 10px;
    white-space: nowrap;
    font-weight: 600;
    color: #4b5563;
  }

  .compliances-table td:last-child {
    border-bottom: none;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.loading-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #4b5563;
  padding: 20px;
  background-color: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.loading-details i {
  color: #3b82f6;
}

/* Animation for expanding details */
.details-row {
  animation: fadeIn 0.3s ease-in-out;
}

/* Empty value styling */
.detail-content:empty::after,
.detail-content:contains('Not specified') {
  color: #d1d5db;
  font-style: italic;
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f3f4f6;
  border: 1px dashed #cbd5e1;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #4b5563;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.filter-btn:hover {
  background-color: #e5e7eb;
  transform: translateY(-1px);
}

.filter-btn i {
  color: #6b7280;
}

/* Container overflow fixes */
.compliance-view-container {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  padding: 20px;
  box-sizing: border-box;
}

.content-wrapper {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}

.compliances-list-view {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* Table improvements */
.compliances-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  table-layout: auto;
}

.compliances-table th {
  background-color: #f9fafb;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #4b5563;
  border-bottom: 1px solid #e5e7eb;
  word-wrap: break-word;
  font-size: 0.9rem;
}

.compliances-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
  word-wrap: break-word;
  vertical-align: top;
}

.compliance-name {
  min-width: 150px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.compliance-id {
  font-family: monospace;
  color: #6b7280;
  font-size: 0.85rem;
  min-width: 80px;
}

/* Enhanced details grid */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  max-height: 500px;
  overflow-y: auto;
  width: 100%;
  box-sizing: border-box;
}

.detail-item {
  background-color: white;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s ease;
  min-height: 100px;
  height: auto;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.detail-item:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.detail-label {
  margin: 0 0 8px 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 6px;
  flex-shrink: 0;
  line-height: 1.3;
}

.detail-content {
  font-size: 0.9rem;
  color: #1f2937;
  line-height: 1.4;
  flex-grow: 1;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
  padding: 4px 0;
  min-height: 40px;
}
</style> 