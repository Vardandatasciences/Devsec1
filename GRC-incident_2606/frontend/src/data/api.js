import axios from 'axios';

// API base URL WITHOUT /api
const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000';
console.log(`Using API URL: ${API_URL}`);

// Axios Instance
const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
});

// Request Interceptor
axiosInstance.interceptors.request.use(
  config => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.baseURL}${config.url}`,
      config.data ? JSON.stringify(config.data) : '{}'
    );
    return config;
  },
  error => {
    console.error("Request error:", error);
    return Promise.reject(error);
  }
);

// Response Interceptor
axiosInstance.interceptors.response.use(
  response => {
    console.log(`API Response from ${response.config.url}:`);
    if (typeof response.data === 'object') {
      console.log('Full Response Data:', response.data);
      console.log('JSON String:', JSON.stringify(response.data));
    } else {
      console.log(response.data);
    }
    return response;
  },
  error => {
    console.error(`API Error from ${error.config?.url || 'unknown endpoint'}:`,
      error.response?.data ? JSON.stringify(error.response.data) : error.message
    );
    console.error(`Status: ${error.response?.status}, Status Text: ${error.response?.statusText}`);
    if (error.response?.data?.details) {
      console.error('Error details:', error.response.data.details);
    }
    return Promise.reject(error);
  }
);

// API Functions
export const api = {
  // Framework
  getFrameworks: () => axiosInstance.get('/api/frameworks/'),
  getFrameworkDetails: (id) => axiosInstance.get(`/api/frameworks/${id}/`),
  getFrameworkDetailsForTree: (id) => axiosInstance.get(`/api/frameworks/${id}/tree/`),

  // Policies
  getPolicies: () => axiosInstance.get('/api/policies/'),
  getPoliciesByFramework: (frameworkId) => axiosInstance.get(`/api/frameworks/${frameworkId}/policies/`),

  // SubPolicies
  getSubPolicies: (policyId) => axiosInstance.get(`/api/policies/${policyId}/get-subpolicies/`),

  // Users
  getUsers: () => axiosInstance.get('/api/users/'),

  // Assignment
  getAssignData: () => axiosInstance.get('/assign-data/'),
  allocatePolicy: (data) => axiosInstance.post('/allocate-policy/', data),

  // Incidents
  getIncidents: () => axiosInstance.get('/api/incidents/'),

  // Audits
  getAllAudits: () => axiosInstance.get('/audits/'),
  getMyAudits: () => axiosInstance.get('/my-audits/'),
  getMyReviews: () => axiosInstance.get('/my-reviews/'),
  getAuditDetails: (id) => axiosInstance.get(`/audits/${id}/`),
  updateAuditStatus: (id, data) => axiosInstance.post(`/audits/${id}/status/`, data),
  updateAuditReviewStatus: (id, data) => axiosInstance.post(`/audits/${id}/review-status/`, data),
  saveReviewProgress: (id, data) => axiosInstance.post(`/audits/${id}/save-review-progress/`, data),
  getAuditStatus: (id) => axiosInstance.get(`/audits/${id}/get-status/`),
  getAuditCompliances: (id) => axiosInstance.get(`/audits/${id}/compliances/`),
  addComplianceToAudit: (id, data) => axiosInstance.post(`/audits/${id}/add-compliance/`, data),
  updateComplianceStatus: (complianceId, data) => axiosInstance.post(`/audit-findings/${complianceId}/`, data),
  submitAuditFindings: (id, data = {}) => axiosInstance.post(`/audits/${id}/submit/`, data),
  loadLatestReviewVersion: (id) => axiosInstance.get(`/audits/${id}/load-latest-review-version/`),
  loadAuditContinuingData: (id) => axiosInstance.get(`/audits/${id}/load-continuing-data/`),
  saveAuditVersion: (id, auditData) => axiosInstance.post(`/audits/${id}/save-audit-version/`, { audit_data: auditData }),

  // Task Views
  getAuditTaskDetails: (id) => axiosInstance.get(`/api/audits/${id}/task-details/`),
  saveVersion: (id, data) => axiosInstance.post(`/audits/${id}/save-version/`, data),
  sendForReview: (id, data) => axiosInstance.post(`/audits/${id}/send-for-review/`, data),

  // Audit Reports
  checkAuditReports: (params) => axiosInstance.get('/audit-reports/check/', { params }),
  getReportDetails: (ids) => axiosInstance.get('/audit-reports/details/', { params: { report_ids: ids } }),

  // Versions
  getAuditVersions: (id) => axiosInstance.get(`/audits/${id}/versions/`),
  getAuditVersionDetails: (id, version) => axiosInstance.get(`/audits/${id}/versions/${version}/`),
  checkAuditVersion: (id) => axiosInstance.get(`/audits/${id}/check-version/`),


  // Evidence Upload
  uploadEvidence: (complianceId, formData) =>
    axiosInstance.post(`/upload-evidence/${complianceId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // S3 Upload
  uploadFile: (formData, onUploadProgress) =>
    axios.post('http://localhost:3001/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress
    }),

  // Compliance Service
  createCompliance: (data) => axiosInstance.post('/compliance/create/', data),
  editCompliance: (id, data) => axiosInstance.put(`/compliance/${id}/edit/`, data),
  cloneCompliance: (id) => axiosInstance.post(`/compliance/${id}/clone/`),
  getComplianceDashboard: () => axiosInstance.get('/compliance/dashboard/'),

  // Audit Report Download
  downloadAuditReport: (id) => axiosInstance.get(`/generate-audit-report/${id}/`, {
    responseType: 'blob',
    headers: {
      'Accept': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
  }),

  // Debug
  debugPrintAuditData: (id) => {
    console.log(`===== DEBUG PRINT AUDIT DATA FOR AUDIT ID: ${id} =====`);
    return Promise.all([
      axiosInstance.get(`/audits/${id}/`),
      axiosInstance.get(`/audits/${id}/check-version/`),
      axiosInstance.get(`/audits/${id}/compliances/`)
    ]).then(([auditDetails, versionCheck, compliances]) => {
      console.log('1. AUDIT DETAILS:', auditDetails.data);
      console.log('2. VERSION INFO:', versionCheck.data);
      console.log('3. COMPLIANCES STRUCTURE:', compliances.data);
      return { auditDetails: auditDetails.data, versionCheck: versionCheck.data, compliances: compliances.data };
    });
  },
};

export default api;
