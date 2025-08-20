from django import forms
from .models import Category, Supplier, InventoryItem, InventoryMovement, Maintenance

class CategoryForm(forms.ModelForm):
    """Kategori formu"""
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent']

class SupplierForm(forms.ModelForm):
    """Tedarikçi formu"""
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'website']

class InventoryItemForm(forms.ModelForm):
    """Envanter öğesi formu"""
    class Meta:
        model = InventoryItem
        fields = ['name', 'serial_number', 'category', 'supplier', 'purchase_date', 
                 'purchase_price', 'warranty_expiry', 'status', 'location', 'notes']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date'}),
        }

class InventoryMovementForm(forms.ModelForm):
    """Envanter hareketi formu"""
    class Meta:
        model = InventoryMovement
        fields = ['item', 'movement_type', 'from_location', 'to_location', 
                 'assigned_to', 'movement_date', 'expected_return_date', 'notes']
        widgets = {
            'movement_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expected_return_date': forms.DateInput(attrs={'type': 'date'}),
        }

class MaintenanceForm(forms.ModelForm):
    """Bakım kaydı formu"""
    class Meta:
        model = Maintenance
        fields = ['item', 'title', 'description', 'maintenance_type', 'scheduled_date', 
                 'actual_date', 'cost', 'status', 'performed_by', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InventoryItemFilterForm(forms.Form):
    """Envanter öğesi filtreleme formu"""
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    status = forms.ChoiceField(choices=[(None, '----')] + list(InventoryItem.STATUS_CHOICES), required=False)
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False)
    search = forms.CharField(required=False)

class MaintenanceFilterForm(forms.Form):
    """Bakım kaydı filtreleme formu"""
    status = forms.ChoiceField(choices=[(None, '----')] + list(Maintenance.STATUS_CHOICES), required=False)
    scheduled_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    scheduled_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))