from netmiko import ConnectHandler

from scripts.device_mgmt import load_devices
from scripts.device_mgmt import ip_routes


def submenu():
    print("--------Device Configuration--------")
    print("1. Change IP address on an interface")
    print("2. Change Hostname")
    print("3. Add Default Route")
    print("4. Change Static Route")
    print("5. Pick another Device")
    print("6. Exit")
    return input("Select what you want to do: ")


def connectToDevice(device):
    try:
        conn = ConnectHandler(
            device_type=device['device_type'],
            host=device['hostname'],
            username=device['username'],
            password=device['password'],
            secret=device['secret']
        )
        conn.enable()
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


def changeIpAddress(device):
    print("Available Interfaces:\n"
          "e1/0\n"
          "e1/1\n"
          "e1/2\n"
          "e1/3\n\n")
    intf = input("Enter interface:").strip()
    ip = input("Enter new IP address:").strip()
    mask = input("Enter subnet mask:").strip()

    commands = [
        f"interface {intf}",
        f"ip address {ip} {mask}",
        "no shutdown",
        "exit"
    ]
    applyConfig(device, commands)


def changeHostname(device):
    new_hostname = input("Enter new hostname: ").strip()
    commands = [f"hostname {new_hostname}"]
    applyConfig(device, commands)


def addDefaultRoute(device):
    next_hop = input("Enter next-hop IP for default route:").strip()
    command = f"ip route 0.0.0.0 0.0.0.0 {next_hop}"
    applyConfig(device, [command])


def changeStaticRoute(device):
    print("1. Delete route\n2. Add Route")
    choice = input("What do you want to do?")

    if choice == '1':
        ip_routes(device)
        destination = input("Enter destination network:").strip()
        mask = input("Enter subnet mask:").strip()
        next_hop = input("Enter next-hop IP address:").strip()
        command = f"no ip route {destination} {mask} {next_hop}"
        applyConfig(device, [command])

    if choice == '2':
        destination = input("Enter destination network:").strip()
        mask = input("Enter subnet mask:").strip()
        next_hop = input("Enter next-hop IP address:").strip()
        command = f"ip route {destination} {mask} {next_hop}"
        applyConfig(device, [command])


def applyConfig(device, commands):
    conn = connectToDevice(device)
    if not conn:
        return

    try:
        print(f"\nApplying configuration to {device['hostname']}...\n")
        output = conn.send_config_set(commands)
        print(output)
        conn.disconnect()
    except Exception as e:
        print(f"Failed to apply config: {e}")


def main():
    devices = load_devices()

    while True:
        print("Available devices:")
        for device in devices:
            print(f"- {device['name']}")

        target = input("Select a device:").strip()
        device = next((d for d in devices if d['name'] == target), None)
        if not device:
            print("Device not found.")
            continue

        while True:
            choice = submenu()

            if choice == '1':
                changeIpAddress(device)
            elif choice == '2':
                changeHostname(device)
            elif choice == '3':
                addDefaultRoute(device)
            elif choice == '4':
                changeStaticRoute(device)
            elif choice == '5':
                break
            elif choice == '6':
                return
            else:
                print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
