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

BADGE_DEFINITION = {
    "First Report": {
        "subtitle": "Earned for submitting your very first complaint.",
        "points": 200
    },
    "First Problem Resolved": {
        "subtitle": "Awarded when your issue gets resolved.",
        "points": 200
    },
    "Pothole Pro": {
        "subtitle": "Recognized for reporting multiple road damage issues.",
        "points": 200
    },
    "Clean City Champ": {
        "subtitle": "For actively reporting cleanliness and waste issues.",
        "points": 200
    },
    "Water Watcher": {
        "subtitle": "Awarded for reporting water leakage or wastage.",
        "points": 200
    },
    "Streetlight Saver": {
        "subtitle": "Earned by reporting faulty or broken streetlights.",
        "points": 200
    },
    "Local Hero": {
        "subtitle": "For making a strong positive impact in your locality.",
        "points": 500
    }
}

def mark_complaint_fake(complaint):
    if complaint.Status == "fake":
        return

    # 1️⃣ Update complaint status
    complaint.Status = "fake"
    complaint.save(update_fields=["Status"])

    # 2️⃣ Timeline entry (🔥 THIS WAS MISSING)
    TimeLineTable.objects.create(
        ComplaintId=complaint,
        Status="fake",
        Remark="Complaint marked as fake"
    )

    # 3️⃣ Warning
    user = complaint.UserId
    user.warnings += 1
    user.save(update_fields=["warnings"])

    # 4️⃣ Points deduction
    PointsTable.objects.create(
        ComplaintId=complaint,
        Points=-100
    )

    # 5️⃣ Recalculate total points
    recalculate_user_points(user)



# # --- Login ---
# class LoginView(View):
#     def get(self, request):
#         return render(request, 'Login.html')

#     def post(self, request):
#         username = request.POST['username']
#         password = request.POST['password']

#         try:
#             user = LoginTable.objects.get(Username=username, Password=password)
#             request.session['loginid'] = user.id

#             if user.UserType == 'admin':
#                 return redirect('adminhome')
#             elif user.UserType == 'Authority':
#                 return redirect('authorityhome')
#             else:
#                 return render(request, 'Login.html', {'error': 'Invalid user type'})
#         except LoginTable.DoesNotExist:
#             return render(request, 'Login.html', {'error': 'Invalid username or password'})

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

            # ✅ ADDITION: blocked users can login
            if user.UserType == 'Blocked':
                return redirect('userhome')

            if user.UserType == 'admin':
                return redirect('adminhome')
            elif user.UserType == 'Authority':
                return redirect('authorityhome')
            elif user.UserType == 'USER':
                return redirect('userhome')
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
        mark_complaint_fake(complaint)
        # # Prevent double punishment
        # if complaint.Status == 'fake':
        #     return redirect('assign_works')

        # # 1️⃣ Mark complaint as fake
        # complaint.Status = 'fake'
        # complaint.save()

        # # 2️⃣ Add warning
        # user = complaint.UserId
        # user.warnings += 1
        # user.save()

        # # 3️⃣ Log -100 points
        # PointsTable.objects.create(
        #     ComplaintId=complaint,
        #     Points=-100
        # )

        # # 4️⃣ Recalculate & store total points (VIEW LOGIC)
        # recalculate_user_points(user)

        return redirect('assign_works')

from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from cityApp.models import ComplaintsTable, DepartmentsTable, TimeLineTable

class UpdateDepartmentView(View):
    def post(self, request, complaint_id):
        department_name = request.POST.get("department")

        # safety check
        if not department_name:
            return HttpResponse(
                "<script>alert('Department not selected');history.back();</script>"
            )

        # get complaint
        complaint = get_object_or_404(ComplaintsTable, id=complaint_id)

        # get department object
        department = get_object_or_404(
            DepartmentsTable,
            DepartmentName__iexact=department_name
        )

        # update complaint
        complaint.DepartmentId = department
        complaint.save(update_fields=["DepartmentId"])

        # timeline entry (IMPORTANT for tracking)
        TimeLineTable.objects.create(
            ComplaintId=complaint,
            Status="Department Changed",
            Remark=f"Department updated to {department.DepartmentName}"
        )

        return redirect("assign_decision")





class AddAdminHomeView(View):
    def get(self, request):
        # Fetching real data for the stats bar
        dept_count = DepartmentsTable.objects.count()
        user_count = UserTable.objects.count()
        total_complaints = ComplaintsTable.objects.count()

        context = {
            'dept_count': dept_count,
            'user_count': user_count,
            'total_complaints': total_complaints,
        }
        return render(request, 'Administration/adminhome.html', context)
    
from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from .models import LoginTable, DepartmentsTable

class AddDepartmentView(View): 
    def get(self, request): 
        return render(request, 'Administration/adddepartment.html')

    def post(self, request):
        # Extract data from form
        department_name = request.POST.get('department_name')
        address = request.POST.get('address')
        contact = request.POST.get('contact')
        head = request.POST.get('head')
        password = request.POST.get('password')
        email = request.POST.get('Email')

        # 1. Create Login Credentials
        login_obj = LoginTable()
        login_obj.Username = email
        login_obj.Password = password
        login_obj.UserType = 'Authority'
        login_obj.save()

        # 2. Create Department Record
        obj = DepartmentsTable()
        obj.DepartmentName = department_name
        obj.Address = address
        obj.Email = email
        obj.ContactInfo = contact
        obj.HeadName = head
        obj.LoginId = login_obj # Link to the login record
        obj.save()

        return HttpResponse('''
            <script>
                alert('Department Added Successfully');
                window.location='/manage-department';
            </script>
        ''')

# class AssignWorks(View):
#     def get(self, request):
#         assign_date = AssignWork.objects.filter(
#             ComplaintId=OuterRef('pk')
#         ).values('EndingDate')[:1]

