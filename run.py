import minimalmodbus
import serial
import serial as pyserial
import time
import keyboard

 
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
PV1_LOG_FILE = f'{timestamp}_pv1_log.txt'  # Log file path for PV1
PV2_LOG_FILE = f'{timestamp}_pv2_log.txt'  # Log file path for PV2
 
logging_active = False
 
def log_pv1(pv1):
    """Log PV1 data to a file with a timestamp."""
    with open(PV1_LOG_FILE, 'a') as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - PV1: {pv1:.2f} \u00b0C\n")
 
def log_pv2(pv2):
    """Log PV2 data to a file with a timestamp."""
    with open(PV2_LOG_FILE, 'a') as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - PV2: {pv2:.2f} \u00b0C\n")
 
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
 
    while True:
        try:
            if logging_active:
                pv1, pv2 = read_temperature()
                if pv1 is not None and pv2 is not None:
                    print(f"PV1: {pv1:.2f} \u00b0C, PV2: {pv2:.2f} \u00b0C")
                    log_pv1(pv1)
                    log_pv2(pv2)
                else:
                    print("Failed to read temperature.")
                
        except KeyboardInterrupt:
            break
        time.sleep(1)  # Read every second
 
if __name__ == "__main__":
    main()