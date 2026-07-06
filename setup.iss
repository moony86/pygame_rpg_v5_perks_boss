[Setup]
AppName=BlueCube
AppVersion=0.5
DefaultDirName={autopf}\BlueCube
DefaultGroupName=BlueCube
UninstallDisplayIcon={app}\main.exe
OutputDir=.\installer_output
OutputBaseFilename=BlueCube_v0.5_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
; 1. الملف التنفيذي الرئيسي
Source: ".\dist_nuitka_demo\main.dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
; 2. تضمين كافة المجلدات الفرعية والمكتبات (assets و data)
Source: ".\dist_nuitka_demo\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BlueCube"; Filename: "{app}\main.exe"
Name: "{autodesktop}\BlueCube"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Description: "{cm:LaunchProgram,BlueCube}"; Filename: "{app}\main.exe"; Flags: nowait postinstall skipifsilent