Option Explicit
Dim shell, files, folder, result
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
On Error Resume Next
result = shell.Run("pyw.exe """ & folder & "\Language Fixer.pyw""", 0, True)
If Err.Number <> 0 Then
    Err.Clear
    result = shell.Run("pythonw.exe """ & folder & "\Language Fixer.pyw""", 0, True)
End If
If Err.Number <> 0 Or result <> 0 Then
    MsgBox "Language Fixer could not start. Check that Python for Windows with Tkinter is installed.", vbExclamation, "Language Fixer"
End If
