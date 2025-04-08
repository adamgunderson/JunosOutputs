#!/usr/bin/env python3
# get_junos_outputs_simple.py - A simplified version using standard library
# instead of paramiko to retrieve Junos device outputs

import subprocess
import os
import sys
import getpass

def run_command(hostname, username, password, command, filename):
    """
    Run a command on a remote Junos device using the ssh command-line tool.
    Saves the output to the specified filename.
    """
    # Use sshpass if available, otherwise the user might be prompted for password
    try:
        # Check if sshpass is available
        subprocess.run(['which', 'sshpass'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        ssh_command = [
            'sshpass', '-p', password, 
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            f'{username}@{hostname}', command
        ]
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"sshpass not found. You may be prompted for a password.")
        ssh_command = [
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            f'{username}@{hostname}', command
        ]
    
    try:
        print(f"Executing command for {filename}:")
        print(f"  {command}")
        
        # Run the SSH command and capture the output
        result = subprocess.run(
            ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False  # Don't raise an exception on non-zero exit code
        )
        
        if result.returncode != 0:
            print(f"Error executing command: {result.stderr}")
            return False
        
        # Write the output to the specified file
        with open(filename, 'w') as f:
            f.write(result.stdout)
        
        print(f"Output saved to file: {filename}")
        return True
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def main():
    # Get device connection details
    hostname = input("Enter device hostname or IP: ")
    port = input("Enter SSH port [22]: ") or "22"
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    
    # Display connection info (except password)
    print(f"\nConnecting to {hostname}:{port} as {username}...")
    
    # Mapping of output filenames to the commands
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
    
    # Loop over each command, execute it, and write the output to a file
    successful = 0
    for filename, command in commands.items():
        if run_command(hostname, username, password, command, filename):
            successful += 1
    
    print(f"\nCompleted {successful} of {len(commands)} commands successfully.")

if __name__ == '__main__':
    main()
