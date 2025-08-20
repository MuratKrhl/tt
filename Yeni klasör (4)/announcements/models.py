from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from ckeditor.fields import RichTextField
from simple_history.models import HistoricalRecords

User = get_user_model()

class Announcement(models.Model):
    """Duyurular, Planlı Çalışmalar ve Bilgilendirmeler için model"""
    
    # Duyuru türleri
    TYPE_CHOICES = (
        ('announcement', 'Duyuru'),
        ('planned_work', 'Planlı Çalışma'),
        ('information', 'Bilgilendirme'),
    )
    
    # Öncelik seviyeleri
    PRIORITY_CHOICES = (
        ('low', 'Düşük'),
        ('medium', 'Orta'),
        ('high', 'Yüksek'),
        ('critical', 'Kritik'),
    )
    
    # Durum seçenekleri
    STATUS_CHOICES = (
        ('draft', 'Taslak'),
        ('published', 'Yayında'),
        ('archived', 'Arşiv'),
    )
    
    title = models.CharField(max_length=255, verbose_name='Başlık')
    content = RichTextField(verbose_name='İçerik')
    announcement_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='announcement',
        verbose_name='Duyuru Türü'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name='Öncelik'
    )
    product = models.CharField(max_length=100, verbose_name='İlgili Ürün')
    start_date = models.DateTimeField(verbose_name='Yayın Başlangıç Tarihi')
    end_date = models.DateTimeField(verbose_name='Yayın Bitiş Tarihi')
    pinned = models.BooleanField(default=False, verbose_name='Sabitlenmiş')
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='Durum'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='announcements',
        verbose_name='Yazar'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')
    
    # Etiketler için ManyToMany ilişkisi
    tags = models.ManyToManyField('Tag', blank=True, related_name='announcements', verbose_name='Etiketler')
    
    # Tarihçe kaydı
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Duyuru'
        verbose_name_plural = 'Duyurular'
        ordering = ['-pinned', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('announcement_detail', kwargs={'pk': self.pk})
    
    def get_priority_color(self):
        """Öncelik seviyesine göre renk döndürür"""
        colors = {
            'low': 'secondary',  # gri
            'medium': 'info',    # mavi
            'high': 'warning',   # turuncu
            'critical': 'danger', # kırmızı
        }
        return colors.get(self.priority, 'secondary')
    
    def archive(self):
        """Duyuruyu arşivler"""
        self.status = 'archived'
        self.save()
    
    def publish(self):
        """Duyuruyu yayınlar"""
        self.status = 'published'
        self.save()


class Tag(models.Model):
    """Duyurular için etiketler"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Etiket Adı')
    
    class Meta:
        verbose_name = 'Etiket'
        verbose_name_plural = 'Etiketler'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AnnouncementFile(models.Model):
    """Duyurulara eklenebilecek dosyalar"""
    announcement = models.ForeignKey(
        Announcement, 
        on_delete=models.CASCADE, 
        related_name='files',
        verbose_name='Duyuru'
    )
    file = models.FileField(upload_to='announcements/', verbose_name='Dosya')
    file_name = models.CharField(max_length=255, verbose_name='Dosya Adı')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Yüklenme Tarihi')
    
    class Meta:
        verbose_name = 'Duyuru Dosyası'
        verbose_name_plural = 'Duyuru Dosyaları'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.file_name