<template>
  <div :class="['sidebar', { collapsed: isCollapsed }]">
    <div class="logo-container">
      <img :src="logo" alt="GRC Logo" class="logo-image" />
      <span v-if="!isCollapsed" class="logo-text">GRC</span>
      <span class="toggle" @click="toggleCollapse">
        {{ isCollapsed ? '»' : '«' }}
      </span>
    </div>

    <div class="menu">
      <!-- Policy Section -->
      <div @click="toggleSubmenu('policy')" class="menu-item has-submenu" :class="{'expanded': openMenus.policy}">
        <i class="fas fa-file-alt icon"></i>
        <span v-if="!isCollapsed">Policy</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.policy" class="submenu">
        <!-- 1. Policy Creation -->
        <div @click="toggleSubmenu('policyCreation')" class="menu-item has-submenu" :class="{'expanded': openMenus.policyCreation}">
          <i class="fas fa-plus-square icon"></i>
          <span>Policy Creation</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.policyCreation" class="submenu">
          <div class="menu-item" @click="navigate('/create-policy/create')">
            <i class="fas fa-plus icon"></i>
            <span>Create Policy</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/framework')">
            <i class="fas fa-sitemap icon"></i>
            <span>Create Framework</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/tailoring')">
            <i class="fas fa-edit icon"></i>
            <span>Tailoring & Templating</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/versioning')">
            <i class="fas fa-code-branch icon"></i>
            <span>Versioning</span>
          </div>
        </div>

        <!-- 2. Policies List -->
        <div @click="toggleSubmenu('policiesList')" class="menu-item has-submenu" :class="{'expanded': openMenus.policiesList}">
          <i class="fas fa-list icon"></i>
          <span>Policies List</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.policiesList" class="submenu">
          <div class="menu-item" @click="navigate('/policies-list/all')">
            <i class="fas fa-list-alt icon"></i>
            <span>All Policies</span>
          </div>
          <div class="menu-item" @click="navigate('/tree-policies')">
            <i class="fas fa-sitemap icon"></i>
            <span>Tree Policies</span>
          </div>
        </div>
        
        <div @click="navigate('/framework-explorer')" class="menu-item">
            <i class="fas fa-cubes icon"></i>
            <span>Framework Explorer</span>
          </div>

        <!-- 3. Policy Approval -->
        <div class="menu-item" @click="navigate('/policy/approval')">
          <i class="fas fa-check-circle icon"></i>
          <span>Policy Approval</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-approval')">
          <i class="fas fa-check-circle icon"></i>
          <span>Framework Approval</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-status-changes')">
          <i class="fas fa-exchange-alt icon"></i>
          <span>Status Change Requests</span>
        </div>

        <!-- 4. Performance Analysis -->
        <div @click="toggleSubmenu('performanceAnalysis')" class="menu-item has-submenu" :class="{'expanded': openMenus.performanceAnalysis}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.performanceAnalysis" class="submenu">
          <div class="menu-item" @click="navigate('/policy/performance/kpis')">
            <i class="fas fa-chart-bar icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/policy/performance/dashboard')">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>User Dashboard</span>
          </div>
        </div>
      </div>
      
      <!-- Compliance Section -->
      <div @click="toggleSubmenu('compliance')" class="menu-item">
        <i class="fas fa-balance-scale icon"></i>
        <span v-if="!isCollapsed">Compliance</span>
      </div>
      <div v-if="!isCollapsed && openMenus.compliance" class="submenu">
        <!-- 1. Compliances -->
        <div @click="toggleSubmenu('compliancesList')" class="menu-item has-submenu">
          <i class="fas fa-list-alt icon"></i>
          <span>Compliances</span>
        </div>
        <div v-if="openMenus.compliancesList" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/list')">
            <i class="fas fa-clipboard-list icon"></i>
            <span>Controls</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/compliances')">
            <i class="fas fa-tasks icon"></i>
            <span>Compliances</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/approver')">
            <i class="fas fa-check-circle icon"></i>
            <span>Compliance Approval</span>
          </div>
        </div>

        <!-- 2. Compliance Creation -->
        <div @click="toggleSubmenu('complianceCreation')" class="menu-item has-submenu">
          <i class="fas fa-plus-square icon"></i>
          <span>Compliance Creation</span>
        </div>
        <div v-if="openMenus.complianceCreation" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/create')">
            <i class="fas fa-file-alt icon"></i>
            <span>Create Compliance</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/tailoring')">
            <i class="fas fa-cut icon"></i>
            <span>Tailoring & Templating</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/versioning')">
            <i class="fas fa-code-branch icon"></i>
            <span>Versioning</span>
          </div>
        </div>

        <!-- 3. Performance Analysis -->
        <div @click="toggleSubmenu('performanceAnalysis')" class="menu-item has-submenu">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
        </div>
        <div v-if="openMenus.performanceAnalysis" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/kpi-dashboard')">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>KPIs Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/user-dashboard')">
            <i class="fas fa-user-chart icon"></i>
            <span>User Dashboard</span>
          </div>
        </div>
      </div>

      <!-- Risk Section -->
      <div @click="toggleSubmenu('risk')" class="menu-item">
        <i class="fas fa-exclamation-triangle icon"></i>
        <span v-if="!isCollapsed">Risk</span>
      </div>
      <div v-if="!isCollapsed && openMenus.risk" class="submenu">
        
        
        <!-- Risk Register with nested submenu -->
        <div @click="toggleSubmenu('riskRegister')" class="menu-item">
          <i class="fas fa-clipboard-list icon"></i>
          <span>Risk Register</span>
        </div>
        <div v-if="openMenus.riskRegister" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskregister-list')">
            <i class="fas fa-list icon"></i>
            <span>Risk Register List</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/create-risk')">
            <i class="fas fa-plus icon"></i>
            <span>Create Risk</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/tailoring')">
            <i class="fas fa-edit icon"></i>
            <span>Tailoring Existing Risk</span>
          </div>
        </div>
        
        <!-- Risk Instances with nested submenu -->
        <div @click="toggleSubmenu('riskInstances')" class="menu-item">
          <i class="fas fa-th-list icon"></i>
          <span>Risk Instances</span>
        </div>
        <div v-if="openMenus.riskInstances" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskinstances-list')">
            <i class="fas fa-list icon"></i>
            <span>Risk Instances List</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/create-instance')">
            <i class="fas fa-plus icon"></i>
            <span>Create Instance</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/scoring')">
            <i class="fas fa-chart-line icon"></i>
            <span>Risk Scoring</span>
          </div>
        </div>
        
        <!-- Risk Handling section -->
        <div @click="navigate('/risk/resolution')" class="menu-item">
          <i class="fas fa-cogs icon"></i>
          <span v-if="!isCollapsed">Risk Handling</span>
        </div>

        <!-- Risk Analytics with collapsible submenu -->
        <div @click="toggleSubmenu('riskAnalytics')" class="menu-item">
          <i class="fas fa-chart-bar icon"></i>
          <span v-if="!isCollapsed">Risk Analytics</span>
        </div>
        <div v-if="!isCollapsed && openMenus.riskAnalytics" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskdashboard')">
            <i class="fas fa-th-large icon"></i>
            <span>Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/riskkpi')">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPI Dashboard</span>
          </div>
        </div>
      </div>
      <!-- Auditor Section -->
      <div @click="toggleSubmenu('auditor')" class="menu-item">
        <i class="fas fa-user-tie icon"></i>
        <span v-if="!isCollapsed">Auditor</span>
      </div>
      <div v-if="!isCollapsed && openMenus.auditor" class="submenu">
        <div class="menu-item" @click="navigate('/auditor/dashboard')">
          <i class="fas fa-th-large icon"></i>
          <span>Audits</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/assign')">
          <i class="fas fa-check-square icon"></i>
          <span>Assign Audit</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/reviews')">
          <i class="fas fa-tasks icon"></i>
          <span>Review Audits</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/reports')">
          <i class="fas fa-file-alt icon"></i>
          <span>Audit Reports</span>
        </div>
        <div class="menu-item" @click="toggleSubmenu('performance')">
          <i class="fas fa-chart-bar icon"></i>
          <span>Performance Analysis</span>
        </div>
        <div v-if="openMenus.performance" class="sub-submenu">
          <div class="menu-item" @click="navigate('/auditor/performance/kpi')">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/auditor/performance/userdashboard')">
            <i class="fas fa-chart-line icon"></i>
            <span>Dashboard</span>
          </div>
        </div>
      </div>


      <!-- Incident Section -->
      <div @click="toggleSubmenu('incident')" class="menu-item">
        <i class="fas fa-exclamation-circle icon"></i>
        <span v-if="!isCollapsed">Incident</span>
      </div>
      <div v-if="!isCollapsed && openMenus.incident" class="submenu">
        <div @click="toggleSubmenu('incidentManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.incidentManagement}">
          <i class="fas fa-clipboard-list icon"></i>
          <span>Incident Management</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.incidentManagement" class="submenu">
          <div class="menu-item" @click="navigate('/incident/incident')">
            <i class="fas fa-list icon"></i>
            <span>Incident List</span>
          </div>
          <div class="menu-item" @click="navigate('/incident/create')">
            <i class="fas fa-plus icon"></i>
            <span>Create Incident</span>
          </div>
          <!-- Audit Findings List -->
          <div class="menu-item" @click="navigate('/incident/audit-findings')">
            <i class="fas fa-search icon"></i>
            <span>Audit Findings</span>
          </div>
          <!-- User Tasks -->
          <div class="menu-item" @click="navigate('/incident/user-tasks')">
            <i class="fas fa-user-check icon"></i>
            <span>User Tasks</span>
          </div>
        </div>
        <div @click="toggleSubmenu('incidentPerformance')" class="menu-item has-submenu" :class="{'expanded': openMenus.incidentPerformance}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.incidentPerformance" class="submenu">
          <div class="menu-item" @click="navigate('/incident/dashboard')">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/incident/performance/dashboard')">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Dashboard</span>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-profile">
      <i class="fas fa-user icon"></i>
      <span v-if="!isCollapsed">User Profile</span>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import logo from '../../assets/grc_logo1.png'
