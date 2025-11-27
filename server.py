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
        self.previous_ignition_status = None  # Track previous ignition status to detect changes
        self.current_latitude = None  # Track most recent latitude from STT messages
        self.current_longitude = None  # Track most recent longitude from STT messages
        self.mac_previous_timestamps = {}  # Track previous timestamp for each MAC ID to calculate frequency
        self.current_input_voltage = None  # Track most recent input voltage from STT messages (in millivolts)
        
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
                            
                            # Update ignition status, latitude, longitude, and other status fields from STT messages
                            report_type = parsed.get('report_type', 'Unknown')
                            if 'STT' in report_type or 'Status Report' in report_type:
                                status = parsed.get('status', {})
                                ignition_status = status.get('ignition_status', 'OFF')
                                
                                # Extract input voltage from status and validate
                                input_voltage_mv = status.get('input_voltage_mv')
                                if input_voltage_mv is not None:
                                    # Validate voltage: should be between 10000mV (10V) and 20000mV (20V)
                                    # Typical values are 12700mV (12.7V) or 15000mV (15.0V)
                                    if 10000 <= input_voltage_mv <= 20000:
                                        self.current_input_voltage = input_voltage_mv
                                    else:
                                        # If voltage is out of range, try alternative parsing locations
                                        # Voltage might be in a different location in the message
                                        # For now, set to None if invalid
                                        self.current_input_voltage = None
                                        print(f"Warning: Invalid voltage reading {input_voltage_mv}mV, expected 10000-20000mV")
                                
                                if ignition_status:
                                    # Check if ignition state has changed
                                    if self.previous_ignition_status is not None and self.previous_ignition_status != ignition_status:
                                        # Ignition state changed - record it in the table
                                        change_timestamp = datetime.now().isoformat()
                                        ignition_change_entry = {
                                            'timestamp': change_timestamp,
                                            'mac_id': f'IGNITION_STATE_CHANGE_{ignition_status}',  # Special marker for ignition changes
                                            'ignition_status': ignition_status,
                                            'latitude': self.current_latitude,
                                            'longitude': self.current_longitude,
                                            'input_voltage': self.current_input_voltage,
                                            'is_ignition_change': True,  # Flag to identify ignition change events
                                            'previous_status': self.previous_ignition_status,
                                            'new_status': ignition_status
                                        }
                                        self.beacon_scan_store.append(ignition_change_entry)
                                        
                                        # Log the ignition state change
                                        self._log_beacon_scan(ignition_change_entry)
                                        
                                        # Keep only last 10000 scans
                                        if len(self.beacon_scan_store) > 10000:
                                            self.beacon_scan_store.pop(0)
                                    
                                    self.previous_ignition_status = ignition_status
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
                                
                                # Debug: Print sensor info
                                if sensors:
                                    print(f"DEBUG: First sensor: {sensors[0]}")
                                    print(f"DEBUG: Processing {len(sensors)} sensors for beacon storage")
                                
                                # Count total number of BLE MAC IDs in this message
                                # Count unique MAC addresses
                                unique_mac_ids = set()
                                for sensor in sensors:
                                    mac_address = sensor.get('mac_address') or sensor.get('mac_address_raw', 'N/A')
                                    if mac_address and mac_address != 'N/A':
                                        unique_mac_ids.add(mac_address)
                                ble_mac_count = len(unique_mac_ids)
                                
                                # Debug: Print sensor processing info
                                for sensor in sensors:
                                    mac_address = sensor.get('mac_address') or sensor.get('mac_address_raw', 'N/A')
                                    if mac_address and mac_address != 'N/A':
                                        print(f"DEBUG: Sensor MAC: {mac_address}, sensor keys: {list(sensor.keys())}")
                                
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
                                            # Calculate frequency (time difference from previous update)
                                            frequency_seconds = None
                                            previous_timestamp = self.mac_previous_timestamps.get(mac_address)
                                            
                                            if previous_timestamp:
                                                try:
                                                    # Parse timestamps and calculate difference
                                                    # Handle ISO format with or without timezone
                                                    def parse_iso_timestamp(ts_str):
                                                        # Remove 'Z' and replace with +00:00 for timezone
                                                        ts_clean = ts_str.replace('Z', '+00:00')
                                                        # Try parsing with fromisoformat
                                                        try:
                                                            dt = datetime.fromisoformat(ts_clean)
                                                        except (ValueError, AttributeError):
                                                            # Fallback: parse without timezone info
                                                            # Remove timezone offset if present
                                                            if '+' in ts_clean:
                                                                ts_no_tz = ts_clean.split('+')[0]
                                                            elif len(ts_clean) > 19 and ts_clean[-6] in ['+', '-']:
                                                                ts_no_tz = ts_clean[:-6]
                                                            else:
                                                                ts_no_tz = ts_clean
                                                            # Try different formats
                                                            for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S']:
                                                                try:
                                                                    # Remove microseconds if format doesn't include them
                                                                    if '.%f' in fmt:
                                                                        dt = datetime.strptime(ts_no_tz, fmt)
                                                                    else:
                                                                        dt = datetime.strptime(ts_no_tz.split('.')[0], fmt)
                                                                    break
                                                                except ValueError:
                                                                    continue
                                                            else:
                                                                raise ValueError(f"Unable to parse timestamp: {ts_str}")
                                                        # Make timezone-aware if naive (use local timezone)
                                                        if dt.tzinfo is None:
                                                            # Use local timezone
                                                            local_tz = datetime.now().astimezone().tzinfo
                                                            dt = dt.replace(tzinfo=local_tz)
                                                        return dt
                                                    
                                                    prev_dt = parse_iso_timestamp(previous_timestamp)
                                                    curr_dt = parse_iso_timestamp(scan_timestamp)
                                                    time_diff = (curr_dt - prev_dt).total_seconds()
                                                    if time_diff > 0:  # Only set if positive (valid update)
                                                        frequency_seconds = time_diff
                                                except Exception as e:
                                                    print(f"Error calculating frequency for {mac_address}: {e}")
                                            
                                            # Extract RSSI, battery level, and raw data from sensor
                                            rssi_value = sensor.get('rssi')
                                            battery_level = sensor.get('battery_level')  # Battery level as percentage (0-100)
                                            raw_data = sensor.get('raw_data', '')
                                            
                                            # Add to beacon scan store with current ignition status, GPS coordinates, frequency, and status fields
                                            beacon_scan = {
                                                'timestamp': scan_timestamp,
                                                'mac_id': mac_address,
                                                'ignition_status': self.current_ignition_status,
                                                'latitude': self.current_latitude,
                                                'longitude': self.current_longitude,
                                                'frequency_seconds': frequency_seconds,  # Time since last update for this MAC
                                                'input_voltage': self.current_input_voltage,  # Input voltage in millivolts from STT messages
                                                'ble_mac_count': ble_mac_count,  # Number of unique BLE MAC IDs in this message
                                                'rssi': rssi_value,  # RSSI value for this BLE beacon
                                                'battery_level': battery_level  # Battery level as percentage (0-100)
                                            }
                                            self.beacon_scan_store.append(beacon_scan)
                                            
                                            # Debug: Print beacon storage info
                                            print(f"DEBUG: Stored beacon scan #{len(self.beacon_scan_store)}: MAC={mac_address}, timestamp={scan_timestamp}")
                                            
                                            # Update previous timestamp for this MAC ID
                                            self.mac_previous_timestamps[mac_address] = scan_timestamp
                                            
                                            # Log the beacon scan to file
                                            self._log_beacon_scan(beacon_scan)
                                            
                                            # Keep only last 10000 scans
                                            if len(self.beacon_scan_store) > 10000:
                                                self.beacon_scan_store.pop(0)
                                
                                # Debug: Print summary after processing all sensors
                                stored_count = len([s for s in sensors if (s.get('mac_address') or s.get('mac_address_raw')) and (s.get('mac_address', '').upper().replace(':', '').startswith('AC233') or s.get('mac_address', '').upper().replace(':', '').startswith('C300') or s.get('is_target_mac', False))])
                                print(f"DEBUG: Total beacons stored from this BDA message: {stored_count}, Total in store: {len(self.beacon_scan_store)}")
                        
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
                'longitude': beacon_scan.get('longitude'),
                'frequency_seconds': beacon_scan.get('frequency_seconds'),
                'input_voltage': beacon_scan.get('input_voltage'),
                'ble_mac_count': beacon_scan.get('ble_mac_count'),
                'rssi': beacon_scan.get('rssi'),
                'battery_level': beacon_scan.get('battery_level')
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

