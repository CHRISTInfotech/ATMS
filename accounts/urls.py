from django.urls import include, path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    # Authentication & Registration
    path('', views.login_view, name='login'),
    path("logout/", views.logout_view, name="logout"),
    path('register/admin/', views.admin_register, name='admin_register'),
    path('register/hod/', views.hod_register, name='hod_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
    
    # Role-based dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('hod_dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),

    # Staff dashboard (no project_id in the path, uses query params instead)
    path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('backlog_page/', views.backlog_page, name='backlog_page'),
    path('board_page/', views.board_page, name='board_page'),
    path('timeline_page/', views.timeline_page, name='timeline_page'),

    # Task management (using query params for task_id)
    path('create_task/', views.create_task, name='create_task'),
    path('update_task_status/', views.update_task_status, name='update_task_status'),  # Without task_id in the path
    path('task/start/<str:id>', views.start_task_timer, name='start_task_timer'),  # Without task_id in the path
    path('task/stop/<str:id>', views.stop_task_timer, name='stop_task_timer'),  # Without task_id in the path

    # Project management
    path('create-project/', views.create_project, name='create_project'),
    
    # Teams
    path('teams/', views.teams_page, name='teams_page'),  # List all teams / main teams page
    path('teams/create/', views.create_team, name='create_team'),  # Create a new team
    path('edit_team/<int:team_id>/', views.edit_team, name='edit_team'), # Edit a specific team
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),  # Delete a specific team
    path('teams/<int:team_id>/users/', views.get_users_in_team, name='get_users_in_team'),  # Get users in a specific team


    path('assign_work/', views.assign_work, name='assign_work'),
    

    # Users (using query params for user_id)
    path('add_staff/', views.add_staff, name='add_staff'),
    path('add_hod/', views.add_hod, name='add_hod'),
    path('user_detail/', views.user_detail, name='user_detail'),  # Without user_id in path
    path('edit_user/', views.edit_user, name='edit_user'),  # Without user_id in path
    path('remove_user/', views.remove_user, name='remove_user'),  # Without user_id in path

    # Projects / Views with project_id (using query params)
    path('board/', views.board_page, name='board_page'),  # Accepts query param 'project_id'
    path('backlog/', views.backlog_page, name='backlog_page'),  # Accepts query param 'project_id'
    path('timeline/', views.timeline_page, name='timeline_page'),  # Accepts query param 'project_id'

    # Email / Profile
    path('email_not_registered/', views.email_not_registered, name='email_not_registered'),
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),

    # Allauth
    path('accounts/', include('allauth.urls')),

    
    path('campus/', views.campus_crud, name='campus_crud'),
    path('school/', views.school_crud, name='school_crud'),
    path('department/', views.department_crud, name='department_crud'),
    path('departments/edit/<int:id>/', views.edit_department, name='edit_department'),
    path('departments/delete/<int:id>/', views.delete_department, name='delete_department'),
    path('create_user/', views.create_user, name='create_user'),
    path('manage_user/', views.manage_user, name='manage_user'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('update_user_role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('create_campus/', views.create_campus, name='create_campus'),
    path('create_school/', views.create_school, name='create_school'),
    path('create_department/', views.create_department, name='create_department'),
    path('campus/delete/<int:campus_id>/', views.delete_campus, name='delete_campus'),
    path('campus/edit/<int:campus_id>/', views.edit_campus, name='edit_campus'),
    path('school/delete/<int:school_id>/', views.delete_school, name='delete_school'),
    path('school/edit/<int:school_id>/', views.edit_school, name='edit_school'),
    path('manage_staff/', views.manage_staff, name='manage_staff'),
    path('hod_create_staff/', views.hod_create_staff, name='hod_create_staff'), 
    path('hod/manage_staff/update/<int:staff_id>/', views.hod_update_staff, name='hod_update_staff'),
    path('hod/manage_staff/delete/<int:staff_id>/', views.hod_delete_staff, name='hod_delete_staff'),

    path('settings/', views.settings_page, name='settings_page'),

    path('manage_roles/', views.manage_roles, name='manage_roles'), 
    path("update_role/<int:user_id>/", views.update_user_role_only, name="update_user_role_only"),

    path('update-task-status/<int:task_id>/', views.update_task_status, name='update_task_status'),





    path('hod_staff/', views.hod_staff, name='hod_staff'),  # <- this line is required
    path('hod/staff/', views.hod_staff, name='hod_staff'),
    path('hod_projects/', views.hod_projects, name='hod_projects'),
    path('hod_teams/', views.hod_teams, name='hod_teams'),
    path('hod_staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('hod_staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('update_staff/<int:staff_id>/', views.update_staff, name='update_staff'),


    path('hod_add_project/', views.hod_add_project, name='hod_add_project'), 
    path("edit_project/<int:project_id>/", views.edit_project, name="edit_project"),
    path("edit_task/<int:task_id>/", views.edit_task, name="edit_task"),
    path("update_task/<int:task_id>/", views.update_task, name="update_task"),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),

    path('delete_project/<int:project_id>/', views.delete_project, name='delete_project'),
    
    path('add_subtask/', views.add_subtask, name='add_subtask'),
    path('task/<int:task_id>/add_comment/', views.add_comment, name='add_comment'),
    path('subtask/<int:pk>/edit/', views.edit_subtask, name='edit_subtask'),


    path('upload-staff-csv/', views.upload_staff_csv, name='upload_staff_csv'),
    path('download-staff-csv-template/', views.download_staff_csv_template, name='download_staff_csv_template'),
    
    path('upload_users_csv/', views.upload_users_csv, name='upload_users_csv'),
    path('download-users-csv-template/', views.download_users_csv_template, name='download_users_csv_template'),

] 
