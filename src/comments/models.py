from django.db import models
from django.urls import reverse

from profiles.models import Profile
from articles.models import Article

from django.core.exceptions import ValidationError


class Comment(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="comments", help_text="Autor/in des Kommentars")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments", help_text="Zuordnung zu Artikel")  # Beziehung zum Artikel
    title = models.CharField(max_length=255, default="Default Title")
    content = models.TextField(default="Default Content")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    tag = models.CharField(max_length=50, default='', blank=True,  help_text="Optionale Zuordnung zu Versuchsbedingung")  #optional Tag für die Versuchsbedingung
    is_secondary = models.BooleanField(default=False, help_text="Gibt an, ob der Kommentar ein Sekundärkommentar ist")  # Gibt an, ob der Kommentar ein Sekundärkommentar ist
    parent_comment = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name="replies", help_text="<strong>Wichtig!</strong> Muss ein Hauptkommentar sein, der zum oben ausgewählten Artikel zugeordnet ist"
    )
    is_public = models.BooleanField(default=True,  help_text="Muss öffentlich sein, um der Versuchsperson angezeigt zu werden.") # Gibt an, ob der Kommentar öffentlich ist
    liked = models.ManyToManyField(Profile, related_name="liked_comments_set", blank=True, help_text="Nur möglich für Primärkommentare.")
    disliked = models.ManyToManyField(Profile, related_name="disliked_comments_set", blank=True, help_text="Nur möglich für Primärkommentare.")
    SIDE_CHOICES = [('pro', 'Pro'), ('contra', 'Contra')]
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, blank=True) #Gibt an, ob der Kommentar Pro oder gegen den Artikel ist (optional)
    def __str__(self):
        # Kürze den Inhalt auf maximal 50 Zeichen
        content_preview = self.content[:50] + ("..." if len(self.content) > 50 else "")
        if not self.parent_comment:
            return f"Article: {self.article.title} - Main Comment: {self.title} by {self.author} - {content_preview}"
        else:
            return f" Reply: {self.title} by {self.author} - {content_preview}"

    class Meta:
        ordering = ['-created']
    
    def get_absolute_url(self):
        return reverse(
            "comments:detailed-comment", 
            kwargs={
                "news_paper_id": self.article.news_paper_id,
                "article_id": self.article.id,
                "comment_id": self.id
            }
        )
    def clean(self):
        # Sekundärer Kommentar benötigt einen Parent-Kommentar
        if self.is_secondary and not self.parent_comment:
            raise ValidationError("Ein sekundärer Kommentar muss einen übergeordneten Kommentar haben.")

        # Hauptkommentar darf keinen Parent-Kommentar haben
        if not self.is_secondary and self.parent_comment:
            raise ValidationError("Ein Hauptkommentar darf keinen übergeordneten Kommentar haben.")
        
        if self.parent_comment and self.parent_comment.is_secondary:
            raise ValidationError("Ein Sekundär-Kommentar darf nicht als Parent-Kommentar ausgewählt werden.")

        super().clean()
