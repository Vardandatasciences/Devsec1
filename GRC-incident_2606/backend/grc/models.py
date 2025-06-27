from django.db import models



from django.contrib.auth.models import User

 
# Users model (Django built-in User model is used)
class Users(models.Model):
    UserId = models.AutoField(primary_key=True)
    UserName = models.CharField(max_length=255)
    Password = models.CharField(max_length=255)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    Email = models.EmailField(max_length=100)
    class Meta:
        db_table = 'users'
    def __str__(self):
        return f"User {self.UserId} - {self.UserName}"
 





class LastChecklistItemVerified(models.Model):
    id = models.BigAutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    ComplianceId = models.IntegerField()
    SubPolicyId = models.IntegerField()
    PolicyId = models.IntegerField()
    Date = models.DateField()
    Time = models.TimeField()
    User = models.IntegerField()
    Complied = models.CharField(max_length=1)  # Since it's a 'char(1)' in the table
    Comments = models.TextField(null=True, blank=True)
    count = models.IntegerField()

    class Meta:
        db_table = 'lastchecklistitemverified'
        constraints = [
            models.CheckConstraint(
                check=models.Q(Complied__in=['0', '1']),
                name='complied_check'
            )
        ]

    def __str__(self):
        return f"Framework {self.FrameworkId} Compliance {self.ComplianceId} Policy {self.PolicyId}"

class CategoryBusinessUnit(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=50)
    value = models.CharField(max_length=255)

    class Meta:
        db_table = 'categoryunit'

    def __str__(self):
        return f"{self.source} - {self.value}"


class Framework(models.Model):
    FrameworkId = models.AutoField(primary_key=True)
    FrameworkName = models.CharField(max_length=255)
    CurrentVersion = models.FloatField(default=1.0)
    FrameworkDescription = models.TextField()
    EffectiveDate = models.DateField(null=True, blank=True)
    CreatedByName = models.CharField(max_length=255)
    CreatedByDate = models.DateField()
    Category = models.CharField(max_length=100, null=True, blank=True)
    DocURL = models.CharField(max_length=255, null=True, blank=True)
    Identifier = models.CharField(max_length=45, null=True, blank=True)
    StartDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)
    Status = models.CharField(max_length=45, null=True, blank=True)
    ActiveInactive = models.CharField(max_length=45, null=True, blank=True)
    Reviewer = models.CharField(max_length=255)  
    # in prahasrshitha s db not there
 
    class Meta:
        db_table = 'frameworks'
 
class FrameworkVersion(models.Model):
    VersionId = models.AutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    Version = models.FloatField()
    FrameworkName = models.CharField(max_length=255)
    CreatedBy = models.CharField(max_length=255)
    CreatedDate = models.DateField()
    PreviousVersionId = models.IntegerField(null=True, blank=True)
 
    class Meta:
        db_table = 'frameworkversions'
 
 
class Policy(models.Model):
    PolicyId = models.AutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    CurrentVersion = models.CharField(max_length=20, default='1.0')
    Status = models.CharField(max_length=50)
    PolicyDescription = models.TextField()
    PolicyName = models.CharField(max_length=255)
    StartDate = models.DateField()
    EndDate = models.DateField(null=True, blank=True)
    Department = models.CharField(max_length=255, null=True, blank=True)
    CreatedByName = models.CharField(max_length=255, null=True, blank=True)
    CreatedByDate = models.DateField(null=True, blank=True)
    Applicability = models.CharField(max_length=255, null=True, blank=True)
    DocURL = models.CharField(max_length=255, null=True, blank=True)
    Scope = models.TextField(null=True, blank=True)
    Objective = models.TextField(null=True, blank=True)
    Identifier = models.CharField(max_length=45, null=True, blank=True)
    PermanentTemporary = models.CharField(max_length=45, null=True, blank=True)
    ActiveInactive = models.CharField(max_length=45, null=True, blank=True)
    Reviewer=models.CharField(max_length=255, null=True, blank=True)
    CoverageRate = models.FloatField(null=True, blank=True)
    AcknowledgedUserIds = models.JSONField(default=list, blank=True, null=True)  # Allow null and use empty list as default
    AcknowledgementCount = models.IntegerField(default=0)
    PolicyType = models.CharField(max_length=255, null=True, blank=True)
    PolicyCategory = models.CharField(max_length=255, null=True, blank=True)
    PolicySubCategory = models.CharField(max_length=255, null=True, blank=True)
 
 
    class Meta:
        db_table = 'policies'
 
 
