from rest_framework import serializers

from cityApp.models import *


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginTable
        fields = ["Username","Password", "UserType"]
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTable
        fields = ["Name", "PhoneNo", "Email", "LoginId"]
        extra_kwargs = {
            "LoginId": {"required": False}
        }

    def validate_Email(self, value):
        if UserTable.objects.filter(Email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value


class DepartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentsTable
        fields = '__all__'


class ComplaintsSerializer(serializers.ModelSerializer):
    Name = serializers.CharField(source='UserId.Name')
    class Meta:
        model = ComplaintsTable
        fields = ['id','Category', 'Description', 'Priority', 'Image', 'Latitude' , 'Longitude','Status','SubmitDate','Description', 'Name']

class AddComplaintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintsTable
        fields = ['Category', 'Description', 'Priority', 'Image', 'Latitude' , 'Longitude','SubmitDate']

        
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackTable
        fields = '__all__'
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'        

class TimeLineSerializer(serializers.ModelSerializer):
    Description = serializers.CharField(source='ComplaintId.Description')
    Category = serializers.CharField(source ='ComplaintId.Category' )
    SubmitDate = serializers.DateTimeField(source ='ComplaintId.SubmitDate')
    Image = serializers.FileField(source = 'ComplaintId.Image')
    class Meta:
        model = TimeLineTable
        fields = ['Status','Remark','Date','Description','Category','SubmitDate','Image']