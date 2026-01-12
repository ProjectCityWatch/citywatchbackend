import os
import django
import sys
import json

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cityWatch.settings')
django.setup()

from django.test import RequestFactory
from cityApp.api_views import NotificationListAPI
from cityApp.models import ComplaintsTable, Notification, LoginTable, UserTable

def verify_api():
    print("Starting API verification...")
    
    # 1. Setup User and Data
    login = LoginTable.objects.first()
    if not login:
        print("No login found, creating one")
        login = LoginTable.objects.create(Username='test_api', Password='123', UserType='USER')
        
    user = UserTable.objects.filter(LoginId=login).first()
    if not user:
        user = UserTable.objects.create(LoginId=login, Name='TestAPI', Email='test_api@test.com')

    # Ensure a notification exists
    complaint = ComplaintsTable.objects.filter(UserId=user).first()
    if not complaint:
        complaint = ComplaintsTable.objects.create(UserId=user, Description="API Test", Status="Open")
    
    # Create notification manually if not exists (signal should have done it if we changed status, but let's force one)
    if not Notification.objects.filter(ComplaintsId=complaint).exists():
        Notification.objects.create(ComplaintsId=complaint)
        
    print(f"Testing for Login ID: {login.id}")

    # 2. Call the API View
    factory = RequestFactory()
    request = factory.get(f'/api/notifications/{login.id}/')
    view = NotificationListAPI.as_view()
    
    response = view(request, lid=login.id)
    
    print(f"Status Code: {response.status_code}")
    print("Response Data:")
    
    if hasattr(response, 'data'):
        print(json.dumps(response.data, indent=2))
        if response.status_code == 200 and response.data.get('status') == 'success':
            print("PASS: API returned success.")
        else:
            print("FAIL: API returned error or unexpected status.")
    else:
        # If it's a rendered response (shouldn't be for APIView)
        print(response.content)

if __name__ == "__main__":
    verify_api()
