param(
    [Parameter(Mandatory)][ValidateSet('Read', 'Enable', 'Disable', 'Resolve')][string] $Action,
    [string] $LanguageTag
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$taskName = 'Language Fixer'
$user = [Security.Principal.WindowsIdentity]::GetCurrent()
switch ($Action) {
    'Resolve' { (New-WinUserLanguageList -Language $LanguageTag)[0].LanguageTag }
    'Read' {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        ConvertTo-Json -Compress -InputObject @{
            enabled = [bool]($task -and $task.State -ne 'Disabled')
            languages = @(foreach ($language in (Get-WinUserLanguageList)) { $language.LanguageTag })
            catalog = @(foreach ($culture in [Globalization.CultureInfo]::GetCultures('NeutralCultures, SpecificCultures')) {
                if ($culture.Name) {
                    @{ tag = $culture.Name; name = $culture.EnglishName; native = $culture.NativeName }
                }
            })
        } -Depth 4
    }
    'Disable' {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) { $task | Disable-ScheduledTask | Out-Null }
    }
    'Enable' {
        $launcher = Join-Path $PSScriptRoot 'Repair-Languages.vbs'
        $taskAction = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\wscript.exe" -Argument ('//B //NoLogo "' + $launcher + '"')
        $repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
        $logon = New-ScheduledTaskTrigger -AtLogOn -User $user.Name
        $principal = New-ScheduledTaskPrincipal -UserId $user.Name -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger @($repeat, $logon) -Principal $principal -Settings $settings -Force | Out-Null
        $repair = Join-Path $PSScriptRoot 'Repair-Languages.ps1'
        & $repair
    }
}
