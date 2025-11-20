"""
Test script to verify BLE beacon parsing with the new message
"""
import sys
from suntech_parser import SuntechParser

# The new BLE message provided by the user
test_message_hex = 'aa00851990000910007fffc701010c0102020003190b1317390f02edf43c874f5a2a1a1a1f0201060303e1ff1216e1ffa108643c2b5e3f23ac566563696d610201060303e1ff1216e1ffa10864efa7753f23ac566563696d610201061bff3906ca1a01e2951929ec052b5eca3c2b5ecaefa775c84f4f8167ac233f5e2b3cac233f75a7efc3000040089dbbb5c4'

def test_ble_parsing():
    """Test parsing of the BLE message"""
    print("=" * 80)
    print("Testing BLE Message Parsing - New Message")
    print("=" * 80)
    print(f"\nInput message (hex): {test_message_hex[:100]}...")
    print(f"Total length: {len(test_message_hex)} hex chars = {len(test_message_hex) // 2} bytes\n")
    
    # Convert hex string to bytes
    try:
        message_bytes = bytes.fromhex(test_message_hex)
        print(f"✓ Successfully converted to bytes: {len(message_bytes)} bytes\n")
    except Exception as e:
        print(f"✗ Error converting hex to bytes: {e}")
        return
    
    # Parse the message
    parser = SuntechParser()
    try:
        result = parser.parse_message(message_bytes)
        print("=" * 80)
        print("PARSING RESULT")
        print("=" * 80)
        
        if 'error' in result:
            print(f"✗ Parse Error: {result['error']}")
            return
        
        print(f"Report Type: {result.get('report_type', 'N/A')}")
        print(f"Device ID: {result.get('device_id_esn', 'N/A')}")
        print(f"BLE Scan Status: {result.get('ble_scan_status', 'N/A')}")
        print(f"Scanned Sensor Count: {result.get('scanned_sensor_count', 'N/A')}")
        print(f"Sensors Parsed: {result.get('sensors_parsed', 0)}")
        print(f"Has Target MAC: {result.get('has_target_mac', False)}")
        
        # Check for beacons
        sensors = result.get('sensors', [])
        print(f"\n{'=' * 80}")
        print(f"BLE BEACONS/TAGS DETECTED: {len(sensors)}")
        print(f"{'=' * 80}\n")
        
        if len(sensors) == 0:
            print("⚠ No beacons detected!")
        else:
            target_beacons = []
            other_beacons = []
            
            for idx, sensor in enumerate(sensors, 1):
                mac = sensor.get('mac_address', sensor.get('mac_address_raw', 'N/A'))
                is_target = sensor.get('is_target_mac', False)
                rssi = sensor.get('rssi', 'N/A')
                rssi_hex = sensor.get('rssi_hex', 'N/A')
                byte_pos = sensor.get('byte_position', 'N/A')
                
                beacon_info = {
                    'index': idx,
                    'mac': mac,
                    'is_target': is_target,
                    'rssi': rssi,
                    'rssi_hex': rssi_hex,
                    'byte_pos': byte_pos
                }
                
                if is_target:
                    target_beacons.append(beacon_info)
                else:
                    other_beacons.append(beacon_info)
            
            # Display target beacons
            if target_beacons:
                print(f"🎯 TARGET BEACONS (AC233F / C3000): {len(target_beacons)}")
                print("-" * 80)
                for beacon in target_beacons:
                    # Use raw MAC (hex without colons) for type detection
                    mac_raw = beacon['mac'].upper().replace(':', '')
                    if mac_raw.startswith('AC233F'):
                        beacon_type = 'AC233F Tag'
                    elif mac_raw.startswith('C30000') or mac_raw.startswith('C3000'):
                        beacon_type = 'C3000 Tag'
                    else:
                        beacon_type = 'Target Tag'
                    print(f"  {beacon['index']}. {beacon['mac']} ({beacon_type})")
                    print(f"     RSSI: {beacon['rssi']} dBm ({beacon['rssi_hex']})")
                    print(f"     Position: Byte {beacon['byte_pos']}")
                    print()
            else:
                print("⚠ No target beacons (AC233F/C3000) detected!")
                print()
        
        # Check raw data for manual verification
        print(f"\n{'=' * 80}")
        print("RAW DATA VERIFICATION")
        print(f"{'=' * 80}")
        raw_data = result.get('raw_data', '')
        if raw_data:
            raw_upper = raw_data.upper()
            print(f"\nSearching for beacon patterns in raw data...")
            
            patterns = ['AC233F', 'C30000', 'C3000']
            for pattern in patterns:
                count = raw_upper.count(pattern)
                if count > 0:
                    print(f"  ✓ Found '{pattern}' {count} time(s)")
                    # Show all occurrences
                    pos = 0
                    occurrences = []
                    while True:
                        pos = raw_upper.find(pattern, pos)
                        if pos < 0:
                            break
                        if pos % 2 == 0:  # Only at byte boundaries
                            occurrences.append(pos)
                        pos += 2
                    for occ in occurrences:
                        start = max(0, occ - 20)
                        end = min(len(raw_upper), occ + 30)
                        context = raw_upper[start:end]
                        print(f"     At hex position {occ} (byte {occ // 2}): ...{context}...")
                else:
                    print(f"  ✗ Pattern '{pattern}' not found")
        
        print(f"\n{'=' * 80}")
        print("TEST COMPLETE")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"✗ Error parsing message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ble_parsing()

