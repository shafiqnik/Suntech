"""
Socket server that listens on port 18160 for Suntech messages
"""
import socket
import threading
from datetime import datetime
from typing import List, Dict, Any
from suntech_parser import SuntechParser
import os
import json


class ThreadedServer:
    """Threaded TCP server for receiving Suntech messages"""
    
    def __init__(self, host: str, port: int, message_store: List[Dict[str, Any]], beacon_scan_store: List[Dict[str, Any]]):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.message_store = message_store
        self.beacon_scan_store = beacon_scan_store
        self.parser = SuntechParser()
        self.lock = threading.Lock()
        self.current_ignition_status = "OFF"  # Track most recent ignition status from STT messages
        self.current_latitude = None  # Track most recent latitude from STT messages
        self.current_longitude = None  # Track most recent longitude from STT messages
        
        # Setup logging directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(script_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Log file path (daily log files)
        today = datetime.now().strftime('%Y%m%d')
        self.log_file = os.path.join(self.log_dir, f'beacon_scans_{today}.log')
    
    def listen(self):
        """Start listening for connections"""
        self.sock.listen(5)
        print(f"Suntech server listening on port {self.port}...")
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            print(f"New connection from {address}")
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()
    
    def listen_to_client(self, client: socket.socket, address: tuple):
        """Handle messages from a client"""
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    print(f'Received data from {address}: {len(data)} bytes')
                    print(f'Raw data (hex): {data.hex()[:100]}...')
                    
                    # Parse the message
                    try:
                        parsed = self.parser.parse_message(data)
                        
                        # Store the parsed message
                        with self.lock:
                            self.message_store.append(parsed)
                            # Keep only last 1000 messages
                            if len(self.message_store) > 1000:
                                self.message_store.pop(0)
                            
                            # Update ignition status, latitude, and longitude from STT messages
                            report_type = parsed.get('report_type', 'Unknown')
                            if 'STT' in report_type or 'Status Report' in report_type:
                                status = parsed.get('status', {})
                                ignition_status = status.get('ignition_status', 'OFF')
                                if ignition_status:
                                    self.current_ignition_status = ignition_status
                                
                                # Extract GPS coordinates
                                gps = parsed.get('gps', {})
                                if gps:
                                    lat_str = gps.get('latitude', '')
                                    lon_str = gps.get('longitude', '')
                                    if lat_str and lat_str != '0.000000':
                                        try:
                                            self.current_latitude = float(lat_str)
                                        except (ValueError, TypeError):
                                            pass
                                    if lon_str and lon_str != '0.000000':
                                        try:
                                            self.current_longitude = float(lon_str)
                                        except (ValueError, TypeError):
                                            pass
                            
                            # Extract and store BLE beacon scans
                            if 'BDA' in report_type or 'BLE Sensor Data Report' in report_type:
                                sensors = parsed.get('sensors', [])
                                scan_timestamp = datetime.now().isoformat()
                                
                                # Extract ALL beacons starting with AC233 or C300 (not just target ones)
                                # Also include all sensors to ensure nothing is missed
                                for sensor in sensors:
                                    mac_address = sensor.get('mac_address') or sensor.get('mac_address_raw', 'N/A')
                                    if mac_address and mac_address != 'N/A':
                                        # Check if MAC starts with AC233 or C300 (case insensitive)
                                        mac_upper = mac_address.upper().replace(':', '')
                                        # Match AC233 (5 chars) or C300 (4 chars)
                                        is_target = (mac_upper.startswith('AC233') or 
                                                   mac_upper.startswith('C300'))
                                        
                                        # Store if it matches our criteria OR if it was marked as target
                                        if is_target or sensor.get('is_target_mac', False):
                                            # Add to beacon scan store with current ignition status and GPS coordinates
                                            beacon_scan = {
                                                'timestamp': scan_timestamp,
                                                'mac_id': mac_address,
                                                'ignition_status': self.current_ignition_status,
                                                'latitude': self.current_latitude,
                                                'longitude': self.current_longitude
                                            }
                                            self.beacon_scan_store.append(beacon_scan)
                                            
                                            # Log the beacon scan to file
                                            self._log_beacon_scan(beacon_scan)
                                            
                                            # Keep only last 10000 scans
                                            if len(self.beacon_scan_store) > 10000:
                                                self.beacon_scan_store.pop(0)
                        
                        print(f"Parsed message type: {report_type}")
                        
                        # Print entire raw message for BDA/SNB (BLE Sensor Data Report)
                        if 'BDA' in report_type or 'BLE Sensor Data Report' in report_type:
                            raw_hex = data.hex()
                            print("\n" + "="*80)
                            print(f"BLE SENSOR DATA REPORT - COMPLETE RAW MESSAGE")
                            print("="*80)
                            print(f"Message Length: {len(data)} bytes ({len(raw_hex)} hex characters)")
                            print(f"Raw Data (Hex): {raw_hex}")
                            print("="*80 + "\n")
                        
                    except Exception as e:
                        print(f"Error parsing message: {e}")
                        error_msg = {
                            "timestamp": __import__('datetime').datetime.now().isoformat(),
                            "error": f"Parse error: {str(e)}",
                            "raw_data": data.hex()
                        }
                        with self.lock:
                            self.message_store.append(error_msg)
                    
                    # Echo back the received data (as per example)
                    response = data
                    client.send(response)
                else:
                    raise Exception('Client disconnected')
            except Exception as e:
                print(f"Client {address} disconnected: {e}")
                client.close()
                return False
    
    def _log_beacon_scan(self, beacon_scan: Dict[str, Any]):
        """Log beacon scan to file"""
        try:
            # Update log file path for today
            today = datetime.now().strftime('%Y%m%d')
            self.log_file = os.path.join(self.log_dir, f'beacon_scans_{today}.log')
            
            # Format log entry
            log_entry = {
                'timestamp': beacon_scan.get('timestamp', ''),
                'mac_id': beacon_scan.get('mac_id', ''),
                'ignition_status': beacon_scan.get('ignition_status', 'N/A'),
                'latitude': beacon_scan.get('latitude'),
                'longitude': beacon_scan.get('longitude')
            }
            
            # Write to log file (append mode)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Error logging beacon scan: {e}")


if __name__ == "__main__":
    # For testing
    message_store = []
    beacon_scan_store = []
    ThreadedServer('', 18160, message_store, beacon_scan_store).listen()

