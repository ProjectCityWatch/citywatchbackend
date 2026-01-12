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


# -------------------------------
# Like Serializer
# -------------------------------
class ComplaintLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='UserId.Name')

    class Meta:
        model = ComplaintLike
        fields = ['id', 'user_name', 'LikedAt']


# -------------------------------
# Comment Serializer
# -------------------------------
class ComplaintCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='UserId.Name')

    class Meta:
        model = ComplaintComment
        fields = ['id', 'user_name', 'CommentText', 'CreatedAt']


# -------------------------------
# Points Serializer
# -------------------------------
class PointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTable
        fields = ['Points', 'CreatedDate']


# -------------------------------
# MAIN Complaint Serializer
# -------------------------------
class ComplaintsSerializer1(serializers.ModelSerializer):
    Name = serializers.CharField(source='UserId.Name')
    likes = ComplaintLikeSerializer(many=True, read_only=True)
    comments = ComplaintCommentSerializer(many=True, read_only=True)
    points = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintsTable
        fields = [
            'id',
            'Category',
            'Description',
            'Priority',
            'Image',
            'Latitude',
            'Longitude',
            'Status',
            'SubmitDate',
            'Name',
            'total_likes',
            'total_comments',
            'likes',
            'comments',
            'points',
        ]

    def get_points(self, obj):
        points = PointsTable.objects.filter(ComplaintId=obj).first()
        return PointsSerializer(points).data if points else None

    def get_total_likes(self, obj):
        return obj.likes.count()

    def get_total_comments(self, obj):
        return obj.comments.count()

class AddComplaintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintsTable
        fields = ['Category', 'Description', 'Priority', 'Image', 'Latitude' , 'Longitude','SubmitDate']

        
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackTable
        fields = '__all__'


class TimeLineSerializer(serializers.ModelSerializer):
    Description = serializers.CharField(source='ComplaintId.Description')
    Category = serializers.CharField(source ='ComplaintId.Category' )
    SubmitDate = serializers.DateTimeField(source ='ComplaintId.SubmitDate')
    Image = serializers.FileField(source = 'ComplaintId.Image')
    class Meta:
        model = TimeLineTable
        fields = ['Status','Remark','Date','Description','Category','SubmitDate','Image']

class NotificationSerializer(serializers.ModelSerializer):
    comp_id = serializers.CharField(source='ComplaintsId.id', read_only=True)
    Description = serializers.CharField(source='ComplaintsId.Description', read_only=True)
    status = serializers.CharField(source='ComplaintsId.Status', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'Description','comp_id', 'Date', 'status']        