class PolicyVersion(models.Model):
    VersionId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId')
    Version = models.CharField(max_length=20)
    PolicyName = models.CharField(max_length=255)
    CreatedBy = models.CharField(max_length=255)
    CreatedDate = models.DateField()
    PreviousVersionId = models.IntegerField(null=True, blank=True)
 
    class Meta:
        db_table = 'policyversions'

class PolicyCategory(models.Model):
    Id = models.AutoField(primary_key=True)
    PolicyType = models.CharField(max_length=255)
    PolicyCategory = models.CharField(max_length=255)
    PolicySubCategory = models.CharField(max_length=255)

    class Meta:
        db_table = 'policycategories'
        unique_together = ('PolicyType', 'PolicyCategory', 'PolicySubCategory')

    def __str__(self):
        return f"{self.PolicyType} - {self.PolicyCategory} - {self.PolicySubCategory}"

 
 
class SubPolicy(models.Model):
    SubPolicyId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId')
    SubPolicyName = models.CharField(max_length=255)
    CreatedByName = models.CharField(max_length=255)
    CreatedByDate = models.DateField()
    Identifier = models.CharField(max_length=45)
    Description = models.TextField()
    Status = models.CharField(max_length=50, null=True, blank=True)
    PermanentTemporary = models.CharField(max_length=50, null=True, blank=True)
    Control = models.TextField(null=True, blank=True)
 
    class Meta:
        db_table = 'subpolicies'
 
 
class PolicyApproval(models.Model):
    ApprovalId = models.AutoField(primary_key=True)
    Identifier = models.CharField(max_length=45, db_column='Identifier')
    ExtractedData = models.JSONField(null=True, blank=True)
    UserId = models.IntegerField()
    ReviewerId = models.IntegerField()
    Version = models.CharField(max_length=50, null=True, blank=True)
    ApprovedNot = models.BooleanField(null=True)
    ApprovedDate = models.DateField(null=True, blank=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True, blank=True)
    ApprovalDueDate = models.DateField(null=True, blank=True)
 
    def __str__(self):
        return f"PolicyApproval {self.Identifier} (Version {self.Version})"
 
    class Meta:
        db_table = 'policyapproval'


class FrameworkApproval(models.Model):
    ApprovalId = models.AutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId', null=True)
    # Identifier field is optional, uncomment if needed
    # Identifier = models.CharField(max_length=45, null=True, blank=True)
    ExtractedData = models.JSONField(null=True, blank=True)
    UserId = models.IntegerField()
    ReviewerId = models.IntegerField(null=True, blank=True)
    Version = models.CharField(max_length=50, null=True, blank=True)
    ApprovedNot = models.BooleanField(null=True)
    ApprovedDate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"FrameworkApproval {self.FrameworkId_id} (Version {self.Version})"

    class Meta:
        db_table = 'frameworkapproval'

