from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Department, UserPermissionRequest, UserNotification

class DateInput(forms.DateInput):
    input_type = 'date'

class CustomAuthenticationForm(AuthenticationForm):
    """Özelleştirilmiş giriş formu"""
    username = forms.CharField(label=_('Kullanıcı Adı'), widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_('Şifre'), widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    error_messages = {
        'invalid_login': _(
            "Lütfen doğru kullanıcı adı ve şifre giriniz. "
            "Her iki alan da büyük/küçük harfe duyarlıdır."
        ),
        'inactive': _('Bu hesap aktif değil.'),
    }

class CustomUserCreationForm(UserCreationForm):
    """Kullanıcı oluşturma formu"""
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password1', 'password2',
            'user_type', 'department', 'employee_id', 'phone_number', 'position',
            'hire_date', 'is_active_employee', 'profile_image'
        ]
        widgets = {
            'hire_date': DateInput(),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class CustomUserChangeForm(UserChangeForm):
    """Kullanıcı güncelleme formu"""
    password = None  # Şifre alanını kaldır
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'user_type', 'department', 'employee_id', 'phone_number', 'position',
            'hire_date', 'is_active_employee', 'profile_image', 'is_active'
        ]
        widgets = {
            'hire_date': DateInput(),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """Şifre değiştirme formu"""
    old_password = forms.CharField(
        label=_('Mevcut Şifre'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label=_('Yeni Şifre'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_('Şifreniz en az 8 karakter olmalı ve rakam içermelidir.'),
    )
    new_password2 = forms.CharField(
        label=_('Yeni Şifre (Tekrar)'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

class ProfileUpdateForm(forms.ModelForm):
    """Kullanıcı profil güncelleme formu"""
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'profile_image']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class DepartmentForm(forms.ModelForm):
    """Departman formu"""
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
        }

class UserPermissionRequestForm(forms.ModelForm):
    """Kullanıcı izin talebi formu"""
    class Meta:
        model = UserPermissionRequest
        fields = ['permission', 'reason']
        widgets = {
            'permission': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UserPermissionRequestProcessForm(forms.ModelForm):
    """İzin talebi işleme formu"""
    class Meta:
        model = UserPermissionRequest
        fields = ['response_note']
        widgets = {
            'response_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UserNotificationForm(forms.ModelForm):
    """Kullanıcı bildirim formu"""
    class Meta:
        model = UserNotification
        fields = ['user', 'title', 'message', 'notification_type', 'priority', 'related_url']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'related_url': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserFilterForm(forms.Form):
    """Kullanıcı filtreleme formu"""
    username = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    user_type = forms.ChoiceField(
        required=False,
        choices=[(None, '----')] + list(CustomUser.USER_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        required=False,
        queryset=Department.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[(None, '----'), (True, 'Aktif'), (False, 'Pasif')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active_employee = forms.ChoiceField(
        required=False,
        choices=[(None, '----'), (True, 'Aktif Çalışan'), (False, 'Pasif Çalışan')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class DepartmentFilterForm(forms.Form):
    """Departman filtreleme formu"""
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    manager = forms.ModelChoiceField(
        required=False,
        queryset=CustomUser.objects.filter(user_type__in=['admin', 'manager']),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class UserPermissionRequestFilterForm(forms.Form):
    """İzin talebi filtreleme formu"""
    user = forms.ModelChoiceField(
        required=False,
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[(None, '----')] + list(UserPermissionRequest.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    requested_from = forms.DateField(
        required=False,
        widget=DateInput(attrs={'class': 'form-control'})
    )
    requested_to = forms.DateField(
        required=False,
        widget=DateInput(attrs={'class': 'form-control'})
    )