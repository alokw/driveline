/**
 * Socket.IO Client Connection
 * Handles real-time communication with Flask backend
 */

// Initialize Socket.IO connection
const socket = io({
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// Connection status
socket.on('connect', () => {
    console.log('[Socket.IO] Connected to server');
    updateConnectionStatus(true);
    requestInitialData();
});

socket.on('disconnect', () => {
    console.log('[Socket.IO] Disconnected from server');
    updateConnectionStatus(false);
});

socket.on('connect_error', (error) => {
    console.error('[Socket.IO] Connection error:', error);
    updateConnectionStatus(false);
});

// Server confirmation
socket.on('connected', (data) => {
    console.log('[Socket.IO] Server message:', data.data);
});

// OSC value updates
socket.on('osc_update', (data) => {
    console.log('[Socket.IO] OSC update:', data.path, '=', data.value);
    updateOSCValue(data.path, data.value);
});

// Showtime updates
socket.on('showtime_update', (data) => {
    console.log('[Socket.IO] Showtime update:', data);
    updateShowtimeDisplays(data);
});

// All OSC values (initial load)
socket.on('all_osc_values', (data) => {
    console.log('[Socket.IO] Received all OSC values:', Object.keys(data).length, 'paths');
    Object.entries(data).forEach(([path, value]) => {
        updateOSCValue(path, value);
    });
});

// Action results
socket.on('action_result', (data) => {
    console.log('[Socket.IO] Action result:', data);
    showActionResult(data);
});

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const indicator = document.querySelector('.connection-status');
    if (indicator) {
        indicator.classList.toggle('active', connected);
        indicator.classList.toggle('error', !connected);
    }
}

/**
 * Update OSC value display elements
 */
function updateOSCValue(path, value) {
    // Update elements with data-osc-path attribute
    document.querySelectorAll(`[data-osc-path="${path}"]`).forEach(element => {
        element.textContent = value;
    });

    // Update debug table if exists with smooth transition
    const debugRow = document.querySelector(`[data-debug-path="${path}"]`);
    if (debugRow) {
        const valueCell = debugRow.querySelector('.debug-value');
        if (valueCell) {
            const codeElement = valueCell.querySelector('code');
            if (codeElement) {
                // Add updating class for smooth transition
                codeElement.classList.add('updating');

                // Update content
                codeElement.textContent = JSON.stringify(value);

                // Remove updating class after brief delay
                setTimeout(() => {
                    codeElement.classList.remove('updating');
                }, 50);
            }
        }
    }
}

/**
 * Update showtime display elements
 */
function updateShowtimeDisplays(data) {
    // Update all showtime data attributes
    Object.keys(data).forEach(key => {
        if (data[key]) {
            document.querySelectorAll(`[data-showtime="${key}"]`).forEach(element => {
                element.textContent = data[key];
            });
        }
    });

    // Update show close countdown
    if (data.show_close_countdown) {
        const showCloseElement = document.querySelector('[data-showtime="show_close"]');
        if (showCloseElement) {
            showCloseElement.textContent = data.show_close_countdown;
        }
    }

    // Update next showtime
    if (data.next_showtime) {
        const nextShowElement = document.querySelector('[data-showtime="next_show"]');
        if (nextShowElement) {
            nextShowElement.textContent = data.next_showtime;
        }
    }

    // Update sequence time FYI
    if (data.seq_time_fyi) {
        const seqTimeElement = document.querySelector('[data-showtime="seq_fyi"]');
        if (seqTimeElement) {
            seqTimeElement.textContent = data.seq_time_fyi;
        }
    }

    // Update section hint
    if (data.section_hint) {
        const sectionHintElement = document.querySelector('[data-showtime="section_hint"]');
        if (sectionHintElement) {
            sectionHintElement.textContent = data.section_hint;
        }
    }
}

/**
 * Request initial data on page load
 */
function requestInitialData() {
    console.log('[Socket.IO] Requesting initial data');

    // Request all OSC values
    socket.emit('get_all_osc_values');

    // Request initial showtime data
    socket.emit('get_showtime_data');
}

/**
 * Show action result feedback
 */
function showActionResult(data) {
    const message = data.success ? 'Success' : 'Failed';
    const className = data.success ? 'text-success' : 'text-error';

    // You could add toast notifications here
    console.log(`[Action] ${data.action}: ${message}`);

    // Update button states if needed
    document.querySelectorAll(`[data-action="${data.action}"]`).forEach(button => {
        button.classList.remove('loading');
    });
}

/**
 * Send OSC value request
 */
function getOSCValue(path) {
    socket.emit('get_osc_value', { path: path });
}

/**
 * Send d3 cue trigger
 */
function sendD3Cue(cue) {
    socket.emit('d3_cue_go', { cue: cue });
}

/**
 * Send d3 clean cue trigger
 */
function sendD3CueClean(cue) {
    socket.emit('d3_cue_go_clean', { cue: cue });
}

/**
 * Send EventMaster preset
 */
function sendEventMasterPreset(preset) {
    socket.emit('eventmaster_preset', { preset: preset });
}

/**
 * Send Millumin column launch
 */
function launchMilluminColumn(column) {
    socket.emit('millumin_column', { column: column });
}

/**
 * Send StageTimer control
 */
function sendStageTimerControl(action, minutes = null, seconds = null) {
    const data = { action: action };
    if (minutes !== null) data.minutes = minutes;
    if (seconds !== null) data.seconds = seconds;
    socket.emit('stagetimer_control', data);
}

/**
 * Set showtimes
 */
function setShowtimes(times) {
    socket.emit('set_showtimes', { times: times });
}
