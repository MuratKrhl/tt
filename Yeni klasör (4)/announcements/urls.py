from django.urls import path
from . import views

urlpatterns = [
    # Dashboard ve ana görünümler
    path('', views.announcement_dashboard, name='announcement_dashboard'),
    path('list/', views.announcement_list, name='announcement_list'),
    path('<int:pk>/', views.announcement_detail, name='announcement_detail'),
    
    # Duyuru türlerine göre görünümler
    path('type/<str:announcement_type>/', views.announcement_by_type, name='announcement_by_type'),
    path('archived/', views.archived_announcements, name='archived_announcements'),
    
    # Duyuru yönetimi
    path('create/', views.announcement_create, name='announcement_create'),
    path('<int:pk>/update/', views.announcement_update, name='announcement_update'),
    path('<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('<int:pk>/archive/', views.announcement_archive, name='announcement_archive'),
    path('<int:pk>/publish/', views.announcement_publish, name='announcement_publish'),
    
    # Etiket yönetimi
    path('tag/create/', views.tag_create, name='tag_create'),
    
    # Dosya yönetimi
    path('file/<int:pk>/delete/', views.file_delete, name='file_delete'),
]