#!/usr/bin/env python3
# get_junos_outputs.py - Standard Library version
# Retrieves Junos outputs, logs command times, saves to /var/tmp/
# No external dependencies required

import os
import sys
import getpass
import time
import tarfile
import socket
import subprocess
import urllib.request
from datetime import datetime

# Default upload URL - can be overridden with command line argument
DEFAULT_UPLOAD_URL = "https://supportfiles.firemon.com/s/rGWsNfq2NZ5RFMz"
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/adamgunderson/JunosOutputs/refs/heads/main/get_junos_outputs.py"

def check_for_updates(script_url, log_file=None, create_backup=False):
    """
    Check for and apply updates from the provided URL.
    
    Args:
        script_url: URL to download the updated script from
        log_file: Path to log file to write messages to
        create_backup: Whether to create a backup before updating (default: False)
        
    Returns:
        True if an update was applied, False otherwise.
    """
    try:
        print("Checking for updates...")
        if log_file:
            with open(log_file, 'a') as log:
                log.write(f"Checking for updates from: {script_url}\n")
        
        # Get the current script path
        current_script = os.path.abspath(sys.argv[0])
        
        # Download the latest version
        print(f"Downloading latest version from {script_url}")
        response = urllib.request.urlopen(script_url)
        latest_code = response.read().decode('utf-8')
        
        # Read the current version
        with open(current_script, 'r') as f:
            current_code = f.read()
        
        # Compare versions
        if latest_code != current_code:
            print("Update available! Applying...")
            if log_file:
                with open(log_file, 'a') as log:
                    log.write("Update available! Applying...\n")
            
            # Create a backup of the current script if requested
            if create_backup:
                backup_file = f"{current_script}.bak"
                with open(backup_file, 'w') as f:
                    f.write(current_code)
                print(f"Backup created at {backup_file}")
                if log_file:
                    with open(log_file, 'a') as log:
                        log.write(f"Backup created at: {backup_file}\n")
            else:
                print("Skipping backup creation (default behavior)")
                if log_file:
                    with open(log_file, 'a') as log:
                        log.write("Skipping backup creation (default behavior)\n")
            
            # Write the new version
            with open(current_script, 'w') as f:
                f.write(latest_code)
            
            print("Update applied successfully. Restarting script...")
            if log_file:
                with open(log_file, 'a') as log:
                    log.write("Update applied successfully.\n")
                    log.write("Restarting script...\n")
            
            # Restart the script
            os.execv(sys.executable, ['python'] + sys.argv)
            
            # We won't reach here, but for clarity:
            return True
        else:
            print("No updates available. Running current version.")
            if log_file:
                with open(log_file, 'a') as log:
                    log.write("No updates available. Running current version.\n")
            return False
    except Exception as e:
        error_message = f"Error checking for updates: {e}"
        print(error_message)
        print("Continuing with current version...")
        if log_file:
            with open(log_file, 'a') as log:
                log.write(f"{error_message}\n")
                log.write("Continuing with current version...\n")
        return False

