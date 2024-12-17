import csv
import time
import minimalmodbus
import serial as pyserial

import serial.tools.list_ports

def list_serial_ports():
    """List all available serial ports that match the pattern /dev/tty.*."""
    ports = serial.tools.list_ports.comports()
    print("All available serial ports:")
    for port in ports:
        print(f"Port: {port.device}, Description: {port.description}, HWID: {port.hwid}")

# Configuration
PORT = '/dev/tty.usbserial-A10KVO9S'  # Replace with the correct port for your system
SLAVE_ADDRESS = 1      # Replace with the MODBUS device address
BAUD_RATE = 9600       # Baud rate for communication
PARITY = pyserial.PARITY_NONE  # Parity: PARITY_NONE, PARITY_EVEN, PARITY_ODD
STOP_BITS = 1          # Number of stop bits
BYTE_SIZE = 8          # Data byte size
PV1_REGISTER_ADDRESS = 0  # The MODBUS register for PV1 (replace with your sensor's register address)
PV2_REGISTER_ADDRESS = 1  # The MODBUS register for PV2
NUM_REGISTERS = 1      # Number of registers to read
REGISTER_SCALE = 1    # Scale factor for temperature (e.g., divide by 10 if temperature is reported as 123 for 12.3)

timestamp = time.strftime("%Y-%m-%d_%H.%M.%S")
 # Assuming the rest of your code is already defined above

CSV_FILE = f'{timestamp}_temperature_log.csv'

def initialize_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'PV1 (°C)', 'PV2 (°C)'])

def log_to_csv(pv1, pv2):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([timestamp, pv1, pv2])
 
def read_temperature():
    """Read temperature data from the sensor."""
    try:
        # Initialize the instrument
        instrument = minimalmodbus.Instrument(PORT, SLAVE_ADDRESS)
        instrument.serial.baudrate = BAUD_RATE
        instrument.serial.parity = PARITY
        instrument.serial.stopbits = STOP_BITS
        instrument.serial.bytesize = BYTE_SIZE
        instrument.serial.timeout = 1  # Seconds

        # Read registers for PV1 and PV2
        raw_data_pv1 = instrument.read_register(PV1_REGISTER_ADDRESS, NUM_REGISTERS, functioncode=3)
        raw_data_pv2 = instrument.read_register(PV2_REGISTER_ADDRESS, NUM_REGISTERS, functioncode=3)
        pv1 = raw_data_pv1 / REGISTER_SCALE  # Apply scale factor
        pv2 = raw_data_pv2 / REGISTER_SCALE  # Apply scale factor

        return pv1, pv2

    except minimalmodbus.NoResponseError as e:
        print(f"No response from the device: {e}")
        return None, None
    except minimalmodbus.InvalidResponseError as e:
        print(f"Invalid response from the device: {e}")
        return None, None
    except pyserial.SerialException as e:
        print(f"Serial communication error: {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None
 
def main():
    global logging_active
    print("Type 'start' to begin logging and press 'Esc' to stop and save the file.")
    logging_active = True

    initialize_csv()

    while True:
        try:
            if logging_active:
                pv1, pv2 = read_temperature()
                if pv1 is not None and pv2 is not None:
                    print(f"PV1: {pv1:.2f} \u00b0C, PV2: {pv2:.2f} \u00b0C")
                    log_to_csv(pv1, pv2)
                else:
                    print("Failed to read temperature.")
                
        except KeyboardInterrupt:
            break
        time.sleep(1)  # Read every second

if __name__ == "__main__":
    list_serial_ports()
    PORT = input("Enter the port name: ")
    main()