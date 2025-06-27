<template>
  <div class="risk-register-container">
    <div class="risk-register-header-row">
      <h2 class="risk-register-title"><i class="fas fa-exclamation-triangle risk-register-icon"></i> Risk Register List</h2>
    </div>
    
    <div class="risk-register-filters-row">
      <div class="filter-group">
        <input 
          v-model="searchQuery" 
          class="risk-search-input" 
          type="text" 
          placeholder="Search..."
          @input="validateSearchInput"
          :class="{'input-error': validationErrors.searchQuery}"
        />
        <select v-model="selectedCriticality" class="sort-select" @change="validateFilterInput('selectedCriticality')">
          <option value="">All Criticality</option>
          <option v-for="c in uniqueCriticality" :key="c">{{ c }}</option>
        </select>
        <select v-model="selectedCategory" class="sort-select" @change="validateFilterInput('selectedCategory')">
          <option value="">All Category</option>
          <option v-for="cat in uniqueCategory" :key="cat">{{ cat }}</option>
        </select>
      </div>
    </div>

    <!-- Error message for validation errors -->
    <div v-if="hasValidationErrors" class="validation-error-summary">
      <p><i class="fas fa-exclamation-triangle"></i> Invalid input detected. Please correct the highlighted fields.</p>
    </div>

    <div class="risk-list-table-container">
      <table v-if="filteredRisks.length" class="risk-list-table">
        <thead>
          <tr>
            <th>RiskID</th>
            <th>ComplianceID</th>
            <th>Category</th>
            <th>Criticality</th>
            <th>Risk Type</th>
            <th>Risk Title</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="risk in paginatedRisks" :key="risk.RiskId">
            <td class="risk-id">{{ risk.RiskId }}</td>
            <td>{{ risk.ComplianceId }}</td>
            <td>
              <div class="category-badge">{{ risk.Category }}</div>
            </td>
            <td>
              <div :class="getCriticalityClass(risk.Criticality)">{{ risk.Criticality }}</div>
            </td>
            <td>{{ risk.RiskType || 'N/A' }}</td>
            <td>
              {{ risk.RiskTitle }}
            </td>
            <td>
              <button @click="viewRiskDetails(risk.RiskId)" class="view-risk-btn">
                View Risk
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="no-incident-data">No risks found for selected filters.</div>
    </div>

    <div class="pagination-controls">
      <button class="pagination-btn" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
        <i class="fas fa-chevron-left pagination-icon"></i> Previous
      </button>
      
      <div class="pagination-numbers">
        <button v-if="showPreviousEllipsis" class="page-number" @click="changePage(1)">1</button>
        <button v-if="showPreviousEllipsis" class="page-number">...</button>
        
        <button 
          v-for="page in displayedPageNumbers" 
          :key="page" 
          @click="changePage(page)" 
          :class="['page-number', currentPage === page ? 'active-page' : '']">
          {{ page }}
        </button>
        
        <button v-if="showNextEllipsis" class="page-number">...</button>
        <button v-if="showNextEllipsis" class="page-number" @click="changePage(totalPages)">{{ totalPages }}</button>
      </div>
      
      <div class="pagination-info">Page {{ currentPage }} of {{ totalPages || 1 }}</div>
      
      <button class="pagination-btn" :disabled="currentPage === totalPages || totalPages === 0" @click="changePage(currentPage + 1)">
        Next <i class="fas fa-chevron-right pagination-icon"></i>
      </button>
    </div>
  </div>
</template>

<script>
import './RiskRegisterList.css'
import axios from 'axios'
import { validateField, sanitizeString } from './validation.js'

