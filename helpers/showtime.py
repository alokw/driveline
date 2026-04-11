"""
Showtime Management - Showtime scheduling, countdowns, and d3 indirection
"""

import os
from datetime import datetime, timedelta, time as dt_time, timezone
from typing import List, Optional, Tuple
import re

from .osc import osc_send, get_osc_value, osc_db


# Global showtime storage
_showtimes: List[dt_time] = []


def parse_timecode(tc: str) -> float:
    """
    Parse timecode string to seconds

    Args:
        tc: Timecode in format HH:MM:SS:FF or HH:MM:SS.FF

    Returns:
        Time in seconds (float)
    """
    try:
        # Handle both colon and decimal formats
        parts = re.split('[:.]', tc)
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        frames = int(parts[3]) if len(parts) > 3 else 0

        total_seconds = hours * 3600 + minutes * 60 + seconds + (frames / 30.0)  # Assuming 30fps
        return total_seconds
    except Exception as e:
        print(f"[Showtime] Error parsing timecode {tc}: {e}")
        return 0.0


def format_time_diff(seconds: float) -> str:
    """
    Format time difference as mm:ss

    Args:
        seconds: Time difference in seconds

    Returns:
        Formatted string (mm:ss)
    """
    if seconds < 0:
        seconds = abs(seconds)

    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def seq_showtime_set(times_str: str) -> bool:
    """
    Store showtimes from comma-separated list

    Args:
        times_str: Comma-separated showtimes in HH:MM format (e.g., "10:30, 12:00, 13:30")

    Returns:
        True if successful, False otherwise
    """
    global _showtimes

    try:
        _showtimes.clear()
        times_list = [t.strip() for t in times_str.split(',')]

        for time_str in times_list:
            try:
                # Parse HH:MM format
                hour, minute = map(int, time_str.split(':'))
                showtime = dt_time(hour=hour, minute=minute)
                _showtimes.append(showtime)
            except Exception as e:
                print(f"[Showtime] Error parsing time {time_str}: {e}")
                return False

        # Sort showtimes
        _showtimes.sort()
        print(f"[Showtime] Set showtimes: {[t.strftime('%H:%M') for t in _showtimes]}")
        return True

    except Exception as e:
        print(f"[Showtime] Error setting showtimes: {e}")
        return False


def get_next_showtime() -> Optional[dt_time]:
    """
    Get the next showtime from current time

    Returns:
        Next showtime as time object, or None if no showtimes set
    """
    if not _showtimes:
        return None

    now = datetime.now()
    today = now.date()
    current_time = now.time()

    # First, try to find a showtime today that hasn't passed yet
    for showtime in _showtimes:
        if showtime > current_time:
            return showtime

    # If all showtimes have passed today, return the first one tomorrow
    return _showtimes[0]


def seq_showtime_check() -> Optional[str]:
    """
    Check and return next showtime, generate d3 indirection

    Returns:
        Next showtime string in HH:MM format, or None
    """
    try:
        next_show = get_next_showtime()
        if not next_show:
            return None

        showtime_str = next_show.strftime('%H:%M')

        # Generate d3 indirection string
        # Format: objects/videofile/9801_nextshow/nextshow_{HH}_{MM}_fg_nlca.mov
        hour_str = next_show.strftime('%H')
        minute_str = next_show.strftime('%M')
        indirection = f"objects/videofile/9801_nextshow/nextshow_{hour_str}{minute_str}_fg_nlca.mov"

        # Send to d3
        address = os.getenv('D3_OSC_OUT_ADDRESS', '10.10.10.255')
        port = int(os.getenv('D3_OSC_OUT_PORT', 7500))

        osc_send(address, port, "/d3/indirection/nextshow", indirection)

        # Store in OSC database for dashboard display
        osc_db.set("/showtime/next", showtime_str)

        return showtime_str

    except Exception as e:
        print(f"[Showtime] Error checking showtime: {e}")
        return None


def show_close_check() -> str:
    """
    Check show close time and return countdown

    Returns:
        Countdown string or "Show is closed"
    """
    try:
        show_close_str = os.getenv('SHOW_CLOSE', '2026-04-12T20:00:00')

        # Get current time with local timezone info
        now = datetime.now().astimezone()
        local_tz = now.tzinfo

        # Parse show_close as naive datetime
        show_close_naive = datetime.fromisoformat(show_close_str)

        # Make show_close timezone-aware in local timezone
        show_close_local = show_close_naive.replace(tzinfo=local_tz)

        if now >= show_close_local:
            return "Show is closed"

        # Calculate countdown
        delta = show_close_local - now

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if days > 0 or hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if days > 0 or hours > 0 or minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        return "Show closes in " + ", ".join(parts)

    except Exception as e:
        print(f"[Showtime] Error checking show close: {e}")
        return "Error checking show close"


