import csv
import time
import minimalmodbus
import serial as pyserial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading

# Configuration
SLAVE_ADDRESS = 1      # Replace with the MODBUS device address
BAUD_RATE = 9600       # Baud rate for communication
PARITY = pyserial.PARITY_NONE  # Parity: PARITY_NONE, PARITY_EVEN, PARITY_ODD
STOP_BITS = 1          # Number of stop bits
BYTE_SIZE = 8          # Data byte size
PV1_REGISTER_ADDRESS = 0  # The MODBUS register for PV1 (replace with your sensor's register address)
PV2_REGISTER_ADDRESS = 1  # The MODBUS register for PV2
PV3_REGISTER_ADDRESS = 2  # The MODBUS register for PV3
PV4_REGISTER_ADDRESS = 3  # The MODBUS register for PV4
NUM_REGISTERS = 1      # Number of registers to read
REGISTER_SCALE = 1    # Scale factor for temperature (e.g., divide by 10 if temperature is reported as 123 for 12.3)

logging_active = False
PORT = None
CSV_FILE = None

def list_serial_ports():
    """List all available serial ports that match the pattern /dev/tty.*."""
    import sys
    ports = []
    if sys.platform.startswith('win'):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    else:
        import os
        ports = os.popen('ls /dev/tty.*').read().strip().split("\n")
        return ports

def initialize_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'PV1 (°C)', 'PV2 (°C)', 'PV3 (°C)', 'PV4 (°C)'])

def log_to_csv(pv1, pv2, pv3, pv4):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([timestamp, pv1, pv2, pv3, pv4])

def read_temperature():
    """Read temperature data from the sensor."""
    try:
        # Initialize the instrument
        instrument = minimalmodbus.Instrument(PORT, SLAVE_ADDRESS)
        instrument.serial.parity = PARITY
        instrument.serial.stopbits = STOP_BITS
        instrument.serial.bytesize = BYTE_SIZE
        instrument.serial.timeout = 1  # Seconds

        # Read registers for PV1, PV2, PV3, and PV4
        raw_data_pv1 = instrument.read_register(PV1_REGISTER_ADDRESS, NUM_REGISTERS, functioncode=3)
        raw_data_pv2 = instrument.read_register(PV2_REGISTER_ADDRESS, NUM_REGISTERS, functioncode=3)
        raw_data_pv3 = instrument.read_register(PV3_REGISTER_ADDRESS, NUM_REGISTERS, functioncode=3)
        raw_data_pv4 = instrument.read_register(PV4_REGISTER_ADDRESS, NUM_REGISTERS, functioncode=3)
        pv1 = raw_data_pv1 / REGISTER_SCALE  # Apply scale factor
        pv2 = raw_data_pv2 / REGISTER_SCALE  # Apply scale factor
        pv3 = raw_data_pv3 / REGISTER_SCALE  # Apply scale factor
        pv4 = raw_data_pv4 / REGISTER_SCALE  # Apply scale factor

        return pv1, pv2, pv3, pv4

    except minimalmodbus.NoResponseError as e:
        print(f"No response from the device: {e}")
        return None, None, None, None
    except minimalmodbus.InvalidResponseError as e:
        print(f"Invalid response from the device: {e}")
        return None, None, None, None
    except pyserial.SerialException as e:
        print(f"Serial communication error: {e}")
        return None, None, None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None, None, None

def start_logging():
    global logging_active
    global PORT
    global CSV_FILE
    PORT = port_combobox.get()
    if not PORT:
        messagebox.showerror("Error", "Please select a serial port.")
        return
    timestamp = time.strftime("%Y-%m-%d_%H.%M.%S")
    CSV_FILE = f'{timestamp}_temperature_log.csv'
    logging_active = True
    csv_label.config(text=f"Logging to file: {CSV_FILE}")
    start_button.config(state=tk.DISABLED)
    port_combobox.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    threading.Thread(target=log_temperature).start()

def stop_logging():
    global logging_active
    logging_active = False
    start_button.config(state=tk.NORMAL)
    port_combobox.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def log_temperature():
    initialize_csv()
    while logging_active:
        pv1, pv2, pv3, pv4 = read_temperature()
        if pv1 is not None and pv2 is not None and pv3 is not None and pv4 is not None:
            print(f"PV1: {pv1:.2f} \u00b0C, PV2: {pv2:.2f} \u00b0C, PV3: {pv3:.2f} \u00b0C, PV4: {pv4:.2f} \u00b0C")
            log_to_csv(pv1, pv2, pv3, pv4)
            pv1_gauge['value'] = pv1
            pv2_gauge['value'] = pv2
            pv3_gauge['value'] = pv3
            pv4_gauge['value'] = pv4
            pv1_label.config(text=f"PV1: {pv1:.2f} \u00b0C")
            pv2_label.config(text=f"PV2: {pv2:.2f} \u00b0C")
            pv3_label.config(text=f"PV3: {pv3:.2f} \u00b0C")
            pv4_label.config(text=f"PV4: {pv4:.2f} \u00b0C")
        else:
            print("Failed to read temperature.")
        time.sleep(1)  # Read every second

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        stop_logging()
        root.destroy()

# Create the main window
root = tk.Tk()
root.title("Temperature Logger")

# Create and place the dropdown for serial ports
ports = list_serial_ports()
port_combobox = ttk.Combobox(root, values=ports)
port_combobox.set("Select Serial Port")
port_combobox.pack(pady=10)

# Create and place the buttons
start_button = tk.Button(root, text="Start Logging", command=start_logging)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Logging", command=stop_logging)
stop_button.pack(pady=10)
stop_button.config(state=tk.DISABLED)

# Create and place the gauges
pv1_label = tk.Label(root, text="PV1: 0.00 \u00b0C")
pv1_label.pack(pady=5)
pv1_gauge = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", maximum=150)
pv1_gauge.pack(pady=5)

pv2_label = tk.Label(root, text="PV2: 0.00 \u00b0C")
pv2_label.pack(pady=5)
pv2_gauge = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", maximum=150)
pv2_gauge.pack(pady=5)

# Create and place the gauges for PV3 and PV4
pv3_label = tk.Label(root, text="PV3: 0.00 \u00b0C")
pv3_label.pack(pady=5)
pv3_gauge = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", maximum=150)
pv3_gauge.pack(pady=5)

pv4_label = tk.Label(root, text="PV4: 0.00 \u00b0C")
pv4_label.pack(pady=5)
pv4_gauge = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", maximum=150)
pv4_gauge.pack(pady=5)

# Create and place the label for CSV file name
csv_label = tk.Label(root, text="")
csv_label.pack(pady=10)

# Handle window close event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter event loop
root.mainloop()