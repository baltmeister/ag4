from django.urls import path
from .views import get_newspapers, article_list, detailed_article, article_agreement

app_name ='articles'

urlpatterns = [
    path('', get_newspapers, name='news-papers'),
    path('article_list/<int:news_paper_id>/', article_list, name='all-articles'),
    path('<int:news_paper_id>/<slug:slug>/', detailed_article, name='detailed-article'),
    path('<int:news_paper_id>/<slug:slug>/agreement/', article_agreement, name='article-agreement'),
]