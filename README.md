# EID Tag Scanner
Scanner for reading industry standard animal EID tags

Hardware/software for reading ISO 11784/11785 compliant RFID tags using 134.2kHz NFC. Hardware is based on the TMS3705 reader IC from Texas Instruments.

## Hardware
The reader IC (TMS3705) interfaces with an RP2040 to charge, read, and decode tag ID's. The TMS3705 requires some unique and precise timing, so the RP2040 uses a PIO state machine to interface with it. Low level filtering ensures a valid ID is found (including checking for the proper start byte `0xAF` and a stability filter that only returns a valid ID after the same ID is read X number of times). The processing/interfacing pretty well maxes out the RP2040 (using both cores and a state machine), so the resulting data is spit out over I2C to an ESP32 to handle the HID and display. A small OLED offers an interface, and Bluetooth allows the device to act as a keyboard, automatically typing the ID into another device.

## Software
The RP2040 runs MicroPython to allow fast development and in-field modifications without the need for a large SDK or compilation. The ESP32 manages the GUI on the OLED display and implements a Bluetooth keyboard.
