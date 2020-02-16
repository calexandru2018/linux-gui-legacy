<h1 align="center">Unofficial ProtonVPN Linux GUI</h1>
<p align="center">
  <!-- <img src="https://i.imgur.com/tDrwkX5l.png" alt="Logo"></img> -->
</p>

<h3 align="center">An <b>UNOFFICIAL</b> Linux GUI for ProtonVPN. Written in Python.</h3>

Protonvpn-linux-gui is based on <a href="https://github.com/ProtonVPN/protonvpn-cli-ng"><b>protonvpn-cli-ng</b></a> code. This was achieved by slightly modifying ProtonVPN's original Python code and adding a new layer on top of it for the GUI.

### Installing Dependencies

**Dependencies:**

- openvpn
- pip for python3 (pip3)
- python3.5+
- setuptools for python3 (python3-setuptools)
- PyGObject

If you have <b>NOT</b> previously installed ProtonVPN-CLI, then install the following dependencies, based on your distribution:

| **Distro**                              | **Command**                                                                                                                           |
|:----------------------------------------|:---------------------------------------------------------------------------------------------------------                             |
|Fedora/CentOS/RHEL                       | `sudo dnf install -y openvpn dialog python3-pip python3-setuptools python3-gobject gtk3`                                              |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y openvpn dialog python3-pip python3-setuptools python3-gi python3-gi-cairo gir1.2-gtk-3.0`                        |
|OpenSUSE/SLES                            | `sudo zypper in -y openvpn dialog python3-pip python3-setuptools python3-gobject python3-gobject-Gdk typelib-1_0-Gtk-3_0 libgtk-3-0`  |
|Arch Linux/Manjaro                       | `sudo pacman -S openvpn dialog python-pip python-setuptools python-gobject gtk3`       |



If you have already installed <a href="https://github.com/ProtonVPN/protonvpn-cli-ng"><b>protonvpn-cli-ng</b></a> and used the CLI, then you will only need to install the following dependencies for the GUI:

| **Distro**                              | **Command**                                                                               |
|:----------------------------------------|:--------------------------------------------------------------------                      |
|Fedora/CentOS/RHEL                       | `sudo dnf install -y sudo dnf install python3-gobject gtk3`                               |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0`                          |
|OpenSUSE/SLES                            | `sudo zypper install python3-gobject python3-gobject-Gdk typelib-1_0-Gtk-3_0 libgtk-3-0`  |
|Arch Linux/Manjaro                       | `sudo pacman -S python-gobject gtk3`                                                      |


## Manual Installation from source

*Note: Make sure to run pip with sudo, so it installs globally and recognizes the command with sudo*

1. Clone this repository

    `git clone https://github.com/protonvpn/protonvpn-cli-ng`

2. Step into the directory

   `cd protonvpn-cli-ng`

3. Install

    `pip3 install -e .`


### How to use

 `sudo protonvpn-gui`