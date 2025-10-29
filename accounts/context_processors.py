from .models import Project

def all_projects(request):
    """
    Makes all projects available in all templates.
    """
    projects = Project.objects.all()
    return {'projects': projects}


from .models import Team
from django.contrib.auth import get_user_model

User = get_user_model()

def global_teams_and_students(request):
    teams = Team.objects.all()
    students = User.objects.filter(role='staff')
    return {
        'teams': teams,
        'students': students
    }
