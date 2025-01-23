[Setup]
AppName=BTViz
AppVersion=1.0
DefaultDirName={pf}\BTViz
DefaultGroupName=BTViz
OutputBaseFilename=installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "BTViz\dist\*"; DestDir: "{app}"; Flags: recursesubdirs

[Run]
Filename: "{app}\run.bat"; Description: "Run BTViz"; Flags: shellexec
