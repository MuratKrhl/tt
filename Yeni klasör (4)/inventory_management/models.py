from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    """Envanter kategorisi modeli"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Supplier(models.Model):
    """Tedarikçi modeli"""
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """Envanter öğesi modeli"""
    STATUS_CHOICES = [
        ('available', 'Kullanılabilir'),
        ('in_use', 'Kullanımda'),
        ('maintenance', 'Bakımda'),
        ('reserved', 'Rezerve'),
        ('retired', 'Emekli'),
    ]
    
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_items')
    purchase_date = models.DateField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.serial_number})"

class InventoryMovement(models.Model):
    """Envanter hareketi modeli"""
    MOVEMENT_TYPE_CHOICES = [
        ('check_out', 'Çıkış'),
        ('check_in', 'Giriş'),
        ('transfer', 'Transfer'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    from_location = models.CharField(max_length=100, blank=True, null=True)
    to_location = models.CharField(max_length=100, blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_items')
    movement_date = models.DateTimeField()
    expected_return_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.get_movement_type_display()} - {self.movement_date}"

class Maintenance(models.Model):
    """Bakım kaydı modeli"""
    STATUS_CHOICES = [
        ('scheduled', 'Planlandı'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='maintenance_records')
    title = models.CharField(max_length=200)
    description = models.TextField()
    maintenance_type = models.CharField(max_length=100)
    scheduled_date = models.DateField()
    actual_date = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    performed_by = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_maintenance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.title}"