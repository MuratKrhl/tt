from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import CertificateType, Certificate, CertificateRenewal, CertificateNotification
from .forms import (
    CertificateTypeForm, CertificateForm, CertificateRenewalForm, 
    CertificateNotificationForm, CertificateFilterForm, CertificateRenewalFilterForm
)

@login_required
def certificate_dashboard(request):
    """Sertifika yönetimi dashboard görünümü"""
    # Sertifika istatistikleri
    total_certificates = Certificate.objects.count()
    active_certificates = Certificate.objects.filter(status='active').count()
    expired_certificates = Certificate.objects.filter(status='expired').count()
    revoked_certificates = Certificate.objects.filter(status='revoked').count()
    pending_certificates = Certificate.objects.filter(status='pending').count()
    
    # Yakında süresi dolacak sertifikalar
    today = timezone.now().date()
    thirty_days_later = today + timezone.timedelta(days=30)
    expiring_soon = Certificate.objects.filter(
        status='active',
        expiry_date__gt=today,
        expiry_date__lte=thirty_days_later
    ).order_by('expiry_date')
    
    # Son yenileme işlemleri
    recent_renewals = CertificateRenewal.objects.all().order_by('-renewal_date')[:5]
    
    # Son bildirimler
    recent_notifications = CertificateNotification.objects.filter(
        acknowledged=False
    ).order_by('-sent_date')[:5]
    
    return render(request, 'certificate_management/dashboard.html', {
        'total_certificates': total_certificates,
        'active_certificates': active_certificates,
        'expired_certificates': expired_certificates,
        'revoked_certificates': revoked_certificates,
        'pending_certificates': pending_certificates,
        'expiring_soon': expiring_soon,
        'recent_renewals': recent_renewals,
        'recent_notifications': recent_notifications,
    })

# Sertifika Türü görünümleri
@login_required
def certificate_type_list(request):
    """Sertifika türleri listesi görünümü"""
    certificate_types = CertificateType.objects.all().order_by('name')
    return render(request, 'certificate_management/certificate_type_list.html', {
        'certificate_types': certificate_types
    })

@login_required
def certificate_type_create(request):
    """Sertifika türü oluşturma görünümü"""
    if request.method == 'POST':
        form = CertificateTypeForm(request.POST)
        if form.is_valid():
            certificate_type = form.save()
            messages.success(request, f'{certificate_type.name} sertifika türü başarıyla oluşturuldu!')
            return redirect('certificate_type_list')
    else:
        form = CertificateTypeForm()
    
    return render(request, 'certificate_management/certificate_type_form.html', {
        'form': form,
        'action': 'Oluştur'
    })

@login_required
def certificate_type_update(request, type_id):
    """Sertifika türü güncelleme görünümü"""
    certificate_type = get_object_or_404(CertificateType, id=type_id)
    
    if request.method == 'POST':
        form = CertificateTypeForm(request.POST, instance=certificate_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'{certificate_type.name} sertifika türü başarıyla güncellendi!')
            return redirect('certificate_type_list')
    else:
        form = CertificateTypeForm(instance=certificate_type)
    
    return render(request, 'certificate_management/certificate_type_form.html', {
        'form': form,
        'certificate_type': certificate_type,
        'action': 'Güncelle'
    })

@login_required
def certificate_type_delete(request, type_id):
    """Sertifika türü silme görünümü"""
    certificate_type = get_object_or_404(CertificateType, id=type_id)
    
    if request.method == 'POST':
        type_name = certificate_type.name
        certificate_type.delete()
        messages.success(request, f'{type_name} sertifika türü başarıyla silindi!')
        return redirect('certificate_type_list')
    
    return render(request, 'certificate_management/certificate_type_confirm_delete.html', {
        'certificate_type': certificate_type
    })

