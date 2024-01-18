
%define version %(awk '{print $3;}' sarracenia/_version.py | sed 's/\"//g') 

Name:           metpx-sr3
Version:        %{version}
Release:        0%{?dist}
Summary:        Subscribe, Acquire, and Re-Advertise (managed multiple hop file transfers)
License:        GPL-2.0-only
URL:            https://metpx.github.io/sarracenia
Source:         %{url}/archive/v%{version}/metpx-sr3-%{version}.tar.gz / %{pypi_source python-metpx-sr3}

BuildArch:      noarch / BuildRequires:  gcc
BuildRequires:  python3-devel
BuildRequires: systemd-rpm-macros


Requires: python3-appdirs, python3-humanfriendly, python3-humanize, python3-jsonpickle, python3-paramiko, python3-psutil

%global _description %{expand:
MetPX-sr3 (Sarracenia v3) is a data duplication or distribution pump that leverage
existing standard technologies (web servers and message queueing protocol brokers) 
to achieve real-time message delivery and end-to-end transparency in file transfers.
Data sources establish a directory structure which is carried through any number of
intervening pumps until they arrive at a client. }

%description %_description

Summary:        %{summary}

%prep
%autosetup -p1 -n metpx-sr3-%{version}

%generate_buildrequires
%pyproject_buildrequires  requirements.txt


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files sarracenia

mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_userunitdir}
install -m 644 debian/metpx-sr3.service %{buildroot}%{_unitdir}/
install -m 644 tools/metpx-sr3_user.service %{buildroot}%{_userunitdir}/metpx-sr3.service


%files -n metpx-sr3 -f %{pyproject_files}
%{_bindir}/sr3
%{_bindir}/sr3_post
%{_bindir}/sr3_rotateLogsManually
%{_bindir}/sr3_tailf
%{_unitdir}/metpx-sr3.service
%{_userunitdir}/metpx-sr3.service

%changelog
%autochangelog

