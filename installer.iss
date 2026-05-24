; Vibrance — Inno Setup installer script.
;
; Local build sequence (or driven by .github/workflows/release.yml):
;   pyinstaller --noconsole --onefile --clean ^
;     --name Vibrance ^
;     --icon src\image_editor\resources\app.ico ^
;     --add-data "src\image_editor\resources;image_editor\resources" ^
;     -p src src\image_editor\__main__.py
;   iscc installer.iss
;
; Produces:  dist\Vibrance_Setup_<version>.exe

#define MyAppName        "Vibrance"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Sandeep Bollavaram"
#define MyAppURL         "https://github.com/sandeepbollavaram/image_editor_python"
#define MyAppExeName     "Vibrance.exe"
#define MyAppIcon        "src\image_editor\resources\app.ico"

[Setup]
AppId={{8E55B6F4-9D71-4F77-A6CE-7E5B7B9F3F11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Vibrance_Setup_{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
WizardSmallImageFile=
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="Vibrance photo editor & compressor"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &Desktop shortcut";    GroupDescription: "Additional shortcuts:";    Flags: checkedonce
Name: "startmenuicon";  Description: "Create a Start &Menu shortcut"; GroupDescription: "Additional shortcuts:";    Flags: checkedonce
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";            DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE";              DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppIcon}";          DestDir: "{app}"; DestName: "app.ico"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: startmenuicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}";        Tasks: startmenuicon
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: quicklaunchicon

[Registry]
; Associate Vibrance with common image extensions (Open with…)
Root: HKCR; Subkey: "Applications\{#MyAppExeName}";                         ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\shell\open\command";      ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes";          ValueType: string; ValueName: ".jpg";  ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes";          ValueType: string; ValueName: ".jpeg"; ValueData: ""
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes";          ValueType: string; ValueName: ".png";  ValueData: ""
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes";          ValueType: string; ValueName: ".webp"; ValueData: ""
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes";          ValueType: string; ValueName: ".tif";  ValueData: ""
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes";          ValueType: string; ValueName: ".tiff"; ValueData: ""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
