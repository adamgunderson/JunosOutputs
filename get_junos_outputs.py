#!/usr/bin/env python3
# get_junos_outputs.py - Uses Paramiko to retrieve Junos outputs with a single password prompt
# Logs command times and saves everything to /var/tmp/

import os
import sys
import getpass
import time
import tarfile
import socket
from datetime import datetime

# Better handling of Paramiko import
PARAMIKO_AVAILABLE = False
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    # Try to find paramiko in site-packages for the current Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    possible_paths = [
        f"./venv/lib/python{python_version}/site-packages",
        f"./venv/lib64/python{python_version}/site-packages",
        f"~/.local/lib/python{python_version}/site-packages",
        f"/usr/local/lib/python{python_version}/site-packages",
        f"/usr/lib/python{python_version}/site-packages",
    ]
    
    for path in possible_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path) and expanded_path not in sys.path:
            sys.path.append(expanded_path)
    
    # Try import again after adding paths
    try:
        import paramiko
        PARAMIKO_AVAILABLE = True
    except ImportError:
        pass  # Will be handled by check_paramiko()

# Default upload URL - can be overridden with command line argument
DEFAULT_UPLOAD_URL = "https://supportfiles.firemon.com/s/rGWsNfq2NZ5RFMz"

def check_paramiko():
    """
    Check if Paramiko is available and provide instructions if not.
    """
    if not PARAMIKO_AVAILABLE:
        print("Paramiko SSH library is not installed. You need to install it to use this script.")
        print("\nTo install Paramiko, run:")
        print("  pip install paramiko")
        print("\nIf pip is not available, you might need to install it first:")
        print("  python -m ensurepip --upgrade")
        print("  python -m pip install --upgrade pip")
        print("\nIf you don't have permission to install system-wide, you can install it for your user only:")
        print("  pip install --user paramiko")
        print("\nOr create a virtual environment:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On Windows, use: venv\\Scripts\\activate")
        print("  pip install paramiko")
        sys.exit(1)

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

def run_commands_with_paramiko(hostname, port, username, password, commands, output_dir, log_file):
    """
    Run commands on a remote Junos device using a single Paramiko SSH session.
    
    Args:
        hostname: The hostname or IP of the remote device
        port: SSH port (usually 22)
        username: Username for SSH authentication
        password: Password for SSH authentication
        commands: Dictionary mapping filenames to commands
        output_dir: Directory to store command outputs
        log_file: Path to the log file
    
    Returns:
        Dictionary with filenames as keys and tuples of (execution_time, success_flag) as values
    """
    execution_times = {}
    successful = 0
    
    # Log connection attempt
    connection_message = f"Establishing SSH connection to {hostname}:{port} as {username}..."
    print(connection_message)
    with open(log_file, 'a') as log:
        log.write(f"{connection_message}\n")
    
    # Create SSH client
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=int(port), username=username, password=password)
        
        connection_success = f"SSH connection established successfully."
        print(connection_success)
        with open(log_file, 'a') as log:
            log.write(f"{connection_success}\n\n")
        
        # Execute each command
        for filename, command in commands.items():
            start_time = time.time()
            log_message = f"Started executing command for {filename} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"\n{log_message}")
            
            with open(log_file, 'a') as log:
                log.write(f"\n{log_message}\n")
                log.write(f"Command: {command}\n")
            
            # Execute the command
            try:
                print(f"Executing: {command}")
                stdin, stdout, stderr = client.exec_command(command)
                
                # Read output
                output = stdout.read().decode()
                error = stderr.read().decode()
                exit_code = stdout.channel.recv_exit_status()
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                output_path = os.path.join(output_dir, filename)
                
                if exit_code != 0:
                    error_message = f"Command for {filename} returned non-zero exit code: {exit_code}"
                    if error:
                        error_message += f"\nError: {error}"
                    
                    print(error_message)
                    with open(log_file, 'a') as log:
                        log.write(f"{error_message}\n")
                        log.write(f"Execution time: {execution_time:.2f} seconds (FAILED)\n")
                    
                    # Still save the stderr output
                    with open(f"{output_path}.err", 'w') as f:
                        f.write(error)
                    
                    # Save stdout too if there's any
                    if output:
                        with open(output_path, 'w') as f:
                            f.write(output)
                    
                    execution_times[filename] = (execution_time, False)
                else:
                    # Write the output to the specified file
                    with open(output_path, 'w') as f:
                        f.write(output)
                    
                    # Also save stderr if there's any content
                    if error:
                        with open(f"{output_path}.err", 'w') as f:
                            f.write(error)
                    
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
        
        # Close SSH connection
        client.close()
        close_message = "SSH connection closed."
        print(close_message)
        with open(log_file, 'a') as log:
            log.write(f"{close_message}\n")
        
    except Exception as e:
        error_message = f"Error establishing SSH connection: {e}"
        print(error_message)
        with open(log_file, 'a') as log:
            log.write(f"{error_message}\n")
    
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
    import subprocess  # Import here to avoid issues if this function isn't used
    
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
        'password': False
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
        elif arg in ['-h', '--help']:
            print("Usage: python get_junos_outputs.py [options]")
            print("Options:")
            print("  -u, --upload-url URL  Specify Nextcloud upload URL")
            print("  -k, --insecure        Use insecure mode for HTTPS connections")
            print("  -q, --quiet           Be quiet (minimal output)")
            print("  -p, --password        Use password from SUPPORT_FILES_PASSWORD environment variable")
            print("  -h, --help            Show this help message and exit")
            sys.exit(0)
        else:
            i += 1
    
    return args

def main():
    # Check if Paramiko is available
    check_paramiko()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # If quiet mode is enabled, redirect stdout to /dev/null
    if args['quiet']:
        sys.stdout = open(os.devnull, 'w')
    
    # Set up the output directory
    output_dir = setup_output_directory()
    
    # Create a log file
    log_file = os.path.join(output_dir, "execution_log.txt")
    with open(log_file, 'w') as log:
        log.write(f"Junos Output Retrieval Tool - Execution Log\n")
        log.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        log.write(f"Upload URL: {args['upload_url']}\n")
        log.write(f"Insecure mode: {'Yes' if args['insecure'] else 'No'}\n\n")
    
    # Get device connection details
    hostname = input("Enter device hostname or IP: ")
    port = input("Enter SSH port [22]: ") or "22"
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    
    # Display connection info (except password)
    print(f"\nConnecting to {hostname}:{port} as {username}...")
    with open(log_file, 'a') as log:
        log.write(f"Device: {hostname}:{port}\n")
        log.write(f"Username: {username}\n\n")
    
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
        "route_bgp": "show route protocol bgp active-path all extensive | display xml | no-more",
        "route_mpls": "show route protocol mpls active-path all | display xml | no-more",
        "route_evpn": "show route protocol evpn active-path all | display xml | no-more",
        "route_bgp_all": "show route table ?",
        "route_bgp.l3vpn0": "show route table bgp.l3vpn0",
        "route_bgp.l3vpn0 extensive": "show route table bgp.l3vpn0 extensive"
    }
    
    # Execute commands with Paramiko
    start_total = time.time()
    execution_times = run_commands_with_paramiko(hostname, port, username, password, commands, output_dir, log_file)
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
