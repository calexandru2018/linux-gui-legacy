try:
    from protonvpn_cli.constants import VERSION as cli_version
except:
    cli_version = "Not installed"
VERSION = "1.8.1"
GITHUB_URL_RELEASE = "https://github.com/calexandru2018/protonvpn-linux-gui/releases/latest"
SERVICE_NAME = "custompvpn-autoconnect" 
PATH_AUTOCONNECT_SERVICE = "/etc/systemd/system/{}.service".format(SERVICE_NAME)
TEMPLATE ="""
[Unit]
Description=Custom ProtonVPN-CLI auto-connect
Wants=network-online.target

[Service]
Type=forking
ExecStart=PATH
ExecStop=STOP
Environment=PVPN_WAIT=300
Environment=PVPN_DEBUG=1
Environment=SUDO_USER=user

[Install]
WantedBy=multi-user.target
"""
HELP_TEXT = """
<b>How is this GUI related to protonvpn-cli-ng ?</b>
This GUI works on top of the original cli v{cli_version}. The CLI in this case acts as a dependency for the GUI. 
All connections are made by invoking the CLI in the background, though all user input is managed by the GUI. 

<b>I am having connectivity issues and I don't know what to do!</b>
I have a developed a Diagnosis tool that should be helpful in the most cases. You can find the tool under About -> Diagnose.
This tool will analyse the current configurations and will attempt to help you solve the problem by giving you a brief summary of the root cause.
It will also provide you some code snippets that you can easily copy/paste into a terminal, even when without internet. If the same issue persists after multiple attempts (to resolve it), try to restart your computer.

<b>I am still experiecing problems, to whom should I create ticket/issue ?</b>
If you are experiencing any issues, then you should first contact me by opening an issue or any other method. 
If, after a closer inspection, I notice that the problem originates from within the CLI, then I would then reccomend you to contact protonvpn support instead.

<b>I would like to suggest a feature, where could I do that ?</b>
If you would like me to implement a new feature or want to give suggestion for one, then you can do it by creating a github issue, select the type of issue, in this case a Feature request.
Then fill in the template and concisely explain what you would like to see implemented, with as much detail as possible.

<b>I woule like to donate, do you have any e-wallets ?</b>
First of all, thank you! Any help is very much appreciated and welcome, all this is developed during my free time. If you would like to donate, at the moment I have a liberapay account: https://liberapay.com/calexandru2018
""".format(cli_version=cli_version)