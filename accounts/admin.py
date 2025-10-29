from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from .models import CustomUser, Team

class CustomUserAdmin(UserAdmin):
    # Fields shown when viewing/editing a user in admin
    fieldsets = (
        (None, {
            "fields": (
                "username", "password", "email", "role",
                "emp_id", "department", "campus", "phone_number"
            )
        }),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Fields shown when creating a user in admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", "email", "password1", "password2", "role",
                "emp_id", "department", "campus", "phone_number"
            ),
        }),
    )

    # Use a custom method for the ManyToManyField
    list_display = ["username", "email", "role", "emp_id", "get_department", "campus", "phone_number", "is_staff"]
    search_fields = ["username", "email", "emp_id", "department__name"]
    ordering = ["username"]

    # This must be inside the CustomUserAdmin class
    def get_department(self, obj):
        return ", ".join([dept.name for dept in obj.department.all()])
    get_department.short_description = "Department"

    def save_model(self, request, obj, form, change):
        # Prevent non-superusers from creating HODs or Admins
        if obj.role in ['hod', 'admin'] and not request.user.is_superuser:
            raise PermissionDenied(f"You don't have permission to create a {obj.role.upper()}.")
        super().save_model(request, obj, form, change)

admin.site.register(CustomUser, CustomUserAdmin)


from .models import Project
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'staff')   # show name & staff in list
    search_fields = ('name', 'staff__username')  # add search support
    filter_horizontal = ('members',)   # nicer UI for selecting members

    

from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'project',
        'assigned_to',
        'assigned_by',
        'status',
        'priority',
        'due_date',
        'created_at',
    )
    
    list_filter = ('status', 'priority', 'project', 'assigned_by')
    search_fields = ('title', 'assigned_to__username', 'assigned_by__username', 'project__name')
    ordering = ('due_date', 'priority')
    date_hierarchy = 'due_date'
    
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'description',
                'project',
                'assigned_to',
                'assigned_by',
                'team',
                'parent_task',
            )
        }),
        ('Task Info', {
            'fields': ('status', 'priority', 'due_date', 'sprint')
        }),
        ('Timers', {
            'fields': ('start_time', 'end_time', 'total_time', 'total_time_seconds')
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'total_time', 'total_time_seconds')



from .models import Campus, School, Department
# ---------------- CAMPUS ----------------
@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Show campus name in admin list
    search_fields = ('name',)  # Enable search by campus name

# ---------------- SCHOOL ----------------
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'campus')  # Show school name & campus
    search_fields = ('name', 'campus__name')  # Search by school or campus name
    list_filter = ('campus',)  # Filter schools by campus

# ---------------- DEPARTMENT ----------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'campus', 'school')  # Show department, campus, school
    search_fields = ('name', 'campus__name', 'school__name')  # Search by name, campus, school
    list_filter = ('campus', 'school')  # Filter by campus & school