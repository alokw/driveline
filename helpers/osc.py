"""
OSC System - Listener, Sender, and Database
Handles all OSC communication with queue-based rate limiting
"""

import asyncio
import queue
import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from flask import current_app


class OSCDatabase:
    """
    Thread-safe in-memory database for storing OSC message values.
    Each OSC path has a single entry with the most recent value.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def set(self, path: str, value: Any) -> None:
        """Set a value for an OSC path and trigger callbacks"""
        with self._lock:
            old_value = self._data.get(path)
            self._data[path] = value

            # Trigger callbacks if value changed or callback is new
            if old_value != value:
                # Debug: Log important value changes
                if 'heartbeat' in path or 'trackposition' in path:
                    print(f"[OSC Database] Updated: {path} = {value}")

                for callback in self._callbacks.get(path, []):
                    try:
                        callback(path, value)
                    except Exception as e:
                        print(f"[OSC Database] Callback error for {path}: {e}")

    def get(self, path: str, default: Any = None) -> Any:
        """Get the current value for an OSC path"""
        with self._lock:
            return self._data.get(path, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all OSC path/values as a dictionary"""
        with self._lock:
            return dict(self._data)

    def register_callback(self, path: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback to be triggered when an OSC path receives a value"""
        with self._lock:
            self._callbacks[path].append(callback)

    def clear(self) -> None:
        """Clear all stored values"""
        with self._lock:
            self._data.clear()


class OSCSender:
    """
    Queue-based OSC sender with rate limiting to prevent message flooding.
    """

    def __init__(
        self,
        send_interval: float = 0.01,
        queue_size: int = 1000,
        max_batch_size: int = 10
    ):
        """
        Initialize OSC sender

        Args:
            send_interval: Minimum seconds between sends (default: 0.01 = 10ms)
            queue_size: Maximum queue size (default: 1000)
            max_batch_size: Maximum messages to send in one batch (default: 10)
        """
        self.send_interval = send_interval
        self.queue = queue.Queue(maxsize=queue_size)
        self.max_batch_size = max_batch_size
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background sender thread"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._send_loop, daemon=True)
            self._thread.start()
            print("[OSC Sender] Started")

    def stop(self) -> None:
        """Stop the background sender thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            print("[OSC Sender] Stopped")

    def send(self, address: str, port: int, path: str, value: Union[str, float, int, List]) -> bool:
        """
        Queue an OSC message to be sent

        Args:
            address: IP address to send to
            port: UDP port to send to
            path: OSC address path (e.g., "/d3/showcontrol/cue")
            value: OSC value (string, float, int, or list)

        Returns:
            True if message was queued, False if queue is full
        """
        try:
            self.queue.put({
                'address': address,
                'port': port,
                'path': path,
                'value': value,
                'timestamp': datetime.now()
            }, block=False)
            # Reduce verbosity - only log when queue is full
            # print(f"[OSC Sender] Queued: {path} = {value} -> {address}:{port}")
            return True
        except queue.Full:
            print(f"[OSC Sender] Queue full, message dropped: {path}")
            return False

    def _send_loop(self) -> None:
        """Background thread that sends queued messages"""
        last_send_time = 0

        while self._running:
            try:
                # Rate limiting
                current_time = time.time()
                time_since_last_send = current_time - last_send_time

                if time_since_last_send < self.send_interval:
                    time.sleep(self.send_interval - time_since_last_send)
                    continue

                # Batch messages if available
                messages_to_send = []
                while len(messages_to_send) < self.max_batch_size:
                    try:
                        msg = self.queue.get_nowait()
                        messages_to_send.append(msg)
                    except queue.Empty:
                        break

                if not messages_to_send:
                    time.sleep(0.001)
                    continue

                # Send batch
                for msg in messages_to_send:
                    self._send_message(msg)

                last_send_time = time.time()

            except Exception as e:
                print(f"[OSC Sender] Error in send loop: {e}")
                time.sleep(0.1)

    def _send_message(self, msg: Dict) -> None:
        """Actually send an OSC message via UDP"""
        try:
            # Create UDP client
            client = SimpleUDPClient(msg['address'], msg['port'])

            # Send message
            value = msg['value']
            if isinstance(value, list):
                client.send_message(msg['path'], value)
            else:
                client.send_message(msg['path'], value)

            # Only log important messages, not every OSC send
            # print(f"[OSC Sender] Sent: {msg['path']} = {value} -> {msg['address']}:{msg['port']}")

        except Exception as e:
            print(f"[OSC Sender] Error sending message: {e}")


class OSCListener:
    """
    OSC listener that supports multiple ports using python-osc.
    Runs in background threads.
    """

    def __init__(self, osc_db: OSCDatabase):
        """
        Initialize OSC listener

        Args:
            osc_db: OSCDatabase instance to store received values
        """
        self.osc_db = osc_db
        self._servers: Dict[int, BlockingOSCUDPServer] = {}
        self._threads: Dict[int, threading.Thread] = {}
        self._running = False

    def start(self, port: int) -> bool:
        """
        Start listening on a UDP port

        Args:
            port: UDP port to listen on

        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Create dispatcher
            dispatcher = Dispatcher()
            dispatcher.set_default_handler(self._handle_osc_message)

            # Create OSC server
            server = BlockingOSCUDPServer(("0.0.0.0", port), dispatcher)

            # Start in background thread
            thread = threading.Thread(target=self._run_server, args=(server, port), daemon=True)
            thread.start()

            self._servers[port] = server
            self._threads[port] = thread
            print(f"[OSC Listener] Started listening on port {port}")
            return True

        except Exception as e:
            print(f"[OSC Listener] Error starting server on port {port}: {e}")
            return False

    def _run_server(self, server: BlockingOSCUDPServer, port: int) -> None:
        """Run the OSC server in a thread"""
        try:
            server.serve_forever()
        except Exception as e:
            print(f"[OSC Listener] Server error on port {port}: {e}")

    def stop(self, port: Optional[int] = None) -> None:
        """
        Stop listening on a port or all ports

        Args:
            port: Specific port to stop, or None to stop all
        """
        if port:
            if port in self._servers:
                try:
                    self._servers[port].shutdown()
                except:
                    pass
                del self._servers[port]
                del self._threads[port]
                print(f"[OSC Listener] Stopped listening on port {port}")
        else:
            for p, server in self._servers.items():
                try:
                    server.shutdown()
                except:
                    pass
            self._servers.clear()
            self._threads.clear()
            print("[OSC Listener] Stopped all listeners")

    def _handle_osc_message(self, address: str, *args) -> None:
        """
        Handle incoming OSC message

        Args:
            address: OSC address path
            *args: OSC values
        """
        try:
            path = address
            value = args[0] if len(args) == 1 else list(args)

            # Store in database
            self.osc_db.set(path, value)

            # Reduce console spam - don't log every OSC message
            # print(f"[OSC Listener] Received: {path} = {value}")

        except Exception as e:
            print(f"[OSC Listener] Error handling message: {e}")


# Singleton instances
osc_db = OSCDatabase()
osc_sender = OSCSender()
osc_listener = OSCListener(osc_db)


def osc_send(address: str, port: int, path: str, value: Union[str, float, int, List]) -> bool:
    """
    Send an OSC message (queued)

    Args:
        address: IP address to send to
        port: UDP port to send to
        path: OSC address path
        value: OSC value

    Returns:
        True if queued successfully, False otherwise
    """
    return osc_sender.send(address, port, path, value)


def get_osc_value(path: str, default: Any = None) -> Any:
    """
    Get current value from OSC database

    Args:
        path: OSC path to retrieve
        default: Default value if path not found

    Returns:
        Current value or default
    """
    return osc_db.get(path, default)


def get_all_osc_values() -> Dict[str, Any]:
    """Get all OSC path/values"""
    return osc_db.get_all()


def register_osc_callback(path: str, callback: Callable[[str, Any], None]) -> None:
    """
    Register a callback for an OSC path

    Args:
        path: OSC path to watch
        callback: Function to call when value changes
    """
    osc_db.register_callback(path, callback)
