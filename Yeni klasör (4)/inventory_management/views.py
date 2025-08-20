from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Supplier, InventoryItem, InventoryMovement, Maintenance
from .forms import (
    CategoryForm, SupplierForm, InventoryItemForm, InventoryMovementForm, 
    MaintenanceForm, InventoryItemFilterForm, MaintenanceFilterForm
)

@login_required
def inventory_dashboard(request):
    """Envanter dashboard görünümü"""
    items = InventoryItem.objects.all()
    
    # Envanter durumu istatistikleri
    status_counts = {
        'available': items.filter(status='available').count(),
        'in_use': items.filter(status='in_use').count(),
        'maintenance': items.filter(status='maintenance').count(),
        'reserved': items.filter(status='reserved').count(),
        'retired': items.filter(status='retired').count(),
    }
    
    # Son hareketler
    recent_movements = InventoryMovement.objects.all().order_by('-movement_date')[:5]
    
    # Yaklaşan bakımlar
    upcoming_maintenance = Maintenance.objects.filter(
        status__in=['scheduled', 'in_progress']
    ).order_by('scheduled_date')[:5]
    
    return render(request, 'inventory_management/dashboard.html', {
        'items': items,
        'status_counts': status_counts,
        'recent_movements': recent_movements,
        'upcoming_maintenance': upcoming_maintenance,
        'total_items': items.count(),
    })

# Kategori görünümleri
@login_required
def category_list(request):
    """Kategori listesi görünümü"""
    categories = Category.objects.all().order_by('name')
    return render(request, 'inventory_management/category_list.html', {'categories': categories})

@login_required
def category_detail(request, category_id):
    """Kategori detay görünümü"""
    category = get_object_or_404(Category, id=category_id)
    items = category.items.all()
    subcategories = category.subcategories.all()
    
    return render(request, 'inventory_management/category_detail.html', {
        'category': category,
        'items': items,
        'subcategories': subcategories
    })

@login_required
def category_create(request):
    """Kategori oluşturma görünümü"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'{category.name} kategorisi başarıyla oluşturuldu!')
            return redirect('category_detail', category_id=category.id)
    else:
        form = CategoryForm()
    
    return render(request, 'inventory_management/category_form.html', {'form': form, 'action': 'Oluştur'})

@login_required
def category_update(request, category_id):
    """Kategori güncelleme görünümü"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'{category.name} kategorisi başarıyla güncellendi!')
            return redirect('category_detail', category_id=category.id)
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'inventory_management/category_form.html', {
        'form': form, 
        'category': category, 
        'action': 'Güncelle'
    })

@login_required
def category_delete(request, category_id):
    """Kategori silme görünümü"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'{category_name} kategorisi başarıyla silindi!')
        return redirect('category_list')
    
    return render(request, 'inventory_management/category_confirm_delete.html', {'category': category})

# Tedarikçi görünümleri
@login_required
def supplier_list(request):
    """Tedarikçi listesi görünümü"""
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'inventory_management/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_detail(request, supplier_id):
    """Tedarikçi detay görünümü"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    items = supplier.supplied_items.all()
    
    return render(request, 'inventory_management/supplier_detail.html', {
        'supplier': supplier,
        'items': items
    })

@login_required
def supplier_create(request):
    """Tedarikçi oluşturma görünümü"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'{supplier.name} tedarikçisi başarıyla oluşturuldu!')
            return redirect('supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm()
    
    return render(request, 'inventory_management/supplier_form.html', {'form': form, 'action': 'Oluştur'})

@login_required
def supplier_update(request, supplier_id):
    """Tedarikçi güncelleme görünümü"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'{supplier.name} tedarikçisi başarıyla güncellendi!')
            return redirect('supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'inventory_management/supplier_form.html', {
        'form': form, 
        'supplier': supplier, 
        'action': 'Güncelle'
    })

