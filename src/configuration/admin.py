from django.contrib import admin
from configuration.models import Configuration

# Entferne unnötige Allauth-Modelle aus dem Admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken

admin.site.unregister(Group)
admin.site.unregister(Site)
admin.site.unregister(EmailAddress)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        "like_dislike_enabled",
        "like_dislike_count_visible",
        "is_timer_enabled",
        "max_session_duration",
        "management_token",
        "is_active",
        "pro_contra_layout",
        "start_view",
        "start_newspaper_id",
        "start_article_id",
    ]
    fields = [
        "like_dislike_enabled",
        "like_dislike_count_visible",
        "is_timer_enabled",
        "max_session_duration",
        "management_token",
        "is_active",
        "pro_contra_layout",
        "start_view",
        "start_newspaper_id",
        "start_article_id",
    ]
    actions = ["set_as_active"]

    def set_as_active(self, request, queryset):
        """Setzt genau eine ausgewählte Konfiguration als aktiv."""
        if queryset.count() != 1:
            self.message_user(request, "Bitte wähle genau eine Konfiguration aus.", level="error")
            return
        
        # Setzt die gewählte Konfiguration als aktiv und deaktiviert alle anderen
        config = queryset.first()
        Configuration.objects.update(is_active=False)
        config.is_active = True
        config.save()
        self.message_user(request, "Die Konfiguration wurde erfolgreich als aktiv gesetzt.")

    set_as_active.short_description = "Diese Konfiguration als aktiv setzen"