from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class DataSource(models.Model):
    """Nöbet listelerinin çekileceği veri kaynakları"""
    SOURCE_TYPE_CHOICES = [
        ('csv', 'CSV Dosyası'),
        ('excel', 'Excel Dosyası'),
        ('html', 'HTML Tablosu'),
        ('pdf', 'PDF Dosyası'),
    ]
    
    name = models.CharField(_('Kaynak Adı'), max_length=100)
    url = models.URLField(_('URL'), help_text=_('Veri kaynağının URL adresi'))
    source_type = models.CharField(_('Kaynak Tipi'), max_length=10, choices=SOURCE_TYPE_CHOICES)
    active = models.BooleanField(_('Aktif'), default=True)
    fetch_interval = models.IntegerField(_('Çekme Aralığı (saat)'), default=24)
    last_fetched = models.DateTimeField(_('Son Çekilme Zamanı'), null=True, blank=True)
    column_mapping = models.JSONField(_('Kolon Eşleştirme'), 
                                    help_text=_('Kaynak kolonlarının sistem kolonlarıyla eşleştirilmesi'),
                                    default=dict)
    created_at = models.DateTimeField(_('Oluşturulma Zamanı'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Zamanı'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='created_sources',
                                 verbose_name=_('Oluşturan'))
    
    class Meta:
        verbose_name = _('Veri Kaynağı')
        verbose_name_plural = _('Veri Kaynakları')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    def is_due_for_fetch(self):
        """Veri kaynağının çekilme zamanı gelip gelmediğini kontrol eder"""
        if not self.last_fetched:
            return True
        
        hours_since_last_fetch = (timezone.now() - self.last_fetched).total_seconds() / 3600
        return hours_since_last_fetch >= self.fetch_interval


class FetchLog(models.Model):
    """Veri çekme işlemlerinin logları"""
    STATUS_CHOICES = [
        ('success', _('Başarılı')),
        ('error', _('Hata')),
        ('partial', _('Kısmi Başarılı')),
    ]
    
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, 
                             related_name='fetch_logs',
                             verbose_name=_('Veri Kaynağı'))
    status = models.CharField(_('Durum'), max_length=10, choices=STATUS_CHOICES)
    started_at = models.DateTimeField(_('Başlangıç Zamanı'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Tamamlanma Zamanı'), null=True, blank=True)
    records_processed = models.IntegerField(_('İşlenen Kayıt Sayısı'), default=0)
    records_created = models.IntegerField(_('Oluşturulan Kayıt Sayısı'), default=0)
    records_updated = models.IntegerField(_('Güncellenen Kayıt Sayısı'), default=0)
    records_failed = models.IntegerField(_('Başarısız Kayıt Sayısı'), default=0)
    error_message = models.TextField(_('Hata Mesajı'), blank=True, null=True)
    raw_data = models.TextField(_('Ham Veri'), blank=True, null=True, 
                             help_text=_('Çekilen ham veri (debug için)'))
    
    class Meta:
        verbose_name = _('Çekme Logu')
        verbose_name_plural = _('Çekme Logları')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.source.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"
    
    def duration(self):
        """İşlemin süresini hesaplar"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class Department(models.Model):
    """Hastane/klinik bölümleri"""
    name = models.CharField(_('Bölüm Adı'), max_length=100)
    code = models.CharField(_('Bölüm Kodu'), max_length=20, blank=True, null=True)
    active = models.BooleanField(_('Aktif'), default=True)
    
    class Meta:
        verbose_name = _('Bölüm')
        verbose_name_plural = _('Bölümler')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Doctor(models.Model):
    """Doktor bilgileri"""
    name = models.CharField(_('Ad'), max_length=100)
    surname = models.CharField(_('Soyad'), max_length=100)
    title = models.CharField(_('Unvan'), max_length=50, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, 
                                 null=True, blank=True,
                                 related_name='doctors',
                                 verbose_name=_('Bölüm'))
    phone = models.CharField(_('Telefon'), max_length=20, blank=True, null=True)
    email = models.EmailField(_('E-posta'), blank=True, null=True)
    active = models.BooleanField(_('Aktif'), default=True)
    external_id = models.CharField(_('Harici ID'), max_length=100, blank=True, null=True,
                                help_text=_('Harici sistemdeki ID'))
    
    class Meta:
        verbose_name = _('Doktor')
        verbose_name_plural = _('Doktorlar')
        ordering = ['surname', 'name']
    
    def __str__(self):
        if self.title:
            return f"{self.title} {self.name} {self.surname}"
        return f"{self.name} {self.surname}"
    
    def get_full_name(self):
        return f"{self.name} {self.surname}"
    
    def get_masked_phone(self):
        """Telefon numarasını maskeler (gizlilik için)"""
        if not self.phone or len(self.phone) < 6:
            return self.phone
        
        visible_digits = 4
        masked_part = len(self.phone) - visible_digits
        return '*' * masked_part + self.phone[-visible_digits:]
    
    def get_masked_email(self):
        """E-posta adresini maskeler (gizlilik için)"""
        if not self.email or '@' not in self.email:
            return self.email
        
        username, domain = self.email.split('@')
        if len(username) <= 2:
            masked_username = username[0] + '*' * (len(username) - 1)
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"


class ShiftList(models.Model):
    """Nöbet listesi ana tablosu"""
    title = models.CharField(_('Başlık'), max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, 
                                 related_name='shift_lists',
                                 verbose_name=_('Bölüm'))
    start_date = models.DateField(_('Başlangıç Tarihi'))
    end_date = models.DateField(_('Bitiş Tarihi'))
    source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, 
                             null=True, blank=True,
                             related_name='shift_lists',
                             verbose_name=_('Veri Kaynağı'))
    fetch_log = models.ForeignKey(FetchLog, on_delete=models.SET_NULL, 
                                null=True, blank=True,
                                related_name='shift_lists',
                                verbose_name=_('Çekme Logu'))
    created_at = models.DateTimeField(_('Oluşturulma Zamanı'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Zamanı'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                 null=True, blank=True,
                                 related_name='created_shift_lists',
                                 verbose_name=_('Oluşturan'))
    is_published = models.BooleanField(_('Yayınlandı'), default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    class Meta:
        verbose_name = _('Nöbet Listesi')
        verbose_name_plural = _('Nöbet Listeleri')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"
    
    def get_shift_count(self):
        """Listedeki toplam nöbet sayısını döndürür"""
        return self.shifts.count()
    
    def get_doctor_count(self):
        """Listedeki toplam doktor sayısını döndürür"""
        return self.shifts.values('doctor').distinct().count()


class Shift(models.Model):
    """Nöbet detayları"""
    SHIFT_TYPE_CHOICES = [
        ('day', _('Gündüz')),
        ('night', _('Gece')),
        ('weekend', _('Hafta Sonu')),
        ('holiday', _('Resmi Tatil')),
    ]
    
    shift_list = models.ForeignKey(ShiftList, on_delete=models.CASCADE, 
                                  related_name='shifts',
                                  verbose_name=_('Nöbet Listesi'))
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, 
                             related_name='shifts',
                             verbose_name=_('Doktor'))
    date = models.DateField(_('Tarih'))
    shift_type = models.CharField(_('Nöbet Tipi'), max_length=10, choices=SHIFT_TYPE_CHOICES)
    start_time = models.TimeField(_('Başlangıç Saati'), null=True, blank=True)
    end_time = models.TimeField(_('Bitiş Saati'), null=True, blank=True)
    notes = models.TextField(_('Notlar'), blank=True, null=True)
    created_at = models.DateTimeField(_('Oluşturulma Zamanı'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Zamanı'), auto_now=True)
    
    class Meta:
        verbose_name = _('Nöbet')
        verbose_name_plural = _('Nöbetler')
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'shift_type']
    
    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.get_shift_type_display()})"


class AuditLog(models.Model):
    """Sistem işlemlerinin denetim logları"""
    ACTION_CHOICES = [
        ('create', _('Oluşturma')),
        ('update', _('Güncelleme')),
        ('delete', _('Silme')),
        ('import', _('İçe Aktarma')),
        ('export', _('Dışa Aktarma')),
        ('fetch', _('Veri Çekme')),
        ('publish', _('Yayınlama')),
        ('unpublish', _('Yayından Kaldırma')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, 
                           null=True, blank=True,
                           related_name='audit_logs',
                           verbose_name=_('Kullanıcı'))
    action = models.CharField(_('İşlem'), max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(_('Model Adı'), max_length=100)
    object_id = models.CharField(_('Nesne ID'), max_length=100)
    object_repr = models.CharField(_('Nesne Gösterimi'), max_length=200)
    changes = models.JSONField(_('Değişiklikler'), null=True, blank=True)
    timestamp = models.DateTimeField(_('Zaman'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP Adresi'), null=True, blank=True)
    user_agent = models.TextField(_('Kullanıcı Ajanı'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Denetim Logu')
        verbose_name_plural = _('Denetim Logları')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.get_action_display()} - {self.object_repr}"