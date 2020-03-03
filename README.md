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

## Create .desktop file

To create at <i>desktop</i> launcher with a .desktop file, follow the instrucitons below.

1. Find the path to the package with `pip3 show protonvpn-linux-gui-calexandru2018`

   You should get something like `Location: /usr/local/lib/<YOUR_PYTHON_VERSION>/dist-packages` , this is where your Python packages reside. **Note:** Based on your distro, your `Location` path may not look exactly like this one, so make sure to use your own and `Location` path.

2. Based on previous information, the path to your icon should be `<PATH_DISPLAYED_IN_STEP_1>/protonvpn_linux_gui/resources/protonvpn_logo.png`

3. Create a `protonvpn-gui.desktop` file in `.local/share/applications/`, and paste in the following code. Remember to change the **`Icon`** path to your own path.

    ```
    [Desktop Entry]
    Name=ProtonVPN GUI
    GenericName=Unofficial ProtonVPN GUI for Linux
    Exec=sudo protonvpn-gui
    Icon=<YOUR_ICON_PATH>
    Type=Application
    Terminal=False
    Categories=Utility;GUI;Network;VPN>
    ```
### Further enhancement
If you would like to launch the GUI without having to type in your sudo password everytime, then you could add the bin to `visudo`. This is extremly useful when you have a .desktop file, and all you want to do is click the launcher to have the GUI pop-up without being prompted for sudo password.

1. First you will need the path to the GUI. This can be found by typing `which protonvpn-gui`. You should get something like this: `/usr/bin/protonvpn-gui`. Save it since you will need it later. **Note:** As previously mentioned, the path may look different for you, based on your distro.
2. Identify your username by typing `whoami`. Save it (or memorize it). 
3. In another terminal, type in `sudo visudo`, and a window should pop-up, scroll to the very bottom of it.
4. Once you are at the botton, type: `<YOUR_USERNAME_FROM_STEP2> ALL = (root) NOPASSWD: <YOUR_PATH_FROM_STEP1>`
5. Exit and save! Have fun :)

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
 