def d3_section_hint_check(path: str, value) -> Optional[str]:
    """
    Parse d3 section hint and send to Medialon (OSC callback)

    Args:
        path: OSC path (should be /d3/showcontrol/sectionhint)
        value: Section hint value from d3

    Returns:
        Truncated section hint string, or None
    """
    try:
        if path != '/d3/showcontrol/sectionhint':
            return None

        if not value or not isinstance(value, str):
            return None

        # Extract text after "/" if present
        if "/" in value:
            truncated = value.split("/")[-1].strip()
        else:
            truncated = value

        # Send to Medialon via OSC
        address = os.getenv('AUTOMATION_OSC_OUT_ADDRESS', '10.10.10.255')
        port = int(os.getenv('AUTOMATION_OSC_OUT_PORT', 7411))

        osc_send(address, port, "/red/fyi", truncated)

        # Store truncated value in OSC database at separate path for dashboard display
        osc_db.set("/showtime/section_hint", truncated)

        return truncated

    except Exception as e:
        print(f"[Showtime] Error checking section hint: {e}")
        return None


def d3_seq_time_check() -> str:
    """
    Check d3 track position and return context-aware countdown

    Returns:
        Formatted countdown string
    """
    try:
        trackname = get_osc_value('/d3/showcontrol/trackname')
        trackposition_value = get_osc_value('/d3/showcontrol/trackposition', 0.0)

        # Convert trackposition to seconds (handle both timecode strings and floats)
        if trackposition_value is None:
            trackposition = 0.0
        elif isinstance(trackposition_value, str):
            # Trackposition is a timecode like "00:02:13.16"
            trackposition = parse_timecode(trackposition_value)
        else:
            # Trackposition is already a number
            trackposition = float(trackposition_value)

        if not trackname or trackname != "public":
            return "No presentations in this sequence"

        # Parse sequence time markers from environment
        drone_deploy = parse_timecode(os.getenv('SEQ_TIME_DRONE_DEPLOY', '00:00:30:00'))
        act2_start = parse_timecode(os.getenv('SEQ_TIME_ACT2_START', '00:04:46:01'))
        presenter_start = parse_timecode(os.getenv('SEQ_TIME_PRESENTER_START', '00:10:31:06'))
        presenter_end = parse_timecode(os.getenv('SEQ_TIME_PRESENTER_END', '00:14:31:06'))
        reset_start = parse_timecode(os.getenv('SEQ_TIME_RESET_START', '01:17:46:05'))
        reset_end = parse_timecode(os.getenv('SEQ_TIME_RESET_END', '01:19:31:05'))
        timeline_end = parse_timecode(os.getenv('SEQ_TIME_TIMELINE_END', '01:29:29.29'))

        # Determine countdown based on position
        if trackposition < drone_deploy:
            # Before drone deploy
            to_act2 = act2_start - trackposition
            to_drone = drone_deploy - trackposition
            return f"Time to Act 2: {format_time_diff(to_act2)}\nTime to Drone Deploy: {format_time_diff(to_drone)}"

        elif trackposition < act2_start:
            # Between drone deploy and Act 2
            to_act2 = act2_start - trackposition
            return f"Time to Act 2: {format_time_diff(to_act2)}"

        elif trackposition < presenter_start:
            # Between Act 2 and presenter
            to_presenter = presenter_start - trackposition
            return f"Time to Presentation: {format_time_diff(to_presenter)}"

        elif trackposition < presenter_end:
            # During presenter
            to_video = presenter_end - trackposition
            return f"Time to Video: {format_time_diff(to_video)}"

        elif trackposition < reset_start:
            # After presenter, before reset
            to_reset = reset_start - trackposition
            return f"Time to Reset: {format_time_diff(to_reset)}"

        else:
            # After reset - wrap around
            time_from_end = timeline_end - trackposition
            to_act2 = time_from_end + act2_start
            to_drone = time_from_end + drone_deploy
            return f"Time to Act 2: {format_time_diff(to_act2)}\nTime to Drone Deploy: {format_time_diff(to_drone)}"
        
    except Exception as e:
        print(f"[Showtime] Error checking sequence time: {e}")
        return "Error checking sequence time"
