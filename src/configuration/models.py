import random
import string

from django.db import models

class Configuration(models.Model):
    like_dislike_enabled = models.BooleanField(default=True)
    management_token = models.CharField(default="changeme", max_length=100)
    is_timer_enabled = models.BooleanField(default=False)
    max_session_duration = models.PositiveIntegerField(default=3600)
    is_active = models.BooleanField(default=False, help_text="Markiert die aktive Konfiguration")
    pro_contra_layout = models.BooleanField(
        default=False,
        help_text="Kommentare in Pro/Contra-Spalten anzeigen (Pro = tag 'pro', Contra = tag 'contra')"
    )


    def save(self, *args, **kwargs):
        """Stellt sicher, dass nur eine Konfiguration aktiv ist."""
        if self.is_active:
            Configuration.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def regenerate_mgmt_token(self):
        self.management_token = "".join(
            [random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(16)]
        )
        self.save()

def get_the_config() -> Configuration:
    """Liefert die aktive Konfiguration oder erstellt eine Standardkonfiguration."""
    config = Configuration.objects.filter(is_active=True).first()
    
    if config is None:
        print("Keine aktive Konfiguration gefunden! Eine neue wird erstellt...")
        config = Configuration.objects.create(
            like_dislike_enabled=True,
            is_timer_enabled=False,
            max_session_duration=1800,
            is_active=True  # Setze die neue Konfiguration als aktiv
        )
    
    if config.management_token == "changeme":
        config.regenerate_mgmt_token()

    return config

def ensure_config_exists():
    """Stellt sicher, dass eine Konfiguration existiert."""
    c = get_the_config()
    if not c:
        raise RuntimeError("Could not create configuration")
