from django.conf import settings


def project_name(request):
    """
    Adds the project name to the template context.
    """
    return {
        "PROJECT_NAME": settings.PROJECT_NAME,
        "LOGGED_IN_REDIRECT": settings.LOGGED_IN_REDIRECT,
    }
