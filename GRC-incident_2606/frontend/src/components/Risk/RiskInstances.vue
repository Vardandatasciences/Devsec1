<template>
  <div class="risk-instance-container">
    <div class="header-row">
      <h2 class="risk-title"><i class="fas fa-exclamation-triangle risk-icon"></i>Risk Instances</h2>
    </div>
    
    <div class="filters-row">
      <div class="filter-group">
        <input 
          v-model="searchQuery" 
          class="risk-search-input" 
          type="text" 
          placeholder="Search..."
          @input="validateSearchInput"
          :class="{'input-error': validationErrors.searchQuery}"
        />
        <select v-model="selectedCriticality" class="filter-select" @change="validateFilterInput('selectedCriticality')">
          <option value="">All Criticality</option>
          <option v-for="c in uniqueCriticality" :key="c">{{ c }}</option>
        </select>
        <select v-model="selectedStatus" class="filter-select" @change="validateFilterInput('selectedStatus')">
          <option value="">All Status</option>
          <option v-for="s in uniqueStatus" :key="s">{{ s }}</option>
        </select>
        <select v-model="selectedCategory" class="filter-select" @change="validateFilterInput('selectedCategory')">
          <option value="">All Category</option>
          <option v-for="cat in uniqueCategory" :key="cat">{{ cat }}</option>
        </select>
        <select v-model="selectedPriority" class="filter-select" @change="validateFilterInput('selectedPriority')">
          <option value="">All Priority</option>
          <option v-for="p in uniquePriority" :key="p">{{ p }}</option>
        </select>
      </div>
    </div>
    
    <!-- Error message for validation errors -->
    <div v-if="hasValidationErrors" class="validation-error-summary">
      <p><i class="fas fa-exclamation-triangle"></i> Invalid input detected. Please correct the highlighted fields.</p>
    </div>
    
    <div class="risk-list-table-container">
      <table v-if="filteredInstances.length" class="risk-list-table">
        <thead>
          <tr>
            <th class="risk-id">RiskID</th>
            <th>Origin</th>
            <th>Category</th>
            <th>Criticality</th>
            <th>Risk Status</th>
            <th>Risk Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="instance in filteredInstances" :key="instance.RiskInstanceId">
            <td class="risk-id" style="background: none !important; border-radius: 0 !important;">{{ instance.RiskId }}</td>
            <td><span class="origin-badge">MANUAL</span></td>
            <td><span class="category-badge">{{ instance.Category }}</span></td>
            <td>
              <span :class="'priority-' + instance.Criticality.toLowerCase()">
                {{ instance.Criticality }}
              </span>
            </td>
            <td>
              <span :class="'status-' + (instance.RiskStatus ? instance.RiskStatus.toLowerCase().replace(/\s+/g, '-') : 'open')">
                {{ instance.RiskStatus || 'Open' }}
              </span>
            </td>
            <td>
              {{ instance.RiskDescription }}
            </td>
            <td>
              <button @click="viewInstanceDetails(instance.RiskInstanceId)" class="view-instance-btn">
                View Instance
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="no-incident-data">No risk instances found for selected filters.</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import '../Risk/RiskInstances.css'
import { validateField, sanitizeString } from './validation.js'

