from django.contrib import admin

from cityApp.models import AssignWork, ComplaintsTable, DepartmentsTable, FeedbackTable, LoginTable, Notification, TimeLineTable, UserTable

# Register your models here.
admin.site.register(LoginTable)
admin.site.register(UserTable)
admin.site.register(DepartmentsTable)
admin.site.register(ComplaintsTable)
admin.site.register(FeedbackTable)
admin.site.register(Notification)
admin.site.register(AssignWork)
admin.site.register(TimeLineTable)