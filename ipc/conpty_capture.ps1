# ConPTY Capture — dot-source this file to get Invoke-ConPtyCapture
# and the persistent session functions (New/Write/Read/Remove-ConPtySession).

if (-not ([System.Management.Automation.PSTypeName]'ConPty.ConPtySession').Type) {
    Add-Type -Language CSharp -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace ConPty {

    [StructLayout(LayoutKind.Sequential)]
    public struct COORD {
        public short X;
        public short Y;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct STARTUPINFO {
        public int    cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        public int    dwX;
        public int    dwY;
        public int    dwXSize;
        public int    dwYSize;
        public int    dwXCountChars;
        public int    dwYCountChars;
        public int    dwFillAttribute;
        public int    dwFlags;
        public short  wShowWindow;
        public short  cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct STARTUPINFOEX {
        public STARTUPINFO StartupInfo;
        public IntPtr      lpAttributeList;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int    dwProcessId;
        public int    dwThreadId;
    }

    public class ConPtySession : IDisposable {

        // ── P/Invoke ────────────────────────────────────────────────────────

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool CreatePipe(out IntPtr hRead, out IntPtr hWrite,
            IntPtr lpPipeAttributes, uint nSize);

        // Returns HRESULT — do NOT use GetLastWin32Error to check this
        [DllImport("kernel32.dll", SetLastError = false)]
        static extern int CreatePseudoConsole(COORD size,
            IntPtr hInput, IntPtr hOutput, uint dwFlags, out IntPtr phPC);

        [DllImport("kernel32.dll", SetLastError = false)]
        static extern void ClosePseudoConsole(IntPtr hPC);

        [DllImport("kernel32.dll", SetLastError = false)]
        static extern int ResizePseudoConsole(IntPtr hPC, COORD size);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool InitializeProcThreadAttributeList(
            IntPtr lpAttributeList, int dwAttributeCount,
            int dwFlags, ref IntPtr lpSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool UpdateProcThreadAttribute(
            IntPtr lpAttributeList, uint dwFlags,
            IntPtr Attribute, IntPtr lpValue,
            IntPtr cbSize, IntPtr lpPreviousValue, IntPtr lpReturnSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern void DeleteProcThreadAttributeList(IntPtr lpAttributeList);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern bool CreateProcessW(
            string lpApplicationName,
            StringBuilder lpCommandLine,
            IntPtr lpProcessAttributes,
            IntPtr lpThreadAttributes,
            bool bInheritHandles,
            uint dwCreationFlags,
            IntPtr lpEnvironment,
            string lpCurrentDirectory,
            ref STARTUPINFOEX lpStartupInfo,
            out PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool TerminateProcess(IntPtr hProcess, uint uExitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool CloseHandle(IntPtr hObject);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool ReadFile(IntPtr hFile, byte[] lpBuffer,
            uint nNumberOfBytesToRead, out uint lpNumberOfBytesRead,
            IntPtr lpOverlapped);

        [DllImport("kernel32.dll")]
        static extern bool PeekNamedPipe(IntPtr hNamedPipe,
            IntPtr lpBuffer, uint nBufferSize, IntPtr lpBytesRead,
            out uint lpTotalBytesAvail, IntPtr lpBytesLeftThisMessage);

        const uint EXTENDED_STARTUPINFO_PRESENT       = 0x00080000;
        const uint DETACHED_PROCESS                   = 0x00000008;
        const uint PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016;
        const uint WAIT_TIMEOUT_CODE                  = 0x00000102;

        // ── Session state ────────────────────────────────────────────────────

        IntPtr _hPC         = IntPtr.Zero;
        IntPtr _hInputWrite = IntPtr.Zero;
        IntPtr _hOutputRead = IntPtr.Zero;
        IntPtr _hProcess    = IntPtr.Zero;
        IntPtr _attrBuf     = IntPtr.Zero;

        Thread     _readerThread;
        List<byte> _accumulator = new List<byte>();
        bool       _disposed;

        // Diagnostics exposed for PowerShell inspection
        public int    ProcessId   { get; private set; }
        public string StartError  { get; private set; }

        // ── Public API ───────────────────────────────────────────────────────

        public void Start(string commandLine, string workingDir) {
            // Step 1: pipes
            IntPtr inputRead, inputWrite, outputRead, outputWrite;
            if (!CreatePipe(out inputRead, out inputWrite, IntPtr.Zero, 0))
                throw new Exception("CreatePipe(input) failed: " + Marshal.GetLastWin32Error());
            if (!CreatePipe(out outputRead, out outputWrite, IntPtr.Zero, 0)) {
                CloseHandle(inputRead); CloseHandle(inputWrite);
                throw new Exception("CreatePipe(output) failed: " + Marshal.GetLastWin32Error());
            }

            // Step 2: CreatePseudoConsole — returns HRESULT, NOT a BOOL
            COORD size = new COORD { X = 220, Y = 50 };
            int hr = CreatePseudoConsole(size, inputRead, outputWrite, 0, out _hPC);
            if (hr != 0) {
                CloseHandle(inputRead); CloseHandle(inputWrite);
                CloseHandle(outputRead); CloseHandle(outputWrite);
                throw new Exception("CreatePseudoConsole HRESULT: 0x" + hr.ToString("X8"));
            }

            // Step 3: close the ConPTY-owned handle copies (ConPTY duplicated them)
            CloseHandle(inputRead);
            CloseHandle(outputWrite);
            _hInputWrite = inputWrite;
            _hOutputRead = outputRead;

            // Step 4: attribute list — first call gives required buffer size
            IntPtr attrSize = IntPtr.Zero;
            InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref attrSize);
            _attrBuf = Marshal.AllocHGlobal((int)attrSize.ToInt64());
            if (!InitializeProcThreadAttributeList(_attrBuf, 1, 0, ref attrSize))
                throw new Exception("InitializeProcThreadAttributeList: " + Marshal.GetLastWin32Error());

            // Step 5: bind the ConPTY handle into the attribute list.
            // lpValue = hPC directly (the handle value itself), NOT a pointer to it.
            // cbSize  = sizeof(HPCON) = sizeof(void*) = IntPtr.Size.
            if (!UpdateProcThreadAttribute(_attrBuf, 0,
                    (IntPtr)PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
                    _hPC, (IntPtr)IntPtr.Size, IntPtr.Zero, IntPtr.Zero))
                throw new Exception("UpdateProcThreadAttribute: " + Marshal.GetLastWin32Error());

            // Step 6: build STARTUPINFOEX with explicit layout (cb = sizeof full struct)
            var siEx = new STARTUPINFOEX();
            siEx.StartupInfo.cb = Marshal.SizeOf(typeof(STARTUPINFOEX));  // 112 on x64
            siEx.lpAttributeList = _attrBuf;

            // Step 7: start reader BEFORE CreateProcess (pipe can fill on startup burst)
            _readerThread = new Thread(() => {
                byte[] buf = new byte[4096];
                uint n;
                while (ReadFile(_hOutputRead, buf, (uint)buf.Length, out n, IntPtr.Zero) && n > 0) {
                    lock (_accumulator) {
                        for (int i = 0; i < (int)n; i++) _accumulator.Add(buf[i]);
                    }
                }
            });
            _readerThread.IsBackground = true;
            _readerThread.Start();

            // Step 8: CreateProcess — lpCommandLine MUST be StringBuilder (writable buffer)
            var cmdSB = new StringBuilder(commandLine);
            PROCESS_INFORMATION pi;
            if (!CreateProcessW(null, cmdSB, IntPtr.Zero, IntPtr.Zero,
                    false, EXTENDED_STARTUPINFO_PRESENT,
                    IntPtr.Zero, workingDir, ref siEx, out pi))
                throw new Exception("CreateProcessW failed: " + Marshal.GetLastWin32Error());

            // Step 9: keep process handle; thread handle not needed
            CloseHandle(pi.hThread);
            _hProcess = pi.hProcess;
            ProcessId = pi.dwProcessId;
        }

        public void WriteInput(byte[] data) {
            // WriteFile P/Invoke not yet imported — add when building persistent sessions
            throw new NotImplementedException("WriteInput requires WriteFile P/Invoke");
        }

        /// Returns false on timeout (process was forcibly terminated).
        public bool WaitForExit(int timeoutMs) {
            uint r = WaitForSingleObject(_hProcess, (uint)timeoutMs);
            if (r == WAIT_TIMEOUT_CODE) {
                TerminateProcess(_hProcess, 1);
                WaitForSingleObject(_hProcess, 5000);
                return false;
            }
            return true;
        }

        public byte[] GetRawBytes() {
            lock (_accumulator) return _accumulator.ToArray();
        }

        public int BytesAvailable() {
            uint avail;
            if (_hOutputRead == IntPtr.Zero) return 0;
            PeekNamedPipe(_hOutputRead, IntPtr.Zero, 0, IntPtr.Zero, out avail, IntPtr.Zero);
            return (int)avail;
        }

        public void Resize(short cols, short rows) {
            if (_hPC != IntPtr.Zero)
                ResizePseudoConsole(_hPC, new COORD { X = cols, Y = rows });
        }

        public void Dispose() {
            if (_disposed) return;
            _disposed = true;
            // CRITICAL ORDER: ClosePseudoConsole signals EOF on outputRead,
            // which lets ReadFile in the reader thread return 0 and exit.
            // Join AFTER close — never before.
            if (_hPC != IntPtr.Zero) {
                ClosePseudoConsole(_hPC);
                _hPC = IntPtr.Zero;
            }
            _readerThread?.Join(5000);

            if (_attrBuf != IntPtr.Zero) {
                DeleteProcThreadAttributeList(_attrBuf);
                Marshal.FreeHGlobal(_attrBuf);
                _attrBuf = IntPtr.Zero;
            }
            if (_hProcess   != IntPtr.Zero) { CloseHandle(_hProcess);        _hProcess   = IntPtr.Zero; }
            if (_hOutputRead != IntPtr.Zero) { CloseHandle(_hOutputRead);    _hOutputRead = IntPtr.Zero; }
            if (_hInputWrite != IntPtr.Zero) { CloseHandle(_hInputWrite);    _hInputWrite = IntPtr.Zero; }
        }
    }
}
'@
}

# ── ANSI / VT100 stripping ────────────────────────────────────────────────────

function Strip-Ansi {
    param([string]$Raw)
    # Normalize CRLF → LF so trailing \r doesn't confuse the overwrite handling
    $normalized = $Raw -replace '\r\n', "`n"
    # Remove VT/ANSI sequences — OSC alternatives come FIRST because [@-Z\\-_] includes ]
    # (ASCII 93 falls in the \-_ range), which would otherwise consume ESC+] before OSC matches
    $stripped = $normalized -replace '\x1b(?:\][^\x07\x1b]*(?:\x07|\x1b\\)|\[[0-?]*[ -/]*[@-~]|[@-Z\\-_])', ''
    # Remove any orphaned BEL-terminated OSC content not caught above
    $stripped = $stripped -replace '\]\d*;[^\x07\n]*\x07?', ''
    # Handle bare CR (overwrite/spinner pattern): keep only text after the last \r
    $lines = $stripped -split '\n' | ForEach-Object {
        $cr = $_.LastIndexOf("`r")
        if ($cr -ge 0) { $_.Substring($cr + 1) } else { $_ }
    }
    return ($lines -join "`n").Trim()
}

# ── Command-line quoting ──────────────────────────────────────────────────────

function Format-CommandLine {
    param([string]$Exe, [string[]]$ArgList = @())
    $parts = @('"' + $Exe.Replace('"', '\"') + '"')
    foreach ($a in $ArgList) {
        if ($a -match '[\s"]') {
            $parts += '"' + $a.Replace('"', '\"') + '"'
        } else {
            $parts += $a
        }
    }
    return $parts -join ' '
}

# ── One-shot capture ──────────────────────────────────────────────────────────

function Invoke-ConPtyCapture {
    param(
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Arguments  = @(),
        [string]$WorkingDir   = 'C:\axiom',
        [int]$TimeoutMs       = 30000,
        [switch]$Diagnostic
    )

    $cmdLine = Format-CommandLine -Exe $Command -ArgList $Arguments
    $session = [ConPty.ConPtySession]::new()
    try {
        $session.Start($cmdLine, $WorkingDir)

        if ($Diagnostic) {
            Write-Host "[conpty-diag] PID: $($session.ProcessId)"
        }

        $timedOut = -not $session.WaitForExit($TimeoutMs)
        $session.Dispose()   # ClosePseudoConsole → EOF → reader joins

        $bytes = $session.GetRawBytes()
        $raw   = [System.Text.Encoding]::UTF8.GetString($bytes)

        if ($Diagnostic) {
            Write-Host "[conpty-diag] raw length : $($raw.Length) chars / $($bytes.Length) bytes"
            if ($bytes.Length -gt 0) {
                $hex = ($bytes[0..[Math]::Min(511, $bytes.Length - 1)] |
                        ForEach-Object { $_.ToString('X2') }) -join ' '
                Write-Host "[conpty-diag] hex dump   : $hex"
            }
            Write-Host "[conpty-diag] raw string : $raw"
        }

        if ($timedOut) {
            Write-Warning "[conpty] timed out after ${TimeoutMs}ms — output may be partial"
        }

        return Strip-Ansi -Raw $raw

    } catch {
        $session.Dispose()
        throw
    }
}

# ── Hosted capture (nested-ConPTY safe) ───────────────────────────────────────
# When this script runs INSIDE a ConPTY (e.g. a Windows Terminal pane), a child
# spawned here attaches to the parent console instead of our pseudo-console, so
# Invoke-ConPtyCapture captures only init bytes. Spawning the capture from a fresh
# hidden pwsh host severs that inheritance chain — the Microsoft-recommended
# pattern. Params/result pass through Clixml/temp files to survive arbitrary
# prompt content (newlines, quotes, markdown).

function Invoke-ConPtyCaptureHosted {
    param(
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Arguments = @(),
        [string]$WorkingDir  = 'C:\axiom',
        [int]$TimeoutMs      = 45000
    )

    $g          = [guid]::NewGuid().ToString('N')
    $paramsFile = Join-Path $env:TEMP "conpty_params_$g.xml"
    $outFile    = Join-Path $env:TEMP "conpty_out_$g.txt"
    $hostScript = Join-Path $env:TEMP "conpty_host_$g.ps1"

    @{ Command = $Command; Arguments = $Arguments; WorkingDir = $WorkingDir; TimeoutMs = $TimeoutMs } |
        Export-Clixml -Path $paramsFile

    $body = @"
. "$PSScriptRoot\conpty_capture.ps1"
`$p = Import-Clixml -Path '$paramsFile'
`$r = Invoke-ConPtyCapture -Command `$p.Command -Arguments `$p.Arguments -WorkingDir `$p.WorkingDir -TimeoutMs `$p.TimeoutMs
[System.IO.File]::WriteAllText('$outFile', `$r)
"@
    Set-Content -Path $hostScript -Value $body -Encoding UTF8

    try {
        $proc = Start-Process pwsh -WindowStyle Hidden -PassThru `
            -ArgumentList @('-NoProfile', '-File', $hostScript)
        # Host startup + ConPTY teardown margin on top of the capture timeout
        if (-not $proc.WaitForExit($TimeoutMs + 20000)) {
            try { $proc.Kill() } catch {}
            return "ERROR: ConPTY host did not exit in time"
        }
        $result = if (Test-Path $outFile) { [System.IO.File]::ReadAllText($outFile) } else { "" }
        return $result.Trim()
    } finally {
        Remove-Item $paramsFile, $outFile, $hostScript -ErrorAction SilentlyContinue
    }
}

# ── Persistent session management ─────────────────────────────────────────────

$script:ConPtySessions = @{}

function New-ConPtySession {
    param(
        [Parameter(Mandatory)][string]$Id,
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Arguments = @(),
        [string]$WorkingDir  = 'C:\axiom'
    )
    if ($script:ConPtySessions.ContainsKey($Id)) {
        throw "ConPTY session '$Id' already exists. Remove it first."
    }
    $session = [ConPty.ConPtySession]::new()
    $cmdLine = Format-CommandLine -Exe $Command -ArgList $Arguments
    $session.Start($cmdLine, $WorkingDir)
    $script:ConPtySessions[$Id] = $session
    Write-Host "[conpty] session '$Id' started (PID $($session.ProcessId))"
    return $Id
}

function Read-ConPtyOutput {
    param([Parameter(Mandatory)][string]$Id, [switch]$Raw)
    if (-not $script:ConPtySessions.ContainsKey($Id)) { throw "No session '$Id'" }
    $bytes = $script:ConPtySessions[$Id].GetRawBytes()
    $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
    if ($Raw) { return $text }
    return Strip-Ansi -Raw $text
}

function Remove-ConPtySession {
    param([Parameter(Mandatory)][string]$Id)
    if (-not $script:ConPtySessions.ContainsKey($Id)) { return }
    $script:ConPtySessions[$Id].Dispose()
    $script:ConPtySessions.Remove($Id)
    Write-Host "[conpty] session '$Id' removed"
}