# Users model (Django built-in User model is used)
class Compliance(models.Model):
    ComplianceId = models.AutoField(primary_key=True)
    SubPolicy = models.ForeignKey(SubPolicy, on_delete=models.CASCADE, db_column='SubPolicyId', related_name='compliances')
    ComplianceTitle = models.CharField(max_length=145, null=True, blank=True)
    ComplianceItemDescription = models.TextField(null=True, blank=True)
    ComplianceType = models.CharField(max_length=100, null=True, blank=True)
    Scope = models.TextField(null=True, blank=True)
    Objective = models.TextField(null=True, blank=True)
    BusinessUnitsCovered = models.CharField(max_length=225, null=True, blank=True)
    IsRisk = models.BooleanField(null=True, blank=True)
    PossibleDamage = models.TextField(null=True, blank=True)
    mitigation = models.TextField(null=True, blank=True)
    Criticality = models.CharField(max_length=50, null=True, blank=True)
    MandatoryOptional = models.CharField(max_length=50, null=True, blank=True)
    ManualAutomatic = models.CharField(max_length=50, null=True, blank=True)
    Impact = models.CharField(max_length=50, null=True, blank=True)
    Probability = models.CharField(max_length=50, null=True, blank=True)
    MaturityLevel = models.CharField(max_length=50, choices=[
        ('Initial', 'Initial'),
        ('Developing', 'Developing'),
        ('Defined', 'Defined'),
        ('Managed', 'Managed'),
        ('Optimizing', 'Optimizing')
    ], default='Initial', null=True, blank=True)
    ActiveInactive = models.CharField(max_length=45, default='Inactive', null=True, blank=True)
    PermanentTemporary = models.CharField(max_length=45, null=True, blank=True)
    CreatedByName = models.CharField(max_length=250, null=True, blank=True)
    CreatedByDate = models.DateField(null=True, blank=True)
    ComplianceVersion = models.CharField(max_length=50, null=False)
    Status = models.CharField(max_length=50, default='Under Review', null=True, blank=True)
    Identifier = models.CharField(max_length=45, null=True, blank=True)
    Applicability = models.CharField(max_length=45, null=True, blank=True)
    PreviousComplianceVersionId = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        db_column='PreviousComplianceVersionId'
    )
    PotentialRiskScenarios = models.TextField(null=True, blank=True)
    RiskType = models.CharField(max_length=45, null=True, blank=True)
    RiskCategory = models.CharField(max_length=45, null=True, blank=True)
    RiskBusinessImpact = models.CharField(max_length=45, null=True, blank=True) 
    class Meta:
        db_table = 'compliance'

    def __str__(self):
        return f"Compliance {self.ComplianceId} - Version {self.ComplianceVersion}"
    

class ExportTask(models.Model):
    id = models.AutoField(primary_key=True)
    export_data = models.JSONField(null=True, blank=True)
    file_type = models.CharField(max_length=10)
    user_id = models.CharField(max_length=100)
    s3_url = models.CharField(max_length=255, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    error = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'exported_files'



# Audit model
class Audit(models.Model):
    AuditId = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=255, null=True, blank=True)
    Scope = models.TextField(null=True, blank=True)
    Objective = models.TextField(null=True, blank=True)
    BusinessUnit = models.CharField(max_length=255, null=True, blank=True)
    Role = models.CharField(max_length=100, null=True, blank=True)
    Responsibility = models.CharField(max_length=255, null=True, blank=True)
    Assignee = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='assignee', db_column='assignee')
    Auditor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='auditor', db_column='auditor')
    Reviewer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='reviewer', null=True, db_column='reviewer')
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True)
    SubPolicyId = models.ForeignKey('SubPolicy', on_delete=models.CASCADE, db_column='SubPolicyId', null=True)
    DueDate = models.DateField()
    Frequency = models.IntegerField(null=True)
    Status = models.CharField(max_length=45)
    CompletionDate = models.DateTimeField(null=True)
    ReviewStatus = models.CharField(max_length=45, null=True)
    ReviewerComments = models.CharField(max_length=255, null=True)
    AuditType = models.CharField(max_length=1)
    Evidence = models.TextField(null=True, blank=True)
    Comments = models.TextField(null=True, blank=True)
    AssignedDate = models.DateTimeField(null=True, db_column='AssignedDate')
    Reports = models.JSONField(null=True, blank=True)
    ReviewStartDate = models.DateTimeField(null=True)
    ReviewDate = models.DateTimeField(null=True)

    class Meta:
        db_table = 'audit'


