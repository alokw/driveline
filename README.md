# Driveline - Show Control System

A web-based show control system for integrating d3 media servers, automation systems, StageTimer.io, Barco EventMaster, and Millumin via OSC and HTTP protocols.

## Features

- **Real-Time Dashboard**: Live updates via Socket.IO
- **OSC Integration**: Bidirectional OSC/UDP with queue-based rate limiting
- **Device Control**: Integrated d3, EventMaster, Millumin, StageTimer controls
- **Component System**: Jinja2 macros for reusable UI components
- **60Hz Crossfades**: Smooth audio/video transitions using background threads
- **Showtime Management**: Automated scheduling with d3 indirection generation
- **Section Hint Display**: Real-time parsing, display, and Medialon forwarding
- **Countdown Displays**: Show close, moments, and sequence cues
- **Data Logging**: Google Sheets logging of all control actions
- **Debug Interface**: Real-time OSC data monitoring
- **Docker Deployment**: Containerized for easy deployment

## Quick Start

### Prerequisites

- Docker Desktop (macOS) or Docker + Docker Compose (Linux/Windows)
- Google Sheets API credentials (for logging)
- Network access to show devices

### Installation

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd driveline
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Set up Google Sheets credentials**
   
   **Option A: Paste JSON in .env (Recommended)**
   - Go to Google Cloud Console → IAM & Admin → Service Accounts
   - Create service account, click "Keys" → "Create New Key" → JSON
   - Copy entire JSON and paste into `.env` as `GOOGLE_CREDENTIALS_JSON`
   
   **Option B: Use credentials file**
   ```bash
   mkdir -p config
   # Copy service account JSON to config/google_credentials.json
   ```
   
   Share your Google Sheet with the service account email.

3. **Run with Docker**
   ```bash
   docker-compose up
   ```

4. **Access dashboard**
   - From host: `http://localhost:5000`
   - From other devices: `http://[YOUR_HOST_IP]:5000`

## Configuration

Key environment variables (see `.env.example` for complete list):

```bash
# Show Configuration
SHOW_CLOSE=2026-04-12T20:00:00                    # Show close datetime
SEQ_TIME_ACT2_START=00:04:46:01                   # Timeline markers

# OSC Configuration
D3_OSC_IN_PORT=7400                                # d3 incoming port
D3_OSC_OUT_ADDRESS=10.10.10.101                    # d3 outgoing address (use specific device IP)
AUTOMATION_OSC_IN_PORT=7587                        # Automation incoming port
AUTOMATION_OSC_OUT_ADDRESS=10.10.10.102            # Automation outgoing address (use specific device IP)
AUTOMATION_OSC_OUT_PORT=7411                       # Automation outgoing port

# HTTP Integrations
STAGETIMER_OUT_URL=http://10.19.53.21:3000/api/v1/  # StageTimer API
EVENTMASTER_OUT_ADDRESS=http://192.168.0.175:9999   # EventMaster URL

# Google Sheets
GOOGLE_SPREADSHEET_ID=your_sheet_id                # Spreadsheet ID
GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'  # Service account JSON
```

## Usage

### Dashboards

- **Main Dashboard** (`/`): Showtime data, quick controls, d3 cues, StageTimer
- **Status Page** (`/status`): System status, OSC listeners, automation values
- **Advanced Controls** (`/advanced`): EventMaster presets, Millumin columns, advanced d3 cues
- **Debug Page** (`/debug`): Real-time OSC database view

### Device Controls

#### d3 Media Server
- **Standard Cue**: Immediate trigger
- **Clean Cue**: 60Hz audio/video crossfades (audio out → video out → trigger → video in → audio in)

#### EventMaster
- Preview preset → 100ms delay → Transition

#### Millumin
- Launch columns by name

#### StageTimer.io
- Actions: start_timer, stop_timer, reset_timer, update_timer, enable_blackout, disable_blackout
- **OSC Forwarding**: Listens for messages from d3 at `/stagetimer` and forwards to StageTimer
  - String: `/stagetimer "start_timer"` → HTTP action
  - List: `/stagetimer ["update_timer", 4, 20]` → update_timer with 4:20

### Showtime Scheduling

Set showtimes via comma-separated lists: `09:00, 10:30, 12:00, 13:30`

