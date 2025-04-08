# Junos Output Collection Tool

A Python-based utility for collecting diagnostic information from Juniper Networks devices.

## Overview

`get_junos_outputs.py` is a standalone Python script that collects operational and configuration data from Junos devices. It requires no external dependencies (uses only the Python standard library), making it suitable for environments where installing packages is restricted.

## Features

- **No Dependencies**: Uses only Python standard library modules
- **SSH Control Master**: Minimizes password prompts during command execution
- **Command Timing**: Logs execution time for each command
- **Output Organization**: Creates a timestamped directory in `/var/tmp/` to store outputs
- **Automatic Compression**: Compresses collected data into a tar.gz archive
- **Cloud Upload**: Uploads the archive to a Nextcloud server for easy sharing

## Requirements

- Python 3.6+
- SSH access to Junos devices
- Write access to `/var/tmp/` (falls back to current directory if unavailable)

## Installation

No installation required. Simply download the script and make it executable:

```bash
chmod +x get_junos_outputs.py
```

## Usage

### Basic Usage

Run the script and follow the prompts:

```bash
./get_junos_outputs.py
```

You will be prompted to enter:
- Device hostname or IP address
- SSH port (defaults to 22)
- Username for SSH authentication

### Command-line Options

```
Usage: python get_junos_outputs.py [options]
Options:
  -u, --upload-url URL  Specify Nextcloud upload URL
                        (default: https://supportfiles.firemon.com/s/rGWsNfq2NZ5RFMz)
  -k, --insecure        Use insecure mode for HTTPS connections
  -q, --quiet           Be quiet (minimal output)
  -p, --password        Use password from SUPPORT_FILES_PASSWORD environment variable
  -h, --help            Show this help message and exit
```

### Examples

Upload to a custom URL:
```bash
./get_junos_outputs.py --upload-url https://mycloud.example.com/s/mytoken
```

Skip SSL verification for upload:
```bash
./get_junos_outputs.py --insecure
```

Run with minimal output:
```bash
./get_junos_outputs.py --quiet
```

## Collected Data

The script collects the following information from Junos devices:

- Device configuration (XML format with inheritance)
- Interface information
- ARP and IPv6 neighbor tables
- Default application configurations
- Routing tables for various protocols:
  - Local routes
  - Direct routes
  - Static routes
  - OSPF routes
  - RIP routes
  - BGP routes (with extensive information)
  - MPLS routes
  - EVPN routes
  - L3VPN routes

## Output Files

The script creates:

1. A timestamped directory in `/var/tmp/` (format: `/var/tmp/junos_outputs_HOSTNAME_YYYYMMDD_HHMMSS/`)
2. Individual output files for each command
3. An execution log (`execution_log.txt`)
4. A compressed archive of all outputs (`.tar.gz`)

## File Upload

The script can upload the compressed outputs to a Nextcloud server:

- Default upload URL: `https://supportfiles.firemon.com/s/rGWsNfq2NZ5RFMz`
- Upload uses `curl` command with the WebDAV protocol
- Authentication uses the share token (extracted from the URL)
- Set the `SUPPORT_FILES_PASSWORD` environment variable if a password is required

## Troubleshooting

- **SSH Connection Issues**: Ensure you have SSH access to the target device
- **Permission Errors**: The script needs write access to `/var/tmp/`
- **Upload Failures**: Check network connectivity to the upload server
- **Command Errors**: Review the execution log for specific command failures

## Output Directory Structure

```
/var/tmp/junos_outputs_HOSTNAME_YYYYMMDD_HHMMSS/
├── config_xml
├── interfaces_xml
├── arp_xml
├── ipv6_neighbor_xml
├── service_xml
├── route_local
├── route_direct
├── ... (other route files)
└── execution_log.txt
```

---

For more information or assistance, please contact your FireMon Sales Engineer.
