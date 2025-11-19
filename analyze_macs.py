"""Analyze MAC address structure in BLE messages"""
msg1_hex = 'aa00851990000910007fffc701010c0102020003190b1315340f02edf43c874f5a2a1a1a1f0201060303e1ff1216e1ffa108649519293f23ac566563696d610201060303e1ff1216e1ffa10864052b5e3f23ac566563696d610201061bff3906ca1a018e3c2b5ec8052b5eca951929eda9aa75c22c5219dcac233f291995ac233f5e2b05c3000040089dcbbfca'
msg1 = bytes.fromhex(msg1_hex)
hex_str = msg1.hex()

# MAC addresses provided by user
macs_str = 'c3000006d821ac233f5e2b05ac233f75aaa9ac233ff2c5a'
print("MAC addresses provided:", macs_str)
print("Length:", len(macs_str))

# Split into 6-byte MAC addresses (12 hex chars each)
mac_addresses = []
for i in range(0, len(macs_str), 12):
    if i + 12 <= len(macs_str):
        mac_hex = macs_str[i:i+12]
        mac_bytes = bytes.fromhex(mac_hex)
        # Format as MAC address
        mac_formatted = ':'.join([mac_hex[j:j+2] for j in range(0, 12, 2)])
        # Check little endian
        mac_bytes_le = bytes(reversed(mac_bytes))
        mac_hex_le = mac_bytes_le.hex().upper()
        mac_formatted_le = ':'.join([mac_hex_le[j:j+2] for j in range(0, 12, 2)])
        
        print(f"\nMAC {len(mac_addresses) + 1}:")
        print(f"  Hex: {mac_hex}")
        print(f"  Big Endian:    {mac_formatted}")
        print(f"  Little Endian: {mac_formatted_le}")
        print(f"  First 3 bytes BE: {mac_hex[:6].upper()}")
        print(f"  First 3 bytes LE: {mac_hex_le[:6]}")
        
        mac_addresses.append({
            'hex': mac_hex,
            'be': mac_formatted,
            'le': mac_formatted_le,
            'bytes': mac_bytes
        })

# Search for these MACs in the message
print("\n" + "="*80)
print("SEARCHING FOR MACs IN MESSAGE")
print("="*80)
for i, mac_info in enumerate(mac_addresses):
    # Search for big endian
    pos_be = hex_str.find(mac_info['hex'].lower())
    # Search for little endian
    pos_le = hex_str.find(mac_info['hex'][::-1].lower())
    # Search for reversed bytes (little endian)
    mac_bytes_le = bytes(reversed(mac_info['bytes']))
    pos_le_bytes = hex_str.find(mac_bytes_le.hex().lower())
    
    print(f"\nMAC {i+1} ({mac_info['be']}):")
    print(f"  Big endian position: {pos_be} (byte {pos_be//2 if pos_be >= 0 else -1})")
    print(f"  Little endian (reversed hex) position: {pos_le} (byte {pos_le//2 if pos_le >= 0 else -1})")
    print(f"  Little endian (reversed bytes) position: {pos_le_bytes} (byte {pos_le_bytes//2 if pos_le_bytes >= 0 else -1})")
    
    if pos_be >= 0:
        byte_pos = pos_be // 2
        print(f"  Context at byte {byte_pos}:")
        start = max(0, byte_pos - 5)
        end = min(len(msg1), byte_pos + 11)
        context = msg1[start:end]
        print(f"    Bytes: {context.hex()}")
        for j, b in enumerate(context):
            marker = " <-- MAC starts" if start + j == byte_pos else ""
            print(f"    [{start+j:3d}] 0x{b:02X}{marker}")



