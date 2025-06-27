/**
 * Centralized validation module for Risk Management components
 * Implements allow-list validation for all user inputs
 */

// Regular expressions for validation
const VALIDATION_PATTERNS = {
  // Basic text - alphanumeric with common punctuation
  text: /^[A-Za-z0-9\s.,;:!?'"()\-_[\]]{0,255}$/,
  
  // Long text fields (descriptions, etc.)
  longText: /^[A-Za-z0-9\s.,;:!?'"()\-_[\]]{0,2000}$/,
  
  // IDs - only numbers
  id: /^\d{1,10}$/,
  
  // Numbers (including decimals)
  number: /^-?\d+(\.\d+)?$/,
  
  // Date in ISO format
  date: /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?)?$/,
  
  // Risk-specific validation patterns
  criticality: /^(Critical|High|Medium|Low)$/i,
  category: /^[A-Za-z0-9\s\-_]{1,50}$/,
  riskStatus: /^(Open|In Progress|Approved|Revision|Closed|Rejected|)$/i,
  riskPriority: /^(High|Medium|Low|)$/i,
  riskRating: /^([0-5](\.\d)?|)$/,
  appetite: /^(Yes|No|)$/i,
  riskResponseType: /^(Accept|Mitigate|Transfer|Avoid|)$/i
};

/**
 * Validates a single field value against the specified validation type
 * @param {*} value - The value to validate
 * @param {string} type - The type of validation to perform
 * @returns {Object} - Result object with isValid flag and error message if invalid
 */
export function validateField(value, type) {
  // Allow empty values for optional fields (except where explicitly required)
  if ((value === null || value === undefined || value === '') && 
      type !== 'required') {
    return { isValid: true };
  }
  
  // Convert to string for regex validation (except for number type)
  const stringValue = type === 'number' ? value : String(value);
  
  // Check if we have a pattern for this type
  const pattern = VALIDATION_PATTERNS[type];
  if (!pattern) {
    console.warn(`No validation pattern defined for type: ${type}`);
    return { isValid: false, error: `Invalid validation type: ${type}` };
  }
  
  // Test the value against the pattern
  if (!pattern.test(stringValue)) {
    return { 
      isValid: false, 
      error: getErrorMessage(type)
    };
  }
  
  // Additional validation for numeric types
  if (type === 'number' || type === 'riskRating' || type === 'id') {
    if (isNaN(Number(value))) {
      return { isValid: false, error: 'Must be a valid number' };
    }
    
    // Check range for risk ratings (0-5)
    if (type === 'riskRating' && (value < 0 || value > 5)) {
      return { isValid: false, error: 'Rating must be between 0 and 5' };
    }
  }
  
  return { isValid: true };
}

/**
 * Validates an entire form object against a validation map
 * @param {Object} formData - The form data object
 * @param {Object} validationMap - Map of field names to validation types
 * @returns {Object} - Result object with isValid flag and errors object
 */
export function validateForm(formData, validationMap) {
  const errors = {};
  let isValid = true;
  
  for (const [field, validationType] of Object.entries(validationMap)) {
    const result = validateField(formData[field], validationType);
    if (!result.isValid) {
      errors[field] = result.error;
      isValid = false;
    }
  }
  
  return { isValid, errors };
}

/**
 * Sanitizes a string to prevent XSS attacks
 * @param {string} input - The string to sanitize
 * @returns {string} - The sanitized string
 */
export function sanitizeString(input) {
  if (input === null || input === undefined) {
    return '';
  }
  
  if (typeof input !== 'string') {
    input = String(input);
  }
  
  // Replace potentially dangerous characters
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
}

/**
 * Sanitizes an entire form object
 * @param {Object} formData - The form data to sanitize
 * @returns {Object} - Sanitized form data
 */
export function sanitizeForm(formData) {
  const sanitized = {};
  
  Object.entries(formData).forEach(([key, value]) => {
    // Skip null/undefined values
    if (value === null || value === undefined) {
      sanitized[key] = value;
      return;
    }
    
    // Sanitize strings
    if (typeof value === 'string') {
      sanitized[key] = sanitizeString(value);
    }
    // Handle numbers
    else if (typeof value === 'number') {
      sanitized[key] = value;
    }
    // Handle booleans
    else if (typeof value === 'boolean') {
      sanitized[key] = value;
    }
    // Handle objects (like nested form data)
    else if (typeof value === 'object') {
      if (Array.isArray(value)) {
        // Handle arrays
        sanitized[key] = value.map(item => 
          typeof item === 'string' ? sanitizeString(item) : item
        );
      } else {
        // Handle objects
        sanitized[key] = sanitizeForm(value);
      }
    } else {
      // Default case
      sanitized[key] = value;
    }
  });
  
  return sanitized;
}

/**
 * Returns a user-friendly error message for validation failures
 * @param {string} type - The validation type
 * @returns {string} - User-friendly error message
 */
function getErrorMessage(type) {
  switch (type) {
    case 'text':
      return 'Contains invalid characters or is too long';
    case 'longText':
      return 'Text is too long or contains invalid characters';
    case 'id':
      return 'Must be a valid numeric ID';
    case 'number':
      return 'Must be a valid number';
    case 'date':
      return 'Must be a valid date format (YYYY-MM-DD)';
    case 'criticality':
      return 'Must be Critical, High, Medium, or Low';
    case 'category':
      return 'Category contains invalid characters';
    case 'riskStatus':
      return 'Invalid risk status value';
    case 'riskPriority':
      return 'Priority must be High, Medium, or Low';
    case 'riskRating':
      return 'Rating must be between 0 and 5';
    case 'appetite':
      return 'Must be Yes or No';
    case 'riskResponseType':
      return 'Must be Accept, Mitigate, Transfer, or Avoid';
    default:
      return 'Invalid input';
  }
}

// Validation maps for different forms
export const RiskInstanceValidationMap = {
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
};

export const RiskRegisterValidationMap = {
  RiskId: 'id',
  ComplianceId: 'id',
  Category: 'category',
  Criticality: 'criticality',
  RiskType: 'text',
  RiskTitle: 'text'
};

// Adding these exports to maintain backward compatibility with existing components
export const riskFormValidationMap = {
  ComplianceId: 'id',
  Criticality: 'criticality',
  PossibleDamage: 'longText',
  Category: 'category',
  RiskDescription: 'longText',
  RiskLikelihood: 'riskRating',
  RiskImpact: 'riskRating',
  RiskExposureRating: 'number',
  RiskPriority: 'riskPriority',
  RiskMitigation: 'longText',
  RiskTitle: 'text',
  RiskType: 'text',
  BusinessImpact: 'longText'
};

export const riskInstanceFormValidationMap = {
  ...RiskInstanceValidationMap,
  IncidentId: 'id',
  RiskTitle: 'text',
  BusinessImpact: 'longText',
  Origin: 'text',
  ComplianceId: 'id',
  RiskType: 'text',
  RecurrenceCount: 'number'
}; 