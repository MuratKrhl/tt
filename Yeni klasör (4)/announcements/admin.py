from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Announcement, Tag, AnnouncementFile

class AnnouncementFileInline(admin.TabularInline):
    model = AnnouncementFile
    extra = 1

@admin.register(Announcement)
class AnnouncementAdmin(SimpleHistoryAdmin):
    list_display = ('title', 'announcement_type', 'priority', 'product', 'status', 'pinned', 'start_date', 'end_date', 'author', 'created_at')
    list_filter = ('announcement_type', 'priority', 'status', 'pinned', 'start_date', 'end_date')
    search_fields = ('title', 'content', 'product')
    date_hierarchy = 'created_at'
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AnnouncementFileInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'content', 'announcement_type', 'priority', 'product')
        }),
        ('Yayın Bilgileri', {
            'fields': ('start_date', 'end_date', 'pinned', 'status')
        }),
        ('İlişkiler', {
            'fields': ('author', 'tags')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yeni kayıt oluşturuluyorsa
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AnnouncementFile)
class AnnouncementFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'announcement', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('file_name', 'announcement__title')
    date_hierarchy = 'uploaded_at'