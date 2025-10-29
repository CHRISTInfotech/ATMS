# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from .forms import AdminRegisterForm, HODRegisterForm, StaffRegisterForm, UserCreationForm, SubTaskForm
from .models import CustomUser
from django.contrib import messages
from .forms import AddStaffForm
from .forms import CSVUploadForm
from .models import UploadedFile
from .forms import TaskForm
from .models import CustomUser, Team, Task, Project

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin, SocialApp
from accounts.models import Task
from accounts.forms import TaskForm
from django.utils import timezone
from django.contrib.auth import logout
from .models import Event  
from datetime import date, timedelta
from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('accounts:admin_dashboard')
        elif request.user.role == 'hod':
            return redirect('accounts:hod_dashboard')
        elif request.user.role == 'staff':
            return redirect('accounts:staff_dashboard')
        elif request.user.role == 'student':
            return redirect('accounts:student_dashboard')
        else:
            return redirect('accounts:email_not_registered')

    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not getattr(user, 'role', None):
                return redirect('accounts:email_not_registered')

            login(request, user)  # ✅ Use user from authenticate
            if user.role == 'admin':
                return redirect('accounts:admin_dashboard')
            elif user.role == 'hod':
                return redirect('accounts:hod_dashboard')
            elif user.role == 'staff':
                return redirect('accounts:staff_dashboard')
            elif user.role == 'student':
                return redirect('accounts:student_dashboard')
            else:
                return redirect('accounts:email_not_registered')
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect('accounts:login')

    return render(request, 'accounts/login.html')



# Role-based dashboard view
@login_required
def dashboard(request):
    user = request.user

    # User exists but has no role
    if not user.role:
        return redirect('accounts:email_not_registered')

    if user.role == 'admin':
        return redirect('accounts:admin_dashboard')
    elif user.role == 'hod':
        return redirect('accounts:hod_dashboard')
    elif user.role == 'staff':
        return redirect('accounts:staff_dashboard')
    elif user.role == 'student':
        return redirect('accounts:student_dashboard')
    else:
        return redirect('accounts:email_not_registered')

# Home page view
def home(request):
    return render(request, 'accounts/home.html')


# View to redirect to the login page
def home_view(request):
    return redirect('accounts:login')


# Admin Registration View for HOD
@login_required
def admin_register(request):
    if request.user.role == 'admin':  # Only admin can register HOD users
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.role = 'hod'  # Admin registers as HOD
                user.save()
                return redirect('accounts:hod_dashboard')  # Redirect to HOD dashboard
        else:
            form = UserCreationForm()

        return render(request, 'accounts/register_admin.html', {'form': form})
    else:
        raise PermissionDenied("You do not have permission to register HOD users.")


# HOD Registration View for Staff
@login_required
def hod_register(request):
    if request.user.role == 'hod':  # Only HOD can register staff users
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.role = 'staff'  # HOD registers as Staff
                user.save()
                return redirect('accounts:staff_dashboard')  # Redirect to Staff dashboard
        else:
            form = UserCreationForm()

        return render(request, 'accounts/register_hod.html', {'form': form})
    else:
        raise PermissionDenied("You do not have permission to register Staff users.")


# Staff Registration View for Staff user (Only Admin can do this)
@login_required
def staff_register(request):
    if request.user.role == 'admin':  # Only admin can register staff
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.role = 'staff'  # Admin registers as Staff
                user.save()
                return redirect('accounts:staff_dashboard')  # Redirect to Staff dashboard
        else:
            form = UserCreationForm()

        return render(request, 'accounts/register_staff.html', {'form': form})
    else:
        raise PermissionDenied("You do not have permission to register Staff users.")


# View for Admin dashboard



# View for Admin dashboard
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('accounts:login')  # Only admin can access

    # Existing logic
    hod_users = CustomUser.objects.filter(role='hod')

    # ✅ Added counts for dashboard statistics
    total_campuses = Campus.objects.count()
    total_schools = School.objects.count()
    total_departments = Department.objects.count()
    total_users = CustomUser.objects.count()

    context = {
        'users': hod_users,  # keep existing
        'total_campuses': total_campuses,
        'total_schools': total_schools,
        'total_departments': total_departments,
        'total_users': total_users,
        'total_campuses': Campus.objects.count(),
        'total_schools': School.objects.count(),
        'total_departments': Department.objects.count(),
        'total_users': CustomUser.objects.count(),
        'campus_names': list(Campus.objects.values_list('name', flat=True)),
        'campus_school_counts': [campus.school_set.count() for campus in Campus.objects.all()],
        'school_names': list(School.objects.values_list('name', flat=True)),
        'school_department_counts': [school.department_set.count() for school in School.objects.all()],
    }

    return render(request, 'accounts/admin_dashboard.html', context)


def settings_page(request):
    return render(request, 'accounts/settings_page.html')
    
@login_required
def hod_dashboard(request):
    user = request.user
    if user.role != 'hod':
        return redirect('accounts:login')

    now = timezone.now()

    # -----------------------------
    # HOD-related entities
    # -----------------------------
    hod_departments = user.department.all()
    hod_schools = School.objects.filter(department__in=hod_departments).distinct()
    hod_campuses = Campus.objects.filter(school__in=hod_schools).distinct()
    
    staff_qs = CustomUser.objects.filter(role='staff', department__in=hod_departments).distinct()
    
    # -----------------------------
    # Projects for HOD
    # -----------------------------
    projects_qs = Project.objects.filter(
        Q(created_by=user) |
        Q(created_by__in=staff_qs) |
        Q(department__in=hod_departments)
    ).distinct()

    # -----------------------------
    # Current project selection
    # -----------------------------
    project_id = request.GET.get('project')
    current_project = None
    if project_id:
        current_project = projects_qs.filter(id=project_id).first()
    # Optional: select first project if none chosen
    # elif projects_qs.exists():
    #     current_project = projects_qs.first()

    # -----------------------------
    # Tasks related to HOD projects
    # -----------------------------
    tasks_qs = Task.objects.filter(
        Q(project__department__in=hod_departments) |
        Q(assigned_to__in=staff_qs) |
        Q(assigned_to__in=CustomUser.objects.filter(role='student', department__in=hod_departments)) |
        Q(assigned_by=user)
    ).distinct()

    if current_project:
        tasks_qs = tasks_qs.filter(project=current_project)
    
    # -----------------------------
    # Kanban tasks
    # -----------------------------
    kanban_tasks = {
        'to_do': tasks_qs.filter(status='to_do'),
        'in_progress': tasks_qs.filter(status='in_progress'),
        'in_review': tasks_qs.filter(status='in_review'),
        'done': tasks_qs.filter(status='done'),
    }

    # -----------------------------
    # Status overview counts
    # -----------------------------
    todo_count = kanban_tasks['to_do'].count()
    in_progress_count = kanban_tasks['in_progress'].count()
    in_review_count = kanban_tasks['in_review'].count()
    done_count = kanban_tasks['done'].count()
    completed_count = tasks_qs.filter(status='done', updated_at__gte=now-timedelta(days=7)).count()
    updated_count = tasks_qs.filter(updated_at__gte=now-timedelta(days=7)).count()
    created_count = tasks_qs.filter(created_at__gte=now-timedelta(days=7)).count()
    due_soon_count = tasks_qs.filter(due_date__lte=now+timedelta(days=7), status__in=['to_do','in_progress']).count()

    # -----------------------------
    # Staff & students for task assignment
    # -----------------------------
    staff = staff_qs
    students = CustomUser.objects.filter(role='student', department__in=hod_departments).distinct()
    staff_and_students = staff | students

    # -----------------------------
    # Teams for HOD
    # -----------------------------
    teams = Team.objects.filter(
        members__department__in=hod_departments
    ).distinct().prefetch_related(
        Prefetch("members", queryset=CustomUser.objects.filter(department__in=hod_departments).distinct())
    )

    # -----------------------------
    # Recent activities (last 5 tasks)
    # -----------------------------
    recent_activities = tasks_qs.order_by('-created_at')[:5]

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        'staff_and_students': staff_and_students,
        'active_tab': 'summary',
        'kanban_tasks': kanban_tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'in_review_count': in_review_count,
        'done_count': done_count,
        'completed_count': completed_count,
        'updated_count': updated_count,
        'created_count': created_count,
        'due_soon_count': due_soon_count,
        'recent_activities': recent_activities,
        'projects': projects_qs,
        'teams': teams,
        'current_project': current_project,
        "total_staff": staff.count(),
        "total_projects": projects_qs.count(),
        "staff_by_campus": [{'campus': c, 'count': staff_qs.filter(campus=c).count()} for c in hod_campuses],
        "staff_by_department": [{'department': d, 'count': staff_qs.filter(department=d).count()} for d in hod_departments],
    }

    return render(request, "accounts/summary.html", context)



