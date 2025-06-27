<template>
  <div class="view-risk-container">
    <div class="view-risk-header">
      <h2 class="view-risk-title"><i class="fas fa-exclamation-triangle risk-icon"></i> Risk Details</h2>
      <button class="back-button" @click="goBack">
        <i class="fas fa-arrow-left"></i> Back to Risk Register
      </button>
    </div>

    <div class="risk-details-card" v-if="risk">
      <div class="risk-details-top">
        <div class="risk-id-section">
          <span class="risk-id-label">Risk ID:</span>
          <span class="risk-id-value">{{ risk.RiskId }}</span>
        </div>
        <div class="risk-meta">
          <div class="risk-category">{{ risk.Category }}</div>
          <div class="risk-criticality" :class="getCriticalityClass(risk.Criticality)">{{ risk.Criticality }}</div>
        </div>
      </div>

      <div class="risk-title-section">
        <h3>{{ risk.RiskTitle }}</h3>
        <div class="compliance-section">
          <span class="compliance-label">Compliance ID:</span>
          <span class="compliance-value">{{ risk.ComplianceId || 'N/A' }}</span>
        </div>
      </div>

      <div class="risk-content">
        <div class="risk-content-row">
          <div class="risk-content-column">
            <h4 class="section-title">Risk Description:</h4>
            <div class="section-content">{{ risk.RiskDescription || 'N/A' }}</div>
          </div>
          <div class="risk-content-column">
            <h4 class="section-title">Business Impact:</h4>
            <div class="section-content">{{ risk.BusinessImpact || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-content-row">
          <div class="risk-content-column">
            <h4 class="section-title">Possible Damage:</h4>
            <div class="section-content">{{ risk.PossibleDamage || 'N/A' }}</div>
          </div>
          <div class="risk-content-column">
            <h4 class="section-title">Risk Likelihood:</h4>
            <div class="section-content">{{ risk.RiskLikelihood || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-content-row">
          <div class="risk-content-column">
            <h4 class="section-title">Risk Impact:</h4>
            <div class="section-content">{{ risk.RiskImpact || 'N/A' }}</div>
          </div>
          <div class="risk-content-column">
            <h4 class="section-title">Risk Exposure Rating:</h4>
            <div class="section-content">{{ risk.RiskExposureRating || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-content-row">
          <div class="risk-content-column">
            <h4 class="section-title">Risk Priority:</h4>
            <div class="section-content">{{ risk.RiskPriority || 'N/A' }}</div>
          </div>
          <div class="risk-content-column">
            <h4 class="section-title">Risk Mitigation:</h4>
            <div class="section-content">{{ risk.RiskMitigation || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-content-row">
          <div class="risk-content-column">
            <h4 class="section-title">Created At:</h4>
            <div class="section-content">{{ formatDate(risk.CreatedAt) }}</div>
          </div>
          <div class="risk-content-column">
            <!-- Empty column for alignment -->
          </div>
        </div>
      </div>
    </div>

    <div v-else class="no-risk-data">
      Loading risk details or no risk found...
    </div>
  </div>
</template>

<script>
import './ViewRisk.css'
import axios from 'axios'

export default {
  name: 'ViewRisk',
  data() {
    return {
      risk: null
    }
  },
  created() {
    this.fetchRiskDetails()
  },
  methods: {
    fetchRiskDetails() {
      const riskId = this.$route.params.id
      if (!riskId) {
        this.$router.push('/risk/riskregister-list')
        return
      }

      axios.get(`http://localhost:8000/api/risks/${riskId}/`)
        .then(response => {
          this.risk = response.data
        })
        .catch(error => {
          console.error('Error fetching risk details:', error)
        })
    },
    getCriticalityClass(criticality) {
      if (!criticality) return ''
      criticality = criticality.toLowerCase()
      if (criticality === 'critical') return 'priority-critical'
      if (criticality === 'high') return 'priority-high'
      if (criticality === 'medium') return 'priority-medium'
      if (criticality === 'low') return 'priority-low'
      return ''
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString()
    },
    goBack() {
      this.$router.push('/risk/riskregister-list')
    }
  }
}
</script> 