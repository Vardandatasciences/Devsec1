import axios from 'axios';
 
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000 // Add a 15-second timeout for all requests
});
 
// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
   
    // Add more detailed logging for network errors
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error details:', {
        message: error.message,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          timeout: error.config?.timeout
        }
      });
    }
    
    return Promise.reject(error);
  }
);

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
 
  // Log outgoing requests
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
    data: config.data,
    params: config.params
  });
  
  return config;
});

export const complianceService = {
  // Framework endpoints
  getFrameworks: () => api.get('api/frameworks/'),
  
  // Policy endpoints
  getPolicies: (frameworkId) => api.get(`api/frameworks/${frameworkId}/policies/`),
  
  // SubPolicy endpoints
  getSubPolicies: (policyId) => api.get(`api/policies/${policyId}/subpolicies/`),
  
  // Compliance endpoints
  createCompliance: (data) => api.post('api/compliance/create/', data),
  editCompliance: (complianceId, data) => api.put(`api/compliance/${complianceId}/edit/`, data),
  cloneCompliance: (complianceId, data) => api.post(`api/compliance/${complianceId}/clone/`, data),
  getComplianceDashboard: (filters) => api.get('api/compliance/user-dashboard/', { params: filters }),
  getComplianceAnalytics: (data) => api.post('api/compliance/kpi-dashboard/analytics/', data),
  getCompliancesBySubPolicy: (subPolicyId) => api.get(`api/subpolicies/${subPolicyId}/compliances/`),
  getComplianceById: (complianceId) => api.get(`api/compliance/${complianceId}/`),
  toggleComplianceVersion: (complianceId) => api.post(`api/compliance/${complianceId}/toggle-version/`),
  deactivateCompliance: (complianceId, data) => api.post(`api/compliance/${complianceId}/deactivate/`, data),
  approveComplianceDeactivation: (approvalId, data) => api.post(`api/compliance/deactivation/${approvalId}/approve/`, data),
  rejectComplianceDeactivation: (approvalId, data) => api.post(`api/compliance/deactivation/${approvalId}/reject/`, data),
  
  // KPI endpoints
  getMaturityLevelKPI: () => api.get('api/compliance/kpi-dashboard/analytics/maturity-level/'),
  getNonComplianceCount: () => api.get('api/compliance/kpi-dashboard/analytics/non-compliance-count/'),
  getMitigatedRisksCount: () => api.get('api/compliance/kpi-dashboard/analytics/mitigated-risks-count/'),
  getAutomatedControlsCount: () => api.get('api/compliance/kpi-dashboard/analytics/automated-controls-count/'),
  getNonComplianceRepetitions: () => api.get('api/compliance/kpi-dashboard/analytics/non-compliance-repetitions/'),
  getComplianceKPI: () => api.get('api/compliance/kpi-dashboard/'),
  getComplianceStatusOverview: () => api.get('api/compliance/kpi-dashboard/analytics/status-overview/'),
  getReputationalImpact: () => api.get('api/compliance/kpi-dashboard/analytics/reputational-impact/'),
  getRemediationCost: () => api.get('api/compliance/kpi-dashboard/analytics/remediation-cost/'),
  getNonCompliantIncidents: (period) => api.get('api/compliance/kpi-dashboard/analytics/non-compliant-incidents/', { params: { period } }),
  
  // Compliance approval endpoints with more robust error handling
  getPolicyApprovals: (params) => api.get('api/policy-compliance-approvals/reviewer/', { params }),
  getRejectedApprovals: (reviewerId) => api.get(`api/policy-approvals/rejected/${reviewerId}/`),
  submitComplianceReview: (approvalId, data) => {
    console.log(`Submitting compliance review for approval ID ${approvalId}:`, data);
    // Use a more explicit timeout for this critical endpoint
    return api.put(`api/compliance-approvals/${approvalId}/review/`, data, { timeout: 20000 });
  },
  resubmitComplianceApproval: (approvalId, data) => api.put(`api/compliance-approvals/resubmit/${approvalId}/`, data),

 
  // User endpoints
  getUsers: () => api.get('api/users/'),
 
  getOntimeMitigationPercentage: () => api.get('api/compliance/kpi-dashboard/analytics/ontime-mitigation/'),
};