@login_required
def hod_staff(request):
    user = request.user

    # HOD's departments, schools, campuses
    hod_departments = user.department.all()
    hod_schools = School.objects.filter(department__in=hod_departments).distinct()
    hod_campuses = Campus.objects.filter(school__in=hod_schools).distinct()

    # Staff in HOD's departments
    staff = CustomUser.objects.filter(role='staff', department__in=hod_departments).distinct()

    # -----------------------------
    # Projects based on role
    # -----------------------------
    if user.role == 'hod':
        # Projects:
        # - Created by HOD
        # - Created by staff in HOD's departments
        # - Belonging to HOD's departments
        projects = Project.objects.filter(
            Q(created_by=user) |
            Q(created_by__in=staff) |
            Q(department__in=hod_departments)
        ).distinct()
    else:  # Staff (if this view is accessed by staff)
        projects = Project.objects.filter(
            Q(tasks__assigned_to=user) | Q(created_by=user)
        ).distinct()

    # -----------------------------
    # Handle staff creation
    # -----------------------------
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        emp_id = request.POST.get("emp_id")
        phone_number = request.POST.get("phone_number")
        gender = request.POST.get("gender")
        campus_id = request.POST.get("campus")
        school_id = request.POST.get("school")
        dept_ids = request.POST.getlist("department")

        # Check duplicate email
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "This email already exists!")
            return redirect('accounts:hod_staff')

        # Create staff
        new_staff = CustomUser.objects.create(
            email=email,
            username=email,
            emp_id=emp_id,
            phone_number=phone_number,
            gender=gender,
            role='staff',
            campus_id=campus_id,
            school_id=school_id,
        )

        # Filter departments to HOD's departments only
        allowed_dept_ids = [str(d.id) for d in hod_departments]
        filtered_dept_ids = [int(did) for did in dept_ids if did in allowed_dept_ids]
        new_staff.department.set(filtered_dept_ids)
        new_staff.save()

        messages.success(request, "Staff created successfully!")
        return redirect('accounts:hod_staff')

    return render(request, "accounts/hod_staff.html", {
        "staff": staff,
        "campuses": hod_campuses,
        "schools": hod_schools,
        "departments": hod_departments,
        "projects": projects,  # Role-wise projects
    })


@login_required
def edit_staff(request, staff_id):
    staff_user = get_object_or_404(CustomUser, id=staff_id)

    # Optionally: restrict editing to HOD's departments
    hod_user = request.user
    allowed_departments = Department.objects.filter(school__campus=hod_user.campus)
    if not staff_user.department.filter(id__in=allowed_departments).exists():
        messages.error(request, "You cannot edit this staff member.")
        return redirect('accounts:hod_staff')

    if request.method == 'POST':
        staff_user.username = request.POST.get('username')
        staff_user.email = request.POST.get('email')
        staff_user.emp_id = request.POST.get('emp_id')
        staff_user.phone_number = request.POST.get('phone_number')
        staff_user.gender = request.POST.get('gender')
        campus_id = request.POST.get('campus')
        school_id = request.POST.get('school')
        department_ids = request.POST.getlist('department')

        staff_user.campus = Campus.objects.filter(id=campus_id).first() if campus_id else None
        staff_user.school = School.objects.filter(id=school_id).first() if school_id else None
        staff_user.department.set(Department.objects.filter(id__in=department_ids))

        staff_user.save()
        messages.success(request, "Staff updated successfully.")
        return redirect('accounts:hod_staff')

    context = {
        'staff_user': staff_user,
        'campuses': Campus.objects.all(),
        'schools': School.objects.all(),
        'departments': Department.objects.all()
    }
    return render(request, 'accounts/edit_staff.html', context)

def update_staff(request, staff_id):
    # Use CustomUser instead of Staff
    staff_member = get_object_or_404(CustomUser, id=staff_id, role='staff')

    if request.method == "POST":
        staff_member.email = request.POST.get("email")
        staff_member.username = staff_member.email
        staff_member.emp_id = request.POST.get("emp_id")
        staff_member.phone_number = request.POST.get("phone_number")
        staff_member.gender = request.POST.get("gender")
        staff_member.campus_id = request.POST.get("campus")
        staff_member.school_id = request.POST.get("school")
        dept_ids = request.POST.getlist("department")
        staff_member.save()
        staff_member.department.set(dept_ids)
        messages.success(request, "Staff updated successfully!")
        return redirect('accounts:hod_staff')


def delete_staff(request, staff_id):
    staff_member = get_object_or_404(CustomUser, id=staff_id, role='staff')
    staff_member.delete()
    messages.success(request, "Staff deleted successfully!")
    return redirect('accounts:hod_staff')


import csv
from django.http import HttpResponse, JsonResponse
from django.contrib import messages


@login_required
def upload_staff_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            success_count = 0
            error_count = 0
            error_rows = []

            for row_number, row in enumerate(reader, start=2):  # Start at 2 for header row offset
                try:
                    # Get or create Campus and School
                    campus_name = row.get('campus_name', '').strip()
                    school_name = row.get('school_name', '').strip()
                    if not campus_name or not school_name:
                        raise ValueError("Campus or School name missing.")

                    campus, _ = Campus.objects.get_or_create(name=campus_name)
                    school, _ = School.objects.get_or_create(name=school_name, campus=campus)

                    # Create or update staff
                    email = row.get('email', '').strip()
                    if not email:
                        raise ValueError("Email is missing.")

                    staff, created = User.objects.update_or_create(
                        email=email,
                        defaults={
                            'emp_id': row.get('emp_id', '').strip(),
                            'phone_number': row.get('phone_number', '').strip(),
                            'campus': campus,
                            'school': school,
                            'role': 'staff',  # ensure role field exists
                        }
                    )

                    # Set default password for new users
                    if created:
                        staff.set_password('Default123!')
                        staff.save()

                    # Handle multiple departments
                    dept_names = row.get('department_names', '').split(';')
                    departments = []
                    for dept_name in dept_names:
                        dept_name = dept_name.strip()
                        if dept_name:
                            # Create department if it doesn't exist and attach
                            department, _ = Department.objects.get_or_create(
                                name=dept_name,
                                school=school
                            )
                            departments.append(department)

                    staff.department.set(departments)  # Update M2M field
                    success_count += 1

                except Exception as row_error:
                    error_count += 1
                    error_rows.append((row_number, str(row_error)))
                    print(f"Error processing row {row_number}: {row} - {row_error}")

            if success_count:
                messages.success(request, f'Successfully imported {success_count} staff members.')
            if error_count:
                messages.error(
                    request, 
                    f'Failed to import {error_count} rows. Errors: {error_rows}'
                )

        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')

    return redirect('accounts:hod_staff')



@login_required
def download_staff_csv_template(request):
    user = request.user

    # Ensure only HODs can access this feature
    if user.role != 'hod':
        return HttpResponse("You are not authorized to download this template.", status=403)

    # Fetch related fields
    campus_name = user.campus.name if hasattr(user, 'campus') and user.campus else ''
    school_name = user.school.name if hasattr(user, 'school') and user.school else ''

    # Handle multiple departments (if HOD manages more than one)
    if hasattr(user, 'department'):
        departments = user.department.all()
        department_names = ";".join([dept.name for dept in departments])
    else:
        department_names = ''

    # Prepare the response
    response = HttpResponse(content_type='text/csv')
    filename = f"staff_template_{user.username}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['email', 'emp_id', 'phone_number', 'campus_name', 'school_name', 'department_names'])
    writer.writerow(['staff@example.com', 'EMP001', '1234567890', campus_name, school_name, department_names])

    return response




