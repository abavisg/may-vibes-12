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

// Format time in 12-hour format with AM/PM
function formatEventTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

// Check if an event is currently happening
function isEventActive(event) {
    const now = new Date();
    const start = new Date(event.start);
    const end = new Date(event.end);
    return now >= start && now <= end;
}

// Get relative time description
function getEventTiming(event) {
    const now = new Date();
    const start = new Date(event.start);
    const end = new Date(event.end);
    
    if (now < start) {
        const diffMinutes = Math.round((start - now) / (1000 * 60));
        if (diffMinutes < 60) {
            return `Starting in ${diffMinutes} minutes`;
        }
        const diffHours = Math.round(diffMinutes / 60);
        return `Starting in ${diffHours} hours`;
    } else if (now <= end) {
        const diffMinutes = Math.round((end - now) / (1000 * 60));
        if (diffMinutes < 60) {
            return `Ending in ${diffMinutes} minutes`;
        }
        const diffHours = Math.round(diffMinutes / 60);
        return `Ending in ${diffHours} hours`;
    } else {
        return 'Ended';
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
            data.events.sort((a, b) => new Date(a.start) - new Date(b.start));
            
            data.events.forEach(event => {
                const startTime = formatEventTime(event.start);
                const endTime = formatEventTime(event.end);
                const isActive = isEventActive(event);
                const timing = getEventTiming(event);
                
                const eventElement = document.createElement('div');
                eventElement.className = `event-item ${isActive ? 'active' : ''}`;
                eventElement.innerHTML = `
                    <div class="event-status ${isActive ? 'active' : ''}">
                        <div class="status-dot"></div>
                        <div class="status-text">${timing}</div>
                    </div>
                    <div class="event-details">
                        <div class="event-title">${event.summary}</div>
                        <div class="event-time">${startTime} - ${endTime}</div>
                        ${event.location ? `<div class="event-location"><i class="fas fa-map-marker-alt"></i> ${event.location}</div>` : ''}
                        ${event.description ? `<div class="event-description">${event.description}</div>` : ''}
                        ${event.attendees && event.attendees.length > 0 ? 
                            `<div class="event-attendees">
                                <i class="fas fa-users"></i> ${event.attendees.length} attendee${event.attendees.length > 1 ? 's' : ''}
                            </div>` : ''
                        }
                    </div>
                `;
                eventsList.appendChild(eventElement);
            });
            
            console.log('Calendar updated with events:', data.events);
        } else {
            eventsList.innerHTML = '<div class="no-events">No events scheduled for today</div>';
            console.log('No upcoming events found');
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
    
    // Auto-hide notification after 10 seconds
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 10000);
    
    // Also show system notification if permitted
    if (Notification.permission === 'granted') {
        new Notification('Work/Life Balance Coach', {
            body: message,
            icon: '/static/img/icon.png'
        });
    }
}

// Add event listeners for buttons
document.addEventListener('DOMContentLoaded', () => {
    const takeBreakBtn = document.getElementById('takeBreak');
    const postponeBreakBtn = document.getElementById('postponeBreak');
    
    takeBreakBtn.addEventListener('click', async () => {
        try {
            await takeBreak();
            showBreakNotification('Enjoy your break! Take time to stretch and relax.');
        } catch (error) {
            console.error('Failed to start break:', error);
        }
    });
    
    postponeBreakBtn.addEventListener('click', () => {
        document.getElementById('notification').classList.add('hidden');
    });
    
    // Request notification permission
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
    
    // Start periodic updates
    updateStatus();
    updateCalendar();
    setInterval(updateStatus, 5000);  // Update every 5 seconds
    setInterval(updateCalendar, 300000);  // Update calendar every 5 minutes
}); 