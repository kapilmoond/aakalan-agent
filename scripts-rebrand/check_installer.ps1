$p = Get-Process -Id 10684 -ErrorAction SilentlyContinue
if ($p) {
  "PID: $($p.Id)"
  "Title: $($p.MainWindowTitle)"
  "Handle: $($p.MainWindowHandle)"
  "Responding: $($p.Responding)"
  "StartTime: $($p.StartTime)"
} else {
  "process gone"
}