# #         complaints = ComplaintsTable.objects.exclude(
# #     Status='fake'
# # ).annotate(
# #     final_deadline=Subquery(assign_date),
# #     deadline_changed=Exists(
# #         TimeLineTable.objects.filter(
# #             ComplaintId=OuterRef('pk'),
# #             Status="Requested"
# #         )
# #     )
# # )
#         complaints = ComplaintsTable.objects.annotate(
#     final_deadline=Subquery(assign_date),
#     deadline_changed=Exists(
#         TimeLineTable.objects.filter(
#             ComplaintId=OuterRef('pk'),
#             Status="Requested"
#         )
#     )
# )


#         departments = DepartmentsTable.objects.all()

#         assigned_ids = list(
#             AssignWork.objects.values_list('ComplaintId_id', flat=True)
#         )

#         department_id = request.GET.get('department')
#         status = request.GET.get('status')

#         if status == "assigned":
#             complaints = complaints.exclude(Status='fake').filter(id__in=assigned_ids)

#         elif status == "not_assigned":
#              complaints = complaints.exclude(Status='fake').exclude(id__in=assigned_ids)

#         elif status == "fake":
#             complaints = complaints.filter(Status='fake')

#         else:
#             complaints = complaints.exclude(Status='fake')


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


# class AssignWorks(View):
#     def get(self, request):
#         assign_date = AssignWork.objects.filter(
#             ComplaintId=OuterRef('pk')
#         ).values('EndingDate')[:1]

#         complaints = ComplaintsTable.objects.exclude(
#             Status__iexact='Pending'   # 👈 THIS LINE
#         ).annotate(
#             final_deadline=Subquery(assign_date),
#             deadline_changed=Exists(
#                 TimeLineTable.objects.filter(
#                     ComplaintId=OuterRef('pk'),
#                     Status="Requested"
#                 )
#             )
#         )

#         departments = DepartmentsTable.objects.all()

#         assigned_ids = list(
#             AssignWork.objects.values_list('ComplaintId_id', flat=True)
#         )

#         department_id = request.GET.get('department')
#         status = request.GET.get('status')

#         if status == "assigned":
#             complaints = complaints.exclude(Status='fake').filter(id__in=assigned_ids)

#         elif status == "not_assigned":
#             complaints = complaints.exclude(Status='fake').exclude(id__in=assigned_ids)

#         elif status == "fake":
#             complaints = complaints.filter(Status='fake')

#         else:
#             complaints = complaints.exclude(Status='fake')

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

class AssignWorks(View):
    def get(self, request):
        assign_date = AssignWork.objects.filter(
            ComplaintId=OuterRef('pk')
        ).values('EndingDate')[:1]

        complaints = ComplaintsTable.objects.exclude(
            Status__iexact='Pending'
        ).annotate(
            final_deadline=Subquery(assign_date),
            deadline_changed=Exists(
                TimeLineTable.objects.filter(
                    ComplaintId=OuterRef('pk'),
                    Status="Requested"
                )
            )
        )

        departments = DepartmentsTable.objects.all()

        department_id = request.GET.get('department')
        # --------------------------------------------------
        # ✅ DEPARTMENT FILTER (THIS WAS MISSING)
        # --------------------------------------------------
        if department_id and department_id != "all":
            complaints = complaints.filter(DepartmentId_id=department_id)
        status = request.GET.get('status')

        # ------------------------------------
        # ✅ STATUS FILTER LOGIC
        # ------------------------------------
        if status == "fake":
            # show ONLY fake complaints
            complaints = complaints.filter(Status='fake')

        elif status and status != "all":
            # show selected status, but exclude fake
            complaints = complaints.filter(Status=status).exclude(Status='fake')

        else:
            # default → hide fake
            complaints = complaints.exclude(Status='fake')

        return render(
            request,
            'Administration/assignworks.html',
            {
                'val': complaints,
                'departments': departments,
                'selected_department': department_id,
                'selected_status': status
            }
        )







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


    



# class SubmitWorkView(View):
#     def post(self, request, id):
#         complaint = ComplaintsTable.objects.get(id=id)

#         # get requested date from complaint
#         requested_date = complaint.EndingDate

#         # create or update AssignWork
#         assign, created = AssignWork.objects.get_or_create(
#             ComplaintId=complaint
#         )
#         assign.EndingDate = requested_date
#         assign.Status = "Assigned"
#         assign.save()

#         # update complaint status
#         complaint.Status = "Assigned"
#         complaint.save()

#         # timeline entry
#         TimeLineTable.objects.create(
#             ComplaintId=complaint,
#             Status="Assigned",
#             Remark=f"Deadline confirmed as {requested_date}"
#         )

#         return HttpResponse(
#             "<script>alert('Work Assigned Successfully');"
#             "window.location='/assign-works/';</script>"
#         )


