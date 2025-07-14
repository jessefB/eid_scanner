def reflect_bits(data: int, num_bits: int) -> int:
    result = 0
    for i in range(num_bits):
        if data & (1 << i):
            result |= (1 << (num_bits - 1 - i))
    return result

def crc_ccitt_kermit(data: bytes, poly=0x1021, init=0x0000) -> int:
    crc = init
    for byte in data:
        byte = reflect_bits(byte, 8)
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return reflect_bits(crc, 16)


data = 0b0111111001010101010111010011100111000011000000001101001000000000100000001100111111111111011111100000000010000110

mask = 0x00FFFFFFFFFFFFFFFF0000000000
input = (data & mask) >> 40
print(bin(input))


print(hex(crc_ccitt_kermit(input.to_bytes(8, byteorder="big"))))