import '@fortawesome/fontawesome-free/css/all.min.css'

export default {
  name: 'PolicySidebar',
  setup() {
    const router = useRouter()
    const isCollapsed = ref(false)
    const openMenus = ref({
      policy: false,
      policyCreation: false,
      policiesList: false,
      performanceAnalysis: false,
      compliance: false,
      risk: false,
      auditor: false,
      incident: false,
      dashboard: false,
      complianceDashboard: false,
      policyManagement: false,

      createPolicy: false,
      performance: false,
      incidentManagement: false,
      incidentPerformance: false,
      auditFindings: false,
      compliances: false,
      compliancesView: false,
      complianceCreation: false,
      compliancesPerformanceAnalysis: false
    })

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    const toggleSubmenu = (section) => {
      openMenus.value[section] = !openMenus.value[section]
    }

    const handleDashboardClick = () => {
      toggleSubmenu('dashboard')
      if (!openMenus.value.dashboard) {
        router.push('/policy/dashboard')
      }
    }

    const navigate = (path) => {
      router.push(path)
    }

    return {
      isCollapsed,
      openMenus,
      logo,
      toggleCollapse,
      toggleSubmenu,
      navigate,
      handleDashboardClick
    }
  }
}
</script>

<style scoped>
/* Import the existing CSS file */
@import './sidebar.css';
</style> 