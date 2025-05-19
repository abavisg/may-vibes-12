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

// Update wellness score visualization
function updateWellnessScore(wellnessData) {
    // Update main score
    const scoreValue = document.querySelector('.score-value');
    scoreValue.textContent = Math.round(wellnessData.current_score);
    
    // Update trend
    const trendIcon = document.querySelector('.score-trend i');
    const trendText = document.querySelector('.score-trend span');
    
    trendIcon.className = 'fas';
    switch (wellnessData.trend) {
        case 'improving':
            trendIcon.classList.add('fa-arrow-up');
            trendText.textContent = 'Improving';
            break;
        case 'declining':
            trendIcon.classList.add('fa-arrow-down');
            trendText.textContent = 'Declining';
            break;
        default:
            trendIcon.classList.add('fa-arrow-right');
            trendText.textContent = 'Stable';
    }
    
    // Update component scores
    Object.entries(wellnessData.components).forEach(([component, value]) => {
        const progressBar = document.querySelector(`[data-component="${component}"]`);
        if (progressBar) {
            progressBar.style.width = `${value}%`;
            if (value < 70) {
                progressBar.classList.add('warning');
            } else if (value < 50) {
                progressBar.classList.add('danger');
            }
        }
    });
    
    // Update suggestions
    const suggestionsList = document.getElementById('wellnessSuggestions');
    suggestionsList.innerHTML = wellnessData.suggestions
        .map(suggestion => `<li>${suggestion}</li>`)
        .join('');
}

// Update status information
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update working time and last break
        document.getElementById('workingTime').textContent = formatDuration(data.active_duration);
        document.getElementById('lastBreak').textContent = formatRelativeTime(data.last_break);
        
        // Update break stats
        document.getElementById('breaksTaken').textContent = data.break_stats.taken;
        document.getElementById('breaksSuggested').textContent = data.break_stats.suggested;
        
        // Update meeting stats
        document.getElementById('meetingsAttended').textContent = data.meeting_stats.attended;
        document.getElementById('totalMeetings').textContent = data.meeting_stats.total;
        
        // Update system stats
        document.getElementById('cpuUsage').textContent = `${Math.round(data.system_stats.cpu_percent)}%`;
        document.getElementById('memoryUsage').textContent = `${Math.round(data.system_stats.memory_percent)}%`;
        
        // Update progress bars
        updateProgressBar('cpuBar', data.system_stats.cpu_percent);
        updateProgressBar('memoryBar', data.system_stats.memory_percent);
        
        // Update wellness score
        if (data.wellness_score) {
            updateWellnessScore(data.wellness_score);
        }
        
        // Update status indicator
        const statusDot = document.querySelector('.status-indicator .dot');
        statusDot.style.backgroundColor = data.is_active ? 'var(--success-color)' : 'var(--warning-color)';
        
        // Show break notification if needed
        if (data.break_suggestion) {
            showBreakNotification(data.break_suggestion.message, data.break_suggestion.duration);
        }
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

// Get event status class
function getEventStatusClass(event) {
    const now = new Date();
    const start = new Date(event.start);
    const end = new Date(event.end);
    
    if (now < start) return 'upcoming';
    if (now > end) return 'past';
    return 'current';
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
                const statusClass = getEventStatusClass(event);
                const timing = getEventTiming(event);
                
                const eventElement = document.createElement('div');
                eventElement.className = `event-card ${statusClass}`;
                eventElement.innerHTML = `
                    <div class="event-time">${startTime} - ${endTime}</div>
                    <div class="event-details">
                        <div class="event-title">${event.summary}</div>
                        <div class="event-status">${timing}</div>
                        ${event.location ? `<div class="event-location"><i class="fas fa-map-marker-alt"></i> ${event.location}</div>` : ''}
                    </div>
                `;
                eventsList.appendChild(eventElement);
            });
        } else {
            eventsList.innerHTML = '<div class="no-events">No events scheduled for today</div>';
        }
    } catch (error) {
        console.error('Failed to update calendar:', error);
        document.getElementById('eventsList').innerHTML = '<div class="error">Failed to load events</div>';
    }
}

// Handle taking a break
async function takeBreak(breakType = 'stretch_break') {
    try {
        const response = await fetch('/api/take-break', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                break_type: breakType,
                accepted: true,
                completed: true
            })
        });
        
        if (response.ok) {
            // Hide notification if visible
            document.getElementById('notification').classList.add('hidden');
            // Update status immediately
            updateStatus();
        }
    } catch (error) {
        console.error('Failed to record break:', error);
    }
}

// Handle skipping a break
async function skipBreak(breakType = 'stretch_break') {
    try {
        await fetch('/api/skip-break', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                break_type: breakType
            })
        });
        
        document.getElementById('notification').classList.add('hidden');
        updateStatus();
    } catch (error) {
        console.error('Failed to skip break:', error);
    }
}

// Show break notification
function showBreakNotification(message, duration, breakType = 'stretch_break') {
    const notification = document.getElementById('notification');
    const messageElement = document.getElementById('notificationMessage');
    
    messageElement.textContent = message;
    notification.classList.remove('hidden');
    
    // Store break type for use in accept/dismiss actions
    notification.dataset.breakType = breakType;
    
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
    const notificationAcceptBtn = document.getElementById('notificationAccept');
    const notificationDismissBtn = document.getElementById('notificationDismiss');
    
    takeBreakBtn.addEventListener('click', () => takeBreak());
    postponeBreakBtn.addEventListener('click', () => skipBreak());
    
    notificationAcceptBtn.addEventListener('click', () => {
        const notification = document.getElementById('notification');
        const breakType = notification.dataset.breakType || 'stretch_break';
        takeBreak(breakType);
    });
    
    notificationDismissBtn.addEventListener('click', () => {
        const notification = document.getElementById('notification');
        const breakType = notification.dataset.breakType || 'stretch_break';
        skipBreak(breakType);
    });
    
    // Request notification permission
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
}); 