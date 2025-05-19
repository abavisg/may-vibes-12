// Request notification permission on page load
document.addEventListener('DOMContentLoaded', async () => {
    if (Notification.permission !== 'granted') {
        await Notification.requestPermission();
    }
    
    // Start periodic updates
    updateStatus();
    updateCalendar();
    setInterval(updateStatus, 5000);  // Update every 5 seconds
    setInterval(updateCalendar, 300000);  // Update calendar every 5 minutes
});

// Format duration in HH:MM format
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}:${minutes.toString().padStart(2, '0')}`;
}

// Format datetime to relative time
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMinutes = Math.floor((date - now) / (1000 * 60));
    
    if (diffMinutes < 60) {
        return `${diffMinutes} minutes ago`;
    } else if (diffMinutes < 1440) {
        const hours = Math.floor(diffMinutes / 60);
        return `${hours} hours ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Update progress bar with appropriate color
function updateProgressBar(elementId, value) {
    const progressBar = document.getElementById(elementId);
    progressBar.style.width = `${value}%`;
    
    // Remove existing classes
    progressBar.classList.remove('warning', 'danger');
    
    // Add appropriate class based on value
    if (value >= 90) {
        progressBar.classList.add('danger');
    } else if (value >= 75) {
        progressBar.classList.add('warning');
    }
}

// Update status information
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update working time and last break
        document.getElementById('workingTime').textContent = formatDuration(data.active_duration);
        document.getElementById('lastBreak').textContent = formatRelativeTime(data.last_break);
        document.getElementById('idleTime').textContent = formatDuration(data.idle_duration);
        
        // Update system stats
        document.getElementById('cpuUsage').textContent = `${Math.round(data.system_stats.cpu_percent)}%`;
        document.getElementById('memoryUsage').textContent = `${Math.round(data.system_stats.memory_percent)}%`;
        
        // Update progress bars
        updateProgressBar('cpuBar', data.system_stats.cpu_percent);
        updateProgressBar('memoryBar', data.system_stats.memory_percent);
        
        // Update status indicator
        const statusDot = document.querySelector('.status-indicator .dot');
        statusDot.style.backgroundColor = data.is_active ? 'var(--success-color)' : 'var(--warning-color)';
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

// Update calendar events
async function updateCalendar() {
    try {
        const response = await fetch('/api/calendar');
        const data = await response.json();
        
        const eventsList = document.getElementById('eventsList');
        eventsList.innerHTML = '';
        
        if (data.events && data.events.length > 0) {
            data.events.forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.className = 'event-item';
                eventElement.innerHTML = `
                    <div class="event-details">
                        <div class="event-title">${event.summary}</div>
                        <div class="event-time">${new Date(event.start).toLocaleTimeString()}</div>
                    </div>
                `;
                eventsList.appendChild(eventElement);
            });
        } else {
            eventsList.innerHTML = '<div class="no-events">No upcoming events</div>';
        }
    } catch (error) {
        console.error('Failed to update calendar:', error);
        document.getElementById('eventsList').innerHTML = '<div class="error">Failed to load events</div>';
    }
}

// Handle taking a break
async function takeBreak() {
    try {
        await fetch('/api/take-break', {
            method: 'POST'
        });
        
        // Hide notification if visible
        document.getElementById('notification').classList.add('hidden');
        
        // Update status immediately
        updateStatus();
    } catch (error) {
        console.error('Failed to record break:', error);
    }
}

// Handle postponing a break
function postponeBreak() {
    document.getElementById('notification').classList.add('hidden');
}

// Show break notification
function showBreakNotification(message, duration) {
    const notification = document.getElementById('notification');
    const messageElement = document.getElementById('notificationMessage');
    
    messageElement.textContent = message;
    notification.classList.remove('hidden');
    
    // Also show system notification if permitted
    if (Notification.permission === 'granted') {
        new Notification('Work/Life Balance Coach', {
            body: message,
            icon: '/static/img/icon.png'
        });
    }
}

// Add event listeners for buttons
document.getElementById('takeBreak').addEventListener('click', takeBreak);
document.getElementById('postponeBreak').addEventListener('click', postponeBreak); 