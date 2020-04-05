<h1 align="center">ProtonVPN Linux GUI</h1>
<p align="center">
  <img src="https://i.imgur.com/rjMuf7p.png" alt="Logo"></img>
</p>

<p align="center">
  <a href="https://github.com/calexandru2018/protonvpn-linux-gui/releases/latest">
      <img alt="Build Status" src="https://img.shields.io/github/release/calexandru2018/protonvpn-linux-gui.svg?style=flat" />
  </a>
  <a href="https://pepy.tech/project/protonvpn-linux-gui-calexandru2018">
    <img alt="Downloads" src="https://pepy.tech/badge/protonvpn-linux-gui-calexandru2018">
  </a>   
    <a href="https://pepy.tech/project/protonvpn-linux-gui-calexandru2018/week">
      <img alt="Downloads per Week" src="https://pepy.tech/badge/protonvpn-linux-gui-calexandru2018/week">
    </a>
</p>
<p align="center">
  <a href="https://liberapay.com/calexandru2018/donate">
      <img src="http://img.shields.io/liberapay/goal/calexandru2018.svg?logo=liberapay">
  </a>
</p>
<p align="center">
  <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/protonvpn-linux-gui-calexandru2018?color=Yellow&label=python&logo=Python&logoColor=Yellow">
</p>
<p align="center">
    <a href="https://actions-badge.atrox.dev/calexandru2018/protonvpn-linux-gui/goto?ref=master">
        <img alt="GitHub Workflow Status (Master)" src="https://img.shields.io/github/workflow/status/calexandru2018/protonvpn-linux-gui/Master branch Flake8/master?label=Master%20branch%20Flake8&logo=Github">
    </a>
    <a href="https://github.com/calexandru2018/protonvpn-linux-gui/blob/master/LICENSE">
        <img src="https://img.shields.io/github/license/calexandru2018/protonvpn-linux-gui">
    </a>
    <a href="https://actions-badge.atrox.dev/calexandru2018/protonvpn-linux-gui/goto?ref=testing">
        <img alt="GitHub Workflow Status (Testing)" src="https://img.shields.io/github/workflow/status/calexandru2018/protonvpn-linux-gui/Testing branch Flake8/testing?label=Testing%20branch%20Flake8&logo=Github">
    </a> 
</p>


<h3 align="center">An <b>unofficial</b> Linux GUI for ProtonVPN, written in Python. Layout designed in Glade.</h3>

Protonvpn-linux-gui works on top of <a href="https://github.com/ProtonVPN/protonvpn-cli-ng"><b>protonvpn-cli-ng</b></a>, making it a dependency. All local configurations are managed by the GUI (such as updating protocol, split tunneling, manage killswitch) while the connections are managed by the CLI. This way, you will be able to use the latest version of the CLI, while also being able to use the GUI.

### Installing Dependencies

**Dependencies:**

- requests
- python3.5+
- pip for python3 (pip3)
- setuptools for python3 (python3-setuptools)
- <a href="https://github.com/ProtonVPN/protonvpn-cli-ng"><b>protonvpn-cli-ng</b></a>


If you have already installed <a href="https://github.com/ProtonVPN/protonvpn-cli-ng"><b>protonvpn-cli-ng</b></a>, then you will only need to <b>install the following packages for the GUI</b>:

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Fedora/CentOS/RHEL                       | `sudo dnf install -y python3-gobject gtk3`                                                                      |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0`                                                |
|OpenSUSE/SLES                            | `sudo zypper install python3-gobject python3-gobject-Gdk typelib-1_0-Gtk-3_0 libgtk-3-0`                        |
|Arch Linux/Manjaro                       | `sudo pacman -S python-gobject gtk3`                                                                            |

If you would also like to use <b>systray/appindicator then you will need to install the following packages</b>:

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Fedora/CentOS/RHEL                       | `sudo dnf install -y libappindicator-gtk3`                                                                      |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y gir1.2-appindicator3`                                                                       |
|OpenSUSE/SLES                            | `sudo zypper install libappindicator-gtk3`                                                                      |
|Arch Linux/Manjaro                       | `sudo pacman -S libappindicator-gtk3`                                                                           |

**NOTE:**
Gnome users will to install and additional extension for this to work: <a href="https://extensions.gnome.org/extension/615/appindicator-support/"> KStatusNotifierItem/AppIndicator Support</a>

### Known issue:
There is a known issue when user attempts to start the systray/appindicator. This might throw an error that is simillar to this one: `(<app-name>:<pid>) LIBDBUSMENU-GLIB-WARNING **: Unable to get session bus: Failed to execute child process "dbus-launch" (No such file or directory)` if a user does not have a specific package installed. If you are unable to use the systray/appindicator and have a simillar error then a solution is provided below.