export default {
  name: 'RiskRegisterList',
  data() {
    return {
      risks: [],
      selectedCriticality: '',
      selectedCategory: '',
      searchQuery: '',
      currentPage: 1,
      itemsPerPage: 15,
      maxDisplayedPages: 5,
      validationErrors: {} // Store validation errors
    }
  },
  computed: {
    uniqueCriticality() {
      return [...new Set(this.risks.map(i => i.Criticality).filter(Boolean))]
    },
    uniqueCategory() {
      return [...new Set(this.risks.map(i => i.Category).filter(Boolean))]
    },
    hasValidationErrors() {
      return Object.keys(this.validationErrors).length > 0
    },
    filteredRisks() {
      // If there are validation errors, don't apply filters
      if (this.hasValidationErrors) {
        return this.risks
      }
      
      let filtered = this.risks.filter(i =>
        (!this.selectedCriticality || i.Criticality === this.selectedCriticality) &&
        (!this.selectedCategory || i.Category === this.selectedCategory)
      )
      
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(risk => 
          risk.RiskTitle.toLowerCase().includes(query) ||
          (risk.RiskId && risk.RiskId.toString().includes(query)) ||
          (risk.ComplianceId && risk.ComplianceId.toString().includes(query)) ||
          (risk.Category && risk.Category.toLowerCase().includes(query))
        )
      }
      
      return filtered
    },
    paginatedRisks() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.filteredRisks.slice(start, end)
    },
    totalPages() {
      return Math.ceil(this.filteredRisks.length / this.itemsPerPage)
    },
    displayedPageNumbers() {
      if (this.totalPages <= this.maxDisplayedPages) {
        return Array.from({ length: this.totalPages }, (_, i) => i + 1)
      }

      let startPage = Math.max(1, this.currentPage - Math.floor(this.maxDisplayedPages / 2))
      let endPage = startPage + this.maxDisplayedPages - 1
      
      if (endPage > this.totalPages) {
        endPage = this.totalPages
        startPage = Math.max(1, endPage - this.maxDisplayedPages + 1)
      }
      
      return Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i)
    },
    showPreviousEllipsis() {
      return this.totalPages > this.maxDisplayedPages && this.displayedPageNumbers[0] > 1
    },
    showNextEllipsis() {
      return this.totalPages > this.maxDisplayedPages && this.displayedPageNumbers[this.displayedPageNumbers.length - 1] < this.totalPages
    }
  },
  mounted() {
    this.fetchRisks()
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
        case 'selectedCategory':
          validationType = 'category'
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
    
    // Validate page number
    validatePageNumber(page) {
      const result = validateField(page, 'number')
      if (!result.isValid || page < 1 || page > this.totalPages) {
        return false
      }
      return true
    },
    
    fetchRisks() {
      axios.get('http://localhost:8000/api/risks/')
        .then(response => {
          // Validate and sanitize the response data
          this.risks = this.validateResponseData(response.data)
        })
        .catch(error => {
          console.error('Error fetching risks:', error)
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
          RiskId: 'id',
          ComplianceId: 'id',
          Category: 'category',
          Criticality: 'criticality',
          RiskType: 'text',
          RiskTitle: 'text'
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
                  sanitized[field] = ''
                  break
                case 'text':
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
    
    getCriticalityClass(criticality) {
      if (!criticality) return ''
      
      // Validate criticality value
      const result = validateField(criticality, 'criticality')
      if (!result.isValid) {
        return ''
      }
      
      criticality = criticality.toLowerCase()
      if (criticality === 'critical') return 'priority-critical'
      if (criticality === 'high') return 'priority-high'
      if (criticality === 'medium') return 'priority-medium'
      if (criticality === 'low') return 'priority-low'
      return ''
    },
    
    changePage(page) {
      // Validate page number before changing
      if (this.validatePageNumber(page)) {
        this.currentPage = page
      }
    },
    
    viewRiskDetails(riskId) {
      // Validate riskId before navigation
      const result = validateField(riskId, 'id')
      if (!result.isValid) {
        console.error('Invalid risk ID:', riskId, result.error)
        return
      }
      
      this.$router.push(`/view-risk/${riskId}`)
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      // Validate date string
      const result = validateField(dateString, 'date')
      if (!result.isValid) {
        return 'Invalid Date'
      }
      
      const date = new Date(dateString)
      return date.toLocaleDateString()
    }
  }
}
</script> 