from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.server_dashboard, name='server_dashboard'),
    
    # Sunucu Türü URL'leri
    path('server-types/', views.server_type_list, name='server_type_list'),
    path('server-types/create/', views.server_type_create, name='server_type_create'),
    path('server-types/<int:type_id>/update/', views.server_type_update, name='server_type_update'),
    path('server-types/<int:type_id>/delete/', views.server_type_delete, name='server_type_delete'),
    
    # Sunucu URL'leri
    path('servers/', views.server_list, name='server_list'),
    path('servers/create/', views.server_create, name='server_create'),
    path('servers/<int:server_id>/', views.server_detail, name='server_detail'),
    path('servers/<int:server_id>/update/', views.server_update, name='server_update'),
    path('servers/<int:server_id>/delete/', views.server_delete, name='server_delete'),
    
    # Sunucu Bakım Kaydı URL'leri
    path('maintenance/', views.server_maintenance_list, name='server_maintenance_list'),
    path('maintenance/create/', views.server_maintenance_create, name='server_maintenance_create'),
    path('servers/<int:server_id>/maintenance/create/', views.server_maintenance_create, name='server_maintenance_create_for_server'),
    path('maintenance/<int:maintenance_id>/update/', views.server_maintenance_update, name='server_maintenance_update'),
    path('maintenance/<int:maintenance_id>/delete/', views.server_maintenance_delete, name='server_maintenance_delete'),
    
    # Sunucu İzleme Günlüğü URL'leri
    path('monitoring-logs/', views.server_monitoring_log_list, name='server_monitoring_log_list'),
    path('monitoring-logs/create/', views.server_monitoring_log_create, name='server_monitoring_log_create'),
    path('servers/<int:server_id>/monitoring-logs/create/', views.server_monitoring_log_create, name='server_monitoring_log_create_for_server'),
    path('monitoring-logs/<int:log_id>/resolve/', views.server_monitoring_log_resolve, name='server_monitoring_log_resolve'),
    
    # Sunucu Belgesi URL'leri
    path('servers/<int:server_id>/documents/create/', views.server_document_create, name='server_document_create'),
    path('documents/<int:document_id>/delete/', views.server_document_delete, name='server_document_delete'),
]