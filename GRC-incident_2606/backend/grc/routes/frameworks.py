from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from ..models import Framework, FrameworkApproval, Policy, SubPolicy, PolicyApproval, FrameworkVersion,Users
import json
from datetime import datetime
from django.db import connection
from ..notification_service import NotificationService  # Add this import


def get_next_reviewer_version(framework):
    """
    Helper function to determine the next reviewer version for a framework
    """
    # Check if there's already a reviewer version for this framework
    latest_reviewer_version = FrameworkApproval.objects.filter(
        FrameworkId=framework,
        Version__startswith='r'
    ).order_by('-ApprovalId').first()
    
    if latest_reviewer_version:
        # Increment the existing reviewer version
        try:
            version_num = int(latest_reviewer_version.Version[1:])
            return f'r{version_num + 1}'
        except ValueError:
            return 'r1'
    else:
        # First reviewer version
        return 'r1'


def get_next_policy_reviewer_version(policy):
    """
    Helper function to determine the next reviewer version for a policy
    """
    # Check if there's already a reviewer version for this policy
    latest_reviewer_version = PolicyApproval.objects.filter(
        PolicyId=policy,
        Version__startswith='r'
    ).order_by('-ApprovalId').first()
    
    if latest_reviewer_version:
        # Increment the existing reviewer version
        try:
            version_num = int(latest_reviewer_version.Version[1:])
            return f'r{version_num + 1}'
        except ValueError:
            return 'r1'
    else:
        # First reviewer version
        return 'r1'


