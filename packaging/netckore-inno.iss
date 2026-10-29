# -*- mode: python ; coding: utf-8 -*-
# Inno Setup script for Netckore (Windows installer).
# Build locally with ISCC.exe /DAppVersion=0.1.0 ...
# Not published to GitHub Releases; releases ship the portable ZIP only.

# NAME                    : {#AppName}
# VERSION                 : {#AppVersion}
# DEFAULTDIRNAME          : {autopf}
# APPMANAGER              : {appmanager}
# OUTPUTDIR               : {##OutputDir}
# OutputBaseFilename      : Netckore-{#AppVersion}
# Compression             : lzma2
# SolidCompression         : yes
# WizardStyle             : modern
# SIGNTOOL                : signingbin\signtool.exe

[Setup]
AppName=Netckore
AppVersion={#AppVersion}
AppVerName=Netckore {#AppVersion}
DefaultDirName=Netckore
DefaultGroupName=Netckore
OutputDir=dist
OutputBaseFilename=Netckore-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\Netckore\Netckore.exe"
Source: "dist\Netckore\Fluxckore.exe"
# Includes all files from dist\Netckore\*

[Icons]
Name="Netckore": "{app}"
Name="Netckore Desktop": "{group}\Netckore"

[Tasks]
GroupNet="Netckore &Netckore": checkbox
GroupNetDescription="Instalar Netckore para tu PC"

[Messages]
WelcomePageTitle="Welcome to Netckore"
WelcomePageText="Download Netckore helps your network connection not become a barrier. Why not install? Click OK to install now."
WelcomePageSkipOptions=1
WelcomePageSkipText="Skip installation..."
InstallSuccessMsg="Netckore has been installed successfully.\nPlease restart your computer if needed."
UninstallSuccessMsg="Netckore was removed.\nThank you!"
