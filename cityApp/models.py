from django.utils import timezone
from django.db import models

# Create your models here.

class LoginTable(models.Model):
    Username = models.CharField(max_length=30, null=True, blank=True)
    Password = models.CharField(max_length=30, null = True, blank=True)
    UserType = models.CharField(max_length=30, null= True, blank=True)


class UserTable(models.Model):
    LoginId = models.ForeignKey(LoginTable, on_delete=models.CASCADE)
    Name = models.CharField(max_length=30, null=True, blank=True)
    PhoneNo = models.CharField(max_length=10, null=True, blank=True)
    Email = models.CharField(max_length=30, null=True, blank=True)

class DepartmentsTable(models.Model):
    DepartmentName = models.CharField(max_length=30, null=True, blank=True)
    LoginId = models.ForeignKey(LoginTable, on_delete=models.CASCADE)
    HeadName = models.CharField(max_length=30, null=True, blank=True)
    Address = models.CharField(max_length=255, null=True, blank=True)
    ContactInfo = models.CharField(max_length=255, null=True, blank=True)
    Email = models.CharField(max_length=30, null=True, blank=True)

class ComplaintsTable(models.Model):
    UserId = models.ForeignKey(UserTable, on_delete=models.CASCADE)
    DepartmentId = models.ForeignKey(DepartmentsTable, on_delete= models.CASCADE)
    Category = models.CharField(max_length=30, null=True, blank=True)
    Description = models.CharField(max_length=100, null=True, blank=True)
    Priority = models.CharField(max_length=30,null=True, blank=True)
    Image = models.FileField(null=True, blank=True)
    Location = models.CharField(max_length=255, null=True, blank=True)
    Status = models.CharField(max_length=30, null=True, blank=True)
    SubmitDate = models.DateTimeField(auto_now_add=True)
    DeadlineDate = models.DateTimeField(null= True, blank=True)
    ResolvedDate = models.DateTimeField(null= True, blank=True)

class FeedbackTable(models.Model):
    UserId = models.ForeignKey(UserTable, on_delete=models.CASCADE)
    ComplaintId = models.ForeignKey(ComplaintsTable, on_delete=models.CASCADE)
    FeedbackText = models.TextField(default="No feedback provided")  
    DateSubmitted = models.DateField(default=timezone.now)
    Replay = models.TextField(null=True, blank=True)

class Notification(models.Model):
    Type=models.CharField(max_length=10, null=True, blank=True)
    Subject=models.CharField(max_length=50, null=True, blank=True)
    Message=models.CharField(max_length=100, null=True, blank=True)
    Date = models.DateTimeField(auto_now_add=True)




