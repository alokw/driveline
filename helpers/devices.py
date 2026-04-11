"""
Device Helpers - Control functions for all integrated devices
Includes d3, EventMaster, Millumin, StageTimer, and utility functions
"""

import os
import time
import logging
import threading
from typing import Optional
import requests

from .osc import osc_send

logger = logging.getLogger(__name__)


def get_request(url: str) -> Optional[requests.Response]:
    """
    Send HTTP GET request

    Args:
        url: URL to send request to

    Returns:
        Response object or None if error
    """
    try:
        print(f"[HTTP GET] Sending to: {url}")
        response = requests.get(url, timeout=5)
        print(f"[HTTP GET] Response: {response.status_code}")
        return response
    except Exception as e:
        print(f"[HTTP GET] Error: {e}")
        return None


def post_request(url: str, data: dict) -> Optional[requests.Response]:
    """
    Send HTTP POST request with JSON data

    Args:
        url: URL to send request to
        data: Dictionary to send as JSON

    Returns:
        Response object or None if error
    """
    try:
        print(f"[HTTP POST] Sending to: {url} with data: {data}")
        response = requests.post(url, json=data, timeout=5)
        print(f"[HTTP POST] Response: {response.status_code}")
        return response
    except Exception as e:
        print(f"[HTTP POST] Error: {e}")
        return None


def crossfade(address: str, port: int, path: str, start_value: float, end_value: float, duration: float) -> threading.Thread:
    """
    Execute a linear crossfade from start_value to end_value over duration seconds
    Runs in background thread and sends OSC updates at 60Hz

    Args:
        address: IP address to send to
        port: UDP port
        path: OSC address path (e.g., "/d3/layervolume")
        start_value: Starting value (float, typically 0.0 to 1.0)
        end_value: Ending value (float, typically 0.0 to 1.0)
        duration: Duration in seconds

    Returns:
        Thread object running the crossfade
    """
    def _crossfade_loop():
        start_time = time.time()
        update_interval = 1.0 / 60.0  # 60Hz = ~16.666ms

        while True:
            elapsed = time.time() - start_time

            if elapsed >= duration:
                # Send final value and exit
                osc_send(address, port, path, end_value)
                logger.debug(f"[Crossfade] Complete: {path} = {end_value}")
                break

            # Calculate linear interpolated value
            progress = elapsed / duration
            current_value = start_value + (end_value - start_value) * progress

            # Send current value
            osc_send(address, port, path, current_value)
            logger.debug(f"[Crossfade] {path} = {current_value:.3f} ({progress*100:.1f}%)")

            # Sleep until next update
            time.sleep(update_interval)

    # Start crossfade in background thread
    thread = threading.Thread(target=_crossfade_loop, daemon=True)
    thread.start()

    return thread


# =============================================================================
# d3 Controls
# =============================================================================

def d3_cue_go(cue: int) -> bool:
    """
    Send cue trigger to d3

    Args:
        cue: Cue number to trigger

    Returns:
        True if successful, False otherwise
    """
    try:
        address = os.getenv('D3_OSC_OUT_ADDRESS', '10.10.10.255')
        port = int(os.getenv('D3_OSC_OUT_PORT', 7500))
        path = "/d3/showcontrol/cue"

        return osc_send(address, port, path, cue)
    except Exception as e:
        logger.error(f"Error triggering cue: {e}")
        return False


def d3_cue_go_clean(cue: int) -> bool:
    """
    Execute clean cue transition with crossfaded audio/video
    Sequence: audio fade out 3s -> wait 1s -> video fade out 2s -> cue -> video fade in 2s -> audio fade in 3s

    Args:
        cue: Cue number to trigger

    Returns:
        True if successful, False otherwise
    """
    try:
        address = os.getenv('D3_OSC_OUT_ADDRESS', '10.10.10.255')
        port = int(os.getenv('D3_OSC_OUT_PORT', 7500))

        logger.info(f"[d3] Starting clean cue transition to cue {cue}")

        # Audio fade out (3 seconds) - start in background
        logger.info("[d3] Fading out audio (3s)")
        crossfade(address, port, "/d3/layervolume", 1.0, 0.0, 3.0)

        # Wait 1 second
        time.sleep(1)

        # Video fade out (2 seconds) - start in background
        logger.info("[d3] Fading out video (2s)")
        crossfade(address, port, "/d3/showcontrol/brightness", 1.0, 0.0, 2.0)

        # Wait 2 second
        time.sleep(2.25)

        # Trigger cue
        logger.info(f"[d3] Triggering cue {cue}")
        osc_send(address, port, "/d3/showcontrol/cue", cue)

        # Video fade in (2 seconds) - start immediately in background
        logger.info("[d3] Fading in video (2s)")
        crossfade(address, port, "/d3/showcontrol/brightness", 0.0, 1.0, 2.0)

        # Audio fade in (3 seconds) - start immediately in background
        logger.info("[d3] Fading in audio (3s)")
        crossfade(address, port, "/d3/layervolume", 0.0, 1.0, 3.0)

        logger.info(f"[d3] Clean cue transition complete")
        return True

    except Exception as e:
        logger.error(f"[d3] Error in clean cue transition: {e}")
        return False


