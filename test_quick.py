"""Quick test of new message"""
from suntech_parser import SuntechParser

msg = 'aa00851990000910007fffc701010c0102020003190b1317390f02edf43c874f5a2a1a1a1f0201060303e1ff1216e1ffa108643c2b5e3f23ac566563696d610201060303e1ff1216e1ffa10864efa7753f23ac566563696d610201061bff3906ca1a01e2951929ec052b5eca3c2b5ecaefa775c84f4f8167ac233f5e2b3cac233f75a7efc3000040089dbbb5c4'

data = bytes.fromhex(msg)
parser = SuntechParser()
result = parser.parse_message(data)

print(f"Sensors found: {len(result.get('sensors', []))}")
print(f"Has target MAC: {result.get('has_target_mac', False)}")

for i, sensor in enumerate(result.get('sensors', []), 1):
    mac = sensor.get('mac_address', sensor.get('mac_address_raw', 'N/A'))
    is_target = sensor.get('is_target_mac', False)
    print(f"{i}. {mac} - Target: {is_target}")

