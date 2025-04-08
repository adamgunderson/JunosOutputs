#!/usr/bin/env python3
# get_junos_outputs.py - Modified version with command timing logging,
# outputs saved to /var/tmp/, and automatic upload to Nextcloud

import subprocess
import os
import sys
import getpass
import time
import tarfile
import tempfile
from datetime import datetime

def ensure_module(module_name):
    """Dynamically import a module by searching for it in potential site-packages locations"""
    # First try the normal import in case it's already in the path
    try:
        return __import__(module_name)
    except ImportError:
        pass
    
    # Get the current Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    # Create a list of potential paths to check
    base_path = '/usr/lib/firemon/devpackfw/lib'
    potential_paths = [
        # Current Python version
        f"{base_path}/python{py_version}/site-packages",
        # Exact Python version with patch
        f"{base_path}/python{sys.version.split()[0]}/site-packages",
        # Try a range of nearby versions (for future-proofing)
        *[f"{base_path}/python3.{i}/site-packages" for i in range(8, 20)]
    ]
    
    # Try each path
    for path in potential_paths:
        if os.path.exists(path):
            if path not in sys.path:
                sys.path.append(path)
            try:
                return __import__(module_name)
            except ImportError:
                continue
    
    # If we get here, we couldn't find the module
    raise ImportError(f"Could not find module {module_name} in any potential site-packages location")

# Import required modules
requests = ensure_module("requests")

# Default upload URL - can be overridden with command line argument
DEFAULT_UPLOAD_URL = "https://supportfiles.firemon.com/s/rGWsNfq2NZ5RFMz"

