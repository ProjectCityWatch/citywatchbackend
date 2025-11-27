


from django.forms import ModelForm

from cityApp.models import *


class ReplayForm(ModelForm):
    class Meta:
        model = FeedbackTable
        fields = ['Replay']

class ProfileForm(ModelForm):
    class Meta:
        model = DepartmentsTable
        fields = ['DepartmentName','HeadName', 'Address', 'ContactInfo', 'Email']