class SubmitWorkView(View):
    def post(self, request, id):
        complaint = ComplaintsTable.objects.get(id=id)

        requested_date = complaint.EndingDate

        assign, created = AssignWork.objects.get_or_create(
            ComplaintId=complaint
        )
        assign.EndingDate = requested_date
        assign.Status = "Assigned"
        assign.save()

        # update complaint status
        complaint.Status = "Assigned"
        complaint.save()

        # ✅ create timeline entry FIRST
        timeline = TimeLineTable.objects.create(
            ComplaintId=complaint,
            Status="Assigned",
            Remark=f"Deadline confirmed as {requested_date}"
        )

        # ✅ now create notification correctly
        Notification.objects.create(
            TimeLineId=timeline,
            status="Assigned"
        )

        return HttpResponse(
            "<script>alert('Work Assigned Successfully');"
            "window.location='/assign-works/';</script>"
        )


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
        timeline_obj=TimeLineTable.objects.create(
            ComplaintId=complaint,
            Status=status
        )

         # ✅ now create notification correctly
        Notification.objects.create(
            TimeLineId=timeline_obj,
            status=status
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



  
    




# ------------------------------ Authority ---------------------------------------
from django.utils import timezone
from django.db.models import Q

class AuthorityHomeView(View):
    def get(self, request):
        # 1. Get the current authority's login ID from session
        login_id = request.session.get('loginid')
        
        # 2. Base query: Only complaints belonging to this Authority's department
        # We also exclude 'fake' complaints from general stats
        base_query = ComplaintsTable.objects.filter(
            DepartmentId__LoginId_id=login_id
        ).exclude(Status='fake')

        # --- LOGIC ---

        # NEW REPORTS: Status is 'Assigned' (as per your requirement)
        new_count = base_query.filter(Status='Assigned').count()

        # OVERDUE: Current date > EndingDate AND status is not Resolved/Fake
        # Note: We check EndingDate from ComplaintsTable as updated in your request_ending_date view
        overdue_count = base_query.filter(
            EndingDate__lt=timezone.now().date(),
        ).exclude(Status='Resolved').count()

        # RESOLVED: Status is 'Resolved'
        resolved_count = base_query.filter(Status='Resolved').count()

        # 3. Pass values to context
        context = {
            'new_count': new_count,
            'overdue_count': overdue_count,
            'resolved_count': resolved_count,
        }

        return render(request, 'Authority/authorityhome.html', context)


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



class ReplayView(View):
    def post(self, request, id):
        c = FeedbackTable.objects.get(id = id)
        replay = ReplayForm(request.POST, instance=c)
        if replay.is_valid():
            replay.save()
        return HttpResponse('''<script>alert('Replayed successfully');window.location='/viewfeedback/';</script>''')


# class ViewComplaintsView(View):
#     def get(self, request):
#         print(request.session['loginid'])
#         complaints = ComplaintsTable.objects.filter(DepartmentId__LoginId_id=request.session['loginid'])
#         print("-----------",complaints)
#         return render(request, 'Authority/viewcomplaints.html', {'val': complaints})
    
# # class ViewComplaintsView(View):
# #     def get(self, request):
# #         complaints = ComplaintsTable.objects.all()

# #         for c in complaints:
# #             try:
# #                 assign = AssignWork.objects.get(ComplaintId=c)
# #                 c.EndingDate = assign.EndingDate
# #                 c.work_status = assign.Status
# #             except AssignWork.DoesNotExist:
# #                 c.assigned_date = None
# #                 c.work_status = "Not Assigned"

# #         return render(request, 'Authority/viewcomplaints.html', {'val': complaints})
    

#     def post(self, request):
#         complaint_id = request.POST.get('complaint_id')
#         status = request.POST.get('status')

#         assign = get_object_or_404(AssignWork, ComplaintId_id=complaint_id)

#         assign.Status = status
#         assign.save()



#         return HttpResponse(
#             "<script>alert('Status changed successfully');"
#             "window.location='/viewcomplaintsview';</script>"
#         )
from django.db.models import Count, Case, When, IntegerField

class ViewComplaintsView(View):
    def get(self, request):
        status_filter = request.GET.get("status")
        priority_filter = request.GET.get("priority")

        # ------------------------------------
        # BASE QUERY (department only)
        # ------------------------------------
        complaints = ComplaintsTable.objects.filter(
            DepartmentId__LoginId_id=request.session['loginid']
        )

        # ------------------------------------
        # STATUS HANDLING (FAKE LOGIC)
        # ------------------------------------
        if status_filter == "fake":
            # ✅ show ONLY fake complaints
            complaints = complaints.filter(Status="fake")
        else:
            # ✅ default → hide fake complaints
            complaints = complaints.exclude(Status="fake")

            # apply normal status filter
            if status_filter and status_filter != "all":
                complaints = complaints.filter(Status=status_filter)
            else:
                # default visible statuses
                complaints = complaints.filter(
                    Status__in=[
                        "Assigned",
                        "Date Fixed",
                        "Extended",
                        "In Progress",
                        "Resolved"
                    ]
                )

        # ------------------------------------
        # PRIORITY FILTER
        # ------------------------------------
        if priority_filter and priority_filter != "all":
            complaints = complaints.filter(Priority=priority_filter)

        # ------------------------------------
        # ANNOTATIONS + ORDERING (UNCHANGED)
        # ------------------------------------
        complaints = complaints.annotate(
            like_count=Count("likes"),
            resolved_order=Case(
                When(Status="Resolved", then=0),
                default=1,
                output_field=IntegerField()
            )
        ).order_by("resolved_order", "-SubmitDate")

        return render(
            request,
            "Authority/viewcomplaints.html",
            {
                "val": complaints,
                "selected_status": status_filter,
                "selected_priority": priority_filter
            }
        )

    # 🔴 post() unchanged
    def post(self, request):
        complaint_id = request.POST.get("complaint_id")
        status = request.POST.get("status")

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
        Notification.objects.create(
            TimeLineId=time_line_obj,
            status="Date Fixed"
        )



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

# class UpdateDeadlineView(View):
#     def get(self, request, id):
#         c = ComplaintsTable.objects.get(id=id)
#         return render(request, 'Authority/updatedeadline.html',{'val':c})


#     def post(self, request, id):
#         # existing complaint
#         c = ComplaintsTable.objects.get(id=id)

#         # assigned work (must exist)
#         v = AssignWork.objects.get(ComplaintId__id=c.id)

#         # form bound to complaint
#         d = ComplaintsForm(request.POST, instance=c)

#         if d.is_valid():
#             reg = d.save(commit=False)

#             # update ending date in AssignWork
#             v.EndingDate = reg.EndingDate
#             v.save(update_fields=['EndingDate'])

#             # save complaint
#             reg.save()

#             # 🔥 CREATE TIMELINE ENTRY ONLY IF EXTENDED
#             if reg.Status == "Extended":
#                 TimeLineTable.objects.create(
#                     ComplaintId=c,
#                     Status="Extended",
#                     EndingDate=reg.EndingDate,
#                     Remark=request.POST.get('reason')
#                 )

#             return redirect('/viewcomplaintsview/')
class UpdateDeadlineView(View):
    def get(self, request, id):
        c = ComplaintsTable.objects.get(id=id)
        return render(request, 'Authority/updatedeadline.html', {'val': c})

    def post(self, request, id):
        c = ComplaintsTable.objects.get(id=id)
        v = AssignWork.objects.get(ComplaintId__id=c.id)

        d = ComplaintsForm(request.POST, instance=c)

        if d.is_valid():
            reg = d.save(commit=False)

            # ✅ FORCE EXTENDED STATUS
            reg.Status = "Extended"

            # update deadline
            v.EndingDate = reg.EndingDate
            v.save(update_fields=["EndingDate"])

            # save complaint
            reg.save(update_fields=["EndingDate", "Status"])

            # timeline entry
            TimeLineTable.objects.create(
                ComplaintId=c,
                Status="Extended",
                EndingDate=reg.EndingDate,
                Remark=request.POST.get("reason")
            )

        return redirect('/viewcomplaintsview/')

from django.views import View
from django.shortcuts import get_object_or_404, redirect
from cityApp.models import ComplaintsTable

class AuthorityMarkFakeComplaint(View):
    def post(self, request, c_id):

        # 🔐 ensure complaint belongs to this authority
        complaint = get_object_or_404(
            ComplaintsTable,
            id=c_id,
            DepartmentId__LoginId_id=request.session['loginid']
        )

        mark_complaint_fake(complaint)

        # go back to same page
        return redirect(request.META.get("HTTP_REFERER", "/authority/date-fixed-complaints/"))


#############################################  API ###########################################
CATEGORY_DEPARTMENT_MAP = {
    "Road damage": "Roads And Public Works",
    "Damaged public property": "Roads And Public Works",

    "Water leakage": "Water Authority",
    "Drainage": "Drainage Department",

    "Waste dumping": "Waste Management",

    "Street Light failure": "Electrical Department",
}


# class UserRegistration(APIView):
#     def post(self, request):
#         print("++++++++++++++", request.data)

#         # LOGIN CREDENTIALS
#         login_serial = LoginSerializer(data={
#             "Username": request.data.get("Username"),
#             "Password": request.data.get("Password"),
#             "UserType": "USER"
#         })

#         # USER BASIC DATA
#         user_serial = UserSerializer(data=request.data)

#         if login_serial.is_valid():
#             login_obj = login_serial.save()

#             if user_serial.is_valid():
#                 user_serial.save(LoginId=login_obj)
#                 return Response(
#                     {"status": "success",
#                      "message": "User Registered Successfully",
#                      "user": user_serial.data},
#                     status=status.HTTP_201_CREATED
#                 )

#             # delete login if user fails
#             login_obj.delete()
#             return Response(
#                 {"status": "error", "errors": user_serial.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         return Response(
#             {"status": "error", "errors": login_serial.errors},
#             status=status.HTTP_400_BAD_REQUEST
#         )
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
class UserRegistration(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        print("++++++++++++++", request.data)
        print("++++++++++++++ FILES:", request.FILES)

        # LOGIN CREDENTIALS
        login_serial = LoginSerializer(data={
            "Username": request.data.get("Username"),
            "Password": request.data.get("Password"),
            "UserType": "USER"
        })

        # USER BASIC DATA (includes profile now)
        user_serial = UserSerializer(data=request.data)

        if login_serial.is_valid():
            login_obj = login_serial.save()

            if user_serial.is_valid():
                user_serial.save(
                    LoginId=login_obj,
                    profile=request.FILES.get("profile")  # ✅ IMPORTANT
                )

                return Response(
                    {
                        "status": "success",
                        "message": "User Registered Successfully",
                        "user": user_serial.data
                    },
                    status=status.HTTP_201_CREATED
                )

            # rollback login if user save fails
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




# class ViewTimelineAPI(APIView):
#     def get(self, request, id):
#         print("------------------------>", id)
#         comp = ComplaintsTable.objects.get(id=id) 
#         print("++++++++++++++++",comp)
#         TimeLine=TimeLineTable.objects.filter(ComplaintId_id=comp)
#         print(TimeLine)
#         serializer=TimeLineSerializer(TimeLine, many=True)
#         print("------------------>", serializer.data)
#         if serializer.data:
         
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
            
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ViewTimelineAPI(APIView):
    def get(self, request, id):
        comp = ComplaintsTable.objects.get(id=id)

        timeline = TimeLineTable.objects.filter(ComplaintId_id=comp)
        serializer = TimeLineSerializer(timeline, many=True)

        data = serializer.data

        # ✅ ADD DEADLINE ONLY FOR THESE STATUSES
        if comp.Status in ["Date Fixed", "Extended"]:
            for item in data:
                item["deadline"] = comp.EndingDate
        print(data)
        if data:
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(data, status=status.HTTP_204_NO_CONTENT)

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

# class ViewAllcomplaintsAPI(APIView):

#     def get(self, request):
#         complaints = ComplaintsTable.objects.all().order_by('-SubmitDate')

#         if not complaints.exists():
#             return Response(
#                 {"message": "No complaints found"},
#                 status=status.HTTP_204_NO_CONTENT
#             )

#         serializer = ComplaintsSerializer1(complaints, many=True)
#         print(serializer.data)
#         return Response(serializer.data, status=status.HTTP_200_OK)
# from django.db.models import Count

# class ViewAllcomplaintsAPI(APIView):
#     def get(self, request):
#         complaints = ComplaintsTable.objects.annotate(
#             total_likes=Count("likes")
#         ).order_by('-SubmitDate')

#         if not complaints.exists():
#             return Response(
#                 {"message": "No complaints found"},
#                 status=status.HTTP_204_NO_CONTENT
#             )

#         serializer = ComplaintsSerializer1(complaints, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ViewAllcomplaintsAPI(APIView):
    def get(self, request):
        complaints = ComplaintsTable.objects.annotate(
            total_likes=Count("likes")
        ).order_by('-SubmitDate')

        serializer = ComplaintsSerializer1(complaints, many=True)
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

from django.views import View
from django.shortcuts import render
from django.db.models import Count
from .models import ComplaintsTable

class AdminDashboardView(View):
    def get(self, request):
        # BASIC COUNTS - Using __iexact to ensure data retrieval regardless of casing
        total_complaints = ComplaintsTable.objects.count()
        pending = ComplaintsTable.objects.filter(Status__iexact='pending').count()
        in_progress = ComplaintsTable.objects.filter(Status__iexact='inprogress').count()
        resolved = ComplaintsTable.objects.filter(Status__iexact='resolved').count()

        # DEPARTMENT WORKLOAD
        dept_qs = (
            ComplaintsTable.objects
            .filter(DepartmentId__isnull=False)
            .values('DepartmentId__DepartmentName')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        dept_labels = [row['DepartmentId__DepartmentName'] for row in dept_qs]
        dept_values = [row['total'] for row in dept_qs]

        context = {
            'total_complaints': total_complaints,
            'pending': pending,
            'in_progress': in_progress,
            'resolved': resolved,
            'dept_labels': dept_labels,
            'dept_values': dept_values,
        }

        return render(request, 'Administration/admin_dashboard.html', context)

class NotificationListAPI(APIView):
    def get(self, request, lid):
        # try:
            # Filter notifications for the specific user (lid)
            notifications = Notification.objects.filter(
                TimeLineId__ComplaintId__UserId__LoginId__id=lid
            ).order_by('-Date')
            
            serializer = NotificationSerializer(notifications, many=True)
            print('---------datadddd--->', serializer.data)
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        # except Exception as e:
        #     return Response(
        #         {"status": "error", "message": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )

class MarkNotificationReadAPI(APIView):
    def post(self, request, nid):
        try:
            notification = Notification.objects.get(id=nid)
            notification.is_read = True
            notification.save(update_fields=["is_read"])

            return Response({"status": "success"})
        except Notification.DoesNotExist:
            return Response(
                {"status": "error", "message": "Not found"},
                status=404
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

# class SendComplaintAPI(APIView):

#     def post(self, request, id):

#         print("📥 Incoming complaint:", request.data)

#         user = get_object_or_404(UserTable, LoginId_id=id)
#         serializer = AddComplaintsSerializer(data=request.data)

#         if serializer.is_valid():
#             complaint = serializer.save(UserId=user)

#             # =====================================
#             # AUTO CATEGORY FROM IMAGE (IMAGGA)
#             # =====================================
#             if complaint.Image:
#                 try:
#                     labels = get_image_labels(complaint.Image.path)
#                     category = detect_category_from_labels(labels)

#                     print("✅ Imagga labels:", labels)
#                     print("✅ Detected category:", category)

#                     complaint.Category = category
#                     complaint.save(update_fields=["Category"])

#                 except Exception as e:
#                     print("❌ Imagga error:", e)

#             return Response(
#                 {
#                     "message": "Complaint submitted successfully",
#                     "category": complaint.Category
#                 },
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
                {
            "status": "blocked",
            "message": "You are blocked by admin. You cannot submit complaints."
        },
                status=status.HTTP_200_OK
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
            # 🧠 CATEGORY → DEPARTMENT MAPPING
            # =====================================
            try:
                cat = request.data.get("Category")

                dept_name = CATEGORY_DEPARTMENT_MAP.get(cat)

                if dept_name:
                    dept_obj = DepartmentsTable.objects.filter(
                        DepartmentName__iexact=dept_name
                    ).first()

                    if dept_obj:
                        complaint.DepartmentId = dept_obj
                        complaint.save(update_fields=["DepartmentId"])
                    else:
                        print("⚠️ Department not found:", dept_name)
                else:
                    print("⚠️ No mapping for category:", cat)

            except Exception as e:
                print("❌ Department mapping error:", e)

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


# class SendComplaintCAPI(APIView):


#     # -------------------------------------------------
#     # POST → Submit complaint
#     # -------------------------------------------------
#     def post(self, request, id):
#         category_map = {
#             "Water Leakage": ["water"],
#             "Road Damage": ["road", "pothole"],
#             "Waste Dumping": ["waste", "garbage"],
#             "Street Light Issue": ["street", "light", "electrical"],
#         }

#         print("📥 Incoming complaint:", request.data)

#         user = get_object_or_404(UserTable, LoginId_id=id)

#         # 🚫 BLOCKED USER CHECK
#         if user.LoginId.UserType == 'Blocked':
#             return Response(
#                 {'error': 'You are blocked and cannot submit complaints'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         serializer = AddComplaintsSerializer(data=request.data)

#         # -----------------------------
#         # Anonymous logic
#         # -----------------------------
#         anonymous = request.data.get('is_anonymous', False)
#         if isinstance(anonymous, str):
#             anonymous = anonymous.lower() == 'true'

#         # -----------------------------
#         # First complaint check
#         # -----------------------------
#         is_first_complaint = not ComplaintsTable.objects.filter(
#             UserId__LoginId_id=id
#         ).exists()

#         if serializer.is_valid():
#             complaint = serializer.save(
#                 UserId=user,
#                 is_anonymous=anonymous
#             )

#             # =====================================
#             # 🧠 AUTO CATEGORY FROM IMAGE (IMAGGA)
#             # =====================================
#             if complaint.Image:
#                 try:
#                     # labels = get_image_labels(complaint.Image.path)
#                     # category = detect_category_from_labels(labels)

#                     # print("✅ Imagga labels:", labels)
#                     # print("✅ Detected category:", category)

#                     dept_obj = None
#                     cat = request.POST['Category']
#                     if cat == "Road Damage":
#                         dept_obj = DepartmentsTable.objects.get(DepartmentName='Roads And Public Works')
                        
#                     elif cat == "Water Leakage":
#                         dept_obj = DepartmentsTable.objects.get(DepartmentName='Water Authority')
                        
#                     elif cat == "Waste Dumping":
#                         dept_obj = DepartmentsTable.objects.get(DepartmentName='Waste Management')
                        
#                     elif cat == "Street Light":
#                         dept_obj = DepartmentsTable.objects.get(DepartmentName='Electrical Department')
                        

#                     # for key, keywords in category_map.items():
#                     #     if category == key:
#                     #         for word in keywords:
#                     #             dept_obj = DepartmentsTable.objects.filter(
#                     #                 DepartmentName__icontains=word
#                     #             ).first()
#                     #             if dept_obj:
#                     #                 break                    
                    
#                     print("---------------->", dept_obj)
#                     if dept_obj:
#                         complaint.DepartmentId = dept_obj
#                         complaint.save()
#                     else:
#                         print("⚠️ No matching department found for:", category)                    

#                 except Exception as e:
#                     print("❌ Imagga error:", e)

#             # -----------------------------
#             # Points logic
#             # -----------------------------
#             points = 200 if is_first_complaint else 50
#             PointsTable.objects.create(
#                 ComplaintId=complaint,
#                 Points=points
#             )

#             # -----------------------------
#             # 🔥 TOTAL POINTS RECALCULATION
#             # -----------------------------
#             from django.db.models import Sum

#             total = PointsTable.objects.filter(
#                 ComplaintId__UserId=user
#             ).aggregate(total=Sum('Points'))['total']

#             user.total_points = total if total is not None else 0
#             user.save(update_fields=['total_points'])

#             # -----------------------------
#             # Badge only for first complaint
#             # -----------------------------
#             if is_first_complaint:
#                 BadgeTable.objects.create(
#                     ComplaintId=complaint,
#                     Badge='First Report'
#                 )

#             # -----------------------------
#             # Timeline entry
#             # -----------------------------
#             TimeLineTable.objects.create(
#                 ComplaintId=complaint,
#                 Status='Pending'
#             )

#             return Response(
#                 {
#                     "message": "Complaint submitted successfully",
#                     "category": complaint.Category,
#                     "points_awarded": points
#                 },
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # -------------------------------------------------
#     # GET → View complaints
#     # -------------------------------------------------
#     def get(self, request, id):
#         user = get_object_or_404(UserTable, LoginId_id=id)

#         complaints = ComplaintsTable.objects.filter(UserId=user)
#         serializer = ComplaintsSerializer(complaints, many=True)

#         return Response(serializer.data, status=status.HTTP_200_OK)

# class ViewProfileAPI(APIView):
#     def get(self, request,id):
#         # userid=UserTable.objects.get(LoginId__id=id)
#         profile = UserTable.objects.filter(LoginId__id=id)
#         print(profile)
#         serializer = UserSerializer(profile, many=True)
#         print(serializer.data)

#         return Response({
#             "status": "success",
#             "data": serializer.data
#         })

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserTable
from .serializers import UserSerializer

class ViewProfileAPI(APIView):
    def get(self, request, id):
        try:
            profile = UserTable.objects.get(LoginId__id=id)
            serializer = UserSerializer(profile)

            return Response({
                "status": "success",
                "data": serializer.data
            })

        except UserTable.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "User not found"
            })


from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum

from .models import (
    UserTable,
    BadgeTable,
    PointsTable
)

class UserPointsAPI(APIView):

    def get(self, request, login_id):

        # -----------------------------------
        # 1️⃣ Get user
        # -----------------------------------
        user = get_object_or_404(UserTable, LoginId_id=login_id)

        # -----------------------------------
        # 2️⃣ SUMMARY DATA
        # -----------------------------------
        total_points = user.total_points

        badges_earned = BadgeTable.objects.filter(
            ComplaintId__UserId=user
        ).count()

        # Rank calculation
        ranked_users = list(
            UserTable.objects.order_by("-total_points")
            .values_list("id", flat=True)
        )
        user_rank = ranked_users.index(user.id) + 1 if user.id in ranked_users else None

        # -----------------------------------
        # 3️⃣ BADGES GRID
        # -----------------------------------
        earned_badges = set(
            BadgeTable.objects.filter(
                ComplaintId__UserId=user
            ).values_list("Badge", flat=True)
        )

        badges = []
        for title, data in BADGE_DEFINITION.items():
            badges.append({
                "title": title,
                "subtitle": data["subtitle"],
                "points": data["points"],
                "is_earned": title in earned_badges
            })

        # -----------------------------------
        # 4️⃣ RECENT ACTIVITIES
        # -----------------------------------
        points_logs = PointsTable.objects.filter(
            ComplaintId__UserId=user
        ).order_by("-CreatedDate")[:10]

        def activity_title(p):
         if p.Points >= 200:
          return "Badge Earned"
         elif p.Points == 100:
            return "Complaint Resolved"
         elif p.Points == -100:
            return "Complaint Marked as Fake"
         else:
             return "Complaint Reported"

        activities = [
            {
                "title": activity_title(p),
                "points": p.Points,
                "created_at": p.CreatedDate
            }
            for p in points_logs
        ]

        # -----------------------------------
        # 5️⃣ FINAL RESPONSE
        # -----------------------------------
        return Response({
            "summary": {
                "total_points": total_points,
                "badges_earned": badges_earned,
                "user_rank": user_rank
            },
            "badges": badges,
            "activities": activities
        })
    


# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserTable
from .serializers import LeaderboardSerializer


class LeaderboardAPI(APIView):
    def get(self, request, user_id):
        users = UserTable.objects.order_by('-total_points')

        leaderboard_data = []
        current_user_rank = 0
        current_user_points = 0

        for index, user in enumerate(users, start=1):
            user.rank = index

            if user.LoginId_id == user_id:
                current_user_rank = index
                current_user_points = user.total_points

            leaderboard_data.append(user)

        serializer = LeaderboardSerializer(
            leaderboard_data[:10],
            many=True,
            context={"request": request}  # 🔴 REQUIRED for image URL
        )

        return Response({
            "leaders": serializer.data,
            "your_rank": {
                "rank": current_user_rank,
                "points": current_user_points
            }
        }, status=status.HTTP_200_OK)



# class LeaderboardAPI(APIView):
#     def get(self, request, user_id):
#         # 1️⃣ Order users by points
#         users = UserTable.objects.order_by('-total_points')

#         leaderboard_data = []
#         current_user_rank = None
#         current_user_points = 0

#         # 2️⃣ Assign ranks
#         for index, user in enumerate(users, start=1):
#             user.rank = index

#             if user.id == user_id:
#                 current_user_rank = index
#                 current_user_points = user.total_points

#             leaderboard_data.append(user)

#         # 3️⃣ Serialize top 10
#         serializer = LeaderboardSerializer(
#             leaderboard_data[:10],
#             many=True
#         )
#         return Response({
#             "leaders": serializer.data,
#             "your_rank": {
#     "rank": current_user_rank if current_user_rank else 0,
#     "points": current_user_points
# }

#         }, status=status.HTTP_200_OK)



from django.views import View
from django.shortcuts import render
from django.db.models import Count
from .models import ComplaintsTable
from django.db.models import Count

class AuthorityAssignedComplaintsView(View):
    def get(self, request):

        priority = request.GET.get("priority")
        liked = request.GET.get("liked")

        complaints = (
            ComplaintsTable.objects
            .filter(
                Status="Assigned",
                EndingDate__isnull=True,
                DepartmentId__LoginId_id=request.session['loginid']
            )
            .annotate(like_count=Count("likes"))
        )

        # ✅ PRIORITY FILTER
        if priority and priority != "all":
            complaints = complaints.filter(Priority=priority)

        # ✅ LIKED FILTER
        if liked == "most_liked":
            complaints = complaints.order_by("-like_count")
        else:
            complaints = complaints.order_by("-SubmitDate")

        return render(
            request,
            "Authority/assigned_complaints.html",
            {
                "val": complaints,
                "selected_priority": priority,
                "selected_liked": liked
            }
        )

        

class AuthorityDateFixedComplaintsView(View):
    def get(self, request):

        priority = request.GET.get("priority", "all")
        liked = request.GET.get("liked", "all")

        complaints = (
            ComplaintsTable.objects
            .filter(
                EndingDate__isnull=False,
                EndingDate__gte=now().date(),
                Status__in=["Date Fixed", "In Progress", "Extended"],
                DepartmentId__LoginId_id=request.session['loginid']
            )
            .annotate(like_count=Count("likes"))
        )

        if priority != "all":
            complaints = complaints.filter(Priority=priority)

        if liked == "most_liked":
            complaints = complaints.order_by("-like_count")
        else:
            complaints = complaints.order_by("EndingDate")

        return render(
            request,
            "Authority/date_fixed_complaints.html",
            {
                "val": complaints,
                "selected_priority": priority,
                "selected_liked": liked
            }
        )


from django.views import View
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count
from .models import ComplaintsTable


class AuthorityOverdueComplaintsView(View):
    def get(self, request):

        # ----------------------------
        # GET FILTER VALUES
        # ----------------------------
        priority = request.GET.get("priority", "all")
        liked = request.GET.get("liked", "all")

        # ----------------------------
        # BASE QUERY (UNCHANGED LOGIC)
        # ----------------------------
        complaints = (
            ComplaintsTable.objects
            .filter(
                EndingDate__lt=now().date(),
                EndingDate__isnull=False,
                DepartmentId__LoginId_id=request.session['loginid']
            )
            .exclude(Status="Resolved")
            .annotate(like_count=Count("likes"))
        )

        # ----------------------------
        # PRIORITY FILTER (ADDED)
        # ----------------------------
        if priority != "all":
            complaints = complaints.filter(Priority=priority)

        # ----------------------------
        # LIKES FILTER (ADDED)
        # ----------------------------
        if liked == "most_liked":
            complaints = complaints.order_by("-like_count")
        else:
            complaints = complaints.order_by("EndingDate")

        # ----------------------------
        # RENDER (UNCHANGED)
        # ----------------------------
        return render(
            request,
            "Authority/overdue_complaints.html",
            {
                "val": complaints,
                "selected_priority": priority,
                "selected_liked": liked
            }
        )

from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.utils.timezone import now
from .models import ComplaintsTable, TimeLineTable

# class AuthorityExtendDeadlineView(View):
#     def post(self, request, cid):
#         new_date = request.POST.get("new_date")
#         reason = request.POST.get("reason")

#         complaint = get_object_or_404(
#             ComplaintsTable,
#             id=cid,
#             DepartmentId__LoginId_id=request.session['loginid']
#         )

#         complaint.EndingDate = new_date
#         complaint.Status = "In Progress"
#         complaint.save(update_fields=["EndingDate", "Status"])

#         TimeLineTable.objects.create(
#             ComplaintId=complaint,
#             Status="Extended",
#             EndingDate=new_date,
#             Remark=reason
#         )

#         return redirect("/authority/date-fixed-complaints/")
class AuthorityExtendDeadlineView(View):
    def post(self, request, cid):
        new_date = request.POST.get("new_date")
        reason = request.POST.get("reason")

        complaint = get_object_or_404(
            ComplaintsTable,
            id=cid,
            DepartmentId__LoginId_id=request.session['loginid']
        )

        # ✅ STORE EXTENDED IN COMPLAINT TABLE
        complaint.EndingDate = new_date
        complaint.Status = "Extended"
        complaint.save(update_fields=["EndingDate", "Status"])

        # timeline
        obj = TimeLineTable.objects.create(
            ComplaintId=complaint,
            Status="Extended",
            EndingDate=new_date,
            Remark=reason
        )
        Notification.objects.create(
            TimeLineId=obj,
            status="Extended"
        )


        return redirect("/authority/date-fixed-complaints/")
    
from django.views import View
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count
from .models import ComplaintsTable

class AuthorityDashboardView(View):
    def get(self, request):
        # Retrieve the logged-in Authority's ID from session
        authority_id = request.session.get('loginid')
        today = now().date()

        # 1. Base Query: Filter complaints strictly for this authority's department
        complaints = ComplaintsTable.objects.filter(
            DepartmentId__LoginId_id=authority_id
        )

        # 2. Metric Calculations
        total_count = complaints.count()
        
        # Assigned but no deadline set
        assigned = complaints.filter(Status__iexact="Assigned", EndingDate__isnull=True).count()

        # Currently being worked on within deadline
        active = complaints.filter(
            EndingDate__gte=today,
            Status__in=["Date Fixed", "In Progress", "Inprogress"]
        ).count()

        # Past deadline and not yet resolved
        overdue = complaints.filter(
            EndingDate__lt=today
        ).exclude(Status__iexact="Resolved").count()

        # Successfully finished
        resolved = complaints.filter(Status__iexact="Resolved").count()

        # 3. Workload by Priority (Using the field confirmed in your FieldError)
        # We group by priority to show the authority the level of urgency in their queue
        priority_qs = (
            complaints.exclude(Status__iexact="Resolved")
            .values('Priority')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        pri_labels = [row['Priority'] for row in priority_qs if row['Priority']]
        pri_values = [row['total'] for row in priority_qs if row['Priority']]

        context = {
            "total": total_count,
            "assigned": assigned,
            "active": active,
            "overdue": overdue,
            "resolved": resolved,
            "pri_labels": pri_labels,
            "pri_values": pri_values,
        }

        return render(request, "Authority/dashboard.html", context)
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    ComplaintsTable,
    ComplaintLike,
    ComplaintComment
)
from .serializers import ComplaintsSerializer1


class TrendingComplaintsAPI(APIView):
    def get(self, request):
        now = timezone.now()

        complaints = ComplaintsTable.objects.filter(
            SubmitDate__gte=now - timedelta(days=7)
        )

        trending_list = []

        for complaint in complaints:
            likes_count = ComplaintLike.objects.filter(
                ComplaintId=complaint
            ).count()

            comments_count = ComplaintComment.objects.filter(
                ComplaintId=complaint
            ).count()

            hours_since_post = (
                now - complaint.SubmitDate
            ).total_seconds() / 3600

            if likes_count == 0 and comments_count == 0:
                score = 1 / (hours_since_post + 1)
            else:
                score = (likes_count * 1.5 + comments_count) / (hours_since_post + 2)

            trending_list.append({
                "complaint": complaint,
                "score": score
            })

        trending_list.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        top_complaints = [
            item["complaint"] for item in trending_list[:3]
        ]

        serializer = ComplaintsSerializer1(top_complaints, many=True)

        return Response(
            {
                "status": "success",
                "count": len(top_complaints),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

from django.views import View
from django.shortcuts import render
from django.db.models import OuterRef, Subquery, Exists
from .models import (
    ComplaintsTable,
    AssignWork,
    DepartmentsTable,
    TimeLineTable
)

# class AssignDecisionPage(View):
#     def get(self, request):

#         assign_date = AssignWork.objects.filter(
#             ComplaintId=OuterRef('pk')
#         ).values('EndingDate')[:1]

#         complaints = ComplaintsTable.objects.annotate(
#             final_deadline=Subquery(assign_date),
#             deadline_changed=Exists(
#                 TimeLineTable.objects.filter(
#                     ComplaintId=OuterRef('pk'),
#                     Status="Requested"
#                 )
#             )
#         )

#         assigned_ids = AssignWork.objects.values_list(
#             'ComplaintId_id', flat=True
#         )

#         # 🎯 ONLY complaints waiting for decision
#         complaints = complaints.filter(
#             Status="pending"
#         ).exclude(
#             id__in=assigned_ids
#         )

#         department_id = request.GET.get("department")
#         if department_id and department_id != "all":
#             complaints = complaints.filter(
#                 DepartmentId_id=department_id
#             )

#         return render(
#             request,
#             "Administration/assign_decision.html",
#             {
#                 "val": complaints,
#                 "departments": DepartmentsTable.objects.all(),
#                 "selected_department": department_id,
#             }
#         )
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
class AssignDecisionPage(View):
    def get(self, request):
        assign_date = AssignWork.objects.filter(
            ComplaintId=OuterRef('pk')
        ).values('EndingDate')[:1]

        complaints = ComplaintsTable.objects.annotate(
            final_deadline=Subquery(assign_date),
            deadline_changed=Exists(
                TimeLineTable.objects.filter(
                    ComplaintId=OuterRef('pk'),
                    Status="Requested"
                )
            )
        )

        assigned_ids = AssignWork.objects.values_list(
            'ComplaintId_id', flat=True
        )

        # 🎯 ONLY complaints waiting for decision
        complaints = complaints.filter(
            Status="pending"
        ).exclude(
            id__in=assigned_ids
        )

        # --- FILTERS ---
        department_id = request.GET.get("department")
        priority_val = request.GET.get("priority") # 1. Capture priority

        if department_id and department_id != "all":
            complaints = complaints.filter(
                DepartmentId_id=department_id
            )
            
        # 2. Apply Priority filter logic
        if priority_val and priority_val != "all":
            complaints = complaints.filter(
                Priority=priority_val
            )

        return render(
            request,
            "Administration/assign_decision.html",
            {
                "val": complaints,
                "departments": DepartmentsTable.objects.all(),
                "selected_department": department_id,
                "selected_priority": priority_val, # 3. Pass back to template
            }
        )
    
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from cityApp.models import UserTable

class UpdateProfileAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, id):
        user = get_object_or_404(UserTable, LoginId__id=id)

        user.Name = request.data.get("Name", user.Name)
        user.PhoneNo = request.data.get("PhoneNo", user.PhoneNo)
        user.Address = request.data.get("Address", user.Address)

        if request.FILES.get("profile"):
            user.profile = request.FILES.get("profile")

        user.save()

        return Response(
            {
                "status": "success",
                "message": "Profile updated successfully"
            },
            status=status.HTTP_200_OK
        )
