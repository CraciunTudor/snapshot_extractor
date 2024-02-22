# snapshot_extractor
Tool to extract files from the snapshot that are essential for MCTRL analysis

Script to unzip the BTS Snapshot file and get the core files used in MCTRL analysis
Convert to .py .exe using pyinstaller
Developed using Python 3.11.8, converted using pyinstaller 6.4.0 (pyinstaller --onefile script.py)
13.02.2024 - Initial version
14.02.2024 - Upon starting the application, the CLI will open and request the zip path
              - The files will be extracted inside a new directory created in the folder where the .exe is
           - Now pm files are also extracted
           - Unfortunately, cannot provide the zip path from a remote server, as the process does not have privileges to open the remote zip

Copyright 2024 Nokia. All rights reserved.
