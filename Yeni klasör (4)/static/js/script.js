/**
 * BMW Middleware Portal - Main JavaScript
 */

// Document Ready Function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar menu functionality
    initSidebar();
    
    // Initialize dropdown menus
    initDropdowns();
    
    // Initialize theme switching
    initThemeSwitch();
});

/**
 * Initialize sidebar functionality
 */
function initSidebar() {
    // Collapse/expand sidebar when trigger is clicked
    const trigger = document.querySelector('.trigger');
    if (trigger) {
        trigger.addEventListener('click', function() {
            const sider = document.querySelector('.ant-layout-sider');
            const layout = document.querySelector('.ant-layout');
            
            if (sider) {
                sider.classList.toggle('ant-layout-sider-collapsed');
            }
            
            if (layout) {
                layout.classList.toggle('ant-layout-has-collapsed-sider');
            }
        });
    }
    
    // Initialize submenu toggles
    const submenuTitles = document.querySelectorAll('.ant-menu-submenu-title');
    submenuTitles.forEach(function(title) {
        title.addEventListener('click', function() {
            const submenu = this.parentNode;
            const submenuList = submenu.querySelector('.ant-menu-sub');
            
            if (submenu && submenuList) {
                submenu.classList.toggle('ant-menu-submenu-open');
                
                // Toggle submenu visibility with animation
                if (submenuList.style.maxHeight) {
                    submenuList.style.maxHeight = null;
                } else {
                    submenuList.style.maxHeight = submenuList.scrollHeight + "px";
                }
            }
        });
    });
}

/**
 * Initialize dropdown menus
 */
function initDropdowns() {
    // User dropdown toggle
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        userDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
            const dropdown = this.querySelector('.ant-dropdown');
            if (dropdown) {
                dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function() {
            const dropdowns = document.querySelectorAll('.ant-dropdown');
            dropdowns.forEach(function(dropdown) {
                dropdown.style.display = 'none';
            });
        });
    }
    
    // Alert close buttons
    const alertCloseButtons = document.querySelectorAll('.ant-alert-close-icon');
    alertCloseButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const alert = this.closest('.ant-alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.style.display = 'none';
                }, 300);
            }
        });
    });
}

/**
 * Initialize theme switching functionality
 */
function initThemeSwitch() {
    const themeSwitch = document.querySelector('.theme-switch');
    if (themeSwitch) {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('bmw-portal-theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            const icon = themeSwitch.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        }
        
        // Theme switch click handler
        themeSwitch.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const icon = this.querySelector('i');
            
            if (document.body.classList.contains('dark-theme')) {
                localStorage.setItem('bmw-portal-theme', 'dark');
                if (icon) {
                    icon.classList.remove('fa-sun');
                    icon.classList.add('fa-moon');
                }
            } else {
                localStorage.setItem('bmw-portal-theme', 'light');
                if (icon) {
                    icon.classList.remove('fa-moon');
                    icon.classList.add('fa-sun');
                }
            }
        });
    }
}

/**
 * Create a notification message
 * @param {string} message - The notification message
 * @param {string} type - The type of notification (success, info, warning, error)
 */
function showNotification(message, type = 'info') {
    const notifications = document.createElement('div');
    notifications.className = 'ant-notification';
    notifications.style.position = 'fixed';
    notifications.style.top = '16px';
    notifications.style.right = '16px';
    notifications.style.zIndex = '1010';
    
    const notification = document.createElement('div');
    notification.className = `ant-notification-notice ant-notification-notice-${type}`;
    notification.style.padding = '16px 24px';
    notification.style.lineHeight = '1.5';
    notification.style.marginBottom = '16px';
    notification.style.backgroundColor = '#fff';
    notification.style.boxShadow = '0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 9px 28px 8px rgba(0, 0, 0, 0.05)';
    notification.style.borderRadius = '2px';
    notification.style.overflow = 'hidden';
    
    const content = document.createElement('div');
    content.className = 'ant-notification-notice-content';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'ant-notification-notice-message';
    messageDiv.textContent = message;
    
    const closeBtn = document.createElement('a');
    closeBtn.className = 'ant-notification-notice-close';
    closeBtn.innerHTML = '<i class="fas fa-times"></i>';
    closeBtn.addEventListener('click', function() {
        document.body.removeChild(notifications);
    });
    
    content.appendChild(messageDiv);
    notification.appendChild(content);
    notification.appendChild(closeBtn);
    notifications.appendChild(notification);
    
    document.body.appendChild(notifications);
    
    // Auto-dismiss after 4.5 seconds
    setTimeout(function() {
        if (document.body.contains(notifications)) {
            document.body.removeChild(notifications);
        }
    }, 4500);
}

/**
 * Handle form submissions with AJAX
 * @param {HTMLFormElement} form - The form element
 * @param {Function} successCallback - Callback function on successful submission
 */
function handleFormSubmit(form, successCallback) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const url = form.getAttribute('action');
        const method = form.getAttribute('method') || 'POST';
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification(data.message || 'İşlem başarıyla tamamlandı', 'success');
                if (typeof successCallback === 'function') {
                    successCallback(data);
                }
            } else {
                showNotification(data.message || 'İşlem sırasında bir hata oluştu', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('İşlem sırasında bir hata oluştu', 'error');
        });
    });
}