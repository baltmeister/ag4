from datetime import timedelta, datetime
from django.utils.timezone import now
from django.shortcuts import redirect
from django.urls import reverse, Resolver404
from configuration.models import get_the_config
import logging

logger = logging.getLogger(__name__)

class NewspaperTimerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_paths = None  # Initialize as None

    def __call__(self, request):
        if self.excluded_paths is None:
            # Initialize excluded_paths here to ensure URL patterns are loaded
            try:
                self.excluded_paths = [
                    reverse('questions:questions_after'),
                    reverse('questions:questions_after').rstrip('/'),
                ]
                logger.debug(f"Excluded paths set to: {self.excluded_paths}")
            except Resolver404:
                # Handle the case where URL reversing fails
                self.excluded_paths = []
                logger.error("Failed to reverse 'questions:questions_after'. Excluded paths set to empty list.")

        if request.user.is_authenticated:
            # Check if the current path is excluded
            if request.path in self.excluded_paths:
                logger.debug(f"Path {request.path} is excluded from redirection.")
                return self.get_response(request)

            # Check if the request comes from a previous timer redirect
            redirected_from_timer = request.GET.get('redirected_from_timer') == 'true'
            if redirected_from_timer:
                logger.debug(f"Request redirected from timer: {request.path}")
                return self.get_response(request)

            # Load configuration from the database
            config = get_the_config()
            if not config or not config.is_timer_enabled:
                logger.debug("Timer is not enabled in the configuration.")
                return self.get_response(request)

            max_session_duration = config.max_session_duration if config.max_session_duration else 3600

            # Set entry time for '/newspapers/' path if not already set
            logger.debug(f"1")
            if 'newspaper_entry_time' not in request.session:
                should_start_timer = False
                logger.debug(f"2")
                if request.path == reverse('articles:news-papers'):
                        should_start_timer = True

                if config.start_newspaper_id:
                    if request.path == reverse('articles:all-articles',
                                            kwargs={'news_paper_id': config.start_newspaper_id}):
                        should_start_timer = True

                if config.start_article_id:
                    from articles.models import Article
                    article = Article.objects.get(id=config.start_article_id)
                    if request.path == reverse('articles:detailed-article',
                                            kwargs={
                                                'news_paper_id': article.news_paper_id,
                                                'slug': article.slug
                                            }):
                        should_start_timer = True

                if should_start_timer:
                    request.session['newspaper_entry_time'] = now().isoformat()
                    logger.debug(f"Newspaper entry time set: {request.session['newspaper_entry_time']}")

            # Check the timer and redirect if the duration exceeds the max limit
            newspaper_entry_time = request.session.get('newspaper_entry_time')
            if newspaper_entry_time:
                try:
                    newspaper_entry_time = datetime.fromisoformat(newspaper_entry_time)
                except ValueError:
                    logger.error("Invalid newspaper_entry_time format.")
                    del request.session['newspaper_entry_time']
                    return self.get_response(request)

                elapsed_time = now() - newspaper_entry_time
                logger.debug(f"Elapsed time: {elapsed_time}")

                if elapsed_time > timedelta(seconds=max_session_duration):
                    logger.debug("Timer exceeded max session duration. Redirecting to /questions/after/")
                    # Clear session entry time to prevent re-evaluation after redirect
                    del request.session['newspaper_entry_time']
                    return redirect(f"{reverse('questions:questions_after')}?redirected_from_timer=true")

        # Continue processing the request
        response = self.get_response(request)
        return response
