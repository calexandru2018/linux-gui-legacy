%define name		protonvpn-gui
%define Summary         Gtk3 GUI for ProtonVPN.
%define Summary_hu      Gtk3 grafikus intgerfész ProtonVPN-hez
%define sourcetype      tar.xz
%define version         2.1.1

Name: 		%name
Summary: 	%Summary
Summary(hu): 	%Summary_hu
Version:	%version
Release: 	%mkrel 1
License: 	GPL2
Distribution:	blackPanther OS
Vendor:    	blackPanther Europe
Packager:  	Charles K Barcza <kbarcza@blackpanther.hu>
URL:		https://github.com/ProtonVPN/linux-gui
Group: 		System/Network
Source0:	%name-%version.%sourcetype
Buildroot:	%_tmppath/%name-%version-%release-root
BuildArch:	noarch
BuildRequires:	python3-setuptools
BuildRequires:	python3
Requires: 	python3-requests >= 2.23.0
Requires: 	protonvpn-cli >= 2.2.2
Requires: 	python3-configparser >= 4.0.2
Requires: 	python3-gobject3
Requires: 	%{_lib}appindicator3_1 libnotify
Provides:	protonvpn-linux-gui = %version

%description
Python3-Gtk3 graphical user interface for ProtonVPN service.


%files
%defattr(-,root,root)
%_bindir/%name
%_bindir/*-tray
%python3_sitelib/linux_gui
%python3_sitelib/protonvpn_gui-2.1.1-py3.7.egg-info
%_datadir/applications/*.desktop
%_iconsdir/*.png
%_iconsdir/*/*.png

%prep
%setup -q -n linux-gui

%build
%py3_build

%install
%py3_install

%define  nameicon linux_gui/resources/img/logo/protonvpn_logo.png
mkdir -p -m755 %{buildroot}{%_liconsdir,%_iconsdir,%_miconsdir}
convert -scale 48x48 %{nameicon} %{buildroot}/%{_liconsdir}/%{name}.png
convert -scale 32x32 %{nameicon} %{buildroot}/%{_iconsdir}/%{name}.png
convert -scale 16x16 %{nameicon} %{buildroot}/%{_miconsdir}/%{name}.png


rm -rf %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/blackPanther-%{name}.desktop <<EOF
[Desktop Entry]
Name=ProtonVPN Client
Name[hu]=ProtonVPN kliens
Comment=%Summary
Comment[hu]=%Summary_hu
GenericName=%Summary.
GenericName[hu]=%Summary_hu.
Exec=%{name}
Icon=%{name}
Terminal=false
Type=Application
StartupNotify=true
Categories=Network;
Keywords=ProtonVPN;VPN;protonvpn-gui;
Actions=tray

[Desktop Action tray]
Name=ProtonVPN-Tray
Name[hu]=ProtonVPN-tálcaikon
Icon=%name
Exec=protonvpn-tray
EOF


%clean
rm -rf %buildroot


%changelog
* Fri Jul 31 2020 Charles K. Barcza <info@blackpanther.hu> 2.1.1-1bP
- build package for blackPanther OS v17-20.1
-------------------------------------------------------------------------