def setup_output_directory():
    """
    Create a directory in /var/tmp/ with a timestamp name to store all outputs.
    Returns the path to the created directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hostname = subprocess.getoutput("hostname").strip()
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

def run_command(hostname, username, password, command, output_dir, filename, log_file):
    """
    Run a command on a remote Junos device using the ssh command-line tool.
    Saves the output to the specified filename in the output directory.
    Logs execution time to the log file.
    """
    start_time = time.time()
    log_message = f"Started executing command for {filename} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print(log_message)
    
    with open(log_file, 'a') as log:
        log.write(f"{log_message}\n")
        log.write(f"Command: {command}\n")
    
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
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        output_path = os.path.join(output_dir, filename)
        
        if result.returncode != 0:
            error_message = f"Error executing command for {filename}: {result.stderr}"
            print(error_message)
            with open(log_file, 'a') as log:
                log.write(f"{error_message}\n")
                log.write(f"Execution time: {execution_time:.2f} seconds (FAILED)\n\n")
            return False
        
        # Write the output to the specified file
        with open(output_path, 'w') as f:
            f.write(result.stdout)
        
        success_message = f"Output saved to file: {output_path}"
        timing_message = f"Execution time for {filename}: {execution_time:.2f} seconds"
        
        print(success_message)
        print(timing_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{success_message}\n")
            log.write(f"{timing_message}\n\n")
        
        return True
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        error_message = f"An error occurred while executing command for {filename}: {e}"
        print(error_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{error_message}\n")
            log.write(f"Execution time: {execution_time:.2f} seconds (ERROR)\n\n")
        
        return False

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

def upload_to_nextcloud(archive_path, upload_url, log_file, insecure=False):
    """
    Upload the compressed archive to the specified Nextcloud URL.
    Similar to the bash script's upload functionality.
    
    Uses either the requests library or falls back to curl if requests is not available.
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
        
        # Check if curl is available as a fallback
        curl_available = False
        try:
            subprocess.run(['which', 'curl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            curl_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Try to use requests library first
        try:
            # Set up headers
            headers = {
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Read file data
            with open(archive_path, 'rb') as file:
                file_data = file.read()
            
            # Upload file using requests
            verify = not insecure
            response = requests.put(
                endpoint,
                data=file_data,
                headers=headers,
                auth=(folder_token, password),
                verify=verify
            )
        
            # Check response
            if response.status_code in [200, 201, 204]:
                success_message = f"Upload successful! Status code: {response.status_code}"
                print(success_message)
                
                with open(log_file, 'a') as log:
                    log.write(f"{success_message}\n")
                
                return True
            else:
                error_message = f"Upload failed. Status code: {response.status_code}"
                print(error_message)
                print(f"Response: {response.text}")
                
                with open(log_file, 'a') as log:
                    log.write(f"{error_message}\n")
                    log.write(f"Response: {response.text}\n")
                
                # If requests failed, try curl as a fallback if available
                if curl_available:
                    print("Attempting upload using curl as fallback...")
                    return _upload_with_curl(archive_path, cloud_url, folder_token, password, insecure, log_file)
                return False
                
        except Exception as e:
            print(f"Error using requests library: {e}")
            print("Attempting upload using curl as fallback...")
            
            with open(log_file, 'a') as log:
                log.write(f"Error using requests library: {e}\n")
                log.write("Attempting upload using curl as fallback...\n")
            
            # If requests failed, try curl as a fallback if available
            if curl_available:
                return _upload_with_curl(archive_path, cloud_url, folder_token, password, insecure, log_file)
            
            # If curl is not available either, return failure
            error_message = "Both requests library and curl are unavailable. Upload failed."
            print(error_message)
            
            with open(log_file, 'a') as log:
                log.write(f"{error_message}\n")
            
            return False
    except Exception as e:
        error_message = f"Error uploading archive: {e}"
        print(error_message)
        
        with open(log_file, 'a') as log:
            log.write(f"{error_message}\n")
        
        return False

def _upload_with_curl(archive_path, cloud_url, folder_token, password, insecure, log_file):
    """
    Helper function to upload the archive using curl command line tool as a fallback.
    """
    try:
        # Get filename from archive path
        filename = os.path.basename(archive_path)
        
        # Set up API endpoint
        endpoint = f"{cloud_url}/public.php/webdav/{filename}"
        
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
    Parse command line arguments.
    Returns a dictionary of arguments.
    """
    try:
        import argparse
    except ImportError:
        argparse = ensure_module("argparse")
    
    parser = argparse.ArgumentParser(description='Retrieve outputs from a Junos device and upload them to Nextcloud.')
    parser.add_argument('-u', '--upload-url', default=DEFAULT_UPLOAD_URL,
                      help='Nextcloud upload URL (default: %(default)s)')
    parser.add_argument('-k', '--insecure', action='store_true',
                      help='Use insecure mode for HTTPS connections')
    parser.add_argument('-q', '--quiet', action='store_true',
                      help='Be quiet (minimal output)')
    parser.add_argument('-p', '--password', action='store_true',
                      help='Use password from SUPPORT_FILES_PASSWORD environment variable')
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # If quiet mode is enabled, redirect stdout to /dev/null
    if args.quiet:
        sys.stdout = open(os.devnull, 'w')
    
    # Set up the output directory
    output_dir = setup_output_directory()
    
    # Create a log file
    log_file = os.path.join(output_dir, "execution_log.txt")
    with open(log_file, 'w') as log:
        log.write(f"Junos Output Retrieval Tool - Execution Log\n")
        log.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        log.write(f"Upload URL: {args.upload_url}\n")
        log.write(f"Insecure mode: {'Yes' if args.insecure else 'No'}\n\n")
    
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
    
    # Loop over each command, execute it, and write the output to a file
    start_total = time.time()
    successful = 0
    
    for filename, command in commands.items():
        if run_command(hostname, username, password, command, output_dir, filename, log_file):
            successful += 1
    
    end_total = time.time()
    total_time = end_total - start_total
    
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
        # Upload the archive to Nextcloud
        upload_success = upload_to_nextcloud(archive_path, args.upload_url, log_file, args.insecure)
        
        with open(log_file, 'a') as log:
            log.write(f"Upload successful: {'Yes' if upload_success else 'No'}\n")
            log.write(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Display final message
        if upload_success:
            print(f"\nArchive uploaded successfully to {args.upload_url}")
        else:
            print(f"\nFailed to upload archive to {args.upload_url}")
    else:
        print("\nFailed to create archive. Upload skipped.")
        
        with open(log_file, 'a') as log:
            log.write("Failed to create archive. Upload skipped.\n")
            log.write(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == '__main__':
    main()
