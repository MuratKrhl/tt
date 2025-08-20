from django.urls import path
from . import views

urlpatterns = [
    # Giriş ve kimlik doğrulama URL'leri
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('password-change/', views.password_change, name='password_change'),
    
    # Kullanıcı profil URL'leri
    path('', views.user_dashboard, name='user_dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Kullanıcı yönetimi URL'leri
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/update/', views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),
    
    # Departman yönetimi URL'leri
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:department_id>/', views.department_detail, name='department_detail'),
    path('departments/<int:department_id>/update/', views.department_update, name='department_update'),
    path('departments/<int:department_id>/delete/', views.department_delete, name='department_delete'),
    
    # İzin talebi URL'leri
    path('permission-requests/', views.permission_request_list, name='permission_request_list'),
    path('permission-requests/create/', views.permission_request_create, name='permission_request_create'),
    path('permission-requests/<int:request_id>/process/', views.permission_request_process, name='permission_request_process'),
    
    # Bildirim URL'leri
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/create/', views.notification_create, name='notification_create'),
    
    # Aktivite URL'leri
    path('activities/', views.activity_list, name='activity_list'),
]