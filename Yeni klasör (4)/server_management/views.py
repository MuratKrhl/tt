from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import ServerType, Server, ServerMaintenanceRecord, ServerMonitoringLog, ServerDocument
from .forms import (
    ServerTypeForm, ServerForm, ServerMaintenanceRecordForm, ServerMonitoringLogForm,
    ServerDocumentForm, ServerFilterForm, ServerMaintenanceFilterForm, ServerMonitoringLogFilterForm
)

@login_required
def server_dashboard(request):
    """Sunucu yönetimi dashboard görünümü"""
    # Sunucu istatistikleri
    total_servers = Server.objects.count()
    active_servers = Server.objects.filter(status='active').count()
    maintenance_servers = Server.objects.filter(status='maintenance').count()
    inactive_servers = Server.objects.filter(status='inactive').count()
    retired_servers = Server.objects.filter(status='retired').count()
    
    # İşletim sistemine göre dağılım
    os_distribution = {}
    for os_choice, os_name in Server.OS_CHOICES:
        os_distribution[os_name] = Server.objects.filter(operating_system=os_choice).count()
    
    # Yakında garantisi dolacak sunucular
    today = timezone.now().date()
    ninety_days_later = today + timezone.timedelta(days=90)
    warranty_expiring_soon = Server.objects.filter(
        warranty_expiry__gt=today,
        warranty_expiry__lte=ninety_days_later
    ).order_by('warranty_expiry')
    
    # Yaklaşan bakımlar
    upcoming_maintenance = ServerMaintenanceRecord.objects.filter(
        status__in=['scheduled', 'in_progress'],
        scheduled_date__gte=today
    ).order_by('scheduled_date')[:5]
    
    # Son izleme günlükleri
    recent_logs = ServerMonitoringLog.objects.filter(
        resolved=False
    ).order_by('-timestamp')[:5]
    
    return render(request, 'server_management/dashboard.html', {
        'total_servers': total_servers,
        'active_servers': active_servers,
        'maintenance_servers': maintenance_servers,
        'inactive_servers': inactive_servers,
        'retired_servers': retired_servers,
        'os_distribution': os_distribution,
        'warranty_expiring_soon': warranty_expiring_soon,
        'upcoming_maintenance': upcoming_maintenance,
        'recent_logs': recent_logs,
    })

# Sunucu Türü görünümleri
@login_required
def server_type_list(request):
    """Sunucu türleri listesi görünümü"""
    server_types = ServerType.objects.all().order_by('name')
    return render(request, 'server_management/server_type_list.html', {
        'server_types': server_types
    })

@login_required
def server_type_create(request):
    """Sunucu türü oluşturma görünümü"""
    if request.method == 'POST':
        form = ServerTypeForm(request.POST)
        if form.is_valid():
            server_type = form.save()
            messages.success(request, f'{server_type.name} sunucu türü başarıyla oluşturuldu!')
            return redirect('server_type_list')
    else:
        form = ServerTypeForm()
    
    return render(request, 'server_management/server_type_form.html', {
        'form': form,
        'action': 'Oluştur'
    })

@login_required
def server_type_update(request, type_id):
    """Sunucu türü güncelleme görünümü"""
    server_type = get_object_or_404(ServerType, id=type_id)
    
    if request.method == 'POST':
        form = ServerTypeForm(request.POST, instance=server_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'{server_type.name} sunucu türü başarıyla güncellendi!')
            return redirect('server_type_list')
    else:
        form = ServerTypeForm(instance=server_type)
    
    return render(request, 'server_management/server_type_form.html', {
        'form': form,
        'server_type': server_type,
        'action': 'Güncelle'
    })

@login_required
def server_type_delete(request, type_id):
    """Sunucu türü silme görünümü"""
    server_type = get_object_or_404(ServerType, id=type_id)
    
    if request.method == 'POST':
        type_name = server_type.name
        server_type.delete()
        messages.success(request, f'{type_name} sunucu türü başarıyla silindi!')
        return redirect('server_type_list')
    
    return render(request, 'server_management/server_type_confirm_delete.html', {
        'server_type': server_type
    })

