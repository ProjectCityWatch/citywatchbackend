from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from rest_framework.views import APIView
from rest_framework.views import Response
from rest_framework.views import status
from cityApp.models import *
from cityApp.form import *
from cityApp.serializers import *
from django.db.models import Exists, OuterRef, Subquery
from django.db.models import Sum
from .models import PointsTable
import requests
from requests.auth import HTTPBasicAuth

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from cityApp.models import UserTable
from cityApp.serializers import AddComplaintsSerializer


# =====================================================
# IMAGGA CONFIG (FREE & CONFIRMED)
# =====================================================

IMAGGA_API_KEY = "acc_dc4bc19828e5b88"
IMAGGA_API_SECRET = "aed3d3c05b419865f1928f5d4b6934e4"
IMAGGA_ENDPOINT = "https://api.imagga.com/v2/tags"




def recalculate_user_points(user):
    total = PointsTable.objects.filter(
        ComplaintId__UserId=user
    ).aggregate(total=Sum('Points'))['total']

    # If no points exist, make it 0
    user.total_points = total if total is not None else 0
    user.save()


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
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from .models import ComplaintsTable, PointsTable

class MarkFakeComplaint(View):
    def post(self, request, c_id):
        complaint = get_object_or_404(ComplaintsTable, id=c_id)

        # Prevent double punishment
        if complaint.Status == 'fake':
            return redirect('assign_works')

        # 1️⃣ Mark complaint as fake
        complaint.Status = 'fake'
        complaint.save()

        # 2️⃣ Add warning
        user = complaint.UserId
        user.warnings += 1
        user.save()

        # 3️⃣ Log -100 points
        PointsTable.objects.create(
            ComplaintId=complaint,
            Points=-100
        )

        # 4️⃣ Recalculate & store total points (VIEW LOGIC)
        recalculate_user_points(user)

        return redirect('assign_works')




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
        login_obj.Username=email
        login_obj.Password=password
        login_obj.UserType='Authority'
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

class AssignWorks(View):
    def get(self, request):
        assign_date = AssignWork.objects.filter(
            ComplaintId=OuterRef('pk')
        ).values('EndingDate')[:1]

