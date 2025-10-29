# accounts/forms.py
from django import forms
from .models import CustomUser, Campus
from django.contrib.auth.models import User
from .models import UploadedFile, Task, SubTask # Replace with your actual model


class AdminRegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'emp_id', 'department', 'campus', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.is_admin = True  # Ensure admin status is set on registration
            user.save()
        return user





class HODRegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'emp_id', 'department', 'campus', 'phone_number', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # hash password
        user.role = 'hod'  # force role to HOD
        if commit:
            user.save()
        return user


class StaffRegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'emp_id', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.is_staff = True  # Ensure staff status is set on registration
            user.save()
        return user


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']  # Removed 'role'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user




class AddStaffForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'emp_id', 'department', 'campus', 'phone_number', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True  # email mandatory

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # hash password
        user.role = 'staff'  # force role = staff
        if commit:
            user.save()
        return user
  


class CSVUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile  # Your model name here
        fields = ['file_name', 'file']  # Replace with your actual field names


class TaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='student'),
        label="Assign to Student"
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        required=False
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date']


class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campus Name'}),
        }

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, label='Add a Comment')

class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['title', 'description', 'deadline', 'status', 'assigned_to']  

    def __init__(self, *args, **kwargs):
        task = kwargs.pop('task', None)
        super().__init__(*args, **kwargs)

        # If task has a team, assign only team members
        if task and task.team:
            self.fields['assigned_to'].queryset = task.team.members.all()
        else:
            self.fields['assigned_to'].queryset = CustomUser.objects.none()

        # Optional: make assigned_to required
        self.fields['assigned_to'].required = True
