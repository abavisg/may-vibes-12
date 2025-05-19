// Main application class
class WorkLifeBalanceApp {
    constructor() {
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeWebSocket();
        this.requestNotificationPermission();
        this.updateInterval = null;
        this.startPeriodicUpdates();
    }

    initializeElements() {
        // Wellness score elements
        this.scoreValue = document.querySelector('.score-value');
        this.scoreComponents = document.querySelectorAll('.progress[data-component]');
        this.suggestionsList = document.getElementById('wellnessSuggestions');

        // Stats elements
        this.workingTime = document.getElementById('workingTime');
        this.lastBreak = document.getElementById('lastBreak');
        this.breaksTaken = document.getElementById('breaksTaken');
        this.breaksSuggested = document.getElementById('breaksSuggested');
        this.meetingsAttended = document.getElementById('meetingsAttended');
        this.totalMeetings = document.getElementById('totalMeetings');

        // System stats elements
        this.cpuBar = document.getElementById('cpuBar');
        this.cpuUsage = document.getElementById('cpuUsage');
        this.memoryBar = document.getElementById('memoryBar');
        this.memoryUsage = document.getElementById('memoryUsage');

        // Calendar elements
        this.eventsList = document.getElementById('eventsList');

        // Notification elements
        this.notification = document.getElementById('notification');
        this.notificationMessage = document.getElementById('notificationMessage');
    }

    initializeEventListeners() {
        // Break buttons
        document.getElementById('takeBreak').addEventListener('click', () => this.handleBreak(true));
        document.getElementById('postponeBreak').addEventListener('click', () => this.handleBreak(false));

        // Notification buttons
        document.getElementById('notificationAccept').addEventListener('click', () => this.handleNotification(true));
        document.getElementById('notificationDismiss').addEventListener('click', () => this.handleNotification(false));
    }

    async initializeWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
            });
            
            this.socket.on('dashboard_update', (data) => {
                this.handleWebSocketMessage({
                    data: JSON.stringify(data)
                });
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                setTimeout(() => this.initializeWebSocket(), 1000);
            });
        } catch (error) {
            console.error('Socket.IO connection failed:', error);
            setTimeout(() => this.initializeWebSocket(), 1000);
        }
    }

    async requestNotificationPermission() {
        try {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
        }
    }

    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => this.fetchDashboardData(), 30000);
        this.fetchDashboardData(); // Initial fetch
    }

    async fetchDashboardData() {
        try {
            const response = await fetch('/api/dashboard');
            const data = await response.json();
            this.updateDashboard(data);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    }

    updateDashboard(data) {
        // Update wellness score
        this.scoreValue.textContent = Math.round(data.wellness_score.current_score);

        // Update score components
        this.scoreComponents.forEach(component => {
            const name = component.dataset.component;
            const value = data.wellness_score.components[name];
            component.style.width = `${value}%`;
        });

        // Update suggestions
        this.suggestionsList.innerHTML = data.wellness_score.suggestions
            .map(suggestion => `<li>${suggestion}</li>`)
            .join('');

        // Update system stats
        this.updateSystemStats(data.activity_stats);

        // Update calendar events
        this.updateCalendarEvents(data.calendar_events);

        // Update break stats
        this.updateBreakStats(data.break_stats);
    }

    updateSystemStats(stats) {
        this.cpuBar.style.width = `${stats.cpu_percent}%`;
        this.cpuUsage.textContent = `${Math.round(stats.cpu_percent)}%`;
        this.memoryBar.style.width = `${stats.memory_percent}%`;
        this.memoryUsage.textContent = `${Math.round(stats.memory_percent)}%`;
    }

    updateCalendarEvents(events) {
        this.eventsList.innerHTML = events.map(event => `
            <div class="event-item ${event.status}">
                <span class="event-time">${event.start_time} - ${event.end_time}</span>
                <span class="event-title">${event.title}</span>
            </div>
        `).join('');
    }

    updateBreakStats(stats) {
        this.breaksTaken.textContent = stats.taken;
        this.breaksSuggested.textContent = stats.suggested;
        this.meetingsAttended.textContent = stats.meetings_attended;
        this.totalMeetings.textContent = stats.total_meetings;
        this.workingTime.textContent = this.formatDuration(stats.working_time);
        this.lastBreak.textContent = this.formatLastBreak(stats.last_break);
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}:${minutes.toString().padStart(2, '0')}`;
    }

    formatLastBreak(timestamp) {
        if (!timestamp) return 'No breaks yet';
        const minutes = Math.floor((Date.now() - timestamp) / 60000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        return `${Math.floor(minutes / 60)}h ${minutes % 60}m ago`;
    }

    async handleBreak(accepted) {
        try {
            const response = await fetch('/api/breaks/respond', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ accepted })
            });
            const result = await response.json();
            this.showNotification(result.message);
        } catch (error) {
            console.error('Error handling break response:', error);
        }
    }

    handleWebSocketMessage(event) {
        const data = JSON.parse(event.data);
        switch (data.type) {
            case 'break_suggestion':
                this.showBreakSuggestion(data.suggestion);
                break;
            case 'dashboard_update':
                this.updateDashboard(data.data);
                break;
            case 'notification':
                this.showNotification(data.message);
                break;
        }
    }

    showBreakSuggestion(suggestion) {
        this.showNotification(
            `Time for a ${suggestion.title}! ${suggestion.activity}`,
            true
        );
        if (Notification.permission === 'granted') {
            new Notification('Break Suggestion', {
                body: suggestion.activity,
                icon: '/static/img/icon.png'
            });
        }
    }

    showNotification(message, isBreak = false) {
        this.notificationMessage.textContent = message;
        this.notification.classList.remove('hidden');
        if (!isBreak) {
            setTimeout(() => this.notification.classList.add('hidden'), 5000);
        }
    }

    handleNotification(accepted) {
        this.notification.classList.add('hidden');
        if (accepted) {
            this.handleBreak(true);
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WorkLifeBalanceApp();
}); 