// popupUtils.js
// Utility functions for compliance-specific popup operations

import { PopupService } from '../../../modules/popup';

/**
 * Compliance Popup Utilities
 * Contains pre-configured popup functions specific to the Compliance module
 */
export const CompliancePopups = {
  /**
   * Show a popup for successful compliance creation
   * @param {Object} compliance - The created compliance data
   */
  complianceCreated(compliance) {
    const complianceId = compliance.compliance_id || compliance.ComplianceId;
    const message = `Compliance #${complianceId} created successfully and sent for review.`;
    PopupService.success(message, 'Compliance Created');
  },

  /**
   * Show a popup for successful compliance update
   * @param {Object} compliance - The updated compliance data
   */
  complianceUpdated(compliance) {
    const complianceId = compliance.compliance_id || compliance.ComplianceId;
    const message = `Compliance #${complianceId} updated successfully and sent for review.`;
    PopupService.success(message, 'Compliance Updated');
  },

  /**
   * Show a popup for successful compliance clone
   * @param {Object} compliance - The cloned compliance data
   */
  complianceCloned(compliance) {
    const complianceId = compliance.compliance_id || compliance.ComplianceId;
    const message = `Compliance #${complianceId} cloned successfully and sent for review.`;
    PopupService.success(message, 'Compliance Cloned');
  },

  /**
   * Show a popup for successful compliance version toggle
   * @param {string} status - The new status (Active/Inactive)
   * @param {string} version - The compliance version
   */
  complianceStatusChanged(status, version) {
    const message = `Compliance version ${version} ${status === 'Active' ? 'activated' : 'deactivated'} successfully.`;
    PopupService.success(message, 'Status Updated');
  },

  /**
   * Show a popup for successful compliance review submission
   * @param {boolean} approved - Whether the compliance was approved
   */
  reviewSubmitted(approved) {
    const message = approved 
      ? 'Compliance has been approved successfully.' 
      : 'Compliance has been rejected.';
    PopupService.success(message, 'Review Submitted');
  },

  /**
   * Show a popup for failed compliance operation
   * @param {string} operation - The operation that failed
   * @param {string} error - The error message
   */
  operationFailed(operation, error) {
    const message = `Failed to ${operation}: ${error}`;
    PopupService.error(message, 'Operation Failed');
  },

  /**
   * Show a popup for compliance validation errors
   * @param {Array|Object} errors - Validation errors
   */
  validationFailed(errors) {
    let errorMessage;
    
    if (Array.isArray(errors)) {
      errorMessage = errors.join('\n');
    } else if (typeof errors === 'object') {
      errorMessage = Object.entries(errors)
        .map(([field, message]) => `${field}: ${message}`)
        .join('\n');
    } else {
      errorMessage = errors || 'Validation failed. Please check your inputs.';
    }
    
    PopupService.error(errorMessage, 'Validation Error');
  },

  /**
   * Show a confirmation popup for compliance deactivation
   * @param {Object} compliance - The compliance to deactivate
   * @param {Function} onConfirm - Callback when user confirms
   * @param {Function} onCancel - Callback when user cancels (optional)
   */
  confirmDeactivation(compliance, onConfirm, onCancel) {
    const description = compliance.ComplianceItemDescription || 'this compliance';
    const message = `Are you sure you want to deactivate "${description}"?`;
    
    PopupService.confirm(message, 'Confirm Deactivation', onConfirm, onCancel);
  },

  /**
   * Show a comment popup for getting deactivation reason
   * @param {Object} compliance - The compliance to deactivate
   * @param {Function} onSubmit - Callback when user submits reason
   */
  getDeactivationReason(compliance, onSubmit) {
    const description = compliance.ComplianceItemDescription || 'this compliance';
    const message = `Please provide a reason for deactivating "${description}":`;
    
    PopupService.comment(message, 'Deactivation Reason', onSubmit);
  },

  /**
   * Show a popup for successful export
   * @param {string} format - The export format
   * @param {string} url - The download URL (optional)
   */
  exportCompleted(format, url = null) {
    let message = `Export to ${format.toUpperCase()} completed successfully.`;
    
    if (url) {
      message += ' The file will be downloaded automatically.';
    }
    
    PopupService.success(message, 'Export Completed');
    
    // If URL is provided, trigger download
    if (url) {
      setTimeout(() => {
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance_export.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }, 1000);
    }
  },

  /**
   * Show an information popup with compliance details
   * @param {Object} compliance - The compliance object
   */
  showComplianceInfo(compliance) {
    if (!compliance) {
      PopupService.show({
        type: 'info',
        heading: 'Information',
        message: 'No compliance details available.',
        buttons: [{ label: 'OK', action: 'ok' }]
      });
      return;
    }

    const info = [
      `ID: ${compliance.ComplianceId || compliance.compliance_id || 'N/A'}`,
      `Description: ${compliance.ComplianceItemDescription || 'N/A'}`,
      `Version: ${compliance.ComplianceVersion || 'N/A'}`,
      `Status: ${compliance.Status || 'N/A'}`,
      `Criticality: ${compliance.Criticality || 'N/A'}`,
      `Created By: ${compliance.CreatedByName || 'N/A'}`,
      `Created Date: ${compliance.CreatedByDate || 'N/A'}`
    ].join('\n');

    PopupService.show({
      type: 'info',
      heading: 'Compliance Details',
      message: info,
      buttons: [{ label: 'OK', action: 'ok' }]
    });
  },

  /**
   * Show a warning popup for potential issues
   * @param {string} message - The warning message
   * @param {string} heading - The popup heading (optional)
   */
  showWarning(message, heading = 'Warning') {
    PopupService.warning(message, heading);
  },

  /**
   * Show a confirmation popup for deleting a compliance
   * @param {Object} compliance - The compliance to delete
   * @param {Function} onConfirm - Callback when user confirms
   * @param {Function} onCancel - Callback when user cancels (optional)
   */
  confirmDelete(compliance, onConfirm, onCancel) {
    const description = compliance.ComplianceItemDescription || 'this compliance';
    const message = `Are you sure you want to delete "${description}"? This action cannot be undone.`;
    
    PopupService.confirm(message, 'Confirm Deletion', onConfirm, onCancel);
  },

  /**
   * Show a confirmation popup for approving a compliance
   * @param {Object} compliance - The compliance to approve
   * @param {Function} onConfirm - Callback when user confirms
   * @param {Function} onCancel - Callback when user cancels (optional)
   */
  confirmApproval(compliance, onConfirm, onCancel) {
    const description = compliance.ComplianceItemDescription || 'this compliance';
    const message = `Are you sure you want to approve "${description}"?`;
    
    PopupService.confirm(message, 'Confirm Approval', onConfirm, onCancel);
  },

  /**
   * Show a confirmation popup for rejecting a compliance
   * @param {Function} onConfirm - Callback when user confirms (to show comment popup)
   * @param {Function} onCancel - Callback when user cancels (optional)
   */
  confirmRejection(onConfirm, onCancel) {
    const message = 'Are you sure you want to reject this compliance?';
    
    PopupService.confirm(message, 'Confirm Rejection', onConfirm, onCancel);
  },

  /**
   * Show a comment popup for getting rejection reason
   * @param {Function} onSubmit - Callback when user submits reason
   */
  getRejectionReason(onSubmit) {
    const message = 'Please provide a reason for rejecting this compliance:';
    
    PopupService.comment(message, 'Rejection Reason', onSubmit);
  },

  /**
   * Show a popup with auto-close for minor notifications
   * @param {string} message - The notification message
   * @param {string} type - The popup type (success, info, warning, error)
   * @param {string} heading - The popup heading
   * @param {number} timeout - Auto-close timeout in milliseconds
   */
  notify(message, type = 'info', heading = 'Notification', timeout = 3000) {
    PopupService.show({
      type: type,
      heading: heading,
      message: message,
      buttons: [{ label: 'OK', action: 'ok' }],
      autoClose: timeout
    });
  },

  /**
   * Show a popup for session timeout warning
   * @param {Function} onExtend - Callback to extend the session
   * @param {Function} onLogout - Callback to logout
   */
  sessionTimeout(onExtend, onLogout) {
    PopupService.show({
      type: 'warning',
      heading: 'Session Expiring',
      message: 'Your session is about to expire due to inactivity. Do you want to stay logged in?',
      buttons: [
        { label: 'Stay Logged In', action: 'extend', class: 'success' },
        { label: 'Logout', action: 'logout', class: 'error' }
      ]
    });

    if (onExtend) PopupService.onAction('extend', onExtend);
    if (onLogout) PopupService.onAction('logout', onLogout);
  },

  /**
   * Show a popup for displaying audit information
   * @param {Object} auditInfo - The audit information
   */
  showAuditInfo(auditInfo) {
    if (!auditInfo) {
      PopupService.show({
        type: 'info',
        heading: 'Audit Information',
        message: 'No audit information available for this compliance.',
        buttons: [{ label: 'OK', action: 'ok' }]
      });
      return;
    }

    const info = [
      `Performed By: ${auditInfo.audit_performer_name || 'N/A'}`,
      `Approved By: ${auditInfo.audit_approver_name || 'N/A'}`,
      `Date: ${auditInfo.audit_date || 'N/A'}`,
      `Time: ${auditInfo.audit_time || 'N/A'}`,
      `Status: ${auditInfo.audit_findings_status || 'N/A'}`,
      `Comments: ${auditInfo.comments || 'N/A'}`
    ].join('\n');

    PopupService.show({
      type: 'info',
      heading: 'Audit Information',
      message: info,
      buttons: [{ label: 'OK', action: 'ok' }]
    });
  }
}; 