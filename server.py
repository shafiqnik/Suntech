"""
Socket server that listens on port 18160 for Suntech messages
"""
import socket
import threading
from datetime import datetime
from typing import List, Dict, Any
from suntech_parser import SuntechParser


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
                            
                            # Extract and store BLE beacon scans
                            report_type = parsed.get('report_type', 'Unknown')
                            if 'BDA' in report_type or 'BLE Sensor Data Report' in report_type:
                                sensors = parsed.get('sensors', [])
                                scan_timestamp = datetime.now().isoformat()
                                
                                # Extract all target beacons (AC233F or C3000)
                                for sensor in sensors:
                                    if sensor.get('is_target_mac', False):
                                        mac_address = sensor.get('mac_address') or sensor.get('mac_address_raw', 'N/A')
                                        if mac_address and mac_address != 'N/A':
                                            # Add to beacon scan store
                                            beacon_scan = {
                                                'timestamp': scan_timestamp,
                                                'mac_id': mac_address
                                            }
                                            self.beacon_scan_store.append(beacon_scan)
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


if __name__ == "__main__":
    # For testing
    message_store = []
    beacon_scan_store = []
    ThreadedServer('', 18160, message_store, beacon_scan_store).listen()

