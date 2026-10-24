[Setup]
AppName=BlueCube
AppVersion=0.5
DefaultDirName={autopf}\BlueCube
DefaultGroupName=BlueCube
UninstallDisplayIcon={app}\BlueCube.exe
OutputDir=.\installer_output
OutputBaseFilename=BlueCube_v0.5_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
; Build BlueCube.exe with BLUECUBE_DEV_TOOLS=0 before compiling this installer.
; 1. الملف التنفيذي الرئيسي
; Set BuildFolder to a verified dist/windows-YYYYMMDD-HHMMSS/BlueCube directory.
#ifndef BuildFolder
  #error "Define BuildFolder as the verified onedir output directory."
#endif
Source: "{#BuildFolder}\BlueCube.exe"; DestDir: "{app}"; Flags: ignoreversion
; 2. تضمين كافة المجلدات الفرعية والمكتبات (assets و data)
Source: "{#BuildFolder}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BlueCube"; Filename: "{app}\BlueCube.exe"
Name: "{autodesktop}\BlueCube"; Filename: "{app}\BlueCube.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Description: "{cm:LaunchProgram,BlueCube}"; Filename: "{app}\BlueCube.exe"; Flags: nowait postinstall skipifsilent
