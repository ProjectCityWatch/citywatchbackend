from django.contrib import admin

from cityApp.models import *

# Register your models here.
admin.site.register(LoginTable)
admin.site.register(UserTable)
admin.site.register(DepartmentsTable)
admin.site.register(ComplaintsTable)
admin.site.register(FeedbackTable)
admin.site.register(Notification)
admin.site.register(AssignWork)
admin.site.register(TimeLineTable)
admin.site.register(PointsTable)
admin.site.register(ComplaintComment)
admin.site.register(ComplaintLike)
admin.site.register(BadgeTable)