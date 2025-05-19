// Main application class
class WorkLifeBalanceApp {
    constructor() {
        this.initialized = false;
        this.initAttempts = 0;
        this.maxInitAttempts = 5;
        
        // Ensure Socket.IO is loaded
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded. Waiting...');
            setTimeout(() => this.initialize(), 500);
            return;
        }
        
        this.initialize();
    }

    initialize() {
        if (this.initialized) return;
        this.initAttempts++;
        
        console.log(`Initialization attempt ${this.initAttempts}...`);
        
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
            return;
        }
        
        if (!this.initializeElements()) {
            if (this.initAttempts < this.maxInitAttempts) {
                console.warn(`Failed to initialize elements. Retrying in 1 second... (Attempt ${this.initAttempts}/${this.maxInitAttempts})`);
                setTimeout(() => this.initialize(), 1000);
            } else {
                console.error('Failed to initialize after maximum attempts');
            }
            return;
        }
        
        try {
            this.initializeEventListeners();
            this.initializeWebSocket();
            this.requestNotificationPermission();
            this.updateInterval = null;
            this.startPeriodicUpdates();
            this.startDateTimeUpdates();
            
            this.initialized = true;
            console.log('Application initialized successfully');
        } catch (error) {
            console.error('Error during initialization:', error);
        }
    }

    initializeElements() {
        console.log('Initializing elements...');
        
        // Date and time elements
        this.currentDate = document.getElementById('currentDate');
        this.currentTime = document.getElementById('currentTime');
        this.mockModeIndicator = document.getElementById('mockModeIndicator');
        this.systemStatus = document.getElementById('systemStatus');

        // Check if all required elements are found
        const requiredElements = {
            currentDate: this.currentDate,
            currentTime: this.currentTime,
            mockModeIndicator: this.mockModeIndicator,
            systemStatus: this.systemStatus
        };

        const missingElements = Object.entries(requiredElements)
            .filter(([_, element]) => !element)
            .map(([name]) => name);

        if (missingElements.length > 0) {
            console.error('Missing required elements:', missingElements);
            return false;
        }

        // Initialize other elements
        this.scoreValue = document.querySelector('.score-value');
        this.scoreComponents = document.querySelectorAll('.progress[data-component]');
        this.suggestionsList = document.getElementById('wellnessSuggestions');
        this.workingTime = document.getElementById('workingTime');
        this.lastBreak = document.getElementById('lastBreak');
        this.breaksTaken = document.getElementById('breaksTaken');
        this.breaksSuggested = document.getElementById('breaksSuggested');
        this.meetingsAttended = document.getElementById('meetingsAttended');
        this.totalMeetings = document.getElementById('totalMeetings');
        this.cpuBar = document.getElementById('cpuBar');
        this.cpuUsage = document.getElementById('cpuUsage');
        this.memoryBar = document.getElementById('memoryBar');
        this.memoryUsage = document.getElementById('memoryUsage');
        this.eventsList = document.getElementById('eventsList');
        this.notification = document.getElementById('notification');
        this.notificationMessage = document.getElementById('notificationMessage');
        
        // Initialize agent countdown elements
        this.countdownTimer = document.getElementById('countdownTimer');
        this.countdownProgress = document.getElementById('countdownProgress');
        this.completedCycles = document.getElementById('completedCycles');
        this.agentCountdown = document.getElementById('agentCountdown');
        
        // Initialize countdown interval
        this.countdownInterval = null;
        this.nextRunTime = null;
        this.intervalDuration = 300; // default to 300 seconds (5 minutes), will be updated from server

        return true;
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
        console.log('Initializing WebSocket...');
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected successfully');
                // Request initial data
                this.fetchDashboardData();
            });
            
            this.socket.on('dashboard_update', (data) => {
                console.log('Received dashboard update:', data);
                this.handleWebSocketMessage({
                    data: JSON.stringify(data)
                });
            });
            
            this.socket.on('disconnect', () => {
                console.warn('WebSocket disconnected, attempting reconnection...');
                setTimeout(() => this.initializeWebSocket(), 1000);
            });

            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
            });
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
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
        console.log('Fetching dashboard data...');
        try {
            const response = await fetch('/api/dashboard');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Received dashboard data:', data);
            
            // Check if scheduler info is present and has a valid next_run_at
            if (data && data.scheduler_info && data.scheduler_info.next_run_at) {
                console.log('Next run scheduled at:', new Date(data.scheduler_info.next_run_at * 1000).toLocaleString());
            } else {
                console.warn('Missing or invalid scheduler information in response');
            }
            
            this.updateDashboard(data);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            // Retry after a short delay if fetch failed
            setTimeout(() => this.fetchDashboardData(), 5000);
        }
    }

    updateDashboard(data) {
        console.log('Updating dashboard with data:', data);
        if (!data) return;

        // Update system info
        const systemInfo = data.system_info || {};
        console.log('System info:', systemInfo);
        
        // Update mock mode indicator
        const mockIndicator = document.getElementById('mockIndicator');
        if (mockIndicator) {
            const isMockMode = !!systemInfo.mock_mode;
            console.log('Setting mock mode:', isMockMode);
            
            // Update text and style based on mock mode status
            mockIndicator.querySelector('span').textContent = `Mock Mode: ${isMockMode ? 'True' : 'False'}`;
            
            if (isMockMode) {
                mockIndicator.style.backgroundColor = '#ffc107'; // Yellow for mock mode
                mockIndicator.style.color = '#000';
            } else {
                mockIndicator.style.backgroundColor = '#6c757d'; // Gray for real mode
                mockIndicator.style.color = 'white';
            }
        }

        if (this.systemStatus) {
            this.systemStatus.textContent = systemInfo.is_active ? 'System Active' : 'System Idle';
        }
        
        // Update LLM status
        this.updateLlmStatus(systemInfo.llm_status);
        
        // Update date/time directly from server data if available
        if (systemInfo.formatted_date && systemInfo.formatted_time) {
            const dateElement = document.getElementById('currentDate');
            const timeElement = document.getElementById('currentTime');
            
            if (dateElement) {
                dateElement.textContent = systemInfo.formatted_date;
                console.log('Updated date from server:', systemInfo.formatted_date);
            }
            
            if (timeElement) {
                timeElement.textContent = systemInfo.formatted_time;
                console.log('Updated time from server:', systemInfo.formatted_time);
            }
        } 
        // Fallback to client-side date formatting if server data not available
        else if (systemInfo.mock_mode && systemInfo.current_time) {
            console.log('Using mock time:', systemInfo.current_time);
            const mockDate = new Date(systemInfo.current_time);
            if (!isNaN(mockDate.getTime())) {
                this.updateDateTimeDisplay(mockDate);
            }
        } else {
            console.log('Using real time');
            this.updateDateTime();
        }

        // Update wellness score
        if (this.scoreValue && data.wellness_score) {
            this.scoreValue.textContent = Math.round(data.wellness_score.current_score);
        }

        // Update score components
        this.scoreComponents.forEach(component => {
            const name = component.dataset.component;
            const value = data.wellness_score.components[name] || 0;
            component.style.width = `${value}%`;
        });

        // Update suggestions
        this.suggestionsList.innerHTML = data.wellness_score.suggestions
            .map(suggestion => `<li>${suggestion}</li>`)
            .join('') || '<li>No suggestions available</li>';

        // Update system stats
        const cpuPercent = Math.round(data.activity_stats.cpu_percent);
        const memoryPercent = Math.round(data.activity_stats.memory_percent);
        
        this.cpuBar.style.width = `${cpuPercent}%`;
        this.cpuUsage.textContent = `${cpuPercent}%`;
        this.memoryBar.style.width = `${memoryPercent}%`;
        this.memoryUsage.textContent = `${memoryPercent}%`;

        // Update calendar events
        this.updateCalendarEvents(data.calendar_events);

        // Update break stats
        const breakStats = data.break_stats;
        this.breaksTaken.textContent = breakStats.taken;
        this.breaksSuggested.textContent = breakStats.suggested;
        this.workingTime.textContent = this.formatDuration(breakStats.working_time);
        this.lastBreak.textContent = this.formatLastBreak(breakStats.last_break);

        // Update meeting stats
        const meetingStats = data.meeting_stats;
        this.meetingsAttended.textContent = `${meetingStats.attended} / ${meetingStats.total}`;

        // Update scheduler countdown
        this.updateAgentCountdown(data.scheduler_info);
    }

    formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}:${minutes.toString().padStart(2, '0')}`;
    }

    formatLastBreak(timestamp) {
        if (!timestamp) return 'No breaks yet';
        try {
            const breakTime = new Date(timestamp);
            const now = new Date();
            const minutes = Math.floor((now - breakTime) / 60000);
            
            if (minutes < 1) return 'Just now';
            if (minutes < 60) return `${minutes}m ago`;
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            return `${hours}h ${remainingMinutes}m ago`;
        } catch (error) {
            console.error('Error formatting break time:', error);
            return 'No breaks yet';
        }
    }

    formatEventTime(time) {
        try {
            const date = new Date(time);
            return date.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
        } catch (error) {
            console.error('Error formatting event time:', error);
            return time;
        }
    }

    getEventStatus(event) {
        const now = new Date();
        const start = new Date(event.start);
        const end = new Date(event.end);

        if (end < now) return 'past';
        if (start <= now && end >= now) return 'current';
        return 'upcoming';
    }

    updateCalendarEvents(events) {
        if (!events) {
            this.eventsList.innerHTML = '<div class="event-item">Loading events...</div>';
            return;
        }
        
        if (!Array.isArray(events) || events.length === 0) {
            this.eventsList.innerHTML = '<div class="event-item">No events scheduled</div>';
            return;
        }

        this.eventsList.innerHTML = events.map(event => {
            const status = this.getEventStatus(event);
            const startTime = this.formatEventTime(event.start);
            const endTime = this.formatEventTime(event.end);
            
            return `
                <div class="event-item ${status} ${event.summary.toLowerCase().includes('break') ? 'break' : ''}">
                    <span class="event-title">${event.summary}</span>
                    <span class="event-time">${startTime} - ${endTime}</span>
                </div>
            `;
        }).join('');
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
        
        // Add timestamp to the notification
        const notificationTime = document.getElementById('notificationTime');
        if (notificationTime) {
            const now = new Date();
            notificationTime.textContent = `Suggested at ${now.toLocaleTimeString()}`;
            notificationTime.setAttribute('title', now.toLocaleString());
        }
        
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

    startDateTimeUpdates() {
        // Check if we're in mock mode
        if (this.mockModeIndicator && !this.mockModeIndicator.classList.contains('hidden')) {
            console.log('Mock mode detected, skipping client-side datetime updates');
            return; // Skip client-side datetime updates if in mock mode
        }
        
        // Only update time if not in mock mode
        this.updateDateTime();
        setInterval(() => this.updateDateTime(), 1000);
    }

    updateDateTime() {
        // Don't update datetime if in mock mode
        if (document.querySelector('.fa-vial') && 
            !document.querySelector('.fa-vial').closest('div').classList.contains('hidden')) {
            console.log('Mock mode detected, skipping client-side datetime update');
            return;
        }
        
        const now = new Date();
        console.log('Updating date/time with:', now);
        this.updateDateTimeDisplay(now);
    }

    updateDateTimeDisplay(date) {
        if (!date) {
            console.error('No date provided to updateDateTimeDisplay');
            return;
        }
        
        try {
            if (this.currentDate) {
                this.currentDate.textContent = date.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            } else {
                console.error('currentDate element not found');
            }
            
            if (this.currentTime) {
                this.currentTime.textContent = date.toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                });
            } else {
                console.error('currentTime element not found');
            }
        } catch (error) {
            console.error('Error updating date/time display:', error);
        }
    }

    updateLlmStatus(llmStatus) {
        const llmStatusElement = document.getElementById('llmStatus');
        if (!llmStatusElement) return;
        
        if (!llmStatus) {
            llmStatusElement.innerHTML = `
                <i class="fas fa-brain"></i>
                <span>LLM: Unknown</span>
            `;
            llmStatusElement.style.backgroundColor = '#6c757d';
            return;
        }
        
        const isAvailable = llmStatus.is_available;
        
        if (isAvailable) {
            const model = llmStatus.model || 'Unknown';
            const modelSize = llmStatus.model_size || '';
            const lastSuggestion = llmStatus.last_suggestion ? 
                new Date(llmStatus.last_suggestion) : null;
            
            let suggestionTime = 'Never';
            if (lastSuggestion) {
                const minutes = Math.floor((new Date() - lastSuggestion) / 60000);
                suggestionTime = minutes < 1 ? 'Just now' : `${minutes}m ago`;
            }
            
            llmStatusElement.innerHTML = `
                <i class="fas fa-brain"></i>
                <span title="Last suggestion: ${suggestionTime}">LLM: ${model.split(':')[0]} ${modelSize}</span>
            `;
            llmStatusElement.style.backgroundColor = '#28a745';
            
            // Update the Last Run indicator
            this.updateLlmLastRun(llmStatus.last_check);
        } else {
            llmStatusElement.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span>LLM: Unavailable</span>
            `;
            llmStatusElement.style.backgroundColor = '#dc3545';
        }
    }
    
    updateLlmLastRun(lastCheckTime) {
        const llmLastRunElement = document.getElementById('llmLastRun');
        if (!llmLastRunElement) return;
        
        if (!lastCheckTime) {
            llmLastRunElement.innerHTML = `
                <i class="fas fa-history"></i>
                <span>Last run: Never</span>
            `;
            return;
        }
        
        try {
            const lastCheck = new Date(lastCheckTime);
            const now = new Date();
            const secondsAgo = Math.floor((now - lastCheck) / 1000);
            
            let timeString = 'Just now';
            if (secondsAgo >= 60) {
                const minutesAgo = Math.floor(secondsAgo / 60);
                timeString = `${minutesAgo}m ago`;
                
                if (minutesAgo >= 60) {
                    const hoursAgo = Math.floor(minutesAgo / 60);
                    timeString = `${hoursAgo}h ago`;
                }
            } else if (secondsAgo > 5) {
                timeString = `${secondsAgo}s ago`;
            }
            
            llmLastRunElement.innerHTML = `
                <i class="fas fa-history"></i>
                <span title="${lastCheck.toLocaleString()}">Last run: ${timeString}</span>
            `;
        } catch (error) {
            console.error('Error updating LLM last run time:', error);
            llmLastRunElement.innerHTML = `
                <i class="fas fa-history"></i>
                <span>Last run: Unknown</span>
            `;
        }
    }

    updateAgentCountdown(schedulerInfo) {
        if (!schedulerInfo || !this.countdownTimer || !this.countdownProgress || !this.completedCycles) {
            console.warn('Missing scheduler info or countdown elements');
            return;
        }
        
        // Update completed cycles
        if (this.completedCycles) {
            this.completedCycles.textContent = schedulerInfo.runs_completed || 0;
        }
        
        // Clear any existing countdown interval
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        // Get the next run time
        const nextRunAt = schedulerInfo.next_run_at;
        if (!nextRunAt) {
            this.countdownTimer.textContent = "00:00";
            this.countdownProgress.style.width = "0%";
            return;
        }
        
        // Set the next run time and update interval duration from server
        this.nextRunTime = nextRunAt;
        
        // Update the interval duration if we have frequency information
        if (schedulerInfo.frequency_seconds) {
            this.intervalDuration = schedulerInfo.frequency_seconds;
            console.log(`Updated interval duration from server frequency: ${this.intervalDuration} seconds`);
            
            // Display interval information
            const intervalDisplay = document.getElementById('intervalDisplay');
            if (intervalDisplay) {
                const minutes = Math.floor(this.intervalDuration / 60);
                const seconds = Math.floor(this.intervalDuration % 60);
                intervalDisplay.textContent = `(interval: ${minutes}m ${seconds > 0 ? seconds + 's' : ''})`;
            }
        }
        // Fallback to calculating from time_remaining if frequency not provided
        else if (schedulerInfo.time_remaining) {
            const totalRemainingSeconds = schedulerInfo.time_remaining.minutes * 60 + schedulerInfo.time_remaining.seconds;
            // Store the full cycle interval for progress calculation (assuming we're at the start of a cycle)
            if (totalRemainingSeconds > 0) {
                this.intervalDuration = totalRemainingSeconds;
                console.log(`Updated interval duration from time remaining: ${this.intervalDuration} seconds`);
            }
        }
        
        // Start a countdown that updates every second
        this.countdownInterval = setInterval(() => {
            const now = Math.floor(Date.now() / 1000);
            const timeRemaining = Math.max(0, this.nextRunTime - now);
            
            if (timeRemaining <= 0) {
                // If time is up, clear the interval and wait for the next update
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
                this.countdownTimer.textContent = "00:00";
                this.countdownProgress.style.width = "0%";
                
                // Make it blink when at zero
                this.agentCountdown.classList.add('pulse');
                setTimeout(() => {
                    this.agentCountdown.classList.remove('pulse');
                }, 5000);
                
                // Request a fresh update to get the new next run time
                console.log("Timer reached zero, requesting fresh data...");
                setTimeout(() => {
                    this.fetchDashboardData();
                }, 2000); // Wait 2 seconds to allow the backend to complete its cycle
                
                return;
            }
            
            // Format the remaining time as MM:SS (no milliseconds)
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = Math.floor(timeRemaining % 60);
            this.countdownTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // Calculate progress bar width (0-100%)
            const elapsedTime = this.intervalDuration - timeRemaining;
            const elapsedPercent = Math.min(100, (elapsedTime / this.intervalDuration) * 100);
            this.countdownProgress.style.width = `${elapsedPercent}%`;
            
            // Change color based on remaining time
            if (timeRemaining < 30) {
                this.countdownTimer.style.color = '#dc3545'; // Red for imminent
                this.countdownProgress.style.backgroundColor = '#dc3545';
            } else if (timeRemaining < 60) {
                this.countdownTimer.style.color = '#fd7e14'; // Orange for soon
                this.countdownProgress.style.backgroundColor = '#fd7e14';
            } else {
                this.countdownTimer.style.color = '#4a90e2'; // Blue for normal
                this.countdownProgress.style.backgroundColor = '#4a90e2';
            }
        }, 1000);
        
        // Run it once immediately to set initial values
        const now = Math.floor(Date.now() / 1000);
        const timeRemaining = Math.max(0, this.nextRunTime - now);
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = Math.floor(timeRemaining % 60);
        this.countdownTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Add a CSS class for the pulse animation
function addStyleToHead() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .pulse {
            animation: pulse 1s infinite;
        }
    `;
    document.head.appendChild(style);
}

// Initialize the application
let app;
function initApp() {
    console.log('Initializing application...');
    addStyleToHead();
    app = new WorkLifeBalanceApp();
    window.app = app; // Export for debugging
}

// Start the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', initApp); 