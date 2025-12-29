from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from rest_framework.views import APIView
from rest_framework.views import Response
from rest_framework.views import status
from cityApp.models import *
from cityApp.form import *
from cityApp.serializers import *

# --- Login ---
class LoginView(View):
    def get(self, request):
        return render(request, 'Login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = LoginTable.objects.get(Username=username, Password=password)
            request.session['loginid'] = user.id

            if user.UserType == 'admin':
                return redirect('adminhome')
            elif user.UserType == 'Authority':
                return redirect('authorityhome')
            else:
                return render(request, 'Login.html', {'error': 'Invalid user type'})
        except LoginTable.DoesNotExist:
            return render(request, 'Login.html', {'error': 'Invalid username or password'})

# -------------------------------------------------- Administration ---------------------------------
class AddAdminHomeView(View):
    def get(self, request):
        return render(request, 'Administration/adminhome.html')
    
class AddDepartmentView(View): 
    def get(self, request): 
        return render(request, 'Administration/adddepartment.html')
    def post(self, request):
        department_name = request.POST['department_name']
        address = request.POST['address']
        contact = request.POST['contact']
        head = request.POST['head']
        password = request.POST['password']
        email = request.POST['Email']
        login_obj = LoginTable()
        login_obj.Username=department_name
        login_obj.Password=password
        login_obj.save()
        obj = DepartmentsTable()
        obj.DepartmentName=department_name
        obj.Address=address
        obj.Email = email
        obj.ContactInfo=contact
        obj.HeadName=head
        obj.LoginId=login_obj
        obj.save()
        return HttpResponse('''<script>alert('Department Added');window.location='/manage-department';</script>''')

class   AssignWorks(View):
    def get(self, request):
        complaints = ComplaintsTable.objects.all()
        departments = DepartmentsTable.objects.all()

        # assigned complaint IDs
        assigned_ids = list(
            AssignWork.objects.values_list('ComplaintId_id', flat=True)
        )

        # FILTERS
        department_id = request.GET.get('department')
        status = request.GET.get('status')

        if department_id and department_id != "all":
            complaints = complaints.filter(DepartmentId_id=department_id)

        if status == "assigned":
            complaints = complaints.filter(id__in=assigned_ids)
        elif status == "not_assigned":
            complaints = complaints.exclude(id__in=assigned_ids)
        return render(
            request,
            'Administration/assignworks.html',
            {
                'val': complaints,
                'departments': departments,
                'assigned_ids': assigned_ids,
                'selected_department': department_id,
                'selected_status': status
            }
        )



# class   AssignWorks(View):
#     def get(self, request):
#         complaints = ComplaintsTable.objects.all()
#         departments = DepartmentsTable.objects.all()

#         # assigned complaint IDs
#         assigned_ids = list(
#             AssignWork.objects.values_list('ComplaintId_id', flat=True)
#         )

#         # FILTERS
#         department_id = request.GET.get('department')
#         status = request.GET.get('status')

#         if department_id and department_id != "all":
#             complaints = complaints.filter(DepartmentId_id=department_id)

#         if status == "assigned":
#             complaints = complaints.filter(id__in=assigned_ids)
#         elif status == "not_assigned":
#             complaints = complaints.exclude(id__in=assigned_ids)

#         return render(
#             request,
#             'Administration/assignworks.html',
#             {
#                 'val': complaints,
#                 'departments': departments,
#                 'assigned_ids': assigned_ids,
#                 'selected_department': department_id,
#                 'selected_status': status
#             }
#         )





class DeleteDepartment(View):
    def get(self, request, d_id):
        obj = DepartmentsTable.objects.get(id=d_id)
        obj.delete()
        return redirect('manage_department')


class ManageDepartmentView(View):
    def get(self, request):
        obj = DepartmentsTable.objects.all()
        return render(request, 'Administration/managedepartment.html', {'val': obj})


class ManageUsersView(View):
    def get(self, request):
        obj = UserTable.objects.all()
        return render(request, 'Administration/manageusers.html', {'val': obj})
    

class BlockUser(View):
    def get(self, request,l_id):
        obj = LoginTable.objects.get(id = l_id)
        obj.UserType = 'Blocked'
        obj.save()
        return HttpResponse('''<script>alert('User Blocked');window.location='/manage-users';</script>''')
        

class UnblockUser(View):
    def get(self, request,l_id):
        obj = LoginTable.objects.get(id = l_id)
        obj.UserType = 'user'
        obj.save()
        return HttpResponse('''<script>alert('User Unblocked');window.location='/manage-users';</script>''')

class NotificationView(View):
    def get(self, request):
        return render(request, 'Administration/notification.html')


class SendNotificationsView(View):
    def get(self, request):
        obj =Notification.objects.all()
        return render(request, 'Administration/sendnotifications.html',{'val': obj})


class SubmitWorkView(View):
    def post(self, request, id):
        complaint = ComplaintsTable.objects.get(id=id)
        complaint.Status="Assigned"
        complaint.save()

        time_line_obj = TimeLineTable()
        time_line_obj.ComplaintId = ComplaintsTable.objects.get(id=complaint.id)
        time_line_obj.Status="Assigned"
        time_line_obj.save()

        return HttpResponse(
            "<script>alert('Work Assigned Successfully');window.location='/assign-works/';</script>"
        )
# class SubmitWorkView(View):
#     def post(self, request, id):
#         assigned_date = request.POST.get('deadline')

#         complaint = ComplaintsTable.objects.get(id=id)

#         # prevent duplicate assignment
#         if AssignWork.objects.filter(ComplaintId=complaint).exists():
#             return HttpResponse(
#                 "<script>alert('This complaint is already assigned');window.location='/assign-works/';</script>"
#             )

#         AssignWork.objects.create(
#             ComplaintId=complaint,
#             AssignedDate=assigned_date
#         )

#         return HttpResponse(
#             "<script>alert('Work Assigned Successfully');window.location='/assign-works/';</script>"
#         )

class UpdateStatus(View):
    def post(self, request, c_id):
        complaint = ComplaintsTable.objects.get(id=c_id)
        complaint.Status = request.POST['status']
        complaint.save()
        time_line_obj = TimeLineTable()
        time_line_obj.ComplaintId = complaint
        time_line_obj.Status = request.POST['status']
        time_line_obj.save()
        return HttpResponse(
            "<script>alert('Status updated Successfully');window.location='/viewcomplaintsview/';</script>"
        )
        

        


class ViewComplaints(View):
    def get(self, request):
        obj =ComplaintsTable.objects.all()
        print(obj)
        return render(request, 'Administration/viewcomplaints.html', {'val':obj})

class ViewFeedback(View):
    def get(self, request):
        feedbacks = FeedbackTable.objects.all()
        return render(request, 'Administration/feedbackview.html', {'feedbacks': feedbacks})

    def post(self, request):
        feedback_id = request.POST.get('feedback_id')
        reply_text = request.POST.get('reply')

        feedback = FeedbackTable.objects.get(id=feedback_id)
        feedback.Replay = reply_text
        feedback.save()

        return redirect('ViewFeedback')
    
class ViewNotification(View):
    def get(self, request):
        notifications = Notification.objects.select_related(
            'Assignid__ComplaintId__DepartmentId'
        ).order_by('-Date')

        return render(
            request,
            'Administration/notificationview.html',
            {'notifications': notifications}
        )


# ------------------------------ Authority ---------------------------------------
class AuthorityHomeView(View):
    def get(self, request):
        return render(request, 'Authority/authorityhome.html')


class UpdateView(View):
    def get(self, request):
        return render(request, 'Authority/update.html')


class UpdateStatusView(View):
    def get(self, request, cid):
        c = ComplaintsTable.objects.get(id=cid)
        return render(request, 'Authority/updatestatus.html', {'val': c})
    def post(self, request, cid):
        c = ComplaintsTable.objects.get(id=cid)
        status = request.POST['status']
        c.Status = status
        c.save()
         
       
        return HttpResponse('''<script>alert('Status changed successfully');window.location='/viewcomplaintsview';</script>''')

class ViewFeedbackView(View):
    def get(self, request):
        feedback = FeedbackTable.objects.all()
        return render(request, 'Authority/viewfeedbacktable.html', {'feedback': feedback})

class ReplayView(View):
    def post(self, request, id):
        c = FeedbackTable.objects.get(id = id)
        replay = ReplayForm(request.POST, instance=c)
        if replay.is_valid():
            replay.save()
        return HttpResponse('''<script>alert('Replayed successfully');window.location='/viewfeedback/';</script>''')


class ViewComplaintsView(View):
    def get(self, request):
        complaints = ComplaintsTable.objects.filter(DepartmentId__LoginId_id=request.session['loginid'])
        return render(request, 'Authority/viewcomplaints.html', {'val': complaints})
    
# class ViewComplaintsView(View):
#     def get(self, request):
#         complaints = ComplaintsTable.objects.all()

#         for c in complaints:
#             try:
#                 assign = AssignWork.objects.get(ComplaintId=c)
#                 c.EndingDate = assign.EndingDate
#                 c.work_status = assign.Status
#             except AssignWork.DoesNotExist:
#                 c.assigned_date = None
#                 c.work_status = "Not Assigned"

#         return render(request, 'Authority/viewcomplaints.html', {'val': complaints})
    

    def post(self, request):
        complaint_id = request.POST.get('complaint_id')
        status = request.POST.get('status')

        assign = get_object_or_404(AssignWork, ComplaintId_id=complaint_id)

        assign.Status = status
        assign.save()

        Notification.objects.create(
            Assignid=assign,
            Message=f"The assigned work status is {status}"
        )

        return HttpResponse(
            "<script>alert('Status changed successfully');"
            "window.location='/viewcomplaintsview';</script>"
        )
class request_ending_date(View):
    def post(self,request):
     if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        print(complaint_id,'************')
        ending_date = request.POST.get("date")
        print(ending_date,'&&&&&&&&')

        complaint = ComplaintsTable.objects.get(id=complaint_id)
        complaint.EndingDate=ending_date
        complaint.Status='Requested'
        complaint.save()
        time_line_obj=TimeLineTable()
        time_line_obj.ComplaintId = ComplaintsTable.objects.get(id=complaint.id)
        time_line_obj.Status = "Requested"
        time_line_obj.save()

        return HttpResponse(
            "<script>alert('successfully Requested');"
            "window.location='/viewcomplaintsview';</script>"
        )
    


    
class AuthorityProfileView(View):
    def get(self, request):
        obj = DepartmentsTable.objects.get(LoginId_id=request.session['loginid'])
        return render(request, 'Authority/authorityprofile.html', {'val':obj})
    def post(self, request):
        c = DepartmentsTable.objects.get(LoginId__id = request.session['loginid'])
        profile = ProfileForm(request.POST, instance=c)
        if profile.is_valid():
            profile.save()
        return HttpResponse('''<script>alert('Updated successfully');window.location='/authorityhome/';</script>''')

class UpdateDeadlineView(View):
    def get(self, request):
        return render(request, 'Authority/updatedeadline.html')

    def post(self, request):
        date = request.POST.get('date')
        reason = request.POST.get('reason')

        # later you can save to DB
        print(date, reason)

        return render(request, 'Authority/updatedeadline.html')  

#############################################  API ###########################################

class UserRegistration(APIView):
    def post(self, request):
        print("++++++++++++++", request.data)

        # LOGIN CREDENTIALS
        login_serial = LoginSerializer(data={
            "Username": request.data.get("Username"),
            "Password": request.data.get("Password"),
            "UserType": "USER"
        })

        # USER BASIC DATA
        user_serial = UserSerializer(data=request.data)

        if login_serial.is_valid():
            login_obj = login_serial.save()

            if user_serial.is_valid():
                user_serial.save(LoginId=login_obj)
                return Response(
                    {"status": "success",
                     "message": "User Registered Successfully",
                     "user": user_serial.data},
                    status=status.HTTP_201_CREATED
                )

            # delete login if user fails
            login_obj.delete()
            return Response(
                {"status": "error", "errors": user_serial.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"status": "error", "errors": login_serial.errors},
            status=status.HTTP_400_BAD_REQUEST
        )



class LoginAPI(APIView):
    def post(self, request):
        username = request.data.get("Username")
        password = request.data.get("Password")

        try:
            user = LoginTable.objects.get(Username=username)
        except LoginTable.DoesNotExist:
            return Response(
                {"status": "error", "message": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.Password != password:
            return Response(
                {"status": "error", "message": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            {"status": "success", "message": "Login successful", "userId": user.id},
            status=status.HTTP_200_OK
        )

