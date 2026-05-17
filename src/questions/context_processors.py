from django.conf import settings
from django.urls import reverse  
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
    config = get_the_config()
    path_to_article_list = ''
    path_to_article = ''

    if config.start_newspaper_id:
        try:
            path_to_article_list = reverse('articles:all-articles',
                                           kwargs={'news_paper_id': config.start_newspaper_id})
        except Exception:
            pass

    if config.start_article_id:
        try:
            article = Article.objects.get(id=config.start_article_id)
            path_to_article = reverse('articles:detailed-article',
                                      kwargs={
                                          'news_paper_id': article.news_paper_id,
                                          'slug': article.slug
                                      })
        except Exception:
            pass

    return {
        'start_view_mode': request.session.get('start_view', config.start_view),
        'path_to_article_list': path_to_article_list,
        'path_to_article': path_to_article,
    }