# Sertifika görünümleri
@login_required
def certificate_list(request):
    """Sertifika listesi görünümü"""
    filter_form = CertificateFilterForm(request.GET)
    certificates = Certificate.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['name']:
            certificates = certificates.filter(name__icontains=filter_form.cleaned_data['name'])
        if filter_form.cleaned_data['domain_name']:
            certificates = certificates.filter(domain_name__icontains=filter_form.cleaned_data['domain_name'])
        if filter_form.cleaned_data['certificate_type']:
            certificates = certificates.filter(certificate_type=filter_form.cleaned_data['certificate_type'])
        if filter_form.cleaned_data['status']:
            certificates = certificates.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['issuer']:
            certificates = certificates.filter(issuer__icontains=filter_form.cleaned_data['issuer'])
        if filter_form.cleaned_data['expiring_in_days']:
            days = filter_form.cleaned_data['expiring_in_days']
            target_date = timezone.now().date() + timezone.timedelta(days=days)
            certificates = certificates.filter(
                status='active',
                expiry_date__lte=target_date
            )
    
    certificates = certificates.order_by('-expiry_date')
    
    # Sertifikaların durumlarını güncelle
    for certificate in certificates:
        certificate.update_status()
    
    return render(request, 'certificate_management/certificate_list.html', {
        'certificates': certificates,
        'filter_form': filter_form
    })

@login_required
def certificate_detail(request, certificate_id):
    """Sertifika detay görünümü"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    certificate.update_status()  # Durumu güncelle
    
    renewals = certificate.renewals.all().order_by('-renewal_date')
    notifications = certificate.notifications.all().order_by('-sent_date')
    
    return render(request, 'certificate_management/certificate_detail.html', {
        'certificate': certificate,
        'renewals': renewals,
        'notifications': notifications
    })

@login_required
def certificate_create(request):
    """Sertifika oluşturma görünümü"""
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.created_by = request.user
            certificate.save()
            messages.success(request, f'{certificate.name} sertifikası başarıyla oluşturuldu!')
            return redirect('certificate_detail', certificate_id=certificate.id)
    else:
        form = CertificateForm()
    
    return render(request, 'certificate_management/certificate_form.html', {
        'form': form,
        'action': 'Oluştur'
    })

@login_required
def certificate_update(request, certificate_id):
    """Sertifika güncelleme görünümü"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, f'{certificate.name} sertifikası başarıyla güncellendi!')
            return redirect('certificate_detail', certificate_id=certificate.id)
    else:
        form = CertificateForm(instance=certificate)
    
    return render(request, 'certificate_management/certificate_form.html', {
        'form': form,
        'certificate': certificate,
        'action': 'Güncelle'
    })

