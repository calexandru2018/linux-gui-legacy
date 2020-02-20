"""setup.py: setuptools control."""


import re
from setuptools import setup

from protonvpn_linux_gui.constants import VERSION


long_descr = """
The Unofficial Linux GUI for ProtonVPN.

For further information and a usage guide, please view the project page:

https://github.com/calexandru2018/protonvpn-linux-gui
"""

setup(
    name="protonvpn-linux-gui-calexandru2018",
    packages=[
        "protonvpn_linux_gui",
        "protonvpn_linux_gui.resources",
        "protonvpn_linux_gui.resources.flags",
        "custom_pvpn_cli_ng",
        "custom_pvpn_cli_ng.protonvpn_cli"
        ],
    entry_points={
            "console_scripts": [
                "protonvpn-gui = protonvpn_linux_gui.gui:initialize_gui",
                "custom-pvpn-cli = custom_pvpn_cli_ng.protonvpn_cli.cli:main"
            ]
        },
    include_package_data=True,
    version=VERSION,
    description="Unofficial Linux GUI client for ProtonVPN",
    long_description=long_descr,
    author="calexandru2018",
    license="GPLv3",
    url="https://github.com/calexandru2018/protonvpn-linux-gui",
    install_requires=[
        "requests",
        "docopt",
        "pythondialog",
    ],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
