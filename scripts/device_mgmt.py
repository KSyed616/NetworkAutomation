import os
import yaml
from netmiko import ConnectHandler
from pyasn1.codec.ber import encoder, decoder
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.carrier.asyncio.dispatch import AsyncioDispatcher
from pysnmp.proto import api


def load_devices():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(base_dir, "..", "inventory", "device.yaml")

    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)["devices"]


def snmp_walk(oid_tuple, ip, community="public"):
    results = []
    pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

    headVars = [pMod.ObjectIdentifier(oid_tuple)]

    reqPDU = pMod.GetNextRequestPDU()
    pMod.apiPDU.set_defaults(reqPDU)
    pMod.apiPDU.set_varbinds(reqPDU, [(x, pMod.null) for x in headVars])

    reqMsg = pMod.Message()
    pMod.apiMessage.set_defaults(reqMsg)
    pMod.apiMessage.set_community(reqMsg, community)
    pMod.apiMessage.set_pdu(reqMsg, reqPDU)

    def cbRecvFun(
            transportDispatcher,
            transportDomain,
            transportAddress,
            wholeMsg,
            reqPDU=reqPDU,
            headVars=headVars,
            oid_tuple=oid_tuple
    ):
        while wholeMsg:
            rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
            rspPDU = pMod.apiMessage.get_pdu(rspMsg)

            if pMod.apiPDU.get_request_id(reqPDU) == pMod.apiPDU.get_request_id(rspPDU):
                errorStatus = pMod.apiPDU.get_error_status(rspPDU)
                if errorStatus and errorStatus != 2:
                    print(f"Error:{errorStatus}")
                    raise Exception(errorStatus)

                varBindTable = pMod.apiPDU.get_varbind_table(reqPDU, rspPDU)

                for tableRow in varBindTable:
                    for name, val in tableRow:
                        oid_str = name.prettyPrint()
                        oid_prefix = '.'.join(str(x) for x in oid_tuple)
                        if oid_str.startswith(oid_prefix):
                            index = oid_str.replace(oid_prefix + '.', '')
                            results.append((index, oid_str, val.prettyPrint()))
                        else:
                            transportDispatcher.job_finished(1)
                            return wholeMsg

                for oid, val in varBindTable[-1]:
                    if not isinstance(val, pMod.Null):
                        break
                else:
                    transportDispatcher.job_finished(1)
                    continue

                pMod.apiPDU.set_varbinds(
                    reqPDU, [(x, pMod.null) for x, y in varBindTable[-1]]
                )

                pMod.apiPDU.set_request_id(reqPDU, pMod.getNextRequestID())

                transportDispatcher.send_message(
                    encoder.encode(reqMsg), transportDomain, transportAddress
                )

        return wholeMsg

    transportDispatcher = AsyncioDispatcher()
    transportDispatcher.register_recv_callback(cbRecvFun)
    transportDispatcher.register_transport(
        udp.DOMAIN_NAME, udp.UdpAsyncioTransport().open_client_mode()
    )
    transportDispatcher.send_message(
        encoder.encode(reqMsg), udp.DOMAIN_NAME, (ip, 161)
    )
    transportDispatcher.job_started(1)
    transportDispatcher.run_dispatcher(3)
    transportDispatcher.close_dispatcher()

    return results


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
    print("5. Pick another Device")
    print("6. Exit")

    return input("\nSelect what you want to do")


def int_status(device):
    int_names = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 2, 2, 1, 2),
        ip=device['hostname'],
        community="public"
    )
    admin_status = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 2, 2, 1, 7),
        ip=device['hostname'],
        community="public"
    )
    operating_status = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 2, 2, 1, 8),
        ip=device['hostname'],
        community="public"
    )

    int_names_dict = {
        idx: name for idx, _, name in int_names
    }
    admin_status_dict = {
        idx: "up" if status == "1" else "down" for idx, _, status in admin_status
    }
    operating_status_dict = {
        idx: "up" if status == "1" else "down" for idx, _, status in operating_status
    }

    print(f"{'Interface':<20} {'Admin Status':<15} {'Operational Status':<20}")
    for idx in int_names_dict:
        admin = admin_status_dict.get(idx, "unknown")
        oper = operating_status_dict.get(idx, "unknown")

        admin_display = f"[{admin}" if admin == "up" else f"{admin}"
        oper_display = f"{oper}" if oper == "up" else f"{oper}"

        print(f"{int_names_dict[idx]:<20} {admin_display:<15} {oper_display:<20}")


