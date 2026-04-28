from django.conf import settings
from configuration.models import get_the_config


def global_settings(request):
    return {
        'LOGOUT_REDIRECT_URL': settings.LOGOUT_REDIRECT_URL,
    }

def session_config(request):
    config = get_the_config()
    return {
        'MAX_SESSION_DURATION': config.max_session_duration if config else 1800  # Fallback: 1 Stunde
    }

def start_view_mode(request):
    return {
        'start_view_mode': request.session.get('start_view', 'newspapers')
    }