# AuditFinding model
class AuditFinding(models.Model):
    AuditFindingsId = models.AutoField(primary_key=True)
    AuditId = models.ForeignKey(Audit, on_delete=models.CASCADE, db_column='AuditId', related_name='findings')
    ComplianceId = models.ForeignKey(Compliance, on_delete=models.CASCADE, db_column='ComplianceId')
    UserId = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserId')
    Evidence = models.TextField()
    Check = models.CharField(max_length=1, choices=[
        ('0', 'Not Started'), 
        ('1', 'In Progress'), 
        ('2', 'Completed'),
        ('3', 'Not Applicable')
    ], default='0')
    MajorMinor = models.CharField(max_length=1, choices=[
        ('0', 'Minor'),
        ('1', 'Major'),
        ('2', 'Not Applicable')
    ], null=True, blank=True)
    HowToVerify = models.TextField(null=True, blank=True)
    Impact = models.TextField(null=True, blank=True)
    Recommendation = models.TextField(null=True, blank=True)
    DetailsOfFinding = models.TextField(null=True, blank=True)
    Comments = models.TextField(null=True, blank=True)
    CheckedDate = models.DateTimeField(null=True, blank=True)
    AssignedDate = models.DateTimeField()
    
    class Meta:
        db_table = 'audit_findings'
        
    def save(self, *args, **kwargs):
        """Override save to ensure AuditId consistency"""
        print(f"DEBUG: Saving AuditFinding {self.AuditFindingsId} with AuditId {self.AuditId.AuditId}")
        super().save(*args, **kwargs)
 
class Incident(models.Model):
    IncidentId = models.AutoField(primary_key=True)
    IncidentTitle = models.CharField(max_length=255)
    Description = models.TextField()
    Mitigation = models.JSONField(null=True, blank=True)
    
    AuditId = models.ForeignKey('Audit', on_delete=models.CASCADE, null=True, blank=True, db_column='AuditId')
    ComplianceId = models.ForeignKey('Compliance', on_delete=models.CASCADE, null=True, blank=True, db_column='ComplianceId')
    
    Date = models.DateField()
    Time = models.TimeField()
    UserId = models.ForeignKey('Users', on_delete=models.CASCADE, null=True, blank=True, db_column='UserId')
    
    Origin = models.CharField(max_length=50)
    Comments = models.TextField(null=True, blank=True)
    RiskCategory = models.CharField(max_length=100, null=True, blank=True)
    RiskPriority = models.CharField(max_length=20, null=True, blank=True)
    Attachments = models.TextField(null=True, blank=True)
    
    CreatedAt = models.DateTimeField(auto_now_add=True)
    Status = models.CharField(max_length=45, null=True, blank=True)
    IdentifiedAt = models.DateTimeField(null=True, blank=True)
    
    RepeatedNot = models.BooleanField(null=True, blank=True)
    CostOfIncident = models.CharField(max_length=45, null=True, blank=True)
    ReopenedNot = models.BooleanField(null=True, blank=True)
    
    RejectionSource = models.CharField(max_length=20, null=True, blank=True, choices=[
        ('INCIDENT', 'Rejected as Incident'),
        ('RISK', 'Rejected from Risk')
    ])
    
    AffectedBusinessUnit = models.CharField(max_length=100, null=True, blank=True)
    SystemsAssetsInvolved = models.TextField(null=True, blank=True)
    GeographicLocation = models.CharField(max_length=100, null=True, blank=True)
    Criticality = models.CharField(max_length=20, null=True, blank=True)
    InitialImpactAssessment = models.TextField(null=True, blank=True)
    InternalContacts = models.TextField(null=True, blank=True)
    ExternalPartiesInvolved = models.TextField(null=True, blank=True)
    RegulatoryBodies = models.TextField(null=True, blank=True)
    RelevantPoliciesProceduresViolated = models.TextField(null=True, blank=True)
    ControlFailures = models.TextField(null=True, blank=True)
    LessonsLearned = models.TextField(null=True, blank=True)
    IncidentClassification = models.CharField(max_length=100, null=True, blank=True)
    PossibleDamage = models.TextField(null=True, blank=True)
    AssignerId = models.IntegerField(null=True, blank=True)
    ReviewerId = models.IntegerField(null=True, blank=True)
    MitigationDueDate = models.DateTimeField(null=True, blank=True)
    AssignedDate = models.DateTimeField(null=True, blank=True)
    AssignmentNotes = models.TextField(null=True, blank=True)
    IncidentFormDetails = models.JSONField(null=True, blank=True)
    MitigationCompletedDate = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'incidents'


class IncidentApproval(models.Model):
    IncidentId = models.IntegerField()
    version = models.CharField(max_length=45)
    ExtractedInfo = models.JSONField(null=True)
    AssigneeId = models.CharField(max_length=45, null=True)
    ReviewerId = models.CharField(max_length=45, null=True)
    ApprovedRejected = models.CharField(max_length=45, null=True)
    Date = models.DateTimeField(null=True, auto_now_add=True)
    
    class Meta:
        db_table = 'incident_approval'
        managed = False  # Since we're connecting to an existing table


