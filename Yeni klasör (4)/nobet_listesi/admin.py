from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from .models import DataSource, ShiftList, Department, Doctor, Shift, FetchLog, AuditLog


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0
    fields = ('doctor', 'date', 'shift_type', 'start_time', 'end_time', 'notes')
    autocomplete_fields = ['doctor']


@admin.register(ShiftList)
class ShiftListAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'start_date', 'end_date', 'is_published', 
                   'created_at', 'shift_count', 'view_link')
    list_filter = ('department', 'is_published', 'created_at')
    search_fields = ('title',)
    date_hierarchy = 'created_at'
    inlines = [ShiftInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'source_type', 'source_url', 'source_file')
    fieldsets = (
        (None, {
            'fields': ('title', 'department', 'start_date', 'end_date', 'is_published')
        }),
        (_('Kaynak Bilgileri'), {
            'fields': ('source_type', 'source_url', 'source_file'),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('shifts', 'department')
    
    def shift_count(self, obj):
        return obj.shifts.count()
    shift_count.short_description = _('Nöbet Sayısı')
    
    def view_link(self, obj):
        url = reverse('shift_list_detail', args=[obj.id])
        return format_html('<a href="{}" target="_blank">{}</a>', url, _('Görüntüle'))
    view_link.short_description = _('Bağlantı')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yeni kayıt oluşturuluyorsa
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'title', 'department', 'phone', 'email', 'active')
    list_filter = ('department', 'active', 'title')
    search_fields = ('name', 'surname', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at', 'external_id')
    fieldsets = (
        (None, {
            'fields': ('name', 'surname', 'title', 'department', 'phone', 'email', 'active')
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('external_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return str(obj)
    full_name.short_description = _('Ad Soyad')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'active', 'doctor_count')
    list_filter = ('active',)
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('doctors')
    
    def doctor_count(self, obj):
        return obj.doctors.count()
    doctor_count.short_description = _('Doktor Sayısı')


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'department', 'active', 'fetch_interval', 
                   'last_fetch', 'fetch_button')
    list_filter = ('source_type', 'department', 'active')
    search_fields = ('name', 'url')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'last_fetch')
    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'source_type', 'department', 'active', 'fetch_interval')
        }),
        (_('Kolon Eşleştirme'), {
            'fields': ('column_mapping',),
            'description': _('JSON formatında kolon eşleştirme bilgileri. Örnek: {"doctor_name": ["Doktor", "Hekim"], "date": ["Tarih", "Nöbet Tarihi"]}')
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_fetch'),
            'classes': ('collapse',)
        }),
    )
    
    def fetch_button(self, obj):
        url = reverse('fetch_data', args=[obj.id])
        return format_html('<a href="{}" class="button">{}</a>', url, _('Veri Çek'))
    fetch_button.short_description = _('İşlem')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yeni kayıt oluşturuluyorsa
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'shift_list', 'date', 'shift_type', 'start_time', 'end_time')
    list_filter = ('shift_type', 'date', 'shift_list__department')
    search_fields = ('doctor__name', 'doctor__surname', 'notes')
    autocomplete_fields = ['doctor', 'shift_list']
    date_hierarchy = 'date'


@admin.register(FetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    list_display = ('source', 'status', 'started_at', 'completed_at', 'duration', 'initiated_by')
    list_filter = ('status', 'started_at', 'source')
    search_fields = ('error_message',)
    readonly_fields = ('source', 'status', 'started_at', 'completed_at', 'duration', 
                      'initiated_by', 'error_message', 'details')
    fieldsets = (
        (None, {
            'fields': ('source', 'status', 'started_at', 'completed_at', 'initiated_by')
        }),
        (_('Hata Bilgileri'), {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        (_('Detaylar'), {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return f"{duration.total_seconds():.2f} sn"
        return "-"
    duration.short_description = _('Süre')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp', 'user')
    search_fields = ('object_repr', 'details', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id', 
                      'object_repr', 'changes', 'details', 'ip_address', 'user_agent')
    fieldsets = (
        (None, {
            'fields': ('timestamp', 'user', 'action', 'model_name', 'object_id', 'object_repr')
        }),
        (_('Değişiklikler'), {
            'fields': ('changes',),
            'classes': ('collapse',)
        }),
        (_('Detaylar'), {
            'fields': ('details', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False