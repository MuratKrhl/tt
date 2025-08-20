from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse

from .models import CustomUser, Department, UserActivity, UserPermissionRequest, UserNotification
from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, CustomUserChangeForm, CustomPasswordChangeForm,
    ProfileUpdateForm, DepartmentForm, UserPermissionRequestForm, UserPermissionRequestProcessForm,
    UserNotificationForm, UserFilterForm, DepartmentFilterForm, UserPermissionRequestFilterForm
)

# Yardımcı fonksiyonlar
def is_admin_or_manager(user):
    """Kullanıcının yönetici veya müdür olup olmadığını kontrol eder"""
    return user.is_authenticated and user.user_type in ['admin', 'manager']

def record_user_activity(user, activity_type, description, request=None, related_model=None, related_object_id=None):
    """Kullanıcı aktivitesini kaydeder"""
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        related_model=related_model,
        related_object_id=related_object_id
    )

# Giriş ve kimlik doğrulama görünümleri
def user_login(request):
    """Kullanıcı giriş görünümü"""
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Giriş aktivitesini kaydet
            user.record_login(request.META.get('REMOTE_ADDR'))
            record_user_activity(user, 'login', 'Kullanıcı sisteme giriş yaptı', request)
            
            # Şifre değişikliği gerekiyorsa yönlendir
            if user.require_password_change:
                messages.warning(request, 'Şifrenizi değiştirmeniz gerekmektedir.')
                return redirect('password_change')
            
            # Okunmamış bildirim kontrolü
            unread_count = UserNotification.objects.filter(user=user, is_read=False).count()
            if unread_count > 0:
                messages.info(request, f'{unread_count} okunmamış bildiriminiz var.')
            
            return redirect('user_dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'user_management/login.html', {'form': form})

@login_required
def user_logout(request):
    """Kullanıcı çıkış görünümü"""
    record_user_activity(request.user, 'logout', 'Kullanıcı sistemden çıkış yaptı', request)
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız.')
    return redirect('login')

@login_required
def password_change(request):
    """Şifre değiştirme görünümü"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Oturumu güncelle
            
            # Şifre değişikliği bilgilerini güncelle
            user.password_changed_at = timezone.now()
            user.require_password_change = False
            user.save(update_fields=['password_changed_at', 'require_password_change'])
            
            # Aktiviteyi kaydet
            record_user_activity(user, 'password_change', 'Kullanıcı şifresini değiştirdi', request)
            
            messages.success(request, 'Şifreniz başarıyla değiştirildi!')
            return redirect('user_dashboard')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'user_management/password_change.html', {'form': form})

# Kullanıcı profil görünümleri
@login_required
def user_dashboard(request):
    """Kullanıcı dashboard görünümü"""
    # Kullanıcı bilgileri
    user = request.user
    
    # Okunmamış bildirimler
    unread_notifications = UserNotification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
    
    # Son aktiviteler
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
    
    # İzin talepleri
    permission_requests = UserPermissionRequest.objects.filter(user=user).order_by('-requested_at')[:5]
    
    # Yöneticiler için ek bilgiler
    pending_permission_requests = None
    department_stats = None
    if is_admin_or_manager(user):
        # Bekleyen izin talepleri
        pending_permission_requests = UserPermissionRequest.objects.filter(status='pending').order_by('-requested_at')[:5]
        
        # Departman istatistikleri
        if user.user_type == 'admin':
            department_stats = Department.objects.annotate(member_count=Count('members'))
        elif user.department:
            department_stats = Department.objects.filter(id=user.department.id).annotate(member_count=Count('members'))
    
    return render(request, 'user_management/dashboard.html', {
        'user': user,
        'unread_notifications': unread_notifications,
        'recent_activities': recent_activities,
        'permission_requests': permission_requests,
        'pending_permission_requests': pending_permission_requests,
        'department_stats': department_stats,
    })

@login_required
def profile_view(request):
    """Kullanıcı profil görünümü"""
    user = request.user
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]
    
    return render(request, 'user_management/profile.html', {
        'user': user,
        'activities': activities,
    })

@login_required
def profile_edit(request):
    """Kullanıcı profil düzenleme görünümü"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            record_user_activity(request.user, 'profile_update', 'Kullanıcı profilini güncelledi', request)
            messages.success(request, 'Profiliniz başarıyla güncellendi!')
            return redirect('profile_view')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'user_management/profile_edit.html', {'form': form})

