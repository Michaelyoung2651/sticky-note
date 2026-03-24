Set WshShell = CreateObject("WScript.Shell")
cmd = "cmd /c cd /d """ & Replace(WScript.ScriptFullName, WScript.ScriptName, "") & """ && pythonw sticky_schedule.py"
WshShell.Run cmd, 0, False
