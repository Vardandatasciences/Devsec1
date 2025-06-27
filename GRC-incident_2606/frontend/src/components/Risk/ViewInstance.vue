<template>
  <div class="view-instance-container">
    <div class="view-instance-header">
      <h2 class="view-instance-title"><i class="fas fa-exclamation-triangle risk-icon"></i> Risk Instance Details</h2>
      <button class="back-button" @click="goBack">
        <i class="fas fa-arrow-left"></i> Back to Risk Instances
      </button>
    </div>

    <div class="instance-details-card" v-if="instance">
      <div class="instance-details-header">
        <div class="instance-id-section">
          <span class="instance-id-label">Risk ID:</span>
          <span class="instance-id-value">{{ instance.RiskId }}</span>
          <span class="instance-id-label ml-4">Instance ID:</span>
          <span class="instance-id-value">{{ instance.RiskInstanceId }}</span>
        </div>
        <div class="instance-meta">
          <div class="instance-meta-item">
            <span class="origin-badge">MANUAL</span>
          </div>
          <div class="instance-meta-item">
            <span class="category-badge">{{ instance.Category }}</span>
          </div>
          <div class="instance-meta-item">
            <span :class="'priority-' + instance.Criticality.toLowerCase()">
              {{ instance.Criticality }}
            </span>
          </div>
          <div class="instance-meta-item">
            <span :class="'status-' + (instance.RiskStatus ? instance.RiskStatus.toLowerCase().replace(/\s+/g, '-') : 'open')">
              {{ instance.RiskStatus || 'Open' }}
            </span>
          </div>
        </div>
      </div>

      <div class="instance-details-grid">
        <div class="detail-item">
          <span class="detail-label">Description:</span>
          <span class="detail-value">{{ instance.RiskDescription }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Category:</span>
          <span class="detail-value">{{ instance.Category }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Criticality:</span>
          <span class="detail-value" :class="'priority-' + instance.Criticality.toLowerCase()">
            {{ instance.Criticality }}
          </span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Status:</span>
          <span class="detail-value" :class="'status-' + (instance.RiskStatus ? instance.RiskStatus.toLowerCase().replace(/\s+/g, '-') : 'open')">
            {{ instance.RiskStatus || 'Open' }}
          </span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Possible Damage:</span>
          <span class="detail-value">{{ instance.PossibleDamage || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Risk Appetite:</span>
          <span class="detail-value">{{ instance.Appetite || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Likelihood:</span>
          <span class="detail-value">{{ instance.RiskLikelihood || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Impact:</span>
          <span class="detail-value">{{ instance.RiskImpact || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Exposure Rating:</span>
          <span class="detail-value">{{ instance.RiskExposureRating || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Priority:</span>
          <span class="detail-value">{{ instance.RiskPriority || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Response Type:</span>
          <span class="detail-value">{{ instance.RiskResponseType || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Response Description:</span>
          <span class="detail-value">{{ instance.RiskResponseDescription || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Mitigation:</span>
          <span class="detail-value">{{ instance.RiskMitigation || 'Not specified' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Risk Owner:</span>
          <span class="detail-value">{{ instance.RiskOwner || 'Not assigned' }}</span>
        </div>
      </div>
    </div>

    <div v-else class="no-instance-data">
      Loading instance details or no instance found...
    </div>
  </div>
</template>

<script>
import './ViewInstance.css'
import axios from 'axios'

export default {
  name: 'ViewInstance',
  data() {
    return {
      instance: null
    }
  },
  created() {
    this.fetchInstanceDetails()
  },
  methods: {
    fetchInstanceDetails() {
      const instanceId = this.$route.params.id
      if (!instanceId) {
        this.$router.push('/risk/riskinstances-list')
        return
      }

      axios.get(`http://localhost:8000/api/risk-instances/${instanceId}/`)
        .then(response => {
          this.instance = response.data
        })
        .catch(error => {
          console.error('Error fetching risk instance details:', error)
          // Try alternative endpoint if the first one fails
          this.tryAlternativeEndpoint(instanceId)
        })
    },
    tryAlternativeEndpoint(instanceId) {
      axios.get(`http://localhost:8000/risk-instances/${instanceId}/`)
        .then(response => {
          this.instance = response.data
        })
        .catch(error => {
          console.error('Error with alternative endpoint:', error)
        })
    },
    goBack() {
      this.$router.push('/risk/riskinstances-list')
    }
  }
}
</script> 