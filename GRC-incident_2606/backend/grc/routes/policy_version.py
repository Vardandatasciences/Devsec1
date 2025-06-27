from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date
from django.shortcuts import get_object_or_404
import traceback
from ..models import Policy, PolicyApproval, SubPolicy, PolicyVersion, Framework, Users


@api_view(['POST'])
@permission_classes([AllowAny])
def create_policy_version(request, policy_id):
    """
    Create a new version of a policy with its subpolicies.
    Integrated from both policy.py and policy_version.py to provide comprehensive versioning functionality.
    This is used from the Versioning.vue component.
    """
    try:
        print(f"DEBUG: Starting policy version creation for policy ID: {policy_id}")
        print(f"DEBUG: Request headers: {request.headers}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request data: {request.data}")
        
        # Get the original policy - use get_object_or_404 for better error handling
        original_policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Verify policy exists and is active
        if original_policy.ActiveInactive != 'Active':
            print(f"DEBUG: Policy with ID {policy_id} is not active, status: {original_policy.ActiveInactive}")
            return Response({"error": "Only active policies can be versioned"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract data from request
        policy_data = request.data
        print(f"DEBUG: Received policy data: {policy_data}")
        
        # Validate policy name
        policy_name = policy_data.get('PolicyName')
        if not policy_name:
            return Response({'error': 'PolicyName is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Start database transaction
        with transaction.atomic():
            print(f"DEBUG: Started transaction for policy version creation")
            
            # Enhanced version calculation logic from policy.py
            current_version = str(original_policy.CurrentVersion).strip()
            
            # Correct version increment logic: find all minor versions as integers and increment
            major_version = current_version.split('.')[0]
            all_versions = PolicyVersion.objects.filter(
                PolicyId__Identifier=original_policy.Identifier,
                Version__startswith=major_version + '.'
            ).values_list('Version', flat=True)
            
            minor_versions = []
            for v in all_versions:
                try:
                    v_str = str(v)  # Convert v to string before splitting
                    parts = v_str.split('.')
                    if len(parts) == 2 and parts[0] == major_version and parts[1].isdigit():
                        minor_versions.append(int(parts[1]))
                except Exception as e:
                    # Skip invalid versions
                    print(f"Skipping invalid version format: {v}, error: {str(e)}")
                    continue
            
            if minor_versions:
                next_minor = max(minor_versions) + 1
            else:
                next_minor = 1
                
            new_version = f"{major_version}.{next_minor}"
            print(f"DEBUG: Creating new policy with version: {new_version}")
            
            # Resolve Reviewer UserName from UserId if given in request, fallback to original
            reviewer_id = policy_data.get('Reviewer')
            reviewer_name = None
            if reviewer_id:
                try:
                    user_obj = Users.objects.filter(UserId=reviewer_id).first()
                    if user_obj:
                        reviewer_name = user_obj.UserName
                except Exception as e:
                    print(f"DEBUG: Error resolving reviewer: {str(e)}")
            if not reviewer_name:
                reviewer_name = original_policy.Reviewer  # fallback to existing username
            
            # Create new policy based on original with updated data
            new_policy = Policy.objects.create(
                FrameworkId=original_policy.FrameworkId,
                PolicyName=policy_name,
                PolicyDescription=policy_data.get('PolicyDescription', original_policy.PolicyDescription),
                Status='Under Review',
                StartDate=policy_data.get('StartDate', original_policy.StartDate),
                EndDate=policy_data.get('EndDate', original_policy.EndDate),
                Department=policy_data.get('Department', original_policy.Department),
                CreatedByName=policy_data.get('CreatedByName', original_policy.CreatedByName),
                CreatedByDate=date.today(),
                Applicability=policy_data.get('Applicability', original_policy.Applicability),
                DocURL=policy_data.get('DocURL', original_policy.DocURL),
                Scope=policy_data.get('Scope', original_policy.Scope),
                Objective=policy_data.get('Objective', original_policy.Objective),
                Identifier=policy_data.get('Identifier', original_policy.Identifier),
                PermanentTemporary=policy_data.get('PermanentTemporary', original_policy.PermanentTemporary),
                ActiveInactive='InActive',  # New versions are inactive and go for approval
                Reviewer=reviewer_name,  # Save UserName here
                CoverageRate=policy_data.get('CoverageRate', original_policy.CoverageRate),
                CurrentVersion=new_version,
                PolicyType=policy_data.get('PolicyType', original_policy.PolicyType),
                PolicyCategory=policy_data.get('PolicyCategory', original_policy.PolicyCategory),
                PolicySubCategory=policy_data.get('PolicySubCategory', original_policy.PolicySubCategory)
            )
            
            print(f"DEBUG: Created new policy with ID: {new_policy.PolicyId}")
            
            # Get original PolicyVersion to link new version
            original_policy_version = PolicyVersion.objects.filter(
                PolicyId=original_policy,
                Version=str(original_policy.CurrentVersion)
            ).first()
            
            if not original_policy_version:
                print(f"WARNING: No PolicyVersion found for PolicyId={original_policy.PolicyId} and Version={original_policy.CurrentVersion}")
                # Create a fallback version record for linking
                original_policy_version = PolicyVersion.objects.filter(
                    PolicyId=original_policy
                ).first()
            
            # Create new PolicyVersion linked to previous
            policy_version = PolicyVersion.objects.create(
                PolicyId=new_policy,
                Version=new_version,
                PolicyName=new_policy.PolicyName,
                CreatedBy=new_policy.CreatedByName,
                CreatedDate=new_policy.CreatedByDate,
                PreviousVersionId=original_policy_version.VersionId if original_policy_version else None
            )
            
            print(f"DEBUG: Created policy version entry with ID: {policy_version.VersionId}")
            
            # Handle subpolicy customizations and new subpolicies
            subpolicy_customizations = {}
            subpolicies_to_exclude = []
            
            if 'subpolicies' in policy_data:
                print(f"DEBUG: Processing {len(policy_data.get('subpolicies', []))} existing subpolicies")
                for sp_data in policy_data.get('subpolicies', []):
                    if 'original_subpolicy_id' in sp_data:
                        sp_id = sp_data.get('original_subpolicy_id')
                        if sp_data.get('exclude', False):
                            subpolicies_to_exclude.append(sp_id)
                        else:
                            if 'Identifier' not in sp_data:
                                return Response({
                                    'error': 'Identifier is required for modified subpolicies',
                                    'subpolicy_id': sp_id
                                }, status=status.HTTP_400_BAD_REQUEST)
                            subpolicy_customizations[sp_id] = sp_data
            
            # Process original subpolicies with customizations
            original_subpolicies = SubPolicy.objects.filter(PolicyId=original_policy)
            for original_subpolicy in original_subpolicies:
                if original_subpolicy.SubPolicyId in subpolicies_to_exclude:
                        continue
                custom_data = subpolicy_customizations.get(original_subpolicy.SubPolicyId, {})
                
                new_subpolicy_data = {
                    'PolicyId': new_policy,
                    'SubPolicyName': custom_data.get('SubPolicyName', original_subpolicy.SubPolicyName),
                    'CreatedByName': new_policy.CreatedByName,
                    'CreatedByDate': new_policy.CreatedByDate,
                    'Identifier': custom_data.get('Identifier', original_subpolicy.Identifier),
                    'Description': custom_data.get('Description', original_subpolicy.Description),
                    'Status': 'Under Review',
                    'PermanentTemporary': custom_data.get('PermanentTemporary', original_subpolicy.PermanentTemporary),
                    'Control': custom_data.get('Control', original_subpolicy.Control)
                }
                
                SubPolicy.objects.create(**new_subpolicy_data)
            
            # Add new subpolicies if any
            if 'new_subpolicies' in policy_data:
                print(f"DEBUG: Processing {len(policy_data.get('new_subpolicies', []))} new subpolicies")
                for new_subpolicy_data in policy_data.get('new_subpolicies', []):
                    required_fields = ['SubPolicyName', 'Description', 'Identifier']
                    missing_fields = [field for field in required_fields if field not in new_subpolicy_data]
                    if missing_fields:
                        return Response({
                            'error': f'Missing required fields for new subpolicy: {", ".join(missing_fields)}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    subpolicy = new_subpolicy_data.copy()
                    subpolicy['PolicyId'] = new_policy
                    if 'CreatedByName' not in subpolicy:
                        subpolicy['CreatedByName'] = new_policy.CreatedByName
                    if 'CreatedByDate' not in subpolicy:
                        subpolicy['CreatedByDate'] = new_policy.CreatedByDate
                    if 'Status' not in subpolicy:
                        subpolicy['Status'] = 'Under Review'
                    
                    SubPolicy.objects.create(**subpolicy)
            
            # Handle any new policies if specified (from policy.py functionality)
            created_policies = []
            if 'new_policies' in policy_data:
                for new_policy_data in policy_data.get('new_policies', []):
                    required_fields = ['PolicyName', 'PolicyDescription', 'Identifier']
                    missing_fields = [field for field in required_fields if field not in new_policy_data]
                    if missing_fields:
                        return Response({
                            'error': f'Missing required fields for new policy: {", ".join(missing_fields)}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    subpolicies_data = new_policy_data.pop('subpolicies', [])
                    policy_data_new = new_policy_data.copy()
                    policy_data_new['FrameworkId'] = original_policy.FrameworkId
                    policy_data_new['CurrentVersion'] = new_version
                    policy_data_new['Status'] = 'Under Review'
                    policy_data_new['ActiveInactive'] = 'Inactive'
                    if 'CreatedByName' not in policy_data_new:
                        policy_data_new['CreatedByName'] = original_policy.CreatedByName
                    if 'CreatedByDate' not in policy_data_new:
                        policy_data_new['CreatedByDate'] = date.today()
                    
                    created_policy = Policy.objects.create(**policy_data_new)
                    created_policies.append(created_policy)
                    
                    PolicyVersion.objects.create(
                        PolicyId=created_policy,
                        Version=new_version,
                        PolicyName=created_policy.PolicyName,
                        CreatedBy=created_policy.CreatedByName,
                        CreatedDate=created_policy.CreatedByDate,
                        PreviousVersionId=None
                    )
                    
                    for subpolicy_data in subpolicies_data:
                        required_fields = ['SubPolicyName', 'Description', 'Identifier']
                        missing_fields = [field for field in required_fields if field not in subpolicy_data]
                        if missing_fields:
                            return Response({
                                'error': f'Missing required fields for subpolicy in new policy {created_policy.PolicyName}: {", ".join(missing_fields)}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        subpolicy = subpolicy_data.copy()
                        subpolicy['PolicyId'] = created_policy
                        if 'CreatedByName' not in subpolicy:
                            subpolicy['CreatedByName'] = created_policy.CreatedByName
                        if 'CreatedByDate' not in subpolicy:
                            subpolicy['CreatedByDate'] = created_policy.CreatedByDate
                        if 'Status' not in subpolicy:
                            subpolicy['Status'] = 'Under Review'
                        
                        SubPolicy.objects.create(**subpolicy)
            
            # Create policy approval entry for the new version
            print(f"DEBUG: Calling create_policy_approval_for_version for new policy ID: {new_policy.PolicyId}")
            approval_created = create_policy_approval_for_version(new_policy.PolicyId)
            print(f"DEBUG: Policy approval creation result: {approval_created}")
            
            # Verify the approval was created
            policy_approval = PolicyApproval.objects.filter(PolicyId=new_policy).first()
            if policy_approval:
                print(f"DEBUG: Verified policy approval was created with ID: {policy_approval.ApprovalId}")
            else:
                print(f"WARNING: Could not verify policy approval creation")
            
            # Prepare response
            response_data = {
                'message': 'New policy version created successfully',
                'PolicyId': new_policy.PolicyId,
                'PolicyName': new_policy.PolicyName,
                'PreviousVersion': current_version,
                'NewVersion': new_version,
                'FrameworkId': new_policy.FrameworkId.FrameworkId if new_policy.FrameworkId else None,
                'Identifier': new_policy.Identifier,
                'Status': new_policy.Status
            }
            
            if created_policies:
                response_data['policies'] = [{
                    'PolicyId': p.PolicyId,
                    'PolicyName': p.PolicyName,
                    'Identifier': p.Identifier,
                    'Version': p.CurrentVersion
                } for p in created_policies]
            
            # Send notification if reviewer is assigned
            if reviewer_name and reviewer_id:
                try:
                    from ..notification_service import NotificationService
                    notification_service = NotificationService()
                    
                    # Get reviewer's email
                    reviewer_email = None
                    reviewer = Users.objects.filter(UserId=reviewer_id).first()
                    if reviewer:
                        reviewer_email = reviewer.Email
                    
                    if reviewer_email:
                        notification_data = {
                            'notification_type': 'policyNewVersion',
                            'email': reviewer_email,
                            'email_type': 'gmail',
                            'template_data': [
                                reviewer_name,
                                new_policy.PolicyName,
                                new_version,
                                new_policy.CreatedByName
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                except Exception as e:
                    print(f"Failed to send notification: {str(e)}")
            
            # Note: Previous policy version will be set to inactive only when this new version is approved
            # This allows both versions to be active during the approval process
            
            return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Policy.DoesNotExist:
        print(f"ERROR: Original policy with ID {policy_id} not found")
        return Response({"error": "Original policy not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"ERROR in create_policy_version: {str(e)}")
        traceback.print_exc()
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error creating new policy version', 'details': error_info}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_policy_approval_for_version(policy_id):
    """
    Helper function to create a policy approval entry for a new policy version
    """
    try:
        # Get the policy
        policy = Policy.objects.get(PolicyId=policy_id)
        print(f"DEBUG: Starting policy approval creation for policy ID: {policy_id}, Name: {policy.PolicyName}")
        
        # Collect subpolicies data for approval JSON
        subpolicies_data = []
        created_subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        
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
        
        # Get framework info if available
        framework_info = {}
        if policy.FrameworkId:
            framework = policy.FrameworkId
            framework_info = {
                "FrameworkId": framework.FrameworkId,
                "FrameworkName": framework.FrameworkName,
                "Category": framework.Category
            }
        
        # Prepare the extracted data for the approval
        extracted_data = {
            "PolicyId": policy.PolicyId,
            "PolicyName": policy.PolicyName,
            "PolicyDescription": policy.PolicyDescription,
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
            "Status": policy.Status,
            "PermanentTemporary": policy.PermanentTemporary,
            "ActiveInactive": policy.ActiveInactive,
            "type": "policy",
            "source": "versioning",
            "reviewer": policy.Reviewer,
            "CoverageRate": policy.CoverageRate,
            "CurrentVersion": policy.CurrentVersion,
            "subpolicies": subpolicies_data,
            "totalSubpolicies": len(subpolicies_data),
            "framework": framework_info
        }
        
        # Get policy version info
        policy_version = PolicyVersion.objects.filter(PolicyId=policy).first()
        if policy_version:
            extracted_data["Version"] = policy_version.Version
            extracted_data["PreviousVersionId"] = policy_version.PreviousVersionId
        
        print(f"DEBUG: Prepared extracted data for policy approval")
        
        # Determine reviewer ID
        reviewer_id = 2  # Default reviewer ID
        if policy.Reviewer:
            # Check if Reviewer is already a numeric ID
            if isinstance(policy.Reviewer, int) or (isinstance(policy.Reviewer, str) and policy.Reviewer.isdigit()):
                reviewer_id = int(policy.Reviewer)
            else:
                # Try to find the reviewer by name in the Users table
                try:
                    user = Users.objects.filter(UserName=policy.Reviewer).first()
                    if user:
                        reviewer_id = user.UserId
                except Exception as e:
                    print(f"DEBUG: Error finding reviewer by name: {str(e)}")
            
        print(f"DEBUG: Using reviewer ID: {reviewer_id}")
        
        # Create the policy approval with direct SQL debug to verify it's working
        try:
            approval = PolicyApproval.objects.create(
                PolicyId=policy,
                ExtractedData=extracted_data,
                UserId=1,  # Default user id
                ReviewerId=reviewer_id,
                Version="u1",  # Default initial version
                ApprovedNot=None  # Not yet approved
            )
            print(f"DEBUG: Successfully created policy approval with ID: {approval.ApprovalId}")
            
            # Verify the approval was created
            verification = PolicyApproval.objects.filter(PolicyId=policy).exists()
            print(f"DEBUG: Verification of policy approval creation: {verification}")
            
            return True
        except Exception as create_error:
            print(f"ERROR creating policy approval record: {str(create_error)}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"ERROR in create_policy_approval_for_version: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_versions(request, policy_id=None):
    """
    Get all versions of a policy by its Identifier
    """
    try:
        if policy_id:
            # Get the policy to find its identifier
            policy = Policy.objects.get(PolicyId=policy_id)
            identifier = policy.Identifier
            
            # Find all policies with this identifier
            policies = Policy.objects.filter(Identifier=identifier).order_by('-PolicyId')
            
            # Get the version information for each policy
            versions_data = []
            for pol in policies:
                version_info = PolicyVersion.objects.filter(PolicyId=pol).first()
                if version_info:
                    versions_data.append({
                        "PolicyId": pol.PolicyId,
                        "PolicyName": pol.PolicyName,
                        "Version": version_info.Version,
                        "CreatedBy": version_info.CreatedBy,
                        "CreatedDate": version_info.CreatedDate.isoformat() if version_info.CreatedDate else None,
                        "Status": pol.Status,
                        "ActiveInactive": pol.ActiveInactive
                    })
                else:
                    # Handle policies without version information
                    versions_data.append({
                        "PolicyId": pol.PolicyId,
                        "PolicyName": pol.PolicyName,
                        "Version": pol.CurrentVersion,
                        "CreatedBy": pol.CreatedByName,
                        "CreatedDate": pol.CreatedByDate.isoformat() if pol.CreatedByDate else None,
                        "Status": pol.Status,
                        "ActiveInactive": pol.ActiveInactive
                    })
            
            return Response(versions_data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Policy ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Policy.DoesNotExist:
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_policy_versions(request):
    """
    Get all policy versions in the system
    """
    try:
        print(f"DEBUG: Starting get_all_policy_versions")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request params: {request.GET}")
        
        # Get all policy versions
        policy_versions = PolicyVersion.objects.all().order_by('-CreatedDate')
        print(f"DEBUG: Found {policy_versions.count()} policy versions")
        
        versions_data = []
        for version in policy_versions:
            policy = version.PolicyId
            if policy:
                versions_data.append({
                    "VersionId": version.VersionId,
                    "PolicyId": policy.PolicyId,
                    "PolicyName": policy.PolicyName,
                    "Version": version.Version,
                    "PreviousVersionId": version.PreviousVersionId,
                    "CreatedBy": version.CreatedBy,
                    "CreatedDate": version.CreatedDate.isoformat() if version.CreatedDate else None,
                    "Status": policy.Status,
                    "ActiveInactive": policy.ActiveInactive
                })
        
        print(f"DEBUG: Returning {len(versions_data)} policy versions")
        return Response(versions_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"ERROR in get_all_policy_versions: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_rejected_policy_versions(request, user_id=None):
    """
    Get all rejected policy versions for a specific user that can be edited and resubmitted
    """
    try:
        if not user_id:
            user_id = request.GET.get('user_id', None)
            
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get all policy approvals where:
        # 1. The approval is rejected (ApprovedNot=False)
        # 2. The version starts with 'r' (reviewer version)
        # 3. If user_id is provided, filter by UserId
        query_filters = {
            'ApprovedNot': False,
            'Version__startswith': 'r'
        }
        
        if user_id:
            query_filters['UserId'] = user_id
            
        rejections = PolicyApproval.objects.filter(**query_filters).order_by('-ApprovalId')
        
        # Group by PolicyId to get only the latest rejection for each policy
        policy_rejections = {}
        for rejection in rejections:
            if not rejection.PolicyId:
                continue
                
            policy_id = rejection.PolicyId.PolicyId
            if policy_id not in policy_rejections:
                policy_rejections[policy_id] = rejection
        
        # Format response
        rejected_policies = []
        for rejection in policy_rejections.values():
            policy = rejection.PolicyId
            if not policy:
                continue
                
            # Get version info - handle cases where version info might not exist
            try:
                version_info = PolicyVersion.objects.filter(PolicyId=policy).first()
                version = version_info.Version if version_info else policy.CurrentVersion
            except (AttributeError, Exception) as e:
                print(f"Error getting version info: {str(e)}")
                version = "Unknown"
                
            # Handle potential missing dates
            try:
                created_date = policy.CreatedByDate.isoformat() if policy.CreatedByDate else None
            except (AttributeError, Exception):
                created_date = None
                
            # Safely extract rejection reason
            try:
                rejection_reason = rejection.ExtractedData.get('policy_approval', {}).get('remarks', 'No reason provided')
            except (AttributeError, TypeError, Exception):
                rejection_reason = 'No reason provided'
            
            rejection_data = {
                "ApprovalId": rejection.ApprovalId,
                "PolicyId": policy.PolicyId,
                "PolicyName": policy.PolicyName,
                "Version": version,
                "Status": policy.Status,
                "CreatedByName": policy.CreatedByName,
                "CreatedDate": created_date,
                "ExtractedData": rejection.ExtractedData or {},
                "RejectionReason": rejection_reason
            }
            
            rejected_policies.append(rejection_data)
        
        return Response(rejected_policies, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR in get_rejected_policy_versions: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['PUT'])
@permission_classes([AllowAny])
def activate_deactivate_policy(request, policy_id):
    """
    Activate or deactivate a policy.
    When activating a policy, all previous versions with the same Identifier will be deactivated.
    """
    try:
        policy = Policy.objects.get(PolicyId=policy_id)
        action = request.data.get('action')
        
        if action == 'activate':
            # Use transaction to ensure atomicity
            with transaction.atomic():
                policy.ActiveInactive = 'Active'
                policy.save()
                
                # When activating a policy, deactivate all previous versions
                deactivated_count = deactivate_previous_policy_versions_on_approval(policy)
                print(f"Policy {policy_id} activated. Deactivated {deactivated_count} previous versions.")
            
            return Response({
                "message": f"Policy activated successfully. {deactivated_count} previous versions deactivated.",
                "PolicyId": policy.PolicyId,
                "ActiveInactive": policy.ActiveInactive,
                "deactivated_previous_versions": deactivated_count
            }, status=status.HTTP_200_OK)
            
        elif action == 'deactivate':
            policy.ActiveInactive = 'Inactive'
            policy.save()
            
            return Response({
                "message": "Policy deactivated successfully",
                "PolicyId": policy.PolicyId,
                "ActiveInactive": policy.ActiveInactive
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid action. Use 'activate' or 'deactivate'"}, status=status.HTTP_400_BAD_REQUEST)
        
    except Policy.DoesNotExist:
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])
def approve_policy_version(request, policy_id):
    """
    Approve a policy version and automatically deactivate all previous versions.
    This endpoint is specifically designed for the Versioning.vue component.
    
    When a policy version (e.g., 6.4) is approved, all previous versions (6.3, 6.2, etc.) 
    with the same Identifier will be set to ActiveInactive='Inactive'.
    """
    try:
        print(f"Approving policy version: {policy_id}")
        
        # Get the policy
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Check if policy can be approved
        if policy.Status == 'Approved':
            return Response({
                "message": "Policy is already approved",
                "PolicyId": policy.PolicyId,
                "Status": policy.Status
            }, status=status.HTTP_200_OK)
        
        # Start database transaction
        with transaction.atomic():
            # Update policy status to Approved and Active
            policy.Status = 'Approved'
            policy.ActiveInactive = 'Active'
            policy.save()
            
            print(f"Policy {policy_id} approved and set to active")
            
            # Deactivate all previous versions with the same Identifier
            deactivated_count = 0
            if policy.Identifier:
                previous_policies = Policy.objects.filter(
                    Identifier=policy.Identifier,
                    ActiveInactive='Active'  # Only get currently active policies
                ).exclude(
                    PolicyId=policy_id
                )
                
                print(f"Found {previous_policies.count()} active previous versions to deactivate for policy {policy.PolicyName} (ID: {policy_id})")
                
                for prev_policy in previous_policies:
                    print(f"Deactivating previous policy version: PolicyId={prev_policy.PolicyId}, Version={prev_policy.CurrentVersion}, Name={prev_policy.PolicyName}")
                    
                    prev_policy.ActiveInactive = 'Inactive'
                    prev_policy.save()
                    deactivated_count += 1
                    
                    print(f"Successfully deactivated policy {prev_policy.PolicyId}")
                    
                    # Also deactivate subpolicies of the previous version
                    prev_subpolicies = SubPolicy.objects.filter(PolicyId=prev_policy)
                    subpolicy_count = 0
                    for prev_subpolicy in prev_subpolicies:
                        if hasattr(prev_subpolicy, 'ActiveInactive'):
                            prev_subpolicy.ActiveInactive = 'Inactive'
                            prev_subpolicy.save()
                            subpolicy_count += 1
                    
                    if subpolicy_count > 0:
                        print(f"Deactivated {subpolicy_count} subpolicies for previous policy {prev_policy.PolicyId}")
            else:
                print(f"Warning: Policy {policy_id} has no Identifier, cannot deactivate previous versions")
            
            # Update all subpolicies for the current policy to Approved
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                subpolicy.Status = 'Approved'
                if hasattr(subpolicy, 'ActiveInactive'):
                    subpolicy.ActiveInactive = 'Active'
                subpolicy.save()
                print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Approved")
            
            # Update the policy approval record if it exists
            try:
                policy_approval = PolicyApproval.objects.filter(
                    PolicyId=policy,
                    ApprovedNot__isnull=True  # Get the pending approval
                ).order_by('-ApprovalId').first()
                
                if policy_approval:
                    policy_approval.ApprovedNot = True
                    policy_approval.save()
                    print(f"Updated policy approval record {policy_approval.ApprovalId}")
            except Exception as approval_error:
                print(f"Error updating policy approval record: {str(approval_error)}")
                # Don't fail the whole operation if approval record update fails
            
            return Response({
                "message": f"Policy approved successfully. {deactivated_count} previous versions deactivated.",
                "PolicyId": policy_id,
                "Status": "Approved",
                "ActiveInactive": "Active",
                "deactivated_previous_versions": deactivated_count
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error approving policy version: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def update_policy_status_based_on_subpolicies(policy_id):
    """
    Update policy status based on its subpolicies statuses
    """
    try:
        policy = Policy.objects.get(PolicyId=policy_id)
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        
        # Check if any subpolicy is rejected
        has_rejected = False
        for subpolicy in subpolicies:
            if subpolicy.Status == 'Rejected':
                has_rejected = True
                break
        
        # Update policy status if any subpolicy is rejected
        if has_rejected:
            policy.Status = 'Rejected'
            policy.save()
            print(f"DEBUG: Updated policy {policy_id} status to Rejected due to rejected subpolicy")
            return True
        
        return False
    except Exception as e:
        print(f"ERROR updating policy status based on subpolicies: {str(e)}")
        return False


def deactivate_previous_policy_versions_on_approval(current_policy):
    """
    Deactivate all previous versions of a policy when a new version is approved.
    This function is specifically for use in the policy versioning workflow.
    
    Args:
        current_policy: The newly approved policy object
        
    Returns:
        int: Number of previous versions deactivated
    """
    print(f"Policy versioning: Deactivating previous versions for policy: PolicyId={current_policy.PolicyId}, Identifier={current_policy.Identifier}")
    
    if not current_policy.Identifier:
        print("Warning: Policy has no Identifier, cannot find previous versions")
        return 0
    
    try:
        # Find all policies with the same Identifier, excluding the current one
        previous_policies = Policy.objects.filter(
            Identifier=current_policy.Identifier
        ).exclude(
            PolicyId=current_policy.PolicyId
        )
        
        print(f"Found {previous_policies.count()} previous versions to check for deactivation")
        
        deactivated_count = 0
        for prev_policy in previous_policies:
            if prev_policy.ActiveInactive == 'Active':
                print(f"Deactivating policy: PolicyId={prev_policy.PolicyId}, Version={prev_policy.CurrentVersion}")
                
                # Set to Inactive but keep the Status unchanged
                prev_policy.ActiveInactive = 'Inactive'
                prev_policy.save()
                deactivated_count += 1
                
                print(f"Successfully deactivated policy {prev_policy.PolicyId}")
                
                # Also deactivate all subpolicies of this previous version
                prev_subpolicies = SubPolicy.objects.filter(PolicyId=prev_policy)
                for prev_subpolicy in prev_subpolicies:
                    if hasattr(prev_subpolicy, 'ActiveInactive'):
                        prev_subpolicy.ActiveInactive = 'Inactive'
                        prev_subpolicy.save()
                        print(f"Deactivated subpolicy {prev_subpolicy.SubPolicyId} of previous policy {prev_policy.PolicyId}")
            else:
                print(f"Policy {prev_policy.PolicyId} is already inactive, skipping")
        
        print(f"Policy versioning: Successfully deactivated {deactivated_count} previous policy versions")
        return deactivated_count
        
    except Exception as e:
        print(f"Error deactivating previous policy versions in versioning: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def approve_policy_version_and_deactivate_previous(policy_id, approval_data):
    """
    Approve a policy version and automatically deactivate previous versions.
    This function can be called when a policy version is approved through the versioning workflow.
    
    Args:
        policy_id: The ID of the policy to approve
        approval_data: Data related to the approval
        
    Returns:
        dict: Result of the approval process
    """
    try:
        # Get the policy
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Update policy status to Approved and Active
            policy.Status = 'Approved'
            policy.ActiveInactive = 'Active'
            policy.save()
            
            print(f"Policy {policy_id} approved and set to active")
            
            # Deactivate all previous versions
            deactivated_count = deactivate_previous_policy_versions_on_approval(policy)
            
            # Update all subpolicies for this policy to Approved
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                subpolicy.Status = 'Approved'
                if hasattr(subpolicy, 'ActiveInactive'):
                    subpolicy.ActiveInactive = 'Active'
                subpolicy.save()
                print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Approved")
        
        return {
            'success': True,
            'message': f'Policy approved successfully. {deactivated_count} previous versions deactivated.',
            'deactivated_count': deactivated_count,
            'policy_id': policy_id
        }
        
    except Exception as e:
        print(f"Error approving policy version: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }