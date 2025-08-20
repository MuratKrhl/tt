from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='nobet_dashboard'),
    
    # Nöbet Listeleri
    path('shift-lists/', views.shift_list_view, name='shift_list_view'),
    path('shift-lists/<int:pk>/', views.shift_list_detail, name='shift_list_detail'),
    path('shift-lists/create/', views.shift_list_create, name='shift_list_create'),
    path('shift-lists/<int:pk>/update/', views.shift_list_update, name='shift_list_update'),
    path('shift-lists/<int:pk>/delete/', views.shift_list_delete, name='shift_list_delete'),
    
    # Nöbetler
    path('shift-lists/<int:shift_list_id>/shifts/create/', views.shift_create, name='shift_create'),
    path('shift-lists/<int:shift_list_id>/shifts/bulk-create/', views.bulk_shift_create, name='bulk_shift_create'),
    path('shifts/<int:pk>/update/', views.shift_update, name='shift_update'),
    path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),
    
    # Veri Kaynakları
    path('data-sources/', views.data_source_list, name='data_source_list'),
    path('data-sources/create/', views.data_source_create, name='data_source_create'),
    path('data-sources/<int:pk>/update/', views.data_source_update, name='data_source_update'),
    path('data-sources/<int:pk>/delete/', views.data_source_delete, name='data_source_delete'),
    path('data-sources/<int:source_id>/fetch/', views.fetch_data, name='fetch_data'),
    
    # Dosya Yükleme
    path('upload/', views.file_upload, name='file_upload'),
    
    # Dışa Aktarma
    path('export/', views.export_shift_list, name='export_shift_list'),
    
    # Doktorlar
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/create/', views.doctor_create, name='doctor_create'),
    path('doctors/<int:pk>/update/', views.doctor_update, name='doctor_update'),
    path('doctors/<int:pk>/delete/', views.doctor_delete, name='doctor_delete'),
    
    # Bölümler
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/update/', views.department_update, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Loglar
    path('audit-logs/', views.audit_log_list, name='audit_log_list'),
    path('fetch-logs/', views.fetch_log_list, name='fetch_log_list'),
    path('fetch-logs/<int:pk>/', views.fetch_log_detail, name='fetch_log_detail'),
]