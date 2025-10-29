from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    emp_id = models.CharField(max_length=20, blank=True, null=True)
    campus = models.ForeignKey('Campus', on_delete=models.SET_NULL, null=True, blank=True)
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ManyToManyField('Department', blank=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    role = models.CharField(
        max_length=10,
        choices=[('admin', 'Admin'), ('hod', 'HOD'), ('staff', 'Staff'), ('student', 'Student')],
        blank=True, null=True,
    )

    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'  # login using email
    REQUIRED_FIELDS = []        # must NOT include 'email'

    def __str__(self):
        return self.username


class StaffFile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class UploadedFile(models.Model):
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class Event(models.Model):
    """Represents an academic event or project."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_events')
    teams = models.ManyToManyField('Team', blank=True, related_name='events')

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    staff = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teams')
    members = models.ManyToManyField(CustomUser, blank=True, related_name='student_teams')
    head = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="team_head")

    def __str__(self):
        return self.name



from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='projects_created')
    created_at = models.DateTimeField(default=timezone.now)
    department = models.ManyToManyField('Department', blank=True)  # link project to a department

    def __str__(self):
        return self.name
    
class Task(models.Model):
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
        limit_choices_to={'role': 'student'},
        null=True,  # now optional to allow team assignment
        blank=True
    )
    assigned_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='created_tasks',
        limit_choices_to={'role': 'staff'}
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True
    )
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subtasks', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sprint = models.CharField(max_length=100, blank=True)

    # Timer fields
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(null=True, blank=True)  # stores timedelta
    total_time_seconds = models.PositiveIntegerField(default=0)  # optional for aggregation

    def __str__(self):
        if self.team:
            return f"{self.title} - Team: {self.team.name}"
        elif self.assigned_to:
            return f"{self.title} - {self.assigned_to.username}"
        else:
            return self.title

    # -----------------------------
    # Dashboard helper methods
    # -----------------------------
    @classmethod
    def completed_count(cls, user):
        return cls.objects.filter(assigned_by=user, status='done').count()

    @classmethod
    def updated_count(cls, user):
        week_ago = timezone.now() - timedelta(days=7)
        return cls.objects.filter(assigned_by=user, updated_at__gte=week_ago).count()

    @classmethod
    def created_count(cls, user):
        week_ago = timezone.now() - timedelta(days=7)
        return cls.objects.filter(assigned_by=user, created_at__gte=week_ago).count()

    @classmethod
    def due_soon_count(cls, user):
        week_ahead = timezone.now() + timedelta(days=7)
        return cls.objects.filter(
            assigned_by=user,
            due_date__lte=week_ahead,
            status__in=['to_do', 'in_progress']
        ).count()

    # -----------------------------
    # Timer helper methods
    # -----------------------------
    def start_timer(self):
        self.status = 'in_progress'
        self.start_time = timezone.now()
        self.save()

    def stop_timer(self):
        if self.start_time:
            elapsed = timezone.now() - self.start_time
            if self.total_time:
                self.total_time += elapsed
            else:
                self.total_time = elapsed
            self.total_time_seconds += int(elapsed.total_seconds())
        self.status = 'in_review'
        self.start_time = None
        self.save()

    def mark_reviewed(self):
        self.status = 'done'
        self.save()


class WorkLog(models.Model):
    """Tracks time spent by a student on a task."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='worklogs')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    def stop(self):
        """Call when task work is finished"""
        if not self.end_time:
            self.end_time = timezone.now()
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
            self.save()
            # Update task total_time_seconds
            self.task.total_time_seconds += self.duration_seconds
            self.task.save()

    def __str__(self):
        return f"{self.student.username} - {self.task.title}"


class SubTask(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('done', 'Done'),
    ]
    assigned_to = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            null=True,
            blank=True,
            related_name='subtasks'
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    is_completed = models.BooleanField(default=False)

    # Timer fields
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)  # cumulative seconds

    def start_timer(self):
        self.status = 'in_progress'
        self.start_time = timezone.now()
        self.save()

    def stop_timer(self):
        if self.start_time:
            elapsed = timezone.now() - self.start_time
            self.time_spent_seconds += int(elapsed.total_seconds())
            self.start_time = None
            self.status = 'in_review'
            self.save()


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)




    
class Campus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class School(models.Model):
    name = models.CharField(max_length=255)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name