# Kullanıcı yönetimi görünümleri
@user_passes_test(is_admin_or_manager)
def user_list(request):
    """Kullanıcı listesi görünümü"""
    filter_form = UserFilterForm(request.GET)
    users = CustomUser.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['username']:
            users = users.filter(username__icontains=filter_form.cleaned_data['username'])
        if filter_form.cleaned_data['name']:
            name_query = filter_form.cleaned_data['name']
            users = users.filter(Q(first_name__icontains=name_query) | Q(last_name__icontains=name_query))
        if filter_form.cleaned_data['email']:
            users = users.filter(email__icontains=filter_form.cleaned_data['email'])
        if filter_form.cleaned_data['user_type']:
            users = users.filter(user_type=filter_form.cleaned_data['user_type'])
        if filter_form.cleaned_data['department']:
            users = users.filter(department=filter_form.cleaned_data['department'])
        if filter_form.cleaned_data['is_active'] is not None:
            users = users.filter(is_active=filter_form.cleaned_data['is_active'])
        if filter_form.cleaned_data['is_active_employee'] is not None:
            users = users.filter(is_active_employee=filter_form.cleaned_data['is_active_employee'])
    
    # Yöneticiler sadece kendi departmanlarındaki kullanıcıları görebilir
    if request.user.user_type == 'manager' and request.user.department:
        users = users.filter(department=request.user.department)
    
    users = users.order_by('username')
    
    return render(request, 'user_management/user_list.html', {
        'users': users,
        'filter_form': filter_form
    })

@user_passes_test(is_admin_or_manager)
def user_detail(request, user_id):
    """Kullanıcı detay görünümü"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    # Yöneticiler sadece kendi departmanlarındaki kullanıcıları görebilir
    if request.user.user_type == 'manager' and request.user.department:
        if user_obj.department != request.user.department:
            messages.error(request, 'Bu kullanıcıyı görüntüleme yetkiniz yok.')
            return redirect('user_list')
    
    activities = UserActivity.objects.filter(user=user_obj).order_by('-timestamp')[:10]
    permission_requests = UserPermissionRequest.objects.filter(user=user_obj).order_by('-requested_at')[:5]
    
    return render(request, 'user_management/user_detail.html', {
        'user_obj': user_obj,
        'activities': activities,
        'permission_requests': permission_requests,
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def user_create(request):
    """Kullanıcı oluşturma görünümü"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            record_user_activity(
                request.user, 
                'data_modification', 
                f'Yeni kullanıcı oluşturuldu: {user.username}', 
                request,
                'CustomUser',
                user.id
            )
            messages.success(request, f'{user.username} kullanıcısı başarıyla oluşturuldu!')
            return redirect('user_detail', user_id=user.id)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'user_management/user_form.html', {
        'form': form,
        'action': 'Oluştur'
    })