class AuditReport(models.Model):
    ReportId = models.AutoField(primary_key=True)
    AuditId = models.ForeignKey(Audit, on_delete=models.CASCADE, db_column='AuditId')
    Report = models.TextField()
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True)
    SubPolicyId = models.ForeignKey('SubPolicy', on_delete=models.CASCADE, db_column='SubPolicyId', null=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')

    class Meta:
        db_table = 'audit_report'
# Risk model

# Workflow model
class Workflow(models.Model):
    Id = models.AutoField(primary_key=True)
    FindingId = models.ForeignKey(AuditFinding, on_delete=models.CASCADE, db_column='finding_id')
    IncidentId = models.ForeignKey(Incident, on_delete=models.CASCADE, db_column='IncidentId')
    AssigneeId = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='assignee_id', related_name='workflow_assignee')
    ReviewerId = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='reviewer_id', related_name='workflow_reviewer')
    AssignedAt = models.DateTimeField()
 
    class Meta:
        db_table = 'workflow'
 
class AuditVersion(models.Model):
    AuditId = models.IntegerField()
    Version = models.CharField(max_length=45)
    ExtractedInfo = models.JSONField()
    UserId = models.IntegerField()
    ApprovedRejected = models.CharField(max_length=45, null=True, blank=True)
    Date = models.DateTimeField(auto_now_add=True)
    ActiveInactive = models.CharField(max_length=1, default='1')

    class Meta:
        db_table = 'audit_version'
        unique_together = ('AuditId', 'Version')

    def __str__(self):
        return f"AuditVersion(AuditId={self.AuditId}, Version={self.Version})"
    



class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    recipient = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    channel = models.CharField(max_length=20)  # 'email' or 'whatsapp'
    success = models.BooleanField()
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'