The system automatically finds the next showtime, generates d3 indirection strings, and sends to d3 via OSC:

```
objects/videofile/9801_nextshow/nextshow_{HH}_{MM}_fg_nlca.mov
```

### Component System

Jinja2 macros for reusable UI components:

```html
{{ components.d3_cue(952, 'Cue 952') }}                         # Standard cue
{{ components.d3_cue_clean(952, 'Description') }}                 # Clean cue
{{ components.eventmaster_preset('primary', 'Primary') }}         # Program preset
{{ components.millumin_column('chicago', 'Chicago') }}
{{ components.schedule_row('10:30 Start', '10:30, 12:00, 13:30') }}
{{ components.stagetimer_action('start_timer', 'Start') }}
{{ components.stagetimer_time(3, 30, '3:30') }}                    # Custom label
```

### 60Hz Crossfade System

Background threads send OSC values at 60Hz (~16.666ms) for smooth transitions:

```
1. Audio fade out:  /d3/layervolume  1.0 → 0.0 over 3s
2. Wait 1s
3. Video fade out: /d3/showcontrol/brightness 1.0 → 0.0 over 2s
4. Wait 1s
5. Trigger cue
6. Video fade in:  /d3/showcontrol/brightness 0.0 → 1.0 over 2s
7. Audio fade in:   /d3/layervolume  0.0 → 1.0 over 3s (steps 6 & 7 run simultaneously)
```

## Architecture

**Backend**: Flask + Flask-SocketIO (threading mode) + python-osc + Jinja2 macros  
**Frontend**: Vanilla JavaScript + Socket.IO client + CSS variables + Mobile-first design  
**OSC System**: Multi-port async listener + queue-based rate-limited sender + thread-safe in-memory database

## Docker Deployment

### Development Mode (Default)
```bash
docker-compose up
```
- Hot-reload enabled
- Debug mode on
- Port mapped for network access
- Accessible from other devices: `http://[HOST_IP]:5000`

### Production Mode
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- Gunicorn WSGI server
- Optimized performance
- Multi-NIC support (network_mode: host)

## Troubleshooting

### OSC Not Working
1. Check firewall allows UDP ports
2. Verify device IPs in `.env` (use specific IPs, not `.255`)
3. Check network connectivity: `docker exec driveline-dev ping -c 2 10.10.10.101`
4. Verify container running: `docker ps | grep driveline`

### Dashboard Not Updating
1. Check browser console for WebSocket errors
2. Clear browser cache and service workers
3. Verify Flask-SocketIO running
4. Check for port conflicts (VS Code Live Server on port 5000)

### Google Sheets Logging Not Working
1. Verify `GOOGLE_CREDENTIALS_JSON` is valid JSON
2. Check service account email has edit access to spreadsheet
3. Verify spreadsheet ID correct in `.env`
4. Check logs: `docker-compose logs driveline | grep -i google`

### Port Conflicts
If port 5000 is in use:
```bash
# Find process
lsof -i :5000
# Kill process
kill <PID>
# Or change port in .env: WEB_PORT=5001
```

### Hot-Reload Not Working
1. Ensure using development mode: `docker-compose up`
2. Check `FLASK_ENV=development` and `FLASK_DEBUG=1` in `.env`
3. For Python helper changes, restart container: `docker-compose restart`

## API Reference

### Socket.IO Events

**Client → Server**
- `d3_cue_go`: `{cue: number}`
- `d3_cue_go_clean`: `{cue: number}`
- `eventmaster_preset`: `{preset: string}`
- `millumin_column`: `{column: string}`
- `stagetimer_control`: `{action: string, minutes?: number, seconds?: number}`
- `set_showtimes`: `{times: string}`

**Server → Client**
- `osc_update`: `{path: string, value: any}`
- `showtime_update`: `{next_showtime, show_close_countdown, seq_time_fyi, section_hint}`
- `action_result`: `{action: string, success: boolean}`

## Performance

- OSC send interval: 10ms (0.01s)
- Queue size: 1000 messages
- Batch size: 10 messages per send
- Showtime check: Every 1 second

## Security

Designed for secure show networks. Add reverse proxy authentication if needed for public access. OSC is unencrypted.
