"""
Framework validator module for validating framework-related inputs.
"""
import re
from datetime import date
from typing import Dict, Any, Union, Optional, List

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

def validate_string(value: Any, field_name: str, max_length: int = 255, 
                    allow_empty: bool = False, allowed_pattern: Optional[str] = None) -> str:
    """
    Validate a string value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed
        allowed_pattern: Optional regex pattern for allowed characters
        
    Returns:
        The validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_empty:
            return ""
        raise ValidationError(f"{field_name} cannot be None")
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    if not allow_empty and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}")
    
    if allowed_pattern and not re.match(allowed_pattern, value):
        raise ValidationError(f"{field_name} contains invalid characters")
    
    return value

def validate_date(value: Any, field_name: str, allow_none: bool = False) -> Optional[date]:
    """
    Validate a date value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        allow_none: Whether None is allowed
        
    Returns:
        The validated date or None
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{field_name} cannot be None")
    
    if isinstance(value, date):
        return value
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string in YYYY-MM-DD format")
    
    try:
        year, month, day = map(int, value.split('-'))
        return date(year, month, day)
    except (ValueError, AttributeError):
        raise ValidationError(f"{field_name} must be a valid date in YYYY-MM-DD format")

def validate_boolean_string(value: Any, field_name: str) -> str:
    """
    Validate a string that should be either 'true' or 'false'.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated string ('true' or 'false')
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    value_lower = value.lower()
    if value_lower not in ['true', 'false']:
        raise ValidationError(f"{field_name} must be either 'true' or 'false'")
    
    return value_lower

def validate_framework_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate query parameters for framework list endpoint.
    
    Args:
        params: The query parameters to validate
        
    Returns:
        Dict of validated parameters
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Validate include_all_status parameter if present
    if 'include_all_status' in params:
        validated['include_all_status'] = validate_boolean_string(
            params.get('include_all_status', 'false'),
            'include_all_status'
        ) == 'true'
    else:
        validated['include_all_status'] = False
    
    return validated

def validate_framework_post_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POST data for framework creation.
    
    Args:
        data: The data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Required fields
    validated['FrameworkName'] = validate_string(
        data.get('FrameworkName'), 
        'FrameworkName', 
        max_length=255, 
        allow_empty=False
    )
    
    # Optional fields with defaults
    validated['FrameworkDescription'] = validate_string(
        data.get('FrameworkDescription', ''), 
        'FrameworkDescription', 
        max_length=65535, 
        allow_empty=True
    )
    
    validated['Category'] = validate_string(
        data.get('Category', ''), 
        'Category', 
        max_length=100, 
        allow_empty=True
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        'DocURL', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        'Identifier', 
        max_length=45, 
        allow_empty=True
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        'StartDate', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        'EndDate', 
        allow_none=True
    )
    
    # Creator fields
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        'CreatedByName', 
        max_length=255, 
        allow_empty=True
    )
    
    # If CreatedByName is empty, try to get from the first policy
    if not validated['CreatedByName'] and 'policies' in data and isinstance(data['policies'], list) and len(data['policies']) > 0:
        validated['CreatedByName'] = validate_string(
            data['policies'][0].get('CreatedByName', ''),
            'CreatedByName from first policy',
            max_length=255,
            allow_empty=True
        )
    
    # Reviewer field
    validated['Reviewer'] = data.get('Reviewer')
    
    # If Reviewer is empty, try to get from the first policy
    if not validated['Reviewer'] and 'policies' in data and isinstance(data['policies'], list) and len(data['policies']) > 0:
        validated['Reviewer'] = data['policies'][0].get('Reviewer')
    
    # Validate policies if present
    if 'policies' in data:
        if not isinstance(data['policies'], list):
            raise ValidationError("Policies must be a list")
        
        validated_policies = []
        for i, policy_data in enumerate(data['policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"Policy at index {i} must be a JSON object")
            
            validated_policy = validate_policy_data(policy_data, i)
            validated_policies.append(validated_policy)
        
        validated['policies'] = validated_policies
    
    # Add additional fields needed for framework creation
    validated['CreatedByDate'] = date.today()
    validated['Status'] = 'Under Review'
    validated['ActiveInactive'] = 'InActive'
    validated['CurrentVersion'] = 1.0
    
    return validated

def validate_policy_data(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate policy data within a framework.
    
    Args:
        data: The policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['PolicyName'] = validate_string(
        data.get('PolicyName', ''), 
        f'PolicyName for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription', ''), 
        f'PolicyDescription for policy {index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        f'StartDate for policy {index}', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        f'EndDate for policy {index}', 
        allow_none=True
    )
    
    # Optional fields
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        f'Department for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Applicability'] = validate_string(
        data.get('Applicability', ''), 
        f'Applicability for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        f'DocURL for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope', ''), 
        f'Scope for policy {index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective', ''), 
        f'Objective for policy {index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for policy {index}', 
        max_length=45, 
        allow_empty=True
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for policy {index}', 
        max_length=45, 
        allow_empty=True
    )
    
    # Store reviewer ID for later lookup, but don't store directly in the validated data
    validated['ReviewerId'] = data.get('Reviewer')
    
    # For the actual Reviewer field, we'll set this to empty string initially
    # The actual name will be looked up and set in the framework_list function
    validated['Reviewer'] = ''
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is not None:
        try:
            validated['CoverageRate'] = float(coverage_rate)
        except (ValueError, TypeError):
            raise ValidationError(f"CoverageRate for policy {index} must be a valid number")
    else:
        validated['CoverageRate'] = None
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType', ''), 
        f'PolicyType for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory', ''), 
        f'PolicyCategory for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory', ''), 
        f'PolicySubCategory for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError(f"Subpolicies for policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_subpolicy_data(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    
    return validated

def validate_subpolicy_data(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data within a policy.
    
    Args:
        data: The subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName', ''), 
        f'SubPolicyName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=True
    )
    
    validated['Description'] = validate_string(
        data.get('Description', ''), 
        f'Description for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    # Optional fields with defaults
    validated['Status'] = 'Under Review'
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', 'Permanent'), 
        f'PermanentTemporary for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=50, 
        allow_empty=True
    )
    
    validated['Control'] = validate_string(
        data.get('Control', ''), 
        f'Control for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    # Set creation date to today
    validated['CreatedByDate'] = date.today()
    
    return validated

def validate_add_policy_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate request data for adding policies to a framework.
    
    Args:
        data: The request data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Check if the request has a 'policies' key
    if 'policies' in data:
        if not isinstance(data['policies'], list):
            raise ValidationError("'policies' must be a list")
        
        # Validate each policy in the list
        validated_policies = []
        for i, policy_data in enumerate(data['policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"Policy at index {i} must be a JSON object")
            
            validated_policy = validate_policy_for_add(policy_data, i)
            validated_policies.append(validated_policy)
        
        validated['policies'] = validated_policies
    else:
        # If no 'policies' key, check if the data itself is a policy
        if 'PolicyName' in data:
            validated_policy = validate_policy_for_add(data, 0)
            validated['policies'] = [validated_policy]
        else:
            raise ValidationError("Invalid request format. Expected 'policies' array or policy object")
    
    return validated

def validate_policy_for_add(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate policy data for adding to a framework.
    
    Args:
        data: The policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['PolicyName'] = validate_string(
        data.get('PolicyName', ''), 
        f'PolicyName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription', ''), 
        f'PolicyDescription for policy {index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        f'StartDate for policy {index}', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        f'EndDate for policy {index}', 
        allow_none=True
    )
    
    # Optional fields
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        f'Department for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['CreatedById'] = data.get('CreatedById')
    
    validated['Applicability'] = validate_string(
        data.get('Applicability', ''), 
        f'Applicability for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        f'DocURL for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope', ''), 
        f'Scope for policy {index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective', ''), 
        f'Objective for policy {index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for policy {index}', 
        max_length=45, 
        allow_empty=True
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for policy {index}', 
        max_length=45, 
        allow_empty=True
    )
    
    # Store reviewer ID for later lookup
    validated['Reviewer'] = data.get('Reviewer')
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is not None:
        try:
            validated['CoverageRate'] = float(coverage_rate)
        except (ValueError, TypeError):
            raise ValidationError(f"CoverageRate for policy {index} must be a valid number")
    else:
        validated['CoverageRate'] = None
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType', ''), 
        f'PolicyType for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory', ''), 
        f'PolicyCategory for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory', ''), 
        f'PolicySubCategory for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError(f"Subpolicies for policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_subpolicy_for_add(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    
    return validated

def validate_subpolicy_for_add(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data for adding to a policy.
    
    Args:
        data: The subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName', ''), 
        f'SubPolicyName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=True
    )
    
    validated['Description'] = validate_string(
        data.get('Description', ''), 
        f'Description for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    # Optional fields with defaults
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', 'Permanent'), 
        f'PermanentTemporary for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=50, 
        allow_empty=True
    )
    
    validated['Control'] = validate_string(
        data.get('Control', ''), 
        f'Control for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=True
    )
    
    return validated

def safe_isoformat(d: Optional[date]) -> Optional[str]:
    """
    Safely convert a date to ISO format string.
    
    Args:
        d: The date to convert
        
    Returns:
        ISO format string or None
    """
    return d.isoformat() if d else None 