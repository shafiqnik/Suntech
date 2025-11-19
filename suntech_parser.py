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
        """Converts BCD bytes to decimal integer."""
        return int("".join(f'{b:02X}' for b in bcd_bytes))
    
    @staticmethod
    def parse_suntech_date(date_bytes: bytes) -> str:
        """Parses YY MM DD BCD to YYYYMMDD string."""
        bcd_str = "".join(f'{b:02X}' for b in date_bytes)
        year = 2000 + int(bcd_str[:2])
        return f"{year}{bcd_str[2:4]}{bcd_str[4:]}"
    
    @staticmethod
    def parse_suntech_time(time_bytes: bytes) -> str:
        """Parses HH MM SS BCD to HH:MM:SS string."""
        bcd_str = "".join(f'{b:02X}' for b in time_bytes)
        return f"{bcd_str[:2]}:{bcd_str[2:4]}:{bcd_str[4:]}"
    
    @staticmethod
    def parse_gps_coord(coord_bytes: bytes) -> float:
        """Converts 4-byte signed integer (Big Endian) to decimal coordinate (value / 1,000,000)."""
        value = struct.unpack('>i', coord_bytes)[0]
        return value / 1_000_000.0
    
    @staticmethod
    def parse_stt_report(data: bytes) -> Dict[str, Any]:
        """Parse STT (Status Report) message with header 0x81"""
        results = {}
        
        # 1. Header and Basic ID (1 + 2 + 5 + 3 + 1 + 3 + 1 = 16 bytes)
        hdr = struct.unpack('>B', data[0:1])[0]
        pkt_len = struct.unpack('>H', data[1:3])[0]
        dev_id = SuntechParser.bcd_to_dec(data[3:8])
        report_map = struct.unpack('>I', b'\x00' + data[8:11])[0]
        model = struct.unpack('>B', data[11:12])[0]
        # SW_VER structure: 3 bytes BCD
        sw_ver_str = "".join(f'{b:02X}' for b in data[12:15])
        
        # 2. Time/Date & Cellular (15 to 33 bytes)
        msg_type = struct.unpack('>B', data[15:16])[0]
        date = SuntechParser.parse_suntech_date(data[16:19])
        time = SuntechParser.parse_suntech_time(data[19:22])
        cell_id = struct.unpack('>I', data[22:26])[0]
        mcc = SuntechParser.bcd_to_dec(data[26:28])
        mnc = SuntechParser.bcd_to_dec(data[28:30])
        lac = struct.unpack('>H', data[30:32])[0]
        rx_lvl = struct.unpack('>B', data[32:33])[0]
        
        # 3. GPS Data (33 to 45 bytes)
        lat = SuntechParser.parse_gps_coord(data[33:37])
        lon = SuntechParser.parse_gps_coord(data[37:41])
        spd = struct.unpack('>H', data[41:43])[0] / 100.0  # /100 for km/h
        crs = struct.unpack('>H', data[43:45])[0] / 100.0  # /100 for degrees
        satt = struct.unpack('>B', data[45:46])[0]
        fix = struct.unpack('>B', data[46:47])[0]
        
        # 4. Status (47 to 52 bytes)
        in_state = struct.unpack('>B', data[47:48])[0]
        out_state = struct.unpack('>B', data[48:49])[0]
        mode = struct.unpack('>B', data[49:50])[0]
        rpt_type = struct.unpack('>B', data[50:51])[0]
        msg_num = struct.unpack('>H', data[51:53])[0]
        
        # 5. Final fields and mapping start (53 onwards)
        reserved1 = struct.unpack('>B', data[53:54])[0]
        assign_map = struct.unpack('>I', data[54:58])[0]
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        results = {
            "timestamp": timestamp,
            "report_type": "STT (Status Report)",
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
            "raw_trailing_data_length": len(data) - 58,
        }
        return results
    
    @staticmethod
    def parse_bda_report(data: bytes) -> Dict[str, Any]:
        """Parse BDA/SNB (BLE Sensor Data Report) message with header 0xAA"""
        idx = 0
        
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
        ble_scan_status = struct.unpack('>B', data[idx:idx+1])[0]
        idx += 1
        total_no = struct.unpack('>B', data[idx:idx+1])[0]
        idx += 1
        curr_no = struct.unpack('>B', data[idx:idx+1])[0]
        idx += 1
        ble_sen_cnt = struct.unpack('>H', data[idx:idx+2])[0]
        idx += 2
        
        # Scan timestamp and location
        scan_date = SuntechParser.parse_suntech_date(data[idx:idx+3])
        idx += 3
        scan_time = SuntechParser.parse_suntech_time(data[idx:idx+3])
        idx += 3
        scan_lat = SuntechParser.parse_gps_coord(data[idx:idx+4])
        idx += 4
        scan_lon = SuntechParser.parse_gps_coord(data[idx:idx+4])
        idx += 4
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        results = {
            "timestamp": timestamp,
            "report_type": "BDA/SNB (BLE Sensor Data Report)",
            "header": f"0x{hdr:02X} (No ACK required)",
            "device_id_esn": dev_id,
            "packet_length": pkt_len,
            "model_id": model,
            "software_version": f"{sw_ver_str[0]}.{sw_ver_str[1]}.{sw_ver_str[2:]}",
            "ble_scan_status": "Scan Performed (1)" if ble_scan_status == 1 else "No Scan (0)",
            "total_reports_expected": total_no,
            "current_report_number": curr_no,
            "scanned_sensor_count": ble_sen_cnt,
            "timestamp_gps": f"{scan_date} {scan_time}",
            "location_scan_start": {
                "latitude": f"{scan_lat:.6f}",
                "longitude": f"{scan_lon:.6f}",
            },
            "raw_data_start_index": idx,
            "remaining_payload_bytes": len(data) - idx
        }
        
        return results
    
    @staticmethod
    def parse_message(data: bytes) -> Dict[str, Any]:
        """Parse a Suntech message based on header byte"""
        if len(data) == 0:
            return {"error": "Empty message"}
        
        header_byte = data[0]
        
        if header_byte == 0x81:
            return SuntechParser.parse_stt_report(data)
        elif header_byte == 0xAA:
            return SuntechParser.parse_bda_report(data)
        else:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"Unknown Header: 0x{header_byte:02X}",
                "raw_data": data.hex()
            }

