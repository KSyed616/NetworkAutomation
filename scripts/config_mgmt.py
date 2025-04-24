import os
import yaml
from netmiko import ConnectHandler
import subprocess


def load_devices():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # gets path to scripts/
    yaml_path = os.path.join(base_dir, "..", "inventory", "device.yaml")

    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)["devices"]


def get_config_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # current: scripts/
    config_path = os.path.join(base_dir, "..", "configuration", filename)
    return os.path.abspath(config_path)


def submenu():
    print("--------Configuration Management--------")
    print("1. View Running Configuration")
    print("2. View Saved Configuration")
    print("3. View Backup Configuration")
    print("4. Save Configuration GNS")
    print("5. Save Configuration GitHub")
    print("6. Backup Configuration")
    print("7. Load Saved Configuration")
    print("8. Load Backup Configuration")
    print("9. Change Device")
    print("10. Exit")

    return input("\nSelect what you want to do")


def git_push(filepath, commit_msg="Config Push"):
    try:
        subprocess.run(["git", "add", filepath], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Config pushed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")


def view_running_config(device):
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
        output = connection.send_command("show running-config")
        print(output, "\n\n")
        connection.disconnect()
    except Exception as e:
        print(f"Failed to connect: {e}")


def view_startup_config(device):
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
        output = connection.send_command("show startup-config")
        print(output, "\n\n")
        connection.disconnect()
    except Exception as e:
        print(f"Failed to connect: {e}")


def view_backup_config(device):
    filename = f"configuration/{device['name']}_Backup.cfg"
    try:
        with open(filename, 'r') as file:
            contents = file.read()
            print(f"\nBackup Config: {filename}\n")
            print(contents)
    except FileNotFoundError:
        print(f"Backup file not found: {filename}")
    except Exception as e:
        print(f"Error reading file: {e}")


def save_config_gns(device):
    netmiko_dev = {
        'device_type': device['device_type'],
        'host': device['hostname'],
        'username': device['username'],
        'password': device['password'],
        'secret': device['secret'],
        'session_log': 'netmiko_debug.log'
    }
    try:
        connection = ConnectHandler(**netmiko_dev)
        connection.enable()

        print(f"Connected to {netmiko_dev['host']}")
        output = connection.send_command_timing("write")

        print(output, "\n\n")
        connection.disconnect()
    except Exception as e:
        print(f"Failed to connect: {e}")


def save_config(device):
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
        output = connection.send_command("show running-config")
        filename = f"{device['name']}_Startup.cfg"
        full_path = get_config_path(filename)

        with open(full_path, 'w') as f:
            f.write(output)
        connection.disconnect()

        git_push(full_path, f"Backup config for {device['name']}")

    except Exception as e:
        print(f"Failed to connect: {e}")


def backup_config(device):
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
        output = connection.send_command("show running-config")

        filename = f"{device['name']}_Backup.cfg"
        full_path = get_config_path(filename)

        with open(full_path, 'w') as f:
            f.write(output)
        connection.disconnect()

        git_push(full_path, f"Backup config for {device['name']}")

    except Exception as e:
        print(f"Failed to connect: {e}")


def load_backup_config(device):
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

        filename = f"{device['name']}_Backup.cfg"
        full_path = get_config_path(filename)
        connection.send_config_from_file(full_path)

        connection.disconnect()

    except Exception as e:
        print(f"Failed to connect: {e}")


def load_startup_config(device):
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

        filename = f"{device['name']}_Startup.cfg"
        full_path = get_config_path(filename)
        output = connection.send_config_from_file(full_path)

        connection.disconnect()

    except Exception as e:
        print(f"Failed to connect: {e}")


def main():
    devices = load_devices()
    while True:
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
                view_running_config(device)

            elif choice == '2':
                view_startup_config(device)

            elif choice == '3':
                view_backup_config(device)

            elif choice == '4':
                save_config_gns(device)

            elif choice == '5':
                save_config(device)

            elif choice == '6':
                backup_config(device)

            elif choice == '7':
                load_startup_config(device)

            elif choice == '8':
                load_backup_config(device)

            elif choice == '9':
                break

            elif choice == '10':
                return

            else:
                print("Invalid choice")


if __name__ == "__main__":
    main()
