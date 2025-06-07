// Session Handler Module
const SessionHandler = {
    // Session state
    currentSession: null,
    sessionHistory: [],
    
    // Initialize session handler
    init() {
        this.loadSessionHistory();
        this.setupEventListeners();
    },

    // Load session history from storage
    loadSessionHistory() {
        try {
            const savedHistory = sessionStorage.getItem('roseTrackerSessionHistory');
            if (savedHistory) {
                this.sessionHistory = JSON.parse(savedHistory);
                this.updateSessionHistoryTable();
            }
        } catch (e) {
            console.warn('Could not load session history from sessionStorage:', e);
        }
    },

    // Save session history to storage
    saveSessionHistory() {
        try {
            sessionStorage.setItem('roseTrackerSessionHistory', JSON.stringify(this.sessionHistory));
        } catch (e) {
            console.warn('Could not save session history to sessionStorage:', e);
        }
    },

    // Update session history table
    updateSessionHistoryTable() {
        const tbody = document.getElementById('sessionHistoryBody');
        if (!tbody) return;

        tbody.innerHTML = '';  // Clear existing rows

        this.sessionHistory.forEach((session, index) => {
            const row = document.createElement('tr');
            row.className = 'session-row';
            if (index === this.sessionHistory.length - 1) {
                row.classList.add('new-session');
            }

            row.innerHTML = `
                <td>${session.session_number}</td>
                <td>${this.formatDuration(session.duration)}</td>
                <td>${session.session_unique_roses}</td>
                <td>${session.total_unique_roses}</td>
                <td>${session.final_count}</td>
                <td>${session.average_fps.toFixed(1)}</td>
                <td>${session.total_frames_processed}</td>
            `;
            tbody.appendChild(row);
        });
    },

    // Format duration in minutes and seconds
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}m ${secs}s`;
    },

    // Add a new session to history
    addSession(sessionStats) {
        if (!sessionStats) return;
        
        this.sessionHistory.push(sessionStats);
        this.updateSessionHistoryTable();
        this.saveSessionHistory();
        
        // Log detailed session information
        console.log('Session Statistics:', {
            session_number: sessionStats.session_number,
            session_unique_roses: sessionStats.session_unique_roses,
            total_unique_roses: sessionStats.total_unique_roses,
            final_count: sessionStats.final_count,
            duration: sessionStats.duration.toFixed(1) + 's',
            average_fps: sessionStats.average_fps.toFixed(1),
            total_frames: sessionStats.total_frames_processed
        });
    },

    // Update current session
    updateCurrentSession(sessionId, sessionNumber) {
        this.currentSession = {
            id: sessionId,
            number: sessionNumber,
            startTime: Date.now()
        };
    },

    // Clear current session
    clearCurrentSession() {
        this.currentSession = null;
    },

    // Get current session info
    getCurrentSession() {
        return this.currentSession;
    },

    // Setup event listeners
    setupEventListeners() {
        // Listen for session updates from the main stream handler
        window.addEventListener('sessionUpdate', (event) => {
            if (event.detail && event.detail.sessionStats) {
                this.addSession(event.detail.sessionStats);
            }
        });
    }
};

// Initialize session handler when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SessionHandler.init();
});

// Export the session handler
window.SessionHandler = SessionHandler; 