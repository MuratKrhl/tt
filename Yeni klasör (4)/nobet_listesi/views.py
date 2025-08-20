from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import DataSource, ShiftList, Department, Doctor, Shift, FetchLog, AuditLog
from .forms import (
    DataSourceForm, FileUploadForm, ShiftListFilterForm, 
    ShiftForm, DoctorForm, DepartmentForm, ExportForm
)

import pandas as pd
import json
import csv
import io
import datetime
import uuid

# Celery tasks
from .tasks import fetch_data_from_source, process_uploaded_file


@login_required
def dashboard(request):
    """Ana dashboard görünümü"""
    # Son eklenen nöbet listeleri
    recent_shift_lists = ShiftList.objects.filter(is_published=True).order_by('-created_at')[:5]
    
    # Bölümlere göre nöbet sayıları
    departments = Department.objects.filter(active=True)
    department_stats = []
    for dept in departments:
        shift_count = Shift.objects.filter(shift_list__department=dept).count()
        department_stats.append({
            'department': dept,
            'shift_count': shift_count
        })
    
    # Son veri çekme işlemleri
    recent_fetch_logs = FetchLog.objects.order_by('-started_at')[:5]
    
    # Aktif veri kaynakları
    active_sources = DataSource.objects.filter(active=True).count()
    
    # Toplam nöbet sayısı
    total_shifts = Shift.objects.count()
    
    # Toplam doktor sayısı
    total_doctors = Doctor.objects.filter(active=True).count()
    
    context = {
        'recent_shift_lists': recent_shift_lists,
        'department_stats': department_stats,
        'recent_fetch_logs': recent_fetch_logs,
        'active_sources': active_sources,
        'total_shifts': total_shifts,
        'total_doctors': total_doctors,
    }
    
    return render(request, 'nobet_listesi/dashboard.html', context)


@login_required
def shift_list_view(request):
    """Nöbet listelerini görüntüleme ve filtreleme"""
    filter_form = ShiftListFilterForm(request.GET)
    shift_lists = ShiftList.objects.all()
    
    # Filtreleme işlemleri
    if filter_form.is_valid():
        department = filter_form.cleaned_data.get('department')
        date_range = filter_form.cleaned_data.get('date_range')
        doctor = filter_form.cleaned_data.get('doctor')
        is_published = filter_form.cleaned_data.get('is_published')
        
        if department:
            shift_lists = shift_lists.filter(department=department)
        
        if date_range:
            start_date, end_date = date_range
            shift_lists = shift_lists.filter(
                Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
            )
        
        if doctor:
            # Belirli bir doktorun nöbetlerinin bulunduğu listeler
            shift_lists = shift_lists.filter(shifts__doctor=doctor).distinct()
        
        if is_published:
            if is_published == 'true':
                shift_lists = shift_lists.filter(is_published=True)
            elif is_published == 'false':
                shift_lists = shift_lists.filter(is_published=False)
    
    # Sıralama
    shift_lists = shift_lists.order_by('-start_date')
    
    # Sayfalama
    paginator = Paginator(shift_lists, 10)  # Her sayfada 10 liste
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'filter_form': filter_form,
        'page_obj': page_obj,
    }
    
    return render(request, 'nobet_listesi/shift_list.html', context)


@login_required
def shift_list_detail(request, pk):
    """Nöbet listesi detayı"""
    shift_list = get_object_or_404(ShiftList, pk=pk)
    shifts = shift_list.shifts.all().order_by('date', 'start_time')
    
    # Doktorlara göre gruplandırma
    doctors = {}
    for shift in shifts:
        if shift.doctor_id not in doctors:
            doctors[shift.doctor_id] = {
                'doctor': shift.doctor,
                'shifts': []
            }
        doctors[shift.doctor_id]['shifts'].append(shift)
    
    context = {
        'shift_list': shift_list,
        'doctors': doctors.values(),
        'shifts': shifts,
    }
    
    return render(request, 'nobet_listesi/shift_list_detail.html', context)


