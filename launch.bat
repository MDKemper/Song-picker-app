@echo off
start "" python app.py
timeout /t 1 >nul

REM Adjust Chrome path if needed
set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"

REM Launch both windows
start "" %CHROME% --new-window http://127.0.0.1:5000/


REM Wait for Chrome windows to open
timeout /t 2 >nul

REM Arrange windows side by side using PowerShell
powershell -command "& {
    Add-Type -AssemblyName 'System.Windows.Forms'
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $width = [int]($screen.Width / 2)
    $height = $screen.Height
    $left = 0
    $right = $width

    $shell = New-Object -ComObject Shell.Application
    $windows = @($shell.Windows() | Where-Object { $_.LocationURL -like '*127.0.0.1*' })

    if ($windows.Count -ge 2) {
        $windows[0].Left = $left
        $windows[0].Top = 0
        $windows[0].Width = $width
        $windows[0].Height = $height

        $windows[1].Left = $right
        $windows[1].Top = 0
        $windows[1].Width = $width
        $windows[1].Height = $height
    }
}"