@user_passes_test(is_admin_or_manager)
def user_update(request, user_id):
    """Kullanıcı güncelleme görünümü"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    # Yöneticiler sadece kendi departmanlarındaki kullanıcıları düzenleyebilir
    if request.user.user_type == 'manager' and request.user.department:
        if user_obj.department != request.user.department:
            messages.error(request, 'Bu kullanıcıyı düzenleme yetkiniz yok.')
            return redirect('user_list')
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            record_user_activity(
                request.user, 
                'data_modification', 
                f'Kullanıcı güncellendi: {user_obj.username}', 
                request,
                'CustomUser',
                user_obj.id
            )
            messages.success(request, f'{user_obj.username} kullanıcısı başarıyla güncellendi!')
            return redirect('user_detail', user_id=user_obj.id)
    else:
        form = CustomUserChangeForm(instance=user_obj)
    
    return render(request, 'user_management/user_form.html', {
        'form': form,
        'user_obj': user_obj,
        'action': 'Güncelle'
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def user_delete(request, user_id):
    """Kullanıcı silme görünümü"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        record_user_activity(
            request.user, 
            'data_modification', 
            f'Kullanıcı silindi: {username}', 
            request,
            'CustomUser'
        )
        messages.success(request, f'{username} kullanıcısı başarıyla silindi!')
        return redirect('user_list')
    
    return render(request, 'user_management/user_confirm_delete.html', {
        'user_obj': user_obj
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def reset_user_password(request, user_id):
    """Kullanıcı şifresini sıfırlama görünümü"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        # Rastgele şifre oluştur
        import random
        import string
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Şifreyi güncelle ve değişiklik gerektir
        user_obj.set_password(temp_password)
        user_obj.require_password_change = True
        user_obj.save(update_fields=['password', 'require_password_change'])
        
        record_user_activity(
            request.user, 
            'password_change', 
            f'Kullanıcı şifresi sıfırlandı: {user_obj.username}', 
            request,
            'CustomUser',
            user_obj.id
        )
        
        messages.success(request, f'{user_obj.username} kullanıcısının şifresi sıfırlandı. Geçici şifre: {temp_password}')
        return redirect('user_detail', user_id=user_obj.id)
    
    return render(request, 'user_management/reset_password_confirm.html', {
        'user_obj': user_obj
    })

# Departman yönetimi görünümleri
@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def department_list(request):
    """Departman listesi görünümü"""
    filter_form = DepartmentFilterForm(request.GET)
    departments = Department.objects.all()
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['name']:
            departments = departments.filter(name__icontains=filter_form.cleaned_data['name'])
        if filter_form.cleaned_data['manager']:
            departments = departments.filter(manager=filter_form.cleaned_data['manager'])
    
    # Üye sayısını hesapla
    departments = departments.annotate(member_count=Count('members'))
    departments = departments.order_by('name')
    
    return render(request, 'user_management/department_list.html', {
        'departments': departments,
        'filter_form': filter_form
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def department_detail(request, department_id):
    """Departman detay görünümü"""
    department = get_object_or_404(Department, id=department_id)
    members = CustomUser.objects.filter(department=department).order_by('username')
    
    return render(request, 'user_management/department_detail.html', {
        'department': department,
        'members': members
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def department_create(request):
    """Departman oluşturma görünümü"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            record_user_activity(
                request.user, 
                'data_modification', 
                f'Yeni departman oluşturuldu: {department.name}', 
                request,
                'Department',
                department.id
            )
            messages.success(request, f'{department.name} departmanı başarıyla oluşturuldu!')
            return redirect('department_detail', department_id=department.id)
    else:
        form = DepartmentForm()
    
    return render(request, 'user_management/department_form.html', {
        'form': form,
        'action': 'Oluştur'
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def department_update(request, department_id):
    """Departman güncelleme görünümü"""
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            record_user_activity(
                request.user, 
                'data_modification', 
                f'Departman güncellendi: {department.name}', 
                request,
                'Department',
                department.id
            )
            messages.success(request, f'{department.name} departmanı başarıyla güncellendi!')
            return redirect('department_detail', department_id=department.id)
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'user_management/department_form.html', {
        'form': form,
        'department': department,
        'action': 'Güncelle'
    })

@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def department_delete(request, department_id):
    """Departman silme görünümü"""
    department = get_object_or_404(Department, id=department_id)
    
    # Departmanda üye varsa silme işlemi yapılmamalı
    member_count = CustomUser.objects.filter(department=department).count()
    if member_count > 0 and request.method != 'POST':
        messages.warning(request, f'Bu departmanda {member_count} üye bulunuyor. Silmeden önce üyeleri başka departmanlara taşıyın.')
    
    if request.method == 'POST':
        department_name = department.name
        department.delete()
        record_user_activity(
            request.user, 
            'data_modification', 
            f'Departman silindi: {department_name}', 
            request,
            'Department'
        )
        messages.success(request, f'{department_name} departmanı başarıyla silindi!')
        return redirect('department_list')
    
    return render(request, 'user_management/department_confirm_delete.html', {
        'department': department,
        'member_count': member_count
    })

# İzin talebi görünümleri
@login_required
def permission_request_list(request):
    """İzin talepleri listesi görünümü"""
    filter_form = UserPermissionRequestFilterForm(request.GET)
    
    # Yönetici veya müdür ise tüm talepleri görebilir
    if is_admin_or_manager(request.user):
        permission_requests = UserPermissionRequest.objects.all()
        
        # Yönetici sadece kendi departmanındaki kullanıcıların taleplerini görebilir
        if request.user.user_type == 'manager' and request.user.department:
            permission_requests = permission_requests.filter(user__department=request.user.department)
    else:
        # Normal kullanıcı sadece kendi taleplerini görebilir
        permission_requests = UserPermissionRequest.objects.filter(user=request.user)
    
    if filter_form.is_valid():
        if filter_form.cleaned_data['user'] and is_admin_or_manager(request.user):
            permission_requests = permission_requests.filter(user=filter_form.cleaned_data['user'])
        if filter_form.cleaned_data['status']:
            permission_requests = permission_requests.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['requested_from']:
            permission_requests = permission_requests.filter(
                requested_at__date__gte=filter_form.cleaned_data['requested_from']
            )
        if filter_form.cleaned_data['requested_to']:
            permission_requests = permission_requests.filter(
                requested_at__date__lte=filter_form.cleaned_data['requested_to']
            )
    
    permission_requests = permission_requests.order_by('-requested_at')
    
    return render(request, 'user_management/permission_request_list.html', {
        'permission_requests': permission_requests,
        'filter_form': filter_form,
        'is_admin_or_manager': is_admin_or_manager(request.user)
    })

@login_required
def permission_request_create(request):
    """İzin talebi oluşturma görünümü"""
    if request.method == 'POST':
        form = UserPermissionRequestForm(request.POST)
        if form.is_valid():
            permission_request = form.save(commit=False)
            permission_request.user = request.user
            permission_request.save()
            
            record_user_activity(
                request.user, 
                'data_access', 
                f'İzin talebi oluşturuldu: {permission_request.permission.name}', 
                request,
                'UserPermissionRequest',
                permission_request.id
            )
            
            messages.success(request, 'İzin talebiniz başarıyla oluşturuldu!')
            return redirect('permission_request_list')
    else:
        form = UserPermissionRequestForm()
    
    return render(request, 'user_management/permission_request_form.html', {
        'form': form
    })

@user_passes_test(is_admin_or_manager)
def permission_request_process(request, request_id):
    """İzin talebi işleme görünümü"""
    permission_request = get_object_or_404(UserPermissionRequest, id=request_id)
    
    # Yönetici sadece kendi departmanındaki kullanıcıların taleplerini işleyebilir
    if request.user.user_type == 'manager' and request.user.department:
        if permission_request.user.department != request.user.department:
            messages.error(request, 'Bu talebi işleme yetkiniz yok.')
            return redirect('permission_request_list')
    
    if permission_request.status != 'pending':
        messages.warning(request, 'Bu talep zaten işlenmiş.')
        return redirect('permission_request_list')
    
    if request.method == 'POST':
        form = UserPermissionRequestProcessForm(request.POST)
        if form.is_valid():
            action = request.POST.get('action')
            note = form.cleaned_data['response_note']
            
            if action == 'approve':
                permission_request.approve(request.user, note)
                record_user_activity(
                    request.user, 
                    'permission_change', 
                    f'İzin talebi onaylandı: {permission_request.permission.name} - {permission_request.user.username}', 
                    request,
                    'UserPermissionRequest',
                    permission_request.id
                )
                messages.success(request, 'İzin talebi onaylandı!')
            elif action == 'reject':
                permission_request.reject(request.user, note)
                record_user_activity(
                    request.user, 
                    'permission_change', 
                    f'İzin talebi reddedildi: {permission_request.permission.name} - {permission_request.user.username}', 
                    request,
                    'UserPermissionRequest',
                    permission_request.id
                )
                messages.success(request, 'İzin talebi reddedildi!')
            
            # Kullanıcıya bildirim gönder
            UserNotification.objects.create(
                user=permission_request.user,
                title='İzin Talebi Güncellendi',
                message=f'İzin talebiniz {permission_request.get_status_display().lower()}. {note}',
                notification_type='info',
                priority='medium',
                related_url=reverse('permission_request_list')
            )
            
            return redirect('permission_request_list')
    else:
        form = UserPermissionRequestProcessForm()
    
    return render(request, 'user_management/permission_request_process.html', {
        'form': form,
        'permission_request': permission_request
    })

# Bildirim görünümleri
@login_required
def notification_list(request):
    """Bildirim listesi görünümü"""
    notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'user_management/notification_list.html', {
        'notifications': notifications
    })

@login_required
def notification_mark_read(request, notification_id):
    """Bildirimi okundu olarak işaretleme görünümü"""
    notification = get_object_or_404(UserNotification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notification_list')

@login_required
def notification_mark_all_read(request):
    """Tüm bildirimleri okundu olarak işaretleme görünümü"""
    UserNotification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    messages.success(request, 'Tüm bildirimler okundu olarak işaretlendi!')
    return redirect('notification_list')

@user_passes_test(is_admin_or_manager)
def notification_create(request):
    """Bildirim oluşturma görünümü"""
    if request.method == 'POST':
        form = UserNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save()
            messages.success(request, 'Bildirim başarıyla oluşturuldu!')
            return redirect('user_detail', user_id=notification.user.id)
    else:
        # URL parametresinden kullanıcı ID'si alınırsa
        user_id = request.GET.get('user_id')
        initial_data = {}
        
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                initial_data['user'] = user
            except CustomUser.DoesNotExist:
                pass
        
        form = UserNotificationForm(initial=initial_data)
    
    return render(request, 'user_management/notification_form.html', {
        'form': form
    })

# Aktivite görünümleri
@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'admin')
def activity_list(request):
    """Aktivite listesi görünümü"""
    activities = UserActivity.objects.all().order_by('-timestamp')[:100]
    
    return render(request, 'user_management/activity_list.html', {
        'activities': activities
    })