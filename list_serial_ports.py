import sys
import serial


def list_serial_ports():
    """Lists serial port names
    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of the serial ports available on the system
    """
    portDesc = ""
    if sys.platform.startswith("win"):
        portDesc = "USB Serial Port"
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        portDesc = "TTL232R-3V3"
    elif sys.platform.startswith("darwin"):
        portDesc = "TTL232R-3V3"
    else:
        raise EnvironmentError("Unsupported platform")

    ports = list(serial.tools.list_ports.comports())
    result = []
    for p in ports:
        if portDesc in p.description:
            try:
                s = serial.Serial(p.device)
                s.close()
                result.append(p.device)
            except (OSError, serial.SerialException) as inst:
                print(inst)
                pass

    return result