@login_required
@permission_required('nobet_listesi.add_shiftlist', raise_exception=True)
def shift_list_create(request):
    """Yeni nöbet listesi oluşturma"""
    if request.method == 'POST':
        form = ShiftListForm(request.POST)
        if form.is_valid():
            shift_list = form.save(commit=False)
            shift_list.created_by = request.user
            shift_list.save()
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='ShiftList',
                object_id=shift_list.id,
                object_repr=str(shift_list),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Nöbet listesi başarıyla oluşturuldu.'))
            return redirect('shift_list_detail', pk=shift_list.pk)
    else:
        form = ShiftListForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'nobet_listesi/shift_list_form.html', context)


@login_required
@permission_required('nobet_listesi.change_shiftlist', raise_exception=True)
def shift_list_update(request, pk):
    """Nöbet listesi güncelleme"""
    shift_list = get_object_or_404(ShiftList, pk=pk)
    
    if request.method == 'POST':
        form = ShiftListForm(request.POST, instance=shift_list)
        if form.is_valid():
            form.save()
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='ShiftList',
                object_id=shift_list.id,
                object_repr=str(shift_list),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Nöbet listesi başarıyla güncellendi.'))
            return redirect('shift_list_detail', pk=shift_list.pk)
    else:
        form = ShiftListForm(instance=shift_list)
    
    context = {
        'form': form,
        'shift_list': shift_list,
    }
    
    return render(request, 'nobet_listesi/shift_list_form.html', context)
@login_required
@permission_required('nobet_listesi.add_shift', raise_exception=True)
def bulk_shift_create(request, shift_list_id):
    """Toplu nöbet kaydı oluşturma"""
    shift_list = get_object_or_404(ShiftList, pk=shift_list_id)
    
    if request.method == 'POST':
        form = BulkShiftForm(request.POST, shift_list=shift_list)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            date_range = form.cleaned_data['date_range']
            days_of_week = form.cleaned_data.get('days_of_week', [])
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            notes = form.cleaned_data.get('notes', '')
            
            # Tarih aralığını parse et
            start_date, end_date = date_range.split(' - ')
            start_date = datetime.datetime.strptime(start_date, '%d.%m.%Y').date()
            end_date = datetime.datetime.strptime(end_date, '%d.%m.%Y').date()
            
            # Seçilen günleri integer listesine çevir
            selected_days = [int(day) for day in days_of_week]
            
            # Tarih aralığındaki her gün için
            current_date = start_date
            created_shifts = 0
            
            while current_date <= end_date:
                # Eğer gün seçilmişse veya hiç gün seçilmemişse (tüm günler)
                if not selected_days or current_date.weekday() in selected_days:
                    # Aynı doktor, tarih ve saatte çakışan nöbet var mı kontrol et
                    existing_shift = Shift.objects.filter(
                        doctor=doctor,
                        date=current_date,
                        start_time__lt=end_time,
                        end_time__gt=start_time
                    ).exists()
                    
                    if not existing_shift:
                        # Nöbet oluştur
                        shift = Shift.objects.create(
                            shift_list=shift_list,
                            doctor=doctor,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            notes=notes,
                            created_by=request.user
                        )
                        created_shifts += 1
                
                current_date += datetime.timedelta(days=1)
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='bulk_create',
                model_name='Shift',
                object_id=shift_list.id,
                object_repr=f"{created_shifts} nöbet kaydı - {shift_list}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('{} nöbet kaydı başarıyla oluşturuldu.').format(created_shifts))
            return redirect('shift_list_detail', pk=shift_list.id)
    else:
        form = BulkShiftForm(shift_list=shift_list)
    
    context = {
        'form': form,
        'shift_list': shift_list,
    }
    
    return render(request, 'nobet_listesi/bulk_shift_form.html', context)
        end_date = request.POST.get('end_date')
        is_published = request.POST.get('is_published') == 'on'
        
        try:
            department = Department.objects.get(id=department_id)
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Değişiklikleri kaydet
            old_data = {
                'title': shift_list.title,
                'department': shift_list.department.id,
                'start_date': shift_list.start_date.isoformat(),
                'end_date': shift_list.end_date.isoformat(),
                'is_published': shift_list.is_published
            }
            
            shift_list.title = title
            shift_list.department = department
            shift_list.start_date = start_date
            shift_list.end_date = end_date
            shift_list.is_published = is_published
            shift_list.save()
            
            # Denetim logu
            new_data = {
                'title': shift_list.title,
                'department': shift_list.department.id,
                'start_date': shift_list.start_date.isoformat(),
                'end_date': shift_list.end_date.isoformat(),
                'is_published': shift_list.is_published
            }
            
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='ShiftList',
                object_id=shift_list.id,
                object_repr=str(shift_list),
                changes={'old': old_data, 'new': new_data},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Nöbet listesi başarıyla güncellendi.'))
            return redirect('shift_list_detail', pk=shift_list.pk)
        
        except (Department.DoesNotExist, ValueError) as e:
            messages.error(request, _('Nöbet listesi güncellenirken hata oluştu: {}').format(str(e)))
    
    # GET isteği veya form hatası durumunda
    departments = Department.objects.filter(active=True)
    context = {
        'shift_list': shift_list,
        'departments': departments,
    }
    
    return render(request, 'nobet_listesi/shift_list_form.html', context)


