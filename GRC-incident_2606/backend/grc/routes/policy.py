from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import Framework, Policy, SubPolicy, FrameworkVersion, PolicyVersion, PolicyApproval, Users, FrameworkApproval, ExportTask, PolicyCategory
from ..serializers import FrameworkSerializer, PolicySerializer, SubPolicySerializer, PolicyApprovalSerializer, UserSerializer   
from django.db import transaction
import traceback
import sys
from datetime import datetime, date, timedelta
from ..export_service import export_data, save_export_record, update_export_status, update_export_url, update_export_metadata
import re
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Case, When, Value, FloatField, F
from django.db.models.functions import Coalesce, Cast
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from django.utils.dateparse import parse_date
from ..utils import parse_date, safe_isoformat
from ..notification_service import NotificationService  # Add this import


# Framework CRUD operations

"""
@api GET /api/frameworks/
Returns all frameworks with Status='Approved' and ActiveInactive='Active'.
Filtered by the serializer to include only policies with Status='Approved' and ActiveInactive='Active',
and subpolicies with Status='Approved'.

@api POST /api/frameworks/
Creates a new framework with associated policies and subpolicies.
New frameworks are created with Status='Under Review' and ActiveInactive='Inactive' by default.
CurrentVersion defaults to 1.0 if not provided.

Example payload:
{
  "FrameworkName": "ISO 27001",
  "FrameworkDescription": "Information Security Management System",
  "EffectiveDate": "2023-10-01",
  "CreatedByName": "John Doe",
  "CreatedByDate": "2023-09-15",
  "Category": "Information Security and Compliance",
  "DocURL": "https://example.com/iso27001",
  "Identifier": "ISO-27001",
  "StartDate": "2023-10-01",
  "EndDate": "2025-10-01",
  "policies": [
    {
      "PolicyName": "Access Control Policy",
      "PolicyDescription": "Guidelines for access control management",
      "StartDate": "2023-10-01",
      "Department": "IT",
      "Applicability": "All Employees",
      "Scope": "All IT systems",
      "Objective": "Ensure proper access control",
      "Identifier": "ACP-001",
      "subpolicies": [
        {
          "SubPolicyName": "Password Management",
          "Identifier": "PWD-001",
          "Description": "Password requirements and management",
          "PermanentTemporary": "Permanent",
          "Control": "Use strong passwords with at least 12 characters"
        }
      ]
    }
  ]
}
"""

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def framework_list(request):
    if request.method == 'GET':
        try:
            # Import validators
            from ..validators.framework_validator import validate_framework_query_params, ValidationError
            
            # Validate query parameters
            try:
                validated_params = validate_framework_query_params(request.GET)
                include_all_status = validated_params['include_all_status']
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            if include_all_status:
                # For approval workflow, fetch all frameworks with Active status
                frameworks = Framework.objects.filter(ActiveInactive='InActive')
            else:
                # Default behavior - only approved and active frameworks
                frameworks = Framework.objects.filter(Status='Approved', ActiveInactive='Active')
            
            framework_data = []
            for framework in frameworks:
                framework_data.append({
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                    'CurrentVersion': framework.CurrentVersion,
                    'FrameworkDescription': framework.FrameworkDescription,
                    'CreatedByName': framework.CreatedByName,
                    'CreatedByDate': framework.CreatedByDate,
                    'Category': framework.Category,
                    'DocURL': framework.DocURL,
                    'Identifier': framework.Identifier,
                    'StartDate': framework.StartDate,
                    'EndDate': framework.EndDate,
                    'Status': framework.Status,
                    'ActiveInactive': framework.ActiveInactive,
                    'Reviewer': framework.Reviewer
                })
            return Response(framework_data)
        except Exception as e:
            print("Exception in framework_list GET:", str(e))
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
    elif request.method == 'POST':
        try:
            # Import validators
            from ..validators.framework_validator import validate_framework_post_data, ValidationError, safe_isoformat
            
            # Initialize notification service
            notification_service = NotificationService()
            
            # Validate request data
            try:
                validated_data = validate_framework_post_data(request.data)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get validated fields
            framework_data = {
                'FrameworkName': validated_data['FrameworkName'],
                'FrameworkDescription': validated_data['FrameworkDescription'],
                'CreatedByName': validated_data['CreatedByName'],
                'CreatedByDate': validated_data['CreatedByDate'],
                'Category': validated_data['Category'],
                'DocURL': validated_data['DocURL'],
                'Identifier': validated_data['Identifier'],
                'StartDate': validated_data['StartDate'],
                'EndDate': validated_data['EndDate'],
                'Status': validated_data['Status'],
                'ActiveInactive': validated_data['ActiveInactive'],
                'CurrentVersion': validated_data['CurrentVersion']
            }

            # Get reviewer information
            reviewer_id = validated_data['Reviewer']
            reviewer_email = None
            
            if reviewer_id:
                try:
                    reviewer = Users.objects.get(UserId=reviewer_id)
                    framework_data['Reviewer'] = reviewer.UserName
                    reviewer_email = reviewer.Email
                    print(f"Found reviewer email: {reviewer_email}")
                except Users.DoesNotExist:
                    print(f"Reviewer with ID {reviewer_id} not found")
                    framework_data['Reviewer'] = ''
            else:
                print("No reviewer ID provided")
                framework_data['Reviewer'] = ''

            with transaction.atomic():
                # Create framework
                framework = Framework.objects.create(**framework_data)
                
                # Create framework version
                framework_version = FrameworkVersion(
                    FrameworkId=framework,
                    Version=framework.CurrentVersion,
                    FrameworkName=framework.FrameworkName,
                    CreatedBy=framework.CreatedByName,
                    CreatedDate=date.today(),
                    PreviousVersionId=None
                )
                framework_version.save()
                
                # Process policies if present
                policies_data = []
                if 'policies' in validated_data:
                    for policy_data in validated_data['policies']:
                        # Look up reviewer name if reviewer ID is provided
                        policy_reviewer_name = ''
                        policy_reviewer_id = policy_data.get('ReviewerId')
                        if policy_reviewer_id:
                            try:
                                policy_reviewer = Users.objects.get(UserId=policy_reviewer_id)
                                policy_reviewer_name = policy_reviewer.UserName
                                print(f"Found policy reviewer: {policy_reviewer_name}")
                            except Users.DoesNotExist:
                                print(f"Policy reviewer with ID {policy_reviewer_id} not found")
                        
                        # Create policy
                        policy = Policy.objects.create(
                            FrameworkId=framework,
                            PolicyName=policy_data['PolicyName'],
                            PolicyDescription=policy_data['PolicyDescription'],
                            Status='Under Review',
                            StartDate=policy_data['StartDate'],
                            EndDate=policy_data['EndDate'],
                            Department=policy_data['Department'],
                            CreatedByName=policy_data['CreatedByName'],
                            CreatedByDate=date.today(),
                            Applicability=policy_data['Applicability'],
                            DocURL=policy_data['DocURL'],
                            Scope=policy_data['Scope'],
                            Objective=policy_data['Objective'],
                            Identifier=policy_data['Identifier'],
                            PermanentTemporary=policy_data['PermanentTemporary'],
                            ActiveInactive='InActive',
                            Reviewer=policy_reviewer_name,  # Store the reviewer name, not ID
                            CoverageRate=policy_data['CoverageRate'],
                            CurrentVersion=framework.CurrentVersion,
                            PolicyType=policy_data['PolicyType'],
                            PolicyCategory=policy_data['PolicyCategory'],
                            PolicySubCategory=policy_data['PolicySubCategory']
                        )

                        # Create policy version
                        policy_version = PolicyVersion(
                            PolicyId=policy,
                            Version=framework.CurrentVersion,
                            PolicyName=policy.PolicyName,
                            CreatedBy=policy.CreatedByName,
                            CreatedDate=date.today(),
                            PreviousVersionId=None
                        )
                        policy_version.save()
                        
                        # Process subpolicies if present
                        if 'subpolicies' in policy_data:
                            for subpolicy_data in policy_data['subpolicies']:
                                SubPolicy.objects.create(
                                    PolicyId=policy,
                                    SubPolicyName=subpolicy_data['SubPolicyName'],
                                    CreatedByName=subpolicy_data['CreatedByName'],
                                    CreatedByDate=subpolicy_data['CreatedByDate'],
                                    Identifier=subpolicy_data['Identifier'],
                                    Description=subpolicy_data['Description'],
                                    Status=subpolicy_data['Status'],
                                    PermanentTemporary=subpolicy_data['PermanentTemporary'],
                                    Control=subpolicy_data['Control']
                                )
                        
                        # Collect policy data for approval record
                        policy_dict = {
                            "PolicyId": policy.PolicyId,
                            "PolicyName": policy.PolicyName,
                            "PolicyDescription": policy.PolicyDescription,
                            "Status": policy.Status,
                            "StartDate": policy.StartDate.isoformat() if policy.StartDate else None,
                            "EndDate": policy.EndDate.isoformat() if policy.EndDate else None,
                            "Department": policy.Department,
                            "CreatedByName": policy.CreatedByName,
                            "CreatedByDate": policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                            "Applicability": policy.Applicability,
                            "DocURL": policy.DocURL,
                            "Scope": policy.Scope,
                            "Objective": policy.Objective,
                            "Identifier": policy.Identifier,
                            "PermanentTemporary": policy.PermanentTemporary,
                            "ActiveInactive": policy.ActiveInactive,
                            "Reviewer": policy.Reviewer,
                            "CoverageRate": policy.CoverageRate,
                            "CurrentVersion": policy.CurrentVersion,
                            "PolicyType": policy.PolicyType,
                            "PolicyCategory": policy.PolicyCategory,
                            "PolicySubCategory": policy.PolicySubCategory,
                            "subpolicies": []
                        }
                        
                        # Add subpolicies data
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        for subpolicy in subpolicies:
                            subpolicy_dict = {
                                "SubPolicyId": subpolicy.SubPolicyId,
                                "SubPolicyName": subpolicy.SubPolicyName,
                                "CreatedByName": subpolicy.CreatedByName,
                                "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
                                "Identifier": subpolicy.Identifier,
                                "Description": subpolicy.Description,
                                "Status": subpolicy.Status,
                                "PermanentTemporary": subpolicy.PermanentTemporary,
                                "Control": subpolicy.Control
                            }
                            policy_dict["subpolicies"].append(subpolicy_dict)
                        
                        policies_data.append(policy_dict)

                # Create framework approval record
                try:
                    # Get creator user ID
                    creator_user_id = request.data.get('CreatedById')
                    
                    if not creator_user_id and 'policies' in request.data and len(request.data['policies']) > 0:
                        creator_user_id = request.data['policies'][0].get('CreatedById')
                    
                    if not creator_user_id and framework_data['CreatedByName']:
                        try:
                            creator_user = Users.objects.get(UserName=framework_data['CreatedByName'])
                            creator_user_id = creator_user.UserId
                        except Users.DoesNotExist:
                            creator_user_id = 1  # Default to admin user
                    else:
                        creator_user_id = 1  # Default to admin user
                    
                    # Ensure creator_user_id is numeric
                    if isinstance(creator_user_id, str):
                        try:
                            creator_user_id = int(creator_user_id)
                        except (ValueError, TypeError):
                            creator_user_id = 1  # Default fallback
                    
                    # Ensure reviewer_id is numeric
                    if reviewer_id is None or reviewer_id == '':
                        reviewer_id = 2  # Default reviewer ID
                    elif isinstance(reviewer_id, str):
                        try:
                            reviewer_id = int(reviewer_id)
                        except (ValueError, TypeError):
                            reviewer_id = 2  # Default fallback
                    
                    # Create extracted data for approval
                    extracted_data = {
                        "FrameworkName": framework.FrameworkName,
                        "FrameworkDescription": framework.FrameworkDescription,
                        "Category": framework.Category,
                        "StartDate": safe_isoformat(framework.StartDate),
                        "EndDate": safe_isoformat(framework.EndDate),
                        "CreatedByName": framework.CreatedByName,
                        "CreatedByDate": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None,
                        "Identifier": framework.Identifier,
                        "Status": framework.Status,
                        "ActiveInactive": framework.ActiveInactive,
                        "type": "framework",
                        "docURL": framework.DocURL,
                        "reviewer": framework.Reviewer,
                        "source": "standard",
                        "policies": policies_data,
                        "totalPolicies": len(policies_data),
                        "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data)
                    }

                    # Create framework approval record
                    FrameworkApproval.objects.create(
                        FrameworkId=framework,
                        ExtractedData=extracted_data,
                        UserId=creator_user_id,
                        ReviewerId=reviewer_id,
                        Version="u1",
                        ApprovedNot=None
                    )

                    # Send notification to reviewer if email is available
                    if reviewer_email:
                        notification_data = {
                            'notification_type': 'frameworkSubmitted',
                            'email': reviewer_email,
                            'email_type': 'gmail',
                            'template_data': [
                                framework_data['Reviewer'],  # reviewer_name
                                framework.FrameworkName,  # framework_title
                                framework.CreatedByName,  # submitter_name
                            ]
                        }
                        notification_result = notification_service.send_multi_channel_notification(notification_data)
                        print(f"Notification result: {notification_result}")
                    else:
                        print("No reviewer email available to send notification")

                except Exception as approval_error:
                    print(f"Error creating framework approval: {str(approval_error)}")
                    traceback.print_exc()

                return Response({"message": "Framework created successfully", "FrameworkId": framework.FrameworkId}, status=status.HTTP_201_CREATED)
 
        except ValidationError as e:
            print(f"Validation error in framework_list POST: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Exception in framework_list POST:", str(e))
            traceback.print_exc()
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 
@api_view(['GET'])
@permission_classes([AllowAny])
def get_policies_by_framework(request, framework_id):
    """
    Get all policies for a specific framework
    """
    try:
        policies = Policy.objects.filter(FrameworkId=framework_id)
        serializer = PolicySerializer(policies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error retrieving policies', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['GET'])
@permission_classes([AllowAny])
def get_subpolicies_by_policy(request, policy_id):
    """
    Get all subpolicies for a specific policy
    """
    try:
        subpolicies = SubPolicy.objects.filter(PolicyId=policy_id)
        serializer = SubPolicySerializer(subpolicies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error retrieving subpolicies', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

"""
@api GET /api/frameworks/{pk}/
Returns a specific framework by ID if it has Status='Approved' and ActiveInactive='Active'.

@api PUT /api/frameworks/{pk}/
Updates an existing framework. Only frameworks with Status='Approved' and ActiveInactive='Active' can be updated.

Example payload:
{
  "FrameworkName": "ISO 27001:2022",
  "FrameworkDescription": "Updated Information Security Management System",
  "Category": "Information Security",
  "DocURL": "https://example.com/iso27001-2022",
  "EndDate": "2026-10-01"
}

@api DELETE /api/frameworks/{pk}/
Soft-deletes a framework by setting ActiveInactive='Inactive'.
Also marks all related policies as inactive and all related subpolicies with Status='Inactive'.
"""
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def framework_detail(request, pk):
    framework = get_object_or_404(Framework, FrameworkId=pk)
    
    if request.method == 'GET':
        # Only return details if framework is Approved and Active
        if framework.Status != 'Approved' or framework.ActiveInactive != 'Active':
            return Response({'error': 'Framework is not approved or active'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all active and approved policies for this framework
        policies = Policy.objects.filter(
            FrameworkId=framework,
            Status='Approved',
            ActiveInactive='Active'
        )
        
        # Get all subpolicies for these policies
        policy_data = []
        for policy in policies:
            policy_dict = {
                'PolicyId': policy.PolicyId,
                'PolicyName': policy.PolicyName,
                'PolicyDescription': policy.PolicyDescription,
                'CurrentVersion': policy.CurrentVersion,
                'StartDate': policy.StartDate,
                'EndDate': policy.EndDate,
                'Department': policy.Department,
                'CreatedByName': policy.CreatedByName,
                'CreatedByDate': policy.CreatedByDate,
                'Applicability': policy.Applicability,
                'DocURL': policy.DocURL,
                'Scope': policy.Scope,
                'Objective': policy.Objective,
                'Identifier': policy.Identifier,
                'PermanentTemporary': policy.PermanentTemporary,
                'subpolicies': []
            }
            
            # Get all subpolicies for this policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                subpolicy_dict = {
                    'SubPolicyId': subpolicy.SubPolicyId,
                    'SubPolicyName': subpolicy.SubPolicyName,
                    'CreatedByName': subpolicy.CreatedByName,
                    'CreatedByDate': subpolicy.CreatedByDate,
                    'Identifier': subpolicy.Identifier,
                    'Description': subpolicy.Description,
                    'Status': subpolicy.Status,
                    'PermanentTemporary': subpolicy.PermanentTemporary,
                    'Control': subpolicy.Control
                }
                policy_dict['subpolicies'].append(subpolicy_dict)
            
            policy_data.append(policy_dict)
        
        # Create response data
        response_data = {
            'FrameworkId': framework.FrameworkId,
            'FrameworkName': framework.FrameworkName,
            'CurrentVersion': framework.CurrentVersion,
            'FrameworkDescription': framework.FrameworkDescription,
            'EffectiveDate': framework.EffectiveDate,
            'CreatedByName': framework.CreatedByName,
            'CreatedByDate': framework.CreatedByDate,
            'Category': framework.Category,
            'DocURL': framework.DocURL,
            'Identifier': framework.Identifier,
            'StartDate': framework.StartDate,
            'EndDate': framework.EndDate,
            'Status': framework.Status,
            'ActiveInactive': framework.ActiveInactive,
            'policies': policy_data
        }
        
        return Response(response_data)
    
    elif request.method == 'PUT':
        # Check if framework is approved and active before allowing update
        if framework.Status != 'Approved' or framework.ActiveInactive != 'Active':
            return Response({'error': 'Only approved and active frameworks can be updated'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                serializer = FrameworkSerializer(framework, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'message': 'Framework updated successfully',
                        'FrameworkId': framework.FrameworkId,
                        'CurrentVersion': framework.CurrentVersion
                    })
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error updating framework', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            with transaction.atomic():
                # Instead of deleting, set ActiveInactive to 'Inactive'
                framework.ActiveInactive = 'Inactive'
                framework.save()
                
                # Set all related policies to inactive
                policies = Policy.objects.filter(FrameworkId=framework)
                for policy in policies:
                    policy.ActiveInactive = 'Inactive'
                    policy.save()
                    
                    # Update Status of subpolicies since they don't have ActiveInactive field
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    for subpolicy in subpolicies:
                        subpolicy.Status = 'Inactive'
                        subpolicy.save()
                
                return Response({'message': 'Framework and related policies marked as inactive'}, status=status.HTTP_200_OK)
        except Exception as e:
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error marking framework as inactive', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

# Policy CRUD operations

"""
@api GET /api/policies/{pk}/
Returns a specific policy by ID if it has Status='Approved' and ActiveInactive='Active',
and its parent framework has Status='Approved' and ActiveInactive='Active'.

@api PUT /api/policies/{pk}/
Updates an existing policy. Only policies with Status='Approved' and ActiveInactive='Active'
whose parent framework is also Approved and Active can be updated.

Example payload:
{
  "PolicyName": "Updated Access Control Policy",
  "PolicyDescription": "Enhanced guidelines for access control management with additional security measures",
  "StartDate": "2023-12-01",
  "EndDate": "2025-12-01",
  "Department": "IT,Security",
  "Scope": "All IT systems and cloud services",
  "Objective": "Ensure proper access control with improved security"
}

@api DELETE /api/policies/{pk}/
Soft-deletes a policy by setting ActiveInactive='Inactive'.
Also marks all related subpolicies with Status='Inactive'.
"""
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def policy_detail(request, pk):
    try:
        policy = Policy.objects.get(PolicyId=pk)
    except Policy.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Remove restrictions that were causing 403 errors
        # Previously only allowed if policy.Status == 'Approved' and policy.ActiveInactive == 'Active'
        serializer = PolicySerializer(policy)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Remove restrictions for updating
        # Previously only allowed if policy.Status == 'Approved' and policy.ActiveInactive == 'Active'
        try:
            with transaction.atomic():
                # Add status and ActiveInactive to request data
                update_data = request.data.copy()
                update_data['Status'] = 'Under Review'
                update_data['ActiveInactive'] = 'Inactive'
                
                serializer = PolicySerializer(policy, data=update_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'message': 'Policy updated successfully and set to Under Review',
                        'PolicyId': policy.PolicyId,
                        'CurrentVersion': policy.CurrentVersion,
                        'Status': 'Under Review',
                        'ActiveInactive': 'Inactive'
                    })
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error updating policy', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            with transaction.atomic():
                # Instead of deleting, set ActiveInactive to 'Inactive'
                original_status = policy.Status
                original_active = policy.ActiveInactive
                
                policy.Status = 'Inactive'  # Set both status and ActiveInactive to 'Inactive'
                policy.ActiveInactive = 'Inactive'
                policy.save()
                
                print(f"Updated policy {policy.PolicyId} status from {original_status} to Inactive and ActiveInactive from {original_active} to Inactive")
                
                # Update Status of subpolicies since they don't have ActiveInactive field
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                for subpolicy in subpolicies:
                    original_subpolicy_status = subpolicy.Status
                    subpolicy.Status = 'Inactive'
                    subpolicy.save()
                    print(f"Updated subpolicy {subpolicy.SubPolicyId} status from {original_subpolicy_status} to Inactive")
                
                # Create a policy approval record to track this change
                try:
                    # Find the latest policy approval for this policy
                    latest_approval = PolicyApproval.objects.filter(
                        PolicyId=policy.PolicyId
                    ).order_by('-ApprovalId').first()
                    
                    if latest_approval:
                        # Create a new approval with 'r' version to mark the inactivation
                        r_versions = []
                        for pa in PolicyApproval.objects.filter(Identifier=latest_approval.Identifier):
                            if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                                r_versions.append(int(pa.Version[1:]))
                        
                        if r_versions:
                            new_version = f"r{max(r_versions) + 1}"
                        else:
                            new_version = "r1"
                        
                        # Update the extracted data to reflect the status change
                        extracted_data = latest_approval.ExtractedData.copy() if hasattr(latest_approval.ExtractedData, 'copy') else latest_approval.ExtractedData
                        extracted_data['Status'] = 'Inactive'
                        
                        # Update subpolicies status in extracted data
                        if 'subpolicies' in extracted_data:
                            for sub in extracted_data['subpolicies']:
                                sub['Status'] = 'Inactive'
                        
                        # Create a new policy approval record
                        new_approval = PolicyApproval(
                            PolicyId=policy,
                            Identifier=latest_approval.Identifier,
                            ExtractedData=extracted_data,
                            UserId=latest_approval.UserId,
                            ReviewerId=latest_approval.ReviewerId,
                            ApprovedNot=1,  # Mark as approved since this is an admin action (1=True)
                            ApprovedDate=datetime.date.today(),
                            Version=new_version
                        )
                        new_approval.save()
                        print(f"Created inactivation record for policy {policy.PolicyId} with version {new_version}")
                except Exception as approval_err:
                    print(f"Error creating inactivation record: {str(approval_err)}")
                    # Continue even if approval record creation fails
                
                return Response({'message': 'Policy and related subpolicies marked as inactive'}, status=status.HTTP_200_OK)
        except Exception as e:
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error marking policy as inactive', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

"""
@api POST /api/frameworks/{framework_id}/policies/
Adds a new policy to an existing framework.
New policies are created with Status='Under Review' and ActiveInactive='Inactive' by default.
CurrentVersion defaults to 1.0 if not provided.

Example payload:
{
  "PolicyName": "Data Classification Policy",
  "PolicyDescription": "Guidelines for data classification and handling",
  "StartDate": "2023-10-01",
  "Department": "IT,Legal",
  "Applicability": "All Employees",
  "Scope": "All company data",
  "Objective": "Ensure proper data classification and handling",
  "Identifier": "DCP-001",
  "subpolicies": [
    {
      "SubPolicyName": "Confidential Data Handling",
      "Identifier": "CDH-001",
      "Description": "Guidelines for handling confidential data",
      "PermanentTemporary": "Permanent",
      "Control": "Encrypt all confidential data at rest and in transit"
    }
  ]
}
"""
@api_view(['POST'])
@permission_classes([AllowAny])
def add_policy_to_framework(request, framework_id):
    try:
        # Import validators
        from ..validators.framework_validator import validate_add_policy_request, ValidationError
        
        # Get framework
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
        except Framework.DoesNotExist:
            return Response({"error": f"Framework with ID {framework_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        notification_service = NotificationService()
        
        # Validate request data
        try:
            validated_data = validate_add_policy_request(request.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated policies data
        policies_data = validated_data['policies']
        
        # Initialize variables that are used later
        policy_ids = []
        policy_names = []
        submitter_name = None
        reviewer_name = None
        reviewer_email = None
        
        # Process each policy in the batch
        for policy_data in policies_data:
            print(f"Processing policy: {policy_data.get('PolicyName', 'unnamed')}")
            
            # Convert reviewer ID to name if provided
            policy_reviewer_name = ''
            policy_reviewer_id = policy_data.get('Reviewer')
            if policy_reviewer_id:
                try:
                    policy_reviewer = Users.objects.get(UserId=policy_reviewer_id)
                    policy_reviewer_name = policy_reviewer.UserName
                    print(f"Found policy reviewer: {policy_reviewer_name}")
                except Users.DoesNotExist:
                    print(f"Policy reviewer with ID {policy_reviewer_id} not found")
            
            # Create policy with category fields
            policy = Policy.objects.create(
                FrameworkId=framework,
                PolicyName=policy_data['PolicyName'],
                PolicyDescription=policy_data['PolicyDescription'],
                Status='Under Review',
                StartDate=policy_data['StartDate'],
                EndDate=policy_data['EndDate'],
                Department=policy_data['Department'],
                CreatedByName=policy_data['CreatedByName'],
                CreatedByDate=datetime.now().date(),
                Applicability=policy_data['Applicability'],
                DocURL=policy_data['DocURL'],
                Scope=policy_data['Scope'],
                Objective=policy_data['Objective'],
                Identifier=policy_data['Identifier'],
                PermanentTemporary=policy_data['PermanentTemporary'],
                ActiveInactive='InActive',
                Reviewer=policy_reviewer_name,  # Store the reviewer name, not ID
                CoverageRate=policy_data['CoverageRate'],
                CurrentVersion=framework.CurrentVersion,
                PolicyType=policy_data['PolicyType'],
                PolicyCategory=policy_data['PolicyCategory'],
                PolicySubCategory=policy_data['PolicySubCategory']
            )
            
            policy_ids.append(policy.PolicyId)
            policy_names.append(policy.PolicyName)
            
            if not submitter_name:
                submitter_name = policy_data.get('CreatedByName', '')
            
            # Create PolicyVersion record
            policy_version = PolicyVersion(
                PolicyId=policy,
                Version=framework.CurrentVersion,
                PolicyName=policy.PolicyName,
                CreatedBy=policy.CreatedByName,
                CreatedDate=date.today(),
                PreviousVersionId=None
            )
            policy_version.save()
            
            # Process subpolicies if they exist
            if 'subpolicies' in policy_data and isinstance(policy_data['subpolicies'], list):
                print(f"Processing {len(policy_data['subpolicies'])} subpolicies for policy {policy.PolicyName}")
                for subpolicy_data in policy_data['subpolicies']:
                    SubPolicy.objects.create(
                        PolicyId=policy,
                        SubPolicyName=subpolicy_data['SubPolicyName'],
                        CreatedByName=subpolicy_data['CreatedByName'],
                        CreatedByDate=datetime.now().date(),
                        Identifier=subpolicy_data['Identifier'],
                        Description=subpolicy_data['Description'],
                        Status='Under Review',
                        PermanentTemporary=subpolicy_data['PermanentTemporary'],
                        Control=subpolicy_data['Control']
                    )
            
            # Create policy approval record
            try:
                # Extract data for the approval
                user_id = policy_data.get('CreatedById', 1)  # Default to 1 if not provided
                reviewer_id = policy_data.get('Reviewer') if policy_data.get('Reviewer') else 2  # Default to 2
                
                # Get reviewer details
                if reviewer_id:
                    try:
                        reviewer_obj = Users.objects.get(UserId=reviewer_id)
                        reviewer_name = reviewer_obj.UserName
                        reviewer_email = reviewer_obj.Email
                        print(f"Found reviewer: {reviewer_name} with email: {reviewer_email}")
                    except Users.DoesNotExist:
                        print(f"Reviewer with ID {reviewer_id} not found")
                        reviewer_name = ''
                        reviewer_email = None
                else:
                    print("No reviewer ID provided")
                    reviewer_name = ''
                    reviewer_email = None
                
                # Get all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                subpolicies_data = []
                
                for subpolicy in subpolicies:
                    subpolicy_data = {
                        "SubPolicyId": subpolicy.SubPolicyId,
                        "SubPolicyName": subpolicy.SubPolicyName,
                        "CreatedByName": subpolicy.CreatedByName,
                        "CreatedByDate": subpolicy.CreatedByDate.isoformat() if hasattr(subpolicy.CreatedByDate, 'isoformat') else subpolicy.CreatedByDate,
                        "Identifier": subpolicy.Identifier,
                        "Description": subpolicy.Description,
                        "Status": subpolicy.Status,
                        "PermanentTemporary": subpolicy.PermanentTemporary,
                        "Control": subpolicy.Control
                    }
                    subpolicies_data.append(subpolicy_data)
                
                # Create extracted data JSON
                extracted_data = {
                    "PolicyName": policy.PolicyName,
                    "PolicyDescription": policy.PolicyDescription,
                    "Status": policy.Status,
                    "StartDate": policy.StartDate.isoformat() if hasattr(policy.StartDate, 'isoformat') else policy.StartDate,
                    "EndDate": policy.EndDate.isoformat() if hasattr(policy.EndDate, 'isoformat') else policy.EndDate,
                    "Department": policy.Department,
                    "CreatedByName": policy.CreatedByName,
                    "CreatedByDate": policy.CreatedByDate.isoformat() if hasattr(policy.CreatedByDate, 'isoformat') else policy.CreatedByDate,
                    "Applicability": policy.Applicability,
                    "Scope": policy.Scope,
                    "Objective": policy.Objective,
                    "Identifier": policy.Identifier,
                    "PolicyType": policy.PolicyType,
                    "PolicyCategory": policy.PolicyCategory,
                    "PolicySubCategory": policy.PolicySubCategory,
                    "type": "policy",
                    "subpolicies": subpolicies_data
                }
                
                # Create the policy approval
                PolicyApproval.objects.create(
                    PolicyId=policy,
                    ExtractedData=extracted_data,
                    UserId=user_id,
                    ReviewerId=reviewer_id,
                    Version="u1",  # Default initial version
                    ApprovedNot=None  # Not yet approved
                )
            except Exception as approval_error:
                print(f"Error creating policy approval: {str(approval_error)}")
                # Continue with policy creation even if approval creation fails
        
        # Send batch notification if more than one policy, else send single notification
        if reviewer_email:
            print(f"Attempting to send notification to reviewer email: {reviewer_email}")
            try:
                if len(policy_names) > 1:
                    policy_list_html = ''.join(f'<li>{name}</li>' for name in policy_names)
                    notification_data = {
                        'notification_type': 'policiesBatchSubmitted',
                        'email': reviewer_email,
                        'email_type': 'gmail',
                        'template_data': [
                            reviewer_name,
                            submitter_name,
                            policy_list_html
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                else:
                    notification_data = {
                        'notification_type': 'policySubmitted',
                        'email': reviewer_email,
                        'email_type': 'gmail',
                        'template_data': [
                            reviewer_name,
                            policy_names[0],
                            submitter_name,
                            date.today().strftime('%Y-%m-%d')
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
            except Exception as notification_error:
                print(f"Error sending notification: {str(notification_error)}")
        
        return Response({
            "message": f"{len(policy_ids)} policies added successfully to framework {framework_id}",
            "policy_ids": policy_ids
        }, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        print(f"Validation error in add_policy_to_framework: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print("Exception in add_policy_to_framework:", str(e))
        traceback.print_exc()
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_policy_approval(request, approval_id):
    try:
        # Get the original approval
        approval = PolicyApproval.objects.get(ApprovalId=approval_id)
       
        # Create a new approval object instead of updating
        new_approval = PolicyApproval()
        new_approval.Identifier = approval.Identifier
        new_approval.ExtractedData = request.data.get('ExtractedData', approval.ExtractedData)
        new_approval.UserId = approval.UserId
        new_approval.ReviewerId = approval.ReviewerId
        new_approval.ApprovedNot = request.data.get('ApprovedNot', approval.ApprovedNot)
        
        # If PolicyId exists in original approval, add it to new approval
        if hasattr(approval, 'PolicyId') and approval.PolicyId:
            new_approval.PolicyId = approval.PolicyId
       
        # Determine version prefix based on who made the change
        # For reviewers (assuming ReviewerId is the one making changes in this endpoint)
        prefix = 'r'
       
        # Get the latest version with this prefix for this identifier
        try:
            r_versions = []
            for pa in PolicyApproval.objects.filter(Identifier=approval.Identifier):
                if pa.Version and pa.Version.startswith(prefix) and len(pa.Version) > 1 and pa.Version[1:].isdigit():
                    r_versions.append(int(pa.Version[1:]))
            
            if r_versions:
                new_approval.Version = f"{prefix}{max(r_versions) + 1}"
            else:
                new_approval.Version = f"{prefix}1"
                
            print(f"Setting approval version to: {new_approval.Version} for Identifier: {approval.Identifier}")
        except Exception as e:
            print(f"Error determining version (using default {prefix}1): {str(e)}")
            new_approval.Version = f"{prefix}1"  # Default fallback
       
        new_approval.save()
       
        return Response({
            'message': 'Policy approval updated successfully',
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_approval.Version
        })
    except PolicyApproval.DoesNotExist:
        return Response({'error': 'Policy approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['PUT'])
@permission_classes([AllowAny])
def submit_policy_review(request, approval_id):
    try:
        # Get the original approval
        approval = PolicyApproval.objects.get(ApprovalId=approval_id)
       
        # Validate and prepare data
        extracted_data = request.data.get('ExtractedData')
        if not extracted_data:
            return Response({'error': 'ExtractedData is required'}, status=status.HTTP_400_BAD_REQUEST)
       
        approved_not = request.data.get('ApprovedNot')
        is_approved = approved_not == True or approved_not == 1
       
        # Get the latest version with "r" prefix for this identifier
        try:
            r_versions = []
            for pa in PolicyApproval.objects.filter(Identifier=approval.Identifier):
                if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                    r_versions.append(int(pa.Version[1:]))
           
            if r_versions:
                new_version = f"r{max(r_versions) + 1}"
            else:
                new_version = "r1"  # Default version for reviewer
                
            print(f"Setting review version to: {new_version} for Identifier: {approval.Identifier}")
        except Exception as version_err:
            print(f"Error determining version (using default r1): {str(version_err)}")
            new_version = "r1"  # Default fallback
       
        # Set approved date if policy is approved
        approved_date = None
        if is_approved:
            approved_date = datetime.date.today()
           
        # Create a new record using Django ORM
        new_approval = PolicyApproval(
            PolicyId=approval.PolicyId,
            Identifier=approval.Identifier,  # Make sure Identifier is included
            ExtractedData=extracted_data,
            UserId=approval.UserId,
            ReviewerId=approval.ReviewerId,
            ApprovedNot=approved_not,
            ApprovedDate=approved_date,  # Set approved date
            Version=new_version
        )
        new_approval.save()
        print(f"Created new policy approval with ID: {new_approval.ApprovalId}, Version: {new_version}")
       
        # Update the policy status based on the approval decision
        try:
            # Get the policy directly from the approval
            policy = approval.PolicyId
            
            if not policy:
                print("Warning: Policy not found in approval, cannot update status")
                raise Exception("Policy not found in approval")

            print(f"Working with policy ID: {policy.PolicyId}, current status: {policy.Status}")

            # Get the policy version record if needed
            policy_version = None
            if is_approved:
                policy_version = PolicyVersion.objects.filter(
                    PolicyId=policy,
                    Version=policy.CurrentVersion
                ).first()

            # If approved and this policy has a previous version, set it to inactive
            if is_approved and policy_version and policy_version.PreviousVersionId:
                try:
                    previous_version = PolicyVersion.objects.get(VersionId=policy_version.PreviousVersionId)
                    previous_policy = previous_version.PolicyId
                    previous_policy.ActiveInactive = 'Inactive'
                    previous_policy.save()
                    print(f"Set previous policy version {previous_policy.PolicyId} to Inactive")
                except Exception as prev_error:
                    print(f"Error updating previous policy version: {str(prev_error)}")
               
            # Update policy status based on approval decision
            if is_approved:
                # If approved, set to Approved and Active regardless of current status
                policy.Status = 'Approved'
                policy.ActiveInactive = 'Active'  # Set to Active when approved
                
                                # Deactivate all previous versions when policy is approved
                print(f"Current policy being approved: PolicyId={policy.PolicyId}, Version={policy.CurrentVersion}, Identifier={policy.Identifier}")
                deactivated_count = deactivate_previous_policy_versions(policy)
                
                print(f"Successfully deactivated {deactivated_count} previous policy versions")
                
                # Ensure CurrentVersion is set correctly
                # Get the current policy version from PolicyVersion table
                current_policy_version = PolicyVersion.objects.filter(
                    PolicyId=policy
                ).first()
                
                if current_policy_version:
                    print(f"Setting CurrentVersion to {current_policy_version.Version} for policy {policy.PolicyId}")
                    policy.CurrentVersion = current_policy_version.Version
                
                policy.save()
                print(f"Updated policy {policy.PolicyId} status to Approved and Active")
                
                # Update all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                for subpolicy in subpolicies:
                    # Update all subpolicies to match the policy status
                    subpolicy.Status = 'Approved'
                    subpolicy.save()
                    print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Approved")
            else:
                # If rejected, update policy status to Rejected
                policy.Status = 'Rejected'
                policy.save()
                print(f"Updated policy {policy.PolicyId} status to Rejected")
                
                # Also update all subpolicies to Rejected
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                for subpolicy in subpolicies:
                    subpolicy.Status = 'Rejected'
                    subpolicy.save()
                    print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Rejected")
            
        except Exception as update_error:
            print(f"Error updating policy/subpolicy status: {str(update_error)}")
            import traceback
            traceback.print_exc()
            # Continue with the response even if status update fails
       
        # Send notification to submitter about approval or rejection
        try:
            from ..notification_service import NotificationService
            notification_service = NotificationService()
            submitter = Users.objects.get(UserId=new_approval.UserId)
            reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
            now_str = date.today().isoformat()
            if is_approved:
                notification_data = {
                    'notification_type': 'policyApproved',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        now_str
                    ]
                }
            else:
                rejection_reason = request.data.get('rejection_reason', '') or 'Policy was rejected'
                notification_data = {
                    'notification_type': 'policyRejected',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        rejection_reason
                    ]
                }
            notification_service.send_multi_channel_notification(notification_data)
        except Exception as notify_ex:
            print(f"DEBUG: Error sending policy approval/rejection notification: {notify_ex}")
        
        return Response({
            'message': f"Policy review submitted successfully. Policy {is_approved and 'approved' or 'rejected'}.",
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_version,
            'ApprovedDate': approved_date.isoformat() if approved_date else None,
            'Status': is_approved and 'Approved' or 'Rejected'
        })
    
    except PolicyApproval.DoesNotExist:
        return Response({'error': 'Policy approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Error in submit_policy_review:", str(e))
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def add_subpolicy_to_policy(request, policy_id):
    policy = get_object_or_404(Policy, PolicyId=policy_id)
   
    try:
        with transaction.atomic():
            # Set policy ID and default values in the request data
            subpolicy_data = request.data.copy()
            subpolicy_data['PolicyId'] = policy.PolicyId
            if 'CreatedByName' not in subpolicy_data:
                subpolicy_data['CreatedByName'] = policy.CreatedByName
            if 'CreatedByDate' not in subpolicy_data:
                subpolicy_data['CreatedByDate'] = date.today()
            if 'Status' not in subpolicy_data:
                subpolicy_data['Status'] = 'Under Review'
           
            subpolicy_serializer = SubPolicySerializer(data=subpolicy_data)
            if not subpolicy_serializer.is_valid():
                return Response(subpolicy_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
            subpolicy = subpolicy_serializer.save()
           
            return Response({
                'message': 'Subpolicy added to policy successfully',
                'SubPolicyId': subpolicy.SubPolicyId,
                'PolicyId': policy.PolicyId
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error adding subpolicy to policy', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
 

"""
@api GET /api/subpolicies/{pk}/
Returns a specific subpolicy by ID if it has Status='Approved',
its parent policy has Status='Approved' and ActiveInactive='Active',
and its parent framework has Status='Approved' and ActiveInactive='Active'.

@api PUT /api/subpolicies/{pk}/
Updates an existing subpolicy. Only subpolicies with Status='Approved'
whose parent policy and framework are also Approved and Active can be updated.

Example payload:
{
  "SubPolicyName": "Enhanced Password Management",
  "Description": "Updated password requirements and management",
  "Control": "Use strong passwords with at least 16 characters, including special characters",
  "Identifier": "PWD-002",
}

@api DELETE /api/subpolicies/{pk}/
Soft-deletes a subpolicy by setting Status='Inactive'.
"""
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def subpolicy_detail(request, pk):
    """
    Retrieve, update or delete a subpolicy.
    """
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
    except SubPolicy.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Remove any restrictions that might cause 403 errors
        serializer = SubPolicySerializer(subpolicy)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Remove any restrictions for updating
        serializer = SubPolicySerializer(subpolicy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Instead of hard deleting, set Status to Inactive
        try:
            subpolicy.Status = 'Inactive'
            subpolicy.save()
            return Response({'message': 'Subpolicy marked as inactive'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([AllowAny])
def submit_subpolicy_review(request, pk):
    """
    Submit a review for a subpolicy
    """
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
    except SubPolicy.DoesNotExist:
        return Response({'error': 'Subpolicy not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update status based on review submission
    status_value = request.data.get('Status')
    remarks = request.data.get('remarks', '')
    
    if not status_value:
        return Response({'error': 'Status value is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    print(f"Updating subpolicy {pk} status to: {status_value}")
    
    # Update the subpolicy status
    subpolicy.Status = status_value
    subpolicy.save()
    print(f"Subpolicy {pk} status updated to {status_value}")
    
    # Get the parent policy
    policy = subpolicy.PolicyId
    if not policy:
        return Response({'error': 'Parent policy not found'}, status=status.HTTP_404_NOT_FOUND)
    
    print(f"Parent policy ID: {policy.PolicyId}, current status: {policy.Status}")
    
    # Update policy status based on all subpolicies
    update_policy_status_from_subpolicies(policy.PolicyId)
    
    # Refresh policy to get updated status
    policy.refresh_from_db()
    
    # Prepare response data with updated policy status
    response_data = {
        'message': 'Subpolicy review submitted successfully',
        'SubPolicyId': pk,
        'Status': status_value,
        'PolicyUpdated': True,
        'PolicyStatus': policy.Status
    }
    
    # Create policy approval record if this is an approval and policy is now approved
    if status_value == 'Approved' and policy.Status == 'Approved':
        try:
            # Find the latest policy approval for this policy
            latest_approval = PolicyApproval.objects.filter(
                PolicyId=policy.PolicyId
            ).order_by('-ApprovalId').first()
            
            if latest_approval:
                # Create a new approval with 'r' version
                r_versions = []
                for pa in PolicyApproval.objects.filter(PolicyId=policy.PolicyId):
                    if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                        r_versions.append(int(pa.Version[1:]))
                
                if r_versions:
                    new_version = f"r{max(r_versions) + 1}"
                else:
                    new_version = "r1"
                
                # Create a new policy approval record
                new_approval = PolicyApproval(
                    PolicyId=policy,
                    ExtractedData=latest_approval.ExtractedData,
                    UserId=latest_approval.UserId,
                    ReviewerId=latest_approval.ReviewerId,
                    ApprovedNot=1,  # Mark as approved (1=True)
                    ApprovedDate=datetime.date.today(),
                    Version=new_version
                )
                new_approval.save()
                print(f"Created auto-approval for policy {policy.PolicyId} with version {new_version}")
        except Exception as approval_err:
            print(f"Error creating policy approval: {str(approval_err)}")
            import traceback
            traceback.print_exc()
    
    # Send notification to reviewer about subpolicy resubmission
    try:
        from ..notification_service import NotificationService
        notification_service = NotificationService()
        reviewer = None
        submitter = None
        if new_approval.ReviewerId:
            reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
        if new_approval.UserId:
            submitter = Users.objects.get(UserId=new_approval.UserId)
        if reviewer and reviewer.Email:
            notification_data = {
                'notification_type': 'subpolicyResubmitted',
                'email': reviewer.Email,
                'email_type': 'gmail',
                'template_data': [
                    reviewer.UserName,
                    subpolicy.SubPolicyName,
                    submitter.UserName if submitter else ''
                ]
            }
            notification_service.send_multi_channel_notification(notification_data)
    except Exception as notify_ex:
        print(f"DEBUG: Error sending subpolicy resubmission notification: {notify_ex}")
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([AllowAny])
def resubmit_subpolicy(request, pk):
    """
    Resubmit a rejected subpolicy with changes
    """
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
        policy_id = subpolicy.PolicyId.PolicyId
        
        print(f"Resubmitting subpolicy {pk} for policy {policy_id}")

        # Get all versions for this policy to find the latest u version
        policy_approvals = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version')

        # Find the latest u version - use Python filtering instead of query filtering
        u_versions = [pa.Version for pa in policy_approvals if pa.Version and pa.Version.startswith('u')]
        new_version = 'u1'

        if u_versions:
            # Get the highest u version number
            latest_u_num = max([int(v[1:]) for v in u_versions if v[1:].isdigit()])
            new_version = f'u{latest_u_num + 1}'
            
        print(f"Setting new version to {new_version} for policy {policy_id}")

        # Update subpolicy with new data
        data = request.data.copy()
        
        if 'Description' in data:
            subpolicy.Description = data['Description']
        
        if 'Control' in data:
            subpolicy.Control = data['Control']
        
        # Set status back to Under Review
        original_status = subpolicy.Status
        subpolicy.Status = 'Under Review'
        
        # Save the changes
        subpolicy.save()
        print(f"Updated subpolicy {pk} status from {original_status} to Under Review")

        # Get the policy
        policy = Policy.objects.get(PolicyId=policy_id)
        original_policy_status = policy.Status
        
        # Update policy status if needed
        if policy.Status != 'Under Review':
            policy.Status = 'Under Review'
            policy.save()
            print(f"Updated policy {policy_id} status from {original_policy_status} to Under Review")

        # Create new policy approval with incremented u version
        # Get the latest policy approval to copy its data
        latest_approval = policy_approvals.first()
        if latest_approval:
            extracted_data = latest_approval.ExtractedData.copy() if hasattr(latest_approval.ExtractedData, 'copy') else latest_approval.ExtractedData
            
            # Update the specific subpolicy in extracted data
            if 'subpolicies' in extracted_data:
                subpolicy_updated = False
                for sub in extracted_data['subpolicies']:
                    if sub.get('SubPolicyId') == pk:
                        sub['Description'] = subpolicy.Description
                        sub['Control'] = subpolicy.Control
                        sub['Status'] = 'Under Review'
                        # Reset approval info if present
                        if 'approval' in sub:
                            sub['approval'] = {
                                'approved': None,
                                'remarks': ''
                            }
                        subpolicy_updated = True
                        break
                
                if not subpolicy_updated:
                    print(f"Warning: Subpolicy {pk} not found in extracted data")

            # Create new policy approval
            new_approval = PolicyApproval(
                PolicyId=policy,
                Identifier=latest_approval.Identifier,
                ExtractedData=extracted_data,
                UserId=latest_approval.UserId,
                ReviewerId=latest_approval.ReviewerId,
                ApprovedNot=None,
                Version=new_version
            )
            new_approval.save()
            print(f"Created new policy approval with ID: {new_approval.ApprovalId}, Version: {new_version}")

            # Send notification to reviewer about subpolicy resubmission
            try:
                from ..notification_service import NotificationService
                notification_service = NotificationService()
                reviewer = None
                submitter = None
                if new_approval.ReviewerId:
                    reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
                if new_approval.UserId:
                    submitter = Users.objects.get(UserId=new_approval.UserId)
                if reviewer and reviewer.Email:
                    notification_data = {
                        'notification_type': 'subpolicyResubmitted',
                        'email': reviewer.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            reviewer.UserName,
                            subpolicy.SubPolicyName,
                            submitter.UserName if submitter else ''
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
            except Exception as notify_ex:
                print(f"DEBUG: Error sending subpolicy resubmission notification: {notify_ex}")

        return Response({
            'message': 'Subpolicy resubmitted successfully',
            'SubPolicyId': pk,
            'Status': 'Under Review',
            'version': new_version
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error resubmitting subpolicy: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_version(request, policy_id):
    """
    Get the latest version of a policy from the policy approvals table
    """
    try:
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Instead of getting the attribute, find the latest approval version from the database
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version').first()
        
        # Extract the latest version from policy approvals
        if latest_approval and latest_approval.Version:
            # If version starts with 'u', return it
            if latest_approval.Version.startswith('u'):
                version = latest_approval.Version
            else:
                # Check if there are any user versions (u1, u2, etc.)
                user_approvals = PolicyApproval.objects.filter(
                    PolicyId=policy_id,
                    Version__startswith='u'
                ).order_by('-Version')
                
                if user_approvals.exists():
                    version = user_approvals.first().Version
                else:
                    version = 'u1'  # Default if no user versions found
        else:
            # If no approvals found, default to u1
            version = 'u1'
        
        print(f"Latest version for policy {policy_id}: {version}")
        
        return Response({
            'policy_id': policy_id,
            'version': version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error getting policy version: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_subpolicy_version(request, subpolicy_id):
    """
    Get the latest version of a subpolicy from policy approvals
    """
    try:
        subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
        policy_id = subpolicy.PolicyId.PolicyId if subpolicy.PolicyId else None
        
        if not policy_id:
            return Response({
                'subpolicy_id': subpolicy_id,
                'version': 'u1',
                'error': 'No parent policy found'
            }, status=status.HTTP_200_OK)
        
        # Find the latest policy approval with this subpolicy
        latest_version = 'u1'  # Default version
        
        try:
            # Get all policy approvals for the parent policy
            policy_approvals = PolicyApproval.objects.filter(
                PolicyId=policy_id
            ).order_by('-Version')
            
            # Look through policy approvals for this subpolicy
            for approval in policy_approvals:
                if not approval.ExtractedData or 'subpolicies' not in approval.ExtractedData:
                    continue
                
                # Find this subpolicy in the extracted data
                for sub in approval.ExtractedData['subpolicies']:
                    if sub.get('SubPolicyId') == subpolicy_id:
                        # Found a reference to this subpolicy
                        if approval.Version and approval.Version.startswith('u'):
                            latest_version = approval.Version
                            # We found a user version, return it
                            print(f"Found version {latest_version} for subpolicy {subpolicy_id}")
                            return Response({
                                'subpolicy_id': subpolicy_id,
                                'version': latest_version
                            }, status=status.HTTP_200_OK)
            
            # If we got here and didn't find a user version, check the subpolicy object
            stored_version = getattr(subpolicy, 'version', None)
            if stored_version and stored_version.startswith('u'):
                latest_version = stored_version
        except Exception as inner_error:
            print(f"Error finding version in approvals: {str(inner_error)}")
            # Continue with default version
        
        print(f"Latest version for subpolicy {subpolicy_id}: {latest_version}")
        
        return Response({
            'subpolicy_id': subpolicy_id,
            'version': latest_version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error getting subpolicy version: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_policy_approval(request, policy_id):
    """
    Get the latest policy approval for a policy
    """
    try:
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version').first()
        
        if not latest_approval:
            return Response({'error': 'No approval found for this policy'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PolicyApprovalSerializer(latest_approval)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_policy_approval_by_role(request, policy_id, role):
    """
    Get the latest policy approval for a policy by role (reviewer/user)
    """
    try:
        # Filter by role - simplistic approach, you might need more complex logic
        if role == 'reviewer':
            latest_approval = PolicyApproval.objects.filter(
                PolicyId=policy_id,
                IsReviewer=True
            ).order_by('-Version').first()
        else:  # user role
            latest_approval = PolicyApproval.objects.filter(
                PolicyId=policy_id,
                IsReviewer=False
            ).order_by('-Version').first()
        
        if not latest_approval:
            return Response({'error': f'No {role} approval found for this policy'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PolicyApprovalSerializer(latest_approval)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_reviewer_version(request, policy_id=None, subpolicy_id=None):
    """
    Get the latest reviewer version (R1, R2, etc.) for a policy or subpolicy
    and return the complete policy approval data for that version
    """
    try:
        latest_r_version = 'R1'  # Default if no reviewer versions found
        policy_approval_data = None
        
        if policy_id:
            # Find the latest R version for a policy
            policy = get_object_or_404(Policy, PolicyId=policy_id)
            
            # Use Python filtering instead of MySQL regex to avoid character set issues
            r_approvals = []
            all_approvals = PolicyApproval.objects.filter(PolicyId=policy_id).order_by('-Version')
            
            for approval in all_approvals:
                if approval.Version and approval.Version.startswith('R'):
                    r_approvals.append(approval)
            
            if r_approvals:
                # Get the latest policy approval with R version
                latest_approval = r_approvals[0]
                latest_r_version = latest_approval.Version
                print(f"Found latest R version for policy {policy_id}: {latest_r_version}")
                
                # Serialize the policy approval data
                serializer = PolicyApprovalSerializer(latest_approval)
                policy_approval_data = serializer.data
        
        elif subpolicy_id:
            # Find the latest R version for a subpolicy
            subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
            policy_id = subpolicy.PolicyId.PolicyId if subpolicy.PolicyId else None
            
            if policy_id:
                # Use Python filtering instead of MySQL regex
                r_approvals = []
                all_approvals = PolicyApproval.objects.filter(PolicyId=policy_id).order_by('-Version')
                
                for approval in all_approvals:
                    if approval.Version and approval.Version.startswith('R'):
                        r_approvals.append(approval)
                
                if r_approvals:
                    # Get the latest policy approval
                    latest_approval = r_approvals[0]
                    latest_r_version = latest_approval.Version
                    
                    # Serialize the policy approval data
                    serializer = PolicyApprovalSerializer(latest_approval)
                    policy_approval_data = serializer.data
                    
                    print(f"Found latest R version for subpolicy {subpolicy_id}: {latest_r_version} in policy {policy_id}")
        
        # If we have policy approval data, return it along with the version
        if policy_approval_data:
            return Response({
                'policy_id': policy_id,
                'subpolicy_id': subpolicy_id,
                'version': latest_r_version,
                'approval_data': policy_approval_data
            }, status=status.HTTP_200_OK)
        else:
            # If no approval data found, just return the version
            return Response({
                'policy_id': policy_id,
                'subpolicy_id': subpolicy_id,
                'version': latest_r_version,
                'approval_data': None
            }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error getting latest reviewer version: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_policy_approval_review(request, policy_id):
    """
    Submit a review for a policy approval
    """
    try:
        data = request.data
        policy = Policy.objects.get(PolicyId=policy_id)
        
        # Extract necessary data
        extracted_data = data.get('ExtractedData', {})
        user_id = data.get('UserId', 1)
        reviewer_id = data.get('ReviewerId', 2)
        
        # Get approval status from request
        approved = data.get('approved', False)
        
        # Check if Status is provided in the ExtractedData
        if extracted_data and 'Status' in extracted_data:
            status_from_json = extracted_data.get('Status')
            # Set ApprovedNot based on Status
            if status_from_json == 'Approved':
                approved_not = 1  # Approved
                is_approved = True
            elif status_from_json == 'Rejected':
                approved_not = 0  # Rejected
                is_approved = False
            else:
                # Use value from request if no matching status
                approved_not = 1 if approved else 0
                is_approved = approved
        else:
            # Use value from request if no Status in ExtractedData
            approved_not = 1 if approved else 0
            is_approved = approved
        
        # Set approved date to today
        approved_date = date.today()
        
        # Determine next version
        policy_approvals = PolicyApproval.objects.filter(
            PolicyId=policy
        ).order_by('-Version')
        
        # Find latest reviewer version
        r_versions = [pa.Version for pa in policy_approvals if pa.Version and pa.Version.startswith('r')]
        new_version = 'r1'
        
        if r_versions:
            try:
                latest_r_num = max([int(v[1:]) for v in r_versions if v[1:].isdigit()])
                new_version = f'r{latest_r_num + 1}'
            except (ValueError, Exception):
                new_version = 'r2'
        
        # Add review details to extracted_data
        if 'policy_approval' not in extracted_data:
            extracted_data['policy_approval'] = {}
            
        extracted_data['policy_approval'].update({
            'approved': approved,
            'remarks': data.get('remarks', ''),
            'reviewer_id': reviewer_id,
            'reviewed_date': approved_date.isoformat()
        })
        
        # Create new policy approval with incremented version
        new_approval = PolicyApproval(
            PolicyId=policy,
            ExtractedData=extracted_data,
            UserId=user_id,
            ReviewerId=reviewer_id,
            ApprovedNot=approved_not,
            ApprovedDate=approved_date,
            Version=new_version
        )
        new_approval.save()
        
        # Initial update of policy status based on review decision
        initial_status = 'Approved' if approved else 'Rejected'
        policy.Status = initial_status
        
        # Update ActiveInactive status for approved policies
        if initial_status == 'Approved':
            policy.ActiveInactive = 'Active'
            
            # Enhanced logic to deactivate previous versions
            print(f"DEBUG: Current policy being approved: PolicyId={policy.PolicyId}, Version={policy.CurrentVersion}, Identifier={policy.Identifier}")
            
            # Method 1: Find by Identifier
            previous_policies_by_identifier = Policy.objects.filter(
                Identifier=policy.Identifier
            ).exclude(
                PolicyId=policy.PolicyId
            )
            
            print(f"DEBUG: Found {previous_policies_by_identifier.count()} previous versions by Identifier: {policy.Identifier}")
            
            # Method 2: Find through PolicyVersion relationships
            previous_policies_by_version = []
            try:
                # Get current policy's version record
                current_policy_version = PolicyVersion.objects.filter(PolicyId=policy).first()
                if current_policy_version:
                    # Find all other policies with versions that have the same base identifier pattern
                    version_pattern = current_policy_version.Version
                    if '.' in version_pattern:
                        major_version = version_pattern.split('.')[0]
                        related_versions = PolicyVersion.objects.filter(
                            Version__startswith=major_version + '.'
                        ).exclude(PolicyId=policy)
                        
                        for version_record in related_versions:
                            if version_record.PolicyId and version_record.PolicyId.Identifier == policy.Identifier:
                                previous_policies_by_version.append(version_record.PolicyId)
                        
                        print(f"DEBUG: Found {len(previous_policies_by_version)} previous versions through PolicyVersion table")
            except Exception as version_err:
                print(f"DEBUG: Error finding related versions: {str(version_err)}")
            
            # Combine and deduplicate all previous policies
            all_previous_policies = set()
            for p in previous_policies_by_identifier:
                all_previous_policies.add(p)
            for p in previous_policies_by_version:
                all_previous_policies.add(p)
            
            all_previous_policies = list(all_previous_policies)
            
            print(f"DEBUG: Total unique previous policies to deactivate: {len(all_previous_policies)}")
            
            # Additional debug info
            if all_previous_policies:
                policy_ids = [p.PolicyId for p in all_previous_policies]
                policy_versions_info = [(p.PolicyId, p.CurrentVersion, p.Status, p.ActiveInactive) for p in all_previous_policies]
                print(f"DEBUG: Previous policy IDs to deactivate: {policy_ids}")
                print(f"DEBUG: Previous policies details: {policy_versions_info}")
            
            # Deactivate all previous versions
            deactivated_count = 0
            for prev_policy in all_previous_policies:
                if prev_policy.ActiveInactive == 'Active':  # Only deactivate if currently active
                    print(f"DEBUG: Processing previous policy: PolicyId={prev_policy.PolicyId}, CurrentVersion={prev_policy.CurrentVersion}, Status={prev_policy.Status}, ActiveInactive={prev_policy.ActiveInactive}")
                    
                    # Set ActiveInactive to 'Inactive'
                    prev_policy.ActiveInactive = 'Inactive'
                    # Keep the Status as 'Approved' if it was already approved
                    if prev_policy.Status == 'Approved':
                        print(f"DEBUG: Keeping Status 'Approved' for policy {prev_policy.PolicyId}")
                    print(f"DEBUG: Setting policy {prev_policy.PolicyId} to Inactive (Status remains {prev_policy.Status})")
                    prev_policy.save()
                    deactivated_count += 1
                    
                    # Verify the save worked
                    updated_policy = Policy.objects.get(PolicyId=prev_policy.PolicyId)
                    print(f"DEBUG: Verified policy {prev_policy.PolicyId} after save: ActiveInactive={updated_policy.ActiveInactive}")
                else:
                    print(f"DEBUG: Skipping policy {prev_policy.PolicyId} - already inactive")
            
            print(f"DEBUG: Successfully deactivated {deactivated_count} previous policy versions")
            
        policy.save()
        print(f"DEBUG: Initial policy status set to {initial_status}")
        
        # Check subpolicy statuses to ensure policy status is consistent
        # If any subpolicy is rejected, the policy will be marked as rejected
        update_policy_status_from_subpolicies(policy_id)
        
        # Refresh policy object to get the updated status after subpolicy check
        policy.refresh_from_db()
        
        # Update subpolicies if policy is approved (only if there are no rejected subpolicies)
        if approved and policy.Status == 'Approved':
            SubPolicy.objects.filter(PolicyId=policy.PolicyId, Status='Under Review').update(Status='Approved')
        
        # Send notification to submitter about approval or rejection
        try:
            from ..notification_service import NotificationService
            notification_service = NotificationService()
            submitter = Users.objects.get(UserId=new_approval.UserId)
            reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
            now_str = date.today().isoformat()
            if is_approved:
                notification_data = {
                    'notification_type': 'policyApproved',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        now_str
                    ]
                }
            else:
                rejection_reason = request.data.get('rejection_reason', '') or 'Policy was rejected'
                notification_data = {
                    'notification_type': 'policyRejected',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        rejection_reason
                    ]
                }
            notification_service.send_multi_channel_notification(notification_data)
        except Exception as notify_ex:
            print(f"DEBUG: Error sending policy approval/rejection notification: {notify_ex}")
        
        return Response({
            'message': 'Policy review submitted successfully',
            'PolicyId': policy.PolicyId,
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_version,
            'Status': policy.Status,
            'ApprovedDate': safe_isoformat(approved_date)
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"Error submitting policy review: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_version_history(request, policy_id):
    """
    Get the version history of a policy
    """
    try:
        approvals = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version')
        
        version_history = []
        for approval in approvals:
            version_history.append({
                'version': approval.Version,
                'previousVersion': approval.PreviousVersion,
                'approvedDate': approval.ApprovedDate,
                'status': 'Approved' if approval.ApprovedNot else 'Rejected' if approval.ApprovedNot is False else 'Under Review'
            })
        
        return Response({
            'policy_id': policy_id,
            'versions': version_history
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_policy_approvals_for_reviewer(request):
    # For now, reviewer_id is hardcoded as 2
    reviewer_id = 2
    
    print(f"Fetching policy approvals for reviewer_id: {reviewer_id}")
    
    # Get all approvals for this reviewer
    approvals = PolicyApproval.objects.filter(ReviewerId=reviewer_id)
    print(f"Found {approvals.count()} total policy approvals for reviewer {reviewer_id}")
    
    # Get unique policy IDs to ensure we only return the latest version of each policy
    unique_policies = {}
    
    for approval in approvals:
        policy_id = approval.PolicyId if approval.PolicyId else f"approval_{approval.ApprovalId}"
        print(f"Processing approval {approval.ApprovalId}: PolicyId={policy_id}, Version={approval.Version}, ApprovedNot={approval.ApprovedNot}")
        
        # If we haven't seen this policy yet, or if this is a newer version
        if policy_id not in unique_policies or float(approval.Version.lower().replace('r', '').replace('u', '') or 0) > float(unique_policies[policy_id].Version.lower().replace('r', '').replace('u', '') or 0):
            unique_policies[policy_id] = approval
    
    # Convert to a list of unique approvals
    unique_approvals = list(unique_policies.values())
    print(f"Returning {len(unique_approvals)} unique policy approvals")
    
    serializer = PolicyApprovalSerializer(unique_approvals, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_rejected_policy_approvals_for_user(request, user_id):
    # Filter policies by ReviewerId (not UserId) since we want reviewer's view
    rejected_approvals = PolicyApproval.objects.filter(
        ReviewerId=user_id,
        ApprovedNot=0  # Use 0 instead of False for consistency
    ).order_by('-ApprovalId')  # Get the most recent first
    
    # Get unique policy IDs to ensure we only return the latest version of each policy
    unique_policies = {}
    
    for approval in rejected_approvals:
        policy_id = approval.PolicyId_id if approval.PolicyId_id else f"approval_{approval.ApprovalId}"
        
        # If we haven't seen this policy yet, or if this is a newer version
        if policy_id not in unique_policies or float(approval.Version.lower().replace('r', '').replace('u', '') or 0):
            unique_policies[policy_id] = approval
    
    # Convert to a list of unique approvals
    unique_approvals = list(unique_policies.values())
    
    serializer = PolicyApprovalSerializer(unique_approvals, many=True)
    return Response(serializer.data)

"""
@api GET /api/frameworks/{framework_id}/export/
Exports all policies and their subpolicies for a specific framework to an Excel file in the following format:
Identifier, PolicyName (PolicyFamily), SubpolicyIdentifier, SubpolicyName, Control, Description

Example response:
Returns an Excel file as attachment
"""
@api_view(['POST'])
@permission_classes([AllowAny])
def export_policies_to_excel(request, framework_id):
    """
    Export framework policies and their subpolicies to various formats
    """
    print(f"[EXPORT] Request received to export policies for Framework ID: {framework_id}")

    try:
        # Get the framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        print(f"[EXPORT] Found framework: {framework.FrameworkName}")

        # Get all policies for this framework
        policy_id = request.data.get('policy_id')
        if policy_id:
            policies = Policy.objects.filter(FrameworkId=framework_id, PolicyId=policy_id)
        else:
            policies = Policy.objects.filter(FrameworkId=framework_id)
        print(f"[EXPORT] Found {policies.count()} policies under framework {framework_id}")

        # Prepare data for export (one row per subpolicy, or one row per policy if no subpolicies)
        export_data_list = []
        for policy in policies:
            print(f"[EXPORT] Processing policy: {policy.PolicyName}")
            subpolicies = policy.subpolicy_set.all()
            if subpolicies.exists():
                for sub in subpolicies:
                    row = {
                        'Policy ID': policy.PolicyId,
                        'Policy Name': policy.PolicyName,
                        'Version': policy.CurrentVersion,
                        'Status': policy.Status,
                        'Description': policy.PolicyDescription,
                        'Department': policy.Department,
                        'Created By': policy.CreatedByName,
                        'Created Date': policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                        'Start Date': policy.StartDate.isoformat() if policy.StartDate else None,
                        'End Date': policy.EndDate.isoformat() if policy.EndDate else None,
                        'Applicability': policy.Applicability,
                        'Scope': policy.Scope,
                        'Objective': policy.Objective,
                        'Identifier': policy.Identifier,
                        'Active/Inactive': policy.ActiveInactive,
                        # Subpolicy fields
                        'Subpolicy ID': sub.SubPolicyId,
                        'Subpolicy Name': sub.SubPolicyName,
                        'Subpolicy Identifier': sub.Identifier,
                        'Subpolicy Description': sub.Description,
                        'Subpolicy Status': sub.Status,
                        'Subpolicy Permanent/Temporary': sub.PermanentTemporary,
                        'Subpolicy Control': sub.Control,
                        'Subpolicy Created By': sub.CreatedByName,
                        'Subpolicy Created Date': sub.CreatedByDate.isoformat() if sub.CreatedByDate else None,
                    }
                    export_data_list.append(row)
            else:
                # Policy with no subpolicies: still include a row
                row = {
                    'Policy ID': policy.PolicyId,
                    'Policy Name': policy.PolicyName,
                    'Version': policy.CurrentVersion,
                    'Status': policy.Status,
                    'Description': policy.PolicyDescription,
                    'Department': policy.Department,
                    'Created By': policy.CreatedByName,
                    'Created Date': policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                    'Start Date': policy.StartDate.isoformat() if policy.StartDate else None,
                    'End Date': policy.EndDate.isoformat() if policy.EndDate else None,
                    'Applicability': policy.Applicability,
                    'Scope': policy.Scope,
                    'Objective': policy.Objective,
                    'Identifier': policy.Identifier,
                    'Active/Inactive': policy.ActiveInactive,
                    # Subpolicy fields (empty)
                    'Subpolicy ID': None,
                    'Subpolicy Name': None,
                    'Subpolicy Identifier': None,
                    'Subpolicy Description': None,
                    'Subpolicy Status': None,
                    'Subpolicy Permanent/Temporary': None,
                    'Subpolicy Control': None,
                    'Subpolicy Created By': None,
                    'Subpolicy Created Date': None,
                }
                export_data_list.append(row)

        # Get export format from request
        export_format = request.data.get('format', 'xlsx')
        print(f"[EXPORT] Export format requested: {export_format}")

        # Export the data
        print("[EXPORT] Initiating export_data process...")
        result = export_data(
            data=export_data_list,
            file_format=export_format,
            user_id=request.user.id if request.user.is_authenticated else 'anonymous',
            options={
                'framework_id': framework_id,
                'framework_name': framework.FrameworkName
            }
        )

        print(f"[EXPORT] Export successful. File name: {result['file_name']}")
        return Response({
            'success': True,
            'export_id': result['export_id'],
            'file_url': result['file_url'],
            'file_name': result['file_name'],
            'metadata': result['metadata']
        })

    except Framework.DoesNotExist:
        print(f"[ERROR] Framework with ID {framework_id} not found.")
        return Response({
            'success': False,
            'error': 'Framework not found'
        }, status=404)
        
    except Exception as e:
        print(f"[ERROR] Exception during export: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def policy_list(request):
    """
    List all policies, or filter by status
    """
    status_param = request.query_params.get('status', None)
    
    if status_param is not None:
        policies = Policy.objects.filter(Status=status_param)
    else:
        policies = Policy.objects.all()
    
    serializer = PolicySerializer(policies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_users(request):
    try:
        users = Users.objects.all()
        data = [{
            'UserId': user.UserId,
            'UserName': user.UserName
        } for user in users]
        return Response(data)
    except Exception as e:
        return Response({
            'error': 'Error fetching users',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
@permission_classes([AllowAny])
def get_framework_explorer_data(request):
    """
    API endpoint for the Framework Explorer page
    Returns frameworks with their status and counts of active/inactive policies
    """
    try:
        # Get all frameworks
        frameworks = Framework.objects.all()
       
        # Prepare response data with additional counts
        framework_data = []
        for fw in frameworks:
            # Count policies for this framework
            active_policies = Policy.objects.filter(
                FrameworkId=fw.FrameworkId,
                ActiveInactive='Active'
            ).count()
           
            inactive_policies = Policy.objects.filter(
                FrameworkId=fw.FrameworkId,
                ActiveInactive='Inactive'
            ).count()
           
            framework_data.append({
                'id': fw.FrameworkId,
                'name': fw.FrameworkName,
                'category': fw.Category or 'Uncategorized',
                'description': fw.FrameworkDescription,
                'status': fw.ActiveInactive,  # 'Active' or 'Inactive'
                'active_policies_count': active_policies,
                'inactive_policies_count': inactive_policies
            })
       
        # Calculate summary counts
        active_frameworks = Framework.objects.filter(ActiveInactive='Active').count()
        inactive_frameworks = Framework.objects.filter(ActiveInactive='Inactive').count()
        active_policies = Policy.objects.filter(ActiveInactive='Active').count()
        inactive_policies = Policy.objects.filter(ActiveInactive='Inactive').count()
       
        return Response({
            'frameworks': framework_data,
            'summary': {
                'active_frameworks': active_frameworks,
                'inactive_frameworks': inactive_frameworks,
                'active_policies': active_policies,
                'inactive_policies': inactive_policies
            }
        })
       
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([AllowAny])
def get_framework_policies(request, framework_id):
    """
    API endpoint for the Framework Policies page
    Returns policies for a specific framework
    """
    try:
        # Check if framework exists
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
       
        # Get policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id)
       
        # Prepare response data
        policy_data = []
        for policy in policies:
            policy_data.append({
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'category': policy.Department or 'General',
                'description': policy.PolicyDescription,
                'status': policy.ActiveInactive  # 'Active' or 'Inactive'
            })
       
        # Framework details
        framework_data = {
            'id': framework.FrameworkId,
            'name': framework.FrameworkName,
            'category': framework.Category,
            'description': framework.FrameworkDescription
        }
       
        return Response({
            'framework': framework_data,
            'policies': policy_data
        })
       
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_framework_status(request, framework_id):
    """
    Toggle the ActiveInactive status of a framework
    When cascadeToApproved=True, also update the status of all approved policies
    but leave their subpolicies status unchanged
    """
    try:
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
       
        # Toggle status
        new_status = 'Inactive' if framework.ActiveInactive == 'Active' else 'Active'
        framework.ActiveInactive = new_status
        
        # Also update the Status field if making inactive
        if new_status == 'Inactive':
            framework.Status = 'Inactive'
        else:
            # If activating, set to Approved status (assuming it was previously approved)
            framework.Status = 'Approved'
            
        framework.save()
       
        # Remove logic for inactivating other versions
        other_versions_deactivated = 0
       
        policies_affected = 0
        subpolicies_affected = 0
       
        # Check if we should cascade to policies
        cascade_to_approved = request.data.get('cascadeToApproved', False)
        if cascade_to_approved:
            # Get ALL policies for this framework (not just approved ones)
            policies = Policy.objects.filter(
                FrameworkId=framework
            )
           
            # Update their status to match the framework
            for policy in policies:
                policy.ActiveInactive = new_status
                
                # Also update the Status field if making inactive
                if new_status == 'Inactive':
                    policy.Status = 'Inactive'
                else:
                    # If activating, set to Approved status (assuming it was previously approved)
                    policy.Status = 'Approved'
                
                policy.save()
                policies_affected += 1
               
                # Also update all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy.Status = new_status
                    subpolicy.save()
                    subpolicies_affected += 1
       
        return Response({
            'id': framework.FrameworkId,
            'status': new_status,
            'message': f'Framework status updated to {new_status}',
            'policies_affected': policies_affected,
            'subpolicies_affected': subpolicies_affected,
            'other_versions_deactivated': other_versions_deactivated
        })
       
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_policy_status(request, policy_id):
    """
    Toggle the ActiveInactive status of a policy
    When cascadeSubpolicies=True, we don't change subpolicy Status but still count them
    """
    try:
        policy = get_object_or_404(Policy, PolicyId=policy_id)
       
        # Toggle status
        new_status = 'Inactive' if policy.ActiveInactive == 'Active' else 'Active'
        policy.ActiveInactive = new_status
        
        # DO NOT update the Status field - keep current status
        # This ensures that Approved policies remain Approved even when inactive
        current_status = policy.Status
        print(f"Toggling policy {policy.PolicyId} ActiveInactive to {new_status}, keeping Status as {current_status}")
        
        policy.save()
       
        # If activating this policy, deactivate other versions with the same Identifier
        other_versions_deactivated = 0
        
        if new_status == 'Active':
            # Use the centralized function to deactivate previous versions
            other_versions_deactivated = deactivate_previous_policy_versions(policy)
       
        subpolicies_affected = 0
       
        # Update subpolicies if cascadeSubpolicies is true
        cascade_to_subpolicies = request.data.get('cascadeSubpolicies', False)
        if cascade_to_subpolicies:
            # Get all subpolicies for this policy and update their status
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                # Only update ActiveInactive if the field exists, otherwise update Status
                if hasattr(subpolicy, 'ActiveInactive'):
                    subpolicy.ActiveInactive = new_status
                    print(f"Setting subpolicy {subpolicy.SubPolicyId} ActiveInactive to {new_status}")
                else:
                    subpolicy.Status = new_status
                    print(f"Setting subpolicy {subpolicy.SubPolicyId} Status to {new_status}")
                subpolicy.save()
                subpolicies_affected += 1
       
        return Response({
            'id': policy.PolicyId,
            'status': new_status,
            'message': f'Policy status updated to {new_status}',
            'subpolicies_affected': subpolicies_affected,
            'other_versions_deactivated': other_versions_deactivated
        })
       
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([AllowAny])
def get_framework_details(request, framework_id):
    """
    API endpoint for detailed framework information
    Returns all details of a framework regardless of status
    """
    try:
        # Get framework by ID
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
       
        # Create response data
        response_data = {
            'FrameworkId': framework.FrameworkId,
            'FrameworkName': framework.FrameworkName,
            'CurrentVersion': framework.CurrentVersion,
            'FrameworkDescription': framework.FrameworkDescription,
            'EffectiveDate': framework.EffectiveDate,
            'CreatedByName': framework.CreatedByName,
            'CreatedByDate': framework.CreatedByDate,
            'Category': framework.Category,
            'DocURL': framework.DocURL,
            'Identifier': framework.Identifier,
            'StartDate': framework.StartDate,
            'EndDate': framework.EndDate,
            'Status': framework.Status,
            'ActiveInactive': framework.ActiveInactive
        }
       
        return Response(response_data)
       
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_details(request, policy_id):
    """
    API endpoint for detailed policy information
    Returns all details of a policy regardless of status
    """
    try:
        # Get policy by ID
        policy = get_object_or_404(Policy, PolicyId=policy_id)
       
        # Get all subpolicies for this policy
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        subpolicy_data = []
       
        for subpolicy in subpolicies:
            subpolicy_data.append({
                'SubPolicyId': subpolicy.SubPolicyId,
                'SubPolicyName': subpolicy.SubPolicyName,
                'CreatedByName': subpolicy.CreatedByName,
                'CreatedByDate': subpolicy.CreatedByDate,
                'Identifier': subpolicy.Identifier,
                'Description': subpolicy.Description,
                'Status': subpolicy.Status,
                'PermanentTemporary': subpolicy.PermanentTemporary,
                'Control': subpolicy.Control
            })
       
        # Create response data
        response_data = {
            'PolicyId': policy.PolicyId,
            'PolicyName': policy.PolicyName,
            'PolicyDescription': policy.PolicyDescription,
            'CurrentVersion': policy.CurrentVersion,
            'StartDate': safe_isoformat(policy.StartDate),
            'EndDate': safe_isoformat(policy.EndDate),
            'Department': policy.Department,
            'CreatedByName': policy.CreatedByName,
            'CreatedByDate': safe_isoformat(policy.CreatedByDate),
            'Applicability': policy.Applicability,
            'DocURL': policy.DocURL,
            'Scope': policy.Scope,
            'Objective': policy.Objective,
            'Identifier': policy.Identifier,
            'PermanentTemporary': policy.PermanentTemporary,
            'Status': policy.Status,
            'ActiveInactive': policy.ActiveInactive,
            'subpolicies': subpolicy_data
        }
       
        return Response(response_data)
       
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#all policies code
@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_frameworks(request):
    """
    API endpoint to get all frameworks for AllPolicies.vue component.
    """
    try:
        frameworks = Framework.objects.all()
        
        frameworks_data = []
        for framework in frameworks:
            framework_data = {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'category': framework.Category,
                'status': framework.ActiveInactive,
                'description': framework.FrameworkDescription,
                'versions': []
            }
            
            # Get versions for this framework
            versions = FrameworkVersion.objects.filter(FrameworkId=framework)
            version_data = []
            for version in versions:
                version_data.append({
                    'id': version.VersionId,
                    'name': f"v{version.Version}",
                    'version': version.Version
                })
            
            framework_data['versions'] = version_data
            frameworks_data.append(framework_data)
            
        return Response(frameworks_data)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_framework_version_policies(request, version_id):
    """
    API endpoint to get all policies for a specific framework version for AllPolicies.vue component.
    """
    try:
        # Get the framework version
        framework_version = get_object_or_404(FrameworkVersion, VersionId=version_id)
        framework = framework_version.FrameworkId
        
        # Get policies for this framework
        policies = Policy.objects.filter(
            FrameworkId=framework, 
            CurrentVersion=framework_version.Version
        )
        
        policies_data = []
        for policy in policies:
            policy_data = {
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'category': policy.Department,
                'status': policy.Status,
                'description': policy.PolicyDescription,
                'versions': []
            }
            
            # Get versions for this policy
            policy_versions = PolicyVersion.objects.filter(PolicyId=policy)
            versions_data = []
            for version in policy_versions:
                versions_data.append({
                    'id': version.VersionId,
                    'name': f"v{version.Version}",
                    'version': version.Version
                })
            
            policy_data['versions'] = versions_data
            policies_data.append(policy_data)
            
        return Response(policies_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_policies(request):
    """
    API endpoint to get all policies for AllPolicies.vue component.
    """
    try:
        # Optional framework filter
        framework_id = request.GET.get('framework_id')
        
        # Start with all policies
        policies_query = Policy.objects.all()
        
        # Apply framework filter if provided
        if framework_id:
            policies_query = policies_query.filter(FrameworkId_id=framework_id)
        
        policies_data = []
        for policy in policies_query:
            policy_data = {
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'category': policy.Department,
                'status': policy.Status,
                'description': policy.PolicyDescription,
                'versions': []
            }
            
            # Get versions for this policy
            policy_versions = PolicyVersion.objects.filter(PolicyId=policy)
            versions_data = []
            for version in policy_versions:
                versions_data.append({
                    'id': version.VersionId,
                    'name': f"v{version.Version}",
                    'version': version.Version
                })
            
            policy_data['versions'] = versions_data
            policies_data.append(policy_data)
            
        return Response(policies_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_policy_versions(request, policy_id):
    """
    API endpoint to get all versions of a specific policy for AllPolicies.vue component.
    Implements a dedicated version that handles version chains through PreviousVersionId.
    """
    try:
        print(f"Request received for policy versions, policy_id: {policy_id}, type: {type(policy_id)}")
        
        # Ensure we have a valid integer ID
        try:
            policy_id = int(policy_id)
        except (ValueError, TypeError):
            return Response({'error': f'Invalid policy ID format: {policy_id}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get the base policy
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
            print(f"Found policy: {policy.PolicyName} (ID: {policy.PolicyId})")
        except Policy.DoesNotExist:
            print(f"Policy with ID {policy_id} not found")
            return Response({'error': f'Policy with ID {policy_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get the direct policy version
        try:
            direct_version = PolicyVersion.objects.get(PolicyId=policy)
            print(f"Found direct policy version: {direct_version.VersionId}")
        except PolicyVersion.DoesNotExist:
            print(f"No policy version found for policy ID {policy_id}")
            return Response({'error': f'No version found for policy with ID {policy_id}'}, 
                           status=status.HTTP_404_NOT_FOUND)
        except PolicyVersion.MultipleObjectsReturned:
            # If there are multiple versions, get all of them
            direct_versions = list(PolicyVersion.objects.filter(PolicyId=policy))
            print(f"Found {len(direct_versions)} direct versions for policy {policy_id}")
            direct_version = direct_versions[0]  # Just use the first one for starting the chain
        
        # Start building version chain
        all_versions = {}
        visited = set()
        to_process = [direct_version.VersionId]
        
        # Find all versions in the chain
        while to_process:
            current_id = to_process.pop(0)
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            try:
                current_version = PolicyVersion.objects.get(VersionId=current_id)
                all_versions[current_id] = current_version
                
                # Follow PreviousVersionId chain backward
                if current_version.PreviousVersionId and current_version.PreviousVersionId not in visited:
                    to_process.append(current_version.PreviousVersionId)
                    
                # Find versions that reference this one as their previous version
                next_versions = PolicyVersion.objects.filter(PreviousVersionId=current_id)
                for next_ver in next_versions:
                    if next_ver.VersionId not in visited:
                        to_process.append(next_ver.VersionId)
            except PolicyVersion.DoesNotExist:
                print(f"Version with ID {current_id} not found")
                continue
        
        versions_data = []
        for version_id, version in all_versions.items():
            try:
                # Get the policy this version belongs to
                version_policy = version.PolicyId
                
                # Count subpolicies for this policy
                subpolicy_count = SubPolicy.objects.filter(PolicyId=version_policy).count()
                
                # Get previous version details if available
                previous_version = None
                if version.PreviousVersionId:
                    try:
                        previous_version = PolicyVersion.objects.get(VersionId=version.PreviousVersionId)
                    except PolicyVersion.DoesNotExist:
                        pass
                
                # Create a descriptive name
                formatted_name = f"{version.PolicyName} v{version.Version}" if version.PolicyName else f"{version_policy.PolicyName} v{version.Version}"
                
                version_data = {
                    'id': version.VersionId,
                    'policy_id': version_policy.PolicyId,
                    'name': formatted_name,
                    'version': version.Version,
                    'category': version_policy.Department or 'General',
                    'status': version_policy.Status or 'Unknown',
                    'description': version_policy.PolicyDescription or '',
                    'created_date': version.CreatedDate,
                    'created_by': version.CreatedBy,
                    'subpolicy_count': subpolicy_count,
                    'previous_version_id': version.PreviousVersionId,
                    'previous_version_name': previous_version.PolicyName + f" v{previous_version.Version}" if previous_version else None
                }
                versions_data.append(version_data)
                print(f"Added version: {version.VersionId} - {formatted_name}, Previous: {version.PreviousVersionId}")
            except Exception as e:
                print(f"Error processing version {version_id}: {str(e)}")
                # Continue to next version
        
        # Sort versions by version number (descending)
        versions_data.sort(key=lambda x: float(x['version']), reverse=True)

        
        
        print(f"Returning {len(versions_data)} policy versions")
        return Response(versions_data)
        
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_policy_versions: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_subpolicies(request):
    """
    API endpoint to get all subpolicies for AllPolicies.vue component.
    """
    try:
        print("Request received for all subpolicies")
        
        # Optional framework filter
        framework_id = request.GET.get('framework_id')
        print(f"Framework filter: {framework_id}")
        
        # Start with all subpolicies
        subpolicies_query = SubPolicy.objects.all()
        
        # If framework filter is provided, filter through policies
        if framework_id:
            try:
                policy_ids = Policy.objects.filter(FrameworkId_id=framework_id).values_list('PolicyId', flat=True)
                print(f"Found {len(policy_ids)} policies for framework {framework_id}")
                subpolicies_query = subpolicies_query.filter(PolicyId_id__in=policy_ids)
            except Exception as e:
                print(f"Error filtering by framework: {str(e)}")
                # Continue with all subpolicies if framework filtering fails
        
        print(f"Found {subpolicies_query.count()} subpolicies")
        
        subpolicies_data = []
        for subpolicy in subpolicies_query:
            try:
                # Get the policy this subpolicy belongs to
                try:
                    policy = Policy.objects.get(PolicyId=subpolicy.PolicyId_id)
                    policy_name = policy.PolicyName
                    department = policy.Department
                except Policy.DoesNotExist:
                    print(f"Policy with ID {subpolicy.PolicyId_id} not found for subpolicy {subpolicy.SubPolicyId}")
                    policy_name = "Unknown Policy"
                    department = "Unknown"
                
                subpolicy_data = {
                    'id': subpolicy.SubPolicyId,
                    'name': subpolicy.SubPolicyName,
                    'category': department or 'General',
                    'status': subpolicy.Status or 'Unknown',
                    'description': subpolicy.Description or '',
                    'control': subpolicy.Control or '',
                    'identifier': subpolicy.Identifier,
                    'permanent_temporary': subpolicy.PermanentTemporary,
                    'policy_id': subpolicy.PolicyId_id,
                    'policy_name': policy_name,
                    'created_by': subpolicy.CreatedByName,
                    'created_date': safe_isoformat(subpolicy.CreatedByDate)
                }
                subpolicies_data.append(subpolicy_data)
                print(f"Added subpolicy: {subpolicy.SubPolicyId} - {subpolicy.SubPolicyName}")
            except Exception as e:
                print(f"Error processing subpolicy {subpolicy.SubPolicyId}: {str(e)}")
                # Continue to next subpolicy
        
        print(f"Returning {len(subpolicies_data)} subpolicies")
        return Response(subpolicies_data)
        
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_subpolicies: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_subpolicy_details(request, subpolicy_id):
    """
    API endpoint to get details of a specific subpolicy for AllPolicies.vue component.
    """
    try:
        subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
        policy = subpolicy.PolicyId
        
        subpolicy_data = {
            'id': subpolicy.SubPolicyId,
            'name': subpolicy.SubPolicyName,
            'category': policy.Department,
            'status': subpolicy.Status,
            'description': subpolicy.Description,
            'control': subpolicy.Control,
            'identifier': subpolicy.Identifier,
            'permanent_temporary': subpolicy.PermanentTemporary,
            'policy_id': policy.PolicyId,
            'policy_name': policy.PolicyName
        }
        
        return Response(subpolicy_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_framework_versions(request, framework_id):
    """
    API endpoint to get all versions of a specific framework for AllPolicies.vue component.
    Implements a dedicated version that handles version chains through PreviousVersionId.
    """
    try:
        print(f"Request received for framework versions, framework_id: {framework_id}, type: {type(framework_id)}")
        
        # Ensure we have a valid integer ID
        try:
            framework_id = int(framework_id)
        except (ValueError, TypeError):
            return Response({'error': f'Invalid framework ID format: {framework_id}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get the base framework
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
            print(f"Found framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
        except Framework.DoesNotExist:
            print(f"Framework with ID {framework_id} not found")
            return Response({'error': f'Framework with ID {framework_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get direct versions that belong to this framework
        direct_versions = list(FrameworkVersion.objects.filter(FrameworkId=framework).order_by('-Version'))
        print(f"Found {len(direct_versions)} direct versions for framework {framework_id}")
        
        # Create a dictionary to track all versions by VersionId
        all_versions = {v.VersionId: v for v in direct_versions}
        
        # Create a queue to process versions and follow PreviousVersionId links
        to_process = [v.VersionId for v in direct_versions]
        
        # Process the version chain by following PreviousVersionId links
        while to_process:
            current_id = to_process.pop(0)
            
            # Find versions that reference this one as their previous version
            linked_versions = FrameworkVersion.objects.filter(PreviousVersionId=current_id)
            print(f"Found {len(linked_versions)} linked versions for version ID {current_id}")
            
            for linked in linked_versions:
                if linked.VersionId not in all_versions:
                    # Add newly discovered version to our collection
                    all_versions[linked.VersionId] = linked
                    to_process.append(linked.VersionId)
        
        versions_data = []
        for version_id, version in all_versions.items():
            try:
                # Get the framework this version belongs to
                version_framework = version.FrameworkId
                
                # Count policies for this framework (without filtering by version)
                # This gets all policies associated with this framework regardless of version
                policy_count = Policy.objects.filter(
                    FrameworkId=version_framework
                ).count()
                
                print(f"Found {policy_count} policies for framework {version_framework.FrameworkId}")
                
                # Get previous version details if available
                previous_version = None
                if version.PreviousVersionId:
                    try:
                        previous_version = FrameworkVersion.objects.get(VersionId=version.PreviousVersionId)
                    except FrameworkVersion.DoesNotExist:
                        pass
                
                # Create a more descriptive name using the FrameworkName from the database
                # and appending the version number like v1.0, v2.0, etc.
                formatted_name = f"{version.FrameworkName} v{version.Version}"
                
                version_data = {
                    'id': version.VersionId,
                    'name': formatted_name,
                    'version': version.Version,
                    'category': version_framework.Category or 'General',
                    'status': version_framework.ActiveInactive or 'Unknown',
                    'description': version_framework.FrameworkDescription or '',
                    'created_date': version.CreatedDate,
                    'created_by': version.CreatedBy,
                    'policy_count': policy_count,
                    'previous_version_id': version.PreviousVersionId,
                    'previous_version_name': previous_version.FrameworkName + f" v{previous_version.Version}" if previous_version else None,
                    'framework_id': version_framework.FrameworkId
                }
                versions_data.append(version_data)
                print(f"Added version: {version.VersionId} - {formatted_name}, Previous: {version.PreviousVersionId}")
            except Exception as e:
                print(f"Error processing version {version_id}: {str(e)}")
                # Continue to next version
        
        # Sort versions by version number (descending)
        versions_data.sort(key=lambda x: float(x['version']), reverse=True)
        
        print(f"Returning {len(versions_data)} versions")
        return Response(versions_data)
        
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_framework_versions: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_policies_get_policy_version_subpolicies(request, version_id):
    """
    API endpoint to get all subpolicies for a specific policy version for AllPolicies.vue component.
    Implements a dedicated version instead of using the existing get_policy_version_subpolicies function.
    """
    try:
        print(f"Request received for policy version subpolicies, version_id: {version_id}, type: {type(version_id)}")
        
        # Ensure we have a valid integer ID
        try:
            version_id = int(version_id)
        except (ValueError, TypeError):
            print(f"Invalid version ID format: {version_id}")
            return Response({'error': f'Invalid version ID format: {version_id}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get the policy version
        try:
            policy_version = PolicyVersion.objects.get(VersionId=version_id)
            print(f"Found policy version: {policy_version.VersionId} for policy {policy_version.PolicyId_id}")
        except PolicyVersion.DoesNotExist:
            print(f"Policy version with ID {version_id} not found")
            return Response({'error': f'Policy version with ID {version_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get the policy this version belongs to
        try:
            policy = Policy.objects.get(PolicyId=policy_version.PolicyId_id)
            print(f"Found policy: {policy.PolicyName} (ID: {policy.PolicyId})")
        except Policy.DoesNotExist:
            print(f"Policy with ID {policy_version.PolicyId_id} not found")
            return Response({'error': f'Policy with ID {policy_version.PolicyId_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get subpolicies for this policy
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        print(f"Found {len(subpolicies)} subpolicies for policy {policy.PolicyId}")
        
        subpolicies_data = []
        for subpolicy in subpolicies:
            try:
                subpolicy_data = {
                    'id': subpolicy.SubPolicyId,
                    'name': subpolicy.SubPolicyName,
                    'category': policy.Department or 'General',
                    'status': subpolicy.Status or 'Unknown',
                    'description': subpolicy.Description or '',
                    'control': subpolicy.Control or '',
                    'identifier': subpolicy.Identifier,
                    'permanent_temporary': subpolicy.PermanentTemporary,
                    'policy_id': policy.PolicyId,
                    'policy_name': policy.PolicyName,
                    'created_by': subpolicy.CreatedByName,
                    'created_date': safe_isoformat(subpolicy.CreatedByDate)
                }
                subpolicies_data.append(subpolicy_data)
                print(f"Added subpolicy: {subpolicy.SubPolicyId} - {subpolicy.SubPolicyName}")
            except Exception as e:
                print(f"Error processing subpolicy {subpolicy.SubPolicyId}: {str(e)}")
                # Continue to next subpolicy
        
        print(f"Returning {len(subpolicies_data)} subpolicies")
        return Response(subpolicies_data)
        
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_policy_version_subpolicies: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_dashboard_summary(request):
    total_policies = Policy.objects.count()
    total_subpolicies = SubPolicy.objects.count()
    active_policies = Policy.objects.filter(ActiveInactive='Active').count()
    inactive_policies = Policy.objects.filter(ActiveInactive='Inactive').count()
    approved_policies = PolicyApproval.objects.filter(ApprovedNot=1).count()
    total_approvals = PolicyApproval.objects.count()
    approval_rate = (approved_policies / total_approvals) * 100 if total_approvals else 0

    # Get all policies with their details
    policies = Policy.objects.all().values(
        'PolicyId', 'PolicyName', 'Department', 'Status', 
        'Applicability', 'CurrentVersion', 'ActiveInactive',
        'PermanentTemporary', 'CreatedByDate'
    )

    return Response({
        'total_policies': total_policies,
        'total_subpolicies': total_subpolicies,
        'active_policies': active_policies,
        'inactive_policies': inactive_policies,
        'approval_rate': round(approval_rate, 2),
        'policies': list(policies)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_status_distribution(request):
    status_counts = Policy.objects.values('Status').annotate(count=Count('Status'))
    return Response(status_counts)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_reviewer_workload(request):
    reviewer_counts = Policy.objects.values('Reviewer').annotate(count=Count('Reviewer')).order_by('-count')
    return Response(reviewer_counts)

from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([AllowAny])
def get_recent_policy_activity(request):
    one_week_ago = timezone.now().date() - timedelta(days=7)
    recent_policies = Policy.objects.filter(CreatedByDate__gte=one_week_ago).order_by('-CreatedByDate')[:5]
    return Response([
        {
            'PolicyName': p.PolicyName,
            'CreatedBy': p.CreatedByName,
            'CreatedDate': safe_isoformat(p.CreatedByDate)
        } for p in recent_policies
    ])

from django.db.models import F, ExpressionWrapper, DurationField

@api_view(['GET'])
@permission_classes([AllowAny])
def get_avg_policy_approval_time(request):
    # Get all approved policies with approval dates
    approved_approvals = PolicyApproval.objects.filter(
        ApprovedNot=True,
        ApprovedDate__isnull=False
    )
    if not approved_approvals:
        return Response({'average_days': 0})

    # Map PolicyId to latest ApprovedDate (use PolicyId_id as integer)
    latest_approval_dates = {}
    for approval in approved_approvals:
        pid = approval.PolicyId  # Use the integer ID, not the object
        if pid not in latest_approval_dates or approval.ApprovedDate > latest_approval_dates[pid]:
            latest_approval_dates[pid] = approval.ApprovedDate

    # For each PolicyId, get CreatedByDate from Policy and compute days
    total_days = 0
    count = 0
    from ..models import Policy
    for pid, approved_date in latest_approval_dates.items():
        try:
            policy = Policy.objects.get(PolicyId=pid)
            created_date = policy.CreatedByDate
            if created_date and approved_date:
                days = (approved_date - created_date).days
                if days >= 0:
                    total_days += days
                    count += 1
        except Policy.DoesNotExist:
            continue

    avg_days = total_days / count if count > 0 else 0
    return Response({'average_days': round(avg_days, 2)})

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_analytics(request):
    try:
        x_axis = request.GET.get('x_axis', 'time')
        y_axis = request.GET.get('y_axis', 'count')
        
        # Initialize base queryset
        if x_axis == 'subpolicy':
            queryset = SubPolicy.objects.all()
            base_model = 'subpolicy'
        elif x_axis == 'framework':
            queryset = Framework.objects.all()
            base_model = 'framework'
        else:
            queryset = Policy.objects.all()
            base_model = 'policy'

        # Select base queryset based on x-axis and y-axis combination
        if y_axis == 'framework_policies' and x_axis == 'time':
            # Count policies created on each date
            queryset = Policy.objects.values(
                'CreatedByDate'
            ).annotate(
                label=F('CreatedByDate'),
                value=Count('PolicyId')
            ).order_by('CreatedByDate')
            
            # Format the dates
            data = list(queryset)
            for item in data:
                item['label'] = item['label'].strftime('%Y-%m-%d') if item['label'] else None
            
            return Response(data)
        
        # Group by X-axis
        if x_axis == 'status':
            queryset = queryset.values(
                'Status'
            ).annotate(
                label=F('Status'),
            )
        elif x_axis == 'policy':
            queryset = queryset.values(
                'PolicyId', 'PolicyName'
            ).annotate(
                label=F('PolicyName'),
            )
        elif x_axis == 'subpolicy':
            queryset = queryset.values(
                'SubPolicyId', 'SubPolicyName'
            ).annotate(
                label=F('SubPolicyName'),
            )
        elif x_axis == 'time':
            date_field = {
                'framework': 'CreatedByDate',
                'policy': 'CreatedByDate',
                'subpolicy': 'CreatedByDate'
            }[base_model]
            queryset = queryset.values(
                date_field
            ).annotate(
                label=F(date_field),
            ).order_by(date_field)
        elif x_axis == 'framework':
            queryset = queryset.values(
                'FrameworkName'
            ).annotate(
                label=F('FrameworkName'),
            )
        
        # Apply Y-axis aggregation
        if y_axis == 'version':
            if base_model == 'framework':
                # Get all framework versions
                framework_versions = FrameworkVersion.objects.values(
                    'FrameworkId__Identifier'  # Group by framework identifier
                ).annotate(
                    version_count=Count('VersionId', distinct=True)  # Count distinct versions
                )
                
                # Create a mapping of framework identifier to version count
                version_counts = {fv['FrameworkId__Identifier']: fv['version_count'] for fv in framework_versions}
                
                # Get all frameworks first
                frameworks = Framework.objects.all()
                framework_id_to_identifier = {f.FrameworkId: f.Identifier for f in frameworks}
                
                # Add version count to each item in queryset
                data = list(queryset)
                for item in data:
                    if x_axis == 'framework':
                        framework_id = item['FrameworkId']
                    else:
                        # For other x_axis types (like department), we need to aggregate versions
                        # Get all frameworks matching the current group
                        if x_axis == 'department':
                            group_frameworks = frameworks.filter(Department=item['Department'])
                        elif x_axis == 'status':
                            group_frameworks = frameworks.filter(Status=item['Status'])
                        elif x_axis == 'applicability':
                            group_frameworks = frameworks.filter(Applicability=item['Applicability'])
                        else:
                            group_frameworks = frameworks
                            
                        # Sum up versions for all frameworks in this group
                        total_versions = 0
                        for framework in group_frameworks:
                            total_versions += version_counts.get(framework.Identifier, 1)
                        item['value'] = total_versions
                        continue
                    
                    # For framework x_axis, use the direct mapping
                    identifier = framework_id_to_identifier.get(framework_id)
                    item['value'] = version_counts.get(identifier, 1) if identifier else 1
                
                return Response(data)
                
            elif base_model == 'policy':
                # Count versions by following PreviousVersionId chain
                policy_versions = PolicyVersion.objects.values('PolicyId').annotate(
                    version_count=Count('VersionId', distinct=True)
                )
                version_counts = {pv['PolicyId']: pv['version_count'] for pv in policy_versions}
                
                # Add version count to each policy
                data = list(queryset)
                for item in data:
                    item['value'] = version_counts.get(item.get('PolicyId'), 0)
                return Response(data)
            else:
                # SubPolicies don't have versions
                queryset = queryset.annotate(value=Value(0))
        elif y_axis == 'activeInactive':
            if base_model == 'framework':
                # For frameworks, use ActiveInactive field
                queryset = queryset.values(
                    'ActiveInactive'
                ).annotate(
                    label=Coalesce('ActiveInactive', Value('Unknown')),
                    value=Count('FrameworkId')
                )
            elif base_model == 'policy':
                # For policies, use ActiveInactive field
                queryset = queryset.values(
                    'ActiveInactive'
                ).annotate(
                    label=Coalesce('ActiveInactive', Value('Unknown')),
                    value=Count('PolicyId')
                )
            else:
                # For subpolicies, use parent policy's ActiveInactive status
                queryset = queryset.values(
                    'PolicyId__ActiveInactive'  # Get ActiveInactive from parent policy
                ).annotate(
                    label=Coalesce('PolicyId__ActiveInactive', Value('Unknown')),
                    value=Count('SubPolicyId')
                )
        elif y_axis == 'framework_policies':
            if base_model == 'framework':
                queryset = queryset.annotate(
                    value=Count('policy')
                )
            else:
                queryset = queryset.annotate(value=Value(0))

        elif y_axis == 'createdByDate':
            # Handle CreatedByDate aggregation based on X-axis selection
            if x_axis == 'framework':
                queryset = queryset.values(
                    'CreatedByDate'
                ).annotate(
                    label=F('CreatedByDate'),
                    value=Count('FrameworkId')
                ).order_by('CreatedByDate')
            elif x_axis == 'policy':
                queryset = queryset.values(
                    'CreatedByDate'
                ).annotate(
                    label=F('CreatedByDate'),
                    value=Count('PolicyId')
                ).order_by('CreatedByDate')
            elif x_axis == 'subpolicy':
                queryset = queryset.values(
                    'CreatedByDate'
                ).annotate(
                    label=F('CreatedByDate'),
                    value=Count('SubPolicyId')
                ).order_by('CreatedByDate')

            # Format the dates for display
            data = list(queryset)
            for item in data:
                if item['label']:
                    # Convert date to string in YYYY-MM-DD format
                    item['label'] = item['label'].strftime('%Y-%m-%d')
            return Response(data)
        elif y_axis == 'department':
            # Handle Department aggregation based on X-axis selection
            if x_axis == 'framework':
                # For frameworks, get departments through policy relationship
                base_queryset = Framework.objects.values(
                    'FrameworkId', 'FrameworkName'
                ).annotate(
                    policy_count=Count('policy')
                ).filter(policy_count__gt=0)

                # Get all policies for these frameworks
                framework_policies = Policy.objects.filter(
                    FrameworkId__in=[f['FrameworkId'] for f in base_queryset]
                ).values('FrameworkId', 'Department')

                # Process departments and count frameworks
                department_counts = {}
                framework_departments = {}  # Track which departments each framework has been counted for

                for policy in framework_policies:
                    framework_id = policy['FrameworkId']
                    dept_str = policy['Department']
                    
                    if not dept_str:
                        continue

                    # Initialize set for this framework if not exists
                    if framework_id not in framework_departments:
                        framework_departments[framework_id] = set()

                    # Split departments and process each
                    departments = [d.strip().upper() for d in dept_str.split(',')]
                    for dept in departments:
                        if dept and dept not in framework_departments[framework_id]:
                            # Count framework for this department only once
                            department_counts[dept] = department_counts.get(dept, 0) + 1
                            framework_departments[framework_id].add(dept)

            elif x_axis == 'policy':
                # For policies, use Department field directly
                base_queryset = queryset.values(
                    'PolicyId',
                    'Department'
                )
            elif x_axis == 'subpolicy':
                # For subpolicies, get department through policy relationship
                base_queryset = queryset.values(
                    'SubPolicyId',
                    'PolicyId__Department'
                )

            if x_axis != 'framework':
                # Process departments and split comma-separated values
                department_counts = {}
                for item in base_queryset:
                    # Get the department field based on the model type
                    dept_field = (
                        item.get('Department') or 
                        item.get('policy__Department') or 
                        item.get('PolicyId__Department')
                    )
                    
                    if dept_field:
                        # Split departments by comma and strip whitespace
                        departments = [d.strip().upper() for d in dept_field.split(',')]
                        for dept in departments:
                            if dept:  # Only count non-empty departments
                                department_counts[dept] = department_counts.get(dept, 0) + 1

            # Convert to list format expected by frontend
            data = [
                {
                    'label': f"{dept.title()} ({count} frameworks)" if x_axis == 'framework' else f"{dept.title()} ({count} items)",
                    'value': count
                }
                for dept, count in department_counts.items()
            ]

            # Sort by count (descending) then by department name
            data.sort(key=lambda x: (-x['value'], x['label']))

            # Add unassigned if no departments found
            if not data:
                label = 'Unassigned (0 frameworks)' if x_axis == 'framework' else 'Unassigned (0 items)'
                data.append({
                    'label': label,
                    'value': 0
                })

            return Response(data)
        elif y_axis == 'createdByName':
            # Handle CreatedByName aggregation based on X-axis selection
            if x_axis == 'framework':
                queryset = queryset.values(
                    'CreatedByName'
                ).annotate(
                    label=F('CreatedByName'),  # Use the actual CreatedByName value
                    value=Count('FrameworkId', distinct=True)  # Count unique frameworks
                ).order_by('-value', 'CreatedByName')  # Order by count desc, then name
            elif x_axis == 'policy':
                queryset = queryset.values(
                    'CreatedByName'
                ).annotate(
                    label=F('CreatedByName'),  # Use the actual CreatedByName value
                    value=Count('PolicyId', distinct=True)  # Count unique policies
                ).order_by('-value', 'CreatedByName')  # Order by count desc, then name
            elif x_axis == 'subpolicy':
                queryset = queryset.values(
                    'CreatedByName'
                ).annotate(
                    label=F('CreatedByName'),  # Use the actual CreatedByName value
                    value=Count('SubPolicyId', distinct=True)  # Count unique subpolicies
                ).order_by('-value', 'CreatedByName')  # Order by count desc, then name

            # Add creator label for clarity
            data = list(queryset)
            for item in data:
                item['label'] = f"{item['label']} ({item['value']} items)"
            return Response(data)
        elif y_axis == 'status':
            if base_model == 'framework':
                # For frameworks, directly use the Status field
                queryset = queryset.values(
                    'Status'
                ).annotate(
                    label=Coalesce('Status', Value('Unknown')),
                    value=Count('FrameworkId')
                )
            elif base_model == 'policy':
                # For policies, use their Status field
                queryset = queryset.values(
                    'Status'
                ).annotate(
                    label=Coalesce('Status', Value('Unknown')),
                    value=Count('PolicyId')
                )
            else:
                # For subpolicies, use their Status field
                queryset = queryset.values(
                    'Status'
                ).annotate(
                    label=Coalesce('Status', Value('Unknown')),
                    value=Count('SubPolicyId')
                )
        elif y_axis == 'category':
            if base_model == 'policy':
                # For policies, use PolicyType, PolicyCategory, and PolicySubCategory fields
                queryset = queryset.values(
                    'PolicyType', 'PolicyCategory', 'PolicySubCategory'
                ).annotate(
                    value=Count('PolicyId')
                )
                
                # Format the category data
                data = []
                for item in queryset:
                    policy_type = item.get('PolicyType') or 'Uncategorized'
                    policy_category = item.get('PolicyCategory') or 'Uncategorized'
                    policy_subcategory = item.get('PolicySubCategory') or 'Uncategorized'
                    
                    # Create a formatted label
                    label = f"{policy_type} > {policy_category} > {policy_subcategory}"
                    if label == "Uncategorized > Uncategorized > Uncategorized":
                        label = "Uncategorized"
                    
                    data.append({
                        'label': label,
                        'value': item['value']
                    })
                
                return Response(data)
            elif base_model == 'subpolicy':
                # For subpolicies, get category through policy relationship
                queryset = queryset.values(
                    'PolicyId__PolicyType', 'PolicyId__PolicyCategory', 'PolicyId__PolicySubCategory'
                ).annotate(
                    value=Count('SubPolicyId')
                )
                
                # Format the category data
                data = []
                for item in queryset:
                    policy_type = item.get('PolicyId__PolicyType') or 'Uncategorized'
                    policy_category = item.get('PolicyId__PolicyCategory') or 'Uncategorized'
                    policy_subcategory = item.get('PolicyId__PolicySubCategory') or 'Uncategorized'
                    
                    # Create a formatted label
                    label = f"{policy_type} > {policy_category} > {policy_subcategory}"
                    if label == "Uncategorized > Uncategorized > Uncategorized":
                        label = "Uncategorized"
                    
                    data.append({
                        'label': label,
                        'value': item['value']
                    })
                
                return Response(data)
            elif base_model == 'framework':
                # For frameworks, use framework category
                queryset = queryset.values(
                    'Category'
                ).annotate(
                    label=Coalesce('Category', Value('Uncategorized')),
                    value=Count('FrameworkId')
                )
            else:
                # For subpolicies, get category through policy->framework relationship
                queryset = queryset.values(
                    'PolicyId__FrameworkId__Category'
                ).annotate(
                    label=Coalesce('PolicyId__FrameworkId__Category', Value('Uncategorized')),
                    value=Count('SubPolicyId')
                )
        
        data = list(queryset)
        
        # Format dates for time-based analysis
        if x_axis == 'time':
            for item in data:
                date_value = item.get(date_field)
                item['label'] = date_value.strftime('%Y-%m-%d') if date_value else None
        
        return Response(data)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=500
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_kpis(request):
    try:
        # Get total policies count
        total_policies = Policy.objects.count()
        
        # Get active policies count
        active_policies = Policy.objects.filter(
            ActiveInactive='Active'
        ).count()

        # Get total users count for acknowledgement rate calculation
        total_users = Users.objects.count()

        # Get top 5 policies by acknowledgement rate
        policies = Policy.objects.filter(ActiveInactive='Active').annotate(
            acknowledgement_rate=Case(
                When(AcknowledgementCount__gt=0, 
                     then=ExpressionWrapper(
                         F('AcknowledgementCount') * 100.0 / total_users,
                         output_field=FloatField()
                     )),
                default=Value(0.0),
                output_field=FloatField(),
            )
        ).order_by('-acknowledgement_rate')[:5]

        top_acknowledged_policies = [
            {
                'policy_id': policy.PolicyId,
                'policy_name': policy.PolicyName,
                'acknowledged_count': policy.AcknowledgementCount,
                'total_users': total_users,
                'acknowledgement_rate': round(float(policy.acknowledgement_rate), 1)
            }
            for policy in policies
        ]

        # Get historical active policy counts for the last 12 months
        twelve_months_ago = date.today() - timedelta(days=365)
        monthly_counts = []
        
        # Get all policies with their creation dates
        policies = Policy.objects.filter(
            CreatedByDate__gte=twelve_months_ago
        ).values('CreatedByDate', 'ActiveInactive')
        
        # Group by month and count active policies
        month_data = {}
        current_date = date.today()
        
        # Initialize all months with 0
        for i in range(12):
            month_date = current_date - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            month_data[month_key] = 0
        
        # Count active policies for each month
        for policy in policies:
            month_key = policy['CreatedByDate'].strftime('%Y-%m')
            if month_key in month_data and policy['ActiveInactive'] == 'Active':
                month_data[month_key] += 1
        
        # Convert to sorted list for last 12 months
        monthly_counts = [
            {
                'month': k,
                'count': v
            }
            for k, v in sorted(month_data.items(), reverse=True)
        ][:12]
        
        # Calculate revision metrics
        three_months_ago = date.today() - timedelta(days=90)
        
        # Get all policy versions with previous version links
        policy_versions = PolicyVersion.objects.filter(
            PreviousVersionId__isnull=False  # Has a previous version
        ).select_related('PolicyId')
        
        # Track revised policies and their revision counts
        revision_counts = {}  # Dictionary to track revisions per PreviousVersionId
        revised_policies_set = set()
        total_revisions = 0
        
        # Process each version that has a previous version
        for version in policy_versions:
            policy_id = version.PolicyId.PolicyId
            prev_version_id = version.PreviousVersionId
            
            # Count this as a revision
            revised_policies_set.add(policy_id)
            total_revisions += 1
            
            # Track revisions per previous version
            if prev_version_id not in revision_counts:
                revision_counts[prev_version_id] = 1
            else:
                revision_counts[prev_version_id] += 1
        
        # Calculate policies with multiple revisions
        multiple_revisions_count = sum(1 for count in revision_counts.values() if count > 1)
        
        # Calculate final metrics
        revised_policies = len(revised_policies_set)
        
        # Calculate revision rate using total policies as denominator
        revision_rate = 0
        if total_policies > 0:  # Avoid division by zero
            revision_rate = (revised_policies / total_policies) * 100
            revision_rate = min(revision_rate, 100)  # Cap at 100%

        # Calculate policy coverage by department
        departments = Policy.objects.values_list('Department', flat=True).distinct()
        department_coverage = []
        
        for dept in departments:
            if dept:  # Skip empty department values
                dept_policies = Policy.objects.filter(Department=dept)
                total_dept_policies = dept_policies.count()
                if total_dept_policies > 0:
                    avg_coverage = dept_policies.aggregate(
                        avg_coverage=Coalesce(Avg('CoverageRate'), 0.0)
                    )['avg_coverage']
                    
                    department_coverage.append({
                        'department': dept,
                        'coverage_rate': round(float(avg_coverage), 2),
                        'total_policies': total_dept_policies
                    })
        
        # Sort departments by coverage rate in descending order
        department_coverage.sort(key=lambda x: x['coverage_rate'], reverse=True)
        
        # Calculate overall average coverage rate
        overall_coverage = Policy.objects.aggregate(
            avg_coverage=Coalesce(Avg('CoverageRate'), 0.0)
        )['avg_coverage']

        # Calculate average approval time metrics
        # Get all approved policies with their approval dates
        approved_policies = PolicyApproval.objects.filter(
            ApprovedNot=True,
            ApprovedDate__isnull=False
        ).select_related('PolicyId')

        # Calculate approval times for each policy
        approval_times = []
        for approval in approved_policies:
            if approval.PolicyId and approval.PolicyId.CreatedByDate:
                approval_time = (approval.ApprovedDate - approval.PolicyId.CreatedByDate).days
                if approval_time >= 0:  # Only include valid approval times
                    approval_times.append({
                        'month': approval.ApprovedDate.strftime('%Y-%m'),
                        'approval_time': approval_time
                    })

        # Calculate monthly averages
        monthly_approval_times = {}
        for time in approval_times:
            month = time['month']
            if month not in monthly_approval_times:
                monthly_approval_times[month] = []
            monthly_approval_times[month].append(time['approval_time'])

        # Calculate average for each month
        monthly_averages = []
        for month, times in monthly_approval_times.items():
            if times:  # Only include months with data
                monthly_averages.append({
                    'month': month,
                    'average_time': round(sum(times) / len(times), 1)
                })

        # Sort by month
        monthly_averages.sort(key=lambda x: x['month'])
        
        return Response({
            'total_policies': total_policies,
            'active_policies': active_policies,
            'active_policies_trend': monthly_counts,  # Add historical trend data
            'revision_rate': round(revision_rate, 2),
            'revised_policies': revised_policies,
            'total_revisions': total_revisions,
            'policies_with_multiple_revisions': multiple_revisions_count,
            'measurement_period': '3 months',
            'coverage_metrics': {
                'overall_coverage_rate': round(float(overall_coverage), 2),
                'department_coverage': department_coverage
            },
            'top_acknowledged_policies': top_acknowledged_policies,
            'approval_time_metrics': {
                'monthly_averages': monthly_averages,
                'overall_average': round(sum(time['approval_time'] for time in approval_times) / len(approval_times), 1) if approval_times else 0
            }
        })
    except Exception as e:
        print(f"Error in get_policy_kpis: {str(e)}")
        return Response({
            'error': 'Error fetching policy KPIs',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def acknowledge_policy(request, policy_id):
    try:
        policy = Policy.objects.get(PolicyId=policy_id)
        user_id = 3  # Hardcoded for testing as requested
        
        # Initialize acknowledged_users list if None
        acknowledged_users = policy.AcknowledgedUserIds if policy.AcknowledgedUserIds is not None else []
        
        # Check if user already acknowledged
        if user_id not in acknowledged_users:
            # Add user to acknowledged list
            acknowledged_users.append(user_id)
            policy.AcknowledgedUserIds = acknowledged_users
            policy.AcknowledgementCount = len(acknowledged_users)
            policy.save()
            
            return Response({
                'message': 'Policy acknowledged successfully',
                'acknowledged_users': policy.AcknowledgedUserIds,
                'acknowledgement_count': policy.AcknowledgementCount
            })
        else:
            return Response({
                'message': 'Policy already acknowledged by this user',
                'acknowledged_users': policy.AcknowledgedUserIds,
                'acknowledgement_count': policy.AcknowledgementCount
            })

    except Policy.DoesNotExist:
        return Response({
            'error': 'Policy not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in acknowledge_policy: {str(e)}")  # Add logging
        return Response({
            'error': 'Error acknowledging policy',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add this helper function near the top of the file (after imports)
def safe_isoformat(val):
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return val if isinstance(val, str) else None


@api_view(['POST'])
@permission_classes([AllowAny])
def create_tailored_framework(request):
    """
    Create a new framework from the Tailoring page with policies and subpolicies
    This will automatically create the framework approval entry for the approval workflow
    """
    try:
        data = request.data
        print(f"Received tailored framework data: {data}")
        
        # Parse date fields safely using parse_date
        effective_date = parse_date(data.get('effectiveDate'))
        start_date = parse_date(data.get('startDate'))
        end_date = parse_date(data.get('endDate'))
        
        # Get user information for reviewer assignment
        reviewer_name = data.get('reviewer', '')
        reviewer_id = None
        if reviewer_name:
            reviewer_user = Users.objects.filter(UserName=reviewer_name).first()
            if reviewer_user:
                reviewer_id = reviewer_user.UserId
            else:
                reviewer_id = 2  # Default reviewer ID
        else:
            reviewer_id = 2  # Default reviewer ID
        
        framework_data = {
            'FrameworkName': data.get('title'),
            'FrameworkDescription': data.get('description', ''),
            'EffectiveDate': effective_date,
            'CreatedByName': data.get('createdByName'),
            'CreatedByDate': date.today(),
            'Category': data.get('category', ''),
            'DocURL': data.get('docURL', ''),
            'Identifier': data.get('identifier', ''),
            'StartDate': start_date,
            'EndDate': end_date,
            'Status': 'Under Review',
            'ActiveInactive': 'InActive',
            'Reviewer': reviewer_name,
            'CurrentVersion': 1.0
        }
        
        with transaction.atomic():
            # Create the framework
            framework = Framework.objects.create(**framework_data)
            print(f"Created framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
            
            # Create framework version record
            framework_version = FrameworkVersion.objects.create(
                FrameworkId=framework,
                Version=1.0,
                FrameworkName=framework.FrameworkName,
                CreatedBy=framework.CreatedByName,
                CreatedDate=date.today(),
                PreviousVersionId=None
            )
            print(f"Created framework version: {framework_version.Version}")
            
            created_policies = []
            
            # Process policies
            if 'policies' in data and isinstance(data['policies'], list):
                for policy_data in data['policies']:
                    # Skip excluded policies
                    if policy_data.get('exclude', False):
                        print(f"Skipping excluded policy: {policy_data.get('title', 'Unknown')}")
                        continue
                    
                    # Parse policy dates
                    policy_start_date = parse_date(policy_data.get('startDate'))
                    policy_end_date = parse_date(policy_data.get('endDate'))
                    
                    # Get policy reviewer information
                    policy_reviewer_name = policy_data.get('reviewer', '')
                    if not policy_reviewer_name:
                        policy_reviewer_name = reviewer_name  # Use framework reviewer as fallback
                    
                    policy = Policy.objects.create(
                        FrameworkId=framework,
                        PolicyName=policy_data.get('title', ''),
                        PolicyDescription=policy_data.get('description', ''),
                        Status='Under Review',
                        StartDate=policy_start_date,
                        EndDate=policy_end_date,
                        Department=policy_data.get('department', ''),
                        CreatedByName=policy_data.get('createdByName', framework.CreatedByName),
                        CreatedByDate=date.today(),
                        Applicability=policy_data.get('applicability', ''),
                        DocURL=policy_data.get('docURL', ''),
                        Scope=policy_data.get('scope', ''),
                        Objective=policy_data.get('objective', ''),
                        Identifier=policy_data.get('identifier', ''),
                        PermanentTemporary='',
                        ActiveInactive='InActive',
                        Reviewer=policy_reviewer_name,
                        CoverageRate=policy_data.get('coverageRate'),
                        CurrentVersion='1.0',
                        # Add policy category fields
                        PolicyType=policy_data.get('PolicyType', ''),
                        PolicyCategory=policy_data.get('PolicyCategory', ''),
                        PolicySubCategory=policy_data.get('PolicySubCategory', '')
                    )
                    
                    created_policies.append(policy)
                    print(f"Created policy: {policy.PolicyName} (ID: {policy.PolicyId})")
                    
                    # Create policy version record
                    PolicyVersion.objects.create(
                        PolicyId=policy,
                        Version='1.0',
                        PolicyName=policy.PolicyName,
                        CreatedBy=policy.CreatedByName,
                        CreatedDate=date.today(),
                        PreviousVersionId=None
                    )
                    
                    # Process subpolicies
                    if 'subPolicies' in policy_data and isinstance(policy_data['subPolicies'], list):
                        for subpolicy_data in policy_data['subPolicies']:
                            # Skip excluded subpolicies
                            if subpolicy_data.get('exclude', False):
                                print(f"Skipping excluded subpolicy: {subpolicy_data.get('title', 'Unknown')}")
                                continue
                            
                            subpolicy = SubPolicy.objects.create(
                                PolicyId=policy,
                                SubPolicyName=subpolicy_data.get('title', ''),
                                CreatedByName=policy_data.get('createdByName', framework.CreatedByName),
                                CreatedByDate=date.today(),
                                Identifier=subpolicy_data.get('identifier', ''),
                                Description=subpolicy_data.get('description', ''),
                                Status='Under Review',
                                PermanentTemporary='',
                                Control=subpolicy_data.get('control', '')
                            )
                            print(f"Created subpolicy: {subpolicy.SubPolicyName} (ID: {subpolicy.SubPolicyId})")
            
            # Create framework approval entry for the approval workflow
            policies_data = []
            
            # Collect all policies and subpolicies data for the approval JSON
            for policy in created_policies:
                policy_dict = {
                    "PolicyId": policy.PolicyId,
                    "PolicyName": policy.PolicyName,
                    "PolicyDescription": policy.PolicyDescription,
                    "Status": policy.Status,
                    "StartDate": policy.StartDate.isoformat() if policy.StartDate else None,
                    "EndDate": policy.EndDate.isoformat() if policy.EndDate else None,
                    "Department": policy.Department,
                    "CreatedByName": policy.CreatedByName,
                    "CreatedByDate": policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                    "Applicability": policy.Applicability,
                    "DocURL": policy.DocURL,
                    "Scope": policy.Scope,
                    "Objective": policy.Objective,
                    "Identifier": policy.Identifier,
                    "PermanentTemporary": policy.PermanentTemporary,
                    "ActiveInactive": policy.ActiveInactive,
                    "Reviewer": policy.Reviewer,
                    "CoverageRate": policy.CoverageRate,
                    "CurrentVersion": policy.CurrentVersion,
                    "PolicyType": policy.PolicyType,
                    "PolicyCategory": policy.PolicyCategory,
                    "PolicySubCategory": policy.PolicySubCategory,
                    "subpolicies": []
                }
                
                # Get subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy_dict = {
                        "SubPolicyId": subpolicy.SubPolicyId,
                        "SubPolicyName": subpolicy.SubPolicyName,
                        "CreatedByName": subpolicy.CreatedByName,
                        "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
                        "Identifier": subpolicy.Identifier,
                        "Description": subpolicy.Description,
                        "Status": subpolicy.Status,
                        "PermanentTemporary": subpolicy.PermanentTemporary,
                        "Control": subpolicy.Control
                    }
                    policy_dict["subpolicies"].append(subpolicy_dict)
                
                policies_data.append(policy_dict)
            
            extracted_data = {
                "FrameworkName": framework.FrameworkName,
                "FrameworkDescription": framework.FrameworkDescription,
                "Category": framework.Category,
                "EffectiveDate": framework.EffectiveDate.isoformat() if framework.EffectiveDate else None,
                "StartDate": framework.StartDate.isoformat() if framework.StartDate else None,
                "EndDate": framework.EndDate.isoformat() if framework.EndDate else None,
                "CreatedByName": framework.CreatedByName,
                "CreatedByDate": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None,
                "Identifier": framework.Identifier,
                "Status": framework.Status,
                "ActiveInactive": framework.ActiveInactive,
                "type": "framework",
                "docURL": framework.DocURL,
                "reviewer": framework.Reviewer,
                "source": "tailoring",
                "policies": policies_data,
                "totalPolicies": len(created_policies),
                "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data)
            }
            
            # Get user ID for framework approval
            user_id = 1  # Default user ID
            created_by_user = Users.objects.filter(UserName=framework.CreatedByName).first()
            if created_by_user:
                user_id = created_by_user.UserId
            
            framework_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version="u1",  # Initial user version
                ApprovedNot=None  # Pending approval
            )
            print(f"Created framework approval: {framework_approval.ApprovalId}")
            
            # --- FIX: Get reviewer email and notification service ---
            from ..notification_service import NotificationService
            notification_service = NotificationService()
            reviewer_email = None
            if reviewer_id:
                reviewer_user_obj = Users.objects.filter(UserId=reviewer_id).first()
                if reviewer_user_obj:
                    reviewer_email = reviewer_user_obj.Email
            # ------------------------------------------------------
            # Send notification to reviewer if email is available
            if reviewer_email:
                print(f"Attempting to send notification to reviewer email: {reviewer_email}")  # Debug log
                notification_data = {
                    'notification_type': 'frameworkSubmitted',
                    'email': reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        framework_data['Reviewer'],  # reviewer_name
                        framework.FrameworkName,  # framework_title
                        framework.CreatedByName,  # submitter_name
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Notification result: {notification_result}")  # Debug log
            else:
                print("No reviewer email available to send notification")  # Debug log
            
            return Response({
                "message": "Tailored framework created successfully",
                "FrameworkId": framework.FrameworkId,
                "FrameworkName": framework.FrameworkName,
                "ApprovalId": framework_approval.ApprovalId,
                "Version": framework_approval.Version,
                "PoliciesCreated": len(created_policies),
                "Status": framework.Status
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        print(f"Error creating tailored framework: {str(e)}")
        print(traceback.format_exc())
        return Response({
            "error": f"Failed to create tailored framework: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_tailored_policy(request):
    """
    Create a new policy from the Tailoring page and automatically create policy approval entry
    This endpoint handles creating a new policy under a selected framework with approval workflow
    """
    try:
        data = request.data
        print(f"Received tailored policy data: {data}")
        
        # Get target framework ID from request
        target_framework_id = data.get('TargetFrameworkId')
        if not target_framework_id:
            return Response({'error': 'TargetFrameworkId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get target framework
        try:
            target_framework = Framework.objects.get(FrameworkId=target_framework_id)
        except Framework.DoesNotExist:
            return Response({'error': 'Target framework not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if policy name is unique within the framework
        policy_name = data.get('PolicyName')
        if not policy_name:
            return Response({'error': 'PolicyName is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if Policy.objects.filter(FrameworkId=target_framework, PolicyName=policy_name).exists():
            return Response({'error': 'A policy with this name already exists in the target framework'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse date fields safely
        start_date = parse_date(data.get('StartDate')) if data.get('StartDate') else None
        end_date = parse_date(data.get('EndDate')) if data.get('EndDate') else None
        
        # Get user information for reviewer assignment
        reviewer_name = data.get('Reviewer', '')
        reviewer_id = 2  # Default reviewer ID
        if reviewer_name:
            reviewer_user = Users.objects.filter(UserName=reviewer_name).first()
            if reviewer_user:
                reviewer_id = reviewer_user.UserId
        
        # Get user ID for policy approval
        user_id = 1  # Default user ID
        created_by_name = data.get('CreatedByName', '')
        if created_by_name:
            created_by_user = Users.objects.filter(UserName=created_by_name).first()
            if created_by_user:
                user_id = created_by_user.UserId
        
        # --- Ensure PolicyCategory Exists ---
        # --- Ensure PolicyCategory Exists ---
        policy_type = data.get('PolicyType', '').strip()
        policy_category = data.get('PolicyCategory', '').strip()
        policy_subcategory = data.get('PolicySubCategory', '').strip()

        # Validate presence if any of them is filled
        if any([policy_type, policy_category, policy_subcategory]):
            if not all([policy_type, policy_category, policy_subcategory]):
                return Response({
                    'error': 'All of PolicyType, PolicyCategory, and PolicySubCategory are required together.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the category exists
            existing_category = PolicyCategory.objects.filter(
                PolicyType=policy_type,
                PolicyCategory=policy_category,
                PolicySubCategory=policy_subcategory
            ).first()

            # If not, insert new category
            if not existing_category:
                try:
                    PolicyCategory.objects.create(
                        PolicyType=policy_type,
                        PolicyCategory=policy_category,
                        PolicySubCategory=policy_subcategory
                    )
                except Exception as e:
                    return Response({
                        'error': f'Failed to insert policy category combination: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)


        
        with transaction.atomic():
            # Create new policy
            new_policy_data = {
                'FrameworkId': target_framework,
                'Status': 'Under Review',
                'PolicyName': policy_name,
                'PolicyDescription': data.get('PolicyDescription', ''),
                'StartDate': start_date,
                'EndDate': end_date,
                'Department': data.get('Department', ''),
                'CreatedByName': created_by_name,
                'CreatedByDate': date.today(),
                'Applicability': data.get('Applicability', ''),
                'DocURL': data.get('DocURL', ''),
                'Scope': data.get('Scope', ''),
                'Objective': data.get('Objective', ''),
                'Identifier': data.get('Identifier', ''),
                'PermanentTemporary': data.get('PermanentTemporary', ''),
                'ActiveInactive': 'InActive',
                'CurrentVersion': 1.0,
                'Reviewer': reviewer_name,
                'CoverageRate': data.get('CoverageRate'),
                # Add policy category fields
                'PolicyType': policy_type,
                'PolicyCategory': policy_category,
                'PolicySubCategory': policy_subcategory,
            }
            
            new_policy = Policy.objects.create(**new_policy_data)
            print(f"Created policy: {new_policy.PolicyName} (ID: {new_policy.PolicyId})")
            # After creating the new policy, send notification to reviewer if email is available
            policy_reviewer_email = None
            if reviewer_name:
                reviewer_user = Users.objects.filter(UserName=reviewer_name).first()
                if reviewer_user:
                    policy_reviewer_email = reviewer_user.Email
            if policy_reviewer_email:
                from ..notification_service import NotificationService
                notification_service = NotificationService()
                notification_data = {
                    'notification_type': 'policySubmitted',
                    'email': policy_reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        reviewer_name,
                        new_policy.PolicyName,
                        new_policy.CreatedByName,
                        (new_policy.EndDate.isoformat() if new_policy.EndDate else '')
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Policy notification result: {notification_result}")
            
            # Create policy version record
                PolicyVersion.objects.create(
                PolicyId=new_policy,
                Version='1.0',
                PolicyName=new_policy.PolicyName,
                CreatedBy=new_policy.CreatedByName,
                CreatedDate=new_policy.CreatedByDate,
                PreviousVersionId=None
             )
            
            # Handle subpolicies
            created_subpolicies = []
            if 'subpolicies' in data and isinstance(data['subpolicies'], list):
                for subpolicy_data in data['subpolicies']:
                    # Skip excluded subpolicies
                    if subpolicy_data.get('exclude', False):
                        continue
                    
                    new_subpolicy_data = {
                        'PolicyId': new_policy,
                        'SubPolicyName': subpolicy_data.get('SubPolicyName', ''),
                        'CreatedByName': new_policy.CreatedByName,
                        'CreatedByDate': new_policy.CreatedByDate,
                        'Identifier': subpolicy_data.get('Identifier', ''),
                        'Description': subpolicy_data.get('Description', ''),
                        'Status': 'Under Review',
                        'PermanentTemporary': subpolicy_data.get('PermanentTemporary', ''),
                        'Control': subpolicy_data.get('Control', '')
                    }
                    
                    new_subpolicy = SubPolicy.objects.create(**new_subpolicy_data)
                    created_subpolicies.append(new_subpolicy)
                    print(f"Created subpolicy: {new_subpolicy.SubPolicyName} (ID: {new_subpolicy.SubPolicyId})")
            
            # Prepare data for policy approval entry
            subpolicies_data = []
            for subpolicy in created_subpolicies:
                subpolicy_dict = {
                    "SubPolicyId": subpolicy.SubPolicyId,
                    "SubPolicyName": subpolicy.SubPolicyName,
                    "CreatedByName": subpolicy.CreatedByName,
                    "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
                    "Identifier": subpolicy.Identifier,
                    "Description": subpolicy.Description,
                    "Status": subpolicy.Status,
                    "PermanentTemporary": subpolicy.PermanentTemporary,
                    "Control": subpolicy.Control
                }
                subpolicies_data.append(subpolicy_dict)
            
            extracted_data = {
                "PolicyId": new_policy.PolicyId,
                "PolicyName": new_policy.PolicyName,
                "PolicyDescription": new_policy.PolicyDescription,
                "Status": new_policy.Status,
                "StartDate": new_policy.StartDate.isoformat() if new_policy.StartDate else None,
                "EndDate": new_policy.EndDate.isoformat() if new_policy.EndDate else None,
                "Department": new_policy.Department,
                "CreatedByName": new_policy.CreatedByName,
                "CreatedByDate": new_policy.CreatedByDate.isoformat() if new_policy.CreatedByDate else None,
                "Applicability": new_policy.Applicability,
                "DocURL": new_policy.DocURL,
                "Scope": new_policy.Scope,
                "Objective": new_policy.Objective,
                "Identifier": new_policy.Identifier,
                "PermanentTemporary": new_policy.PermanentTemporary,
                "ActiveInactive": new_policy.ActiveInactive,
                "Reviewer": new_policy.Reviewer,
                "CoverageRate": new_policy.CoverageRate,
                "CurrentVersion": new_policy.CurrentVersion,
                "type": "policy",
                "source": "tailoring",
                "FrameworkId": target_framework.FrameworkId,
                "FrameworkName": target_framework.FrameworkName,
                "subpolicies": subpolicies_data,
                "totalSubpolicies": len(subpolicies_data)
            }
            
            # Create policy approval entry
            policy_approval = PolicyApproval.objects.create(
                PolicyId=new_policy,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version="u1",  # Initial user version
                ApprovedNot=None  # Pending approval
            )
            print(f"Created policy approval: {policy_approval.ApprovalId}")
            print(f"Policy approval details - PolicyId: {policy_approval.PolicyId}, ReviewerId: {policy_approval.ReviewerId}, Version: {policy_approval.Version}")
            print(f"ExtractedData keys: {list(extracted_data.keys())}")
            
            return Response({
                'message': 'Tailored policy created successfully',
                'PolicyId': new_policy.PolicyId,
                'PolicyName': new_policy.PolicyName,
                'FrameworkId': target_framework.FrameworkId,
                'FrameworkName': target_framework.FrameworkName,
                'ApprovalId': policy_approval.ApprovalId,
                'Version': policy_approval.Version,
                'SubpoliciesCreated': len(created_subpolicies),
                'Status': new_policy.Status
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        print(f"Error creating tailored policy: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': f'Failed to create tailored policy: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def resubmit_policy_approval(request, policy_id):
    """
    Resubmit a rejected policy with updated data
    Creates new PolicyApproval record with incremented version
    """
    try:
        print(f"DEBUG: resubmit_policy_approval called for policy_id: {policy_id}")
        print(f"DEBUG: Request data: {request.data}")
        
        # Get the policy
        policy = Policy.objects.get(PolicyId=policy_id)
        print(f"DEBUG: Found policy with name: {policy.PolicyName}, status: {policy.Status}")
        
        # Verify policy exists and is rejected
        if policy.Status != 'Rejected':
            print(f"DEBUG: Policy status is not 'Rejected', it's '{policy.Status}'")
            return Response({"error": "Only rejected policies can be resubmitted"}, status=400)
        
        # Get the latest PolicyApproval for this policy to determine next version
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy
        ).order_by('-Version').first()
        
        if latest_approval:
            # Parse the version and increment
            current_version = latest_approval.Version or 'u1'
            print(f"DEBUG: Current version: {current_version}")
            
            if current_version.startswith('u'):
                version_num = int(current_version[1:]) + 1
                new_version = f'u{version_num}'
            else:
                new_version = 'u2'
        else:
            new_version = 'u1'
        
        print(f"DEBUG: New version will be: {new_version}")
        
        # Update policy data with submitted changes
        if 'PolicyName' in request.data:
            policy.PolicyName = request.data['PolicyName']
        if 'PolicyDescription' in request.data:
            policy.PolicyDescription = request.data['PolicyDescription']
        if 'Scope' in request.data:
            policy.Scope = request.data['Scope']
        if 'Objective' in request.data:
            policy.Objective = request.data['Objective']
        if 'Department' in request.data:
            policy.Department = request.data['Department']
        if 'Applicability' in request.data:
            policy.Applicability = request.data['Applicability']
        
        # Update policy status to Under Review
        policy.Status = 'Under Review'
        policy.save()
        print(f"DEBUG: Updated policy status to 'Under Review'")
        
        # Process subpolicies if provided
        if 'subpolicies' in request.data and request.data['subpolicies']:
            print(f"DEBUG: Processing {len(request.data['subpolicies'])} subpolicies")
            
            for subpolicy_data in request.data['subpolicies']:
                print(f"DEBUG: Processing subpolicy: {subpolicy_data}")
                
                if 'SubPolicyId' in subpolicy_data and subpolicy_data['SubPolicyId']:
                    try:
                        subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_data['SubPolicyId'])
                        
                        # Update subpolicy fields
                        if 'SubPolicyName' in subpolicy_data:
                            subpolicy.SubPolicyName = subpolicy_data['SubPolicyName']
                        if 'Description' in subpolicy_data:
                            subpolicy.Description = subpolicy_data['Description']
                        if 'Control' in subpolicy_data:
                            subpolicy.Control = subpolicy_data['Control']
                        
                        # Reset subpolicy status to Under Review
                        subpolicy.Status = 'Under Review'
                        subpolicy.save()
                        print(f"DEBUG: Updated subpolicy {subpolicy.SubPolicyId}")
                        
                    except SubPolicy.DoesNotExist:
                        print(f"DEBUG: SubPolicy with ID {subpolicy_data['SubPolicyId']} not found")
        
        # Prepare ExtractedData for the new PolicyApproval
        extracted_data = {
            'PolicyName': policy.PolicyName,
            'PolicyDescription': policy.PolicyDescription,
            'Scope': policy.Scope,
            'Objective': policy.Objective,
            'Department': policy.Department,
            'Applicability': policy.Applicability,
            'Status': 'Under Review',
            'subpolicies': []
        }
        
        # Add subpolicies to ExtractedData
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        for subpolicy in subpolicies:
            extracted_data['subpolicies'].append({
                'SubPolicyId': subpolicy.SubPolicyId,
                'SubPolicyName': subpolicy.SubPolicyName,
                'Description': subpolicy.Description,
                'Control': subpolicy.Control,
                'Status': subpolicy.Status,
                'Identifier': subpolicy.Identifier
            })
        
        print(f"DEBUG: Prepared ExtractedData with {len(extracted_data['subpolicies'])} subpolicies")
        
        # Create new PolicyApproval record
        new_policy_approval = PolicyApproval.objects.create(
            PolicyId=policy,
            ExtractedData=extracted_data,
            Version=new_version,
            UserId=request.data.get('UserId', 1),  # Default to user 1 if not provided
            ReviewerId=None,  # Will be assigned when reviewer picks it up
            ApprovedNot=None,  # Reset approval status
            ApprovedDate=None,
            Identifier=f"POL-{policy.PolicyId}-{new_version}"
        )
        
        print(f"DEBUG: Created new PolicyApproval with ID: {new_policy_approval.ApprovalId}, Version: {new_version}")
        
        # Send notification to reviewer about policy resubmission
        try:
            from ..notification_service import NotificationService
            notification_service = NotificationService()
            reviewer = None
            submitter = None
            if new_policy_approval.ReviewerId:
                reviewer = Users.objects.get(UserId=new_policy_approval.ReviewerId)
            if new_policy_approval.UserId:
                submitter = Users.objects.get(UserId=new_policy_approval.UserId)
            if reviewer and reviewer.Email:
                notification_data = {
                    'notification_type': 'policyResubmitted',
                    'email': reviewer.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        reviewer.UserName,
                        policy.PolicyName,
                        submitter.UserName if submitter else ''
                    ]
                }
                notification_service.send_multi_channel_notification(notification_data)
        except Exception as notify_ex:
            print(f"DEBUG: Error sending policy resubmission notification: {notify_ex}")
        
        return Response({
            "message": "Policy resubmitted successfully",
            "ApprovalId": new_policy_approval.ApprovalId,
            "Version": new_version,
            "Status": "Under Review"
        })
        
    except Policy.DoesNotExist:
        print(f"DEBUG: Policy with ID {policy_id} not found")
        return Response({"error": "Policy not found"}, status=404)
    except Exception as e:
        print(f"DEBUG: Error in resubmit_policy_approval: {str(e)}")
        return Response({"error": str(e)}, status=500)

def update_policy_status_from_subpolicies(policy_id):
    """
    Helper function to update a policy's status based on its subpolicies
    """
    try:
        print(f"DEBUG: Starting update_policy_status_from_subpolicies for policy_id: {policy_id}")
        policy = Policy.objects.get(PolicyId=policy_id)
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        
        print(f"DEBUG: Found {subpolicies.count()} subpolicies for policy {policy_id}")
        
        # Default status if no subpolicies
        if not subpolicies.exists():
            print(f"DEBUG: No subpolicies found for policy {policy_id}, no status change needed")
            return
            
        # Check if any subpolicy is rejected
        any_rejected = False
        all_approved = True
        
        for subpolicy in subpolicies:
            print(f"DEBUG: Checking subpolicy {subpolicy.SubPolicyId} with status: {subpolicy.Status}")
            if subpolicy.Status == 'Rejected':
                any_rejected = True
                all_approved = False
                print(f"DEBUG: Found rejected subpolicy {subpolicy.SubPolicyId}")
                break
            elif subpolicy.Status != 'Approved':
                all_approved = False
                print(f"DEBUG: Found non-approved subpolicy {subpolicy.SubPolicyId} with status: {subpolicy.Status}")
                
        # Update policy status based on subpolicies
        if any_rejected:
            # Always set to rejected if any subpolicy is rejected, regardless of policy status
            if policy.Status != 'Rejected':
                policy.Status = 'Rejected'
                policy.save()
                print(f"DEBUG: Policy {policy_id} status set to Rejected due to rejected subpolicy")
        elif all_approved:
            # Only set to approved if all subpolicies are approved
            print(f"DEBUG: All subpolicies are approved for policy {policy_id}, setting status to Approved")
            policy.Status = 'Approved'
            policy.ActiveInactive = 'Active'  # Also mark as Active when approved
            policy.save()
            print(f"DEBUG: Policy {policy_id} status set to Approved as all subpolicies are approved")
            
            # Deactivate previous versions when a policy is approved
            deactivated_count = deactivate_previous_version_policies(policy_id)
            print(f"DEBUG: Deactivated {deactivated_count} previous versions of policy {policy_id}")
            
    except Policy.DoesNotExist:
        print(f"ERROR: Policy {policy_id} not found")
    except Exception as e:
        print(f"ERROR updating policy status from subpolicies: {str(e)}")


def deactivate_previous_version_policies(policy_id):
    """
    Deactivates previous versions of a policy when a new version is approved.
    
    Args:
        policy_id: The ID of the newly approved policy
        
    Returns:
        int: Number of previous version policies deactivated
    """
    try:
        print(f"DEBUG: Starting deactivate_previous_version_policies for policy_id: {policy_id}")
        
        # Get the current policy
        current_policy = Policy.objects.get(PolicyId=policy_id)
        print(f"DEBUG: Found current policy: {current_policy.PolicyName}, Identifier: {current_policy.Identifier}")
        
        # Get the current policy version
        current_version = PolicyVersion.objects.filter(PolicyId=current_policy).first()
        if not current_version:
            print(f"DEBUG: No version information found for policy {policy_id}")
            return 0
            
        print(f"DEBUG: Current policy version: {current_version.Version}, VersionId: {current_version.VersionId}")
        
        # Check if there's a previous version
        if not current_version.PreviousVersionId:
            print(f"DEBUG: No previous version found for policy {policy_id}")
            return 0
            
        previous_version_id = current_version.PreviousVersionId
        print(f"DEBUG: Found previous version ID: {previous_version_id}")
        
        # Get the previous version record
        previous_version = PolicyVersion.objects.filter(VersionId=previous_version_id).first()
        if not previous_version:
            print(f"DEBUG: Previous version record {previous_version_id} not found")
            return 0
            
        print(f"DEBUG: Previous version policy ID: {previous_version.PolicyId.PolicyId}, Version: {previous_version.Version}")
        
        # Get the previous policy
        previous_policy = previous_version.PolicyId
        if not previous_policy:
            print(f"DEBUG: Previous policy not found")
            return 0
            
        print(f"DEBUG: Deactivating previous policy: {previous_policy.PolicyName}, ID: {previous_policy.PolicyId}")
        
        # Deactivate the previous policy
        previous_policy.ActiveInactive = 'Inactive'
        previous_policy.save()
        
        print(f"DEBUG: Successfully deactivated previous policy {previous_policy.PolicyId} (changed status to Inactive)")
        
        return 1
    except Exception as e:
        print(f"ERROR in deactivate_previous_version_policies: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_categories(request):
    try:
        categories = PolicyCategory.objects.all()
        categories_data = []
        for category in categories:
            categories_data.append({
                'Id': category.Id,
                'PolicyType': category.PolicyType,
                'PolicyCategory': category.PolicyCategory,
                'PolicySubCategory': category.PolicySubCategory
            })
        return Response(categories_data)
    except Exception as e:
        print(f"Error in get_policy_categories: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def save_policy_category(request):
    try:
        policy_type = request.data.get('PolicyType')
        policy_category = request.data.get('PolicyCategory')
        policy_subcategory = request.data.get('PolicySubCategory')

        if not all([policy_type, policy_category, policy_subcategory]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the combination already exists
        existing_category = PolicyCategory.objects.filter(
            PolicyType=policy_type,
            PolicyCategory=policy_category,
            PolicySubCategory=policy_subcategory
        ).first()

        if existing_category:
            return Response({
                "message": "Category combination already exists",
                "category": {
                    'Id': existing_category.Id,
                    'PolicyType': existing_category.PolicyType,
                    'PolicyCategory': existing_category.PolicyCategory,
                    'PolicySubCategory': existing_category.PolicySubCategory
                }
            })

        # Create new category
        new_category = PolicyCategory.objects.create(
            PolicyType=policy_type,
            PolicyCategory=policy_category,
            PolicySubCategory=policy_subcategory
        )

        return Response({
            "message": "Category saved successfully",
            "category": {
                'Id': new_category.Id,
                'PolicyType': new_category.PolicyType,
                'PolicyCategory': new_category.PolicyCategory,
                'PolicySubCategory': new_category.PolicySubCategory
            }
        })

    except Exception as e:
        print(f"Error in save_policy_category: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)