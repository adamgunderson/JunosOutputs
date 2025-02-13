import paramiko

def main():
    # Device connection details (update these with your actual device info)
    device = {
        'hostname': 'your_device_ip_or_hostname',
        'port': 22,
        'username': 'your_username',
        'password': 'your_password'
    }

    # Mapping of output filenames to the commands that will be executed on the device.
    commands = {
        "config_xml": "show configuration | display xml | display inheritance | no-more",
        "interfaces_xml": "show interfaces | display xml | no-more",
        "arp_xml": "show arp | display xml | no-more",
        "ipv6_neighbor_xml": "show ipv6 neighbor | display xml | no-more",
        "service_xml": "show configuration groups junos-defaults applications | display xml | no-more",
        "route_local": "show route protocol local active-path all | display xml | no-more",
        "route_direct": "show route protocol direct active-path all | display xml | no-more",
        "route_static": "show route protocol static active-path all | display xml | no-more",
        "route_ospf": "show route protocol ospf active-path all | display xml | no-more",
        "route_rip": "show route protocol rip active-path all | display xml | no-more",
        "route_bgp": "show route protocol bgp active-path all | display xml | no-more",
        "route_mpls": "show route protocol mpls active-path all | display xml | no-more",
        "route_evpn": "show route protocol evpn active-path all | display xml | no-more"
    }

    # Create an SSH client instance and set policy to add the device's SSH key automatically.
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print("Connecting to device...")
        client.connect(**device)
        print("Connected to device.")

        # Loop over each command, execute it, and write the output to a file.
        for filename, command in commands.items():
            print(f"\nExecuting command for {filename}:")
            print(f"  {command}")
            
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                print(f"Error executing command '{command}': {error}")
            else:
                # Write the output to the specified file.
                with open(filename, 'w') as f:
                    f.write(output)
                print(f"Output saved to file: {filename}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
        print("SSH connection closed.")

if __name__ == '__main__':
    main()