export const incidentService = {
  // Incident main endpoints
  getIncidents: (params) => api.get('api/incidents/', { params }),
  createIncident: (data) => api.post('api/incidents/create/', data),
  updateIncidentStatus: (incidentId, data) => api.put(`api/incidents/${incidentId}/status/`, data),
  
  // Incident analytics endpoints
  getIncidentMetrics: (params) => api.get('api/incidents/metrics/', { params }),
  getIncidentMTTD: (params) => api.get('api/incidents/metrics/mttd/', { params }),
  getIncidentMTTR: (params) => api.get('api/incidents/metrics/mttr/', { params }),
  getIncidentMTTC: (params) => api.get('api/incidents/metrics/mttc/', { params }),
  getIncidentMTTRV: (params) => api.get('api/incidents/metrics/mttrv/', { params }),
  getIncidentVolume: (params) => api.get('api/incidents/metrics/volume/', { params }),
  getIncidentsBySeverity: (params) => api.get('api/incidents/metrics/by-severity/', { params }),
  getIncidentRootCauses: (params) => api.get('api/incidents/metrics/root-causes/', { params }),
  getIncidentTypes: (params) => api.get('api/incidents/metrics/types/', { params }),
  getIncidentOrigins: (params) => api.get('api/incidents/metrics/origins/', { params }),
  getIncidentCost: (params) => api.get('api/incidents/metrics/cost/', { params }),
  getIncidentClosureRate: (params) => api.get('api/incidents/metrics/closure-rate/', { params }),
  getIncidentReopenedCount: (params) => api.get('api/incidents/metrics/reopened-count/', { params }),
  getIncidentCount: (params) => api.get('api/incidents/metrics/count/', { params }),
  
  // Incident analytics for dashboard
  getIncidentDashboard: (params) => api.get('api/incidents/dashboard/', { params }),
  getIncidentAnalytics: (data) => api.post('api/incidents/dashboard/analytics/', data),
  
  // Other incident-related endpoints
  getIncidentCountsByStatus: () => api.get('api/incidents/counts-by-status/'),
  getRecentIncidents: (limit = 3) => api.get('api/incidents/recent/', { params: { limit } })
};

export const auditService = {
  // Audit findings related endpoints
  getAuditFindings: (params) => api.get('api/audit-findings/', { params }),
  getAuditFindingsDetail: (complianceId) => api.get(`api/audit-findings/${complianceId}/details/`),
  
  // Get data from lastchecklistitemverified table
  getChecklistVerified: (params = {}) => {
    const url = new URL(`${api.defaults.baseURL}/api/lastchecklistitemverified/`);
    
    // Add complied parameters if present
    if (params.complied && Array.isArray(params.complied)) {
      params.complied.forEach(value => {
        url.searchParams.append('complied[]', value);
      });
    } else {
      // Default to showing only non-compliant (0) and partially compliant (1)
      url.searchParams.append('complied[]', '0');
      url.searchParams.append('complied[]', '1');
    }
    
    return api.get(url.toString());
  },
  
  // Get specific audit finding details
  getAuditDetail: (auditId) => api.get(`api/audits/${auditId}/`),
  
  // Get audit findings by compliance id
  getAuditFindingsByCompliance: (complianceId) => api.get(`api/audit-findings/compliance/${complianceId}/`),
  getUsers: () => api.get('api/users/'),

  getOntimeMitigationPercentage: () => api.get('api/compliance/kpi-dashboard/analytics/ontime-mitigation/'),
};

 
export default api;
 

