@echo off
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed. Installing Python...
    curl https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe --output python-installer.exe
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python-installer.exe
) ELSE (
    echo Python is installed.
)
echo Installing required packages...
python -m pip install PyQt5==5.15.6 PyQtWebEngine==5.15.6
echo Done.

echo Downloading file...
curl https://example.com/path/to/file --output "C:\Program Files\htaamas\browser\app.py"
echo File downloaded.

echo Creating shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Your Shortcut.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "C:\path\to\downloaded\file" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs
echo Shortcut created.