@login_required
@permission_required('nobet_listesi.delete_shiftlist', raise_exception=True)
@require_POST
def shift_list_delete(request, pk):
    """Nöbet listesi silme"""
    shift_list = get_object_or_404(ShiftList, pk=pk)
    shift_list_repr = str(shift_list)
    
    try:
        # Denetim logu
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='ShiftList',
            object_id=shift_list.id,
            object_repr=shift_list_repr,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Nöbet listesini sil
        shift_list.delete()
        
        messages.success(request, _('Nöbet listesi başarıyla silindi.'))
    except Exception as e:
        messages.error(request, _('Nöbet listesi silinirken hata oluştu: {}').format(str(e)))
    
    return redirect('shift_list_view')


@login_required
@permission_required('nobet_listesi.add_shift', raise_exception=True)
def shift_create(request, shift_list_id):
    """Nöbet ekleme"""
    shift_list = get_object_or_404(ShiftList, pk=shift_list_id)
    
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.shift_list = shift_list
            shift.save()
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='Shift',
                object_id=shift.id,
                object_repr=str(shift),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Nöbet başarıyla eklendi.'))
            return redirect('shift_list_detail', pk=shift_list_id)
    else:
        form = ShiftForm()
    
    context = {
        'form': form,
        'shift_list': shift_list,
    }
    
    return render(request, 'nobet_listesi/shift_form.html', context)


@login_required
@permission_required('nobet_listesi.change_shift', raise_exception=True)
def shift_update(request, pk):
    """Nöbet güncelleme"""
    shift = get_object_or_404(Shift, pk=pk)
    shift_list_id = shift.shift_list.id
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            # Değişiklikleri kaydet
            old_data = {
                'doctor': shift.doctor.id,
                'date': shift.date.isoformat(),
                'shift_type': shift.shift_type,
                'start_time': shift.start_time.isoformat() if shift.start_time else None,
                'end_time': shift.end_time.isoformat() if shift.end_time else None,
                'notes': shift.notes
            }
            
            shift = form.save()
            
            # Denetim logu
            new_data = {
                'doctor': shift.doctor.id,
                'date': shift.date.isoformat(),
                'shift_type': shift.shift_type,
                'start_time': shift.start_time.isoformat() if shift.start_time else None,
                'end_time': shift.end_time.isoformat() if shift.end_time else None,
                'notes': shift.notes
            }
            
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='Shift',
                object_id=shift.id,
                object_repr=str(shift),
                changes={'old': old_data, 'new': new_data},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Nöbet başarıyla güncellendi.'))
            return redirect('shift_list_detail', pk=shift_list_id)
    else:
        form = ShiftForm(instance=shift)
    
    context = {
        'form': form,
        'shift': shift,
        'shift_list': shift.shift_list,
    }
    
    return render(request, 'nobet_listesi/shift_form.html', context)


