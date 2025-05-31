@echo off
REM Batch file to run the JSON Updater Python script
REM Created on: May 23, 2025

REM Script path - ensure this is correct
SET PYTHON_SCRIPT_PATH="D:\OneDrive\Documents\GitHub\SagaIndex\scripts\apps\json_updater.py"

REM Ensure Python is in your PATH or the 'py' launcher is available.
echo Running Python script: %PYTHON_SCRIPT_PATH%
echo Please wait, this may take a moment...
echo.

REM Option 1: Using the 'py' launcher (recommended if available)

REM usage: json_updater.py [-h] [--root_path ROOT_PATH] [--npc_profile_file NPC_PROFILE_FILE] [--dry_run] edits_file
rem		positional arguments:
rem		  edits_file            Path to the JSON file containing edit requests.
rem		
rem		options:
rem		  -h, --help            show this help message and exit
rem		  --root_path ROOT_PATH
rem		                        Root path of the SagaIndex repository. Defaults to:
rem		                        'D:\OneDrive\Documents\GitHub\SagaIndex'.
rem		  --npc_profile_file NPC_PROFILE_FILE
rem		                        Absolute path to the NPC Profile JSON file. If not provided, uses path from script config: 		'D:\OneDrive\Documents\GitHub\SagaIndex\scripts\json\WIDT_NPCS.json'.
rem		  --dry_run             Simulate updates without writing to files.
		
REM		 py %PYTHON_SCRIPT_PATH% "D:\OneDrive\Documents\GitHub\SagaIndex\scripts\json\updates.json" --dry_run

REM ###  GET HELP  ###
rem py %PYTHON_SCRIPT_PATH% -h


py %PYTHON_SCRIPT_PATH% "D:\OneDrive\Documents\GitHub\SagaIndex\scripts\json\updates.json"
rem  --npc_profile_file "G:\My Drive\Google AI Studio\WIDT\WIDT_NPCS.json"

REM Option 2: Calling python.exe directly
REM If the 'py' launcher doesn't work, or you need to specify a particular Python installation,
REM you can try using the full path to your python.exe.
REM Uncomment the line below and update the path to your python.exe if needed.
REM "C:\Path\To\Your\Python\Installation\python.exe" %PYTHON_SCRIPT_PATH%

echo.
echo Script execution finished.
pause