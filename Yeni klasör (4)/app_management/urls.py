from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Sunucu URL'leri
    path('servers/', views.server_list_view, name='server_list'),
    path('servers/<int:server_id>/', views.server_detail_view, name='server_detail'),
    path('servers/create/', views.server_create_view, name='server_create'),
    path('servers/<int:server_id>/update/', views.server_update_view, name='server_update'),
    path('servers/<int:server_id>/delete/', views.server_delete_view, name='server_delete'),
    
    # Uygulama URL'leri
    path('applications/', views.application_list_view, name='application_list'),
    path('applications/<int:application_id>/', views.application_detail_view, name='application_detail'),
    path('applications/create/', views.application_create_view, name='application_create'),
    path('applications/<int:application_id>/update/', views.application_update_view, name='application_update'),
    path('applications/<int:application_id>/delete/', views.application_delete_view, name='application_delete'),
    
    # Uygulama log URL'leri
    path('applications/<int:application_id>/logs/create/', views.application_log_create_view, name='application_log_create'),
    
    # Bakım kaydı URL'leri
    path('applications/<int:application_id>/maintenance/create/', views.maintenance_record_create_view, name='maintenance_create'),
    path('maintenance/<int:maintenance_id>/update/', views.maintenance_record_update_view, name='maintenance_update'),
    
    # Doküman URL'leri
    path('applications/<int:application_id>/documents/upload/', views.document_upload_view, name='document_upload'),
    path('documents/<int:document_id>/delete/', views.document_delete_view, name='document_delete'),
]