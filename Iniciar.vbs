Set fso = CreateObject("Scripting.FileSystemObject")
pasta = fso.GetParentFolderName(WScript.ScriptFullName)
script = fso.BuildPath(pasta, "guardiao.py")

Set shellApp = CreateObject("Shell.Application")
shellApp.ShellExecute "pythonw.exe", """" & script & """", pasta, "open", 0
