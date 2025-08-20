from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.inventory_dashboard, name='inventory_dashboard'),
    
    # Kategori URL'leri
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # Tedarikçi URL'leri
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:supplier_id>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:supplier_id>/delete/', views.supplier_delete, name='supplier_delete'),
    
    # Envanter öğesi URL'leri
    path('items/', views.inventory_item_list, name='inventory_item_list'),
    path('items/<int:item_id>/', views.inventory_item_detail, name='inventory_item_detail'),
    path('items/create/', views.inventory_item_create, name='inventory_item_create'),
    path('items/<int:item_id>/update/', views.inventory_item_update, name='inventory_item_update'),
    path('items/<int:item_id>/delete/', views.inventory_item_delete, name='inventory_item_delete'),
    
    # Envanter hareketi URL'leri
    path('movements/create/', views.inventory_movement_create, name='inventory_movement_create'),
    path('items/<int:item_id>/movements/create/', views.inventory_movement_create, name='inventory_movement_create_for_item'),
    
    # Bakım kaydı URL'leri
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/create/', views.maintenance_create, name='maintenance_create'),
    path('items/<int:item_id>/maintenance/create/', views.maintenance_create, name='maintenance_create_for_item'),
    path('maintenance/<int:maintenance_id>/update/', views.maintenance_update, name='maintenance_update'),
]