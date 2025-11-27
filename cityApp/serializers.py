from rest_framework import serializers

from cityApp.models import *


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginTable
        fields = ["Username","Password", "UserType"]
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTable
        fields = ["Name","PhoneNo", "Email",]
class DepartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentsTable
        fields = '__all__'
class ComplaintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintsTable
        fields = '__all__'
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackTable
        fields = '__all__'
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'        