# Sunucu görünümleri
@login_required
def server_list(request):
    """Sunucu listesi görünümü"""
    filter_form = ServerFilterForm(request.GET)
    servers = Server.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['name']:
            servers = servers.filter(name__icontains=filter_form.cleaned_data['name'])
        if filter_form.cleaned_data['hostname']:
            servers = servers.filter(hostname__icontains=filter_form.cleaned_data['hostname'])
        if filter_form.cleaned_data['ip_address']:
            servers = servers.filter(ip_address__icontains=filter_form.cleaned_data['ip_address'])
        if filter_form.cleaned_data['server_type']:
            servers = servers.filter(server_type=filter_form.cleaned_data['server_type'])
        if filter_form.cleaned_data['operating_system']:
            servers = servers.filter(operating_system=filter_form.cleaned_data['operating_system'])
        if filter_form.cleaned_data['status']:
            servers = servers.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['location']:
            servers = servers.filter(location__icontains=filter_form.cleaned_data['location'])
        if filter_form.cleaned_data['warranty_expiring_in_days']:
            days = filter_form.cleaned_data['warranty_expiring_in_days']
            target_date = timezone.now().date() + timezone.timedelta(days=days)
            servers = servers.filter(
                warranty_expiry__lte=target_date,
                warranty_expiry__gt=timezone.now().date()
            )
    
    servers = servers.order_by('name')
    
    return render(request, 'server_management/server_list.html', {
        'servers': servers,
        'filter_form': filter_form
    })

@login_required
def server_detail(request, server_id):
    """Sunucu detay görünümü"""
    server = get_object_or_404(Server, id=server_id)
    maintenance_records = server.maintenance_records.all().order_by('-scheduled_date')
    monitoring_logs = server.monitoring_logs.all().order_by('-timestamp')[:10]
    documents = server.documents.all().order_by('-uploaded_at')
    
    return render(request, 'server_management/server_detail.html', {
        'server': server,
        'maintenance_records': maintenance_records,
        'monitoring_logs': monitoring_logs,
        'documents': documents
    })

@login_required
def server_create(request):
    """Sunucu oluşturma görünümü"""
    if request.method == 'POST':
        form = ServerForm(request.POST)
        if form.is_valid():
            server = form.save(commit=False)
            server.created_by = request.user
            server.save()
            messages.success(request, f'{server.name} sunucusu başarıyla oluşturuldu!')
            return redirect('server_detail', server_id=server.id)
    else:
        form = ServerForm()
    
    return render(request, 'server_management/server_form.html', {
        'form': form,
        'action': 'Oluştur'
    })

@login_required
def server_update(request, server_id):
    """Sunucu güncelleme görünümü"""
    server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        form = ServerForm(request.POST, instance=server)
        if form.is_valid():
            form.save()
            messages.success(request, f'{server.name} sunucusu başarıyla güncellendi!')
            return redirect('server_detail', server_id=server.id)
    else:
        form = ServerForm(instance=server)
    
    return render(request, 'server_management/server_form.html', {
        'form': form,
        'server': server,
        'action': 'Güncelle'
    })

@login_required
def server_delete(request, server_id):
    """Sunucu silme görünümü"""
    server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        server_name = server.name
        server.delete()
        messages.success(request, f'{server_name} sunucusu başarıyla silindi!')
        return redirect('server_list')
    
    return render(request, 'server_management/server_confirm_delete.html', {
        'server': server
    })

# Sunucu Bakım Kaydı görünümleri
@login_required
def server_maintenance_list(request):
    """Sunucu bakım kayıtları listesi görünümü"""
    filter_form = ServerMaintenanceFilterForm(request.GET)
    maintenance_records = ServerMaintenanceRecord.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['server']:
            maintenance_records = maintenance_records.filter(server=filter_form.cleaned_data['server'])
        if filter_form.cleaned_data['maintenance_type']:
            maintenance_records = maintenance_records.filter(
                maintenance_type__icontains=filter_form.cleaned_data['maintenance_type']
            )
        if filter_form.cleaned_data['status']:
            maintenance_records = maintenance_records.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['scheduled_from']:
            from_date = filter_form.cleaned_data['scheduled_from']
            maintenance_records = maintenance_records.filter(scheduled_date__date__gte=from_date)
        if filter_form.cleaned_data['scheduled_to']:
            to_date = filter_form.cleaned_data['scheduled_to']
            maintenance_records = maintenance_records.filter(scheduled_date__date__lte=to_date)
        if filter_form.cleaned_data['performed_by']:
            maintenance_records = maintenance_records.filter(performed_by=filter_form.cleaned_data['performed_by'])
    
    maintenance_records = maintenance_records.order_by('-scheduled_date')
    
    return render(request, 'server_management/server_maintenance_list.html', {
        'maintenance_records': maintenance_records,
        'filter_form': filter_form
    })

@login_required
def server_maintenance_create(request, server_id=None):
    """Sunucu bakım kaydı oluşturma görünümü"""
    server = None
    if server_id:
        server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        form = ServerMaintenanceRecordForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.created_by = request.user
            maintenance.save()
            
            messages.success(request, 'Sunucu bakım kaydı başarıyla oluşturuldu!')
            return redirect('server_detail', server_id=maintenance.server.id)
    else:
        initial_data = {}
        if server:
            initial_data['server'] = server
        
        form = ServerMaintenanceRecordForm(initial=initial_data)
    
    return render(request, 'server_management/server_maintenance_form.html', {
        'form': form,
        'server': server,
        'action': 'Oluştur'
    })

