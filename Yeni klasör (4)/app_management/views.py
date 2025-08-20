from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Server, Application, ApplicationLog, MaintenanceRecord, ApplicationDocument
from .forms import ServerForm, ApplicationForm, MaintenanceRecordForm, ApplicationDocumentForm

@login_required
def dashboard_view(request):
    """Ana dashboard görünümü"""
    servers = Server.objects.all()
    applications = Application.objects.all()
    
    # Son 5 uygulama logu
    recent_logs = ApplicationLog.objects.all().order_by('-timestamp')[:5]
    
    # Yaklaşan bakımlar
    upcoming_maintenance = MaintenanceRecord.objects.filter(
        status__in=['scheduled', 'in_progress']
    ).order_by('scheduled_start')[:5]
    
    return render(request, 'app_management/dashboard.html', {
        'servers': servers,
        'applications': applications,
        'recent_logs': recent_logs,
        'upcoming_maintenance': upcoming_maintenance,
        'server_count': servers.count(),
        'application_count': applications.count(),
    })

@login_required
def server_list_view(request):
    """Sunucu listesi görünümü"""
    servers = Server.objects.all().order_by('name')
    
    return render(request, 'app_management/server_list.html', {'servers': servers})

@login_required
def server_detail_view(request, server_id):
    """Sunucu detay görünümü"""
    server = get_object_or_404(Server, id=server_id)
    applications = server.applications.all()
    
    return render(request, 'app_management/server_detail.html', {
        'server': server,
        'applications': applications
    })

@login_required
def server_create_view(request):
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
    
    return render(request, 'app_management/server_form.html', {'form': form, 'action': 'Oluştur'})

@login_required
def server_update_view(request, server_id):
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
    
    return render(request, 'app_management/server_form.html', {'form': form, 'server': server, 'action': 'Güncelle'})

@login_required
def server_delete_view(request, server_id):
    """Sunucu silme görünümü"""
    server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        server_name = server.name
        server.delete()
        messages.success(request, f'{server_name} sunucusu başarıyla silindi!')
        return redirect('server_list')
    
    return render(request, 'app_management/server_confirm_delete.html', {'server': server})

@login_required
def application_list_view(request):
    """Uygulama listesi görünümü"""
    applications = Application.objects.all().order_by('name')
    
    return render(request, 'app_management/application_list.html', {'applications': applications})

@login_required
def application_detail_view(request, application_id):
    """Uygulama detay görünümü"""
    application = get_object_or_404(Application, id=application_id)
    logs = application.logs.all().order_by('-timestamp')[:10]
    maintenance_records = application.maintenance_records.all().order_by('-scheduled_start')
    documents = application.documents.all()
    
    return render(request, 'app_management/application_detail.html', {
        'application': application,
        'logs': logs,
        'maintenance_records': maintenance_records,
        'documents': documents
    })

@login_required
def application_create_view(request):
    """Uygulama oluşturma görünümü"""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.created_by = request.user
            application.save()
            
            # Uygulama logu oluştur
            ApplicationLog.objects.create(
                application=application,
                log_type='info',
                message=f'{application.name} uygulaması oluşturuldu.',
                user=request.user
            )
            
            messages.success(request, f'{application.name} uygulaması başarıyla oluşturuldu!')
            return redirect('application_detail', application_id=application.id)
    else:
        form = ApplicationForm()
    
    return render(request, 'app_management/application_form.html', {'form': form, 'action': 'Oluştur'})

@login_required
def application_update_view(request, application_id):
    """Uygulama güncelleme görünümü"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            
            # Uygulama logu oluştur
            ApplicationLog.objects.create(
                application=application,
                log_type='info',
                message=f'{application.name} uygulaması güncellendi.',
                user=request.user
            )
            
            messages.success(request, f'{application.name} uygulaması başarıyla güncellendi!')
            return redirect('application_detail', application_id=application.id)
    else:
        form = ApplicationForm(instance=application)
    
    return render(request, 'app_management/application_form.html', {
        'form': form, 
        'application': application, 
        'action': 'Güncelle'
    })

@login_required
def application_delete_view(request, application_id):
    """Uygulama silme görünümü"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        application_name = application.name
        application.delete()
        messages.success(request, f'{application_name} uygulaması başarıyla silindi!')
        return redirect('application_list')
    
    return render(request, 'app_management/application_confirm_delete.html', {'application': application})

@login_required
def application_log_create_view(request, application_id):
    """Uygulama logu oluşturma görünümü"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        log_type = request.POST.get('log_type')
        message = request.POST.get('message')
        
        if message:
            ApplicationLog.objects.create(
                application=application,
                log_type=log_type,
                message=message,
                user=request.user
            )
            messages.success(request, 'Log başarıyla kaydedildi!')
        else:
            messages.error(request, 'Log mesajı boş olamaz!')
        
        return redirect('application_detail', application_id=application.id)
    
    return render(request, 'app_management/application_log_form.html', {'application': application})

@login_required
def maintenance_record_create_view(request, application_id):
    """Bakım kaydı oluşturma görünümü"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.application = application
            maintenance.created_by = request.user
            maintenance.save()
            
            # Uygulama logu oluştur
            ApplicationLog.objects.create(
                application=application,
                log_type='info',
                message=f'Bakım planlandı: {maintenance.title}',
                user=request.user
            )
            
            messages.success(request, 'Bakım kaydı başarıyla oluşturuldu!')
            return redirect('application_detail', application_id=application.id)
    else:
        form = MaintenanceRecordForm()
    
    return render(request, 'app_management/maintenance_form.html', {
        'form': form, 
        'application': application,
        'action': 'Oluştur'
    })

@login_required
def maintenance_record_update_view(request, maintenance_id):
    """Bakım kaydı güncelleme görünümü"""
    maintenance = get_object_or_404(MaintenanceRecord, id=maintenance_id)
    application = maintenance.application
    
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            
            # Uygulama logu oluştur
            ApplicationLog.objects.create(
                application=application,
                log_type='info',
                message=f'Bakım güncellendi: {maintenance.title}',
                user=request.user
            )
            
            messages.success(request, 'Bakım kaydı başarıyla güncellendi!')
            return redirect('application_detail', application_id=application.id)
    else:
        form = MaintenanceRecordForm(instance=maintenance)
    
    return render(request, 'app_management/maintenance_form.html', {
        'form': form, 
        'maintenance': maintenance,
        'application': application,
        'action': 'Güncelle'
    })

@login_required
def document_upload_view(request, application_id):
    """Doküman yükleme görünümü"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        form = ApplicationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.application = application
            document.uploaded_by = request.user
            document.save()
            
            messages.success(request, 'Doküman başarıyla yüklendi!')
            return redirect('application_detail', application_id=application.id)
    else:
        form = ApplicationDocumentForm()
    
    return render(request, 'app_management/document_form.html', {
        'form': form, 
        'application': application
    })

@login_required
def document_delete_view(request, document_id):
    """Doküman silme görünümü"""
    document = get_object_or_404(ApplicationDocument, id=document_id)
    application = document.application
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Doküman başarıyla silindi!')
        return redirect('application_detail', application_id=application.id)
    
    return render(request, 'app_management/document_confirm_delete.html', {
        'document': document,
        'application': application
    })

@login_required
def home_view(request):
    """Ana sayfa görünümü"""
    return render(request, 'app_management/home.html')