"""
A CLI for ProtonVPN.

Usage:
    protonvpn init
    protonvpn (c | connect) [<servername>] [-p <protocol>]
    protonvpn (c | connect) [-f | --fastest] [-p <protocol>]
    protonvpn (c | connect) [--cc <code>] [-p <protocol>]
    protonvpn (c | connect) [--sc] [-p <protocol>]
    protonvpn (c | connect) [--p2p] [-p <protocol>]
    protonvpn (c | connect) [--tor] [-p <protocol>]
    protonvpn (c | connect) [-r | --random] [-p <protocol>]
    protonvpn (r | reconnect)
    protonvpn (d | disconnect)
    protonvpn (s | status)
    protonvpn configure
    protonvpn refresh
    protonvpn examples
    protonvpn (-h | --help)
    protonvpn (-v | --version)

Options:
    -f, --fastest       Select the fastest ProtonVPN server.
    -r, --random        Select a random ProtonVPN server.
    --cc CODE           Determine the country for fastest connect.
    --sc                Connect to the fastest Secure-Core server.
    --p2p               Connect to the fastest torrent server.
    --tor               Connect to the fastest Tor server.
    -p PROTOCOL         Determine the protocol (UDP or TCP).
    -h, --help          Show this help message.
    -v, --version       Display version.

Commands:
    init                Initialize a ProtonVPN profile.
    c, connect          Connect to a ProtonVPN server.
    r, reconnect        Reconnect to the last server.
    d, disconnect       Disconnect the current session.
    s, status           Show connection status.
    configure           Change ProtonVPN-CLI configuration.
    refresh             Refresh OpenVPN configuration and server data.
    examples            Print some example commands.

Arguments:
    <servername>        Servername (CH#4, CH-US-1, HK5-Tor).
"""
# Standard Libraries
import sys
import os
import textwrap
import configparser
import getpass
import shutil
import time

# External Libraries
from docopt import docopt

# protonvpn-cli Functions
from . import connection
from protonvpn_linux_gui.gui_logger import gui_logger
from .utils import (
    check_root, change_file_owner, pull_server_data, make_ovpn_template,
    check_init, set_config_value, get_config_value, is_valid_ip,
    wait_for_network
)
# Constants
from .constants import (
    CONFIG_DIR, CONFIG_FILE, PASSFILE, USER, VERSION, SPLIT_TUNNEL_FILE
)

def main():
    """Main function"""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nQuitting...")
        sys.exit(1)


def cli():
    """Run user's input command."""

    # Initial log values
    change_file_owner(os.path.join(CONFIG_DIR, "protonvpn-gui.log"))
    gui_logger.debug("###########################")
    gui_logger.debug("### NEW PROCESS STARTED ###")
    gui_logger.debug("###########################")
    gui_logger.debug(sys.argv)
    gui_logger.debug("USER: {0}".format(USER))
    gui_logger.debug("CONFIG_DIR: {0}".format(CONFIG_DIR))

    args = docopt(__doc__, version="ProtonVPN-CLI v{0}".format(VERSION))
    gui_logger.debug("Arguments\n{0}".format(str(args).replace("\n", "")))

    # Parse arguments
    if args.get("init"):
        init_cli()
    elif args.get("c") or args.get("connect"):
        check_root()
        check_init()

        # Wait until a connection to the ProtonVPN API can be made
        # As this is mainly for automatically connecting on boot, it only
        # activates when the environment variable PVPN_WAIT is 1
        # Otherwise it wouldn't connect when a VPN process without
        # internet access exists or the Kill Switch is active
        if int(os.environ.get("PVPN_WAIT", 0)) > 0:
            wait_for_network(int(os.environ["PVPN_WAIT"]))

        protocol = args.get("-p")
        if protocol is not None and protocol.lower().strip() in ["tcp", "udp"]:
            protocol = protocol.lower().strip()

        if args.get("--random"):
            connection.random_c(protocol)
        elif args.get("--fastest"):
            connection.fastest(protocol)
        elif args.get("<servername>"):
            connection.direct(args.get("<servername>"), protocol)
        elif args.get("--cc") is not None:
            connection.country_f(args.get("--cc"), protocol)
        # Features: 1: Secure-Core, 2: Tor, 4: P2P
        elif args.get("--p2p"):
            connection.feature_f(4, protocol)
        elif args.get("--sc"):
            connection.feature_f(1, protocol)
        elif args.get("--tor"):
            connection.feature_f(2, protocol)
        else:
            connection.dialog()
    elif args.get("r") or args.get("reconnect"):
        check_root()
        check_init()
        connection.reconnect()
    elif args.get("d") or args.get("disconnect"):
        check_root()
        check_init()
        connection.disconnect()
    elif args.get("s") or args.get("status"):
        connection.status()
    elif args.get("configure"):
        check_root()
        check_init()
        configure_cli()
    elif args.get("refresh"):
        pull_server_data(force=True)
        make_ovpn_template()
    elif args.get("examples"):
        print_examples()

