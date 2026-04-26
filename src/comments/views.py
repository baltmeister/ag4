from django.shortcuts import render, get_object_or_404, redirect
from django.db import models

from django.db.models import Q, Prefetch
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.contrib.contenttypes.models import ContentType
from analytics.models import UserContentPosition
import random

from .models import Comment
from .forms import CommentModelForm, SecondaryCommentModelForm
from profiles.models import Profile
from articles.models import Article, NewsPaper  # Importiere Articles und Newspapers for IDs
from configuration.models import get_the_config

from django.core.exceptions import ValidationError

from django.http import JsonResponse
import json


def save_comment(form, profile, article, parent_comment=None, is_public=False, is_secondary=False):
    """Helper-Funktion zum Speichern von Haupt- und Sekundärkommentaren und Event-Tracking."""
    try:
        # Formulardaten speichern, ohne die Instanz direkt zu committen
        instance = form.save(commit=False)
        instance.author = profile
        instance.article = article
        instance.parent_comment = parent_comment
        instance.is_public = is_public
        instance.is_secondary = is_secondary

        # Speichere den Kommentar
        instance.save()

        # Log für Debugging
        print(f"Kommentar gespeichert: ID {instance.id}, Titel: {instance.title}")
        return instance
    
    except Exception as e:
        print(f"Fehler beim Speichern des Kommentars: {str(e)}")
        raise

    
from django.contrib.contenttypes.models import ContentType
import random

@login_required
def article_comments_view(request, news_paper_id, article_id):
    user = request.user
    article = get_object_or_404(Article, id=article_id)
    profile = get_object_or_404(Profile, user=request.user)
    newspaper = get_object_or_404(NewsPaper, id=news_paper_id)
    comment_type = ContentType.objects.get_for_model(Comment)
    config = get_the_config()


    # Prüfen, ob der Nutzer eine Bedingung hat
    condition_tag = profile.condition.tag if profile.condition else None
    print(f"Condition des Nutzers: {condition_tag}")  # Debugging

    # 1. Hauptkommentare abrufen (nur IDs)
    main_comment_ids = Comment.objects.filter(
        article=article,
        parent_comment=None,
    ).filter(
        Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)  # Nur Kommentare mit passenden Tags
    ).filter(
        Q(is_public=True) | Q(author=profile)
    ).values_list('id', flat=True)

    print(f"Main comment IDs: {list(main_comment_ids)}")  # Debugging

    # 2. Prüfen, ob Hauptkommentare randomisiert wurden
    if not UserContentPosition.objects.filter(user=user, content_type=comment_type, object_id__in=main_comment_ids).exists():
        main_comments = list(Comment.objects.filter(id__in=main_comment_ids))
        random.shuffle(main_comments)

        # Reihenfolge speichern
        for index, comment in enumerate(main_comments):
            UserContentPosition.objects.create(
                user=user,
                content_type=comment_type,
                object_id=comment.id,
                position=index + 1
            )
    else:
        # Prüfen, ob neue Kommentare hinzugefügt wurden
        existing_ids = UserContentPosition.objects.filter(
            user=user, content_type=comment_type
        ).values_list('object_id', flat=True)
        new_comments = Comment.objects.filter(
            id__in=main_comment_ids
        ).exclude(id__in=existing_ids)

        if new_comments.exists():
            new_comments = list(new_comments)
            random.shuffle(new_comments)
            max_position = UserContentPosition.objects.filter(
                user=user, content_type=comment_type
            ).aggregate(max_pos=models.Max('position'))['max_pos'] or 0

            for index, comment in enumerate(new_comments, start=max_position + 1):
                UserContentPosition.objects.create(
                    user=user,
                    content_type=comment_type,
                    object_id=comment.id,
                    position=index
                )

            # Update positions for all users
            for new_comment in new_comments:
                for user_position in UserContentPosition.objects.filter(content_type=comment_type, object_id=new_comment.id):
                    user_position.position += len(new_comments)
                    user_position.save()

    # 3. Hauptkommentare in gespeicherter Reihenfolge laden
    user_positions = UserContentPosition.objects.filter(
        user=user, content_type=comment_type, object_id__in=main_comment_ids
    ).order_by('position')

    main_comments = [position.content_object for position in user_positions]

    # 4. Sekundärkommentare für jeden Hauptkommentar randomisieren und laden
    for comment in main_comments:
        # IDs der Antworten abrufen
        reply_ids = comment.replies.filter(
            Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)  # Filter für passende Tags
        ).filter(
            Q(is_public=True) | Q(author=profile)
        ).values_list('id', flat=True)

        # Antworten randomisieren, falls noch nicht geschehen
        if not UserContentPosition.objects.filter(user=user, content_type=comment_type, object_id__in=reply_ids).exists():
            replies = list(comment.replies.filter(id__in=reply_ids))
            random.shuffle(replies)

            # Reihenfolge speichern
            for index, reply in enumerate(replies):
                UserContentPosition.objects.create(
                    user=user,
                    content_type=comment_type,
                    object_id=reply.id,
                    position=index + 1
                )

        # Antworten in der gespeicherten Reihenfolge laden
        reply_positions = UserContentPosition.objects.filter(
            user=user, content_type=comment_type, object_id__in=reply_ids
        ).order_by('position')

        # Antworten zum Kommentar hinzufügen
        comment.loaded_replies = [position.content_object for position in reply_positions]

    # 5. Kommentarformulare
    comment_form = CommentModelForm()
    secondary_comment_form = SecondaryCommentModelForm()

    # Hauptkommentar hinzufügen
    if request.method == "POST" and 'submit_comment_form' in request.POST:
        comment_form = CommentModelForm(request.POST)
        if comment_form.is_valid():
            new_comment = save_comment(
                form=comment_form,
                profile=profile,
                article=article,
                is_public=request.user.is_staff,
                is_secondary=False,
            )
            if config.pro_contra_layout:
                side = request.POST.get('side', '')
                if side in ('pro', 'contra'):
                    new_comment.side = side
                    new_comment.save()

            messages.success(request, _("Dein Kommentar wurde erfolgreich hinzugefügt!"))
            return redirect('comments:article-comments',
                           news_paper_id=newspaper.id,
                           article_id=article.id)
        else:
            messages.error(request, _("Es gab einen Fehler beim Hinzufügen deines Kommentars."))
    # 6. Kontextdaten für das Template

    # Kommentare aufteilen falls Pro/Contra-Layout aktiv
    if config.pro_contra_layout:
        pro_comments = [c for c in main_comments if c.side == 'pro']
        contra_comments = [c for c in main_comments if c.side == 'contra']

        # Reihenfolge der Spalten zufällig aber stabil pro User
        layout_type = ContentType.objects.get_for_model(Comment)  # kannst du auch eigenes "Layout" Model machen

        layout_entry = UserContentPosition.objects.filter(
            user=user,
            content_type=layout_type,
            object_id=0  # spezielle ID für Layout
        ).first()

        if not layout_entry:
            #choice = random.choice(['pro_left', 'contra_left'])
            choice = 'contra_left'
            layout_entry = UserContentPosition.objects.create(
                user=user,
                content_type=layout_type,
                object_id=0,
                position=1 if choice == 'pro_left' else 2
            )
        if layout_entry.position == 1:
            order = 'pro_left'
        else:
            order = 'contra_left'

        if order == 'contra_left':
            left_comments = contra_comments
            right_comments = pro_comments
            left_label = 'Contra'
            right_label = 'Pro'
            left_side = 'contra'
            right_side = 'pro'
        else:
            left_comments = pro_comments
            right_comments = contra_comments
            left_label = 'Pro'
            right_label = 'Contra'
            left_side = 'pro'
            right_side = 'contra'
    else:
        left_comments = []
        right_comments = []
        left_label = ''
        right_label = ''
        left_side = ''
        right_side = ''
        pro_comments = []
        contra_comments = []

    context = {
        'newspaper': newspaper,
        'article': article,
        'comments': main_comments,  # Hauptkommentare in zufälliger Reihenfolge
        'comment_form': comment_form,
        'like_dislike_enabled': config.like_dislike_enabled,  # Wert an das Template übergeben
        'pro_contra_layout': config.pro_contra_layout,
        'pro_comments': pro_comments,
        'contra_comments': contra_comments,
        'left_comments': left_comments,
        'right_comments': right_comments,
        'left_label': left_label,
        'right_label': right_label,
        'left_side': left_side,
        'right_side': right_side,
    }
    return render(request, 'comments/article_comments.html', context)


from django.contrib.contenttypes.models import ContentType
import random

from django.db import models

@login_required
def detailed_comment_view(request, news_paper_id, article_id, comment_id):
    # Objekte abrufen
    comment = get_object_or_404(Comment, id=comment_id)
    article = get_object_or_404(Article, id=article_id)
    profile = Profile.objects.get(user=request.user)
    newspaper = get_object_or_404(NewsPaper, id=news_paper_id)
    comment_type = ContentType.objects.get_for_model(Comment)
    config = get_the_config()


    # Prüfen, ob der Nutzer eine Bedingung hat
    condition_tag = profile.condition.tag if profile.condition else None
    print(f"Condition des Nutzers: {condition_tag}")  # Debugging


    # Primärkommentar-Aktionen berechnen
    comment.like_action = "unlike" if profile in comment.liked.all() else "like"
    comment.dislike_action = "undislike" if profile in comment.disliked.all() else "dislike"

    # Antworten (`replies`) abrufen
    reply_ids = comment.replies.filter(
        Q(tag__isnull=True) | Q(tag="") | Q(tag=condition_tag)  # Filter für passende Tags
    ).filter(
        Q(is_public=True) | Q(author=profile)
    ).values_list('id', flat=True)

    # Prüfen, ob neue Antworten hinzugefügt wurden
    existing_reply_ids = UserContentPosition.objects.filter(
        user=request.user, content_type=comment_type, object_id__in=reply_ids
    ).values_list('object_id', flat=True)

    new_replies = Comment.objects.filter(
        id__in=reply_ids
    ).exclude(id__in=existing_reply_ids)

    # Falls es neue Antworten gibt, randomisieren und hinzufügen
    if new_replies.exists():
        new_replies = list(new_replies)
        random.shuffle(new_replies)

        # Aktuelle maximale Position finden
        max_position = UserContentPosition.objects.filter(
            user=request.user, content_type=comment_type
        ).aggregate(max_pos=models.Max('position'))['max_pos'] or 0

        for index, reply in enumerate(new_replies, start=max_position + 1):
            UserContentPosition.objects.create(
                user=request.user,
                content_type=comment_type,
                object_id=reply.id,
                position=index
            )

    # Antworten in gespeicherter Reihenfolge laden
    reply_positions = UserContentPosition.objects.filter(
        user=request.user, content_type=comment_type, object_id__in=reply_ids
    ).order_by('position')

    replies = [position.content_object for position in reply_positions]

    # Sekundärkommentar hinzufügen
    if request.method == "POST" and 'submit_secondary_comment_form' in request.POST:
        form = SecondaryCommentModelForm(request.POST)
        if form.is_valid():
            new_reply = save_comment(
                form=form,
                profile=profile,
                article=article,
                parent_comment=comment,
                is_public=request.user.is_staff,  # Antworten von Admins sind direkt öffentlich
                is_secondary=True
            )
            # Neue Antwort in die Positionen einfügen
            max_position = UserContentPosition.objects.filter(
                user=request.user, content_type=comment_type
            ).aggregate(max_pos=models.Max('position'))['max_pos'] or 0

            UserContentPosition.objects.create(
                user=request.user,
                content_type=comment_type,
                object_id=new_reply.id,
                position=max_position + 1
            )

            messages.success(request, _("Deine Antwort wurde erfolgreich hinzugefügt!"))
            return redirect('comments:detailed-comment', comment_id=comment_id, news_paper_id=newspaper.id, article_id=article.id)
        else:
            messages.error(request, _("Es gab einen Fehler beim Hinzufügen deiner Antwort."))

    # Kontext für das Template
    context = {
        'comment': comment,
        'replies': replies,  # Antworten in zufälliger, aber gespeicherter Reihenfolge
        'article': article,
        'newspaper': newspaper,
        'secondary_comment_form': SecondaryCommentModelForm(),
        'like_dislike_enabled': config.like_dislike_enabled,  # Wert an das Template übergeben

    }
    return render(request, 'comments/detailed_comment.html', context)

@login_required
def like_unlike_comment(request):
    if request.method == 'POST':
        body = json.loads(request.body)  # JSON-Body auslesen
        comment_id = body.get('comment_id')  # Abruf der comment_id
        if not comment_id:
            return JsonResponse({'success': False, 'error': 'Comment ID not provided'}, status=400)

        comment = Comment.objects.get(id=comment_id)
        profile = Profile.objects.get(user=request.user)

        action = toggle_like(profile, comment, request)

        return JsonResponse({
            "success": True,
            "action": action,  # "like" oder "unlike"
            "new_like_count": comment.liked.count(),
            "new_dislike_count": comment.disliked.count(),
            'user_has_liked': profile in comment.liked.all(),  # Benutzer hat geliked
            'user_has_disliked': profile in comment.disliked.all()  # Benutzer hat disliked
        })


@login_required
def dislike_undislike_comment(request):
    if request.method == 'POST':
        body = json.loads(request.body)  # JSON-Body auslesen
        comment_id = body.get('comment_id')  # Abruf der comment_id
        if not comment_id:
            return JsonResponse({'success': False, 'error': 'Comment ID not provided'}, status=400)
        comment = Comment.objects.get(id=comment_id)
        profile = Profile.objects.get(user=request.user)

        action = toggle_dislike(profile, comment, request)

        # JSON-Antwort für AJAX zurückgeben
        return JsonResponse({
            'success': True,
            'action': action,
            'new_like_count': comment.liked.count(),
            'new_dislike_count': comment.disliked.count(),
            'user_has_liked': profile in comment.liked.all(),  # Benutzer hat geliked
            'user_has_disliked': profile in comment.disliked.all()  # Benutzer hat disliked
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def toggle_like(profile, comment, request):

    if comment.is_secondary:
        raise ValidationError("Sekundäre Kommentare können nicht geliked werden.")


    action = "like"  # Standardaktion ist "like"
    if profile in comment.liked.all():
        # If already liked, remove like
        comment.liked.remove(profile)
        action = "unlike"  # Aktion ändern
    else:
        # Add like
        comment.liked.add(profile)
        # Remove dislike if exists
        if profile in comment.disliked.all():
            comment.disliked.remove(profile)

    # Speichern der Änderungen
    comment.save()

    # Rückgabe der Aktion an das Frontend
    return action


def toggle_dislike(profile, comment, request):
    if comment.is_secondary:
        raise ValidationError("Sekundäre Kommentare können nicht disliked werden.")


    action = "dislike"  # Standardaktion ist "dislike"
    if profile in comment.disliked.all():
        # If already disliked, remove dislike
        comment.disliked.remove(profile)
        action = "undislike"  # Aktion ändern
    else:
        # Add dislike
        comment.disliked.add(profile)
        # Remove like if exists
        if profile in comment.liked.all():
            comment.liked.remove(profile)

    # Speichern der Änderungen
    comment.save()

    # Rückgabe der Aktion an das Frontend
    return action
