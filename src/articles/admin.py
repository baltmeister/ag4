from django.contrib import admin
from django import forms

from .models import NewsPaper, Article
from fakebook.downloads import get_csv
from django.utils.html import format_html
from analytics.models import ExperimentCondition

class NewsPaperAdminForm(forms.ModelForm):
    class Meta:
        model = NewsPaper
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamische Dropdown-Werte aus der ExperimentCondition-Tabelle
        self.fields['tag'].widget = forms.Select(
            choices=[("", "Keine Condition auswählen")]+
            [(condition.tag, condition.name) for condition in ExperimentCondition.objects.all()]
        )

@admin.register(NewsPaper)
class NewsPaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'tag')  # Zeigt ID, Name, Content-Vorschau und Tag an
    search_fields = ('name', 'content', 'tag')  # Ermöglicht die Suche nach Name, Content und Tag
    ordering = ('id',)  # Sortiert nach ID
    list_filter = ('tag',)  # Filter für den Tag hinzufügen

    form = NewsPaperAdminForm  # Verwende das benutzerdefinierte Formular
    actions = ['download_csv']
    # list_display = ['id', 'image', 'text', 'url', 'num_clicked']

    def download_csv(self, request, queryset):
        response = get_csv(self.list_display, queryset, 'newspaper.csv')
        return response

    download_csv.short_description = "Download CSV file"

class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = NewsPaper
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamische Dropdown-Werte aus der ExperimentCondition-Tabelle
        self.fields['tag'].widget = forms.Select(
            choices=[("", "Keine Condition auswählen")]+
            [(condition.tag, condition.name) for condition in ExperimentCondition.objects.all()]
        )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'tag', 'news_paper_id', 'agreement_question')  # Zeigt ID, Titel, Vorschau, Tag und zugehörige Zeitung
    search_fields = ('title', 'content', 'tag', 'news_paper_id', 'agreement_question')  # Ermöglicht Suche nach Titel, Content, Tag und zugehöriger Zeitung
    ordering = ('id',)  # Sortiert nach ID
    list_filter = ('tag', 'news_paper_id')  # Filter für Tag und Zeitung

    form = ArticleAdminForm
    actions = ['download_csv']
    # list_display = ['id', 'image', 'text', 'url', 'num_clicked']

    def download_csv(self, request, queryset):
        response = get_csv(self.list_display, queryset, 'newspaper.csv')
        return response

    download_csv.short_description = "Download CSV file"
