const socket = io('/alerts');

socket.on('connect', function() {
    console.log('Connected to alerts WebSocket');
});

socket.on('connected', function(data) {
    console.log(data.message);
});

socket.on('new_alert', function(data) {
    console.log('New alert received:', data);
    showAlertNotification(data);
    updateUnreadCount();
});

socket.on('disconnect', function() {
    console.log('Disconnected from alerts WebSocket');
});

function showAlertNotification(alert) {
    const severityClass = {
        'low': 'info',
        'medium': 'warning',
        'high': 'warning',
        'critical': 'danger'
    }[alert.severity] || 'info';
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${severityClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 70px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <strong>${alert.title}</strong><br>
        ${alert.message}<br>
        <small class="text-muted">${new Date(alert.created_at).toLocaleTimeString()}</small>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(alert.title, {
            body: alert.message,
            icon: '/static/icon.png',
            tag: `alert-${alert.id}`
        });
    }
    
    setTimeout(() => {
        notification.remove();
    }, 10000);
}

async function updateUnreadCount() {
    try {
        const response = await fetch('/alerts/unread');
        const data = await response.json();
        
        if (data.success) {
            const badge = document.getElementById('unread-count');
            if (badge) {
                if (data.alerts.length > 0) {
                    badge.textContent = data.alerts.length;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}

if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

updateUnreadCount();
setInterval(updateUnreadCount, 30000);
