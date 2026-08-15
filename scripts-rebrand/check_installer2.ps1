$procs = Get-Process | Where-Object { $_.ProcessName -like '*Aakalan*' -or $_.ProcessName -like '*Hermes*' -or $_.ProcessName -like '*nsis*' -or $_.ProcessName -like '*Setup*' }
foreach ($p in $procs) {
  "PID: $($p.Id) | Name: $($p.ProcessName) | Title: $($p.MainWindowTitle) | Path: $($p.Path)"
}
