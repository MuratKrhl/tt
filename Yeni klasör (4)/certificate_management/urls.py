from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.certificate_dashboard, name='certificate_dashboard'),
    
    # Sertifika Türü URL'leri
    path('types/', views.certificate_type_list, name='certificate_type_list'),
    path('types/create/', views.certificate_type_create, name='certificate_type_create'),
    path('types/<int:type_id>/update/', views.certificate_type_update, name='certificate_type_update'),
    path('types/<int:type_id>/delete/', views.certificate_type_delete, name='certificate_type_delete'),
    
    # Sertifika URL'leri
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificates/<int:certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificates/create/', views.certificate_create, name='certificate_create'),
    path('certificates/<int:certificate_id>/update/', views.certificate_update, name='certificate_update'),
    path('certificates/<int:certificate_id>/delete/', views.certificate_delete, name='certificate_delete'),
    
    # Sertifika Yenileme URL'leri
    path('renewals/', views.certificate_renewal_list, name='certificate_renewal_list'),
    path('renewals/create/', views.certificate_renewal_create, name='certificate_renewal_create'),
    path('certificates/<int:certificate_id>/renewals/create/', views.certificate_renewal_create, name='certificate_renewal_create_for_certificate'),
    path('renewals/<int:renewal_id>/update/', views.certificate_renewal_update, name='certificate_renewal_update'),
    
    # Sertifika Bildirimi URL'leri
    path('notifications/', views.certificate_notification_list, name='certificate_notification_list'),
    path('notifications/create/', views.certificate_notification_create, name='certificate_notification_create'),
    path('certificates/<int:certificate_id>/notifications/create/', views.certificate_notification_create, name='certificate_notification_create_for_certificate'),
    path('notifications/<int:notification_id>/acknowledge/', views.certificate_notification_acknowledge, name='certificate_notification_acknowledge'),
]