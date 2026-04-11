/**
 * Dashboard Interactions
 * UI event handlers and interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] DOM Content Loaded - Initializing');

    // Initialize all button handlers
    initButtonHandlers();

    // Initialize showtime schedule buttons
    initShowtimeButtons();

    // Initialize auto-refresh for debug page
    initDebugRefresh();

    console.log('[Dashboard] Initialization complete');
});

/**
 * Initialize button click handlers
 */
function initButtonHandlers() {
    // d3 cue buttons
    const d3Buttons = document.querySelectorAll('[data-d3-cue]');
    console.log(`[Dashboard] Found ${d3Buttons.length} D3 cue buttons`);

    d3Buttons.forEach(button => {
        button.addEventListener('click', () => {
            const cue = parseInt(button.dataset.d3Cue);
            const clean = button.dataset.d3Clean === 'true';

            console.log('[Dashboard] D3 cue button clicked:', cue, 'clean:', clean);

            if (clean) {
                sendD3CueClean(cue);
            } else {
                sendD3Cue(cue);
            }
        });
    });

    // EventMaster preset buttons
    document.querySelectorAll('[data-eventmaster-preset]').forEach(button => {
        button.addEventListener('click', () => {
            const preset = button.dataset.eventmasterPreset;
            sendEventMasterPreset(preset);
        });
    });

    // Millumin column buttons
    document.querySelectorAll('[data-millumin-column]').forEach(button => {
        button.addEventListener('click', () => {
            const column = button.dataset.milluminColumn;
            launchMilluminColumn(column);
        });
    });

    // StageTimer control buttons
    document.querySelectorAll('[data-stagetimer-action]').forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.stagetimerAction;
            const minutes = button.dataset.stagetimerMinutes
                ? parseInt(button.dataset.stagetimerMinutes)
                : null;
            const seconds = button.dataset.stagetimerSeconds
                ? parseInt(button.dataset.stagetimerSeconds)
                : null;

            sendStageTimerControl(action, minutes, seconds);
        });
    });

    // Showtime schedule buttons
    document.querySelectorAll('[data-showtimes]').forEach(button => {
        button.addEventListener('click', () => {
            const times = button.dataset.showtimes;
            setShowtimes(times);
        });
    });
}

/**
 * Initialize showtime schedule buttons
 */
function initShowtimeButtons() {
    // These are handled by the general button handler above
    // This function is for any additional showtime-specific logic
}

/**
 * Initialize debug page auto-refresh
 */
function initDebugRefresh() {
    const debugTable = document.querySelector('.debug-table');
    if (debugTable) {
        // Refresh debug data every 1 second
        setInterval(() => {
            fetch('/api/osc/all')
                .then(response => response.json())
                .then(data => {
                    updateDebugTable(data);
                })
                .catch(error => {
                    console.error('[Dashboard] Error fetching debug data:', error);
                });
        }, 1000);
    }
}

/**
 * Update debug table with OSC data
 */
function updateDebugTable(data) {
    const tbody = document.querySelector('.debug-table tbody');
    if (!tbody) return;

    // Clear existing rows
    tbody.innerHTML = '';

    // Add rows for each OSC path
    Object.entries(data).forEach(([path, value]) => {
        const row = document.createElement('tr');
        row.dataset.debugPath = path;

        row.innerHTML = `
            <td><code>${path}</code></td>
            <td class="debug-value"><code>${JSON.stringify(value)}</code></td>
        `;

        tbody.appendChild(row);
    });
}

/**
 * Utility: Format timestamp
 */
function formatTimestamp(date) {
    return date.toISOString().replace('T', ' ').substring(0, 19);
}

/**
 * Utility: Debounce function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
