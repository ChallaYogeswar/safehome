/**
 * Notifications & Firebase Cloud Messaging (FCM) Client
 * Handles permission requests, token registration, and incoming messages
 */

// firebase-config usually comes from a global variable or fetch
// For this implementation, we'll assume firebase is available globally via CDN
// or initialized in base.html. If not, we'll check for it.

const VAPID_KEY = 'YOUR_VAPID_PUBLIC_KEY'; // Replace with actual key from Firebase Console

document.addEventListener('DOMContentLoaded', () => {
    if (typeof firebase === 'undefined') {
        console.warn('Firebase SDK not loaded - notifications disabled');
        return;
    }

    // Initialize formatting for timestamps
    const timeFormatter = new Intl.DateTimeFormat('en-US', {
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    });

    // Check notification permission
    if (Notification.permission === 'granted') {
        initializeMessaging();
    } else if (Notification.permission !== 'denied') {
        showPermissionRequest();
    }
});

function showPermissionRequest() {
    const banner = document.createElement('div');
    banner.id = 'notification-banner';
    banner.className = 'alert alert-info alert-dismissible fade show fixed-top m-3 shadow-lg';
    banner.style.zIndex = '9999';
    banner.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-bell-fill me-2 fs-4"></i>
            <div>
                <strong>Enable Notifications?</strong>
                <p class="mb-0 small">Get real-time alerts when someone is at your door.</p>
            </div>
            <button class="btn btn-primary btn-sm ms-auto me-2" id="enable-notifs-btn">Enable</button>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.body.appendChild(banner);

    document.getElementById('enable-notifs-btn').addEventListener('click', () => {
        requestPermission();
        banner.remove();
    });
}

async function requestPermission() {
    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            initializeMessaging();
            showToast('success', 'Notifications enabled!');
        } else {
            console.warn('Notification permission denied');
        }
    } catch (error) {
        console.error('Error requesting notification permission:', error);
    }
}

async function initializeMessaging() {
    try {
        const messaging = firebase.messaging();

        // Handle incoming messages when app is in foreground
        messaging.onMessage((payload) => {
            console.log('Message received. ', payload);
            showForegroundNotification(payload);

            // Refresh entries list if on entries page
            if (window.location.pathname.includes('/entries')) {
                if (typeof loadEntries === 'function') loadEntries();
            }
            // Refresh dashboard stats if on dashboard
            if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
                if (typeof updateDashboard === 'function') updateDashboard();
            }
        });

        // Get and register token
        const token = await messaging.getToken({ vapidKey: VAPID_KEY });
        if (token) {
            registerToken(token);
        } else {
            console.warn('No registration token available. Request permission to generate one.');
        }

    } catch (error) {
        console.error('Firebase messaging initialization failed:', error);
    }
}

async function registerToken(token) {
    try {
        const response = await fetch('/notifications/register-device', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                token: token,
                device_type: 'web',
                device_name: navigator.userAgent
            })
        });

        const data = await response.json();
        if (data.success) {
            console.log('Device token registered:', data.device_id);
        } else {
            console.error('Token registration failed:', data.message);
        }
    } catch (error) {
        console.error('Error registering token:', error);
    }
}

function showForegroundNotification(payload) {
    const { title, body, image } = payload.notification || {};
    const data = payload.data || {};

    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast show position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '10000';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    // Determine icon and color based on type
    let iconClass = 'bi-info-circle';
    let headerClass = 'text-primary';

    if (data.type === 'entry_alert') {
        const isKnown = data.is_known === 'True';
        iconClass = isKnown ? 'bi-person-check' : 'bi-person-exclamation';
        headerClass = isKnown ? 'text-success' : 'text-danger';
    } else if (data.type === 'door_action') {
        iconClass = data.action === 'door_opened' ? 'bi-door-open' : 'bi-door-closed';
        headerClass = data.action === 'door_opened' ? 'text-success' : 'text-danger';
    }

    toast.innerHTML = `
        <div class="toast-header">
            <i class="bi ${iconClass} ${headerClass} me-2"></i>
            <strong class="me-auto">${title || 'Notification'}</strong>
            <small class="text-muted">Just now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${image ? `<img src="${image}" class="img-fluid mb-2 rounded" alt="Notification image">` : ''}
            <p class="mb-0">${body || ''}</p>
            ${data.action_required === 'True' ? `
                <div class="mt-2 pt-2 border-top">
                    <a href="/entries" class="btn btn-sm btn-primary w-100">Review Entry</a>
                </div>
            ` : ''}
        </div>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 60000); // Keep alerts longer (1 min) so user doesn't miss them
}

// Utility function to show standard toasts (reused from other files if needed)
function showToast(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';
    const toast = document.createElement('div');
    toast.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);';
    toast.innerHTML = `<i class="bi ${icon}"></i> ${message} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
