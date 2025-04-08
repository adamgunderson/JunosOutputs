# Junos Output Retrieval Tool

A Python script for collecting XML outputs from Junos devices with execution time logging. The script saves all outputs to a timestamped directory in `/var/tmp/` and can optionally upload the results to a Nextcloud server.

## Features

- Retrieves multiple command outputs from Junos devices in XML format
- Uses a single SSH connection with one password prompt via Paramiko
- Logs execution time for each command
- Organizes outputs in a timestamped directory in `/var/tmp/`
- Compresses all outputs into a tar.gz archive
- Uploads results to a Nextcloud server (optional)
- Comprehensive logging of all operations

## Requirements

- Python 3.x (tested with Python 3.12)
- Paramiko SSH library
- Curl (for upload functionality)

## Installation

1. Clone or download this repository

2. Set up a virtual environment (recommended):

```bash
# Create a virtual environment
python3.12 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Your terminal prompt should now show (venv) at the beginning
```

3. Install the required Paramiko library:

```bash
# Inside the activated virtual environment
pip install paramiko
```

4. When you're done using the script, you can deactivate the virtual environment:

```bash
deactivate
```

### Alternative Installation Methods

If you prefer not to use a virtual environment, you can install Paramiko directly:

```bash
python3.12 -m pip install paramiko
```

If you don't have permission to install system-wide, you can install for your user only:

```bash
python3.12 -m pip install --user paramiko
```

## Usage

### Using with a Virtual Environment

If you installed with a virtual environment (recommended), make sure the environment is activated before running the script:

```bash
# Activate the virtual environment if not already activated
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate   # On Windows

# Then run the script
python get_junos_outputs.py
```

### Basic Usage

```bash
python3.12 get_junos_outputs.py
```

With options:

```bash
python3.12 get_junos_outputs.py [options]
```

### Command Line Options

```
-u, --upload-url URL  Specify Nextcloud upload URL
-k, --insecure        Use insecure mode for HTTPS connections
-q, --quiet           Be quiet (minimal output)
-p, --password        Use password from SUPPORT_FILES_PASSWORD environment variable
-h, --help            Show this help message and exit
```

### Example

To retrieve outputs and upload to a custom Nextcloud URL with insecure SSL:

```bash
python3.12 get_junos_outputs.py -u https://yourserver.com/s/yourtoken -k
```

## Output Structure

The script creates a directory in `/var/tmp/` with the following naming convention:

```
/var/tmp/junos_outputs_[hostname]_YYYYMMDD_HHMMSS/
```

This directory contains:
- Command outputs in XML format
- Error files (if any)
- Execution log with timing information
- Archive created in the same location with .tar.gz extension

## Collected Command Outputs

The script collects the following information from Junos devices:

- Configuration (XML format)
- Interfaces information
- ARP table
- IPv6 neighbor table
- Default service definitions
- Routing tables (multiple protocols)
- And more...

## Troubleshooting

### Paramiko Not Installed

If you get an error about Paramiko not being installed, follow the installation instructions in the error message:

```bash
python3.12 -m pip install --user paramiko
```

### Connection Issues

- Verify device hostname/IP is correct
- Check that SSH port is correct (default is 22)
- Verify username and password are correct
- Ensure device is reachable from your system

### Upload Failures

- Check your Nextcloud URL
- Verify that curl is installed
- For SSL certificate issues, try using the `-k` flag

## License

This script is provided as-is for use with Juniper devices. Feel free to modify as needed.
