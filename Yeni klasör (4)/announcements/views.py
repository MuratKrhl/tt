from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import Announcement, Tag, AnnouncementFile
from .forms import AnnouncementForm, AnnouncementFilterForm, TagForm, AnnouncementFileForm

@login_required
def announcement_dashboard(request):
    """Duyurular ve Planlı Çalışmalar için dashboard görünümü"""
    # Sabitlenmiş ve aktif duyurular
    pinned_announcements = Announcement.objects.filter(
        status='published',
        pinned=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at')[:5]
    
    # Son duyurular (sabitlenmemiş)
    recent_announcements = Announcement.objects.filter(
        status='published',
        pinned=False,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at')[:5]
    
    # Duyuru türlerine göre sayılar
    announcement_count = Announcement.objects.filter(announcement_type='announcement', status='published').count()
    planned_work_count = Announcement.objects.filter(announcement_type='planned_work', status='published').count()
    information_count = Announcement.objects.filter(announcement_type='information', status='published').count()
    archived_count = Announcement.objects.filter(status='archived').count()
    
    context = {
        'pinned_announcements': pinned_announcements,
        'recent_announcements': recent_announcements,
        'announcement_count': announcement_count,
        'planned_work_count': planned_work_count,
        'information_count': information_count,
        'archived_count': archived_count,
    }
    
    return render(request, 'announcements/dashboard.html', context)

@login_required
def announcement_list(request):
    """Tüm duyuruları listeler ve filtreleme sağlar"""
    filter_form = AnnouncementFilterForm(request.GET)
    announcements = Announcement.objects.all()
    
    # Filtreleme işlemleri
    if filter_form.is_valid():
        title = filter_form.cleaned_data.get('title')
        announcement_type = filter_form.cleaned_data.get('announcement_type')
        priority = filter_form.cleaned_data.get('priority')
        product = filter_form.cleaned_data.get('product')
        status = filter_form.cleaned_data.get('status')
        tags = filter_form.cleaned_data.get('tags')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if title:
            announcements = announcements.filter(title__icontains=title)
        
        if announcement_type:
            announcements = announcements.filter(announcement_type=announcement_type)
        
        if priority:
            announcements = announcements.filter(priority=priority)
        
        if product:
            announcements = announcements.filter(product__icontains=product)
        
        if status:
            announcements = announcements.filter(status=status)
        
        if tags:
            announcements = announcements.filter(tags__in=tags).distinct()
        
        if date_from:
            announcements = announcements.filter(start_date__gte=date_from)
        
        if date_to:
            announcements = announcements.filter(end_date__lte=date_to)
    
    # Varsayılan olarak sadece yayında olanları göster
    if not request.GET:
        announcements = announcements.filter(status='published')
    
    # Sıralama: Önce sabitlenmiş, sonra oluşturma tarihine göre
    announcements = announcements.order_by('-pinned', '-created_at')
    
    # Sayfalama
    paginator = Paginator(announcements, 10)  # Her sayfada 10 duyuru
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'filter_form': filter_form,
        'page_obj': page_obj,
    }
    
    return render(request, 'announcements/announcement_list.html', context)

@login_required
def announcement_detail(request, pk):
    """Duyuru detaylarını gösterir"""
    announcement = get_object_or_404(Announcement, pk=pk)
    
    # Arşivlenmiş duyurular için uyarı mesajı
    if announcement.status == 'archived':
        messages.warning(request, 'Bu duyuru arşivlenmiştir.')
    
    context = {
        'announcement': announcement,
    }
    
    return render(request, 'announcements/announcement_detail.html', context)

@login_required
@permission_required('announcements.add_announcement', raise_exception=True)
def announcement_create(request):
    """Yeni duyuru oluşturma"""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            form.save_m2m()  # ManyToMany ilişkilerini kaydet (etiketler)
            
            # Dosya yükleme işlemi
            files = request.FILES.getlist('file')
            for f in files:
                AnnouncementFile.objects.create(
                    announcement=announcement,
                    file=f,
                    file_name=f.name
                )
            
            messages.success(request, 'Duyuru başarıyla oluşturuldu.')
            
            # AJAX isteği ise JSON yanıtı döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Duyuru başarıyla oluşturuldu.',
                    'redirect_url': announcement.get_absolute_url()
                })
            
            return redirect('announcement_detail', pk=announcement.pk)
        else:
            # AJAX isteği ise form hatalarını JSON olarak döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors.as_json()
                }, status=400)
    else:
        form = AnnouncementForm()
    
    file_form = AnnouncementFileForm()
    
    context = {
        'form': form,
        'file_form': file_form,
        'is_modal': request.headers.get('x-requested-with') == 'XMLHttpRequest'
    }
    
    # AJAX isteği ise sadece form içeriğini döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'announcements/includes/announcement_form.html', context)
    
    return render(request, 'announcements/announcement_form.html', context)