@login_required
@permission_required('nobet_listesi.delete_shift', raise_exception=True)
@require_POST
def shift_delete(request, pk):
    """Nöbet silme"""
    shift = get_object_or_404(Shift, pk=pk)
    shift_list_id = shift.shift_list.id
    shift_repr = str(shift)
    
    try:
        # Denetim logu
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Shift',
            object_id=shift.id,
            object_repr=shift_repr,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Nöbeti sil
        shift.delete()
        
        messages.success(request, _('Nöbet başarıyla silindi.'))
    except Exception as e:
        messages.error(request, _('Nöbet silinirken hata oluştu: {}').format(str(e)))
    
    return redirect('shift_list_detail', pk=shift_list_id)


@login_required
@permission_required('nobet_listesi.add_datasource', raise_exception=True)
def data_source_list(request):
    """Veri kaynaklarını listeleme"""
    data_sources = DataSource.objects.all().order_by('-updated_at')
    
    context = {
        'data_sources': data_sources,
    }
    
    return render(request, 'nobet_listesi/data_source_list.html', context)


@login_required
@permission_required('nobet_listesi.add_datasource', raise_exception=True)
def data_source_create(request):
    """Veri kaynağı ekleme"""
    if request.method == 'POST':
        form = DataSourceForm(request.POST)
        if form.is_valid():
            data_source = form.save(commit=False)
            data_source.created_by = request.user
            data_source.save()
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='DataSource',
                object_id=data_source.id,
                object_repr=str(data_source),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Veri kaynağı başarıyla eklendi.'))
            return redirect('data_source_list')
    else:
        form = DataSourceForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'nobet_listesi/data_source_form.html', context)


@login_required
@permission_required('nobet_listesi.change_datasource', raise_exception=True)
def data_source_update(request, pk):
    """Veri kaynağı güncelleme"""
    data_source = get_object_or_404(DataSource, pk=pk)
    
    if request.method == 'POST':
        form = DataSourceForm(request.POST, instance=data_source)
        if form.is_valid():
            # Değişiklikleri kaydet
            old_data = {
                'name': data_source.name,
                'url': data_source.url,
                'source_type': data_source.source_type,
                'active': data_source.active,
                'fetch_interval': data_source.fetch_interval,
                'column_mapping': data_source.column_mapping
            }
            
            data_source = form.save()
            
            # Denetim logu
            new_data = {
                'name': data_source.name,
                'url': data_source.url,
                'source_type': data_source.source_type,
                'active': data_source.active,
                'fetch_interval': data_source.fetch_interval,
                'column_mapping': data_source.column_mapping
            }
            
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='DataSource',
                object_id=data_source.id,
                object_repr=str(data_source),
                changes={'old': old_data, 'new': new_data},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Veri kaynağı başarıyla güncellendi.'))
            return redirect('data_source_list')
    else:
        form = DataSourceForm(instance=data_source)
    
    context = {
        'form': form,
        'data_source': data_source,
    }
    
    return render(request, 'nobet_listesi/data_source_form.html', context)


@login_required
@permission_required('nobet_listesi.delete_datasource', raise_exception=True)
@require_POST
def data_source_delete(request, pk):
    """Veri kaynağı silme"""
    data_source = get_object_or_404(DataSource, pk=pk)
    data_source_repr = str(data_source)
    
    try:
        # Denetim logu
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='DataSource',
            object_id=data_source.id,
            object_repr=data_source_repr,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Veri kaynağını sil
        data_source.delete()
        
        messages.success(request, _('Veri kaynağı başarıyla silindi.'))
    except Exception as e:
        messages.error(request, _('Veri kaynağı silinirken hata oluştu: {}').format(str(e)))
    
    return redirect('data_source_list')