#         complaints = ComplaintsTable.objects.exclude(
#     Status='fake'
# ).annotate(
#     final_deadline=Subquery(assign_date),
#     deadline_changed=Exists(
#         TimeLineTable.objects.filter(
#             ComplaintId=OuterRef('pk'),
#             Status="Requested"
#         )
#     )
# )
        complaints = ComplaintsTable.objects.annotate(
    final_deadline=Subquery(assign_date),
    deadline_changed=Exists(
        TimeLineTable.objects.filter(
            ComplaintId=OuterRef('pk'),
            Status="Requested"
        )
    )
)


        departments = DepartmentsTable.objects.all()

        assigned_ids = list(
            AssignWork.objects.values_list('ComplaintId_id', flat=True)
        )

        department_id = request.GET.get('department')
        status = request.GET.get('status')

        if status == "assigned":
            complaints = complaints.exclude(Status='fake').filter(id__in=assigned_ids)

        elif status == "not_assigned":
             complaints = complaints.exclude(Status='fake').exclude(id__in=assigned_ids)

        elif status == "fake":
            complaints = complaints.filter(Status='fake')

        else:
            complaints = complaints.exclude(Status='fake')


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
        obj = UserTable.objects.order_by('-warnings', '-total_points')
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
        obj.UserType = 'USER'
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

        # get requested date from complaint
        requested_date = complaint.EndingDate

        # create or update AssignWork
        assign, created = AssignWork.objects.get_or_create(
            ComplaintId=complaint
        )
        assign.EndingDate = requested_date
        assign.Status = "Assigned"
        assign.save()

        # update complaint status
        complaint.Status = "Assigned"
        complaint.save()

        # timeline entry
        TimeLineTable.objects.create(
            ComplaintId=complaint,
            Status="Assigned",
            Remark=f"Deadline confirmed as {requested_date}"
        )

        return HttpResponse(
            "<script>alert('Work Assigned Successfully');"
            "window.location='/assign-works/';</script>"
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

# class UpdateStatus(View):
#     def post(self, request, c_id):
#         complaint = ComplaintsTable.objects.get(id=c_id)
#         complaint.Status = request.POST['status']
#         complaint.save()
#         time_line_obj = TimeLineTable()
#         time_line_obj.ComplaintId = complaint
#         time_line_obj.Status = request.POST['status']
#         time_line_obj.save()
#         return HttpResponse(
#             "<script>alert('Status updated Successfully');window.location='/viewcomplaintsview/';</script>"
#         )
        
# class UpdateStatus(View):
#     def post(self, request, c_id):
#         status = request.POST.get('status')

#         # update complaint status
#         complaint = ComplaintsTable.objects.get(id=c_id)
#         complaint.Status = status
#         complaint.save(update_fields=['Status'])

#         assign = AssignWork.objects.filter(ComplaintId__id = c_id).first()
#         assign.Status = status
#         assign.save(update_fields=['Status'])

#         # update timeline if exists, else create
#         TimeLineTable.objects.update_or_create(
#             ComplaintId=complaint,
#             defaults={
#                 'Status': status
#             }
#         )

#         return HttpResponse(
#             "<script>alert('Status updated Successfully');"
#             "window.location='/viewcomplaintsview/';</script>"
#         )


# class UpdateStatus(View):
#     def post(self, request, c_id):
#         status = request.POST.get('status')

#         # 1️⃣ Update complaint status
#         complaint = ComplaintsTable.objects.get(id=c_id)
#         user_id=complaint.UserId.id
    
#         complaint.Status = status
#         complaint.save(update_fields=['Status'])
   
#         if status == "Resolved":
#             Point_obj = PointsTable.objects.get(ComplaintId_id=complaint.id)
#             point = Point_obj.Points
#             Point_obj.Points = 200 + point
#             Point_obj.save()
#             obj = BadgeTable.objects.filter(ComplaintId__UserId_id=user_id, ComplaintId__Status="Resolved")
#             if len(obj)==1:
#                 Badge_obj = BadgeTable()
#                 Badge_obj.ComplaintId = complaint
#                 Badge_obj.Badge = 'First Problem Resolved'
#                 Badge_obj.save()

#         # 2️⃣ Update assigned work status (if exists)
#         assign = AssignWork.objects.filter(ComplaintId_id=c_id).first()
#         if assign:
#             assign.Status = status
#             assign.save(update_fields=['Status'])

#         # 3️⃣ ALWAYS create a new timeline entry (HISTORY)
#         TimeLineTable.objects.create(
#             ComplaintId=complaint,
#             Status=status
#         )
#         Notification.objects.create(ComplaintsId=complaint)
#         return HttpResponse(
#             "<script>alert('Status updated Successfully');"
#             "window.location='/viewcomplaintsview/';</script>"
#         )
# 
class UpdateStatus(View):
    def post(self, request, c_id):
        status = request.POST.get('status')

        # ---------------------------------------
        # 1️⃣ Get complaint & user
        # ---------------------------------------
        complaint = ComplaintsTable.objects.get(id=c_id)
        user = complaint.UserId

        # Update complaint status
        complaint.Status = status
        complaint.save(update_fields=['Status'])

        # ---------------------------------------
        # 2️⃣ RESOLUTION LOGIC
        # ---------------------------------------
        if status == "Resolved":

            # 🔹 First Resolution badge + points
            if not BadgeTable.objects.filter(
                ComplaintId__UserId=user,
                Badge="First Problem Resolved"
            ).exists():
                PointsTable.objects.create(ComplaintId=complaint, Points=200)
                BadgeTable.objects.create(
                    ComplaintId=complaint,
                    Badge="First Problem Resolved"
                )
            else:
                PointsTable.objects.create(ComplaintId=complaint, Points=100)

            # ---------------------------------------
            # 🏅 CATEGORY-BASED BADGES
            # ---------------------------------------
            badge_rules = [
                ("Road Damage", "Pothole Pro"),
                ("Waste", "Clean City Champ"),
                ("Water Leak", "Water Watcher"),
                ("Street Light", "Streetlight Saver"),
            ]

            for category, badge_name in badge_rules:
                if (
                    ComplaintsTable.objects.filter(UserId=user, Category=category).count() >= 5 and
                    ComplaintsTable.objects.filter(
                        UserId=user,
                        Category=category,
                        Status="Resolved"
                    ).count() >= 5 and
                    not BadgeTable.objects.filter(
                        ComplaintId__UserId=user,
                        Badge=badge_name
                    ).exists()
                ):
                    BadgeTable.objects.create(
                        ComplaintId=complaint,
                        Badge=badge_name
                    )
                    PointsTable.objects.create(
                        ComplaintId=complaint,
                        Points=200
                    )

            # ---------------------------------------
            # 🏆 LOCAL HERO BADGE
            # ---------------------------------------
            total_resolved = ComplaintsTable.objects.filter(
                UserId=user,
                Status="Resolved"
            ).count()

            if (
                total_resolved >= 10 and
                not BadgeTable.objects.filter(
                    ComplaintId__UserId=user,
                    Badge="Local Hero"
                ).exists()
            ):
                BadgeTable.objects.create(
                    ComplaintId=complaint,
                    Badge="Local Hero"
                )
                PointsTable.objects.create(
                    ComplaintId=complaint,
                    Points=200
                )

            # ---------------------------------------
            # 🔥 TOTAL POINTS RECALCULATION (ADDED)
            # ---------------------------------------
            from django.db.models import Sum

            total = PointsTable.objects.filter(
                ComplaintId__UserId=user
            ).aggregate(total=Sum('Points'))['total']

            user.total_points = total if total is not None else 0
            user.save(update_fields=['total_points'])

        # ---------------------------------------
        # 3️⃣ Update assigned work
        # ---------------------------------------
        assign = AssignWork.objects.filter(ComplaintId_id=c_id).first()
        if assign:
            assign.Status = status
            assign.save(update_fields=['Status'])

        # ---------------------------------------
        # 4️⃣ Timeline
        # ---------------------------------------
        TimeLineTable.objects.create(
            ComplaintId=complaint,
            Status=status
        )



        return HttpResponse(
            "<script>alert('Status updated Successfully');"
            "window.location='/viewcomplaintsview/';</script>"
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
        print(request.session['loginid'])
        complaints = ComplaintsTable.objects.filter(DepartmentId__LoginId_id=request.session['loginid'])
        print("-----------",complaints)
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
        complaint.Status='Date Fixed'
        complaint.save()
        time_line_obj=TimeLineTable()
        time_line_obj.ComplaintId = ComplaintsTable.objects.get(id=complaint.id)
        time_line_obj.Status = "Date Fixed"
        time_line_obj.save()

        # assign = AssignWork.objects.get(ComplaintId__id = complaint_id)
        # assign.EndingDate = ending_date
        # assign.save()

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
    def get(self, request, id):
        c = ComplaintsTable.objects.get(id=id)
        return render(request, 'Authority/updatedeadline.html',{'val':c})


    def post(self, request, id):
        # existing complaint
        c = ComplaintsTable.objects.get(id=id)

        # assigned work (must exist)
        v = AssignWork.objects.get(ComplaintId__id=c.id)

        # form bound to complaint
        d = ComplaintsForm(request.POST, instance=c)

        if d.is_valid():
            reg = d.save(commit=False)

            # update ending date in AssignWork
            v.EndingDate = reg.EndingDate
            v.save(update_fields=['EndingDate'])

            # save complaint
            reg.save()

            # 🔥 CREATE TIMELINE ENTRY ONLY IF EXTENDED
            if reg.Status == "Extended":
                TimeLineTable.objects.create(
                    ComplaintId=c,
                    Status="Extended",
                    EndingDate=reg.EndingDate,
                    Remark=request.POST.get('reason')
                )

            return redirect('/viewcomplaintsview/')


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
    
# class SendComplaintAPI(APIView):
#     def post(self,request,id):
#         print(request.data)
#         user = UserTable.objects.get(LoginId__id=id)
#         serializer=AddComplaintsSerializer(data=request.data)
#         anonymous = request.data.get('is_anonymous')
#         if anonymous == 'false':
#             anonymous=False
#         elif anonymous == 'true':
#             anonymous=True
#         c_obj = ComplaintsTable.objects.filter(UserId__LoginId_id=id) 
#         print("***********************",c_obj) 
#         if len(c_obj) == 0:   
#             if serializer.is_valid():
#                 c=serializer.save(UserId=user, is_anonymous=anonymous)
#                 Point_obj = PointsTable()
#                 Point_obj.ComplaintId = c
#                 Point_obj.Points = 200
#                 Point_obj.save()
#                 Badge_obj = BadgeTable()
#                 Badge_obj.ComplaintId = c
#                 Badge_obj.Badge = 'First Report'
#                 Badge_obj.save()
#                 TimeLineTable.objects.create(ComplaintId=c, Status='Pending')
                
#                 return Response(serializer.data,status=status.HTTP_201_CREATED)
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         else:    
#             if serializer.is_valid():
#                 c=serializer.save(UserId=user, is_anonymous=anonymous)
#                 Point_obj = PointsTable()
#                 Point_obj.ComplaintId = c
#                 Point_obj.Points = 50
#                 Point_obj.save()
#                 TimeLineTable.objects.create(ComplaintId=c, Status='Pending')

#                 return Response(serializer.data,status=status.HTTP_201_CREATED)
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
#     def get(self, request, id):
#         user = UserTable.objects.get(LoginId_id=id) 
#         comp=ComplaintsTable.objects.filter(UserId_id=user)
#         serializer=ComplaintsSerializer(comp, many=True)
#         print("-------------------", serializer.data)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    

# class SendComplaintAPI(APIView):

#     # -------------------------------------------------
#     # POST → Submit complaint
#     # -------------------------------------------------
#     def post(self, request, id):
#         print(request.data)

#         user = get_object_or_404(UserTable, LoginId_id=id)
#         serializer = AddComplaintsSerializer(data=request.data)

#         anonymous = request.data.get('is_anonymous', False)
#         if isinstance(anonymous, str):
#             anonymous = anonymous.lower() == 'true'

#         is_first_complaint = not ComplaintsTable.objects.filter(
#             UserId__LoginId_id=id
#         ).exists()

#         if serializer.is_valid():
#             complaint = serializer.save(
#                 UserId=user,
#                 is_anonymous=anonymous
#             )

#             # Points logic
#             points = 200 if is_first_complaint else 50
#             PointsTable.objects.create(
#                 ComplaintId=complaint,
#                 Points=points
#             )

#             # Badge only for first complaint
#             if is_first_complaint:
#                 BadgeTable.objects.create(
#                     ComplaintId=complaint,
#                     Badge='First Report'
#                 )

#             TimeLineTable.objects.create(
#                 ComplaintId=complaint,
#                 Status='Pending'
#             )

#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # -------------------------------------------------
#     # GET → View complaints
#     # -------------------------------------------------
#     def get(self, request, id):
#         user = get_object_or_404(UserTable, LoginId_id=id)

#         complaints = ComplaintsTable.objects.filter(UserId=user)
#         serializer = ComplaintsSerializer(complaints, many=True)

#         return Response(serializer.data, status=status.HTTP_200_OK)
# ================================
# AI IMAGE ANALYSIS + DEPARTMENT LOGIC
# ================================



# class SendComplaintAPI(APIView):

#     # -------------------------------------------------
#     # POST → Submit complaint
#     # -------------------------------------------------
#     def post(self, request, id):
#         print(request.data)

#         user = get_object_or_404(UserTable, LoginId_id=id)

#         # 🚫 BLOCKED USER CHECK (ONLY ADDITION)
#         if user.LoginId.UserType == 'Blocked':
#             return Response(
#                 {'error': 'You are blocked and cannot submit complaints'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         serializer = AddComplaintsSerializer(data=request.data)

#         anonymous = request.data.get('is_anonymous', False)
#         if isinstance(anonymous, str):
#             anonymous = anonymous.lower() == 'true'

#         is_first_complaint = not ComplaintsTable.objects.filter(
#             UserId__LoginId_id=id
#         ).exists()

#         if serializer.is_valid():
#             complaint = serializer.save(
#                 UserId=user,
#                 is_anonymous=anonymous
#             )
       

#             # Points logic
#             points = 200 if is_first_complaint else 50
#             PointsTable.objects.create(
#                 ComplaintId=complaint,
#                 Points=points
#             )

#             # -------------------------------
#             # 🔥 TOTAL POINTS RECALCULATION
#             # -------------------------------
#             from django.db.models import Sum

#             total = PointsTable.objects.filter(
#                 ComplaintId__UserId=user
#             ).aggregate(total=Sum('Points'))['total']

#             user.total_points = total if total is not None else 0
#             user.save(update_fields=['total_points'])

#             # Badge only for first complaint
#             if is_first_complaint:
#                 BadgeTable.objects.create(
#                     ComplaintId=complaint,
#                     Badge='First Report'
#                 )

#             TimeLineTable.objects.create(
#                 ComplaintId=complaint,
#                 Status='Pending'
#             )

#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------
    # GET → View complaints
    # -------------------------------------------------
    def get(self, request, id):
        user = get_object_or_404(UserTable, LoginId_id=id)

        complaints = ComplaintsTable.objects.filter(UserId=user)
        serializer = ComplaintsSerializer(complaints, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)




class ViewTimelineAPI(APIView):
    def get(self, request, id):
        print("------------------------>", id)
        comp = ComplaintsTable.objects.get(id=id) 
        print("++++++++++++++++",comp)
        TimeLine=TimeLineTable.objects.filter(ComplaintId_id=comp)
        print(TimeLine)
        serializer=TimeLineSerializer(TimeLine, many=True)
        print("------------------>", serializer.data)
        if serializer.data:
         
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
            
    
class SendAck(APIView):
    def post(self,request,id):
        print(request.data)
        complaint = ComplaintsTable.objects.get(id=id)
        complaint.Status = "ACK"
        complaint.save()
        time_line_obj = TimeLineTable()
        time_line_obj.Status = "ACK"
        time_line_obj.ComplaintId=complaint
        time_line_obj.save()
        return Response(status=status.HTTP_400_BAD_REQUEST)

# class ViewAllcomplaintsAPI(APIView):
#     def get(self, request):
#         print("------------------------>", id)
#         comp = ComplaintsTable.objects.all() 
#         serializer=ComplaintsSerializer1(comp, many=True)
#         print("------------------>", serializer.data)
#         if serializer.data:
         
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
           
#             return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

class ViewAllcomplaintsAPI(APIView):

    def get(self, request):
        complaints = ComplaintsTable.objects.all().order_by('-SubmitDate')

        if not complaints.exists():
            return Response(
                {"message": "No complaints found"},
                status=status.HTTP_204_NO_CONTENT
            )

        serializer = ComplaintsSerializer1(complaints, many=True)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ComplaintLikeAPI(APIView):
    def post(self, request, lid):
        try:
            user = UserTable.objects.get(LoginId_id=lid)
            complaint = ComplaintsTable.objects.get(id=request.data.get('ComplaintId'))
        except (UserTable.DoesNotExist, ComplaintsTable.DoesNotExist):
            return Response(
                {"status": "error", "message": "Invalid data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        like_obj = ComplaintLike.objects.filter(
            ComplaintId=complaint,
            UserId=user
        )

        # TOGGLE LIKE
        if like_obj.exists():
            like_obj.delete()
            return Response(
                {"status": "unliked"},
                status=status.HTTP_200_OK
            )
        else:
            ComplaintLike.objects.create(ComplaintId=complaint,UserId=user)
            
            return Response(
                {"status": "liked"},
                status=status.HTTP_200_OK)
        
class ComplaintCommentAPI(APIView):
    def post(self, request, lid):
        comp_id = request.data.get("comp_id")
        comment_text = request.data.get("comment")

        if not comment_text:
            return Response(
                {"status": "error", "message": "Comment is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = UserTable.objects.get(LoginId_id=lid)
            complaint = ComplaintsTable.objects.get(id=comp_id)
        except (UserTable.DoesNotExist, ComplaintsTable.DoesNotExist):
            return Response(
                {"status": "error", "message": "Invalid data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = ComplaintComment.objects.create(
            ComplaintId=complaint,
            UserId=user,
            CommentText=comment_text
        )

        return Response(
            {
                "status": "success",
                "comment": {
                    "text": comment.CommentText,
                    "user": user.Name,
                    "created_at": comment.CreatedAt
                }
            },
            status=status.HTTP_201_CREATED
        )
class ViewNotification(APIView):
    def get(self, request, lid):
        print("###############login#", lid)
        userid=UserTable.objects.get(LoginId__id=lid)
        notifications = Notification.objects.filter(ComplaintsId__UserId__LoginId__id=userid)
        print(notifications)
        serializer = NotificationSerializer(notifications, many=True)
        print(serializer.data)

        return Response({
            "status": "success",
            "data": serializer.data
        })

from django.views import View
from django.shortcuts import render
from django.db.models import Count
from .models import ComplaintsTable


class AdminDashboardView(View):
    def get(self, request):

        # BASIC COUNTS
        total_complaints = ComplaintsTable.objects.count()
        assignment_pending = ComplaintsTable.objects.filter(Status='pending').count()
        resolved = ComplaintsTable.objects.filter(Status='resolved').count()
        fake = ComplaintsTable.objects.filter(Status='fake').count()

        # DEPARTMENT WORKLOAD (ONLY ASSIGNED)
        dept_qs = (
            ComplaintsTable.objects
            .filter(DepartmentId__isnull=False)
            .values('DepartmentId__DepartmentName')
            .annotate(total=Count('id'))
        )

        dept_labels = []
        dept_values = []

        for row in dept_qs:
            if row['DepartmentId__DepartmentName']:
                dept_labels.append(row['DepartmentId__DepartmentName'])
                dept_values.append(row['total'])

        context = {
            'total_complaints': total_complaints,
            'assignment_pending': assignment_pending,
            'resolved': resolved,
            'fake': fake,
            'dept_labels': dept_labels,
            'dept_values': dept_values,
        }

        return render(
            request,
            'Administration/admin_dashboard.html',
            context
        )

class NotificationListAPI(APIView):
    def get(self, request, lid):
        try:
            # Filter notifications for the specific user (lid)
            notifications = Notification.objects.filter(
                ComplaintsId__UserId__LoginId__id=lid
            ).order_by('-Date')
            
            serializer = NotificationSerializer(notifications, many=True)
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =====================================================
# IMAGGA IMAGE TAGGING
# =====================================================

def get_image_labels(image_path):
    """
    Send image to Imagga API and return image tags
    """

    print("🔍 Sending image to Imagga API...")

    with open(image_path, "rb") as image_file:
        response = requests.post(
            IMAGGA_ENDPOINT,
            files={"image": image_file},
            auth=HTTPBasicAuth(IMAGGA_API_KEY, IMAGGA_API_SECRET),
            timeout=20
        )

    response.raise_for_status()
    data = response.json()

    tags = data.get("result", {}).get("tags", [])

    # Return top 10 labels
    return [tag["tag"]["en"].lower() for tag in tags[:10]]


# =====================================================
# CATEGORY DETECTION
# =====================================================

def detect_category_from_labels(labels):
    """
    Map Imagga tags to complaint category
    """

    if any(word in labels for word in [
        "water"
    ]):
        return "Water Leakage"

    if any(word in labels for word in [
        "garbage", "waste", "trash", "dump", "bin"
    ]):
        return "Waste Dumping"

    if any(word in labels for word in [
        "light", "lamp", "electricity", "lighting"
    ]):
        return "Street Light Issue"

    if any(word in labels for word in [
        "road", "pothole", "asphalt", "crack", "street"
    ]):
        return "Road Damage"

    return "Other"


# =====================================================
# SEND COMPLAINT API
# =====================================================

class SendComplaintAPI(APIView):

    def post(self, request, id):

        print("📥 Incoming complaint:", request.data)

        user = get_object_or_404(UserTable, LoginId_id=id)
        serializer = AddComplaintsSerializer(data=request.data)

        if serializer.is_valid():
            complaint = serializer.save(UserId=user)

            # =====================================
            # AUTO CATEGORY FROM IMAGE (IMAGGA)
            # =====================================
            if complaint.Image:
                try:
                    labels = get_image_labels(complaint.Image.path)
                    category = detect_category_from_labels(labels)

                    print("✅ Imagga labels:", labels)
                    print("✅ Detected category:", category)

                    complaint.Category = category
                    complaint.save(update_fields=["Category"])

                except Exception as e:
                    print("❌ Imagga error:", e)

            return Response(
                {
                    "message": "Complaint submitted successfully",
                    "category": complaint.Category
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# //////////////////////////////////////////////////////////////////////////////

class SendComplaintCAPI(APIView):


    # -------------------------------------------------
    # POST → Submit complaint
    # -------------------------------------------------
    def post(self, request, id):
        category_map = {
            "Water Leakage": ["water"],
            "Road Damage": ["road", "pothole"],
            "Waste Dumping": ["waste", "garbage"],
            "Street Light Issue": ["street", "light", "electrical"],
        }

        print("📥 Incoming complaint:", request.data)

        user = get_object_or_404(UserTable, LoginId_id=id)

        # 🚫 BLOCKED USER CHECK
        if user.LoginId.UserType == 'Blocked':
            return Response(
                {'error': 'You are blocked and cannot submit complaints'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddComplaintsSerializer(data=request.data)

        # -----------------------------
        # Anonymous logic
        # -----------------------------
        anonymous = request.data.get('is_anonymous', False)
        if isinstance(anonymous, str):
            anonymous = anonymous.lower() == 'true'

        # -----------------------------
        # First complaint check
        # -----------------------------
        is_first_complaint = not ComplaintsTable.objects.filter(
            UserId__LoginId_id=id
        ).exists()

        if serializer.is_valid():
            complaint = serializer.save(
                UserId=user,
                is_anonymous=anonymous
            )

            # =====================================
            # 🧠 AUTO CATEGORY FROM IMAGE (IMAGGA)
            # =====================================
            if complaint.Image:
                try:
                    # labels = get_image_labels(complaint.Image.path)
                    # category = detect_category_from_labels(labels)

                    # print("✅ Imagga labels:", labels)
                    # print("✅ Detected category:", category)

                    dept_obj = None
                    cat = request.POST['Category']
                    if cat == "Road Damage":
                        dept_obj = DepartmentsTable.objects.get(DepartmentName='Roads And Public Works')
                        
                    elif cat == "Water Leakage":
                        dept_obj = DepartmentsTable.objects.get(DepartmentName='Water Authority')
                        
                    elif cat == "Waste Dumping":
                        dept_obj = DepartmentsTable.objects.get(DepartmentName='Waste Management')
                        
                    elif cat == "Street Light":
                        dept_obj = DepartmentsTable.objects.get(DepartmentName='Electrical Department')
                        

                    # for key, keywords in category_map.items():
                    #     if category == key:
                    #         for word in keywords:
                    #             dept_obj = DepartmentsTable.objects.filter(
                    #                 DepartmentName__icontains=word
                    #             ).first()
                    #             if dept_obj:
                    #                 break                    
                    
                    print("---------------->", dept_obj)
                    if dept_obj:
                        complaint.DepartmentId = dept_obj
                        complaint.save()
                    else:
                        print("⚠️ No matching department found for:", category)                    

                except Exception as e:
                    print("❌ Imagga error:", e)

            # -----------------------------
            # Points logic
            # -----------------------------
            points = 200 if is_first_complaint else 50
            PointsTable.objects.create(
                ComplaintId=complaint,
                Points=points
            )

            # -----------------------------
            # 🔥 TOTAL POINTS RECALCULATION
            # -----------------------------
            from django.db.models import Sum

            total = PointsTable.objects.filter(
                ComplaintId__UserId=user
            ).aggregate(total=Sum('Points'))['total']

            user.total_points = total if total is not None else 0
            user.save(update_fields=['total_points'])

            # -----------------------------
            # Badge only for first complaint
            # -----------------------------
            if is_first_complaint:
                BadgeTable.objects.create(
                    ComplaintId=complaint,
                    Badge='First Report'
                )

            # -----------------------------
            # Timeline entry
            # -----------------------------
            TimeLineTable.objects.create(
                ComplaintId=complaint,
                Status='Pending'
            )

            return Response(
                {
                    "message": "Complaint submitted successfully",
                    "category": complaint.Category,
                    "points_awarded": points
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------
    # GET → View complaints
    # -------------------------------------------------
    def get(self, request, id):
        user = get_object_or_404(UserTable, LoginId_id=id)

        complaints = ComplaintsTable.objects.filter(UserId=user)
        serializer = ComplaintsSerializer(complaints, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ViewProfileAPI(APIView):
    def get(self, request,id):
        # userid=UserTable.objects.get(LoginId__id=id)
        profile = UserTable.objects.filter(LoginId__id=id)
        print(profile)
        serializer = UserSerializer(profile, many=True)
        print(serializer.data)

        return Response({
            "status": "success",
            "data": serializer.data
        })