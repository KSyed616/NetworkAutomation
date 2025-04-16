import importlib
import sys


def header():
    print("-----------------------------------------------")
    print("NETWORK AUTOMATION SYSTEM")
    print("-----------------------------------------------")


def menu():
    options = {
        "1": {"title": "Device Management", "module": "device_mgmt"},
        "2": {"title": "Configuration Management", "module": "config_mgmt"},
        "3": {"title": "Device Configuration", "module": "device_config"},
        "4": {"title": "SNMP Configuration", "module": "snmp_config"},
        "q": {"title": "Quit", "module": None}
    }

    for key, options in options.items():
        print(f"{key}. {options['title']}")

    return options


def execute_module(name):
    try:
        module = importlib.import_module(f"scripts.{name}")

        if hasattr(module, 'main'):
            module.main()

        input("\nEnter to return to main menu")

    except ImportError:
        print(f"Module {name} not found.")
        input("\nEnter to return to main menu")
    except Exception as e:
        print(f"Error executing module: {str(e)}")
        input("\nEnter to return to main menu")


def main():
    while True:
        header()
        options = menu()

        choice = input("\nWhat do you want to do: ").lower()

        if choice == 'q':
            print("Terminating session")
            sys.exit(0)

        if choice in options:
            module_name = options[choice]["module"]
            execute_module(module_name)
        else:
            print("Invalid option, try again\n")
            input("Enter to return to main menu")


if __name__ == "__main__":
    main()