@login_required
def server_maintenance_update(request, maintenance_id):
    """Sunucu bakım kaydı güncelleme görünümü"""
    maintenance = get_object_or_404(ServerMaintenanceRecord, id=maintenance_id)
    server = maintenance.server
    
    if request.method == 'POST':
        form = ServerMaintenanceRecordForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sunucu bakım kaydı başarıyla güncellendi!')
            return redirect('server_detail', server_id=server.id)
    else:
        form = ServerMaintenanceRecordForm(instance=maintenance)
    
    return render(request, 'server_management/server_maintenance_form.html', {
        'form': form,
        'maintenance': maintenance,
        'server': server,
        'action': 'Güncelle'
    })

@login_required
def server_maintenance_delete(request, maintenance_id):
    """Sunucu bakım kaydı silme görünümü"""
    maintenance = get_object_or_404(ServerMaintenanceRecord, id=maintenance_id)
    server = maintenance.server
    
    if request.method == 'POST':
        maintenance.delete()
        messages.success(request, 'Sunucu bakım kaydı başarıyla silindi!')
        return redirect('server_detail', server_id=server.id)
    
    return render(request, 'server_management/server_maintenance_confirm_delete.html', {
        'maintenance': maintenance,
        'server': server
    })

# Sunucu İzleme Günlüğü görünümleri
@login_required
def server_monitoring_log_list(request):
    """Sunucu izleme günlükleri listesi görünümü"""
    filter_form = ServerMonitoringLogFilterForm(request.GET)
    logs = ServerMonitoringLog.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['server']:
            logs = logs.filter(server=filter_form.cleaned_data['server'])
        if filter_form.cleaned_data['log_level']:
            logs = logs.filter(log_level=filter_form.cleaned_data['log_level'])
        if filter_form.cleaned_data['metric_name']:
            logs = logs.filter(metric_name__icontains=filter_form.cleaned_data['metric_name'])
        if filter_form.cleaned_data['timestamp_from']:
            logs = logs.filter(timestamp__gte=filter_form.cleaned_data['timestamp_from'])
        if filter_form.cleaned_data['timestamp_to']:
            logs = logs.filter(timestamp__lte=filter_form.cleaned_data['timestamp_to'])
        if filter_form.cleaned_data['resolved'] is not None:
            logs = logs.filter(resolved=filter_form.cleaned_data['resolved'])
    
    logs = logs.order_by('-timestamp')
    
    return render(request, 'server_management/server_monitoring_log_list.html', {
        'logs': logs,
        'filter_form': filter_form
    })

@login_required
def server_monitoring_log_create(request, server_id=None):
    """Sunucu izleme günlüğü oluşturma görünümü"""
    server = None
    if server_id:
        server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        form = ServerMonitoringLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(request, 'Sunucu izleme günlüğü başarıyla oluşturuldu!')
            return redirect('server_detail', server_id=log.server.id)
    else:
        initial_data = {}
        if server:
            initial_data['server'] = server
        initial_data['timestamp'] = timezone.now()
        
        form = ServerMonitoringLogForm(initial=initial_data)
    
    return render(request, 'server_management/server_monitoring_log_form.html', {
        'form': form,
        'server': server,
        'action': 'Oluştur'
    })

@login_required
def server_monitoring_log_resolve(request, log_id):
    """Sunucu izleme günlüğünü çözüldü olarak işaretleme görünümü"""
    log = get_object_or_404(ServerMonitoringLog, id=log_id)
    
    if request.method == 'POST':
        log.resolve(request.user)
        messages.success(request, 'Sunucu izleme günlüğü çözüldü olarak işaretlendi!')
        return redirect('server_monitoring_log_list')
    
    return render(request, 'server_management/server_monitoring_log_resolve.html', {
        'log': log
    })

# Sunucu Belgesi görünümleri
@login_required
def server_document_create(request, server_id):
    """Sunucu belgesi oluşturma görünümü"""
    server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        form = ServerDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.server = server
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'{document.title} belgesi başarıyla yüklendi!')
            return redirect('server_detail', server_id=server.id)
    else:
        form = ServerDocumentForm(initial={'server': server})
    
    return render(request, 'server_management/server_document_form.html', {
        'form': form,
        'server': server
    })

@login_required
def server_document_delete(request, document_id):
    """Sunucu belgesi silme görünümü"""
    document = get_object_or_404(ServerDocument, id=document_id)
    server = document.server
    
    if request.method == 'POST':
        document_title = document.title
        document.delete()
        messages.success(request, f'{document_title} belgesi başarıyla silindi!')
        return redirect('server_detail', server_id=server.id)
    
    return render(request, 'server_management/server_document_confirm_delete.html', {
        'document': document,
        'server': server
    })