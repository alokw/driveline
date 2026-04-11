# Driveline - Show Control System

A professional web-based show control system for integrating and managing live show devices including d3 media servers, automation systems, StageTimer.io, Barco EventMaster, and Millumin via OSC and HTTP protocols.

## Features

- **Real-Time Dashboard**: Web-based UI with live data updates via Socket.IO
- **OSC Integration**: Bidirectional OSC/UDP communication with queue-based rate limiting
- **Device Control**: Integrated control for d3, EventMaster, Millumin, and StageTimer
- **Component System**: Jinja2 macros for reusable, clean dashboard components
- **Advanced Crossfades**: 60Hz background crossfading for smooth audio/video transitions
- **Showtime Management**: Automated showtime scheduling with d3 indirection generation
- **Countdown Displays**: Live countdowns to show close, show moments, and sequence cues
- **Data Logging**: Automatic Google Sheets logging of all control actions
- **Debug Interface**: Comprehensive debug page showing all OSC data in real-time
- **Docker Deployment**: Containerized application for easy deployment
- **Dark Theme UI**: Modern, responsive interface optimized for show control environments

## Quick Start

### Prerequisites

**For macOS:**
- Docker Desktop (recommended for development)
- Google Sheets API credentials (for logging)
- Network access to show devices (d3, EventMaster, etc.)

**For Linux/Windows:**
- Docker and Docker Compose
- Google Sheets API credentials (for logging)
- Network access to show devices (d3, EventMaster, etc.)