# -------------------------------
# Download CSV Template for Users
# -------------------------------
@login_required
def download_users_csv_template(request):
    """
    Generate a CSV template for uploading users.
    Format: Email | Emp ID | Phone | Campus | School | Departments
    Includes one sample row with random values
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_upload_template.csv"'

    writer = csv.writer(response)

    # Header row
    writer.writerow([
        'Email',
        'Emp ID',
        'Phone',
        'Campus',
        'School',
        'Departments'  # Multiple departments separated by semicolon
    ])

    # Sample row
    writer.writerow([
        'mangesh.kokare@bds.christuniversity.in',
        '24352435',
        '43543543545',
        'Pune',
        'Law',
        'BALLB'
    ])

    return response


# -------------------------------
# Upload Users CSV
# -------------------------------
@login_required
def upload_users_csv(request):
    if request.method == "POST" and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            created_count = 0
            error_count = 0

            for row_number, row in enumerate(reader, start=2):
                try:
                    email = row.get('Email', '').strip()
                    emp_id = row.get('Emp ID', '').strip()
                    phone = row.get('Phone', '').strip()
                    campus_name = row.get('Campus', '').strip()
                    school_name = row.get('School', '').strip()
                    dept_names = row.get('Departments', '').strip()

                    if not email or not emp_id:
                        raise ValueError(f"Missing email or emp_id at row {row_number}")

                    # Get or create campus & school by name
                    campus = Campus.objects.get_or_create(name=campus_name)[0] if campus_name else None
                    school = School.objects.get_or_create(name=school_name, campus=campus)[0] if school_name else None

                    # Create or update user
                    user, created = CustomUser.objects.update_or_create(
                        email=email,
                        defaults={
                            'username': email,
                            'emp_id': emp_id,
                            'phone_number': phone,
                            'campus': campus,
                            'school': school,
                            'is_staff': True,
                        }
                    )

                    # Handle departments
                    departments = []
                    if dept_names:
                        for dept_name in dept_names.split(','):
                            dept_name = dept_name.strip()
                            if dept_name:
                                department, _ = Department.objects.get_or_create(name=dept_name, school=school)
                                departments.append(department)
                    user.department.set(departments)

                    created_count += 1

                except Exception as e:
                    error_count += 1
                    print(f"Error processing row {row_number}: {row} - {e}")

            messages.success(
                request,
                f"CSV upload complete: {created_count} users added/updated, {error_count} rows failed."
            )

        except Exception as e:
            messages.error(request, f"Failed to process CSV file: {e}")

        # Redirect to create_user page
        return redirect('/accounts/create_user/')

    messages.error(request, "No file uploaded or invalid request.")
    return redirect('/accounts/create_user/')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # 🔹 Important: Q for complex filters
from .models import Project, CustomUser, School, Campus, Department

@login_required
def hod_projects(request):
    hod_user = request.user

    # HOD-related departments
    hod_departments = hod_user.department.all()

    # Staff related to HOD
    staff_qs = CustomUser.objects.filter(role='staff', department__in=hod_departments).distinct()

    # Handle POST request to add new project + task
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        task_name = request.POST.get('task_name')
        deadline = request.POST.get('deadline')
        campus_id = request.POST.get('campus')
        school_id = request.POST.get('school')
        department_id = request.POST.get('department')
        assigned_staff_id = request.POST.get('assigned_staff')
        status = request.POST.get('status')

        try:
            department_obj = Department.objects.get(id=department_id)
            assigned_staff = CustomUser.objects.get(id=assigned_staff_id)

            # Create project
            project = Project.objects.create(
                name=project_name,
                department=department_obj,
                created_by=hod_user
            )

            # Create task
            Task.objects.create(
                title=task_name,
                assigned_to=assigned_staff,
                assigned_by=hod_user,
                project=project,
                due_date=deadline,
                status=status
            )

            messages.success(request, "Project and task added successfully!")
            return redirect('accounts:hod_projects')

        except Exception as e:
            messages.error(request, f"Error adding project/task: {str(e)}")
            # continue to render the page with context

    # Projects related to HOD departments OR tasks assigned to HOD staff
    projects = Project.objects.filter(
        Q(department__in=hod_departments) |
        Q(tasks__assigned_to__in=staff_qs)
    ).distinct()

    # HOD-related schools and campuses
    hod_schools = School.objects.filter(department__in=hod_departments).distinct()
    hod_campuses = Campus.objects.filter(school__in=hod_schools).distinct()

    context = {
        "campuses": hod_campuses,
        "schools": hod_schools,
        "departments": hod_departments,
        "staff": staff_qs,
        "projects": projects,
    }

    return render(request, "accounts/hod_project.html", context)

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    try:
        project.delete()  # This will also delete all tasks if on_delete=models.CASCADE is set
        messages.success(request, "Project and all its tasks have been deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting project: {str(e)}")

    return redirect('accounts:hod_projects')

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == "POST":
        project.name = request.POST.get("project_name")
        project.description = request.POST.get("project_description")
        project.save()
        messages.success(request, "Project updated successfully.")
        return redirect("accounts:hod_projects")

    context = {
        "project": project
    }
    return render(request, "accounts/edit_project.html", context)


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    staff = CustomUser.objects.filter(role='staff')  # staff list for selection
    if request.method == "POST":
        task.title = request.POST.get("task_name")
        task.description = request.POST.get("task_description")
        task.due_date = request.POST.get("deadline")
        task.status = request.POST.get("status")
        assigned_staff_id = request.POST.get("assigned_staff")
        if assigned_staff_id:
            task.assigned_to = CustomUser.objects.get(id=assigned_staff_id)
        task.save()
        messages.success(request, "Task updated successfully.")
        return redirect("accounts:hod_projects")

    context = {
        "task": task,
        "staff": staff
    }
    return render(request, "accounts/edit_task.html", context)

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Only staff or HOD/admin can delete tasks
    if request.user.role not in ['admin', 'hod', 'staff']:
        messages.error(request, "You do not have permission to delete this task.")
        return redirect('accounts:hod_projects')

    task.delete()
    messages.success(request, "Task deleted successfully!")
    return redirect('accounts:hod_projects')

@login_required
def hod_add_project(request):
    staff = CustomUser.objects.filter(role='staff')
    projects = Project.objects.all()

    if request.method == "POST":
        # Get POST data
        project_id = request.POST.get("project_select")  # Optional existing project
        project_name = request.POST.get("project_name")  # New project name if creating new
        task_title = request.POST.get("task_name")
        assigned_staff_id = request.POST.get("assigned_staff")
        due_date = request.POST.get("deadline")
        status = request.POST.get("status")

        # Use existing project or create new
        if project_id:
            project = Project.objects.get(id=project_id)
        else:
            project = Project.objects.create(
                name=project_name,
                created_by=request.user
            )

        assigned_staff = CustomUser.objects.get(id=assigned_staff_id)

        # Create Task using correct fields
        Task.objects.create(
            title=task_title,
            assigned_to=assigned_staff,
            assigned_by=request.user,
            project=project,
            due_date=due_date,
            status=status
        )

        messages.success(request, "Task added successfully.")
        return redirect("accounts:hod_projects")

    context = {
        "staff": staff,
        "projects": projects,
    }
    return render(request, "accounts/hod_project.html", context)


def hod_teams(request):
    return render(request, 'hod_teams.html', {})

def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        # Update task fields
        task.title = request.POST.get("task_name")
        task.description = request.POST.get("task_description", task.description)
        task.due_date = request.POST.get("deadline")
        task.status = request.POST.get("status")
        assigned_staff_id = request.POST.get("assigned_staff")
        if assigned_staff_id:
            task.assigned_to = CustomUser.objects.get(id=assigned_staff_id)
        task.save()
        messages.success(request, "Task updated successfully!")
        return redirect("accounts:hod_projects")
    

           
# ---------------- MANAGE STAFF ----------------
@login_required
def manage_staff(request):
    if not hasattr(request.user, "role") or request.user.role != 'hod':
        return redirect('accounts:login')
    
    staff_list = CustomUser.objects.filter(role='staff')
    campuses = Campus.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()
    
    return render(request, 'accounts/manage_staff.html', {
        'staff_list': staff_list,
        'campuses': campuses,
        'schools': schools,
        'departments': departments
    })

# ---------------- CREATE STAFF ----------------
@login_required
def hod_create_staff(request):
    if not hasattr(request.user, "role") or request.user.role != 'hod':
        return redirect('accounts:login')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        username = email.split('@')[0]  # auto-generate username
        emp_id = request.POST.get('emp_id')
        phone_number = request.POST.get('phone_number')
        gender = request.POST.get('gender')
        campus_id = request.POST.get('campus')
        school_id = request.POST.get('school')
        department_id = request.POST.get('department')
        
        # Get related objects
        campus = Campus.objects.get(id=campus_id) if campus_id else None
        school = School.objects.get(id=school_id) if school_id else None
        department = Department.objects.get(id=department_id) if department_id else None
        
        # Create staff user
        staff = CustomUser.objects.create_user(
            username=username,
            email=email,
            role='staff',
            emp_id=emp_id,
            phone_number=phone_number,
            gender=gender,
            campus=campus,
            school=school,
            password='defaultpassword123'
        )

        # Assign department using .set() (if it's a ManyToManyField)
        if department:
            staff.department.set([department])  # Use set() for ManyToManyField

        messages.success(request, f'Staff {email} created successfully!')
        return redirect('accounts:manage_staff')
    
    campuses = Campus.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()
    
    return render(request, 'accounts/hod_create_staff.html', {
        'campuses': campuses,
        'schools': schools,
        'departments': departments
    })

# ---------------- UPDATE STAFF ----------------
@login_required
def hod_update_staff(request, staff_id):
    # Check if the user is 'hod'
    if not hasattr(request.user, "role") or request.user.role != 'hod':
        return redirect('accounts:login')

    # Get the staff instance
    staff = CustomUser.objects.get(id=staff_id)

    if request.method == 'POST':
        email = request.POST.get('email')
        emp_id = request.POST.get('emp_id')
        phone_number = request.POST.get('phone_number')
        gender = request.POST.get('gender')
        campus_id = request.POST.get('campus')
        school_id = request.POST.get('school')
        department_ids = request.POST.getlist('department')  # Use getlist() for multiple departments

        # Fetch the related objects (Campus, School, Department)
        campus = Campus.objects.get(id=campus_id) if campus_id else None
        school = School.objects.get(id=school_id) if school_id else None
        departments = Department.objects.filter(id__in=department_ids)  # Get departments by ID

        # Update the staff user
        staff.email = email
        staff.emp_id = emp_id
        staff.phone_number = phone_number
        staff.gender = gender
        staff.campus = campus
        staff.school = school
        staff.save()

        # Use .set() to assign multiple departments
        if departments.exists():
            staff.department.set(departments)  # This updates the many-to-many relationship

        messages.success(request, f'Staff {email} updated successfully!')
        return redirect('accounts:manage_staff')

    # Pre-fill the form with existing data
    campuses = Campus.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()

    return render(request, 'accounts/hod_update_staff.html', {
        'staff': staff,
        'campuses': campuses,
        'schools': schools,
        'departments': departments,
    })


# ---------------- DELETE STAFF ----------------
@login_required
def hod_delete_staff(request, staff_id):
    if request.user.role != 'hod':
        return HttpResponseForbidden("You are not authorized to perform this action.")
    
    staff = get_object_or_404(CustomUser, id=staff_id, role='staff')
    email = staff.email
    staff.delete()
    messages.success(request, f'{email} deleted successfully!')
    return redirect('accounts:manage_staff')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_subtask_time(request, subtask_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        elapsed_seconds = data.get('time_spent', 0)
        subtask = SubTask.objects.get(id=subtask_id)

        # Save total_time_seconds
        if hasattr(subtask, 'total_time_seconds'):
            subtask.total_time_seconds += elapsed_seconds
        else:
            subtask.total_time_seconds = elapsed_seconds

        # Optional: save total_time as timedelta
        from datetime import timedelta
        if hasattr(subtask, 'total_time'):
            subtask.total_time += timedelta(seconds=elapsed_seconds)
        else:
            subtask.total_time = timedelta(seconds=elapsed_seconds)

        subtask.save()
        return JsonResponse({'status': 'success', 'total_time_seconds': subtask.total_time_seconds})
    return JsonResponse({'status': 'fail'})

@login_required 
def staff_dashboard(request):
    if request.user.role != 'staff':
        return redirect('accounts:login')

    user = request.user
    user_departments = user.department.all()

    # -----------------------------
    # Task creation form handling
    # -----------------------------
    if request.method == 'POST' and 'create_task' in request.POST:
        task_form = TaskForm(request.POST)
        if task_form.is_valid():
            task = task_form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            messages.success(request, "Task created successfully!")
            return redirect('accounts:staff_dashboard')
        else:
            messages.error(request, "There was an error creating the task.")
    else:
        task_form = TaskForm()

    # -----------------------------
    # Fetch projects where staff belongs to the department or is assigned/creator
    # -----------------------------
    projects = Project.objects.filter(
        Q(department__in=user_departments) | Q(tasks__assigned_to=user) | Q(created_by=user)
    ).distinct()  # distinct avoids duplicates if multiple criteria match

    # -----------------------------
    # Current project selection
    # -----------------------------
    project_id = request.GET.get('project')
    current_project = None
    if project_id:
        current_project = projects.filter(id=project_id).first()
    # If no project selected, keep current_project as None to show all projects
    # else:
    #     current_project = projects.first()

    # -----------------------------
    # Tasks in selected project or all visible projects
    # -----------------------------
    if current_project:
        tasks = Task.objects.filter(project=current_project)
    else:
        tasks = Task.objects.filter(project__in=projects)
    tasks = tasks.order_by('-created_at')

    # -----------------------------
    # Kanban organization
    # -----------------------------
    kanban_tasks = {
        'to_do': tasks.filter(status='to_do'),
        'in_progress': tasks.filter(status='in_progress'),
        'in_review': tasks.filter(status='in_review'),
        'done': tasks.filter(status='done'),
    }

    # -----------------------------
    # Status overview counts
    # -----------------------------
    todo_count = kanban_tasks['to_do'].count()
    in_progress_count = kanban_tasks['in_progress'].count()
    in_review_count = kanban_tasks['in_review'].count()
    done_count = kanban_tasks['done'].count()
    completed_count = tasks.filter(status='done', updated_at__gte=timezone.now()-timedelta(days=7)).count()
    updated_count = tasks.filter(updated_at__gte=timezone.now()-timedelta(days=7)).count()
    created_count = tasks.filter(created_at__gte=timezone.now()-timedelta(days=7)).count()
    due_soon_count = tasks.filter(due_date__lte=timezone.now()+timedelta(days=7), status__in=['to_do','in_progress']).count()

    # -----------------------------
    # Users in the same department (distinct)
    # -----------------------------
    staff_and_students = CustomUser.objects.filter(
        role='staff',
        department__in=user_departments
    ).distinct()  # distinct ensures a user appears only once

    # -----------------------------
    # Teams: only teams that have members in the user's departments
    # -----------------------------
    teams = Team.objects.filter(
        members__department__in=user_departments
    ).distinct().prefetch_related(
        Prefetch("members", queryset=CustomUser.objects.filter(department__in=user_departments).distinct())
    )

    # -----------------------------
    # Recent activities (last 5 tasks)
    # -----------------------------
    recent_activities = tasks[:5]

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        'staff_and_students': staff_and_students,
        'active_tab': 'summary',
        'task_form': task_form,
        'kanban_tasks': kanban_tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'in_review_count': in_review_count,
        'done_count': done_count,
        'completed_count': completed_count,
        'updated_count': updated_count,
        'created_count': created_count,
        'due_soon_count': due_soon_count,
        'recent_activities': recent_activities,
        'projects': projects,
        'teams': teams,
        'current_project': current_project,
    }

    return render(request, 'accounts/summary.html', context)





def delete_team(request):
    if request.method == "POST":
        team_id = request.POST.get("team_id")
        team = get_object_or_404(Team, id=team_id)
        team.delete()
    return redirect("accounts:staff_dashboard")



def staff_dashboard_3(request):
    return render(request, "accounts/staff_dashboard_3.html")



@login_required
def create_project(request):
    user = request.user

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        if name:
            project = Project.objects.create(
                name=name,
                description=description,
                created_by=user,
                created_at=timezone.now()
            )

            # If HOD, automatically associate with their departments
            if user.role == 'hod':
                hod_departments = user.department.all()
                # Check if hod_departments is not empty
                if hod_departments.exists():
                    project.department.set(hod_departments)
                else:
                    # Handle the case where no departments are found, e.g., show an error or handle gracefully
                    messages.error(request, 'No departments found to associate with the project.')

            project.save()
            return redirect('accounts:hod_dashboard')  # redirect to summary/dashboard

    return render(request, 'accounts/create_project.html')


@login_required
def timeline_page(request):
    user = request.user

    # -----------------------------
    # Projects based on role
    # -----------------------------
    if user.role == 'hod':
        hod_departments = user.department.all()
        staff_qs = CustomUser.objects.filter(
            role='staff',
            department__in=hod_departments
        ).distinct()

        projects = Project.objects.filter(
            Q(created_by=user) |
            Q(created_by__in=staff_qs) |
            Q(department__in=hod_departments)
        ).distinct()

        # Users in HOD's departments (exclude HODs and Admins)
        staff_and_students = CustomUser.objects.filter(
            department__in=hod_departments
        ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()

        # Teams in HOD's departments (exclude HODs and Admins)
        teams = Team.objects.filter(
            members__department__in=hod_departments
        ).distinct().prefetch_related(
            Prefetch(
                "members",
                queryset=CustomUser.objects.filter(
                    department__in=hod_departments
                ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()
            )
        )

    else:  # Staff
        user_departments = user.department.all()

        projects = Project.objects.filter(
            Q(tasks__assigned_to=user) |
            Q(created_by=user) |
            Q(department__in=user_departments)
        ).distinct()

        # Users in staff's departments (exclude HODs and Admins)
        staff_and_students = CustomUser.objects.filter(
            department__in=user_departments
        ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()

        # Teams in staff's departments (exclude HODs and Admins)
        teams = Team.objects.filter(
            members__department__in=user_departments
        ).distinct().prefetch_related(
            Prefetch(
                "members",
                queryset=CustomUser.objects.filter(
                    department__in=user_departments
                ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()
            )
        )

    # -----------------------------
    # Current project selection
    # -----------------------------
    selected_project_id = request.GET.get("project")
    current_project = get_object_or_404(projects, id=selected_project_id) if selected_project_id else None

    # -----------------------------
    # Tasks for selected project or all visible projects
    # -----------------------------
    if current_project:
        tasks = Task.objects.filter(project=current_project)
    else:
        tasks = Task.objects.filter(project__in=projects)

    # -----------------------------
    # Filters
    # -----------------------------
    query = request.GET.get("q", "").strip()
    sprint_filter = request.GET.get("sprint", "").strip()

    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) |
            Q(due_date__icontains=query)
        )
    if sprint_filter:
        tasks = tasks.filter(sprint=sprint_filter)

    # -----------------------------
    # Tasks sorted by due date & distinct sprints
    # -----------------------------
    tasks_by_date = tasks.order_by("due_date")
    sprints = Task.objects.exclude(sprint__exact="").values_list("sprint", flat=True).distinct()

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "tasks": tasks_by_date,
        "teams": teams,
        "projects": projects,
        "current_project": current_project,
        "sprints": sprints,
        "query": query,
        "selected_sprint": sprint_filter,
        "active_tab": "timeline",
        "today": timezone.now().date(),
        "staff_and_students": staff_and_students,
    }

    return render(request, "accounts/timeline.html", context)





@login_required
def board_page(request):
    user = request.user

    # -----------------------------
    # Projects based on role
    # -----------------------------
    if user.role == 'hod':
        hod_departments = user.department.all()
        staff_qs = CustomUser.objects.filter(
            role='staff', department__in=hod_departments
        ).distinct()

        # Projects
        projects = Project.objects.filter(
            Q(created_by=user) |
            Q(created_by__in=staff_qs) |
            Q(department__in=hod_departments)
        ).distinct()

        # Users in HOD's departments (exclude HODs and Admins)
        staff_and_students = CustomUser.objects.filter(
            department__in=hod_departments
        ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()

        # Teams in HOD's departments (exclude HODs and Admins)
        teams = Team.objects.filter(
            members__department__in=hod_departments
        ).distinct().prefetch_related(
            Prefetch(
                "members",
                queryset=CustomUser.objects.filter(
                    department__in=hod_departments
                ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()
            )
        )

    else:  # Staff
        user_departments = user.department.all()

        # Projects: assigned to or created by the staff OR in their departments
        projects = Project.objects.filter(
            Q(tasks__assigned_to=user) |
            Q(created_by=user) |
            Q(department__in=user_departments)
        ).distinct()

        # Users in staff's departments (exclude HODs and Admins)
        staff_and_students = CustomUser.objects.filter(
            department__in=user_departments
        ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()

        # Teams in staff's departments (exclude HODs and Admins)
        teams = Team.objects.filter(
            members__department__in=user_departments
        ).distinct().prefetch_related(
            Prefetch(
                "members",
                queryset=CustomUser.objects.filter(
                    department__in=user_departments
                ).exclude(Q(role='hod') | Q(role='admin') | Q(is_superuser=True)).distinct()
            )
        )

    # -----------------------------
    # Current project selection
    # -----------------------------
    project_id = request.GET.get('project')
    current_project = get_object_or_404(projects, id=project_id) if project_id else None

    # -----------------------------
    # Tasks for selected project or all visible projects
    # -----------------------------
    if current_project:
        tasks = Task.objects.filter(project=current_project)
    else:
        tasks = Task.objects.filter(project__in=projects)

    # -----------------------------
    # Filters
    # -----------------------------
    query = request.GET.get('q')
    status = request.GET.get('status')
    priority = request.GET.get('priority')

    if query:
        tasks = tasks.filter(title__icontains=query)
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)

    # -----------------------------
    # Kanban columns
    # -----------------------------
    kanban_tasks = {
        'to_do': tasks.filter(status='to_do'),
        'in_progress': tasks.filter(status='in_progress'),
        'in_review': tasks.filter(status='in_review'),
        'done': tasks.filter(status='done'),
    }

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        'projects': projects,
        'staff_and_students': staff_and_students,
        'teams': teams,
        'tasks': tasks,
        'kanban_tasks': kanban_tasks,
        'current_project': current_project,
        'active_tab': 'board',
    }

    return render(request, 'accounts/board.html', context)




from django.views.decorators.http import require_POST
from .models import Project, Task, SubTask, Comment

@require_POST
def add_subtask(request):
    task_id = request.POST.get('task_id')
    title = request.POST.get('title')
    deadline = request.POST.get('deadline')
    description = request.POST.get('description')

    task = get_object_or_404(Task, id=task_id)

    SubTask.objects.create(
        task=task,
        title=title,
        description=description,
        deadline=deadline if deadline else None
    )

    return redirect(request.META.get('HTTP_REFERER', 'accounts:board_page'))

@require_POST
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    comment_text = request.POST.get('comment')
    if comment_text:
        Comment.objects.create(task=task, user=request.user, text=comment_text)
    return redirect(request.META.get('HTTP_REFERER', 'accounts:board_page'))


def edit_subtask(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk)

    if request.method == "POST":
        subtask.title = request.POST.get('title', subtask.title)
        subtask.description = request.POST.get('description', subtask.description)

        deadline_str = request.POST.get('deadline', '')
        if deadline_str:
            subtask.deadline = deadline_str  # Django will parse YYYY-MM-DD correctly
        else:
            subtask.deadline = None  # no date provided

        subtask.status = request.POST.get('status', subtask.status)
        subtask.save()

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect(request.META.get('HTTP_REFERER', '/'))


def profile_view(request):
    user = request.user

    # -----------------------------
    # Projects based on role
    # -----------------------------
    if user.role == 'hod':
        hod_departments = user.department.all()
        staff_qs = CustomUser.objects.filter(role='staff', department__in=hod_departments).distinct()

        # Projects:
        # - Created by HOD
        # - Created by staff in HOD's departments
        # - Belonging to HOD's departments
        projects = Project.objects.filter(
            Q(created_by=user) |
            Q(created_by__in=staff_qs) |
            Q(department__in=hod_departments)
        ).distinct()

    else:  # Staff
        projects = Project.objects.filter(
            Q(tasks__assigned_to=user) | Q(created_by=user)
        ).distinct()

    # -----------------------------
    # Current project selection
    # -----------------------------
    project_id = request.GET.get('project')
    current_project = get_object_or_404(projects, id=project_id) if project_id else None

    # -----------------------------
    # Tasks for selected project or all visible projects
    # -----------------------------
    if current_project:
        tasks = Task.objects.filter(project=current_project)
    else:
        tasks = Task.objects.filter(project__in=projects)

    # -----------------------------
    # Filters
    # -----------------------------
    query = request.GET.get('q')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    team_filter = request.GET.get('team')

    if query:
        tasks = tasks.filter(title__icontains=query)
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if team_filter:
        tasks = tasks.filter(team__id=team_filter)

    # -----------------------------
    # Users and teams (only staff from the same department)
    # -----------------------------
    staff_and_students = CustomUser.objects.filter(
        role='staff', department__in=request.user.department.all()
    )

    teams = Team.objects.prefetch_related(
        Prefetch("members", queryset=CustomUser.objects.all())
    ).all()

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        'projects': projects,
        'tasks': tasks,
        'teams': teams,
        'current_project': current_project,
        'active_tab': 'backlog',
        'staff_and_students': staff_and_students,  # Pass filtered staff members
    }

    return render(request, "accounts/profile.html", context)


def settings_view(request):
    return render(request, "accounts/settings.html")

def logout_view(request):
    logout(request)
    return redirect("accounts:login")



from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import CustomUser, Team, Project, Task

@login_required
def create_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        team_id = request.POST.get('team')
        project_id = request.POST.get('project')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date') or None

        if not assigned_to_id and not team_id:
            messages.error(request, 'You must assign this task to a user or a team.')
            return redirect('accounts:staff_dashboard')

        assigned_to = get_object_or_404(CustomUser, id=assigned_to_id) if assigned_to_id else None
        team = get_object_or_404(Team, id=team_id) if team_id else None
        project = get_object_or_404(Project, id=project_id) if project_id else None

        assigned_by = request.user

        if assigned_to:
            # Create task for individual user
            Task.objects.create(
                title=title,
                description=description,
                assigned_to=assigned_to,
                team=team,
                project=project,
                assigned_by=assigned_by,
                status=status,
                priority=priority,
                due_date=due_date
            )
        elif team:
            # Create task for all team members including team lead
            team_members = list(team.members.all())
            if team.staff not in team_members:
                team_members.append(team.staff)

            for member in team_members:
                Task.objects.create(
                    title=title,
                    description=description,
                    assigned_to=member,
                    team=team,
                    project=project,
                    assigned_by=assigned_by,
                    status=status,
                    priority=priority,
                    due_date=due_date
                )

        messages.success(request, 'Task created successfully!')
        return redirect('accounts:staff_dashboard')

    # Filter users in the same department as the logged-in user
    logged_in_user = request.user
    staff_and_students = CustomUser.objects.filter(department__in=logged_in_user.department.all())

    teams = Team.objects.all()  # Add your logic to fetch the available teams
    projects = Project.objects.all()  # Add your logic to fetch the available projects

    return render(request, 'accounts/create_task_modal.html', {
        'staff_and_students': staff_and_students,
        'teams': teams,
        'projects': projects,
    })

def update_task_status(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_status = request.POST.get("new_status")

        task = get_object_or_404(Task, id=task_id)

        # If moving to in_progress, start timer
        if new_status == "in_progress":
            if not task.start_time:  # Start only if not already started
                task.start_time = timezone.now()
        # If moving to done, calculate elapsed time
        elif new_status == "done":
            if task.start_time:
                elapsed = timezone.now() - task.start_time
                if task.total_time:
                    task.total_time += elapsed
                else:
                    task.total_time = elapsed
                task.start_time = None  # Reset timer after done
        # If moving back to to_do or in_review, just reset start_time
        elif new_status in ["to_do", "in_review"]:
            task.start_time = None

        task.status = new_status
        task.save()
        messages.success(request, f"Task '{task.title}' moved to {new_status.replace('_',' ').title()}")

        # Redirect back
        project_id = request.GET.get("project")
        return redirect(f"{request.META.get('HTTP_REFERER','/')}")


@login_required
def backlog_page(request):
    user = request.user

    # -----------------------------
    # Projects based on role
    # -----------------------------
    if user.role == 'hod':
        hod_departments = user.department.all()
        staff_qs = CustomUser.objects.filter(role='staff', department__in=hod_departments).distinct()

        # Projects:
        # - Created by HOD
        # - Created by staff in HOD's departments
        # - Belonging to HOD's departments
        projects = Project.objects.filter(
            Q(created_by=user) |
            Q(created_by__in=staff_qs) |
            Q(department__in=hod_departments)
        ).distinct()

        # Users in HOD's departments (distinct)
        staff_and_students = CustomUser.objects.filter(
            role='staff',
            department__in=hod_departments
        ).distinct()

        # Teams in HOD's departments
        teams = Team.objects.filter(
            members__department__in=hod_departments
        ).distinct().prefetch_related(
            Prefetch("members", queryset=CustomUser.objects.filter(department__in=hod_departments).distinct())
        )

    else:  # Staff
        user_departments = user.department.all()

        # Projects: assigned to or created by the staff OR in their departments
        projects = Project.objects.filter(
            Q(tasks__assigned_to=user) | Q(created_by=user) | Q(department__in=user_departments)
        ).distinct()

        # Users in staff's departments (distinct)
        staff_and_students = CustomUser.objects.filter(
            role='staff',
            department__in=user_departments
        ).distinct()

        # Teams in staff's departments
        teams = Team.objects.filter(
            members__department__in=user_departments
        ).distinct().prefetch_related(
            Prefetch("members", queryset=CustomUser.objects.filter(department__in=user_departments).distinct())
        )

    # -----------------------------
    # Current project selection
    # -----------------------------
    project_id = request.GET.get('project')
    current_project = get_object_or_404(projects, id=project_id) if project_id else None

    # -----------------------------
    # Tasks for selected project or all visible projects
    # -----------------------------
    if current_project:
        tasks = Task.objects.filter(project=current_project)
    else:
        tasks = Task.objects.filter(project__in=projects)

    # -----------------------------
    # Filters
    # -----------------------------
    query = request.GET.get('q')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    team_filter = request.GET.get('team')

    if query:
        tasks = tasks.filter(title__icontains=query)
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if team_filter:
        tasks = tasks.filter(team__id=team_filter)

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        'projects': projects,
        'tasks': tasks,
        'teams': teams,
        'current_project': current_project,
        'active_tab': 'backlog',
        'staff_and_students': staff_and_students,  # Pass filtered staff members
    }

    return render(request, 'accounts/backlog.html', context)



# New view for students to see their tasks
def student_dashboard(request):
    user = request.user
    tasks = Task.objects.filter(assigned_to=user)

    # Kanban tasks
    kanban_tasks = {
        'to_do': tasks.filter(status='to_do'),
        'in_progress': tasks.filter(status='in_progress'),
        'in_review': tasks.filter(status='in_review'),
        'done': tasks.filter(status='done'),
    }

    # Counts
    completed_count = tasks.filter(status='done', updated_at__gte=date.today()-timedelta(days=7)).count()
    updated_count = tasks.filter(updated_at__gte=date.today()-timedelta(days=7)).count()
    in_progress_count = kanban_tasks['in_progress'].count()
    todo_count = kanban_tasks['to_do'].count()
    done_count = kanban_tasks['done'].count()
    created_count = tasks.filter(created_at__gte=date.today()-timedelta(days=7)).count()

    # due soon (next 7 days)
    due_soon_count = tasks.filter(due_date__range=[date.today(), date.today() + timedelta(days=7)]).count()

    context = {
        'kanban_tasks': kanban_tasks,
        'completed_count': completed_count,
        'updated_count': updated_count,
        'in_progress_count': in_progress_count,
        'todo_count': todo_count,
        'done_count': done_count,
        'created_count': created_count,
        'due_soon_count': due_soon_count,
        'active_tab': 'summary',
    }

    return render(request, 'accounts/student_dashboard.html', context)

  
@login_required
def teams_page(request):
    user = request.user

    if user.role == 'hod':
        hod_departments = user.department.all()
        staff_qs = CustomUser.objects.filter(role='staff', department__in=hod_departments).distinct()

        # Projects
        projects = Project.objects.filter(
            Q(created_by=user) |
            Q(created_by__in=staff_qs) |
            Q(department__in=hod_departments)
        ).distinct()

        # Users in HOD's departments
        staff_and_students = CustomUser.objects.filter(
            role='staff',
            department__in=hod_departments
        ).distinct()

        # Teams in HOD's departments
        teams = Team.objects.filter(
            Q(members__department__in=hod_departments) |
            Q(staff__department__in=hod_departments)
        ).distinct().prefetch_related(
            Prefetch("members", queryset=CustomUser.objects.filter(department__in=hod_departments).distinct())
        )

    else:  # Staff
        user_departments = user.department.all()

        # Projects
        projects = Project.objects.filter(
            Q(tasks__assigned_to=user) |
            Q(created_by=user) |
            Q(department__in=user_departments)
        ).distinct()

        # Users in staff's departments
        staff_and_students = CustomUser.objects.filter(
            role='staff',
            department__in=user_departments
        ).distinct()

        # Teams in staff's departments
        teams = Team.objects.filter(
            Q(members__department__in=user_departments) |
            Q(staff__department__in=user_departments) |
            Q(members=user) |
            Q(staff=user)
        ).distinct().prefetch_related(
            Prefetch("members", queryset=CustomUser.objects.filter(department__in=user_departments).distinct())
        )

    # Current project selection
    project_id = request.GET.get('project')
    current_project = get_object_or_404(projects, id=project_id) if project_id else None

    # Tasks for selected project or all visible projects
    if current_project:
        tasks = Task.objects.filter(project=current_project)
    else:
        tasks = Task.objects.filter(project__in=projects)

    # Filters
    query = request.GET.get('q')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    team_filter = request.GET.get('team')

    if query:
        tasks = tasks.filter(title__icontains=query)
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if team_filter:
        tasks = tasks.filter(team__id=team_filter)

    # Context
    context = {
        'projects': projects,
        'tasks': tasks,
        'teams': teams,
        'current_project': current_project,
        'active_tab': 'backlog',
        'staff_and_students': staff_and_students,
    }

    return render(request, 'accounts/teams_page.html', context)


@login_required
def create_team(request):
    """Create a new team with selected head"""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        head_id = request.POST.get("head")
        member_ids = request.POST.getlist("members")

        # Validation
        if not name:
            messages.error(request, "Team name is required.")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams"))

        if not head_id:
            messages.error(request, "Team lead is required.")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams"))

        try:
            # Get the selected team lead
            head = CustomUser.objects.get(id=head_id)
            
            # Filter out the head from members to avoid duplication
            filtered_member_ids = [mid for mid in member_ids if str(mid) != str(head_id)]
            
            # Create the team with the selected head
            team = Team.objects.create(
                name=name,
                staff=head
            )
            
            # Set members (excluding the head)
            if filtered_member_ids:
                members = CustomUser.objects.filter(id__in=filtered_member_ids)
                team.members.set(members)

            messages.success(request, f"Team '{name}' created successfully!")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams"))
        
        except CustomUser.DoesNotExist:
            messages.error(request, "Selected team lead does not exist.")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams"))
        except Exception as e:
            messages.error(request, f"Error creating team: {str(e)}")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams"))
    
    return redirect("accounts:teams")


@login_required
def edit_team(request, team_id):  # ✅ team_id is now a URL parameter
    """Edit an existing team with proper database updates"""
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        # Get form data
        new_name = request.POST.get('name', '').strip()
        new_head_id = request.POST.get('head')
        new_member_ids = request.POST.getlist('members[]')

        try:
            # Validate team name
            if not new_name:
                messages.error(request, "Team name cannot be empty.")
                return redirect(request.META.get("HTTP_REFERER", "accounts:teams_page"))

            # Validate team lead
            if not new_head_id:
                messages.error(request, "Team lead is required.")
                return redirect(request.META.get("HTTP_REFERER", "accounts:teams_page"))

            # Update team name
            team.name = new_name

            # Update team lead
            new_head = get_object_or_404(CustomUser, id=new_head_id)
            team.staff = new_head

            # Save the team first
            team.save()

            # Filter out the head from members to avoid duplication
            filtered_member_ids = [
                int(mid) for mid in new_member_ids 
                if str(mid) != str(new_head_id)
            ]

            # ✅ CRITICAL FIX: Properly update team members in database
            team.members.clear()  # Clear existing members first
            
            if filtered_member_ids:
                members = CustomUser.objects.filter(id__in=filtered_member_ids)
                team.members.add(*members)  # Add new members
            
            messages.success(request, f"Team '{team.name}' updated successfully!")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams_page"))

        except CustomUser.DoesNotExist:
            messages.error(request, "Selected user does not exist.")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams_page"))
        except ValueError as e:
            messages.error(request, "Invalid member ID provided.")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams_page"))
        except Exception as e:
            messages.error(request, f"Error updating team: {str(e)}")
            return redirect(request.META.get("HTTP_REFERER", "accounts:teams_page"))

    return redirect("accounts:teams_page")


@login_required
def delete_team(request, team_id):
    """Delete a team"""
    team = get_object_or_404(Team, id=team_id)
    team_name = team.name
    
    try:
        team.delete()
        messages.success(request, f"Team '{team_name}' deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting team: {str(e)}")
    
    return redirect(request.META.get("HTTP_REFERER", "accounts:teams"))


@login_required
def get_users_in_team(request, team_id):
    """Return JSON of users in a team (for AJAX calls)."""
    team = get_object_or_404(Team, id=team_id)
    users = [{'id': user.id, 'username': user.username, 'email': user.email} for user in team.members.all()]
    return JsonResponse({'users': users})


# View to assign work to students
@login_required
def assign_work(request):
    if request.user.role != 'staff':
        messages.error(request, "You do not have permission to assign work.")
        return redirect('accounts:staff_dashboard')

    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        student_ids = request.POST.getlist('student_ids')
        task_desc = request.POST.get('task_description')

        if team_id and student_ids and task_desc:
            from .models import Team, Task
            team = Team.objects.get(id=team_id)
            for sid in student_ids:
                student = CustomUser.objects.get(id=sid)
                Task.objects.create(team=team, student=student, description=task_desc)
            messages.success(request, "Work assigned successfully!")
        else:
            messages.error(request, "All fields are required.")

    return redirect('accounts:staff_dashboard')


def add_staff(request):
    if request.method == 'POST':
        form = AddStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member added successfully!')
            return redirect('accounts:hod_dashboard')
        else:
            messages.error(request, 'There were errors in the form. Please fix them below.')
            print(form.errors)  # helpful for debugging
    else:
        form = AddStaffForm()

    return render(request, 'accounts/add_staff.html', {'form': form})

@login_required
def add_hod(request):
    # Ensure only admin can add HODs
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission to add HOD.")
        return redirect('accounts:admin_dashboard')

    if request.method == 'POST':
        form = HODRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'hod'  # Set the role to HOD
            user.save()

            # Automatically create a social account for this HOD's email
            email = user.email
            # Check if the email is already linked with a social account
            social_account = SocialAccount.objects.filter(user=user).first()
            if not social_account:
                # Create a new social account for the user
                social_account = SocialAccount(user=user, provider='email')
                social_account.save()
            
            # Make sure the email address is confirmed for this user
            email_address = EmailAddress.objects.get_or_create(user=user, email=email, verified=True)
            
            # Optionally, you can create an EmailAddress instance for the social account if necessary.
            # Redirect to the admin dashboard after success
            messages.success(request, f'HOD {user.username} added successfully!')
            return redirect('accounts:admin_dashboard')

    else:
        form = HODRegisterForm()

    return render(request, 'accounts/add_hod.html', {'form': form})


@login_required
def user_detail(request, user_id):
    # Get the user by their ID
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'accounts/user_detail.html', {'user': user})


@login_required
def edit_user(request, user_id):
    # Fetch the user by ID
    user = get_object_or_404(CustomUser, id=user_id)

    # Ensure only admin or HOD can edit staff
    if request.user.role not in ['admin', 'hod']:
        messages.error(request, "You do not have permission to edit this user.")
        return redirect('accounts:dashboard')  # Redirect to a safe page

    # Handle form submission
    if request.method == 'POST':
        form = HODRegisterForm(request.POST, instance=user)  # Or a custom StaffEditForm
        if form.is_valid():
            form.save()
            messages.success(request, "User details updated successfully!")
            # Redirect to HOD staff management page
            return redirect('accounts:hod_staff')
        else:
            messages.error(request, "There were errors in the form. Please try again.")
    else:
        form = HODRegisterForm(instance=user)

    return render(request, 'accounts/edit_user.html', {'form': form, 'user': user})



# Remove User View
@login_required
def remove_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    # Make sure only admin can delete users
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission to remove this user.")
        return redirect('accounts:admin_dashboard')

    if request.method == 'POST':
        user.delete()
        messages.success(request, "User removed successfully!")
        return redirect('accounts:admin_dashboard')

    return render(request, 'accounts/confirm_remove_user.html', {'user': user})

# View for unregistered users
def email_not_registered(request):
    return render(request, 'accounts/email_not_registered.html')




def start_task_timer(request):
    if request.method == "POST":
        task_id = request.POST.get('task_id')
        task = Task.objects.get(id=task_id)

        if task.status != 'in_progress':  # Only start if not already in progress
            task.status = 'in_progress'
            task.start_time = timezone.now()  # Set the start time
            task.save()

        # Get the current URL and redirect back to it
        project_id = request.GET.get('project')
        return redirect(f'{request.path}?project={project_id}')  # Redirect back with project query param

    return redirect('accounts:staff_dashboard')  # Fallback

def stop_task_timer(request):
    if request.method == "POST":
        task_id = request.POST.get('task_id')
        try:
            task = Task.objects.get(id=task_id)

            if task.status == 'in_progress':
                if task.start_time:  # Ensure the timer was started
                    now = timezone.now()
                    elapsed = now - task.start_time

                    # Accumulate total_time
                    if task.total_time:
                        task.total_time += elapsed
                    else:
                        task.total_time = elapsed

                    # Optional: keep total_time_seconds for aggregation
                    task.total_time_seconds += int(elapsed.total_seconds())

                    task.status = 'done'
                    task.end_time = now
                    task.start_time = None
                    task.save()

                    messages.success(request, f"Task timer stopped. Total time: {task.total_time}.")
                else:
                    messages.error(request, "Task does not have a start time.")
            else:
                messages.error(request, "Task is not in progress.")

        except Task.DoesNotExist:
            messages.error(request, "Task not found.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        project_id = request.GET.get('project')
        return redirect(f"{request.path}?project={project_id}")

    return redirect("accounts:staff_dashboard")
@login_required
def create_event(request):
    if request.user.role not in ['staff', 'hod', 'admin']:
        messages.error(request, "You do not have permission to create events.")
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if title and start_date and end_date:
            Event.objects.create(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user
            )
            messages.success(request, "Event created successfully!")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Please fill all required fields.")

    return render(request, 'accounts/create_event.html')


def all_projects(request):
    return {
        'projects': Project.objects.all()
    }

from .models import Campus, School, Department 
def create_campus(request):
    if request.method == "POST":
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:campus_crud')
    else:
        form = CampusForm()
    
    campuses = Campus.objects.all()
    return render(request, 'accounts/campus_crud.html', {'form': form, 'campuses': campuses})


# Campus CRUD
def campus_crud(request):
    # Add campus
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Campus.objects.create(name=name)
            return redirect('accounts:campus_crud')

    # GET request: show all campuses
    campuses = Campus.objects.all()
    return render(request, 'accounts/campus_crud.html', {'campuses': campuses})


# Delete campus
def delete_campus(request, campus_id):
    campus = get_object_or_404(Campus, id=campus_id)
    campus.delete()
    return redirect('accounts:campus_crud')


# Edit campus
def edit_campus(request, campus_id):
    campus = get_object_or_404(Campus, id=campus_id)

    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            campus.name = name
            campus.save()
            return redirect('accounts:campus_crud')

    return render(request, 'accounts/edit_campus.html', {'campus': campus})

# School CRUD
def school_crud(request):
    if request.method == "POST":
        name = request.POST.get("name")
        campus_id = request.POST.get("campus")
        if name and campus_id:
            campus = get_object_or_404(Campus, id=campus_id)
            School.objects.create(name=name, campus=campus)
            return redirect('accounts:school_crud')

    schools = School.objects.select_related('campus').all()
    campuses = Campus.objects.all()
    return render(request, 'accounts/school_crud.html', {'schools': schools, 'campuses': campuses})


# Delete school
def delete_school(request, school_id):
    school = get_object_or_404(School, id=school_id)
    school.delete()
    return redirect('accounts:school_crud')


# Edit school
def edit_school(request, school_id):
    school = get_object_or_404(School, id=school_id)
    campuses = Campus.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        campus_id = request.POST.get("campus")
        if name and campus_id:
            campus = get_object_or_404(Campus, id=campus_id)
            school.name = name
            school.campus = campus
            school.save()
            return redirect('accounts:school_crud')

    return render(request, 'accounts/edit_school.html', {'school': school, 'campuses': campuses})



def department_crud(request):
    campuses = Campus.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()

    # ADD Department
    if request.method == "POST" and 'add_department' in request.POST:
        campus_id = request.POST.get("campus")
        school_id = request.POST.get("school")
        department_name = request.POST.get("name")

        if campus_id and school_id and department_name:
            campus = Campus.objects.get(id=campus_id)
            school = School.objects.get(id=school_id)
            Department.objects.create(
                name=department_name,
                campus=campus,
                school=school
            )
        return redirect('accounts:department_crud')

    # EDIT Department
    if request.method == "POST" and 'edit_department' in request.POST:
        dept_id = request.POST.get("dept_id")
        department = get_object_or_404(Department, id=dept_id)
        department.name = request.POST.get("name")
        department.campus = Campus.objects.get(id=request.POST.get("campus"))
        department.school = School.objects.get(id=request.POST.get("school"))
        department.save()
        return redirect('accounts:department_crud')

    # DELETE Department
    if request.method == "POST" and 'delete_department' in request.POST:
        dept_id = request.POST.get("dept_id")
        department = get_object_or_404(Department, id=dept_id)
        department.delete()
        return redirect('accounts:department_crud')

    context = {
        'campuses': campuses,
        'schools': schools,
        'departments': departments
    }
    return render(request, 'accounts/department_crud.html', context)

def edit_department(request, id):
    department = Department.objects.get(id=id)
    campuses = Campus.objects.all()
    schools = School.objects.all()

    if request.method == 'POST':
        department.name = request.POST.get('name')
        department.campus = Campus.objects.get(id=request.POST.get('campus'))
        department.school = School.objects.get(id=request.POST.get('school'))
        department.save()
        return redirect('accounts:department_crud')  

    context = {
        'department': department,
        'campuses': campuses,
        'schools': schools
    }
    return render(request, 'accounts/edit_department.html', context)


def delete_department(request, id):
    department = get_object_or_404(Department, id=id)  # safer
    department.delete()
    return redirect('accounts:department_crud')


def create_user(request):
    # Fetch data for dropdowns and table
    campuses = Campus.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()
    users = CustomUser.objects.all().order_by('-id')  # newest first

    if request.method == 'POST':
        # Fetch form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        emp_id = request.POST.get('emp_id')
        phone_number = request.POST.get("phone_number")
        gender = request.POST.get('gender')
        campus_id = request.POST.get('campus')
        school_id = request.POST.get('school')
        department_ids = request.POST.getlist('department')  # 🔹 multiple selection
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('accounts:create_user')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('accounts:create_user')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('accounts:create_user')

        # Fetch related objects safely
        campus = Campus.objects.get(id=campus_id) if campus_id else None
        school = School.objects.get(id=school_id) if school_id else None

        # Create user
        user = CustomUser(
            username=username,
            email=email,
            emp_id=emp_id,
            phone_number=phone_number,
            gender=gender,
            campus=campus,
            school=school
        )
        user.set_password(password)
        user.save()

        # 🔹 Assign departments (ManyToMany)
        if department_ids:
            user.department.set(Department.objects.filter(id__in=department_ids))

        messages.success(request, f"User '{username}' created successfully.")
        return redirect('accounts:create_user')

    context = {
        'campuses': campuses,
        'schools': schools,
        'departments': departments,
        'users': users
    }
    return render(request, 'accounts/create_user.html', context)


def manage_user(request):
    users = CustomUser.objects.all()
    campuses = Campus.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()
    return render(request, 'accounts/manage_user.html', {
        'users': users,
        'campuses': campuses,
        'schools': schools,
        'departments': departments,
    })

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from .models import CustomUser, Campus, School, Department

@login_required
def update_user_role(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    # Only admins can update roles
    if not hasattr(request.user, "role") or request.user.role != "admin":
        return HttpResponseForbidden("You are not authorized to perform this action.")

    if request.method == "POST":
        # Get values from form
        email = request.POST.get("email")
        emp_id = request.POST.get("emp_id")
        phone_number = request.POST.get("phone_number")
        gender = request.POST.get("gender")
        role = request.POST.get("role")

        campus_id = request.POST.get("campus") or None
        school_id = request.POST.get("school") or None
        dept_ids = request.POST.getlist("department")  # multiple departments

        # Validate phone number
        if phone_number and not phone_number.isdigit():
            messages.error(request, f"Phone number must contain only digits for {user.email}.")
            return redirect("/accounts/create_user/")

        # Check for duplicates
        if email and CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already taken.")
            return redirect("/accounts/create_user/")

        if emp_id and CustomUser.objects.exclude(id=user.id).filter(emp_id=emp_id).exists():
            messages.error(request, f"Employee ID '{emp_id}' is already taken.")
            return redirect("/accounts/create_user/")

        if phone_number and CustomUser.objects.exclude(id=user.id).filter(phone_number=phone_number).exists():
            messages.error(request, f"Phone number '{phone_number}' is already taken.")
            return redirect("/accounts/create_user/")

        # Validate school belongs to campus
        if school_id and not School.objects.filter(id=school_id, campus_id=campus_id).exists():
            messages.error(request, "Invalid selection: School does not belong to the chosen Campus.")
            return redirect("/accounts/create_user/")

        # Validate departments belong to school
        if dept_ids:
            valid_dept_ids = Department.objects.filter(id__in=dept_ids, school_id=school_id).values_list('id', flat=True)
            if set(map(int, dept_ids)) != set(valid_dept_ids):
                messages.error(request, "Invalid selection: One or more Departments do not belong to the chosen School.")
                return redirect("/accounts/create_user/")

        # Update user
        if email:
            user.email = email
        if emp_id:
            user.emp_id = emp_id
        if phone_number:
            user.phone_number = phone_number
        if gender:
            user.gender = gender
        if role:
            user.role = role

        user.campus_id = campus_id
        user.school_id = school_id
        user.save()

        # Update ManyToMany Departments
        if dept_ids:
            user.department.set(dept_ids)
        else:
            user.department.clear()

        messages.success(request, f"User {user.username} updated successfully.")

    # Redirect to create_user page
    return redirect("/accounts/create_user/")




@login_required
def update_user_role_only(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    # Only admins can update roles
    if not hasattr(request.user, "role") or request.user.role != "admin":
        return HttpResponseForbidden("You are not authorized to perform this action.")

    if request.method == "POST":
        role = request.POST.get("role")
        if role in ["admin", "hod", "staff", "student"]:
            user.role = role
            user.save()
            messages.success(request, f"Role of {user.username} updated to {role}.")
        else:
            messages.error(request, "Invalid role selected.")

    # Redirect back to the Manage Roles page
    return redirect("accounts:manage_roles")  # Make sure this URL name exists

@login_required
def manage_roles(request):
    if not hasattr(request.user, "role") or request.user.role != "admin":
        return HttpResponseForbidden("You are not authorized to access this page.")

    users = CustomUser.objects.all().order_by('id')

    return render(request, 'accounts/manage_roles.html', {
        'users': users,
    })

def get_current_project(request, projects):
    project_id = request.GET.get('project')
    if project_id:
        return get_object_or_404(projects, id=project_id)
    return projects.first() if projects.exists() else None
    
@login_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return redirect('accounts:create_user')

def create_campus(request):
    if request.method == "POST":
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:campus_crud')  # redirect after creation
    else:
        form = CampusForm()
    
    context = {'form': form}
    return render(request, 'accounts/create_campus.html', context)



from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def create_school(request):
    if request.method == "POST":
        name = request.POST.get("name")
        campus_id = request.POST.get("campus")
        if name and campus_id:
            campus = Campus.objects.get(id=campus_id)
            School.objects.create(name=name, campus=campus)
        return redirect('accounts:admin_dashboard')

@csrf_exempt
def create_department(request):
    if request.method == "POST":
        name = request.POST.get("name")
        campus_id = request.POST.get("campus")
        school_id = request.POST.get("school")
        if name and campus_id and school_id:
            campus = Campus.objects.get(id=campus_id)
            school = School.objects.get(id=school_id)
            Department.objects.create(name=name, campus=campus, school=school)
        return redirect('accounts:admin_dashboard')