@api_view(['POST'])
@permission_classes([AllowAny])
def create_framework_approval(request, framework_id):
    """
    Create a framework approval entry when a new framework is created
    """
    try:
        # Get the framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Extract data for the approval
        user_id = request.data.get('UserId', 1)  # Default to 1 if not provided
        reviewer_id = framework.Reviewer if framework.Reviewer else request.data.get('ReviewerId', 2)  # Default to 2
        
        # Collect policies and subpolicies data for approval JSON
        policies_data = []
        created_policies = Policy.objects.filter(FrameworkId=framework)
        
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
            "source": "manual_approval",
            "policies": policies_data,
            "totalPolicies": len(policies_data),
            "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data)
        }
        
        # Create the framework approval
        framework_approval = FrameworkApproval.objects.create(
            FrameworkId=framework,
            ExtractedData=extracted_data,
            UserId=user_id,
            ReviewerId=reviewer_id,
            Version="u1",  # Default initial version
            ApprovedNot=None  # Not yet approved
        )
        
        return Response({
            "message": "Framework approval created successfully",
            "ApprovalId": framework_approval.ApprovalId,
            "Version": framework_approval.Version
        }, status=status.HTTP_201_CREATED)
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_framework_approvals(request, framework_id=None):
    """
    Get all framework approvals or approvals for a specific framework
    """
    try:
        if framework_id:
            approvals = FrameworkApproval.objects.filter(FrameworkId=framework_id)
        else:
            approvals = FrameworkApproval.objects.all()
            
        approvals_data = []
        for approval in approvals:
            approval_data = {
                "ApprovalId": approval.ApprovalId,
                "FrameworkId": approval.FrameworkId.FrameworkId if approval.FrameworkId else None,
                "ExtractedData": approval.ExtractedData,
                "UserId": approval.UserId,
                "ReviewerId": approval.ReviewerId,
                "Version": approval.Version,
                "ApprovedNot": approval.ApprovedNot,
                "ApprovedDate": approval.ApprovedDate.isoformat() if approval.ApprovedDate else None
            }
            
            # If this is an approved framework, also include its policies
            if approval.ApprovedNot is True:
                policies = Policy.objects.filter(FrameworkId=approval.FrameworkId)
                policies_data = []
                
                for policy in policies:
                    policy_data = {
                        "PolicyId": policy.PolicyId,
                        "PolicyName": policy.PolicyName,
                        "Status": policy.Status
                    }
                    policies_data.append(policy_data)
                
                approval_data["policies"] = policies_data
            
            approvals_data.append(approval_data)
            
        return Response(approvals_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_framework_approval(request, approval_id):
    """
    Update a framework approval status
    """
    try:
        approval = FrameworkApproval.objects.get(ApprovalId=approval_id)
        
        # Update approval status
        approved = request.data.get('ApprovedNot')
        if approved is not None:
            approval.ApprovedNot = approved
            
            # If approved, set approval date
            if approved:
                approval.ApprovedDate = timezone.now().date()
                
                # Also update the framework status
                if approval.FrameworkId:
                    framework = approval.FrameworkId
                    framework.Status = 'Approved'
                    
                    # Check if the framework is inactive, and update Status accordingly
                    if framework.ActiveInactive == 'Inactive':
                        framework.Status = 'Inactive'
                        
                        # Also update the ExtractedData
                        if extracted_data:
                            # If extracted_data was provided in the request
                            if 'ActiveInactive' in extracted_data and extracted_data['ActiveInactive'] == 'Inactive':
                                extracted_data['Status'] = 'Inactive'
                        elif 'ActiveInactive' in approval.ExtractedData and approval.ExtractedData['ActiveInactive'] == 'Inactive':
                            # If using existing ExtractedData
                            approval.ExtractedData['Status'] = 'Inactive'
                    
                    framework.save()
            elif approved is False:
                # If rejected, update framework status
                if approval.FrameworkId:
                    framework = approval.FrameworkId
                    framework.Status = 'Rejected'
                    framework.save()
        
        # Update extracted data if provided
        extracted_data = request.data.get('ExtractedData')
        if extracted_data:
            approval.ExtractedData = extracted_data
            
        approval.save()
        
        return Response({
            "message": "Framework approval updated successfully",
            "ApprovalId": approval.ApprovalId,
            "ApprovedNot": approval.ApprovedNot,
            "ApprovedDate": approval.ApprovedDate.isoformat() if approval.ApprovedDate else None
        }, status=status.HTTP_200_OK)
        
    except FrameworkApproval.DoesNotExist:
        return Response({"error": "Framework approval not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_framework_review(request, framework_id):
    """
    Submit a review for a framework
    """
    try:
        print(f"submit_framework_review called for framework_id: {framework_id}")
        print(f"Request data: {request.data}")
        
        framework = Framework.objects.get(FrameworkId=framework_id)
        print(f"Found framework: {framework.FrameworkName}, current status: {framework.Status}")
        
        # Get current version info
        current_version = request.data.get('currentVersion', 'u1')
        user_id = request.data.get('UserId', 1)
        reviewer_id = request.data.get('ReviewerId', 2)
        approved = request.data.get('ApprovedNot')
        extracted_data = request.data.get('ExtractedData')
        remarks = request.data.get('remarks', '')
        
        print(f"Processing: version={current_version}, approved={approved}, type={type(approved)}")
        
        # Validate required data
        if extracted_data is None:
            return Response({"error": "ExtractedData is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert boolean/null to proper values
        if approved == 'true' or approved is True:
            approved = True
        elif approved == 'false' or approved is False:
            approved = False
        else:
            approved = None
            
        print(f"Normalized approved value: {approved}, type={type(approved)}")
        
        # Create or update the framework approval
        with transaction.atomic():
            # Determine the next version
            # Check if there's already a reviewer version for this framework
            latest_reviewer_version = FrameworkApproval.objects.filter(
                FrameworkId=framework,
                Version__startswith='r'
            ).order_by('-ApprovalId').first()
            
            if latest_reviewer_version:
                # Increment the existing reviewer version
                try:
                    version_num = int(latest_reviewer_version.Version[1:])
                    new_version = f'r{version_num + 1}'
                except ValueError:
                    new_version = 'r1'
            else:
                # First reviewer version
                new_version = 'r1'
            
            # Create a new approval record with the reviewer version
            new_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version=new_version,
                ApprovedNot=approved
            )
            
            # Set approval date if approved
            if approved:
                new_approval.ApprovedDate = timezone.now().date()
                new_approval.save()
                
                # Update framework status
                framework.Status = 'Approved'
                
                # Ensure CurrentVersion is preserved during approval
                # We do this by not touching the CurrentVersion field
                # or by setting it explicitly from the framework version record
                current_framework_version = FrameworkVersion.objects.filter(
                    FrameworkId=framework
                ).first()
                if current_framework_version:
                    print(f"Setting CurrentVersion to {current_framework_version.Version} for framework {framework_id}")
                    framework.CurrentVersion = current_framework_version.Version
                    
                    # Update all policies to have the same CurrentVersion
                    policies = Policy.objects.filter(FrameworkId=framework)
                    for policy in policies:
                        policy.CurrentVersion = str(float(current_framework_version.Version))
                        print(f"Setting CurrentVersion to {policy.CurrentVersion} for policy {policy.PolicyId}")
                        policy.save()
                
                # Check if the framework is inactive, and update Status accordingly
                if framework.ActiveInactive == 'Inactive':
                    framework.Status = 'Inactive'
                    # Also update the ExtractedData
                    if 'ActiveInactive' in extracted_data and extracted_data['ActiveInactive'] == 'Inactive':
                        extracted_data['Status'] = 'Inactive'
                
                # Send notification to submitter about framework approval
                try:
                    notification_service = NotificationService()
                    submitter = Users.objects.get(UserId=user_id)
                    reviewer = Users.objects.get(UserId=reviewer_id)
                    approval_date = timezone.now().date().isoformat()
                    notification_data = {
                        'notification_type': 'frameworkFinalApproved',
                        'email': submitter.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            submitter.UserName,
                            framework.FrameworkName,
                            reviewer.UserName,
                            approval_date
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                except Exception as notify_ex:
                    print(f"DEBUG: Error sending framework approval notification: {notify_ex}")
                
                # IMPORTANT: Deactivate previous versions of this framework
                print("\n--- STARTING PREVIOUS VERSION DEACTIVATION ---")
                
                previous_frameworks_deactivated = []
                
                # Method 1: Use the FrameworkVersion.PreviousVersionId relationship
                print("DEBUG: Method 1 - Using PreviousVersionId relationship")
                try:
                    # Get the version record for the current framework
                    current_framework_version = FrameworkVersion.objects.filter(
                        FrameworkId=framework
                    ).first()
                    
                    if current_framework_version:
                        print(f"DEBUG: Current framework {framework_id} has version record: ID={current_framework_version.VersionId}, Version={current_framework_version.Version}, PreviousVersionId={current_framework_version.PreviousVersionId}")
                        
                        # First, try using PreviousVersionId
                        if current_framework_version.PreviousVersionId:
                            try:
                                # Get the previous version record
                                previous_version = FrameworkVersion.objects.get(
                                    VersionId=current_framework_version.PreviousVersionId
                                )
                                
                                if previous_version and previous_version.FrameworkId:
                                    previous_framework_id = previous_version.FrameworkId.FrameworkId
                                    print(f"DEBUG: Previous version points to framework ID: {previous_framework_id}")
                                    
                                    previous_framework = previous_version.FrameworkId
                                    
                                    print(f"DEBUG: Previous framework {previous_framework_id} status before update: {previous_framework.ActiveInactive}")
                                    previous_framework.ActiveInactive = 'Inactive'
                                    # Make sure Status remains 'Approved' if it was already approved
                                    if previous_framework.Status == 'Approved':
                                        # Don't change the Status, leave it as 'Approved'
                                        print(f"DEBUG: Keeping Status 'Approved' for framework {previous_framework_id}")
                                    previous_framework.save()
                                    
                                    # Verify the update
                                    previous_framework.refresh_from_db()
                                    print(f"DEBUG: Previous framework {previous_framework_id} status after update: {previous_framework.ActiveInactive}, Status: {previous_framework.Status}")
                                    
                                    # Set all policies of the previous framework to inactive
                                    previous_policies = Policy.objects.filter(FrameworkId=previous_framework)
                                    for prev_policy in previous_policies:
                                        prev_policy.ActiveInactive = 'Inactive'
                                        # Don't change Status if it's already Approved
                                        if prev_policy.Status == 'Approved':
                                            print(f"DEBUG: Keeping Status 'Approved' for policy {prev_policy.PolicyId}")
                                        # Don't change CurrentVersion value
                                        print(f"DEBUG: Preserving CurrentVersion {prev_policy.CurrentVersion} for policy {prev_policy.PolicyId}")
                                        prev_policy.save()
                                    
                                    print(f"DEBUG: Using PreviousVersionId: Deactivated framework {previous_framework_id} and its {previous_policies.count()} policies")
                                    previous_frameworks_deactivated.append(int(previous_framework_id))
                            except FrameworkVersion.DoesNotExist:
                                print(f"DEBUG: Previous version record with ID {current_framework_version.PreviousVersionId} not found")
                    else:
                        print(f"DEBUG: No FrameworkVersion record found for framework {framework_id}")
                except Exception as e:
                    print(f"DEBUG: Error in Method 1: {str(e)}")
                
                # Method 2: Fallback method - direct check and update for frameworks with same identifier
                print("\nDEBUG: Method 2 - Fallback direct check for frameworks with same identifier")
                try:
                    # Get the identifier of the current framework
                    current_identifier = framework.Identifier
                    print(f"DEBUG: Current framework identifier: {current_identifier}")
                    
                    # Find all frameworks with this identifier except the current one
                    other_frameworks = Framework.objects.filter(
                        Identifier=current_identifier
                    ).exclude(FrameworkId=framework_id)
                    
                    print(f"DEBUG: Found {other_frameworks.count()} other frameworks with the same identifier")
                    
                    for other_framework in other_frameworks:
                        # Skip if already deactivated
                        if int(other_framework.FrameworkId) in previous_frameworks_deactivated:
                            print(f"DEBUG: Framework {other_framework.FrameworkId} already processed, skipping")
                            continue
                        
                        print(f"DEBUG: Framework {other_framework.FrameworkId} status before update: {other_framework.ActiveInactive}")
                        
                        # Set to inactive
                        other_framework.ActiveInactive = 'Inactive'
                        # Make sure Status remains 'Approved' if it was already approved
                        if other_framework.Status == 'Approved':
                            # Don't change the Status, leave it as 'Approved'
                            print(f"DEBUG: Keeping Status 'Approved' for framework {other_framework.FrameworkId}")
                        other_framework.save()
                        
                        # Verify the update
                        other_framework.refresh_from_db()
                        print(f"DEBUG: Framework {other_framework.FrameworkId} status after update: {other_framework.ActiveInactive}, Status: {other_framework.Status}")
                        
                        # Set all policies to inactive
                        other_policies = Policy.objects.filter(FrameworkId=other_framework)
                        for other_policy in other_policies:
                            other_policy.ActiveInactive = 'Inactive'
                            # Don't change Status if it's already Approved
                            if other_policy.Status == 'Approved':
                                print(f"DEBUG: Keeping Status 'Approved' for policy {other_policy.PolicyId}")
                            # Don't change CurrentVersion value
                            print(f"DEBUG: Preserving CurrentVersion {other_policy.CurrentVersion} for policy {other_policy.PolicyId}")
                            other_policy.save()
                        
                        print(f"DEBUG: By direct check: Deactivated framework {other_framework.FrameworkId} and its {other_policies.count()} policies")
                        previous_frameworks_deactivated.append(int(other_framework.FrameworkId))
                except Exception as e:
                    print(f"DEBUG: Error in Method 2: {str(e)}")
                
                # Log summary of what was deactivated
                print(f"\nDEBUG: Deactivated frameworks: {previous_frameworks_deactivated}")
                
                # Approve all policies and subpolicies associated with this framework
                policies = Policy.objects.filter(FrameworkId=framework)
                print(f"Approving {policies.count()} policies for framework {framework_id}")
                
                # Update all policies in the database
                for policy in policies:
                    policy.Status = 'Approved'
                    policy.ActiveInactive = 'Active'  # Set policies to Active
                    # 🔁 Patch to pull updated values from ExtractedData
                    for pol_data in extracted_data.get('policies', []):
                        if str(pol_data.get('PolicyId')) == str(policy.PolicyId):
                            policy.PolicyType = pol_data.get('PolicyType', '')
                            policy.PolicyCategory = pol_data.get('PolicyCategory', '')
                            policy.PolicySubCategory = pol_data.get('PolicySubCategory', '')
                            break

                    policy.save()
                    print(f"Set policy {policy.PolicyId} to Approved status and Active status")
                    
                    # Update all subpolicies for this policy
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    for subpolicy in subpolicies:
                        subpolicy.Status = 'Approved'
                        subpolicy.save()
                        print(f"Set subpolicy {subpolicy.SubPolicyId} to Approved status")
                
                # Also update the status in the extracted data
                if 'policies' in extracted_data:
                    for policy_data in extracted_data['policies']:
                        policy_data['Status'] = 'Approved'
                        policy_data['ActiveInactive'] = 'Active'  # Set to Active in JSON too
                        if 'subpolicies' in policy_data:
                            for subpolicy_data in policy_data['subpolicies']:
                                subpolicy_data['Status'] = 'Approved'
                    
                    # Update the extracted data in the approval record
                    new_approval.ExtractedData = extracted_data
                    new_approval.save()
                
                framework.save()
            elif approved is False:
                # Update framework status if rejected
                framework.Status = 'Rejected'
                framework.save()
                
                # Also reject all policies in this framework
                # Get all policies for this framework
                policies = Policy.objects.filter(FrameworkId=framework)
                
                for policy in policies:
                    # Update policy status to rejected
                    policy.Status = 'Rejected'
                    policy.save()
                    
                    # Create rejection entry in policy approval
                    policy_extracted_data = {
                        "PolicyName": policy.PolicyName,
                        "PolicyDescription": policy.PolicyDescription,
                        "Status": "Rejected",
                        "Scope": policy.Scope,
                        "Objective": policy.Objective,
                        "type": "policy",
                        "framework_rejection": True,
                        "rejection_reason": remarks or f'Framework was rejected',
                        "remarks": remarks
                    }
                    
                    # Get all subpolicies for this policy
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    
                    # Create subpolicies data
                    subpolicies_data = []
                    for subpolicy in subpolicies:
                        # Update subpolicy status to rejected
                        subpolicy.Status = 'Rejected'
                        subpolicy.save()
                        
                        subpolicy_data = {
                            "SubPolicyId": subpolicy.SubPolicyId,
                            "SubPolicyName": subpolicy.SubPolicyName,
                            "Identifier": subpolicy.Identifier,
                            "Description": subpolicy.Description,
                            "Status": "Rejected",
                            "approval": {
                                "approved": False,
                                "remarks": remarks or f'Subpolicy "{subpolicy.SubPolicyName}" was rejected'
                            }
                        }
                        subpolicies_data.append(subpolicy_data)
                    
                    # Add subpolicies to policy data
                    policy_extracted_data["subpolicies"] = subpolicies_data
                    
                    # Create policy approval record
                    PolicyApproval.objects.create(
                        PolicyId=policy,
                        ExtractedData=policy_extracted_data,
                        UserId=user_id,
                        ReviewerId=reviewer_id,
                        Version=get_next_policy_reviewer_version(policy),
                        ApprovedNot=False  # Rejected
                    )
                # Send notification to submitter about framework rejection
                try:
                    notification_service = NotificationService()
                    submitter = Users.objects.get(UserId=user_id)
                    reviewer = Users.objects.get(UserId=reviewer_id)
                    notification_data = {
                        'notification_type': 'frameworkRejected',
                        'email': submitter.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            submitter.UserName,
                            framework.FrameworkName,
                            reviewer.UserName,
                            remarks or 'Framework was rejected'
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                except Exception as notify_ex:
                    print(f"DEBUG: Error sending framework rejection notification: {notify_ex}")
            
            return Response({
                "message": "Framework review submitted successfully",
                "ApprovalId": new_approval.ApprovalId,
                "Version": new_approval.Version,
                "ApprovedNot": new_approval.ApprovedNot,
                "ApprovedDate": new_approval.ApprovedDate.isoformat() if new_approval.ApprovedDate else None
            }, status=status.HTTP_200_OK)
            
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_framework_approval(request, framework_id):
    """
    Get the latest approval for a framework
    """
    try:
        # Get the latest approval by created date
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework_id
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"message": "No approvals found for this framework"}, status=status.HTTP_404_NOT_FOUND)
        
        approval_data = {
            "ApprovalId": latest_approval.ApprovalId,
            "FrameworkId": latest_approval.FrameworkId.FrameworkId if latest_approval.FrameworkId else None,
            "ExtractedData": latest_approval.ExtractedData,
            "UserId": latest_approval.UserId,
            "ReviewerId": latest_approval.ReviewerId,
            "Version": latest_approval.Version,
            "ApprovedNot": latest_approval.ApprovedNot,
            "ApprovedDate": latest_approval.ApprovedDate.isoformat() if latest_approval.ApprovedDate else None
        }
        
        return Response(approval_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])
def approve_reject_subpolicy_in_framework(request, framework_id, policy_id, subpolicy_id):
    """
    Approve or reject a specific subpolicy within a framework approval process
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get the latest framework approval
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"error": "No framework approval found"}, status=status.HTTP_404_NOT_FOUND)
        
        approved = request.data.get('approved', None)  # True for approve, False for reject
        rejection_reason = request.data.get('rejection_reason', '')
        submit_review = request.data.get('submit_review', False)  # New flag to submit review immediately
        
        if approved is None:
            return Response({"error": "Approval status not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a copy of the extracted data for the new version
        extracted_data = latest_approval.ExtractedData.copy()
        
        # Find and update the subpolicy status in JSON
        policies = extracted_data.get('policies', [])
        policy_found = False
        subpolicy_found = False
        
        with transaction.atomic():
            for policy in policies:
                if str(policy.get('PolicyId')) == str(policy_id):
                    policy_found = True
                    subpolicies = policy.get('subpolicies', [])
                    
                    for subpolicy in subpolicies:
                        if str(subpolicy.get('SubPolicyId')) == str(subpolicy_id):
                            subpolicy_found = True
                            
                            # Update the actual SubPolicy record in database
                            try:
                                db_subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_id)
                                db_policy = Policy.objects.get(PolicyId=policy_id)
                                db_framework = framework
                                submitter = Users.objects.get(UserId=latest_approval.UserId)
                                reviewer = Users.objects.get(UserId=latest_approval.ReviewerId)
                                notification_service = NotificationService()
                                
                                if approved:
                                    db_subpolicy.Status = 'Approved'
                                    subpolicy['Status'] = 'Approved'
                                    
                                    # Check if all subpolicies for this policy are approved
                                    all_subpolicies = SubPolicy.objects.filter(PolicyId=policy_id)
                                    all_approved = all(sp.Status == 'Approved' for sp in all_subpolicies)
                                    
                                    # If all subpolicies are approved, we can mark the policy as ready for approval
                                    if all_approved:
                                        db_policy.Status = 'Ready for Approval'
                                        db_policy.save()
                                        policy['Status'] = 'Ready for Approval'
                                    
                                    # Send notification to submitter about approval
                                    if submitter and reviewer:
                                        notification_data = {
                                            'notification_type': 'policyApproved',
                                            'email': submitter.Email,
                                            'email_type': 'gmail',
                                            'template_data': [
                                                submitter.UserName,
                                                db_policy.PolicyName,
                                                reviewer.UserName,
                                                db_framework.FrameworkName
                                            ]
                                        }
                                        notification_service.send_multi_channel_notification(notification_data)
                                else:
                                    db_subpolicy.Status = 'Rejected'
                                    subpolicy['Status'] = 'Rejected'
                                    
                                    # Also update the policy status in database
                                    db_policy.Status = 'Rejected'
                                    db_policy.save()
                                    policy['Status'] = 'Rejected'
                                    
                                    # Add rejection details to framework ExtractedData
                                    extracted_data['framework_approval'] = {
                                        'approved': False,
                                        'remarks': rejection_reason or f'Subpolicy "{subpolicy.get("SubPolicyName", "")}" was rejected',
                                        'rejected_by': 'Reviewer',
                                        'rejection_level': 'subpolicy',
                                        'rejected_item': f'Subpolicy: {subpolicy.get("SubPolicyName", "")}'
                                    }
                                    
                                    # Send notification to submitter about rejection
                                    if submitter and reviewer:
                                        notification_data = {
                                            'notification_type': 'policyRejected',
                                            'email': submitter.Email,
                                            'email_type': 'gmail',
                                            'template_data': [
                                                submitter.UserName,
                                                db_policy.PolicyName,
                                                reviewer.UserName,
                                                rejection_reason or f'Policy "{policy.get("PolicyName", "")}" was rejected'
                                            ]
                                        }
                                        notification_service.send_multi_channel_notification(notification_data)
                                    
                                    # If submit_review flag is true, submit the final review directly
                                    if submit_review:
                                        # Create a single reviewer version with rejection
                                        framework_approval = FrameworkApproval.objects.create(
                                            FrameworkId=framework,
                                            ExtractedData=extracted_data,
                                            UserId=latest_approval.UserId,
                                            ReviewerId=latest_approval.ReviewerId,
                                            ApprovedNot=False,  # Rejected
                                            Version=get_next_reviewer_version(framework)  # Use the helper function
                                        )
                                        
                                        # Update framework status to rejected
                                        framework.Status = 'Rejected'
                                        framework.save()
                                        
                                        return Response({
                                            "message": "Subpolicy rejected and review submitted successfully",
                                            "subpolicy_status": "Rejected",
                                            "framework_status": "Rejected",
                                            "ApprovalId": framework_approval.ApprovalId,
                                            "Version": framework_approval.Version
                                        }, status=status.HTTP_200_OK)
                                    else:
                                        # Create new reviewer version without final submission
                                        return create_reviewer_version(framework, extracted_data, latest_approval, False, rejection_reason)
                                
                                db_subpolicy.save()
                                
                            except SubPolicy.DoesNotExist:
                                return Response({"error": "SubPolicy not found in database"}, status=status.HTTP_404_NOT_FOUND)
                            
                            break
                    
                    if not approved:
                        break  # No need to continue if rejecting
            
            if not policy_found:
                return Response({"error": "Policy not found in framework"}, status=status.HTTP_404_NOT_FOUND)
            
            if not subpolicy_found:
                return Response({"error": "Subpolicy not found in policy"}, status=status.HTTP_404_NOT_FOUND)
            
            # If approved, just update the current approval
            latest_approval.ExtractedData = extracted_data
            latest_approval.save()
            
            return Response({
                "message": f"Subpolicy {'approved' if approved else 'rejected'} successfully",
                "subpolicy_status": "Approved" if approved else "Rejected"
            }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def approve_reject_policy_in_framework(request, framework_id, policy_id):
    """
    Approve or reject a specific policy within a framework approval process
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get the latest framework approval
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"error": "No framework approval found"}, status=status.HTTP_404_NOT_FOUND)
        
        approved = request.data.get('approved', None)  # True for approve, False for reject
        rejection_reason = request.data.get('rejection_reason', '')
        submit_review = request.data.get('submit_review', False)  # New flag to submit review immediately
        
        if approved is None:
            return Response({"error": "Approval status not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a copy of the extracted data for the new version
        extracted_data = latest_approval.ExtractedData.copy()
        
        # Find and update the policy status in JSON
        policies = extracted_data.get('policies', [])
        policy_found = False
        
        with transaction.atomic():
            for policy in policies:
                if str(policy.get('PolicyId')) == str(policy_id):
                    policy_found = True
                    
                    # Prepare notification service and user info
                    notification_service = NotificationService()
                    try:
                        db_policy = Policy.objects.get(PolicyId=policy_id)
                        submitter = Users.objects.get(UserId=latest_approval.UserId)
                        reviewer = Users.objects.get(UserId=latest_approval.ReviewerId)
                    except Exception as user_ex:
                        print(f"Notification user lookup error: {user_ex}")
                        submitter = None
                        reviewer = None
                    now_str = timezone.now().strftime('%Y-%m-%d %H:%M')
                    
                    if approved:
                        # Check if all subpolicies are approved first
                        subpolicies = policy.get('subpolicies', [])
                        if subpolicies:
                            all_subpolicies_approved = all(sp.get('Status') == 'Approved' for sp in subpolicies)
                            if not all_subpolicies_approved:
                                return Response({
                                    "error": "All subpolicies must be approved before approving the policy"
                                }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Update the actual Policy record in database
                        try:
                            db_policy.Status = 'Approved'
                            db_policy.save()
                            policy['Status'] = 'Approved'
                            
                            # Check if all policies are approved to update framework status
                            all_policies_approved = all(p.get('Status') == 'Approved' for p in policies)
                            if all_policies_approved:
                                extracted_data['Status'] = 'Ready for Final Approval'
                            
                            # Send notification to submitter about approval
                            if submitter and reviewer:
                                notification_data = {
                                    'notification_type': 'policyApproved',
                                    'email': submitter.Email,
                                    'email_type': 'gmail',
                                    'template_data': [
                                        submitter.UserName,
                                        db_policy.PolicyName,
                                        reviewer.UserName,
                                        now_str
                                    ]
                                }
                                notification_service.send_multi_channel_notification(notification_data)
                        except Policy.DoesNotExist:
                            return Response({"error": "Policy not found in database"}, status=status.HTTP_404_NOT_FOUND)
                        
                    else:
                        # Update the actual Policy record in database
                        try:
                            db_policy.Status = 'Rejected'
                            db_policy.save()
                            policy['Status'] = 'Rejected'
                            
                            # Reject all subpolicies in this policy
                            subpolicies_in_db = SubPolicy.objects.filter(PolicyId=policy_id)
                            for sp_db in subpolicies_in_db:
                                sp_db.Status = 'Rejected'
                                sp_db.save()
                            
                            subpolicies = policy.get('subpolicies', [])
                            for subpolicy in subpolicies:
                                subpolicy['Status'] = 'Rejected'
                            
                            # Reject entire framework
                            framework.Status = 'Rejected'
                            framework.save()
                            extracted_data['Status'] = 'Rejected'
                            
                            # Add rejection details
                            extracted_data['framework_approval'] = {
                                'approved': False,
                                'remarks': rejection_reason or f'Policy "{policy.get("PolicyName", "")}" was rejected',
                                'rejected_by': 'Reviewer',
                                'rejection_level': 'policy',
                                'rejected_item': f'Policy: {policy.get("PolicyName", "")}'
                            }
                            
                            # Send notification to submitter about rejection
                            if submitter and reviewer:
                                notification_data = {
                                    'notification_type': 'policyRejected',
                                    'email': submitter.Email,
                                    'email_type': 'gmail',
                                    'template_data': [
                                        submitter.UserName,
                                        db_policy.PolicyName,
                                        reviewer.UserName,
                                        rejection_reason or f'Policy "{policy.get("PolicyName", "")}" was rejected'
                                    ]
                                }
                                notification_service.send_multi_channel_notification(notification_data)
                            
                            # If submit_review flag is true, submit the final review directly
                            if submit_review:
                                # Create a single reviewer version with rejection
                                framework_approval = FrameworkApproval.objects.create(
                                    FrameworkId=framework,
                                    ExtractedData=extracted_data,
                                    UserId=latest_approval.UserId,
                                    ReviewerId=latest_approval.ReviewerId,
                                    ApprovedNot=False,  # Rejected
                                    Version=get_next_reviewer_version(framework)  # Use the helper function
                                )
                                
                                # Update framework status to rejected
                                framework.Status = 'Rejected'
                                framework.save()
                                
                                return Response({
                                    "message": "Policy rejected and review submitted successfully",
                                    "policy_status": "Rejected",
                                    "framework_status": "Rejected",
                                    "ApprovalId": framework_approval.ApprovalId,
                                    "Version": framework_approval.Version
                                }, status=status.HTTP_200_OK)
                            else:
                                # Create new reviewer version without final submission
                                return create_reviewer_version(framework, extracted_data, latest_approval, False, rejection_reason)
                        
                        except Policy.DoesNotExist:
                            return Response({"error": "Policy not found in database"}, status=status.HTTP_404_NOT_FOUND)
                    
                    break
            
            if not policy_found:
                return Response({"error": "Policy not found in framework"}, status=status.HTTP_404_NOT_FOUND)
            
            # If approved, just update the current approval
            latest_approval.ExtractedData = extracted_data
            latest_approval.save()
            
            return Response({
                "message": f"Policy {'approved' if approved else 'rejected'} successfully",
                "policy_status": "Approved" if approved else "Rejected"
            }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def approve_entire_framework_final(request, framework_id):
    """
    Final approval of entire framework after all policies are approved
    """
    try:
        print(f"\n\n==== DEBUG: Starting approve_entire_framework_final for framework ID: {framework_id} ====")
        framework = Framework.objects.get(FrameworkId=framework_id)
        print(f"DEBUG: Found framework: {framework.FrameworkName} (ID: {framework.FrameworkId}), Status: {framework.Status}, ActiveInactive: {framework.ActiveInactive}")
        
        # Get the latest framework approval
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"error": "No framework approval found"}, status=status.HTTP_404_NOT_FOUND)
        
        extracted_data = latest_approval.ExtractedData.copy()
        policies = extracted_data.get('policies', [])
        
        # Verify all policies are approved
        if not all(p.get('Status') == 'Approved' for p in policies):
            return Response({
                "error": "All policies must be approved before final framework approval"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update framework status in database
            framework.Status = 'Approved'
            
            # Ensure CurrentVersion is set correctly from the FrameworkVersion record
            current_framework_version = FrameworkVersion.objects.filter(
                FrameworkId=framework
            ).first()
            if current_framework_version:
                print(f"DEBUG: Setting CurrentVersion to {current_framework_version.Version} for framework {framework_id}")
                framework.CurrentVersion = current_framework_version.Version
                
                # Update all policies to have the same CurrentVersion
                policies_db = Policy.objects.filter(FrameworkId=framework)
                for policy in policies_db:
                    policy.CurrentVersion = str(float(current_framework_version.Version))
                    # Set policy status to Active when framework is approved
                    policy.Status = 'Approved'
                    policy.ActiveInactive = 'Active'
                    print(f"DEBUG: Setting policy {policy.PolicyId} to Status='Approved', ActiveInactive='Active'")
                    policy.save()
            
            framework.save()
            print(f"DEBUG: Updated framework {framework_id} status to 'Approved'")
            
            # Update all policies in the JSON data as well
            for policy_data in policies:
                policy_data['Status'] = 'Approved'
                policy_data['ActiveInactive'] = 'Active'
            
            # Also update all related SubPolicies to be Approved
            for policy in policies_db:
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy.Status = 'Approved'
                    subpolicy.save()
                    print(f"DEBUG: Set subpolicy {subpolicy.SubPolicyId} to Status='Approved'")
            
            # Now deactivate any previous frameworks with the same identifier
            previous_frameworks_deactivated = []
            
            # Method 1: Check if there's a previous version record for this framework
            try:
                latest_version = FrameworkVersion.objects.filter(
                    FrameworkId=framework
                ).order_by('-Version').first()
                
                if latest_version and latest_version.PreviousVersionId:
                    previous_framework_id = latest_version.PreviousVersionId
                    print(f"DEBUG: Found previous framework version: {previous_framework_id}")
                    
                    try:
                        previous_version = FrameworkVersion.objects.get(FrameworkId=previous_framework_id)
                        previous_framework = previous_version.FrameworkId
                        
                        print(f"DEBUG: Previous framework {previous_framework_id} status before update: {previous_framework.ActiveInactive}")
                        previous_framework.ActiveInactive = 'Inactive'
                        # Make sure Status remains 'Approved' if it was already approved
                        if previous_framework.Status == 'Approved':
                            # Don't change the Status, leave it as 'Approved'
                            print(f"DEBUG: Keeping Status 'Approved' for framework {previous_framework_id}")
                        previous_framework.save()
                        
                        # Verify the update
                        previous_framework.refresh_from_db()
                        print(f"DEBUG: Previous framework {previous_framework_id} status after update: {previous_framework.ActiveInactive}, Status: {previous_framework.Status}")
                        
                        # Set all policies of the previous framework to inactive
                        previous_policies = Policy.objects.filter(FrameworkId=previous_framework)
                        for previous_policy in previous_policies:
                            previous_policy.ActiveInactive = 'Inactive'
                            # Don't change Status if it's already Approved
                            if previous_policy.Status == 'Approved':
                                print(f"DEBUG: Keeping Status 'Approved' for policy {previous_policy.PolicyId}")
                            # Don't change CurrentVersion value
                            print(f"DEBUG: Preserving CurrentVersion {previous_policy.CurrentVersion} for policy {previous_policy.PolicyId}")
                            previous_policy.save()
                        
                        previous_frameworks_deactivated.append(int(previous_framework_id))
                        print(f"DEBUG: Deactivated previous framework {previous_framework_id} and its {previous_policies.count()} policies")
                    except Exception as e:
                        print(f"DEBUG: Error in Method 1: {str(e)}")
            except Exception as e:
                print(f"DEBUG: Error in Method 1 (outer): {str(e)}")
            
            # Method 2: Use the identifier field to find other frameworks
            try:
                # Get the identifier of the current framework
                current_identifier = framework.Identifier
                print(f"DEBUG: Current framework identifier: {current_identifier}")
                
                # Find all frameworks with this identifier except the current one
                other_frameworks = Framework.objects.filter(
                    Identifier=current_identifier
                ).exclude(FrameworkId=framework_id)
                
                print(f"DEBUG: Found {other_frameworks.count()} other frameworks with the same identifier")
                
                for other_framework in other_frameworks:
                    # Skip if already deactivated
                    if int(other_framework.FrameworkId) in previous_frameworks_deactivated:
                        print(f"DEBUG: Framework {other_framework.FrameworkId} already processed, skipping")
                        continue
                    
                    print(f"DEBUG: Framework {other_framework.FrameworkId} status before update: {other_framework.ActiveInactive}")
                    
                    # Set to inactive
                    other_framework.ActiveInactive = 'Inactive'
                    # Make sure Status remains 'Approved' if it was already approved
                    if other_framework.Status == 'Approved':
                        # Don't change the Status, leave it as 'Approved'
                        print(f"DEBUG: Keeping Status 'Approved' for framework {other_framework.FrameworkId}")
                    other_framework.save()
                    
                    # Verify the update
                    other_framework.refresh_from_db()
                    print(f"DEBUG: Framework {other_framework.FrameworkId} status after update: {other_framework.ActiveInactive}, Status: {other_framework.Status}")
                    
                    # Set all policies to inactive
                    other_policies = Policy.objects.filter(FrameworkId=other_framework)
                    for other_policy in other_policies:
                        other_policy.ActiveInactive = 'Inactive'
                        # Don't change Status if it's already Approved
                        if other_policy.Status == 'Approved':
                            print(f"DEBUG: Keeping Status 'Approved' for policy {other_policy.PolicyId}")
                        # Don't change CurrentVersion value
                        print(f"DEBUG: Preserving CurrentVersion {other_policy.CurrentVersion} for policy {other_policy.PolicyId}")
                        other_policy.save()
                    
                    print(f"DEBUG: By direct check: Deactivated framework {other_framework.FrameworkId} and its {other_policies.count()} policies")
                    previous_frameworks_deactivated.append(int(other_framework.FrameworkId))
            except Exception as e:
                print(f"DEBUG: Error in Method 2: {str(e)}")
            
            # Log summary of what was deactivated
            print(f"\nDEBUG: Deactivated frameworks: {previous_frameworks_deactivated}")
            
            # Approve all policies and subpolicies associated with this framework
            policies = Policy.objects.filter(FrameworkId=framework)
            print(f"Approving {policies.count()} policies for framework {framework_id}")
            
            # Update all policies in the database
            for policy in policies:
                policy.Status = 'Approved'
                policy.ActiveInactive = 'Active'  # Set to Active
                policy.save()
                print(f"Set policy {policy.PolicyId} to Approved status and Active status")
                
                # Update all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy.Status = 'Approved'
                    subpolicy.save()
                    print(f"Set subpolicy {subpolicy.SubPolicyId} to Approved status")
            
            # Also update the status in the extracted data
            if 'policies' in extracted_data:
                for policy_data in extracted_data['policies']:
                    policy_data['Status'] = 'Approved'
                    policy_data['ActiveInactive'] = 'Active'  # Set to Active in JSON too
                    if 'subpolicies' in policy_data:
                        for subpolicy_data in policy_data['subpolicies']:
                            subpolicy_data['Status'] = 'Approved'
                
                # Update the extracted data in the approval record
                latest_approval.ExtractedData = extracted_data
                latest_approval.save()
            
            # Send notification to submitter about final framework approval
            try:
                notification_service = NotificationService()
                submitter = Users.objects.get(UserId=latest_approval.UserId)
                reviewer = Users.objects.get(UserId=latest_approval.ReviewerId)
                approval_date = timezone.now().date().isoformat()
                notification_data = {
                    'notification_type': 'frameworkFinalApproved',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        framework.FrameworkName,
                        reviewer.UserName,
                        approval_date
                    ]
                }
                notification_service.send_multi_channel_notification(notification_data)
            except Exception as notify_ex:
                print(f"DEBUG: Error sending framework final approval notification: {notify_ex}")
            
            extracted_data['framework_approval'] = {
                'approved': True,
                'remarks': 'Framework approved successfully',
                'approved_by': 'Reviewer',
                'approval_date': timezone.now().date().isoformat()
            }
            
            print("\n==== DEBUG: Completed framework approval process ====\n")
            
            # Create new reviewer version for final approval
            return create_reviewer_version(framework, extracted_data, latest_approval, True, 'Framework approved successfully')
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"DEBUG: Unhandled exception in approve_entire_framework_final: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def create_reviewer_version(framework, extracted_data, latest_approval, approved, remarks):
    """
    Helper function to create a new reviewer version of framework approval
    """
    try:
        with transaction.atomic():
            # Determine the next reviewer version using the helper function
            new_version = get_next_reviewer_version(framework)
            
            # Create a new approval record with the reviewer version
            new_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=latest_approval.UserId,
                ReviewerId=latest_approval.ReviewerId,
                Version=new_version,
                ApprovedNot=approved
            )
            
            # Set approval/rejection date
            if approved:
                # Set the approval date to current date
                new_approval.ApprovedDate = timezone.now().date()
                
                # Update framework status
                if framework.ActiveInactive == 'Inactive':
                    framework.Status = 'Inactive'
                else:
                    framework.Status = 'Approved'
                
                # Ensure all policies and subpolicies are approved in the extracted data
                if 'policies' in extracted_data:
                    for policy_data in extracted_data['policies']:
                        policy_data['Status'] = 'Approved'
                        if 'subpolicies' in policy_data:
                            for subpolicy_data in policy_data['subpolicies']:
                                subpolicy_data['Status'] = 'Approved'
                
                # Update the extracted data in the approval record
                new_approval.ExtractedData = extracted_data
                
                framework.save()
            else:
                # Update framework status to rejected
                framework.Status = 'Rejected'
                framework.save()
            
            # Save the approval record with the date
            new_approval.save()
            
            return Response({
                "message": f"Framework {'approved' if approved else 'rejected'} successfully",
                "ApprovalId": new_approval.ApprovalId,
                "Version": new_approval.Version,
                "ApprovedNot": new_approval.ApprovedNot,
                "framework_status": "Approved" if approved else "Rejected",
                "ApprovedDate": new_approval.ApprovedDate.isoformat() if new_approval.ApprovedDate else None
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({"error": f"Error creating reviewer version: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_rejected_frameworks_for_user(request, framework_id=None, user_id=None):
    """
    Get all rejected frameworks for a specific user that can be edited and resubmitted
    Note: framework_id parameter is ignored - it's only in URL for consistency
    """
    try:
        if not user_id:
            user_id = request.GET.get('user_id', 1)  # Default user
            
        # Get all frameworks with rejected status
        rejected_frameworks = Framework.objects.filter(Status='Rejected')
        
        # Find the latest approval for each rejected framework
        rejected_framework_data = []
        
        for framework in rejected_frameworks:
            # Get the latest approval for this framework
            latest_approval = FrameworkApproval.objects.filter(
                FrameworkId=framework.FrameworkId,
                ApprovedNot=False  # Must be rejected
            ).order_by('-ApprovalId').first()
            
            if latest_approval:
                framework_data = {
                    "ApprovalId": latest_approval.ApprovalId,
                    "FrameworkId": framework.FrameworkId,
                    "ExtractedData": latest_approval.ExtractedData,
                    "Version": latest_approval.Version,
                    "ApprovedNot": latest_approval.ApprovedNot,
                    "rejection_reason": latest_approval.ExtractedData.get('framework_approval', {}).get('remarks', 'No reason provided'),
                    "created_at": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None
                }
                rejected_framework_data.append(framework_data)
        
        return Response(rejected_framework_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def request_framework_status_change(request, framework_id):
    """
    Request approval for changing a framework's status from Active to Inactive
    Creates a framework approval entry that needs to be approved by a reviewer
    """
    try:
        # Get the framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Check if framework is active
        if framework.ActiveInactive != 'Active':
            return Response({"error": "Only Active frameworks can be submitted for status change approval"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Extract data for the approval
        user_id = request.data.get('UserId', 1)  # Default to 1 if not provided
        reviewer_id = request.data.get('ReviewerId', 2)  # Default to 2
        reviewer_email = None
        if framework.Reviewer:
            reviewer_user = Users.objects.filter(UserName=framework.Reviewer).first()
            if reviewer_user:
                reviewer_id = reviewer_user.UserId
                reviewer_email = reviewer_user.Email
        reason = request.data.get('reason', 'No reason provided')
        
        # Collect policies and subpolicies data for approval JSON
        policies_data = []
        created_policies = Policy.objects.filter(FrameworkId=framework)
        
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
            "source": "status_change_request",
            "request_type": "status_change",
            "requested_status": "Inactive",
            "current_status": "Active",
            "reason_for_change": reason,
            "requested_date": timezone.now().date().isoformat(),
            "policies": policies_data,
            "totalPolicies": len(policies_data),
            "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data),
            "cascade_to_policies": request.data.get('cascadeToApproved', True)
        }
        
        with transaction.atomic():
            # Update framework status to Under Review
            framework.Status = 'Under Review'
            framework.save()
            
            # Determine the next user version
            latest_user_version = FrameworkApproval.objects.filter(
                FrameworkId=framework,
                Version__startswith='u'
            ).order_by('-ApprovalId').first()
            
            if latest_user_version:
                try:
                    version_num = int(latest_user_version.Version[1:])
                    new_version = f'u{version_num + 1}'
                except ValueError:
                    new_version = 'u1'
            else:
                new_version = 'u1'  # First approval
            
            # Create the framework approval
            framework_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version=new_version,
                ApprovedNot=None  # Not yet approved
            )
            # Send notification to reviewer if email is available
            if 'reviewer_email' not in locals():
                reviewer_email = None
                if framework.Reviewer:
                    reviewer_user = Users.objects.filter(UserName=framework.Reviewer).first()
                    if reviewer_user:
                        reviewer_email = reviewer_user.Email
            if reviewer_email:
                notification_service = NotificationService()
                notification_data = {
                    'notification_type': 'frameworkInactiveRequested',
                    'email': reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        framework.FrameworkName,
                        framework.Reviewer,
                        framework.CreatedByName,
                        reason
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Framework inactivation notification result: {notification_result}")
        
        return Response({
            "message": "Framework status change request submitted successfully. Awaiting approval.",
            "ApprovalId": framework_approval.ApprovalId,
            "Version": framework_approval.Version,
            "Status": "Under Review"
        }, status=status.HTTP_201_CREATED)
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def approve_framework_status_change(request, approval_id):
    """
    Approve or reject a framework status change request
    """
    try:
        approval = FrameworkApproval.objects.get(ApprovalId=approval_id)
        framework = approval.FrameworkId
        
        # Check if this is a status change request
        if approval.ExtractedData.get('request_type') != 'status_change':
            return Response({"error": "This is not a status change request"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get approval decision
        approved = request.data.get('approved', False)
        remarks = request.data.get('remarks', '')
        
        with transaction.atomic():
            # Create a copy of the extracted data
            extracted_data = approval.ExtractedData.copy()
            
            if approved:
                # Change framework status to Inactive
                framework.ActiveInactive = 'Inactive'
                framework.Status = 'Approved'  # Also set Status field to Inactive
                framework.save()
                
                # Update extracted data
                extracted_data['ActiveInactive'] = 'Inactive'
                extracted_data['Status'] = 'Approved'
                extracted_data['status_change_approval'] = {
                    'approved': True,
                    'remarks': remarks or 'Status change approved',
                    'approved_by': 'Reviewer',
                    'approval_date': timezone.now().date().isoformat()
                }
                
                # Check if we should cascade to policies
                cascade_to_policies = extracted_data.get('cascade_to_policies', True)
                if cascade_to_policies:
                    # Get all policies for this framework (not just approved ones)
                    policies = Policy.objects.filter(
                        FrameworkId=framework
                    )
                    
                    # Update their status to Inactive
                    for policy in policies:
                        policy.ActiveInactive = 'Inactive'
                        policy.Status = 'Approved'  # Also set Status field to Inactive
                        policy.save()
                        
                        # Also update all subpolicies for this policy to Inactive
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        for subpolicy in subpolicies:
                            subpolicy.Status = 'Inactive'
                            subpolicy.save()
                        
                        # Update in extracted data
                        for policy_data in extracted_data.get('policies', []):
                            if policy_data.get('PolicyId') == policy.PolicyId:
                                policy_data['ActiveInactive'] = 'Inactive'
                                policy_data['Status'] = 'Approved'  # Also update Status in JSON
                                
                                # Update subpolicies in extracted data
                                for subpolicy_data in policy_data.get('subpolicies', []):
                                    subpolicy_data['Status'] = 'Approved'
            else:
                # Reject status change request, revert framework status
                framework.Status = 'Approved'  # Reset from "Under Review"
                framework.save()
                
                # Update extracted data
                extracted_data['status_change_approval'] = {
                    'approved': False,
                    'remarks': remarks or 'Status change rejected',
                    'rejected_by': 'Reviewer',
                    'rejection_date': timezone.now().date().isoformat()
                }
            
            # Determine the next reviewer version
            latest_reviewer_version = FrameworkApproval.objects.filter(
                FrameworkId=framework,
                Version__startswith='r'
            ).order_by('-ApprovalId').first()
            
            if latest_reviewer_version:
                try:
                    version_num = int(latest_reviewer_version.Version[1:])
                    new_version = f'r{version_num + 1}'
                except ValueError:
                    new_version = 'r1'
            else:
                new_version = 'r1'
                
            # Create a new approval record with the reviewer version
            new_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=approval.UserId,
                ReviewerId=approval.ReviewerId,
                Version=new_version,
                ApprovedNot=approved
            )
            
            # Set approval date if approved
            if approved:
                new_approval.ApprovedDate = timezone.now().date()
                new_approval.save()
            
            # Send notification to submitter about approval or rejection
            submitter_email = None
            submitter_name = framework.CreatedByName
            if submitter_name:
                submitter_user = Users.objects.filter(UserName=submitter_name).first()
                if submitter_user:
                    submitter_email = submitter_user.Email
            reviewer_name = None
            if approval.ReviewerId:
                reviewer_user = Users.objects.filter(UserId=approval.ReviewerId).first()
                if reviewer_user:
                    reviewer_name = reviewer_user.UserName
            if submitter_email and reviewer_name:
                notification_service = NotificationService()
                if approved:
                    notification_data = {
                        'notification_type': 'frameworkInactivationApproved',
                        'email': submitter_email,
                        'email_type': 'gmail',
                        'template_data': [
                            submitter_name,
                            framework.FrameworkName,
                            reviewer_name,
                            remarks or 'Status change approved'
                        ]
                    }
                else:
                    notification_data = {
                        'notification_type': 'frameworkInactivationRejected',
                        'email': submitter_email,
                        'email_type': 'gmail',
                        'template_data': [
                            framework.FrameworkName,
                            submitter_name,
                            reviewer_name,
                            remarks or 'Status change rejected'
                        ]
                    }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Framework inactivation approval notification result: {notification_result}")
            
        return Response({
            "message": f"Framework status change request {'approved' if approved else 'rejected'}",
            "ApprovalId": new_approval.ApprovalId,
            "Version": new_approval.Version,
            "ApprovedNot": approved,
            "framework_status": framework.Status,
            "framework_active_inactive": framework.ActiveInactive
        }, status=status.HTTP_200_OK)
        
    except FrameworkApproval.DoesNotExist:
        return Response({"error": "Framework approval not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_status_change_requests(request):
    """
    Get all framework status change requests
    Include both pending and processed (approved/rejected) requests
    Group related approvals by framework name to ensure consistent status display
    """
    try:
        # Find all framework approvals with request_type=status_change
        status_change_requests = []
        framework_status_map = {}  # To track the latest status for each framework
        
        # Get all approvals, not just those with ApprovedNot=None
        approvals = FrameworkApproval.objects.filter().order_by('-ApprovalId')
        
        # First pass: Get the latest status for each framework
        for approval in approvals:
            # Check if the extracted data contains request_type=status_change
            if approval.ExtractedData.get('request_type') == 'status_change':
                framework = approval.FrameworkId
                framework_name = framework.FrameworkName
                
                # Only track the status if we haven't seen this framework before
                # or if this is a newer approval (with a higher ApprovalId)
                if framework_name not in framework_status_map:
                    framework_status_map[framework_name] = {
                        'status': approval.ApprovedNot,
                        'approvalId': approval.ApprovalId
                    }
        
        # Second pass: Create the request data with consistent status
        for approval in approvals:
            # Check if the extracted data contains request_type=status_change
            if approval.ExtractedData.get('request_type') == 'status_change':
                framework = approval.FrameworkId
                framework_name = framework.FrameworkName
                
                # Get the policies and subpolicies that would be affected if approved
                affected_policies = []
                total_subpolicies = 0
                if approval.ExtractedData.get('cascade_to_policies', True):
                    policies = Policy.objects.filter(
                        FrameworkId=framework
                    )
                    
                    for policy in policies:
                        # Count subpolicies for this policy
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        subpolicy_count = subpolicies.count()
                        total_subpolicies += subpolicy_count
                        
                        affected_policies.append({
                            'PolicyId': policy.PolicyId,
                            'PolicyName': policy.PolicyName,
                            'Department': policy.Department,
                            'Status': policy.Status,
                            'ActiveInactive': policy.ActiveInactive,
                            'Identifier': policy.Identifier,
                            'Description': policy.PolicyDescription[:100] + '...' if policy.PolicyDescription and len(policy.PolicyDescription) > 100 else policy.PolicyDescription,
                            'SubpolicyCount': subpolicy_count
                        })
                
                # Use the latest status for this framework from our map
                latest_status = framework_status_map.get(framework_name, {'status': None})['status']
                
                # Determine status based on the latest status for this framework
                approval_status = "Pending Approval"
                if latest_status is True:
                    approval_status = "Approved"
                elif latest_status is False:
                    approval_status = "Rejected"
                
                # Include any approval remarks
                approval_remarks = ""
                if approval.ExtractedData.get('status_change_approval'):
                    approval_remarks = approval.ExtractedData.get('status_change_approval').get('remarks', '')
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                    'Category': framework.Category,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': approval.ExtractedData.get('requested_date'),
                    'Reason': approval.ExtractedData.get('reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'Version': approval.Version,
                    'Status': approval_status,
                    'ApprovedNot': latest_status,  # Use the latest status for consistency
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToApproved': approval.ExtractedData.get('cascade_to_policies', True),
                    'PolicyCount': len(affected_policies),
                    'SubpolicyCount': total_subpolicies,
                    'AffectedPolicies': affected_policies,
                    'Remarks': approval_remarks,
                    'IsLatestApproval': approval.ApprovalId == framework_status_map.get(framework_name, {'approvalId': None})['approvalId']
                }
                
                status_change_requests.append(request_data)
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 