def ip_routes(device):
    dest_routes = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1),
        ip=device['hostname'],
        community="public"
    )
    masks = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 21, 1, 11),
        ip=device['hostname'],
        community="public"
    )
    next_hop = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 21, 1, 7),
        ip=device['hostname'],
        community="public"
    )

    dest_routes_dict = {
        idx: dest for idx, _, dest in dest_routes
    }
    mask_dict = {
        idx: mask for idx, _, mask in masks
    }
    next_hop_dict = {
        idx: hop for idx, _, hop in next_hop
    }

    print(f"{'Destination':<20} {'Mask':<15} {'Next-hop':<20}")
    for idx in dest_routes_dict:
        mask = mask_dict.get(idx, "255.255.255.255")
        next_hop = next_hop_dict.get(idx, "0.0.0.0")

        print(f"{dest_routes_dict[idx]:<20} {mask:<15} {next_hop:<15}")


def ip_addresses(device):
    address = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 20, 1, 1),
        ip=device['hostname'],
        community="public"
    )
    masks = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 20, 1, 3),
        ip=device['hostname'],
        community="public"
    )
    interfaces = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 20, 1, 2),
        ip=device['hostname'],
        community="public"
    )
    int_names = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 2, 2, 1, 2),
        ip=device['hostname'],
        community="public"
    )

    address_dict = {
        idx: addr for idx, _, addr in address
    }
    mask_dict = {
        idx: mask for idx, _, mask in masks
    }
    int_dict = {
        idx: x for idx, _, x in interfaces
    }
    int_names_dict = {
        idx: name for idx, _, name in int_names
    }

    print(f"{'Address':<20} {'Mask':<15} {'Interface':<20}")
    for idx in address_dict:
        mask = mask_dict.get(idx, "255.255.255.255")
        interface = int_dict.get(idx, "0.0.0.0")
        int_name = int_names_dict.get(interface, f"Interface {interface}")

        print(f"{address_dict[idx]:<20} {mask:<15} {int_name:<15}")


def ip_protocols(device):
    commands = "show ip protocols"
    manage_device(device, commands)

    protocols_snmp = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 5),
        ip=device['hostname'],
        community="public"
    )
    log_snmp = snmp_walk(
        oid_tuple=(1, 3, 6, 1, 4, 1, 9, 9, 41, 1, 2, 3, 1, 2),
        ip=device['hostname'],
        community="public"
    )

    protocol_types = {
        "1": "other",
        "2": "local",
        "3": "netmgmt",
        "4": "icmp",
        "5": "egp",
        "6": "ggp",
        "7": "hello",
        "8": "rip",
        "9": "is-is",
        "10": "es-is",
        "11": "ciscoIgrp",
        "12": "bbnSpfIgp",
        "13": "ospf",
        "14": "bgp"
    }

    protocols_dict = {
        idx: protocol_types.get(proto, f"Unknown ({proto})")
        for idx, _, proto in protocols_snmp
    }

    print("\nROUTING PROTOCOLS")

    if protocols_dict:
        print(f"{'Route':<40} {'Protocol':<15}")

        for idx, proto in protocols_dict.items():
            print(f"{idx:<40} {proto:<15}")
    else:
        print("No routing protocol information available")

    if log_snmp:
        print("\n\nSYSTEM LOGS")

        for _, _, message in log_snmp:
            try:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                print(message)
            except:
                print(f"[Not decodable message]")


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
                int_status(device)

            elif choice == '2':
                ip_routes(device)

            elif choice == '3':
                ip_addresses(device)

            elif choice == '4':
                ip_protocols(device)

            elif choice == '5':
                break

            elif choice == '6':
                return

            else:
                print("Invalid choice")


if __name__ == "__main__":
    main()