@login_required
def certificate_delete(request, certificate_id):
    """Sertifika silme görünümü"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        certificate_name = certificate.name
        certificate.delete()
        messages.success(request, f'{certificate_name} sertifikası başarıyla silindi!')
        return redirect('certificate_list')
    
    return render(request, 'certificate_management/certificate_confirm_delete.html', {
        'certificate': certificate
    })

# Sertifika Yenileme görünümleri
@login_required
def certificate_renewal_list(request):
    """Sertifika yenileme listesi görünümü"""
    filter_form = CertificateRenewalFilterForm(request.GET)
    renewals = CertificateRenewal.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['certificate_name']:
            search_term = filter_form.cleaned_data['certificate_name']
            renewals = renewals.filter(certificate__name__icontains=search_term)
        if filter_form.cleaned_data['status']:
            renewals = renewals.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['renewal_date_from']:
            renewals = renewals.filter(renewal_date__gte=filter_form.cleaned_data['renewal_date_from'])
        if filter_form.cleaned_data['renewal_date_to']:
            renewals = renewals.filter(renewal_date__lte=filter_form.cleaned_data['renewal_date_to'])
    
    renewals = renewals.order_by('-renewal_date')
    
    return render(request, 'certificate_management/certificate_renewal_list.html', {
        'renewals': renewals,
        'filter_form': filter_form
    })

@login_required
def certificate_renewal_create(request, certificate_id=None):
    """Sertifika yenileme oluşturma görünümü"""
    certificate = None
    if certificate_id:
        certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        form = CertificateRenewalForm(request.POST)
        if form.is_valid():
            renewal = form.save(commit=False)
            renewal.old_expiry_date = renewal.certificate.expiry_date
            renewal.renewed_by = request.user
            renewal.save()
            
            # Sertifikanın geçerlilik tarihini güncelle
            if renewal.status == 'completed' and renewal.new_expiry_date:
                certificate = renewal.certificate
                certificate.expiry_date = renewal.new_expiry_date
                certificate.status = 'active'  # Yenilenen sertifika aktif olur
                certificate.save()
            
            messages.success(request, 'Sertifika yenileme işlemi başarıyla kaydedildi!')
            return redirect('certificate_detail', certificate_id=renewal.certificate.id)
    else:
        initial_data = {}
        if certificate:
            initial_data['certificate'] = certificate
        
        form = CertificateRenewalForm(initial=initial_data)
    
    return render(request, 'certificate_management/certificate_renewal_form.html', {
        'form': form,
        'certificate': certificate,
        'action': 'Oluştur'
    })

@login_required
def certificate_renewal_update(request, renewal_id):
    """Sertifika yenileme güncelleme görünümü"""
    renewal = get_object_or_404(CertificateRenewal, id=renewal_id)
    certificate = renewal.certificate
    
    if request.method == 'POST':
        form = CertificateRenewalForm(request.POST, instance=renewal)
        if form.is_valid():
            updated_renewal = form.save()
            
            # Sertifikanın geçerlilik tarihini güncelle
            if updated_renewal.status == 'completed' and updated_renewal.new_expiry_date:
                certificate.expiry_date = updated_renewal.new_expiry_date
                certificate.status = 'active'  # Yenilenen sertifika aktif olur
                certificate.save()
            
            messages.success(request, 'Sertifika yenileme işlemi başarıyla güncellendi!')
            return redirect('certificate_detail', certificate_id=certificate.id)
    else:
        form = CertificateRenewalForm(instance=renewal)
    
    return render(request, 'certificate_management/certificate_renewal_form.html', {
        'form': form,
        'renewal': renewal,
        'certificate': certificate,
        'action': 'Güncelle'
    })

# Sertifika Bildirimi görünümleri
@login_required
def certificate_notification_list(request):
    """Sertifika bildirimleri listesi görünümü"""
    notifications = CertificateNotification.objects.all().order_by('-sent_date')
    return render(request, 'certificate_management/certificate_notification_list.html', {
        'notifications': notifications
    })

@login_required
def certificate_notification_create(request, certificate_id=None):
    """Sertifika bildirimi oluşturma görünümü"""
    certificate = None
    if certificate_id:
        certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        form = CertificateNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save()
            messages.success(request, 'Sertifika bildirimi başarıyla oluşturuldu!')
            return redirect('certificate_detail', certificate_id=notification.certificate.id)
    else:
        initial_data = {}
        if certificate:
            initial_data['certificate'] = certificate
            
            # Sertifikanın durumuna göre bildirim türü öner
            if certificate.status == 'expired':
                initial_data['notification_type'] = 'expired'
                initial_data['message'] = f"{certificate.name} sertifikasının süresi dolmuştur. Lütfen en kısa sürede yenileyin."
            elif certificate.is_expiring_soon():
                initial_data['notification_type'] = 'expiry_warning'
                days_left = certificate.days_until_expiry()
                initial_data['message'] = f"{certificate.name} sertifikasının süresinin dolmasına {days_left} gün kaldı. Lütfen yenileme işlemlerini başlatın."
        
        form = CertificateNotificationForm(initial=initial_data)
    
    return render(request, 'certificate_management/certificate_notification_form.html', {
        'form': form,
        'certificate': certificate,
        'action': 'Oluştur'
    })

@login_required
def certificate_notification_acknowledge(request, notification_id):
    """Sertifika bildirimini onaylama görünümü"""
    notification = get_object_or_404(CertificateNotification, id=notification_id)
    
    if request.method == 'POST':
        notification.acknowledge(request.user)
        messages.success(request, 'Bildirim başarıyla onaylandı!')
        return redirect('certificate_notification_list')
    
    return render(request, 'certificate_management/certificate_notification_acknowledge.html', {
        'notification': notification
    })