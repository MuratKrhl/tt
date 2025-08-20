from django.db import models
#from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Department(models.Model):
    """Departman modeli"""
    name = models.CharField(_('Departman Adı'), max_length=100)
    description = models.TextField(_('Açıklama'), blank=True)
    manager = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='managed_departments')
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Tarihi'), auto_now=True)
    
    class Meta:
        verbose_name = _('Departman')
        verbose_name_plural = _('Departmanlar')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        """Departmandaki kullanıcı sayısını döndürür"""
        return self.members.count()

class CustomUser(AbstractUser):
    """Özelleştirilmiş kullanıcı modeli"""
    # Kullanıcı türleri
    USER_TYPE_CHOICES = (
        ('admin', _('Yönetici')),
        ('manager', _('Müdür')),
        ('staff', _('Personel')),
        ('technician', _('Teknisyen')),
        ('guest', _('Misafir')),
    )
    
    # Temel bilgiler
    user_type = models.CharField(_('Kullanıcı Türü'), max_length=20, choices=USER_TYPE_CHOICES, default='staff')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='members')
    employee_id = models.CharField(_('Çalışan ID'), max_length=50, blank=True)
    phone_number = models.CharField(_('Telefon Numarası'), max_length=20, blank=True)
    profile_image = models.ImageField(_('Profil Resmi'), upload_to='profile_images/', null=True, blank=True)
    
    # İş bilgileri
    position = models.CharField(_('Pozisyon'), max_length=100, blank=True)
    hire_date = models.DateField(_('İşe Alım Tarihi'), null=True, blank=True)
    is_active_employee = models.BooleanField(_('Aktif Çalışan'), default=True)
    
    # İzin ve yetki bilgileri
    last_login_ip = models.GenericIPAddressField(_('Son Giriş IP'), null=True, blank=True)
    login_count = models.PositiveIntegerField(_('Giriş Sayısı'), default=0)
    require_password_change = models.BooleanField(_('Şifre Değişikliği Gerekli'), default=False)
    password_changed_at = models.DateTimeField(_('Şifre Değişiklik Tarihi'), null=True, blank=True)
    
    # Özel izinler
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_department_name(self):
        """Kullanıcının departman adını döndürür"""
        return self.department.name if self.department else ""
    
    def record_login(self, ip_address):
        """Kullanıcı girişini kaydeder"""
        self.last_login_ip = ip_address
        self.login_count += 1
        self.save(update_fields=['last_login_ip', 'login_count', 'last_login'])
    
    def change_password(self, password):
        """Kullanıcı şifresini değiştirir"""
        self.set_password(password)
        self.password_changed_at = timezone.now()
        self.require_password_change = False
        self.save(update_fields=['password', 'password_changed_at', 'require_password_change'])

class UserActivity(models.Model):
    """Kullanıcı aktivite kaydı modeli"""
    # Aktivite türleri
    ACTIVITY_TYPE_CHOICES = (
        ('login', _('Giriş')),
        ('logout', _('Çıkış')),
        ('password_change', _('Şifre Değişikliği')),
        ('profile_update', _('Profil Güncelleme')),
        ('permission_change', _('İzin Değişikliği')),
        ('data_access', _('Veri Erişimi')),
        ('data_modification', _('Veri Değişikliği')),
        ('other', _('Diğer')),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(_('Aktivite Türü'), max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    description = models.TextField(_('Açıklama'))
    timestamp = models.DateTimeField(_('Zaman Damgası'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP Adresi'), null=True, blank=True)
    user_agent = models.TextField(_('Kullanıcı Tarayıcısı'), blank=True)
    related_model = models.CharField(_('İlgili Model'), max_length=100, blank=True)
    related_object_id = models.PositiveIntegerField(_('İlgili Nesne ID'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Kullanıcı Aktivitesi')
        verbose_name_plural = _('Kullanıcı Aktiviteleri')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"

class UserPermissionRequest(models.Model):
    """Kullanıcı izin talebi modeli"""
    # Talep durumları
    STATUS_CHOICES = (
        ('pending', _('Beklemede')),
        ('approved', _('Onaylandı')),
        ('rejected', _('Reddedildi')),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='permission_requests')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    reason = models.TextField(_('Talep Nedeni'))
    status = models.CharField(_('Durum'), max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(_('Talep Tarihi'), auto_now_add=True)
    processed_at = models.DateTimeField(_('İşlem Tarihi'), null=True, blank=True)
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='processed_permission_requests')
    response_note = models.TextField(_('Yanıt Notu'), blank=True)
    
    class Meta:
        verbose_name = _('İzin Talebi')
        verbose_name_plural = _('İzin Talepleri')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.permission.name} - {self.get_status_display()}"
    
    def approve(self, approver, note=''):
        """İzin talebini onaylar"""
        self.status = 'approved'
        self.processed_at = timezone.now()
        self.processed_by = approver
        self.response_note = note
        self.save()
        
        # Kullanıcıya izni ekle
        self.user.user_permissions.add(self.permission)
        
        # Aktivite kaydı oluştur
        UserActivity.objects.create(
            user=self.user,
            activity_type='permission_change',
            description=f"İzin eklendi: {self.permission.name}",
            related_model='Permission',
            related_object_id=self.permission.id
        )
    
    def reject(self, rejecter, note=''):
        """İzin talebini reddeder"""
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.processed_by = rejecter
        self.response_note = note
        self.save()

class UserNotification(models.Model):
    """Kullanıcı bildirim modeli"""
    # Bildirim türleri
    NOTIFICATION_TYPE_CHOICES = (
        ('system', _('Sistem')),
        ('task', _('Görev')),
        ('alert', _('Uyarı')),
        ('info', _('Bilgi')),
    )
    
    # Bildirim öncelikleri
    PRIORITY_CHOICES = (
        ('high', _('Yüksek')),
        ('medium', _('Orta')),
        ('low', _('Düşük')),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(_('Başlık'), max_length=200)
    message = models.TextField(_('Mesaj'))
    notification_type = models.CharField(_('Bildirim Türü'), max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    priority = models.CharField(_('Öncelik'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    is_read = models.BooleanField(_('Okundu'), default=False)
    read_at = models.DateTimeField(_('Okunma Tarihi'), null=True, blank=True)
    related_url = models.CharField(_('İlgili URL'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('Bildirim')
        verbose_name_plural = _('Bildirimler')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Bildirimi okundu olarak işaretler"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
