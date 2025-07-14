# Written by Jesse 07/4/25

import rp2, _thread
from machine import Pin
from time import sleep_us, sleep_ms

# Set up pins
TXCT = Pin(6, Pin.OUT)
SCIO = Pin(4, Pin.IN)

# Flag for controlling second core
reader_run = False

# Create the reading state machine
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def read_byte():
    wrap_target()       # Infinite loop
    wait(1, pin, 0)     # Wait for a rising edge
    nop()   [31]
    nop()   [31]
    nop()   [31]        # Move sample point to center of first bit
    set(x, 7)           # Set countdown (8 bits)
    label("loop")
    in_(pins, 1)        # Sample 1 bit into the ISR
    nop()   [29]
    nop()   [31]        # Wait one period (64 cycles - 1 in_ - 1 jmp = 62 nop)
    jmp(x_dec, "loop")  # Decrement counter and jump to loop
    push()              # Push the ISR to the RX_FIFO buffer after every byte
    wrap()              # Loop

sm = rp2.StateMachine(0, read_byte, freq=1000000, in_base=SCIO)
sm.active(1)    # Start the machine (I said hey, you, feed the machine)


# Basic reader to retrieve a byte from the FIFO queue 
def read():
    if sm.rx_fifo():    # If data is available
        byte = sm.get() & 0xFF  # Read and mask 8 bits
        return byte
    return None


# Runs on Core 0
def charge():
    global reader_run
    # TXCT initialization
    TXCT.on()
    sleep_us(10000) # delay to let everything stabalize

    while True:
        # Charge cycle
        TXCT.off()
        sleep_us(4500)  # 4.5ms (found through experimentation)
        TXCT.on()

        b = read()  # Check diagnostic byte
        if b is None:
            print("No diag response")
            continue
            

        elif b != 0xF5: # Diag byte check
            print(f"Bad diag byte: {b}")
            # NOTE: The true diagnostic byte is 0xAF, but the bits are sent MSB, so reversing it gives 0xF5
            

        reader_run = True   # Run the reader
        sleep_ms(30)     # Wait maximum read time: 20ms (from the datasheet) + 10ms for good luck
        reader_run = False  # Disable the reader

        # Dump the buffer for next read
        while read() is not None:
            pass


# Runs on Core 1
def reader():
    data_bytes = []
    previous_buffer = []
    previous_id = 0

    
    while True:
        if reader_run:  # Allow blocking in this function
            value = read()
            if value is not None:
                # Reverse the byte (MSB -> LSB)
                reversed_byte = 0
                for i in range(8):
                    reversed_byte <<= 1
                    reversed_byte |= (value >> i) & 1
                
                # Invert all bits (mask to 1 byte)
                value = ~reversed_byte & 0xFF

                # Add to the raw data collected
                data_bytes.append(value)

        # Only run this section after the reader is done
        # and there is new data in the data_byte buffer
        elif len(data_bytes) != 0:
            # Make sure we have a valid data sequence
            if data_bytes[0] == 0x7e:
                # Interpret the ID
                tag_id = 0

                # Assemble the ID from bytes 2 - 6
                for c in reversed(data_bytes[1:5]):
                    tag_id = (tag_id << 8) | c
                
                # Run a stability filter (need X matching samples to pass the filter)
                previous_buffer.insert(0, tag_id)
                if len(previous_buffer) > 4:
                    previous_buffer.pop()
                if len(previous_buffer) == 4 and all(s == previous_buffer[0] for s in previous_buffer):
                    # Only print the most recent scan once
                    if previous_id != tag_id:
                        print(tag_id)
                    previous_id = tag_id
            
            data_bytes = [] # Dump the data buffer
        
        sleep_us(1)


# Start the second core on the reader function
_thread.start_new_thread(reader, ())


charge()