import glib

from pyudev import Context, Monitor

try:
    from pyudev.glib import MonitorObserver

    def device_event(observer, device):
        print("event {0} on device {1}".format(device.action, device))


except:
    from pyudev.glib import GUDevMonitorObserver as MonitorObserver

    def device_event(observer, action, device):
        print("event {0} on device {1}".format(action, device))


context = Context()
monitor = Monitor.from_netlink(context)

monitor.filter_by(subsystem="usb")
observer = MonitorObserver(monitor)

observer.connect("device-event", device_event)
monitor.start()

glib.MainLoop().run()