@login_required
@permission_required('announcements.change_announcement', raise_exception=True)
def announcement_update(request, pk):
    """Duyuru düzenleme"""
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            
            # Dosya yükleme işlemi
            files = request.FILES.getlist('file')
            for f in files:
                AnnouncementFile.objects.create(
                    announcement=announcement,
                    file=f,
                    file_name=f.name
                )
            
            messages.success(request, 'Duyuru başarıyla güncellendi.')
            
            # AJAX isteği ise JSON yanıtı döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Duyuru başarıyla güncellendi.',
                    'redirect_url': announcement.get_absolute_url()
                })
            
            return redirect('announcement_detail', pk=announcement.pk)
        else:
            # AJAX isteği ise form hatalarını JSON olarak döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors.as_json()
                }, status=400)
    else:
        form = AnnouncementForm(instance=announcement)
    
    file_form = AnnouncementFileForm()
    
    context = {
        'form': form,
        'file_form': file_form,
        'announcement': announcement,
        'is_modal': request.headers.get('x-requested-with') == 'XMLHttpRequest'
    }
    
    # AJAX isteği ise sadece form içeriğini döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'announcements/includes/announcement_form.html', context)
    
    return render(request, 'announcements/announcement_form.html', context)

@login_required
@permission_required('announcements.delete_announcement', raise_exception=True)
@require_POST
def announcement_delete(request, pk):
    """Duyuru silme"""
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.delete()
    
    messages.success(request, 'Duyuru başarıyla silindi.')
    
    # AJAX isteği ise JSON yanıtı döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Duyuru başarıyla silindi.',
            'redirect_url': '/announcements/'
        })
    
    return redirect('announcement_list')

@login_required
@permission_required('announcements.change_announcement', raise_exception=True)
@require_POST
def announcement_archive(request, pk):
    """Duyuruyu arşivleme"""
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.archive()
    
    messages.success(request, 'Duyuru başarıyla arşivlendi.')
    
    # AJAX isteği ise JSON yanıtı döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Duyuru başarıyla arşivlendi.',
            'redirect_url': announcement.get_absolute_url()
        })
    
    return redirect('announcement_detail', pk=announcement.pk)

@login_required
@permission_required('announcements.change_announcement', raise_exception=True)
@require_POST
def announcement_publish(request, pk):
    """Duyuruyu yayınlama"""
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.publish()
    
    messages.success(request, 'Duyuru başarıyla yayınlandı.')
    
    # AJAX isteği ise JSON yanıtı döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Duyuru başarıyla yayınlandı.',
            'redirect_url': announcement.get_absolute_url()
        })
    
    return redirect('announcement_detail', pk=announcement.pk)

