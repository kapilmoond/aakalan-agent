Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {
  $c = $_.CommandLine
  if ($c -match "serve|gateway|run_agent") {
    "PID: $($_.ProcessId)"
    "  CMD: $($c.Substring(0, [Math]::Min(200, $c.Length)))"
  }
}
