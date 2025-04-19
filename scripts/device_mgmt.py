import os
import yaml
from netmiko import ConnectHandler


def load_devices():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # gets path to scripts/
    yaml_path = os.path.join(base_dir, "..", "inventory", "device.yaml")

    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)["devices"]


def manage_device(device, commands):
    netmiko_dev = {
        'device_type': device['device_type'],
        'host': device['hostname'],
        'username': device['username'],
        'password': device['password'],
        'secret': device['secret']
    }
    try:
        connection = ConnectHandler(**netmiko_dev)
        connection.enable()
        print(f"Connected to {netmiko_dev['host']}")
        output = connection.send_command(commands)
        print(output, "\n\n")
        connection.disconnect()
    except Exception as e:
        print(f"Failed to connect: {e}")


def submenu():
    print("--------Device Management--------")
    print("1. View Interface status")
    print("2. View IP routes")
    print("3. View IP Addresses")
    print("4. View IP Protocols")

    return input("\nSelect what you want to do")


def int_status(device):
    commands = "show interface"
    manage_device(device, commands)


def ip_routes(device):
    commands = "show ip route"
    manage_device(device, commands)


def ip_addresses(device):
    commands = "show ip int brief"
    manage_device(device, commands)


def ip_protocols(device):
    commands = "show ip protocols"
    manage_device(device, commands)


def main():
    devices = load_devices()
    print("Available devices:")
    for device in devices:
        print(f"- {device['name']}")

    target = input("Select a router; R1 or R2: ").strip()
    device = next((d for d in devices if d['name'] == target), None)
    if not device:
        print("Device not found.")
        return

    while True:

        choice = submenu()

        if choice == '1':
            int_status(device)

        elif choice == '2':
            ip_routes(device)

        elif choice == '3':
            ip_addresses(device)

        elif choice == '4':
            ip_protocols(device)

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
