"""
SuntechParser - Parses Suntech ST6560 binary protocol messages
Supports STT (Status Report) and BDA/SNB (BLE Sensor Data Report) message types
"""
import struct
from datetime import datetime
from typing import Dict, Any


class SuntechParser:
    """Parser for Suntech ST6560 binary protocol messages"""
    
    @staticmethod
    def bcd_to_dec(bcd_bytes: bytes) -> int:
        """Converts BCD bytes to decimal integer.
        BCD format: each byte contains two decimal digits (each 4 bits).
        Example: 0x19 = 0001 1001 = 1 and 9 = 19 decimal
        """
        result = 0
        for byte in bcd_bytes:
            # Extract high and low nibbles (4 bits each)
            high_nibble = (byte >> 4) & 0x0F
            low_nibble = byte & 0x0F
            
            # Validate BCD (each nibble must be 0-9)
            if high_nibble > 9 or low_nibble > 9:
                # Invalid BCD, try hex interpretation as fallback
                # This handles cases where data might not be pure BCD
                return int("".join(f'{b:02X}' for b in bcd_bytes), 16)
            
            # Combine: high_nibble * 10 + low_nibble
            result = result * 100 + (high_nibble * 10 + low_nibble)
        
        return result
    
    @staticmethod
    def parse_suntech_date(date_bytes: bytes) -> str:
        """Parses YY MM DD BCD to YYYYMMDD string."""
        try:
            # Parse BCD: each byte is two digits
            year_byte = date_bytes[0] if len(date_bytes) > 0 else 0
            month_byte = date_bytes[1] if len(date_bytes) > 1 else 0
            day_byte = date_bytes[2] if len(date_bytes) > 2 else 0
            
            year = 2000 + ((year_byte >> 4) & 0x0F) * 10 + (year_byte & 0x0F)
            month = ((month_byte >> 4) & 0x0F) * 10 + (month_byte & 0x0F)
            day = ((day_byte >> 4) & 0x0F) * 10 + (day_byte & 0x0F)
            
            return f"{year:04d}{month:02d}{day:02d}"
        except (IndexError, ValueError) as e:
            # Fallback to hex representation
            bcd_str = "".join(f'{b:02X}' for b in date_bytes)
            year = 2000 + int(bcd_str[:2], 16) if len(bcd_str) >= 2 else 2000
            return f"{year}{bcd_str[2:4] if len(bcd_str) >= 4 else '00'}{bcd_str[4:6] if len(bcd_str) >= 6 else '00'}"
    
    @staticmethod
    def parse_suntech_time(time_bytes: bytes) -> str:
        """Parses HH MM SS BCD to HH:MM:SS string."""
        try:
            # Parse BCD: each byte is two digits
            hour_byte = time_bytes[0] if len(time_bytes) > 0 else 0
            minute_byte = time_bytes[1] if len(time_bytes) > 1 else 0
            second_byte = time_bytes[2] if len(time_bytes) > 2 else 0
            
            hour = ((hour_byte >> 4) & 0x0F) * 10 + (hour_byte & 0x0F)
            minute = ((minute_byte >> 4) & 0x0F) * 10 + (minute_byte & 0x0F)
            second = ((second_byte >> 4) & 0x0F) * 10 + (second_byte & 0x0F)
            
            return f"{hour:02d}:{minute:02d}:{second:02d}"
        except (IndexError, ValueError) as e:
            # Fallback to hex representation
            bcd_str = "".join(f'{b:02X}' for b in time_bytes)
            return f"{bcd_str[:2] if len(bcd_str) >= 2 else '00'}:{bcd_str[2:4] if len(bcd_str) >= 4 else '00'}:{bcd_str[4:6] if len(bcd_str) >= 6 else '00'}"
    
    @staticmethod
    def parse_gps_coord(coord_bytes: bytes) -> float:
        """Converts 4-byte signed integer (Big Endian) to decimal coordinate (value / 1,000,000)."""
        value = struct.unpack('>i', coord_bytes)[0]
        return value / 1_000_000.0
    
    @staticmethod
    def parse_stt_report(data: bytes) -> Dict[str, Any]:
        """Parse STT (Status Report) message with header 0x81"""
        try:
            results = {}
            
            # Check minimum length (some variants may be shorter)
            if len(data) < 15:
                raise ValueError(f"STT message too short: {len(data)} bytes (expected at least 15)")
            
            # 1. Header and Basic ID (1 + 2 + 5 + 3 + 1 + 3 + 1 = 16 bytes)
            hdr = struct.unpack('>B', data[0:1])[0]
            pkt_len = struct.unpack('>H', data[1:3])[0]
            dev_id = SuntechParser.bcd_to_dec(data[3:8])
            report_map = struct.unpack('>I', b'\x00' + data[8:11])[0]
            model = struct.unpack('>B', data[11:12])[0]
            # SW_VER structure: 3 bytes BCD
            sw_ver_str = "".join(f'{b:02X}' for b in data[12:15])
            
            # 2. Time/Date & Cellular (15 to 33 bytes) - with bounds checking
            msg_type = struct.unpack('>B', data[15:16])[0] if len(data) > 15 else 0
            date = SuntechParser.parse_suntech_date(data[16:19]) if len(data) > 18 else "N/A"
            time = SuntechParser.parse_suntech_time(data[19:22]) if len(data) > 21 else "N/A"
            cell_id = struct.unpack('>I', data[22:26])[0] if len(data) > 25 else 0
            mcc = SuntechParser.bcd_to_dec(data[26:28]) if len(data) > 27 else 0
            mnc = SuntechParser.bcd_to_dec(data[28:30]) if len(data) > 29 else 0
            lac = struct.unpack('>H', data[30:32])[0] if len(data) > 31 else 0
            rx_lvl = struct.unpack('>B', data[32:33])[0] if len(data) > 32 else 0
            
            # 3. GPS Data (33 to 45 bytes) - with bounds checking
            lat = SuntechParser.parse_gps_coord(data[33:37]) if len(data) > 36 else 0.0
            lon = SuntechParser.parse_gps_coord(data[37:41]) if len(data) > 40 else 0.0
            spd = (struct.unpack('>H', data[41:43])[0] / 100.0) if len(data) > 42 else 0.0
            crs = (struct.unpack('>H', data[43:45])[0] / 100.0) if len(data) > 44 else 0.0
            satt = struct.unpack('>B', data[45:46])[0] if len(data) > 45 else 0
            fix = struct.unpack('>B', data[46:47])[0] if len(data) > 46 else 0
            
            # 4. Status (47 to 52 bytes) - with bounds checking
            in_state = struct.unpack('>B', data[47:48])[0] if len(data) > 47 else 0
            out_state = struct.unpack('>B', data[48:49])[0] if len(data) > 48 else 0
            mode = struct.unpack('>B', data[49:50])[0] if len(data) > 49 else 0
            rpt_type = struct.unpack('>B', data[50:51])[0] if len(data) > 50 else 0
            msg_num = struct.unpack('>H', data[51:53])[0] if len(data) > 52 else 0
            
            # 5. Final fields and mapping start (53 onwards) - with bounds checking
            reserved1 = struct.unpack('>B', data[53:54])[0] if len(data) > 53 else 0
            assign_map = struct.unpack('>I', data[54:58])[0] if len(data) > 57 else 0
            
            # Create timestamp
            timestamp = datetime.now().isoformat()
            
            # Include raw data for keyword detection
            raw_data_hex = data.hex()
            
            results = {
                "timestamp": timestamp,
                "report_type": "STT (Status Report)",
                "raw_data": raw_data_hex,
                "header": f"0x{hdr:02X} (No ACK required)",
                "device_id_esn": dev_id,
                "packet_length": pkt_len,
                "model_id": model,
                "software_version": f"{sw_ver_str[0]}.{sw_ver_str[1]}.{sw_ver_str[2:]}",
                "message_type": "Real Time (1)" if msg_type == 1 else "Stored (0)",
                "timestamp_gps": f"{date} {time}",
                "gps": {
                    "latitude": f"{lat:.6f}",
                    "longitude": f"{lon:.6f}",
                    "speed_kmh": f"{spd:.2f}",
                    "course_deg": f"{crs:.2f}",
                    "satellites": satt,
                    "fix_status": {0: "Not Fixed", 1: "Fixed", 3: "DR Activated"}.get(fix, str(fix)),
                },
                "cellular": {
                    "mcc": mcc,
                    "mnc": mnc,
                    "lac": f"{lac:04X}",
                    "rx_level_rssi": rx_lvl,
                    "cell_id": f"{cell_id:08X}",
                },
                "status": {
                    "input_state_hex": f"0x{in_state:02X}",
                    "output_state_hex": f"0x{out_state:02X}",
                    "device_mode": {1: "Driving", 5: "Deactivate Zone"}.get(mode, str(mode)),
                    "report_type_id": rpt_type,
                    "message_number": msg_num,
                },
                "assign_map_custom_headers": f"0x{assign_map:08X}",
                "raw_trailing_data_length": max(0, len(data) - 58),
                "message_length": len(data),
            }
            return results
        except Exception as e:
            # Return error with context
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"STT parse error: {str(e)}",
                "raw_data": data.hex(),
                "data_length": len(data)
            }
    
    @staticmethod
    def parse_bda_report(data: bytes) -> Dict[str, Any]:
        """Parse BDA/SNB (BLE Sensor Data Report) message with header 0xAA"""
        try:
            idx = 0
            
            # Check minimum length (header + basic fields = ~15 bytes minimum)
            if len(data) < 15:
                raise ValueError(f"BDA message too short: {len(data)} bytes (expected at least 15)")
            
            # Header and Basic ID
            hdr = struct.unpack('>B', data[idx:idx+1])[0]
            idx += 1
            pkt_len = struct.unpack('>H', data[idx:idx+2])[0]
            idx += 2
            dev_id = SuntechParser.bcd_to_dec(data[idx:idx+5])
            idx += 5
            report_map = struct.unpack('>I', b'\x00' + data[idx:idx+3])[0]
            idx += 3
            model = struct.unpack('>B', data[idx:idx+1])[0]
            idx += 1
            sw_ver_str = "".join(f'{b:02X}' for b in data[idx:idx+3])
            idx += 3
            
            # BLE Scan Metadata
            if idx + 1 > len(data):
                raise ValueError("BDA message incomplete: missing BLE scan status")
            ble_scan_status = struct.unpack('>B', data[idx:idx+1])[0]
            idx += 1
            
            if idx + 1 > len(data):
                raise ValueError("BDA message incomplete: missing total_no")
            total_no = struct.unpack('>B', data[idx:idx+1])[0]
            idx += 1
            
            if idx + 1 > len(data):
                raise ValueError("BDA message incomplete: missing curr_no")
            curr_no = struct.unpack('>B', data[idx:idx+1])[0]
            idx += 1
            
            if idx + 2 > len(data):
                raise ValueError("BDA message incomplete: missing ble_sen_cnt")
            ble_sen_cnt = struct.unpack('>H', data[idx:idx+2])[0]
            idx += 2
            
            # Scan timestamp and location (may be missing in very short messages)
            scan_date = None
            scan_time = None
            scan_lat = None
            scan_lon = None
            
            if idx + 3 <= len(data):
                scan_date = SuntechParser.parse_suntech_date(data[idx:idx+3])
                idx += 3
            if idx + 3 <= len(data):
                scan_time = SuntechParser.parse_suntech_time(data[idx:idx+3])
                idx += 3
            if idx + 4 <= len(data):
                scan_lat = SuntechParser.parse_gps_coord(data[idx:idx+4])
                idx += 4
            if idx + 4 <= len(data):
                scan_lon = SuntechParser.parse_gps_coord(data[idx:idx+4])
                idx += 4
            
            # Parse BLE Sensor Data
            # Structure for each sensor:
            # - BLE_SEN_DATA_SIZE (2 bytes) - Size of raw data
            # - BLE_SEN_DATA (variable, up to 521 bytes) - Raw BLE data
            # - BLE_SEN_MAC (6 bytes) - MAC address (may be little endian)
            # - BLE_SEN_RSSI (1 byte) - RSSI value
            sensors = []
            start_idx = idx
            remaining_data = data[idx:]
            data_hex = remaining_data.hex().upper()
            
            # Helper function to extract MAC address from bytes (handles both endian formats)
            def extract_mac(mac_bytes):
                """Extract MAC address, trying both big and little endian"""
                # Big endian (standard): AC:23:3F:XX:XX:XX
                mac_hex_be = mac_bytes.hex().upper()
                # Little endian (reversed bytes): reverse the byte order
                mac_bytes_le = bytes(reversed(mac_bytes))
                mac_hex_le = mac_bytes_le.hex().upper()
                
                # Check which format matches our target MACs
                mac_prefix_be = mac_hex_be[:6]  # First 3 bytes big endian
                mac_prefix_le = mac_hex_le[:6]  # First 3 bytes little endian
                
                # Determine if this is a target MAC in either format
                # Support both C30000 and C3000 (user mentioned C3000)
                is_target_be = (mac_prefix_be.startswith('AC233F') or 
                               mac_prefix_be.startswith('C30000') or 
                               mac_prefix_be.startswith('C3000'))
                is_target_le = (mac_prefix_le.startswith('AC233F') or 
                               mac_prefix_le.startswith('C30000') or 
                               mac_prefix_le.startswith('C3000'))
                
                # Use the format that matches target, or default to big endian
                if is_target_le and not is_target_be:
                    # Little endian format detected
                    mac_hex = mac_hex_le
                    mac_bytes_final = mac_bytes_le
                    endian = 'little'
                else:
                    # Big endian format (default)
                    mac_hex = mac_hex_be
                    mac_bytes_final = mac_bytes
                    endian = 'big'
                
                # Format MAC address: AC:23:3F or C3:00:00 or C3:00:0X
                mac_formatted = ':'.join([mac_hex[i:i+2] for i in range(0, len(mac_hex), 2)])
                mac_prefix = mac_hex[:6]
                # Check if target MAC (support AC233F, C30000, or C3000)
                is_target = (mac_prefix.startswith('AC233F') or 
                           mac_prefix.startswith('C30000') or 
                           mac_prefix.startswith('C3000') or 
                           is_target_le)
                
                return {
                    'mac_hex': mac_hex,
                    'mac_formatted': mac_formatted,
                    'mac_bytes_original': mac_bytes.hex().upper(),
                    'endian': endian,
                    'is_target': is_target
                }
            
            # Try to parse sensors using the expected structure
            for sensor_idx in range(ble_sen_cnt):
                if idx >= len(data):
                    break
                
                sensor_data = {}
                
                # BLE_SEN_DATA_SIZE (2 bytes)
                if idx + 2 > len(data):
                    break
                data_size = struct.unpack('>H', data[idx:idx+2])[0]
                idx += 2
                sensor_data['data_size'] = data_size
                
                # BLE_SEN_DATA (variable size)
                if idx + data_size > len(data):
                    # Not enough data, break
                    break
                ble_raw_data = data[idx:idx+data_size]
                idx += data_size
                sensor_data['raw_data'] = ble_raw_data.hex()
                
                # BLE_SEN_MAC (6 bytes) - may be in little endian format
                if idx + 6 > len(data):
                    break
                mac_bytes = data[idx:idx+6]
                idx += 6
                
                # Extract MAC using helper function
                mac_info = extract_mac(mac_bytes)
                sensor_data['mac_address'] = mac_info['mac_formatted']
                sensor_data['mac_address_raw'] = mac_info['mac_hex']
                sensor_data['mac_bytes_original'] = mac_info['mac_bytes_original']
                sensor_data['mac_endian'] = mac_info['endian']
                sensor_data['is_target_mac'] = mac_info['is_target']
                
                # BLE_SEN_RSSI (1 byte)
                if idx + 1 > len(data):
                    break
                rssi_byte = struct.unpack('>B', data[idx:idx+1])[0]
                idx += 1
                # RSSI is signed: C3 = -61, convert to signed
                if rssi_byte > 127:
                    rssi_value = rssi_byte - 256
                else:
                    rssi_value = rssi_byte
                sensor_data['rssi'] = rssi_value
                sensor_data['rssi_hex'] = f"0x{rssi_byte:02X}"
                
                sensors.append(sensor_data)
            
            # Always scan the entire raw data for BLE beacons/tags starting with AC233F or C3000/C30000
            # This ensures we catch all beacons even if they're embedded in advertisement data
            data_hex_upper = data.hex().upper()
            
            # Always scan the entire raw data for BLE beacons/tags starting with AC233F or C3000/C30000
            # This ensures we catch all beacons even if they're embedded in advertisement data
            # Use longer prefixes first to avoid partial matches (C30000 before C3000)
            target_prefixes = ['AC233F', 'C30000', 'C3000', '3F23AC', '0000C3', '000C3']
            
            # Track found MAC addresses to avoid duplicates (use full 12-char hex MAC as key)
            found_macs = set()
            
            # Scan entire message for beacon patterns - check each byte position
            # This ensures we don't miss any beacons
            for byte_pos in range(len(data) - 5):  # Need at least 6 bytes for MAC
                # Extract 6 bytes for potential MAC address
                mac_bytes = data[byte_pos:byte_pos + 6]
                mac_info = extract_mac(mac_bytes)
                mac_hex = mac_info['mac_hex']
                
                # Check if this is a target MAC (AC233F or C3000/C30000)
                is_target = (mac_hex.startswith('AC233F') or 
                           mac_hex.startswith('C30000') or 
                           mac_hex.startswith('C3000'))
                
                if is_target:
                    # Create unique key to avoid duplicates
                    mac_key = mac_hex
                    
                    if mac_key not in found_macs:
                        found_macs.add(mac_key)
                        
                        # Try to find RSSI (usually 1 byte after MAC, but may vary)
                        rssi_value = 0
                        rssi_hex = '0x00'
                        if byte_pos + 7 <= len(data):
                            rssi_byte = struct.unpack('>B', data[byte_pos + 6:byte_pos + 7])[0]
                            if rssi_byte > 127:
                                rssi_value = rssi_byte - 256
                            else:
                                rssi_value = rssi_byte
                            rssi_hex = f"0x{rssi_byte:02X}"
                        
                        # Extract surrounding raw data for context (up to 20 bytes before and after)
                        context_start = max(0, byte_pos - 20)
                        context_end = min(len(data), byte_pos + 26)
                        context_data = data[context_start:context_end]
                        
                        sensor_data = {
                            'data_size': 0,
                            'raw_data': context_data.hex().upper(),
                            'mac_address': mac_info['mac_formatted'],
                            'mac_address_raw': mac_hex,
                            'mac_bytes_original': mac_info['mac_bytes_original'],
                            'mac_endian': mac_info['endian'],
                            'is_target_mac': True,
                            'rssi': rssi_value,
                            'rssi_hex': rssi_hex,
                            'found_in_raw_data': True,
                            'byte_position': byte_pos
                        }
                        sensors.append(sensor_data)
            
            # If we didn't parse all sensors from structured format, also try to find MACs in remaining data
            if len(sensors) < ble_sen_cnt and idx < len(data):
                # Search for MAC addresses in the remaining data (already handled above, but keep for compatibility)
                remaining_hex = data[idx:].hex().upper()
                
                for prefix in target_prefixes:
                    pos = remaining_hex.find(prefix)
                    if pos >= 0 and pos % 2 == 0:  # Must be at byte boundary
                        byte_pos = pos // 2
                        if byte_pos + 6 <= len(data[idx:]):
                            mac_bytes = data[idx + byte_pos:idx + byte_pos + 6]
                            mac_info = extract_mac(mac_bytes)
                            mac_hex = mac_info['mac_hex']
                            mac_key = mac_hex
                            
                            if mac_info['is_target'] and mac_key not in found_macs:
                                found_macs.add(mac_key)
                                sensor_data = {
                                    'data_size': 0,
                                    'raw_data': '',
                                    'mac_address': mac_info['mac_formatted'],
                                    'mac_address_raw': mac_hex,
                                    'mac_bytes_original': mac_info['mac_bytes_original'],
                                    'mac_endian': mac_info['endian'],
                                    'is_target_mac': True,
                                    'rssi': 0,
                                    'rssi_hex': '0x00',
                                    'found_in_raw_data': True
                                }
                                sensors.append(sensor_data)
            
            # Create timestamp
            timestamp = datetime.now().isoformat()
            
            # Include raw data for keyword detection
            raw_data_hex = data.hex()
            
            # Check if any sensor has target MAC addresses
            has_target_mac = any(s.get('is_target_mac', False) for s in sensors)
            
            results = {
                "timestamp": timestamp,
                "report_type": "BDA/SNB (BLE Sensor Data Report)",
                "raw_data": raw_data_hex,
                "header": f"0x{hdr:02X} (No ACK required)",
                "device_id_esn": dev_id,
                "packet_length": pkt_len,
                "model_id": model,
                "software_version": f"{sw_ver_str[0]}.{sw_ver_str[1]}.{sw_ver_str[2:]}",
                "ble_scan_status": "Scan Performed (1)" if ble_scan_status == 1 else "No Scan (0)",
                "total_reports_expected": total_no,
                "current_report_number": curr_no,
                "scanned_sensor_count": ble_sen_cnt,
                "timestamp_gps": f"{scan_date} {scan_time}" if scan_date and scan_time else "N/A",
                "location_scan_start": {
                    "latitude": f"{scan_lat:.6f}" if scan_lat is not None else "N/A",
                    "longitude": f"{scan_lon:.6f}" if scan_lon is not None else "N/A",
                } if scan_lat is not None and scan_lon is not None else None,
                "sensors": sensors,
                "sensors_parsed": len(sensors),
                "has_target_mac": has_target_mac,
                "raw_data_start_index": start_idx,
                "remaining_payload_bytes": len(data) - idx
            }
            
            return results
        except Exception as e:
            # Return error with context
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"BDA parse error: {str(e)}",
                "raw_data": data.hex(),
                "data_length": len(data)
            }
    
    @staticmethod
    def parse_message(data: bytes) -> Dict[str, Any]:
        """Parse a Suntech message based on header byte"""
        if len(data) == 0:
            return {"error": "Empty message"}
        
        header_byte = data[0]
        
        if header_byte == 0x81:
            # STT (Status Report) - No ACK required
            return SuntechParser.parse_stt_report(data)
        elif header_byte == 0x82:
            # STT variant (Status Report) - Possibly with ACK or different format
            # Try parsing as STT first, if it fails, return as unknown
            try:
                return SuntechParser.parse_stt_report(data)
            except Exception as e:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "report_type": "STT Variant (Header 0x82)",
                    "error": f"Parse error: {str(e)}",
                    "raw_data": data.hex(),
                    "data_length": len(data)
                }
        elif header_byte == 0xAA:
            # BDA/SNB (BLE Sensor Data Report) - No ACK required
            return SuntechParser.parse_bda_report(data)
        elif header_byte == 0xBA:
            # BDA/SNB (BLE Sensor Data Report) - ACK required
            return SuntechParser.parse_bda_report(data)
        else:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"Unknown Header: 0x{header_byte:02X}",
                "raw_data": data.hex(),
                "data_length": len(data)
            }