See [macOS Development](#macos-development) for important networking details.

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd driveline
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up Google Sheets credentials**

   **Option A: Paste JSON directly in .env (Recommended)**
   - Go to Google Cloud Console → IAM & Admin → Service Accounts
   - Create service account or select existing one
   - Click "Keys" → "Add Key" → "Create New Key" → JSON
   - Copy the entire JSON content
   - Paste it into `.env` as the `GOOGLE_CREDENTIALS_JSON` value

   Example:
   ```bash
   GOOGLE_CREDENTIALS_JSON='{"type": "service_account", "project_id": "your-project", "private_key_id": "...", "private_key": "...", ...}'
   ```

   **Option B: Use credentials file**
   ```bash
   mkdir -p config
   # Copy your Google service account JSON to config/google_credentials.json
   ```

4. **Share your Google Sheet** with the service account email (from the JSON)

5. **Build and run with Docker**

   **Development Mode (Default - with hot-reload)**
   ```bash
   docker-compose up
   ```

   **Production Mode (Optimized, no hot-reload)**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

6. **Access the dashboard**
   - From the host machine: `http://localhost:5000`
   - From other devices: `http://[YOUR_HOST_IP]:5000`
   - Example: `http://192.168.1.100:5000`

7. **Find your host IP address** (if accessing from other devices)
   - macOS/Linux: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - Windows: `ipconfig | findstr IPv4`

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Show Configuration
SHOW_CLOSE=2026-04-12T20:00:00                    # Show close datetime
SEQ_TIME_ACT2_START=00:04:46:01                   # Timeline markers
SEQ_TIME_PRESENTER_START=00:10:31:06

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
GOOGLE_SPREADSHEET_CELLS="'control log'!A:D"       # Cell range (use double quotes outer, single quotes inner for spaces)
GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'  # Service account JSON (recommended)
# GOOGLE_CREDENTIALS_PATH=/app/config/google_credentials.json  # Alternative: file path
```

### Google Sheets Setup

**Method 1: Environment Variable (Recommended)**

1. Create a Google Cloud project or use existing one
2. Enable the Google Sheets API
3. Create a service account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Note the service account email address
4. Create and download JSON key:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key" → "JSON"
   - Download the JSON file
5. Copy the entire contents of the JSON file
6. Paste into your `.env` file as `GOOGLE_CREDENTIALS_JSON`:
   ```bash
   GOOGLE_CREDENTIALS_JSON='{"type": "service_account", "project_id": "...", ...}'
   ```
7. Share your Google Sheet with the service account email address

**Method 2: Credentials File (Alternative)**

1. Follow steps 1-4 above
2. Place the downloaded JSON file at `config/google_credentials.json`
3. Set `GOOGLE_CREDENTIALS_PATH=/app/config/google_credentials.json` in `.env`
4. Share your Google Sheet with the service account email address

## Usage

### Dashboards

**Main Dashboard** (`/`)
- Show close countdown
- Sequence time FYI
- Next showtime display
- Quick controls for d3 cues and StageTimer
- Showtime schedule buttons

**Status Page** (`/status`)
- System status indicators
- OSC listener status
- Live automation values
- D3 status information

**Advanced Controls** (`/advanced`)
- EventMaster preset controls
- Millumin column launches
- Advanced d3 cue controls
- Custom timer presets

**Debug Page** (`/debug`)
- Real-time OSC database view
- All monitored OSC paths and values
- Auto-refreshing every second

### Device Controls

#### d3 Media Server
- **Standard Cue**: `d3_cue_go(cue_number)` - Immediate cue trigger
- **Clean Cue**: `d3_cue_go_clean(cue_number)` - Advanced crossfaded transition
  - 60Hz audio/video crossfades in background threads
  - Automated sequence: audio out → video out → trigger → video in → audio in
  - Smooth linear interpolation for professional transitions

#### EventMaster
- **Preset Activation**: Preview preset → 100ms delay → Transition
- Presets: primary, secondary, backup (configurable)

#### Millumin
- **Column Launch**: Launch columns by name
- Example: chicago, newyork, losangeles

#### StageTimer.io
- **Actions**: start_timer, stop_timer, reset_timer, update_timer, enable_blackout, disable_blackout
- **Update Timer**: Set custom minutes and seconds

### Showtime Scheduling

Showtimes are set via comma-separated lists:
```
09:00, 10:30, 12:00, 13:30, 15:30, 17:00, 18:30, 20:00
```

The system automatically:
1. Finds the next showtime from current time
2. Generates d3 indirection strings
3. Sends indirection to d3 via OSC

Indirection format:
```
objects/videofile/9801_nextshow/nextshow_{HH}_{MM}_fg_nlca.mov
```

### Component System

Driveline uses Jinja2 macros for reusable UI components, making dashboard HTML cleaner and more maintainable.

**Available Components:**
```html
<!-- D3 Cues -->
{{ components.d3_cue(952, 'Description', 'Trigger') }}           # Custom button text
{{ components.d3_cue_clean(952, 'Description', 'Clean') }}       # Clean cue

<!-- EventMaster -->
{{ components.eventmaster_preset('primary', 'Primary') }}        # Program preset
{{ components.eventmaster_preview('secondary', 'Preview') }}      # Preview preset
{{ components.eventmaster_transition('Take') }}                  # Transition

<!-- Millumin -->
{{ components.millumin_column('chicago', 'Chicago') }}

<!-- Schedule Buttons -->
{{ components.schedule_row('10:30 Start', '10:30, 12:00, 13:30') }}

<!-- StageTimer -->
{{ components.stagetimer_action('start_timer', 'Start') }}
{{ components.stagetimer_time(3, 30, '3:30') }}                  # Custom label
{{ components.stagetimer_time(5, 0) }}                           # Auto-generates "05:00"
```

**Benefits:**
- **Cleaner Code**: 4-line HTML blocks become 1-line macro calls
- **Consistency**: All buttons styled uniformly
- **Maintainability**: Update macro once, changes apply everywhere
- **Flexibility**: Optional parameters for customization (button text, labels, etc.)

**Before (4 lines):**
```html
<div class="d3-cue-row">
    <button class="button button-secondary button-d3-cue" data-d3-cue="952">Trigger</button>
    <span class="d3-cue-label">Cue 952</span>
</div>
```

**After (1 line):**
```html
{{ components.d3_cue(952, 'Cue 952') }}
```

### Advanced Crossfade System

Driveline includes a sophisticated crossfade system for smooth audio/video transitions:

**Features:**
- **60Hz Update Rate**: Sends OSC values every ~16.666ms for buttery-smooth transitions
- **Background Threading**: Multiple crossfades can run simultaneously without blocking
- **Linear Interpolation**: Mathematically smooth transitions from start to end values
- **d3 Integration**: Sends single float values to `/d3/layervolume` and `/d3/showcontrol/brightness`

**Clean Cue Sequence:**
```
1. Audio fade out:  /d3/layervolume  1.0 → 0.0 over 3s (background)
2. Wait 1s
3. Video fade out: /d3/showcontrol/brightness 1.0 → 0.0 over 2s (background)
4. Wait 1s
5. Trigger cue
6. Video fade in:  /d3/showcontrol/brightness 0.0 → 1.0 over 2s (background)
7. Audio fade in:   /d3/layervolume  0.0 → 1.0 over 3s (background)
   (steps 6 & 7 run simultaneously)
```

**Usage:**
```python
# In helpers/devices.py
crossfade(address, port, "/d3/layervolume", 1.0, 0.0, 3.0)  # Start, end, duration
```

### OSC Data Monitoring

Monitored OSC paths:
```
/automation/wall0/pos_x
/automation/wall1/pos_x
/automation/turntable/rot_y
/automation/turntable/rot_y_ro
/d3/showcontrol/heartbeat
/d3/showcontrol/trackname
/d3/showcontrol/currentsectionname
/d3/showcontrol/nextsectionname
/d3/showcontrol/sectionhint
/d3/showcontrol/playmode
/d3/showcontrol/trackposition
```

## Architecture

### Backend
- **Flask**: Web framework
- **Flask-SocketIO**: WebSocket support with polling fallback for real-time updates
- **python-osc**: OSC protocol implementation
- **Threading**: Background OSC listener, sender, and crossfade system
- **Jinja2 Macros**: Component system for reusable UI elements
- **Python logging**: Structured logging with configurable verbosity

### Frontend
- **Vanilla JavaScript**: No frameworks, minimal dependencies
- **Socket.IO Client**: Real-time data updates
- **Jinja2 Components**: Macro-based reusable UI elements
- **CSS Variables**: Easy theming and maintenance
- **Mobile-First**: Responsive design for all screen sizes

### OSC System
- **Listener**: Multi-port async OSC server supporting bundles
- **Sender**: Queue-based rate-limited OSC sender (configurable interval)
- **Crossfade Engine**: 60Hz background thread system for smooth value transitions
- **Database**: Thread-safe in-memory storage for all OSC values

## Docker Deployment

### Production Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Custom Configuration (Production)
```bash
docker-compose -f docker-compose.prod.yml up -d --env-file .env.custom
```

### View Logs (Production)
```bash
docker-compose -f docker-compose.prod.yml logs -f driveline
```

### Stop Production Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Development Deployment (Default with Hot-Reload)
See the Development section below for details.

**macOS Users:** See [macOS Development with Colima](#macos-development-with-colima) for important networking requirements.

### Network Configuration

**Development (macOS with Docker Desktop):**
- Uses **port mappings** for network access
- Web GUI accessible from other devices: `http://[HOST_IP]:5000`
- OSC broadcast messages are received properly
- Outgoing OSC should use specific device IPs (not `.255`)

**Production (Linux servers):**
- Uses `network_mode: host` for multi-NIC support
- Container shares host's network stack
- Web GUI accessible on all network interfaces
- Full OSC broadcast send/receive capability

**Accessing from Other Devices:**
1. Find your host IP address:
   - macOS/Linux: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - Windows: `ipconfig | findstr IPv4`
2. Access via: `http://[HOST_IP]:5000`
   - Example: `http://192.168.1.100:5000`

**Firewall Configuration:**
- Ensure port 5000 is not blocked by your firewall
- macOS: System Settings → Network → Firewall
- Linux: `sudo ufw allow 5000` or configure firewalld
- Windows: Windows Defender Firewall → Allow an app

### Building from Source

```bash
# Build the production image
docker-compose -f docker-compose.prod.yml build

# Rebuild without cache
docker-compose -f docker-compose.prod.yml build --no-cache
```

## Development

### Default Mode (Development with Hot-Reload)

By default, the system runs in development mode with hot-reload enabled:

```bash
docker-compose up
```

**Features:**
- ✅ **Hot-reload**: Templates, CSS, JS, and Python code reload automatically
- ✅ **Debug mode**: Detailed error messages and stack traces
- ✅ **Verbose logging**: More detailed console output
- ⚠️ **Not production-ready**: Slower performance, higher memory usage

**When to use:**
- Developing new features
- Modifying templates, CSS, or JavaScript
- Debugging code issues
- Testing configuration changes

### Production Mode (Optimized)

For deployment and production use, specify the production configuration:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Features:**
- ✅ **Optimized performance**: Gunicorn WSGi server
- ✅ **Stable**: No code reloading, consistent behavior
- ✅ **Production-ready**: Proper worker threads and error handling
- ⚠️ **No hot-reload**: Requires restart to see changes

**When to use:**
- Running the system in production
- Stable deployments
- Maximum performance required

### Switching Between Modes

If you're currently running in one mode and want to switch:

```bash
# Stop development mode
docker-compose down

# Start production mode
docker-compose -f docker-compose.prod.yml up -d

# Or vice versa
docker-compose -f docker-compose.prod.yml down
docker-compose up
```

### Viewing Changes in Development Mode

With development mode running (default):
1. Edit any template (`.html`), CSS (`.css`), JS (`.js`), or Python (`.py`) file
2. Save the file
3. **Wait 1-2 seconds** - Flask detects the change and automatically reloads
4. Refresh your browser - changes are live!

**Note:** Some Python changes (like modifying helper functions) may require a full container restart:

```bash
docker-compose restart
```

### Local Development (without Docker)

For development without Docker:

### Project Structure
```
driveline/
├── app.py                    # Flask application
├── helpers/                  # Helper modules
│   ├── osc.py               # OSC system
│   ├── devices.py           # Device controls
│   ├── showtime.py          # Showtime management
│   └── logging.py           # Google Sheets logging
├── static/
│   ├── css/                 # Stylesheets
│   └── js/                  # JavaScript
├── templates/
│   ├── base.html            # Base template
│   └── dashboards/          # Dashboard pages
├── config/                  # Configuration files (optional)
├── .env                     # Environment variables
├── Dockerfile               # Docker image
├── docker-compose.yml       # Development configuration (default)
└── docker-compose.prod.yml  # Production configuration
```

## Troubleshooting

### OSC Not Receiving Data

**Problem**: No OSC data appearing in dashboard

**Solutions**:
1. Check firewall settings - UDP ports must be open
2. Verify device IP addresses and ports in `.env`
3. Check network connectivity to OSC devices
4. Verify devices are sending to correct IP (this machine's IP)
5. Check Docker port mappings are configured correctly in `docker-compose.yml`
6. Verify container is running: `docker ps | grep driveline`

### OSC Not Sending to Devices

**Problem**: Commands not reaching d3 or automation devices

**Solutions**:
1. **Use specific device IPs** instead of broadcast addresses in `.env`
   - Change `D3_OSC_OUT_ADDRESS=10.10.10.255` to `D3_OSC_OUT_ADDRESS=10.10.10.101` (actual device IP)
2. Verify device IPs are reachable: `docker exec driveline-dev ping -c 2 10.10.10.101`
3. Check logs for OSC queue/send messages: `docker-compose logs driveline | grep OSC`
4. Verify outgoing port configuration in `.env`
5. Test with specific device IP instead of broadcast

### Google Sheets Logging Not Working

**Problem**: Actions not being logged

**Solutions**:
1. Verify `GOOGLE_CREDENTIALS_JSON` is set correctly in `.env`
   - Ensure the JSON is properly formatted and escaped
   - Test parsing: `echo $GOOGLE_CREDENTIALS_JSON | python -m json.tool`
2. Check service account email has edit access to spreadsheet
3. Verify spreadsheet ID in `.env` is correct
4. Check Google Sheets API is enabled in Google Cloud project
5. Check logs for API errors: `docker-compose logs driveline | grep -i google`
6. If using file method, verify `config/google_credentials.json` exists

### Socket.IO Connection Issues

**Problem**: Dashboard not updating in real-time

**Solutions**:
1. Check browser console for WebSocket errors
2. Verify Flask-SocketIO is running
3. Check firewall allows WebSocket connections
4. Try accessing via HTTP (not HTTPS) in development
5. Restart Docker container

### Docker Container Won't Start

**Problem**: Container exits immediately

**Solutions**:
1. Check logs: `docker-compose logs driveline`
2. Verify `.env` file exists and is valid
3. Check port 5000 is not already in use
4. Verify all required files are present
5. Try rebuilding: `docker-compose build --no-cache`

### High CPU Usage

**Problem**: Container using excessive CPU

**Solutions**:
1. Adjust OSC send interval via `OSC_SEND_INTERVAL` env variable
2. Reduce OSC queue size via `OSC_QUEUE_SIZE` env variable
3. Check for infinite loops in background tasks
4. Monitor debug page for excessive OSC traffic

### Hot-Reload Not Working in Development

**Problem**: Template/code changes not appearing automatically

**Solutions**:
1. Ensure you're using development mode (default): `docker-compose up`
2. Check that `FLASK_ENV=development` and `FLASK_DEBUG=1` are set
3. Wait 2-3 seconds after saving - Flask needs time to detect changes
4. For Python helper changes, try restarting: `docker-compose restart`
5. Check logs for reload messages: `docker-compose logs -f driveline`
6. Verify volume mount is working: `docker-compose exec driveline ls -la /app/templates`

### Cannot Access Web GUI from Other Devices

**Problem**: Other devices on network cannot access the dashboard

**Solutions**:
1. **Check Flask is binding to all interfaces**:
   - Verify `FLASK_HOST=0.0.0.0` in `.env` (not `127.0.0.1`)
   - Check logs for: `Running on http://0.0.0.0:5000`

2. **Verify port mapping is active**:
   ```bash
   docker ps | grep driveline
   # Should show port mapping like "0.0.0.0:5000->5000/tcp"
   ```

3. **Find your host IP address**:
   - macOS/Linux: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - Windows: `ipconfig | findstr IPv4`

4. **Test from host machine first**:
   ```bash
   curl http://localhost:5000
   # Should return HTML
   ```

5. **Check firewall**:
   - macOS: System Settings → Network → Firewall
   - Linux: `sudo ufw status` or `sudo firewall-cmd --list-ports`
   - Windows: Windows Defender Firewall

6. **Test network connectivity**:
   ```bash
   # From another device, test if port is accessible:
   telnet [HOST_IP] 5000
   # OR
   nc -zv [HOST_IP] 5000
   ```

7. **Verify container is running**:
   ```bash
   docker ps
   # Should show driveline container with status "Up"
   ```

8. **Check container logs for errors**:
   ```bash
   docker logs driveline
   ```

**Example access URLs:**
- From host: `http://localhost:5000`
- From another device: `http://192.168.1.100:5000` (replace with your host IP)

## macOS Development

### Recommended Setup: Docker Desktop

For macOS development, **Docker Desktop with port mappings** is the recommended approach. This provides:

- ✅ **Full network access** - OSC broadcast messages (`.255`) are received properly
- ✅ **Port forwarding** - All required ports are mapped to the host
- ✅ **Easy setup** - No additional tools required
- ✅ **Web GUI access** - Dashboard accessible from other devices on the network

### Port Mapping Configuration

The default `docker-compose.yml` uses port mappings for development:

```yaml
services:
  driveline:
    ports:
      - "${WEB_PORT:-5000}:${WEB_PORT:-5000}"           # Web GUI
      - "${D3_OSC_IN_PORT:-7400}:${D3_OSC_IN_PORT:-7400}/udp"      # d3 OSC in
      - "${AUTOMATION_OSC_IN_PORT:-7587}:${AUTOMATION_OSC_IN_PORT:-7587}/udp"  # Automation OSC in
```

This configuration allows:
- Web GUI access from other devices: `http://[YOUR_MAC_IP]:5000`
- OSC broadcast message reception on ports 7400 and 7587
- Outgoing OSC messages to specific device IPs

### OSC Network Configuration

**Important**: For reliable OSC communication on macOS:

1. **Use specific device IPs** instead of broadcast addresses for outgoing OSC
   ```bash
   D3_OSC_OUT_ADDRESS=10.10.10.101  # Specific device, not .255
   AUTOMATION_OSC_OUT_ADDRESS=10.10.10.102  # Specific device, not .255
   ```

2. **Broadcast reception works** with port mappings - incoming OSC on `.255` is received properly

3. **For production Linux servers** with multiple network interfaces, use `docker-compose.prod.yml` which uses `network_mode: host` for proper multi-NIC access

### Running Driveline on macOS

```bash
# Start development mode (with hot-reload)
docker-compose up

# Access from your Mac
open http://localhost:5000

# Access from other devices
# Find your Mac's IP address
ifconfig | grep "inet " | grep -v 127.0.0.1
# Then access from other devices: http://[YOUR_MAC_IP]:5000
```

### Troubleshooting macOS OSC Issues

**OSC not reaching devices:**
1. Verify specific device IPs are set in `.env` (not broadcast addresses)
2. Test connectivity: `docker exec driveline-dev ping -c 2 10.10.10.101`
3. Check firewall settings

**Not receiving OSC broadcasts:**
1. Verify port mappings are active in `docker-compose.yml`
2. Check devices are sending to correct IP (your Mac's IP)
3. Verify UDP ports are not blocked by firewall

## API Reference

### HTTP Endpoints

#### Get All OSC Values
```http
GET /api/osc/all
```

#### Get Specific OSC Value
```http
GET /api/osc/<path>
```

### Socket.IO Events

#### Client → Server

| Event | Parameters | Description |
|-------|-----------|-------------|
| `d3_cue_go` | `{cue: number}` | Trigger d3 cue |
| `d3_cue_go_clean` | `{cue: number}` | Trigger clean d3 cue |
| `eventmaster_preset` | `{preset: string}` | Activate EventMaster preset |
| `millumin_column` | `{column: string}` | Launch Millumin column |
| `stagetimer_control` | `{action: string, minutes?: number, seconds?: number}` | Control StageTimer |
| `set_showtimes` | `{times: string}` | Set showtime schedule |

#### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `osc_update` | `{path: string, value: any}` | OSC value updated |
| `showtime_update` | `{next_showtime, show_close_countdown, seq_time_fyi, section_hint}` | Showtime data updated |
| `action_result` | `{action: string, success: boolean}` | Action completed |

## Performance

### OSC Rate Limiting
- Default send interval: 10ms (0.01s)
- Queue size: 1000 messages
- Batch size: 10 messages per send
- Configurable via environment variables

### Background Tasks
- Showtime check: Every 1 second
- OSC callback processing: Instant (async)
- Debug page refresh: Every 1 second

## Security Considerations

1. **Network**: This system is designed for secure show networks
2. **Authentication**: No built-in authentication - add reverse proxy authentication if needed
3. **OSC**: OSC is unencrypted - use secure show networks
4. **Google Sheets**: Service account credentials should be kept secure
5. **Docker**: Container runs as root - consider adding non-root user for production

## Support

For issues and questions:
- Check the Troubleshooting section
- Review debug page for real-time system status
- Check Docker logs: `docker-compose logs -f driveline`
- Verify network connectivity to all devices