# =============================================================================
# EventMaster Controls
# =============================================================================

def eventmaster_preset_prvw_by_name(preset: str) -> bool:
    """
    Activate EventMaster preview preset

    Args:
        preset: Preset name to activate

    Returns:
        True if successful, False otherwise
    """
    try:
        address = os.getenv('EVENTMASTER_OUT_ADDRESS', 'http://192.168.0.175:9999')

        payload = {
            "jsonrpc": "2.0",
            "method": "activatePreset",
            "params": {
                "presetName": preset,
                "type": 0
            },
            "id": "1234"
        }

        print(f"[EventMaster] Activating preview preset: {preset}")
        response = post_request(address, payload)
        return response is not None

    except Exception as e:
        print(f"[EventMaster] Error activating preview preset: {e}")
        return False


def eventmaster_alltrans() -> bool:
    """
    Execute EventMaster allTrans (take transition)

    Returns:
        True if successful, False otherwise
    """
    try:
        address = os.getenv('EVENTMASTER_OUT_ADDRESS', 'http://192.168.0.175:9999')

        payload = {
            "jsonrpc": "2.0",
            "method": "allTrans",
            "id": "1234"
        }

        print("[EventMaster] Executing allTrans")
        response = post_request(address, payload)
        return response is not None

    except Exception as e:
        print(f"[EventMaster] Error executing allTrans: {e}")
        return False


def eventmaster_preset_prgm_by_name(preset: str) -> bool:
    """
    Activate EventMaster program preset (preview + transition)
    Sequence: activate preview -> wait 100ms -> execute transition

    Args:
        preset: Preset name to activate

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"[EventMaster] Activating program preset: {preset}")

        # Activate preview preset
        if not eventmaster_preset_prvw_by_name(preset):
            return False

        # Wait 100ms
        time.sleep(0.1)

        # Execute transition
        return eventmaster_alltrans()

    except Exception as e:
        print(f"[EventMaster] Error activating program preset: {e}")
        return False


# =============================================================================
# Millumin Controls
# =============================================================================

def millumin_launch_column_by_name(column: str) -> bool:
    """
    Launch Millumin column by name

    Args:
        column: Column name to launch

    Returns:
        True if successful, False otherwise
    """
    try:
        address = os.getenv('MILLUMIN_OUT_ADDRESS', '10.10.20.255')
        port = int(os.getenv('MILLUMIN_OUT_PORT', 5000))
        path = "/millumin/action/launchColumn"

        print(f"[Millumin] Launching column: {column}")
        return osc_send(address, port, path, column)

    except Exception as e:
        print(f"[Millumin] Error launching column: {e}")
        return False


# =============================================================================
# StageTimer Controls
# =============================================================================

def stagetimer_control(action: str, minutes: Optional[int] = None, seconds: Optional[int] = None) -> bool:
    """
    Send control command to StageTimer.io

    Args:
        action: Action to perform (start_timer, stop_timer, reset_timer, update_timer, enable_blackout, disable_blackout)
        minutes: Optional minutes for update_timer action
        seconds: Optional seconds for update_timer action

    Returns:
        True if successful, False otherwise
    """
    try:
        base_url = os.getenv('STAGETIMER_OUT_URL', 'http://10.19.53.21:3000/api/v1/')
        suffix = os.getenv('STAGETIMER_OUT_SUFFIX', '')

        # Build URL based on action
        if action == "update_timer" and minutes is not None and seconds is not None:
            url = f"{base_url}{action}{suffix}&minutes={minutes}&seconds={seconds}"
        else:
            url = f"{base_url}{action}{suffix}"

        print(f"[StageTimer] Sending action: {action}")
        response = get_request(url)
        return response is not None

    except Exception as e:
        print(f"[StageTimer] Error sending control: {e}")
        return False
