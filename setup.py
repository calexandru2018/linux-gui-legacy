"""setup.py: setuptools control."""
import re
import os
from setuptools import setup

from app.constants import VERSION, APP_NAME, GITHUB_URL

try:
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
        long_descr = '\n' + f.read()
except FileNotFoundError:
    long_descr = """
    ProtonVPN Application for Linux based OSs.

    For further information and a usage guide, please view the project page:

    {}
    """.format(GITHUB_URL)

setup(
    name=APP_NAME,
    packages=[
        "app",
        "app.presenters",
        "app.services",
        "app.views",
        "app.resources",
        "app.resources.img.flags",
        "app.resources.img.flags.small",
        "app.resources.img.flags.large",
        "app.resources.img.logo",
        "app.resources.img.utils",
        "app.resources.styles",
        "app.resources.ui",
        ],
    entry_points={
            "console_scripts": [
                "protonvpn-app = app.main:init",
                "protonvpn-tray = app.indicator:ProtonVPNIndicator",
            ]
        },
    include_package_data=True,
    version=VERSION,
    description="ProtonVPN Application for Linux based OSs",
    long_description=long_descr,
    long_description_content_type="text/markdown",
    author="Proton Technologies AG",
    author_email="contact@protonvpn.com",
    license="GPLv3",
    url=GITHUB_URL,
    install_requires=[
        "protonvpn-cli>=2.2.2",
        "requests>=2.23.0",
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
