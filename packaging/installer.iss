; Gayatri Demo v4.0.0 — Inno Setup Script
#define MyAppName "Gayatri — AI-Powered Adaptive Learning Platform"
#define MyAppVersion "4.0.0"
#define MyAppPublisher "Gayatri Education"
#define MyAppURL "https://github.com/Gayatri-Education/Gayatri-Demo"
#define MyAppExeName "Gayatri.exe"

[Setup]
AppId={{E6F7A310-8C4D-4F21-9B5A-GAYATRI400}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Gayatri AI
DefaultGroupName=Gayatri AI
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup
SetupIconFile=..\gai3.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Gayatri_Adaptive_Learning_Platform_v4.0.0\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent