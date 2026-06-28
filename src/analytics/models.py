from django.db import models
from django.contrib.auth.models import User

class UserEventLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)  # e.g., "article_click", "comment", "page_load"
    event_data = models.TextField(blank=True, null=True)  # e.g., article ID, comment text
    timestamp = models.DateTimeField() ##possible: auto_now_add=True

class NewspaperClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    newspaper_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Newspaper Click"

class ArticleClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Article Click"

class CommentPageClick(models.Model):
    CLICK_TYPE_CHOICES = [
        ('comments', 'Zu den Kommentaren'),
        ('agree', 'Stimme zu'),
        ('disagree', 'Stimme nicht zu'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_id = models.IntegerField()
    click_type = models.CharField(max_length=20, choices=CLICK_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comment Page Click"

class CommentClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_id = models.IntegerField()
    side = models.CharField(max_length=10, blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class UserContentPosition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Versuchsperson
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Typ: Article, NewsPaper, Comment
    object_id = models.PositiveIntegerField()  # ID des zugehörigen Objekts (z.B. Artikel-ID)
    content_object = GenericForeignKey('content_type', 'object_id')  # Verknüpfung zum echten Objekt
    position = models.IntegerField()  # Die zufällige Position

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')  # Eindeutige Zuordnung für jeden Benutzer und Inhalt

class ExperimentCondition(models.Model):

    name = models.CharField(max_length=100, help_text="Der Name der Bedingung (z.B. 'Kontrolle', 'Experimentell'). Maximale Länge beträgt 100 Zeichen.")
    description = models.TextField(blank=True, help_text="Eine detaillierte Beschreibung der Bedingung. Dieses Feld ist optional.")
    tag = models.CharField(max_length=50, help_text="Ein kurzer Tag zur Identifizierung der Bedingung (z.B. 'exp' für experimentell, 'control' für Kontrolle). Wird auch für die Zuordnung von Inhalten (Zeitungen, Artikel, Kommentare) verwendet.")
    def __str__(self):
        return self.name
