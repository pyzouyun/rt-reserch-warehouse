#define MyAppName "RT Research Warehouse Legacy"
#define MyAppVersion "0.2.0-win7-legacy"
#define MyAppPublisher "RT Research"
#define MyAppExeName "start-all.ps1"

[Setup]
AppId={{6BA5F7C4-7DBE-4CE3-B86A-5DD24B18F7E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\RTResearchWarehouseLegacy
DefaultGroupName=RT Research Warehouse Legacy
OutputDir=..\output
OutputBaseFilename=RTResearchWarehouseLegacySetup-0.2.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=6.1sp1
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\scripts\start-all.ps1

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\staging\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\RT Research Warehouse"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\start-all.ps1"""; WorkingDir: "{app}"
Name: "{autodesktop}\RT Research Warehouse - Stop"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\stop-all.ps1"""; WorkingDir: "{app}"
Name: "{group}\Open RT Research Warehouse"; Filename: "http://localhost:8080"
Name: "{group}\Start Services"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\start-all.ps1"""; WorkingDir: "{app}"
Name: "{group}\Stop Services"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\stop-all.ps1"""; WorkingDir: "{app}"
Name: "{group}\Run ETL"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\run-etl.ps1"""; WorkingDir: "{app}"
Name: "{group}\Import MOSAIQ CSV"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\import-mosaiq.ps1"""; WorkingDir: "{app}"

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\init-config.ps1"""; WorkingDir: "{app}"; StatusMsg: "Initializing configuration..."
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\init-postgres.ps1"""; WorkingDir: "{app}"; StatusMsg: "Initializing PostgreSQL database..."
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\install-services.ps1"""; WorkingDir: "{app}"; StatusMsg: "Installing Windows services..."
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\start-all.ps1"""; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent; Description: "Start RT Research Warehouse"

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\uninstall-services.ps1"""; WorkingDir: "{app}"; RunOnceId: "RemoveRTResearchServices"