**Solution:**
Install `dbus-x11` package for your distribution, more information can be found on this <a href="https://askubuntu.com/questions/1005623/libdbusmenu-glib-warning-unable-to-get-session-bus-failed-to-execute-child">stackoverflow</a> post.

## Installing ProtonVPN Linux GUI

### Distribution based
- Fedora/CentOS/RHEL: To-do
- Ubuntu derivatives: To-do
- OpenSUSE/SLES: To-do
- Arch Linux/Manjaro: <a href="https://aur.archlinux.org/packages/protonvpn-linux-gui/" target="_blank">Available at AUR</a>


### PIP based

*Note: Make sure to run pip with sudo*

`sudo pip3 install protonvpn-linux-gui-calexandru2018`

#### To update to a new version

`sudo pip3 install protonvpn-linux-gui-calexandru2018 --upgrade`

### Manual Installation

1. Clone this repository

    `git clone https://github.com/calexandru2018/protonvpn-linux-gui`

2. Step into the directory

   `cd protonvpn-linux-gui`

3. Install

    `sudo python3 setup.py install`

## How to use

### ProtonVPN GUI

 `sudo protonvpn-gui`

### ProtonVPN Tray

 `protonvpn-tray`

## Virtual environment

If you would like to run the the GUI within a virtual environment (for either development purpose or other), then you can easily do that with the help of <a href="https://pipenv.readthedocs.io/en/latest/">pipenv</a>. After cloning the repo and `cd` into the directory, start by installing the virtual environment with the help of `pipenv install`. This will install and configure the environment and also install all dependencies in the `Pipfile` file. After that the configuration and installation process is completed, you can enter the virtual environment with `pipenv shell`. To install the GUI in your virtual environment you can type the following in the terminal `sudo pip install -e .` and after that, you can start the GUI as you normally would with `sudo protonvpn-gui`.

## Create .desktop file

### ProtonVPN GUI
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
    Categories=Utility;GUI;Network;VPN
    ```

### ProtonVPN Tray
To create at <i>tray icon</i> launcher with a .desktop file, follow the instrucitons below.

1. Find the path to the package with `pip3 show protonvpn-linux-gui-calexandru2018`

   You should get something like `Location: /usr/local/lib/<YOUR_PYTHON_VERSION>/dist-packages` , this is where your Python packages reside. **Note:** Based on your distro, your `Location` path may not look exactly like this one, so make sure to use your own and `Location` path.

2. Based on previous information, the path to your icon should be `<PATH_DISPLAYED_IN_STEP_1>/protonvpn_linux_gui/resources/protonvpn_logo.png`

3. Create a `protonvpn-tray.desktop` file in `.local/share/applications/`, and paste in the following code. Remember to change the **`Icon`** path to your own path.

    ```
    [Desktop Entry]
    Name=ProtonVPN GUI Tray
    GenericName=Unofficial ProtonVPN GUI Tray for Linux
    Exec=protonvpn-tray
    Icon=<YOUR_ICON_PATH>
    Type=Application
    Terminal=False
    Categories=Utility;GUI;Network;VPN
    ```

## Further enhancement
If you would like to launch the GUI without having to type in your sudo password everytime, then you could add the bin to `visudo`. This is extremly useful when you have a .desktop file, and all you want to do is click the launcher to have the GUI pop-up without being prompted for sudo password.

1. First you will need the path to the GUI. This can be found by typing `which protonvpn-gui`. You should get something like this: `/usr/bin/protonvpn-gui`. Save it since you will need it later. **Note:** As previously mentioned, the path may look different for you, based on your distro.
2. Identify your username by typing `whoami`. Save it (or memorize it). 
3. In another terminal, type in `sudo visudo`, and a window should pop-up, scroll to the very bottom of it.
4. Once you are at the botton, type: `<YOUR_USERNAME_FROM_STEP2> ALL = (root) NOPASSWD: <YOUR_PATH_FROM_STEP1>`
5. Exit and save! Have fun :)

## Not yet implemented:

- ~~Split Tunneling~~
- ~~Kill Switch~~
- ~~Filtering servers~~
- ~~Start on Boot~~ (only for systemd/systemctl based OS's)
- ~~Systray/AppIndicator~~

## GUI Layout
<p align="center">
  <img src="https://i.imgur.com/VnOMaeg.png" alt="Logo"></img>
</p>

<p align="center">
  <img src="https://i.imgur.com/BbwBiu6.png" alt="Logo"></img>
</p>

<p align="center">
  <img src="https://i.imgur.com/103IBOc.png" alt="Logo"></img>
</p>

<p align="center">
  <img src="https://i.imgur.com/zq93OdU.png" alt="Logo"></img>
</p> 

 <p align="center">
  <img src="https://i.imgur.com/bhK8qqB.png" alt="Logo"></img>
</p> 
 
