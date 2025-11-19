"""Test script to analyze BLE message structure"""
from suntech_parser import SuntechParser
import struct

# Test messages
msg1_hex = 'aa00851990000910007fffc701010c0102020003190b1315340f02edf43c874f5a2a1a1a1f0201060303e1ff1216e1ffa108649519293f23ac566563696d610201060303e1ff1216e1ffa10864052b5e3f23ac566563696d610201061bff3906ca1a018e3c2b5ec8052b5eca951929eda9aa75c22c5219dcac233f291995ac233f5e2b05c3000040089dcbbfca'
msg2_hex = 'aa00e51990000910007fffc701010c0102010006190b1315340f02edf43c874f5a2a1a1a1a1a191a0201060303e1ff1216e1ffa10864a9aa753f23ac566563696d610201060303e1ff1216e1ffa108643c2b5e3f23ac566563696d610201060303e1ff1216e1ffa10864efa7753f23ac566563696d610201060303e1ff1216e1ffa10864acc5f23f23ac566563696d610201060303e1ff1116e1ffa10864739d410000c34d544230370201060303e1ff1216e1ffa1086421d8060000c3566563696d61ac233f75aaa9ac233f5e2b3cac233f75a7efac233ff2c5acc30000419d73c3000006d821b6c1bcbbbbb8'

msg1 = bytes.fromhex(msg1_hex)
msg2 = bytes.fromhex(msg2_hex)

print("="*80)
print("MESSAGE 1 ANALYSIS")
print("="*80)
print(f"Total length: {len(msg1)} bytes")
print(f"Header: 0x{msg1[0]:02X}")
print(f"Packet length: {struct.unpack('>H', msg1[1:3])[0]}")

# Parse header
idx = 0
hdr = msg1[idx]; idx += 1
pkt_len = struct.unpack('>H', msg1[idx:idx+2])[0]; idx += 2
dev_id = int("".join(f'{b:02X}' for b in msg1[idx:idx+5])); idx += 5
report_map = struct.unpack('>I', b'\x00' + msg1[idx:idx+3])[0]; idx += 3
model = msg1[idx]; idx += 1
sw_ver = msg1[idx:idx+3]; idx += 3
ble_scan_status = msg1[idx]; idx += 1
total_no = msg1[idx]; idx += 1
curr_no = msg1[idx]; idx += 1
ble_sen_cnt = struct.unpack('>H', msg1[idx:idx+2])[0]; idx += 2

print(f"Device ID: {dev_id}")
print(f"BLE Sensor Count: {ble_sen_cnt}")
print(f"Index after header: {idx}")

# Parse date/time and location
scan_date = msg1[idx:idx+3]; idx += 3
scan_time = msg1[idx:idx+3]; idx += 3
scan_lat = struct.unpack('>i', msg1[idx:idx+4])[0] / 1_000_000.0; idx += 4
scan_lon = struct.unpack('>i', msg1[idx:idx+4])[0] / 1_000_000.0; idx += 4

print(f"Index after GPS: {idx}")
print(f"Remaining bytes: {len(msg1) - idx}")

# Look for MAC addresses in the data
hex_str = msg1.hex().upper()
ac_pos = hex_str.find('AC233F')
c3_pos = hex_str.find('C30000')

print(f"\nMAC Address Positions:")
print(f"AC233F found at hex position: {ac_pos} (byte: {ac_pos//2})")
print(f"C30000 found at hex position: {c3_pos} (byte: {c3_pos//2})")

# Check bytes around MAC positions
if ac_pos >= 0:
    byte_pos = ac_pos // 2
    print(f"\nBytes around AC233F (byte {byte_pos}):")
    start = max(0, byte_pos - 10)
    end = min(len(msg1), byte_pos + 16)
    for i in range(start, end):
        marker = " <-- AC233F starts" if i == byte_pos else ""
        print(f"  [{i:3d}] 0x{msg1[i]:02X} ({msg1[i]:3d}){marker}")
    
    # Check if it's little endian
    mac_bytes = msg1[byte_pos:byte_pos+6]
    mac_be = mac_bytes.hex().upper()
    mac_le = bytes(reversed(mac_bytes)).hex().upper()
    print(f"  Big endian:    {mac_be}")
    print(f"  Little endian: {mac_le}")
    print(f"  First 3 bytes BE: {mac_be[:6]}")
    print(f"  First 3 bytes LE: {mac_le[:6]}")

if c3_pos >= 0:
    byte_pos = c3_pos // 2
    print(f"\nBytes around C30000 (byte {byte_pos}):")
    start = max(0, byte_pos - 10)
    end = min(len(msg1), byte_pos + 16)
    for i in range(start, end):
        marker = " <-- C30000 starts" if i == byte_pos else ""
        print(f"  [{i:3d}] 0x{msg1[i]:02X} ({msg1[i]:3d}){marker}")
    
    # Check if it's little endian
    mac_bytes = msg1[byte_pos:byte_pos+6]
    mac_be = mac_bytes.hex().upper()
    mac_le = bytes(reversed(mac_bytes)).hex().upper()
    print(f"  Big endian:    {mac_be}")
    print(f"  Little endian: {mac_le}")
    print(f"  First 3 bytes BE: {mac_be[:6]}")
    print(f"  First 3 bytes LE: {mac_le[:6]}")

# Try to parse sensor data
print(f"\nAttempting to parse sensor data starting at index {idx}:")
remaining = msg1[idx:]
print(f"Remaining data length: {len(remaining)} bytes")
print(f"First 50 bytes: {remaining[:50].hex()}")

# Try to find data size fields
print(f"\nLooking for data size patterns (2-byte values):")
for i in range(0, min(100, len(remaining)), 2):
    if i + 2 <= len(remaining):
        size = struct.unpack('>H', remaining[i:i+2])[0]
        if 10 <= size <= 200:  # Reasonable data size
            print(f"  Offset {i}: potential size = {size} bytes")