@login_required
def announcement_by_type(request, announcement_type):
    """Belirli türdeki duyuruları listeler"""
    filter_form = AnnouncementFilterForm(request.GET)
    
    # Tür kontrolü
    valid_types = dict(Announcement.TYPE_CHOICES).keys()
    if announcement_type not in valid_types:
        messages.error(request, 'Geçersiz duyuru türü.')
        return redirect('announcement_list')
    
    # Duyuruları filtrele
    announcements = Announcement.objects.filter(
        announcement_type=announcement_type,
        status='published'
    )
    
    # Ek filtreleme işlemleri
    if filter_form.is_valid():
        title = filter_form.cleaned_data.get('title')
        priority = filter_form.cleaned_data.get('priority')
        product = filter_form.cleaned_data.get('product')
        tags = filter_form.cleaned_data.get('tags')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if title:
            announcements = announcements.filter(title__icontains=title)
        
        if priority:
            announcements = announcements.filter(priority=priority)
        
        if product:
            announcements = announcements.filter(product__icontains=product)
        
        if tags:
            announcements = announcements.filter(tags__in=tags).distinct()
        
        if date_from:
            announcements = announcements.filter(start_date__gte=date_from)
        
        if date_to:
            announcements = announcements.filter(end_date__lte=date_to)
    
    # Sıralama: Önce sabitlenmiş, sonra oluşturma tarihine göre
    announcements = announcements.order_by('-pinned', '-created_at')
    
    # Sayfalama
    paginator = Paginator(announcements, 10)  # Her sayfada 10 duyuru
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Türe göre başlık belirleme
    type_titles = {
        'announcement': 'Duyurular',
        'planned_work': 'Planlı Çalışmalar',
        'information': 'Bilgilendirmeler',
    }
    
    context = {
        'filter_form': filter_form,
        'page_obj': page_obj,
        'announcement_type': announcement_type,
        'type_title': type_titles.get(announcement_type, 'Duyurular')
    }
    
    return render(request, 'announcements/announcement_by_type.html', context)

@login_required
def archived_announcements(request):
    """Arşivlenmiş duyuruları listeler"""
    filter_form = AnnouncementFilterForm(request.GET)
    announcements = Announcement.objects.filter(status='archived')
    
    # Filtreleme işlemleri
    if filter_form.is_valid():
        title = filter_form.cleaned_data.get('title')
        announcement_type = filter_form.cleaned_data.get('announcement_type')
        priority = filter_form.cleaned_data.get('priority')
        product = filter_form.cleaned_data.get('product')
        tags = filter_form.cleaned_data.get('tags')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if title:
            announcements = announcements.filter(title__icontains=title)
        
        if announcement_type:
            announcements = announcements.filter(announcement_type=announcement_type)
        
        if priority:
            announcements = announcements.filter(priority=priority)
        
        if product:
            announcements = announcements.filter(product__icontains=product)
        
        if tags:
            announcements = announcements.filter(tags__in=tags).distinct()
        
        if date_from:
            announcements = announcements.filter(start_date__gte=date_from)
        
        if date_to:
            announcements = announcements.filter(end_date__lte=date_to)
    
    # Sıralama: Oluşturma tarihine göre
    announcements = announcements.order_by('-created_at')
    
    # Sayfalama
    paginator = Paginator(announcements, 10)  # Her sayfada 10 duyuru
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'filter_form': filter_form,
        'page_obj': page_obj,
    }
    
    return render(request, 'announcements/archived_announcements.html', context)

@login_required
@permission_required('announcements.add_tag', raise_exception=True)
def tag_create(request):
    """Yeni etiket oluşturma"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            
            # AJAX isteği ise JSON yanıtı döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Etiket başarıyla oluşturuldu.',
                    'tag_id': tag.id,
                    'tag_name': tag.name
                })
            
            messages.success(request, 'Etiket başarıyla oluşturuldu.')
            return redirect('announcement_create')
        else:
            # AJAX isteği ise form hatalarını JSON olarak döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors.as_json()
                }, status=400)
    else:
        form = TagForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'announcements/tag_form.html', context)

@login_required
@permission_required('announcements.delete_announcementfile', raise_exception=True)
@require_POST
def file_delete(request, pk):
    """Duyuruya ait dosyayı silme"""
    file = get_object_or_404(AnnouncementFile, pk=pk)
    announcement_pk = file.announcement.pk
    file.delete()
    
    # AJAX isteği ise JSON yanıtı döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Dosya başarıyla silindi.'
        })
    
    messages.success(request, 'Dosya başarıyla silindi.')
    return redirect('announcement_update', pk=announcement_pk)