@login_required
def supplier_delete(request, supplier_id):
    """Tedarikçi silme görünümü"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        supplier_name = supplier.name
        supplier.delete()
        messages.success(request, f'{supplier_name} tedarikçisi başarıyla silindi!')
        return redirect('supplier_list')
    
    return render(request, 'inventory_management/supplier_confirm_delete.html', {'supplier': supplier})

# Envanter öğesi görünümleri
@login_required
def inventory_item_list(request):
    """Envanter öğesi listesi görünümü"""
    filter_form = InventoryItemFilterForm(request.GET)
    items = InventoryItem.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['category']:
            items = items.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data['status']:
            items = items.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['supplier']:
            items = items.filter(supplier=filter_form.cleaned_data['supplier'])
        if filter_form.cleaned_data['search']:
            search_term = filter_form.cleaned_data['search']
            items = items.filter(
                Q(name__icontains=search_term) | 
                Q(serial_number__icontains=search_term) | 
                Q(location__icontains=search_term)
            )
    
    items = items.order_by('name')
    
    return render(request, 'inventory_management/inventory_item_list.html', {
        'items': items,
        'filter_form': filter_form
    })

@login_required
def inventory_item_detail(request, item_id):
    """Envanter öğesi detay görünümü"""
    item = get_object_or_404(InventoryItem, id=item_id)
    movements = item.movements.all().order_by('-movement_date')
    maintenance_records = item.maintenance_records.all().order_by('-scheduled_date')
    
    return render(request, 'inventory_management/inventory_item_detail.html', {
        'item': item,
        'movements': movements,
        'maintenance_records': maintenance_records
    })

@login_required
def inventory_item_create(request):
    """Envanter öğesi oluşturma görünümü"""
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            messages.success(request, f'{item.name} öğesi başarıyla oluşturuldu!')
            return redirect('inventory_item_detail', item_id=item.id)
    else:
        form = InventoryItemForm()
    
    return render(request, 'inventory_management/inventory_item_form.html', {'form': form, 'action': 'Oluştur'})

@login_required
def inventory_item_update(request, item_id):
    """Envanter öğesi güncelleme görünümü"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'{item.name} öğesi başarıyla güncellendi!')
            return redirect('inventory_item_detail', item_id=item.id)
    else:
        form = InventoryItemForm(instance=item)
    
    return render(request, 'inventory_management/inventory_item_form.html', {
        'form': form, 
        'item': item, 
        'action': 'Güncelle'
    })

@login_required
def inventory_item_delete(request, item_id):
    """Envanter öğesi silme görünümü"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'{item_name} öğesi başarıyla silindi!')
        return redirect('inventory_item_list')
    
    return render(request, 'inventory_management/inventory_item_confirm_delete.html', {'item': item})

# Envanter hareketi görünümleri
@login_required
def inventory_movement_create(request, item_id=None):
    """Envanter hareketi oluşturma görünümü"""
    item = None
    if item_id:
        item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        form = InventoryMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.save()
            
            # Öğenin durumunu güncelle
            if movement.movement_type == 'check_out':
                movement.item.status = 'in_use'
                movement.item.location = movement.to_location
            elif movement.movement_type == 'check_in':
                movement.item.status = 'available'
                movement.item.location = movement.to_location
            elif movement.movement_type == 'transfer':
                movement.item.location = movement.to_location
            
            movement.item.save()
            
            messages.success(request, 'Envanter hareketi başarıyla kaydedildi!')
            return redirect('inventory_item_detail', item_id=movement.item.id)
    else:
        initial_data = {}
        if item:
            initial_data['item'] = item
            initial_data['from_location'] = item.location
        
        form = InventoryMovementForm(initial=initial_data)
    
    return render(request, 'inventory_management/inventory_movement_form.html', {
        'form': form,
        'item': item
    })

# Bakım kaydı görünümleri
@login_required
def maintenance_list(request):
    """Bakım kaydı listesi görünümü"""
    filter_form = MaintenanceFilterForm(request.GET)
    maintenance_records = Maintenance.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['status']:
            maintenance_records = maintenance_records.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['scheduled_from']:
            maintenance_records = maintenance_records.filter(scheduled_date__gte=filter_form.cleaned_data['scheduled_from'])
        if filter_form.cleaned_data['scheduled_to']:
            maintenance_records = maintenance_records.filter(scheduled_date__lte=filter_form.cleaned_data['scheduled_to'])
    
    maintenance_records = maintenance_records.order_by('scheduled_date')
    
    return render(request, 'inventory_management/maintenance_list.html', {
        'maintenance_records': maintenance_records,
        'filter_form': filter_form
    })

@login_required
def maintenance_create(request, item_id=None):
    """Bakım kaydı oluşturma görünümü"""
    item = None
    if item_id:
        item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.created_by = request.user
            maintenance.save()
            
            # Öğenin durumunu güncelle
            if maintenance.status in ['scheduled', 'in_progress']:
                maintenance.item.status = 'maintenance'
                maintenance.item.save()
            
            messages.success(request, 'Bakım kaydı başarıyla oluşturuldu!')
            return redirect('inventory_item_detail', item_id=maintenance.item.id)
    else:
        initial_data = {}
        if item:
            initial_data['item'] = item
        
        form = MaintenanceForm(initial=initial_data)
    
    return render(request, 'inventory_management/maintenance_form.html', {
        'form': form,
        'item': item,
        'action': 'Oluştur'
    })

@login_required
def maintenance_update(request, maintenance_id):
    """Bakım kaydı güncelleme görünümü"""
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    item = maintenance.item
    
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            
            # Öğenin durumunu güncelle
            if maintenance.status == 'completed' or maintenance.status == 'cancelled':
                item.status = 'available'
            elif maintenance.status in ['scheduled', 'in_progress']:
                item.status = 'maintenance'
            
            item.save()
            
            messages.success(request, 'Bakım kaydı başarıyla güncellendi!')
            return redirect('inventory_item_detail', item_id=item.id)
    else:
        form = MaintenanceForm(instance=maintenance)
    
    return render(request, 'inventory_management/maintenance_form.html', {
        'form': form,
        'maintenance': maintenance,
        'item': item,
        'action': 'Güncelle'
    })