<h1 align="center">ProtonVPN Linux GUI</h1>
<p align="center">
  <img src="https://i.imgur.com/rjMuf7p.png" alt="Logo"></img>
</p>

<p align="center">
    <a href="https://pepy.tech/project/protonvpn-linux-gui-calexandru2018"><img alt="Downloads" src="https://pepy.tech/badge/protonvpn-linux-gui-calexandru2018"></a>   
    <a href="https://pepy.tech/project/protonvpn-linux-gui-calexandru2018/week"><img alt="Downloads per Week" src="https://pepy.tech/badge/protonvpn-linux-gui-calexandru2018/week"></a>
</p>

<h3 align="center">An <b>unofficial</b> Linux GUI for ProtonVPN, written in Python. Layout designed in Glade.</h3>

Protonvpn-linux-gui is based on <a href="https://github.com/ProtonVPN/protonvpn-cli-ng"><b>protonvpn-cli-ng</b></a> code. This was achieved by slightly modifying ProtonVPN's original Python code and adding a new layer on top of it for the GUI.

### Installing Dependencies

**Dependencies:**

- openvpn
- pip for python3 (pip3)
- python3.5+
- setuptools for python3 (python3-setuptools)
- PyGObject

If you have <b>NOT</b> previously installed <b><a href="https://github.com/ProtonVPN/protonvpn-cli-ng">protonvpn-cli-ng</b></a>, then install the following dependencies, based on your distribution:

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


## Installing ProtonVPN Linux GUI

You can either install via <b>PIP</b> or by cloning the repository.

*Note: Make sure to run pip with sudo*

`sudo pip3 install protonvpn-linux-gui-calexandru2018`

### To update to a new version

`sudo pip3 install protonvpn-linux-gui-calexandru2018 --upgrade`

## Manual Installation

1. Clone this repository

    `git clone https://github.com/calexandru2018/protonvpn-linux-gui`

2. Step into the directory

   `cd protonvpn-linux-gui`

3. Install

    `sudo python3 setup.py install`

### How to use

 `sudo protonvpn-gui`

After connecting to a server, if you want to close the GUI and the terminal, then do not <b>CTRL+C!</b> This will cause the process to be interrupted, instead just close the terminal by pressing on the <b>X</b> in the terminal and the process will continue to work in the background.

### Not yet implemented:

- ~~Split Tunneling~~
- ~~Kill Switch~~
- ~~Filtering servers~~
- Start on Boot (only for systemd OS's)

## GUI Layout
<p align="center">
  <img src="https://i.imgur.com/Dxe9vRH.png" alt="Logo"></img>
</p>

<p align="center">
  <img src="https://i.imgur.com/ToooLUV.png" alt="Logo"></img>
</p>

<p align="center">
  <img src="https://i.imgur.com/nVU65pO.png" alt="Logo"></img>
</p> 

<p align="center">
  <img src="https://i.imgur.com/UdKoMGC.png" alt="Logo"></img>
</p>
 