export default {
  name: 'RiskInstances',
  data() {
    return {
      instances: [],
      selectedCriticality: '',
      selectedStatus: '',
      selectedCategory: '',
      selectedPriority: '',
      searchQuery: '',
      showAddForm: false,
      validationErrors: {}, // Store validation errors
      newInstance: {
        RiskId: null,
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        Appetite: '',
        RiskDescription: '',
        RiskLikelihood: '',
        RiskImpact: '',
        RiskExposureRating: '',
        RiskPriority: '',
        RiskResponseType: '',
        RiskResponseDescription: '',
        RiskMitigation: '',
        RiskOwner: '',
        RiskStatus: 'Open',
        UserId: 1
      }
    }
  },
  computed: {
    uniqueCriticality() {
      return [...new Set(this.instances.map(i => i.Criticality).filter(Boolean))]
    },
    uniqueStatus() {
      return [...new Set(this.instances.map(i => i.RiskStatus).filter(Boolean))]
    },
    uniqueCategory() {
      return [...new Set(this.instances.map(i => i.Category).filter(Boolean))]
    },
    uniquePriority() {
      return [...new Set(this.instances.map(i => i.RiskPriority).filter(Boolean))]
    },
    hasValidationErrors() {
      return Object.keys(this.validationErrors).length > 0
    },
    filteredInstances() {
      // If there are validation errors, don't apply filters
      if (this.hasValidationErrors) {
        return this.instances
      }
      
      let filtered = this.instances.filter(i =>
        (!this.selectedCriticality || i.Criticality === this.selectedCriticality) &&
        (!this.selectedStatus || i.RiskStatus === this.selectedStatus) &&
        (!this.selectedCategory || i.Category === this.selectedCategory) &&
        (!this.selectedPriority || i.RiskPriority === this.selectedPriority)
      )
      
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(instance => 
          (instance.RiskDescription && instance.RiskDescription.toLowerCase().includes(query)) ||
          (instance.RiskId && instance.RiskId.toString().includes(query)) ||
          (instance.Category && instance.Category.toLowerCase().includes(query)) ||
          (instance.RiskStatus && instance.RiskStatus.toLowerCase().includes(query)) ||
          (instance.Criticality && instance.Criticality.toLowerCase().includes(query))
        )
      }
      
      return filtered
    }
  },
  mounted() {
    this.fetchInstances()
  },
  methods: {
    // Validate search input
    validateSearchInput() {
      const result = validateField(this.searchQuery, 'text')
      if (!result.isValid) {
        this.validationErrors.searchQuery = result.error
      } else {
        delete this.validationErrors.searchQuery
      }
    },
    
    // Validate filter inputs
    validateFilterInput(field) {
      let value = this[field]
      let validationType
      
      switch(field) {
        case 'selectedCriticality':
          validationType = 'criticality'
          break
        case 'selectedStatus':
          validationType = 'riskStatus'
          break
        case 'selectedCategory':
          validationType = 'category'
          break
        case 'selectedPriority':
          validationType = 'riskPriority'
          break
        default:
          validationType = 'text'
      }
      
      const result = validateField(value, validationType)
      if (!result.isValid) {
        this.validationErrors[field] = result.error
      } else {
        delete this.validationErrors[field]
      }
    },
    
    // Sanitize query parameters for API calls
    sanitizeQueryParams(params) {
      const sanitized = {}
      
      for (const [key, value] of Object.entries(params)) {
        if (value === null || value === undefined || value === '') continue
        
        if (typeof value === 'string') {
          sanitized[key] = sanitizeString(value)
        } else {
          sanitized[key] = value
        }
      }
      
      return sanitized
    },
    
    fetchInstances() {
      // Using the direct endpoint as shown in Postman
      axios.get('http://localhost:8000/risk-instances')
        .then(response => {
          // Validate and sanitize the response data
          this.instances = this.validateResponseData(response.data)
          console.log('Fetched risk instances:', this.instances.length)
        })
        .catch(error => {
          console.error('Error fetching risk instances:', error)
          // Try alternative endpoint if the first one fails
          this.tryAlternativeEndpoint()
        })
    },
    
    tryAlternativeEndpoint() {
      console.log('Trying alternative endpoint...')
      axios.get('http://localhost:8000/api/risk-instances')
        .then(response => {
          // Validate and sanitize the response data
          this.instances = this.validateResponseData(response.data)
          console.log('Fetched risk instances from alternative endpoint:', this.instances.length)
        })
        .catch(error => {
          console.error('Error with alternative endpoint:', error)
        })
    },
    
    // Validate and sanitize response data
    validateResponseData(data) {
      if (!Array.isArray(data)) {
        console.error('Expected array response, got:', typeof data)
        return []
      }
      
      return data.map(item => {
        const sanitized = {}
        
        // Define expected fields and their types
        const expectedFields = {
          RiskInstanceId: 'id',
          RiskId: 'id',
          Category: 'category',
          Criticality: 'criticality',
          RiskStatus: 'riskStatus',
          RiskDescription: 'longText',
          RiskPriority: 'riskPriority'
        }
        
        // Validate and sanitize each field
        for (const [field, validationType] of Object.entries(expectedFields)) {
          if (item[field] !== undefined) {
            const result = validateField(item[field], validationType)
            if (result.isValid) {
              sanitized[field] = typeof item[field] === 'string' ? 
                sanitizeString(item[field]) : item[field]
            } else {
              // If invalid, use a safe default value
              switch(validationType) {
                case 'id':
                  sanitized[field] = null
                  break
                case 'category':
                case 'criticality':
                case 'riskStatus':
                case 'riskPriority':
                  sanitized[field] = ''
                  break
                case 'longText':
                  sanitized[field] = 'Invalid content'
                  break
                default:
                  sanitized[field] = null
              }
              console.warn(`Invalid ${field} value:`, item[field], result.error)
            }
          } else {
            // Field is missing, use default value
            sanitized[field] = validationType === 'id' ? null : ''
          }
        }
        
        return sanitized
      })
    },
    
    viewInstanceDetails(instanceId) {
      // Validate instanceId before navigation
      const result = validateField(instanceId, 'id')
      if (!result.isValid) {
        console.error('Invalid instance ID:', instanceId, result.error)
        return
      }
      
      this.$router.push(`/view-instance/${instanceId}`)
    },
    
    submitInstance() {
      // Validate all fields before submission
      const validationMap = {
        RiskId: 'id',
        Criticality: 'criticality',
        PossibleDamage: 'longText',
        Category: 'category',
        Appetite: 'appetite',
        RiskDescription: 'longText',
        RiskLikelihood: 'riskRating',
        RiskImpact: 'riskRating',
        RiskExposureRating: 'number',
        RiskPriority: 'riskPriority',
        RiskResponseType: 'riskResponseType',
        RiskResponseDescription: 'longText',
        RiskMitigation: 'longText',
        RiskOwner: 'text',
        RiskStatus: 'riskStatus',
        UserId: 'id'
      }
      
      const errors = {}
      let isValid = true
      
      // Validate each field
      for (const [field, validationType] of Object.entries(validationMap)) {
        const result = validateField(this.newInstance[field], validationType)
        if (!result.isValid) {
          errors[field] = result.error
          isValid = false
        }
      }
      
      // If validation fails, update errors and return
      if (!isValid) {
        this.validationErrors = errors
        console.error('Validation failed:', errors)
        return
      }
      
      // Clear validation errors
      this.validationErrors = {}
      
      // Convert numeric string values to actual numbers and sanitize
      const formData = {
        RiskId: parseInt(this.newInstance.RiskId) || null,
        Criticality: sanitizeString(this.newInstance.Criticality),
        PossibleDamage: sanitizeString(this.newInstance.PossibleDamage),
        Category: sanitizeString(this.newInstance.Category),
        Appetite: sanitizeString(this.newInstance.Appetite),
        RiskDescription: sanitizeString(this.newInstance.RiskDescription),
        RiskLikelihood: parseFloat(this.newInstance.RiskLikelihood) || 0,
        RiskImpact: parseFloat(this.newInstance.RiskImpact) || 0,
        RiskExposureRating: this.newInstance.RiskExposureRating ? 
          parseFloat(this.newInstance.RiskExposureRating) : null,
        RiskPriority: sanitizeString(this.newInstance.RiskPriority),
        RiskResponseType: sanitizeString(this.newInstance.RiskResponseType),
        RiskResponseDescription: sanitizeString(this.newInstance.RiskResponseDescription),
        RiskMitigation: sanitizeString(this.newInstance.RiskMitigation),
        RiskOwner: sanitizeString(this.newInstance.RiskOwner),
        RiskStatus: sanitizeString(this.newInstance.RiskStatus),
        UserId: parseInt(this.newInstance.UserId) || null
      }
      
      axios.post('http://localhost:8000/api/risk-instances/', formData)
        .then(response => {
          // Validate response data before adding to instances
          const validatedInstance = this.validateResponseData([response.data])[0]
          
          // Add the new instance to the table
          this.instances.push(validatedInstance)
          
          // Reset the form
          this.newInstance = {
            RiskId: null,
            Criticality: '',
            PossibleDamage: '',
            Category: '',
            Appetite: '',
            RiskDescription: '',
            RiskLikelihood: '',
            RiskImpact: '',
            RiskExposureRating: '',
            RiskPriority: '',
            RiskResponseType: '',
            RiskResponseDescription: '',
            RiskMitigation: '',
            RiskOwner: '',
            RiskStatus: 'Open',
            UserId: 1
          }
          
          // Hide the form
          this.showAddForm = false
          
          // Show success message
          alert('Risk instance added successfully!')
        })
        .catch(error => {
          console.error('Error adding risk instance:', error.response?.data || error.message)
          alert('Error adding risk instance. Please check your data and try again.')
        })
    }
  }
}
</script>