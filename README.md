# Junos Output Retrieval Tools

This repository contains two tools for retrieving configuration and command outputs from a Junos device:

1. **Python Script (`get_junos_outputs.py`)**  
   Uses Paramiko to SSH into a device, execute commands, and save the output to local files.

2. **Ansible Playbook (`get_junos_outputs.yml`)**  
   Uses Ansible (with the Junos collection) to connect via SSH (`network_cli`), run commands on the device, and save the output to local files.

Both tools will save the output files (e.g., `config_xml`, `interfaces_xml`, etc.) on the workstation where the script or playbook is executed.

---

## Python Script: `get_junos_outputs.py`

### Prerequisites

- **Python 3** installed.
- **Paramiko** library installed.

### Setting Up a Virtual Environment (Recommended)

1. **Create a Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```
   *(On Windows, you can use `python -m venv venv`.)*

2. **Activate the Virtual Environment:**
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install paramiko
   ```

### Configuration

- Open `get_junos_outputs.py` in your favorite text editor.
- Update the `device` dictionary with your device's connection details:
  - `hostname`
  - `port`
  - `username`
  - `password`

### Running the Script

1. **Ensure the virtual environment is activated.**
2. **Run the script:**
   ```bash
   python get_junos_outputs.py
   ```
3. The script will:
   - Connect to the device via SSH.
   - Execute each command.
   - Save each command's output to a file with a name matching the corresponding key (e.g., `config_xml`, `interfaces_xml`, etc.) on your local machine.

---

## Ansible Playbook: `get_junos_outputs.yml`

### Prerequisites

- **Ansible** installed.
- **Juniper Networks Junos Ansible Collection** installed.  
  Install the collection using:
  ```bash
  ansible-galaxy collection install junipernetworks.junos
  ```
- A proper inventory file set up with device details.

### Inventory Setup

Create an inventory file (e.g., `hosts.ini`) with your device information. For example:

```ini
[junos]
your_device_ip_or_hostname ansible_network_os=junos ansible_user=your_username ansible_password=your_password
```

### Running the Playbook

1. **Run the playbook with your inventory file:**
   ```bash
   ansible-playbook -i hosts.ini get_junos_outputs.yml
   ```
2. The playbook will:
   - Connect to the Junos device using the `network_cli` connection.
   - Execute each command defined in the playbook.
   - Save the command outputs to files (e.g., `config_xml`, `interfaces_xml`, etc.) on your local workstation in the directory from which you run the playbook.

---

## Additional Notes

- **Output Files:** Both tools save the command outputs locally on the workstation running the tool.
- **Customization:** Feel free to modify command strings, filenames, or connection details as needed.
- **Documentation:**
  - [Paramiko Documentation](https://docs.paramiko.org/)
  - [Ansible Documentation](https://docs.ansible.com/)
  - [Juniper Networks Junos Ansible Collection](https://galaxy.ansible.com/junipernetworks/junos)
