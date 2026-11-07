$ErrorActionPreference = 'Stop'

Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class LoadedKeyboardLayouts
{
    [DllImport("user32.dll")]
    public static extern int GetKeyboardLayoutList(int count, [Out] IntPtr[] layouts);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool UnloadKeyboardLayout(IntPtr layout);
}
"@

$config = Join-Path $env:LOCALAPPDATA 'Language Fixer\languages.json'
if (-not (Test-Path -LiteralPath $config)) { return }

$allowed = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
if ($allowed.Count -eq 0) { throw 'Select at least one language in Language Fixer.' }
foreach ($tag in $allowed) {
    if ($tag -isnot [string] -or (New-WinUserLanguageList -Language $tag)[0].LanguageTag -ne $tag) {
        throw 'The saved language list contains an invalid language tag.'
    }
}
$languages = Get-WinUserLanguageList
$changed = $false

for ($i = $languages.Count - 1; $i -ge 0; $i--) {
    if ($languages[$i].LanguageTag -notin $allowed) {
        $languages.RemoveAt($i)
        $changed = $true
    }
}

foreach ($tag in $allowed) {
    if ($tag -notin $languages.LanguageTag) {
        $languages.Add((New-WinUserLanguageList -Language $tag)[0])
        $changed = $true
    }
}

if ($changed) {
    Set-WinUserLanguageList -LanguageList $languages -Force
    $actual = @(foreach ($language in (Get-WinUserLanguageList)) { $language.LanguageTag })
    $missing = @($allowed | Where-Object { $_ -notin $actual })
    if ($missing.Count) {
        throw "Windows did not accept these input languages: $($missing -join ', ')."
    }
    if (@($actual | Where-Object { $_ -notin $allowed }).Count) {
        throw 'Windows did not remove all unselected input languages.'
    }
}

# Standard Windows input tips begin with the input language's hexadecimal LCID.
$allowedLocales = foreach ($language in $languages) {
    foreach ($tip in $language.InputMethodTips) {
        if ($tip -match '^([0-9a-f]{4}):') {
            [Convert]::ToInt32($Matches[1], 16)
        }
    }
}
if (-not $allowedLocales) { return }

$count = [LoadedKeyboardLayouts]::GetKeyboardLayoutList(0, $null)
$layouts = [IntPtr[]]::new($count)
$count = [LoadedKeyboardLayouts]::GetKeyboardLayoutList($count, $layouts)
for ($i = 0; $i -lt $count; $i++) {
    $locale = $layouts[$i].ToInt64() -band 0xffff
    if ($locale -notin $allowedLocales) {
        [void][LoadedKeyboardLayouts]::UnloadKeyboardLayout($layouts[$i])
    }
}