class S3File(models.Model):
    url = models.TextField()
    file_type = models.CharField(max_length=50, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 's3_files'

    def __str__(self):
        return f"{self.file_name} ({self.file_type}) - {self.user_id}"



class Risk(models.Model):
    RiskId = models.AutoField(primary_key=True)  # Primary Key
    ComplianceId = models.IntegerField(null=True)
    RiskTitle = models.CharField(max_length=50, null=True)
    Criticality = models.TextField(null=True)
    PossibleDamage = models.TextField(null=True)
    Category = models.CharField(max_length=100, null=True)
    RiskType = models.CharField(max_length=50, null=True)
    BusinessImpact = models.CharField(max_length=50, null=True)
    RiskPriority = models.CharField(max_length=50, null=True)
    RiskDescription = models.TextField(null=True)
    RiskLikelihood = models.IntegerField(null=True)
    RiskImpact = models.IntegerField(null=True)
    RiskExposureRating = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    RiskMitigation = models.TextField(null=True)
    CreatedAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'risk'  # Ensure Django uses the correct table in the database

    def __str__(self):
        return f"Risk {self.RiskId}"

class RiskInstance(models.Model):
    RiskInstanceId = models.AutoField(primary_key=True)
    RiskId = models.IntegerField(null=True)
    IncidentId = models.IntegerField(null=True)
    ComplianceId = models.IntegerField(null=True)
    RiskTitle = models.TextField(null=True)
    Criticality = models.CharField(max_length=100, null=True)
    PossibleDamage = models.TextField(null=True)
    Category = models.CharField(max_length=100, null=True)
    Appetite = models.CharField(max_length=50, null=True)
    RiskDescription = models.TextField(null=True)
    RiskLikelihood = models.FloatField(null=True)
    RiskImpact = models.FloatField(null=True)
    RiskExposureRating = models.FloatField(null=True)
    RiskPriority = models.CharField(max_length=50, null=True)
    RiskResponseType = models.CharField(max_length=100, null=True)
    RiskResponseDescription = models.TextField(null=True)
    RiskMitigation = models.JSONField(null=True, blank=True)
    RiskType = models.TextField(null=True)
    RiskOwner = models.CharField(max_length=255, null=True)
    Reviewer=models.CharField(max_length=255, null=True)
    ReportedBy = models.IntegerField(null=True)
    RiskStatus = models.CharField(max_length=50, null=True)
    BusinessImpact = models.TextField(null=True)
    Origin = models.CharField(max_length=50, null=True)
    UserId = models.IntegerField(null=True)
    MitigationDueDate = models.DateField(null=True)
    ModifiedMitigations = models.JSONField(null=True)
    MitigationStatus = models.CharField(max_length=45, null=True)
    MitigationCompletedDate = models.DateField(null=True)
    ReviewerCount = models.IntegerField(null=True)
    RiskFormDetails = models.JSONField(null=True, blank=True)
    RecurrenceCount = models.IntegerField(default=1, null=True)
    CreatedAt = models.DateField(auto_now_add=True)
    FirstResponseAt=models.DateTimeField(null=True)


    # Define choices for RiskStatus
    STATUS_NOT_ASSIGNED = 'Not Assigned'
    STATUS_ASSIGNED = 'Assigned'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    
    RISK_STATUS_CHOICES = [
        (STATUS_NOT_ASSIGNED, 'Not Assigned'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    # Define choices for MitigationStatus
    MITIGATION_YET_TO_START = 'Yet to Start'
    MITIGATION_IN_PROGRESS = 'Work In Progress'
    MITIGATION_REVISION_REVIEWER = 'Revision Required by Reviewer'
    MITIGATION_REVISION_USER = 'Revision Required by User'
    MITIGATION_COMPLETED = 'Completed'
    
    MITIGATION_STATUS_CHOICES = [
        (MITIGATION_YET_TO_START, 'Yet to Start'),
        (MITIGATION_IN_PROGRESS, 'Work In Progress'),
        (MITIGATION_REVISION_REVIEWER, 'Revision Required by Reviewer'),
        (MITIGATION_REVISION_USER, 'Revision Required by User'),
        (MITIGATION_COMPLETED, 'Completed'),
    ]
    
    # Update the field definitions to use choices
    RiskStatus = models.CharField(max_length=50, choices=RISK_STATUS_CHOICES, default=STATUS_NOT_ASSIGNED, null=True)
    MitigationStatus = models.CharField(max_length=45, choices=MITIGATION_STATUS_CHOICES, default=MITIGATION_YET_TO_START, null=True)
    
    def __str__(self):
        return f"Risk Instance {self.RiskInstanceId}"

    class Meta:
        db_table = 'risk_instance'  # Ensure Django uses the correct table name in the database
        managed = False  # Since we're connecting to an existing table


class RiskAssignment(models.Model):
    risk = models.ForeignKey('Risk', on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(Users, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='risk_assignments_created')
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'risk_assignments'
    
    def __str__(self):
        return f"Risk {self.risk.RiskId} assigned to {self.assigned_to.UserName}"


class RiskApproval(models.Model):
    RiskInstanceId = models.IntegerField()
    version = models.CharField(max_length=45)
    ExtractedInfo = models.JSONField(null=True)
    UserId = models.CharField(max_length=45, null=True)
    ApproverId = models.CharField(max_length=45, null=True)
    ApprovedRejected = models.CharField(max_length=45, null=True)
    Date = models.DateTimeField(null=True, auto_now_add=True)
    
    class Meta:
        db_table = 'grc.risk_approval'
        managed = False  # Since we're connecting to an existing table


class GRCLog(models.Model):
    LogId = models.AutoField(primary_key=True)
    Timestamp = models.DateTimeField(auto_now_add=True)
    UserId = models.CharField(max_length=50, null=True)
    UserName = models.CharField(max_length=100, null=True)
    Module = models.CharField(max_length=100, null=True)
    ActionType = models.CharField(max_length=50, null=True)
    EntityId = models.CharField(max_length=50, null=True)
    EntityType = models.CharField(max_length=50, null=True)
    LogLevel = models.CharField(max_length=20, default='INFO')
    Description = models.TextField(null=True)
    IPAddress = models.CharField(max_length=45, null=True)
    AdditionalInfo = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'grc_logs'

    def __str__(self):
        return f"Log {self.LogId}: {self.ActionType} on {self.Module}"