def setup_output_directory():
    """
    Create a directory in /var/tmp/ with a timestamp name to store all outputs.
    Returns the path to the created directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hostname = socket.gethostname()
    dir_path = f"/var/tmp/junos_outputs_{hostname}_{timestamp}"
    
    try:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created output directory: {dir_path}")
        return dir_path
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")
        # Fallback to current directory if /var/tmp/ is not accessible
        fallback_dir = f"./junos_outputs_{hostname}_{timestamp}"
        os.makedirs(fallback_dir, exist_ok=True)
        print(f"Using fallback directory: {fallback_dir}")
        return fallback_dir

def setup_ssh_control_master(hostname, port, username, log_file):
    """
    Attempt to set up an SSH control master connection to avoid multiple password prompts.
    
    Returns:
        tuple: (success, connection_command)
    """
    try:
        # Create a control socket directory if it doesn't exist
        socket_dir = os.path.expanduser("~/.ssh/cm")
        os.makedirs(socket_dir, exist_ok=True)
        
        # Define the control socket path
        control_path = f"{socket_dir}/junos-ssh-%h-%p-%r"
        
        # Build the connection command
        connection_cmd = [
            "ssh", 
            "-o", "ControlMaster=auto",
            "-o", "ControlPersist=60m",
            "-o", "ControlPath=" + control_path,
            "-o", "StrictHostKeyChecking=no",
            "-p", str(port),
            f"{username}@{hostname}",
            "echo 'SSH Control Master connection established'"
        ]
        
        # Attempt to establish the control connection
        print("Attempting to establish SSH control connection...")
        with open(log_file, 'a') as log:
            log.write("Attempting to establish SSH control connection...\n")
        
        process = subprocess.run(
            connection_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode == 0:
            success_msg = "SSH control connection established successfully. You should only need to enter your password once."
            print(success_msg)
            with open(log_file, 'a') as log:
                log.write(f"{success_msg}\n")
            
            # Return the base command to use for future connections
            ssh_cmd = [
                "ssh",
                "-o", "ControlPath=" + control_path,
                "-o", "StrictHostKeyChecking=no",
                "-p", str(port),
                f"{username}@{hostname}"
            ]
            
            return True, ssh_cmd
        else:
            failure_msg = "Failed to establish SSH control connection. You may be prompted for password multiple times."
            print(failure_msg)
            if process.stderr:
                print(f"Error: {process.stderr}")
            with open(log_file, 'a') as log:
                log.write(f"{failure_msg}\n")
                if process.stderr:
                    log.write(f"Error: {process.stderr}\n")
            
            # Fall back to regular SSH command
            ssh_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-p", str(port),
                f"{username}@{hostname}"
            ]
            
            return False, ssh_cmd
    
    except Exception as e:
        error_msg = f"Error setting up SSH control connection: {e}"
        print(error_msg)
        with open(log_file, 'a') as log:
            log.write(f"{error_msg}\n")
        
        # Fall back to regular SSH command
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-p", str(port),
            f"{username}@{hostname}"
        ]
        
        return False, ssh_cmd

def run_commands(hostname, port, username, commands, output_dir, log_file):
    """
    Run commands on a remote Junos device.
    Attempts to use SSH control master to minimize password prompts.
    
    Args:
        hostname: The hostname or IP of the remote device
        port: SSH port (usually 22)
        username: Username for SSH authentication
        commands: Dictionary mapping filenames to commands
        output_dir: Directory to store command outputs
        log_file: Path to the log file
    
    Returns:
        Dictionary with filenames as keys and tuples of (execution_time, success_flag) as values
    """
    execution_times = {}
    successful = 0
    
    # First, try to set up an SSH control master connection
    control_success, ssh_base_cmd = setup_ssh_control_master(hostname, port, username, log_file)
    
    # Check if we're in CLI or shell mode
    print("Detecting Junos environment...")
    with open(log_file, 'a') as log:
        log.write("Detecting Junos environment...\n")
    
    test_cmd = ssh_base_cmd + ["echo $SHELL"]
    result = subprocess.run(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # If we get a valid shell path, we're in shell mode and need to use 'cli' command
    in_shell_mode = False
    if result.returncode == 0 and ('/' in result.stdout or '\\' in result.stdout):
        print("Detected shell environment. Using 'cli' command to execute Junos commands.")
        with open(log_file, 'a') as log:
            log.write("Detected shell environment. Using 'cli' command to execute Junos commands.\n")
        in_shell_mode = True
    else:
        print("Detected Junos CLI environment. Executing commands directly.")
        with open(log_file, 'a') as log:
            log.write("Detected Junos CLI environment. Executing commands directly.\n")
    
    # Execute each command
    for filename, command in commands.items():
        start_time = time.time()
        log_message = f"Started executing command for {filename} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        print(f"\n{log_message}")
        
        with open(log_file, 'a') as log:
            log.write(f"\n{log_message}\n")
            log.write(f"Command: {command}\n")
        
        # Modify command for shell mode if needed
        if in_shell_mode:
            # Escape quotes in the command
            escaped_command = command.replace('"', '\\"')
            exec_command = f'cli -c "{escaped_command}"'
        else:
            exec_command = command
        
        # Build the full command to execute
        cmd = ssh_base_cmd + [exec_command]
        
        # Execute the command
        try:
            print(f"Executing: {exec_command}")
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            output_path = os.path.join(output_dir, filename)
            
            if process.returncode != 0:
                error_message = f"Command for {filename} failed with exit code {process.returncode}"
                if process.stderr:
                    error_message += f"\nError: {process.stderr}"
                
                print(error_message)
                with open(log_file, 'a') as log:
                    log.write(f"{error_message}\n")
                    log.write(f"Execution time: {execution_time:.2f} seconds (FAILED)\n")
                
                # Save stderr to error file
                with open(f"{output_path}.err", 'w') as f:
                    f.write(process.stderr)
                
                # Save stdout too if there's any
                if process.stdout:
                    with open(output_path, 'w') as f:
                        f.write(process.stdout)
                
                execution_times[filename] = (execution_time, False)
            else:
                # Write the output to the specified file
                with open(output_path, 'w') as f:
                    f.write(process.stdout)
                
                # Also save stderr if there's any content
                if process.stderr:
                    with open(f"{output_path}.err", 'w') as f:
                        f.write(process.stderr)
                
                success_message = f"Output saved to file: {output_path}"
                timing_message = f"Execution time for {filename}: {execution_time:.2f} seconds"
                
                print(success_message)
                print(timing_message)
                
                with open(log_file, 'a') as log:
                    log.write(f"{success_message}\n")
                    log.write(f"{timing_message}\n")
                
                execution_times[filename] = (execution_time, True)
                successful += 1
                
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            error_message = f"An error occurred while executing command for {filename}: {e}"
            print(error_message)
            
            with open(log_file, 'a') as log:
                log.write(f"{error_message}\n")
                log.write(f"Execution time: {execution_time:.2f} seconds (ERROR)\n")
            
            execution_times[filename] = (execution_time, False)
    
    # Clean up SSH control master if it was established
    if control_success:
        cleanup_cmd = ssh_base_cmd[:-1] + ["-O", "exit", hostname]
        try:
            subprocess.run(cleanup_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("SSH control connection closed.")
        except:
            pass
    
    # Print summary
    print(f"\nCompleted {successful} of {len(commands)} commands successfully.")
    
    return execution_times

def compress_directory(directory_path, log_file):
    """
    Compress the output directory into a tar.gz archive.
    Returns the path to the compressed archive.
    """
    try:
        # Get directory name for the archive filename
        dir_name = os.path.basename(directory_path)
        archive_path = f"{directory_path}.tar.gz"
        
        log_message = f"Compressing directory {directory_path} to {archive_path}"
        print(log_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{log_message}\n")
        
        # Create archive
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(directory_path, arcname=dir_name)
        
        # Get archive size
        archive_size_bytes = os.path.getsize(archive_path)
        if archive_size_bytes < 1024:
            size_str = f"{archive_size_bytes} bytes"
        elif archive_size_bytes < 1048576:
            size_str = f"{archive_size_bytes/1024:.2f} KB"
        elif archive_size_bytes < 1073741824:
            size_str = f"{archive_size_bytes/1048576:.2f} MB"
        else:
            size_str = f"{archive_size_bytes/1073741824:.2f} GB"
        
        success_message = f"Archive created: {archive_path} ({size_str})"
        print(success_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{success_message}\n")
        
        return archive_path
    except Exception as e:
        error_message = f"Error compressing directory: {e}"
        print(error_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{error_message}\n")
        
        return None

def upload_with_curl(archive_path, upload_url, log_file, insecure=False):
    """
    Upload the compressed archive to the specified Nextcloud URL using curl.
    """
    try:
        # Extract cloud URL and folder token from the upload URL
        # Remove /s/token from the end of the URL to get the base URL
        cloud_url = upload_url.split('/s/')[0]
        # Extract token from the URL
        folder_token = upload_url.split('/s/')[1]
        
        log_message = f"Uploading archive to Nextcloud..."
        print(log_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{log_message}\n")
            log.write(f"Cloud URL: {cloud_url}\n")
            log.write(f"Folder Token: {folder_token}\n")
        
        # Get filename from archive path
        filename = os.path.basename(archive_path)
        
        # Set up API endpoint
        endpoint = f"{cloud_url}/public.php/webdav/{filename}"
        
        # Get password from environment variable if set
        password = os.environ.get('SUPPORT_FILES_PASSWORD', '')
        
        # Build curl command
        curl_cmd = ['curl']
        
        # Add insecure flag if requested
        if insecure:
            curl_cmd.append('-k')
        
        # Add authentication
        curl_cmd.extend(['-u', f"{folder_token}:{password}"])
        
        # Add headers
        curl_cmd.extend(['-H', 'X-Requested-With: XMLHttpRequest'])
        
        # Add upload file option
        curl_cmd.extend(['-T', archive_path])
        
        # Add URL
        curl_cmd.append(endpoint)
        
        # Log the command (without password)
        safe_cmd = ' '.join([arg if not password or password not in arg else arg.replace(password, '********') for arg in curl_cmd])
        log_message = f"Running curl command: {safe_cmd}"
        print(log_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{log_message}\n")
        
        # Execute curl command
        result = subprocess.run(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Check result
        if result.returncode == 0:
            success_message = "Upload successful using curl!"
            print(success_message)
            
            with open(log_file, 'a') as log:
                log.write(f"{success_message}\n")
            
            return True
        else:
            error_message = f"Upload failed using curl. Return code: {result.returncode}"
            print(error_message)
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            
            with open(log_file, 'a') as log:
                log.write(f"{error_message}\n")
                log.write(f"stdout: {result.stdout}\n")
                log.write(f"stderr: {result.stderr}\n")
            
            return False
    except Exception as e:
        error_message = f"Error using curl for upload: {e}"
        print(error_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{error_message}\n")
        
        return False

def parse_arguments():
    """
    Parse command line arguments using a simple approach that doesn't require argparse.
    """
    args = {
        'upload_url': DEFAULT_UPLOAD_URL,
        'insecure': False,
        'quiet': False,
        'password': False,
        'auto_update': False,
        'update_url': DEFAULT_UPDATE_URL,
        'create_backup': False  # Default to NOT creating backups
    }
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['-u', '--upload-url'] and i + 1 < len(sys.argv):
            args['upload_url'] = sys.argv[i + 1]
            i += 2
        elif arg in ['-k', '--insecure']:
            args['insecure'] = True
            i += 1
        elif arg in ['-q', '--quiet']:
            args['quiet'] = True
            i += 1
        elif arg in ['-p', '--password']:
            args['password'] = True
            i += 1
        elif arg in ['--auto-update']:
            args['auto_update'] = True
            i += 1
        elif arg in ['--update-url'] and i + 1 < len(sys.argv):
            args['update_url'] = sys.argv[i + 1]
            i += 2
        elif arg in ['--with-backup']:  # Changed from --no-backup to --with-backup
            args['create_backup'] = True  # Now this enables backups instead of disabling them
            i += 1
        elif arg in ['-h', '--help']:
            print("Usage: python get_junos_outputs.py [options]")
            print("Options:")
            print("  -u, --upload-url URL  Specify Nextcloud upload URL")
            print("  -k, --insecure        Use insecure mode for HTTPS connections")
            print("  -q, --quiet           Be quiet (minimal output)")
            print("  -p, --password        Use password from SUPPORT_FILES_PASSWORD environment variable")
            print("  --auto-update         Automatically check for and apply updates")
            print("  --update-url URL      Specify the URL to check for updates")
            print("  --with-backup         Create backup files when updating (not the default)")
            print("  -h, --help            Show this help message and exit")
            sys.exit(0)
        else:
            i += 1
    
    return args

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up the output directory
    output_dir = setup_output_directory()
    
    # Create a log file
    log_file = os.path.join(output_dir, "execution_log.txt")
    with open(log_file, 'w') as log:
        log.write(f"Junos Output Retrieval Tool - Execution Log\n")
        log.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        log.write(f"Upload URL: {args['upload_url']}\n")
        log.write(f"Insecure mode: {'Yes' if args['insecure'] else 'No'}\n\n")
        if args['auto_update']:
            log.write(f"Auto-update: Enabled\n")
            log.write(f"Update URL: {args['update_url']}\n")
            log.write(f"Create backup: {'Yes' if args['create_backup'] else 'No'}\n\n")
    
    # Check for updates if auto-update is enabled
    if args['auto_update']:
        updated = check_for_updates(args['update_url'], log_file, args['create_backup'])
        if updated:
            # If an update was applied, the script would have restarted
            # So we won't reach here
            return
    
    # If quiet mode is enabled, redirect stdout to /dev/null
    if args['quiet']:
        sys.stdout = open(os.devnull, 'w')
    
    # Get device connection details
    hostname = input("Enter device hostname or IP: ")
    port = input("Enter SSH port [22]: ") or "22"
    username = input("Enter username: ")
    
    # Display connection info
    print(f"\nConnecting to {hostname}:{port} as {username}...")
    with open(log_file, 'a') as log:
        log.write(f"Device: {hostname}:{port}\n")
        log.write(f"Username: {username}\n\n")
    
    # Mapping of output filenames to the commands
    commands = {
        # "config_xml": "show configuration | display xml | display inheritance | no-more",
        # "interfaces_xml": "show interfaces | display xml | no-more",
        # "arp_xml": "show arp | display xml | no-more",
        # "ipv6_neighbor_xml": "show ipv6 neighbor | display xml | no-more",
        # "service_xml": "show configuration groups junos-defaults applications | display xml | no-more",
        # "route_local": "show route protocol local active-path all | display xml | no-more",
        # "route_direct": "show route protocol direct active-path all | display xml | no-more",
        # "route_static": "show route protocol static active-path all | display xml | no-more",
        # "route_ospf": "show route protocol ospf active-path all | display xml | no-more",
        # "route_rip": "show route protocol rip active-path all | display xml | no-more",
        # "route_bgp": "show route protocol bgp active-path all extensive | display xml | no-more",
        # "route_mpls": "show route protocol mpls active-path all | display xml | no-more",
        # "route_evpn": "show route protocol evpn active-path all | display xml | no-more",
        "route_bgp.l3vpn0": "show route table bgp.l3vpn.0",
        "route_bgp.l3vpn0_extensive": "show route table bgp.l3vpn.0 extensive",
        "route_bgp.l3vpn-inet6_extensive": "show route table bgp.l3vpn-inet6.0 extensive | display xml | no-more"
    }
    
    # Execute commands
    start_total = time.time()
    execution_times = run_commands(hostname, port, username, commands, output_dir, log_file)
    end_total = time.time()
    total_time = end_total - start_total
    
    # Count successful commands
    successful = sum(1 for _, (_, success) in execution_times.items() if success)
    
    completion_message = f"\nCompleted {successful} of {len(commands)} commands successfully."
    timing_message = f"Total execution time: {total_time:.2f} seconds"
    
    print(completion_message)
    print(timing_message)
    print(f"All outputs and logs saved to: {output_dir}")
    
    with open(log_file, 'a') as log:
        log.write(f"{completion_message}\n")
        log.write(f"{timing_message}\n")
    
    # Compress the output directory
    archive_path = compress_directory(output_dir, log_file)
    
    if archive_path:
        # Upload the archive to Nextcloud using curl
        upload_success = upload_with_curl(archive_path, args['upload_url'], log_file, args['insecure'])
        
        with open(log_file, 'a') as log:
            log.write(f"Upload successful: {'Yes' if upload_success else 'No'}\n")
            log.write(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Display final message
        if upload_success:
            print(f"\nArchive uploaded successfully to {args['upload_url']}")
        else:
            print(f"\nFailed to upload archive to {args['upload_url']}")
    else:
        print("\nFailed to create archive. Upload skipped.")
        
        with open(log_file, 'a') as log:
            log.write("Failed to create archive. Upload skipped.\n")
            log.write(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == '__main__':
    main()
