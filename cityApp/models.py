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
    Email = models.CharField(max_length=30, unique=True, null=True, blank=True)
    warnings = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

class DepartmentsTable(models.Model):
    DepartmentName = models.CharField(max_length=30, null=True, blank=True)
    LoginId = models.ForeignKey(LoginTable, on_delete=models.CASCADE)
    HeadName = models.CharField(max_length=30, null=True, blank=True)
    Address = models.CharField(max_length=255, null=True, blank=True)
    ContactInfo = models.CharField(max_length=255, null=True, blank=True)
    Email = models.CharField(max_length=30, null=True, blank=True)

class ComplaintsTable(models.Model):
    UserId = models.ForeignKey(UserTable, on_delete=models.CASCADE)
    DepartmentId = models.ForeignKey(DepartmentsTable, on_delete=models.CASCADE, null=True, blank=True)
    Category = models.CharField(max_length=30, null=True, blank=True)
    Description = models.CharField(max_length=100, null=True, blank=True)
    Priority = models.CharField(max_length=30, null=True, blank=True)
    Image = models.FileField(null=True, blank=True)
    EndingDate=models.DateField(null=True,blank=True)
    Status = models.CharField(max_length=30, default="pending")

    Latitude = models.FloatField(
        null=True, blank=True
    )
    Longitude = models.FloatField(
        null=True, blank=True
    )

    SubmitDate = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(null=True, blank=True)

class TimeLineTable(models.Model):
    ComplaintId = models.ForeignKey(
        ComplaintsTable,
        on_delete=models.CASCADE,
    )
    Status = models.CharField(max_length=30)
    Remark = models.CharField(max_length=255, null=True, blank=True)
    Date = models.DateTimeField(default=timezone.now)
    EndingDate = models.DateField(null=True, blank=True)

class FeedbackTable(models.Model):
    UserId = models.ForeignKey(UserTable, on_delete=models.CASCADE)
    FeedbackText = models.TextField(default="No feedback provided")  
    DateSubmitted = models.DateField(default=timezone.now)
    Replay = models.TextField(null=True, blank=True)

class AssignWork(models.Model):
    ComplaintId = models.ForeignKey(ComplaintsTable, on_delete=models.CASCADE)
    EndingDate=models.DateField(null=True,blank=True)
    Status = models.CharField(max_length=30, default="pending")  

class Notification(models.Model):
    ComplaintsId=models.ForeignKey(ComplaintsTable,on_delete=models.CASCADE,null=True,blank=True)
    Date = models.DateTimeField(auto_now_add=True)

class ComplaintLike(models.Model):
    ComplaintId = models.ForeignKey(ComplaintsTable,on_delete=models.CASCADE, related_name="likes")
    UserId = models.ForeignKey(UserTable,on_delete=models.CASCADE)
    LikedAt = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("ComplaintId", "UserId")  # 🚫 prevents double-like

class ComplaintComment(models.Model):
    ComplaintId = models.ForeignKey(ComplaintsTable,on_delete=models.CASCADE,related_name="comments")
    UserId = models.ForeignKey(UserTable,on_delete=models.CASCADE)
    CommentText = models.TextField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

class PointsTable(models.Model):
    ComplaintId = models.ForeignKey(ComplaintsTable,on_delete=models.CASCADE)
    Points = models.IntegerField()
    CreatedDate = models.DateTimeField(auto_now_add=True)

class BadgeTable(models.Model):
    ComplaintId = models.ForeignKey(ComplaintsTable,on_delete=models.CASCADE)
    Badge = models.CharField(max_length=20)
    CreatedDate = models.DateTimeField(auto_now_add=True)










