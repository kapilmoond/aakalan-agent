Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
$h = [IntPtr]2296778
"Visible before: $([Win32]::IsWindowVisible($h))"
$r = New-Object Win32+RECT
[Win32]::GetWindowRect($h, [ref]$r) | Out-Null
"Rect: $($r.Left),$($r.Top) - $($r.Right),$($r.Bottom)"
# SW_RESTORE = 9, then bring to front
[Win32]::ShowWindow($h, 9) | Out-Null
[Win32]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 500
"Visible after: $([Win32]::IsWindowVisible($h))"
[Win32]::GetWindowRect($h, [ref]$r) | Out-Null
"Rect after: $($r.Left),$($r.Top) - $($r.Right),$($r.Bottom)"
