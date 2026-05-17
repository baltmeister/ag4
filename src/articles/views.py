from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import reverse, get_object_or_404
from .models import Article, NewsPaper
from profiles.models import Profile
from django.db.models import Q

from analytics.models import UserContentPosition

from django.contrib.contenttypes.models import ContentType
import random

# Create your views here.

### Get the newspapers
import random
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .models import NewsPaper
from analytics.models import UserContentPosition

@login_required
def get_newspapers(request):
    user = request.user
    profile = user.profile
    newspaper_type = ContentType.objects.get_for_model(NewsPaper)
    condition_tag = profile.condition.tag if profile.condition else None

    if not condition_tag:
        return render(request, 'articles/news_papers.html', {'news_papers': []})

    # Filterung mit derselben Logik wie beim Positions-Check
    newspapers = NewsPaper.objects.filter(
        Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)
    )

    # Existierende Positionen
    existing_positions = UserContentPosition.objects.filter(
        user=user,
        content_type=newspaper_type,
        object_id__in=newspapers.values_list('id', flat=True)
    )

    if not existing_positions.exists():
        # Alte Einträge löschen
        UserContentPosition.objects.filter(
            user=user,
            content_type=newspaper_type
        ).delete()

        # Neue Randomisierung
        newspapers_list = list(newspapers)
        random.shuffle(newspapers_list)

        # Positionen mit get_or_create anlegen
        for index, newspaper in enumerate(newspapers_list, start=1):
            UserContentPosition.objects.get_or_create(
                user=user,
                content_type=newspaper_type,
                object_id=newspaper.id,
                defaults={'position': index}
            )

    # Lade die gespeicherte Reihenfolge
    newspaper_positions = UserContentPosition.objects.filter(
        user=user,
        content_type=newspaper_type
    ).order_by('position')
    
    news_papers = [pos.content_object for pos in newspaper_positions]
    return render(request, 'articles/news_papers.html', {'news_papers': news_papers})
## Article definitions
@login_required
def article_list(request, news_paper_id):
    user = request.user
    profile = user.profile
    article_type = ContentType.objects.get_for_model(Article)
    newspaper = get_object_or_404(NewsPaper, id=news_paper_id)

    # Bedingung des Nutzers
    condition_tag = profile.condition.tag if profile.condition else None

    # Filter für Artikel mit derselben Logik wie beim Positions-Check
    articles = Article.objects.filter(
        news_paper_id=news_paper_id
    ).filter(
        Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)
    )

    # Existierende Positionen für diese Artikel
    existing_positions = UserContentPosition.objects.filter(
        user=user,
        content_type=article_type,
        object_id__in=articles.values_list('id', flat=True)
    )

    # Nur neu generieren wenn keine Positionen existieren
    if not existing_positions.exists():
        # Alte Positionen löschen falls vorhanden
        UserContentPosition.objects.filter(
            user=user,
            content_type=article_type
        ).delete()

        # Neue zufällige Reihenfolge erstellen
        articles_list = list(articles)
        random.shuffle(articles_list)

        # Positionen mit get_or_create anlegen
        for index, article in enumerate(articles_list, start=1):
            UserContentPosition.objects.get_or_create(
                user=user,
                content_type=article_type,
                object_id=article.id,
                defaults={'position': index}
            )

    # Artikel in der gespeicherten Reihenfolge laden
    article_positions = UserContentPosition.objects.filter(
        user=user,
        content_type=article_type
    ).order_by('position')
    
    articles = [pos.content_object for pos in article_positions]

    context = {'articles': articles, 'newspaper': newspaper}
    return render(request, 'articles/all_articles.html', context)


#track article interactions

@login_required
def detailed_article(request, news_paper_id, slug):

    # Hole die Zeitung und prüfe, ob sie existiert
    newspaper = get_object_or_404(NewsPaper, id=news_paper_id)
    # Abrufen des spezifischen Artikels anhand des Slugs
    article = get_object_or_404(Article, slug=slug, news_paper_id=news_paper_id)
    profile = Profile.objects.get(user=request.user)

    condition_tag = profile.condition.tag if profile.condition else None
    print(f"Condition des Nutzers: {condition_tag}")  # Debugging



    # load Configuration
    from configuration.models import get_the_config
    config = get_the_config()

    if config.pro_contra_layout:
        # In Pro/Contra-Layout nur Kommentare mit 'pro' oder 'contra' zählen
        public_comments_count = article.comments.filter(
            Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)
        ).filter(
            side__in=['pro', 'contra']
        ).filter(
            Q(is_public=True) | Q(author=profile)
        ).filter(
            Q(parent_comment=None)
        ).values_list('id', flat=True).count()
    else:
        public_comments_count = article.comments.filter(
            Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)  # Filter für passende Tags
        ).filter(
            Q(is_public=True) | Q(author=profile)
        ).filter(
            Q(parent_comment=None)
        ).values_list('id', flat=True).count()

    #
    if config.pro_contra_layout:
        session_key = f'agreement_order_{article.id}'
        if session_key not in request.session:
            import random
            request.session[session_key] = random.choice(['agree_left', 'disagree_left'])

        if request.session[session_key] == 'agree_left':
            left_button = ('agree', 'Stimme zu und weiter zu den Kommentaren', 'green')
            right_button = ('disagree', 'Stimme nicht zu und weiter zu den Kommentaren', 'red')
        else:
            left_button = ('disagree', 'Stimme nicht zu und weiter zu den Kommentaren', 'red')
            right_button = ('agree', 'Stimme zu und weiter zu den Kommentaren', 'green')
    else:
        left_button = None
        right_button = None

    context = {
        'article': article, 
        'newspaper': newspaper,
        'public_comments_count': public_comments_count,
        'left_button': left_button,
        'right_button': right_button,
        'pro_contra_layout': config.pro_contra_layout,
    }
    return render(request, 'articles/detailed_article.html', context)

#track newspaper interactions
# @login_required
# def click_newspaper(request, pk):
#     user = request.user
#     ad_obj = get_newspapers.objects.get(id=pk)
#     profile = Profile.objects.get(user=user)

#     if profile not in ad_obj.user_clicked.all():
#         ad_obj.user_clicked.add(profile)

#     ad_obj.num_clicked += 1
#     ad_obj.save()

#     return redirect(ad_obj.url)

