import sys
import serial


def list_serial_ports():
    """Lists serial port names
    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of the serial ports available on the system
    """
    port_descriptors = ["USB Serial Port", "TTL232R-3V3", "USB to UART", "usbserial", "RS232", "USB-UART"]
    ports = list(serial.tools.list_ports.comports())
    result = []
    # print("Found {} ports:".format(len(ports)))
    for p in ports:
        is_correct_type_of_port = False
        for desc in port_descriptors:
            # print("\t{}".format(p.description))
            if desc in p.description:
                is_correct_type_of_port = True
        if is_correct_type_of_port:
            try:
                # s = serial.Serial(p.device)
                # s.close()
                result.append(p.device)
            except (OSError, serial.SerialException) as inst:
                print(inst)
                pass

    return result
