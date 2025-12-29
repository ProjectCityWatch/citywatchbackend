
from django.urls import path

from cityApp.views import *

urlpatterns = [
   
    path('', LoginView.as_view(), name='login'),

    # --- ADMINISTRATION ---
path('adminhome/', AddAdminHomeView.as_view(), name='adminhome'),
path('add-department/', AddDepartmentView.as_view(), name='add_department'),
path('assign-works/', AssignWorks.as_view(), name='assign_works'),
path('DeleteDepartment/<int:d_id>', DeleteDepartment.as_view(), name='DeleteDepartment'),
path('manage-department/', ManageDepartmentView.as_view(), name='manage_department'),
path('manage-users/', ManageUsersView.as_view(), name='manage_users'),
path('BlockUser/<int:l_id>', BlockUser.as_view(), name='BlockUser'),
path('UnblockUser/<int:l_id>', UnblockUser.as_view(), name='UnblockUser'),
path('notification/', NotificationView.as_view(), name='notification'),
path('send-notifications/', SendNotificationsView.as_view(), name='send_notifications'),
path('notificationview/', ViewNotification.as_view(), name='notificationview'),
path('submit-work/<int:id>/', SubmitWorkView.as_view(), name='submit_work'),
path('feedbackview/', ViewFeedback.as_view(), name='ViewFeedback'),
path('viewcomplaints/', ViewComplaints.as_view(), name='viewcomplaints'),

  # --- AUTHORITY ---
path('authorityhome/', AuthorityHomeView.as_view(), name='authorityhome'),
path('update/', UpdateView.as_view(), name='update'),
path('updatestatus/<int:cid>/', UpdateStatusView.as_view(), name='update_status'),
path('viewfeedback/', ViewFeedbackView.as_view(), name='viewfeedback'),
path('viewcomplaintsview/', ViewComplaintsView.as_view(), name='viewcomplaintsview'),
path('authorityprofile/', AuthorityProfileView.as_view(), name='authorityprofile'),
path('submit-work/<int:complaint_id>/', SubmitWorkView.as_view(), name='submit_work'),
path('replay/<int:id>', ReplayView.as_view()),
path('request_ending_date',request_ending_date.as_view(),name='request_ending_date'),
path('UpdateStatus/<int:c_id>', UpdateStatus.as_view(), name="UpdateStatus"),
path('updatedeadline/', UpdateDeadlineView.as_view(), name='updatedeadline'),



    #####################################API###############################

    path('UserLogin', LoginAPI.as_view(), name='userlogin'),
    path('User', UserRegistration.as_view(), name='register'),
   


]