@login_required
@permission_required('nobet_listesi.add_fetchlog', raise_exception=True)
@require_POST
def fetch_data(request, source_id):
    """Veri kaynağından veri çekme işlemini başlatır"""
    data_source = get_object_or_404(DataSource, pk=source_id)
    
    try:
        # Celery task'ı başlat
        task = fetch_data_from_source.delay(data_source.id, request.user.id)
        
        messages.success(
            request, 
            _('Veri çekme işlemi başlatıldı. İşlem ID: {}').format(task.id)
        )
    except Exception as e:
        messages.error(
            request, 
            _('Veri çekme işlemi başlatılırken hata oluştu: {}').format(str(e))
        )
    
    return redirect('data_source_list')


@login_required
@permission_required('nobet_listesi.add_shiftlist', raise_exception=True)
def file_upload(request):
    """Manuel dosya yükleme"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_type = form.cleaned_data['file_type']
            department = form.cleaned_data['department']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            title = form.cleaned_data['title']
            column_mapping = form.cleaned_data['column_mapping']
            
            # Dosyayı geçici olarak kaydet
            temp_file_path = f"/tmp/{uuid.uuid4()}_{file.name}"
            with open(temp_file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            try:
                # Celery task'ı başlat
                task = process_uploaded_file.delay(
                    temp_file_path,
                    file_type,
                    department.id,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    title,
                    column_mapping,
                    request.user.id
                )
                
                messages.success(
                    request, 
                    _('Dosya yükleme işlemi başlatıldı. İşlem ID: {}').format(task.id)
                )
                return redirect('shift_list_view')
            
            except Exception as e:
                messages.error(
                    request, 
                    _('Dosya işlenirken hata oluştu: {}').format(str(e))
                )
    else:
        form = FileUploadForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'nobet_listesi/file_upload.html', context)


@login_required
def export_shift_list(request):
    """Nöbet listesini dışa aktarma"""
    if request.method == 'POST':
        form = ExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['format']
            shift_list = form.cleaned_data['shift_list']
            include_contact_info = form.cleaned_data['include_contact_info']
            mask_contact_info = form.cleaned_data['mask_contact_info']
            
            # Nöbetleri al
            shifts = shift_list.shifts.all().order_by('date', 'start_time')
            
            # Dışa aktarılacak verileri hazırla
            data = []
            for shift in shifts:
                row = {
                    'Tarih': shift.date.strftime('%d.%m.%Y'),
                    'Doktor': str(shift.doctor),
                    'Nöbet Tipi': shift.get_shift_type_display(),
                    'Başlangıç': shift.start_time.strftime('%H:%M') if shift.start_time else '',
                    'Bitiş': shift.end_time.strftime('%H:%M') if shift.end_time else '',
                    'Notlar': shift.notes or ''
                }
                
                # İletişim bilgilerini ekle
                if include_contact_info:
                    if mask_contact_info:
                        row['Telefon'] = shift.doctor.get_masked_phone() or ''
                        row['E-posta'] = shift.doctor.get_masked_email() or ''
                    else:
                        row['Telefon'] = shift.doctor.phone or ''
                        row['E-posta'] = shift.doctor.email or ''
                
                data.append(row)
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='export',
                model_name='ShiftList',
                object_id=shift_list.id,
                object_repr=str(shift_list),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Seçilen formatta dışa aktar
            if export_format == 'excel':
                # Excel formatında dışa aktar
                output = io.BytesIO()
                df = pd.DataFrame(data)
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Nöbet Listesi', index=False)
                    worksheet = writer.sheets['Nöbet Listesi']
                    for i, col in enumerate(df.columns):
                        worksheet.set_column(i, i, max(len(col) + 2, df[col].astype(str).str.len().max() + 2))
                
                output.seek(0)
                response = HttpResponse(
                    output.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{shift_list.title}.xlsx"'
                return response
            
            elif export_format == 'csv':
                # CSV formatında dışa aktar
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{shift_list.title}.csv"'
                
                writer = csv.DictWriter(response, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                return response
            
            elif export_format == 'pdf':
                # PDF formatında dışa aktar (basit HTML tablosu olarak)
                context = {
                    'shift_list': shift_list,
                    'data': data,
                    'include_contact_info': include_contact_info,
                }
                return render(request, 'nobet_listesi/shift_list_pdf.html', context)
    
    else:
        form = ExportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'nobet_listesi/export_form.html', context)


@login_required
@permission_required('nobet_listesi.view_auditlog', raise_exception=True)
def audit_log_list(request):
    """Denetim loglarını görüntüleme"""
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Filtreleme
    action = request.GET.get('action')
    model_name = request.GET.get('model_name')
    user_id = request.GET.get('user')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if action:
        logs = logs.filter(action=action)
    
    if model_name:
        logs = logs.filter(model_name=model_name)
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if date_from:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__lte=date_to)
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(logs, 20)  # Her sayfada 20 log
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtre seçenekleri
    action_choices = AuditLog.ACTION_CHOICES
    model_names = AuditLog.objects.values_list('model_name', flat=True).distinct()
    users = User.objects.filter(audit_logs__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'action_choices': action_choices,
        'model_names': model_names,
        'users': users,
        'selected_action': action,
        'selected_model': model_name,
        'selected_user': user_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'nobet_listesi/audit_log_list.html', context)


@login_required
@permission_required('nobet_listesi.view_fetchlog', raise_exception=True)
def fetch_log_list(request):
    """Veri çekme loglarını görüntüleme"""
    logs = FetchLog.objects.all().order_by('-started_at')
    
    # Filtreleme
    status = request.GET.get('status')
    source_id = request.GET.get('source')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        logs = logs.filter(status=status)
    
    if source_id:
        logs = logs.filter(source_id=source_id)
    
    if date_from:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(started_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(started_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(logs, 20)  # Her sayfada 20 log
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtre seçenekleri
    status_choices = FetchLog.STATUS_CHOICES
    sources = DataSource.objects.all()
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'sources': sources,
        'selected_status': status,
        'selected_source': source_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'nobet_listesi/fetch_log_list.html', context)


@login_required
@permission_required('nobet_listesi.view_fetchlog', raise_exception=True)
def fetch_log_detail(request, pk):
    """Veri çekme logu detayı"""
    log = get_object_or_404(FetchLog, pk=pk)
    
    context = {
        'log': log,
    }
    
    return render(request, 'nobet_listesi/fetch_log_detail.html', context)


@login_required
@permission_required('nobet_listesi.add_doctor', raise_exception=True)
def doctor_list(request):
    """Doktorları listeleme"""
    doctors = Doctor.objects.all().order_by('surname', 'name')
    
    # Filtreleme
    department_id = request.GET.get('department')
    active = request.GET.get('active')
    search = request.GET.get('search')
    
    if department_id:
        doctors = doctors.filter(department_id=department_id)
    
    if active is not None:
        active = active.lower() == 'true'
        doctors = doctors.filter(active=active)
    
    if search:
        doctors = doctors.filter(
            Q(name__icontains=search) | 
            Q(surname__icontains=search) | 
            Q(title__icontains=search)
        )
    
    # Sayfalama
    paginator = Paginator(doctors, 20)  # Her sayfada 20 doktor
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtre seçenekleri
    departments = Department.objects.filter(active=True)
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'selected_department': department_id,
        'selected_active': active,
        'search': search,
    }
    
    return render(request, 'nobet_listesi/doctor_list.html', context)


@login_required
@permission_required('nobet_listesi.add_doctor', raise_exception=True)
def doctor_create(request):
    """Doktor ekleme"""
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='Doctor',
                object_id=doctor.id,
                object_repr=str(doctor),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Doktor başarıyla eklendi.'))
            return redirect('doctor_list')
    else:
        form = DoctorForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'nobet_listesi/doctor_form.html', context)


@login_required
@permission_required('nobet_listesi.change_doctor', raise_exception=True)
def doctor_update(request, pk):
    """Doktor güncelleme"""
    doctor = get_object_or_404(Doctor, pk=pk)
    
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            # Değişiklikleri kaydet
            old_data = {
                'name': doctor.name,
                'surname': doctor.surname,
                'title': doctor.title,
                'department': doctor.department.id if doctor.department else None,
                'phone': doctor.phone,
                'email': doctor.email,
                'active': doctor.active,
                'external_id': doctor.external_id
            }
            
            doctor = form.save()
            
            # Denetim logu
            new_data = {
                'name': doctor.name,
                'surname': doctor.surname,
                'title': doctor.title,
                'department': doctor.department.id if doctor.department else None,
                'phone': doctor.phone,
                'email': doctor.email,
                'active': doctor.active,
                'external_id': doctor.external_id
            }
            
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='Doctor',
                object_id=doctor.id,
                object_repr=str(doctor),
                changes={'old': old_data, 'new': new_data},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Doktor başarıyla güncellendi.'))
            return redirect('doctor_list')
    else:
        form = DoctorForm(instance=doctor)
    
    context = {
        'form': form,
        'doctor': doctor,
    }
    
    return render(request, 'nobet_listesi/doctor_form.html', context)


@login_required
@permission_required('nobet_listesi.delete_doctor', raise_exception=True)
@require_POST
def doctor_delete(request, pk):
    """Doktor silme"""
    doctor = get_object_or_404(Doctor, pk=pk)
    doctor_repr = str(doctor)
    
    try:
        # Denetim logu
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Doctor',
            object_id=doctor.id,
            object_repr=doctor_repr,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Doktoru sil
        doctor.delete()
        
        messages.success(request, _('Doktor başarıyla silindi.'))
    except Exception as e:
        messages.error(request, _('Doktor silinirken hata oluştu: {}').format(str(e)))
    
    return redirect('doctor_list')


@login_required
@permission_required('nobet_listesi.add_department', raise_exception=True)
def department_list(request):
    """Bölümleri listeleme"""
    departments = Department.objects.all().order_by('name')
    
    # Filtreleme
    active = request.GET.get('active')
    search = request.GET.get('search')
    
    if active is not None:
        active = active.lower() == 'true'
        departments = departments.filter(active=active)
    
    if search:
        departments = departments.filter(
            Q(name__icontains=search) | 
            Q(code__icontains=search)
        )
    
    # Sayfalama
    paginator = Paginator(departments, 20)  # Her sayfada 20 bölüm
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'selected_active': active,
        'search': search,
    }
    
    return render(request, 'nobet_listesi/department_list.html', context)


@login_required
@permission_required('nobet_listesi.add_department', raise_exception=True)
def department_create(request):
    """Bölüm ekleme"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            
            # Denetim logu
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='Department',
                object_id=department.id,
                object_repr=str(department),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Bölüm başarıyla eklendi.'))
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'nobet_listesi/department_form.html', context)


