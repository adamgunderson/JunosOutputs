# Junos Output Collection Tools

This repository contains tools for collecting and exporting output from Juniper Networks devices (Junos OS). These scripts help network engineers gather diagnostic information quickly and efficiently.

## Contents

- [Overview](#overview)
- [Scripts](#scripts)
  - [Python Script](#python-script)
  - [Ansible Playbook](#ansible-playbook)
- [Installation](#installation)
- [Usage](#usage)
  - [Using the Python Script](#using-the-python-script)
  - [Using the Ansible Playbook](#using-the-ansible-playbook)
- [Collected Data](#collected-data)
- [File Upload](#file-upload)
- [Troubleshooting](#troubleshooting)

## Overview

These scripts automate the collection of operational and configuration data from Junos devices. This is particularly useful for:

- Troubleshooting network issues
- Gathering data for support cases
- Auditing network configuration
- Documenting network state

## Scripts

### Python Script

`get_junos_outputs.py` is a standalone Python script that:

- Requires no external dependencies (uses only the Python standard library)
- Connects to Junos devices via SSH
- Executes multiple show commands and saves their outputs
- Times command execution
- Compresses the outputs into a tar.gz archive
- Optionally uploads the archive to a Nextcloud server

### Ansible Playbook

`get_junos_outputs.yml` is an Ansible playbook that:

- Uses the Juniper.junos collection
- Executes multiple show commands in XML format
- Saves command outputs to local files
- Works with existing Ansible inventory

## Installation

### Python Script Requirements

- Python 3.6+
- SSH access to Junos devices

### Ansible Playbook Requirements

- Ansible 2.9+
- Juniper.junos collection
- SSH access to Junos devices

To install the required Ansible collection:

```bash
ansible-galaxy collection install junipernetworks.junos
```

## Usage

### Using the Python Script

1. Make the script executable:

```bash
chmod +x get_junos_outputs.py
```

2. Run the script:

```bash
./get_junos_outputs.py
```

3. Enter the device hostname/IP, SSH port, and username when prompted

#### Command-line Options

```
Usage: python get_junos_outputs.py [options]
Options:
  -u, --upload-url URL  Specify Nextcloud upload URL
  -k, --insecure        Use insecure mode for HTTPS connections
  -q, --quiet           Be quiet (minimal output)
  -p, --password        Use password from SUPPORT_FILES_PASSWORD environment variable
  -h, --help            Show this help message and exit
```

### Using the Ansible Playbook

1. Ensure your Ansible inventory includes Junos devices in a group called `junos`

2. Run the playbook:

```bash
ansible-playbook get_junos_outputs.yml
```

## Collected Data

Both scripts collect similar data, including:

- Device configuration (XML format)
- Interface information
- ARP/IPv6 neighbor tables
- Routing tables (from various protocols)
- Service definitions

The Python script collects a few additional outputs beyond what the Ansible playbook captures.

## File Upload

The Python script can upload the compressed outputs to a Nextcloud server:

- Default upload URL: `https://supportfiles.firemon.com/s/rGWsNfq2NZ5RFMz`
- You can specify a different URL using the `-u` option
- Use `-k` if SSL certificate verification should be disabled
- Set the `SUPPORT_FILES_PASSWORD` environment variable if authentication is required

## Troubleshooting

- **SSH Issues**: Ensure you have SSH access to the target devices
- **Permission Errors**: The Python script needs write access to `/var/tmp/` (falls back to current directory if unavailable)
- **Upload Failures**: Check network connectivity to the upload server
- **Ansible Errors**: Ensure the Juniper.junos collection is installed and your inventory is correctly configured

---

For more information or assistance, please contact your FireMon Sales Engineer.
