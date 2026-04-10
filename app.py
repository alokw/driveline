"""
Driveline - Show Control System
Flask application with Socket.IO for real-time show control
"""

import os
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask import jsonify

from helpers import (
    osc_db, osc_listener, osc_sender,
    get_osc_value, get_all_osc_values,
    d3_cue_go, d3_cue_go_clean,
    eventmaster_preset_prgm_by_name, millumin_launch_column_by_name, stagetimer_control,
    seq_showtime_set, seq_showtime_check, show_close_check,
    d3_section_hint_check, d3_seq_time_check,
    log_action
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'driveline-secret-key')

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# =============================================================================
# Template Context Processors
# =============================================================================

@app.context_processor
def utility_functions():
    """Custom template functions for Jinja2"""

    def osc_value(path, default=None):
        """Get OSC value for display"""
        try:
            return get_osc_value(path, default)
        except Exception as e:
            print(f"[Template Context] Error getting OSC value for {path}: {e}")
            return default

    return dict(
        osc_value=osc_value
    )


# =============================================================================
# Routes
# =============================================================================

@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('dashboards/dashboard.html', active_page='dashboard')


@app.route('/status')
def status():
    """Render status page"""
    return render_template('dashboards/status.html', active_page='status')


@app.route('/advanced')
def advanced():
    """Render advanced controls page"""
    return render_template('dashboards/advanced.html', active_page='advanced')


@app.route('/debug')
def debug():
    """Render debug page"""
    return render_template('dashboards/debug.html', active_page='debug')


# =============================================================================
# API Routes
# =============================================================================

@app.route('/api/osc/all')
def api_osc_all():
    """Get all OSC values"""
    return jsonify(get_all_osc_values())


@app.route('/api/osc/<path:path>')
def api_osc_path(path):
    """Get specific OSC value"""
    value = get_osc_value('/' + path)
    return jsonify({'path': '/' + path, 'value': value})


# =============================================================================
# Socket.IO Events
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"[Socket.IO] Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to Driveline'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[Socket.IO] Client disconnected: {request.sid}")


@socketio.on('get_osc_value')
def handle_get_osc_value(data):
    """Get OSC value via Socket.IO"""
    path = data.get('path')
    if path:
        value = get_osc_value(path)
        emit('osc_value', {'path': path, 'value': value})


@socketio.on('get_all_osc_values')
def handle_get_all_osc_values():
    """Get all OSC values via Socket.IO"""
    values = get_all_osc_values()
    emit('all_osc_values', values)


@socketio.on('get_showtime_data')
def handle_get_showtime_data():
    """Get current showtime data"""
    data = {
        'next_showtime': seq_showtime_check(),
        'show_close_countdown': show_close_check(),
        'seq_time_fyi': d3_seq_time_check(),
        'section_hint': d3_section_hint_check()
    }
    emit('showtime_update', data)


# =============================================================================
# Device Control Socket.IO Events
# =============================================================================

@socketio.on('d3_cue_go')
def handle_d3_cue_go(data):
    """Handle d3 cue trigger"""
    cue = data.get('cue')
    ip = request.remote_addr

    if cue:
        success = d3_cue_go(cue)
        log_action(ip, 'd3_cue_go', cue)
        emit('action_result', {'action': 'd3_cue_go', 'success': success, 'cue': cue})


@socketio.on('d3_cue_go_clean')
def handle_d3_cue_go_clean(data):
    """Handle d3 clean cue trigger"""
    cue = data.get('cue')
    ip = request.remote_addr

    if cue:
        success = d3_cue_go_clean(cue)
        log_action(ip, 'd3_cue_go_clean', cue)
        emit('action_result', {'action': 'd3_cue_go_clean', 'success': success, 'cue': cue})


@socketio.on('eventmaster_preset')
def handle_eventmaster_preset(data):
    """Handle EventMaster preset activation"""
    preset = data.get('preset')
    ip = request.remote_addr

    if preset:
        success = eventmaster_preset_prgm_by_name(preset)
        log_action(ip, 'eventmaster_preset', preset)
        emit('action_result', {'action': 'eventmaster_preset', 'success': success, 'preset': preset})


@socketio.on('millumin_column')
def handle_millumin_column(data):
    """Handle Millumin column launch"""
    column = data.get('column')
    ip = request.remote_addr

    if column:
        success = millumin_launch_column_by_name(column)
        log_action(ip, 'millumin_column', column)
        emit('action_result', {'action': 'millumin_column', 'success': success, 'column': column})


@socketio.on('stagetimer_control')
def handle_stagetimer_control(data):
    """Handle StageTimer control"""
    action = data.get('action')
    minutes = data.get('minutes')
    seconds = data.get('seconds')
    ip = request.remote_addr

    if action:
        param = f"{action}" + (f" {minutes}:{seconds}" if minutes else "")
        success = stagetimer_control(action, minutes, seconds)
        log_action(ip, 'stagetimer', param)
        emit('action_result', {'action': 'stagetimer', 'success': success, 'action': action})


@socketio.on('set_showtimes')
def handle_set_showtimes(data):
    """Handle showtime schedule update"""
    times = data.get('times')
    ip = request.remote_addr

    if times:
        success = seq_showtime_set(times)
        log_action(ip, 'set_showtimes', times)
        emit('action_result', {'action': 'set_showtimes', 'success': success, 'times': times})


# =============================================================================
# OSC Callback - Broadcast updates to all clients
# =============================================================================

def osc_update_callback(path: str, value):
    """Callback when OSC value updates - broadcast to all clients"""
    socketio.emit('osc_update', {'path': path, 'value': value})


# =============================================================================
# Background Tasks
# =============================================================================

def background_showtime_check():
    """Background task to check showtimes every second"""
    while True:
        try:
            socketio.sleep(1)
            next_show = seq_showtime_check()
            show_close = show_close_check()
            seq_fyi = d3_seq_time_check()
            section_hint = d3_section_hint_check()

            # Emit updates to all clients
            socketio.emit('showtime_update', {
                'next_showtime': next_show,
                'show_close_countdown': show_close,
                'seq_time_fyi': seq_fyi,
                'section_hint': section_hint
            })

        except Exception as e:
            print(f"[Background] Error in showtime check: {e}")


# =============================================================================
# Application Startup
# =============================================================================

def start_osc_listeners():
    """Start OSC listeners on configured ports"""
    d3_port = int(os.getenv('D3_OSC_IN_PORT', 7400))
    automation_port = int(os.getenv('AUTOMATION_OSC_IN_PORT', 7587))

    osc_listener.start(d3_port)
    osc_listener.start(automation_port)

    # Register OSC update callback for important paths
    important_paths = [
        '/d3/showcontrol/heartbeat',
        '/d3/showcontrol/trackposition',
        '/d3/showcontrol/sectionhint',
        '/d3/showcontrol/trackname',
        '/d3/showcontrol/currentsectionname',
        '/d3/showcontrol/nextsectionname',
        '/d3/showcontrol/playmode',
        '/automation/wall0/pos_x',
        '/automation/wall1/pos_x',
        '/automation/turntable/rot_y',
        '/automation/turntable/rot_y_ro',
    ]

    for path in important_paths:
        osc_db.register_callback(path, osc_update_callback)


def start_background_tasks():
    """Start background tasks"""
    socketio.start_background_task(background_showtime_check)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    # Start OSC system
    osc_sender.start()
    start_osc_listeners()
    start_background_tasks()

    # Run Flask app
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"[Driveline] Starting server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