@login_required
@permission_required('nobet_listesi.change_department', raise_exception=True)
def department_update(request, pk):
    """Bölüm güncelleme"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            # Değişiklikleri kaydet
            old_data = {
                'name': department.name,
                'code': department.code,
                'active': department.active
            }
            
            department = form.save()
            
            # Denetim logu
            new_data = {
                'name': department.name,
                'code': department.code,
                'active': department.active
            }
            
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='Department',
                object_id=department.id,
                object_repr=str(department),
                changes={'old': old_data, 'new': new_data},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            messages.success(request, _('Bölüm başarıyla güncellendi.'))
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
    }
    
    return render(request, 'nobet_listesi/department_form.html', context)


@login_required
@permission_required('nobet_listesi.delete_department', raise_exception=True)
@require_POST
def department_delete(request, pk):
    """Bölüm silme"""
    department = get_object_or_404(Department, pk=pk)
    department_repr = str(department)
    
    try:
        # Denetim logu
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Department',
            object_id=department.id,
            object_repr=department_repr,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Bölümü sil
        department.delete()
        
        messages.success(request, _('Bölüm başarıyla silindi.'))
    except Exception as e:
        messages.error(request, _('Bölüm silinirken hata oluştu: {}').format(str(e)))
    
    return redirect('department_list')