def init_cli(gui_enabled=False, gui_user_input=False):
    """Initialize the CLI."""

    def init_config_file():
        """"Initialize configuration file."""
        config = configparser.ConfigParser()
        config["USER"] = {
            "username": "None",
            "tier": "None",
            "default_protocol": "None",
            "initialized": "0",
            "dns_leak_protection": "1",
            "custom_dns": "None",
            "check_update_interval": "3",
            "autoconnect": "0"
        }
        config["metadata"] = {
            "last_api_pull": "0",
            "last_update_check": str(int(time.time())),
        }

        with open(CONFIG_FILE, "w") as f:
            config.write(f)
        change_file_owner(CONFIG_FILE)
        gui_logger.debug("pvpn-cli.cfg initialized")

    check_root()

    if not os.path.isdir(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
        gui_logger.debug("Config Directory created")
    change_file_owner(CONFIG_DIR)

    # Warn user about reinitialization
    try:
        if int(get_config_value("USER", "initialized")):
            print("An initialized profile has been found.")
            overwrite = input(
                "Are you sure you want to overwrite that profile? [y/N]: "
            )
            if overwrite.strip().lower() != "y":
                print("Quitting...")
                sys.exit(1)
            # Disconnect, so every setting (Kill Switch, IPv6, ...)
            # will be reverted (See #62)
            connection.disconnect(passed=True)
    except KeyError:
        pass

    term_width = shutil.get_terminal_size()[0]
    print("[ -- PROTONVPN-CLI INIT -- ]\n".center(term_width))

    init_msg = (
        "ProtonVPN uses two different sets of credentials, one for the "
        "website and official apps where the username is most likely your "
        "e-mail, and one for connecting to the VPN servers.\n\n"
        "You can find the OpenVPN credentials at "
        "https://account.protonvpn.com/account.\n\n"
        "--- Please make sure to use the OpenVPN credentials ---\n"
    ).splitlines()

    for line in init_msg:
        print(textwrap.fill(line, width=term_width))

    # Check if GUI was enabled and get the data from GUI
    if gui_enabled == True:
        ovpn_username = gui_user_input['username']
        ovpn_password = gui_user_input['password']
        user_tier = gui_user_input['protonvpn_plan']
        user_protocol = gui_user_input['openvpn_protocol']
    else:
        # Set ProtonVPN Username and Password
        ovpn_username, ovpn_password = set_username_password(write=False)
        # Set the ProtonVPN Plan
        user_tier = set_protonvpn_tier(write=False)
        # Set default Protocol
        user_protocol = set_default_protocol(write=False)

    protonvpn_plans = {1: "Free", 2: "Basic", 3: "Plus", 4: "Visionary"}

    print()
    print(
        "You entered the following information:\n" +
        "Username: {0}\n".format(ovpn_username) +
        "Password: {0}\n".format("*" * len(ovpn_password)) +
        "Tier: {0}\n".format(protonvpn_plans[user_tier]) +
        "Default protocol: {0}".format(user_protocol.upper())
    )
    print()

    if not gui_enabled: 
        user_confirmation = input(
            "Is this information correct? [Y/n]: "
        ).strip().lower()

    if gui_enabled or (user_confirmation == "y" or user_confirmation == ""):
        print("Writing configuration to disk...")
        init_config_file()

        pull_server_data()
        make_ovpn_template()

        # Change user tier to correct value
        if user_tier == 4:
            user_tier = 3
        user_tier -= 1

        set_config_value("USER", "username", ovpn_username)
        set_config_value("USER", "tier", user_tier)
        set_config_value("USER", "default_protocol", user_protocol)
        set_config_value("USER", "dns_leak_protection", 1)
        set_config_value("USER", "custom_dns", None)
        set_config_value("USER", "killswitch", 0)
        set_config_value("USER", "autoconnect", "0")

        with open(PASSFILE, "w") as f:
            f.write("{0}\n{1}".format(ovpn_username, ovpn_password))
            gui_logger.debug("Passfile created")
            os.chmod(PASSFILE, 0o600)

        set_config_value("USER", "initialized", 1)

        print()
        print("Done! Your account has been successfully initialized.")
        gui_logger.debug("Initialization completed.")
        if gui_enabled:
            return True
    else:
        print()
        print("Please restart the initialization process.")
        sys.exit(1)


def print_examples():
    """Print some examples on how to use this program"""

    examples = (
        "protonvpn connect\n"
        "               Display a menu and select server interactively.\n\n"
        "protonvpn c BE-5\n"
        "               Connect to BE#5 with the default protocol.\n\n"
        "protonvpn connect NO#3 -p tcp\n"
        "               Connect to NO#3 with TCP.\n\n"
        "protonvpn c --fastest\n"
        "               Connect to the fastest VPN Server.\n\n"
        "protonvpn connect --cc AU\n"
        "               Connect to the fastest Australian server\n"
        "               with the default protocol.\n\n"
        "protonvpn c --p2p -p tcp\n"
        "               Connect to the fastest torrent server with TCP.\n\n"
        "protonvpn c --sc\n"
        "               Connect to the fastest Secure-Core server with\n"
        "               the default protocol.\n\n"
        "protonvpn reconnect\n"
        "               Reconnect the currently active session or connect\n"
        "               to the last connected server.\n\n"
        "protonvpn disconnect\n"
        "               Disconnect the current session.\n\n"
        "protonvpn s\n"
        "               Print information about the current session."
    )

    print(examples)


def configure_cli():
    """Change single configuration values"""

    while True:
        print(
            "What do you want to change?\n"
            "\n"
            "1) Username and Password\n"
            "2) ProtonVPN Plan\n"
            "3) Default Protocol\n"
            "4) DNS Management\n"
            "5) Kill Switch\n"
            "6) Split Tunneling\n"
            "7) Purge Configuration\n"
        )

        user_choice = input(
            "Please enter your choice or leave empty to quit: "
        )

        user_choice = user_choice.lower().strip()
        if user_choice == "1":
            set_username_password(write=True)
            break
        elif user_choice == "2":
            set_protonvpn_tier(write=True)
            break
        elif user_choice == "3":
            set_default_protocol(write=True)
            break
        elif user_choice == "4":
            set_dns_protection()
            break
        elif user_choice == "5":
            set_killswitch()
            break
        elif user_choice == "6":
            set_split_tunnel()
            break
        # Make sure this is always the last option
        elif user_choice == "7":
            purge_configuration()
            break
        elif user_choice == "":
            print("Quitting configuration.")
            sys.exit(0)
        else:
            print(
                "[!] Invalid choice. Please enter the number of your choice.\n"
            )
            time.sleep(0.5)


def purge_configuration(gui_enabled=False):
    """Purges CLI configuration"""

    if gui_enabled == False:
        user_choice = input(
            "Are you sure you want to purge the configuration? [y/N]: "
        ).lower().strip()

        if not user_choice == "y":
            return

        print("Okay :(")
        time.sleep(0.5)

    connection.disconnect(passed=True)

    if os.path.isdir(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)
        print("Configuration purged.")
        if gui_enabled:
            return "All your configurations were purged. Re-initilize your profile."

def set_username_password(write=False, gui_enabled=False, user_data=False):
    """Set the ProtonVPN Username and Password."""
    
    return_message = 'Something went wrong.'
    print()
    if gui_enabled:
        ovpn_username, ovpn_password1 = user_data
    else:
        ovpn_username = input("Enter your ProtonVPN OpenVPN username: ")

        # Ask for the password and confirmation until both are the same
        while True:
            ovpn_password1 = getpass.getpass(
                "Enter your ProtonVPN OpenVPN password: "
            )
            ovpn_password2 = getpass.getpass(
                "Confirm your ProtonVPN OpenVPN password: "
            )

            if not ovpn_password1 == ovpn_password2:
                print()
                print("[!] The passwords do not match. Please try again.")
            else:
                break

    if write:
        set_config_value("USER", "username", ovpn_username)

        with open(PASSFILE, "w") as f:
            f.write("{0}\n{1}".format(ovpn_username, ovpn_password1))
            gui_logger.debug("Passfile updated")
            os.chmod(PASSFILE, 0o600)

        print("Username and Password has been updated!")
        return_message = "Username and Password has been updated!"

    if gui_enabled:
        return return_message
    return ovpn_username, ovpn_password1


def set_protonvpn_tier(write=False, gui_enabled=False, tier=False):
    """Set the users ProtonVPN Plan."""

    result_message = "Some error occured updating ProtonVPN plan."

    protonvpn_plans = {1: "Free", 2: "Basic", 3: "Plus", 4: "Visionary"}

    print()
    if gui_enabled:
        user_tier = tier
    else:
        print("Please choose your ProtonVPN Plan")

        for plan in protonvpn_plans:
            print("{0}) {1}".format(plan, protonvpn_plans[plan]))

        while True:
            print()
            user_tier = input("Your plan: ")

            try:
                user_tier = int(user_tier)
                # Check if the choice exists in the dictionary
                protonvpn_plans[user_tier]
                break
            except (KeyError, ValueError):
                print()
                print("[!] Invalid choice. Please enter the number of your plan.")

    if write:
        # Set Visionary to plus as it has the same access
        if user_tier == 4:
            user_tier = 3

        # Lower tier by one to match API allocation
        user_tier -= 1

        set_config_value("USER", "tier", str(user_tier))

        print("ProtonVPN Plan has been updated!")
        result_message = "ProtonVPN Plan has been updated!\n\nServer list has been refreshed."

    if gui_enabled:
        return result_message
    return user_tier


def set_default_protocol(write=False, gui_enabled=False, protoc=False):
    """Set the users default protocol"""

    result_message = "Some error occured in updating default OpenVPN protocol..."

    print()
    if gui_enabled:
        user_protocol = protoc
    else:
        print(
            "Choose the default OpenVPN protocol.\n"
            "OpenVPN can act on two different protocols: UDP and TCP.\n"
            "UDP is preferred for speed but might be blocked in some networks.\n"
            "TCP is not as fast but a lot harder to block.\n"
            "Input your preferred protocol. (Default: UDP)\n"
        )

        protonvpn_protocols = {1: "UDP", 2: "TCP"}

        for protocol in protonvpn_protocols:
            print("{0}) {1}".format(protocol, protonvpn_protocols[protocol]))

        while True:
            print()
            user_protocol_choice = input("Your choice: ")

            try:
                if user_protocol_choice == "":
                    user_protocol_choice = 1
                user_protocol_choice = int(user_protocol_choice)
                # Check if the choice exists in the dictionary
                user_protocol = protonvpn_protocols[user_protocol_choice].lower()
                break
            except (KeyError, ValueError):
                print()
                print(
                    "[!] Invalid choice. "
                    "Please enter the number of your preferred protocol."
                )

    if write:
        set_config_value("USER", "default_protocol", user_protocol)
        print("Default protocol has been updated.")
        result_message = "Default OpenVPN protocol has been updated."

    if gui_enabled:
        return result_message

    return user_protocol


def set_dns_protection(gui_enabled=False, dns_settings=False):
    """Enable or disable DNS Leak Protection and custom DNS"""

    result_message = 'Some error occured during DNS configuration.'

    if gui_enabled == True:
        dns_leak_protection, custom_dns = dns_settings
    else:
        while True:
            print()
            print(
                "DNS Leak Protection makes sure that you always use "
                "ProtonVPN's DNS servers.\n"
                "For security reasons this option is recommended.\n"
                "\n"
                "1) Enable DNS Leak Protection (recommended)\n"
                "2) Configure Custom DNS Servers\n"
                "3) Disable DNS Management"
            )
            print()
            user_choice = input(
                    "Please enter your choice or leave empty to quit: "
            )
            user_choice = user_choice.lower().strip()
            if user_choice == "1":
                dns_leak_protection = 1
                custom_dns = None
                break
            elif user_choice == "2":
                dns_leak_protection = 0
                custom_dns = input(
                    "Please enter your custom DNS servers (space separated): "
                )
                custom_dns = custom_dns.strip().split()

                # Check DNS Servers for validity
                if len(custom_dns) > 3:
                    print("[!] Don't enter more than 3 DNS Servers")
                    return

                for dns in custom_dns:
                    if not is_valid_ip(dns):
                        print("[!] {0} is invalid. Please try again.".format(dns))
                        return
                custom_dns = " ".join(dns for dns in custom_dns)
                break
            elif user_choice == "3":
                dns_leak_protection = 0
                custom_dns = None
                break
            elif user_choice == "":
                print("Quitting configuration.")
                sys.exit(0)
            else:
                print(
                    "[!] Invalid choice. Please enter the number of your choice.\n"
                )
                time.sleep(0.5)

    set_config_value("USER", "dns_leak_protection", dns_leak_protection)
    set_config_value("USER", "custom_dns", custom_dns)
    print("DNS Management updated.")

    result_message = "DNS settings updated."

    if gui_enabled:
        return result_message

def set_killswitch(gui_enabled=True, user_choice=False):
    """Enable or disable the Kill Switch."""
    
    # result_message = "Error occured during update of killswitch configurations."
    result_message = ""

    if gui_enabled == True:
        killswitch = user_choice
    else:
        while True:
            print()
            print(
                "The Kill Switch will block all network traffic\n"
                "if the VPN connection drops unexpectedly.\n"
                "\n"
                "Please note that the Kill Switch assumes only one network interface being active.\n" # noqa
                "\n"
                "1) Enable Kill Switch (Block access to/from LAN)\n"
                "2) Enable Kill Switch (Allow access to/from LAN)\n"
                "3) Disable Kill Switch"
            )
            print()
            user_choice = input(
                    "Please enter your choice or leave empty to quit: "
            )
            user_choice = user_choice.lower().strip()
            # 1) Enable Kill Switch (Block access to/from LAN)
            if user_choice == "1":
                killswitch = 1
                break
            # 2) Enable Kill Switch (Allow access to/from LAN)
            elif user_choice == "2":
                killswitch = 2
                break
            # 3) Disable Kill Switch
            elif user_choice == "3":
                killswitch = 0
                break
            elif user_choice == "":
                print("Quitting configuration.")
                sys.exit(0)
            else:
                print(
                    "[!] Invalid choice. Please enter the number of your choice.\n"
                )
                time.sleep(0.5)

    if killswitch and int(get_config_value("USER", "split_tunnel")):
        set_config_value("USER", "split_tunnel", 0)
        print()
        print(
            "[!] Kill Switch can't be used with Split Tunneling.\n" +
            "[!] Split Tunneling has been disabled."
        )
        time.sleep(1)
        result_message = "Kill Switch can't be used with Split Tunneling.\nSplit Tunneling has been disabled."

    set_config_value("USER", "killswitch", killswitch)
    print()
    print("Kill Switch configuration updated.")
    result_message = result_message + "Kill Switch configuration updated."
    if gui_enabled:
        return result_message

def set_split_tunnel(gui_enabled=False, user_data=False):
    """Enable or disable split tunneling"""

    result_message = ''

    print()

    if gui_enabled == True:
        if len(user_data) == 0:
            set_config_value("USER", "split_tunnel", 0)
            if os.path.isfile(SPLIT_TUNNEL_FILE):
                os.remove(SPLIT_TUNNEL_FILE)
                result_message = "Split tunneling disabled.\n\n"
        else:
            if int(get_config_value("USER", "killswitch")):
                set_config_value("USER", "killswitch", 0)
                print()
                print(
                    "[!] Split Tunneling can't be used with Kill Switch.\n" +
                    "[!] Kill Switch has been disabled.\n"
                )
                result_message = "Split Tunneling can't be used with Kill Switch.\nKill Switch has been disabled.\n\n"
                time.sleep(1)

            set_config_value("USER", "split_tunnel", 1)

            with open(SPLIT_TUNNEL_FILE, "w") as f:
                for ip in user_data:
                    f.write("\n{0}".format(ip))

            if os.path.isfile(SPLIT_TUNNEL_FILE):
                change_file_owner(SPLIT_TUNNEL_FILE)
            else:
                # If no no config file exists,
                # split tunneling should be disabled again
                gui_logger.debug("No split tunneling file existing.")
                set_config_value("USER", "split_tunnel", 0)
                result_message = result_message + "No split tunneling file, split tunneling will be disabled.\n\n"
    else:
        user_choice = input("Enable split tunneling? [y/N]: ")

        if user_choice.strip().lower() == "y":
            if int(get_config_value("USER", "killswitch")):
                set_config_value("USER", "killswitch", 0)
                print()
                print(
                    "[!] Split Tunneling can't be used with Kill Switch.\n" +
                    "[!] Kill Switch has been disabled.\n"
                )
                time.sleep(1)

            set_config_value("USER", "split_tunnel", 1)


            while True:
                ip = input(
                    "Please enter an IP or CIDR to exclude from VPN.\n"
                    "Or leave empty to stop: "
                ).strip()

                if ip == "":
                    break

                if not is_valid_ip(ip):
                    print("[!] Invalid IP")
                    print()
                    continue

                with open(SPLIT_TUNNEL_FILE, "a") as f:
                    f.write("\n{0}".format(ip))

            if os.path.isfile(SPLIT_TUNNEL_FILE):
                change_file_owner(SPLIT_TUNNEL_FILE)
            else:
                # If no no config file exists,
                # split tunneling should be disabled again
                gui_logger.debug("No split tunneling file existing.")
                set_config_value("USER", "split_tunnel", 0)

        else:
            set_config_value("USER", "split_tunnel", 0)

            if os.path.isfile(SPLIT_TUNNEL_FILE):
                clear_config = input("Remove split tunnel configuration? [y/N]: ")

                if clear_config.strip().lower() == "y":
                    os.remove(SPLIT_TUNNEL_FILE)

    print()
    print("Split tunneling configuration updated.")
    result_message = result_message + "Split tunneling configuration updated."
    make_ovpn_template()

    if gui_enabled:
        return result_message
