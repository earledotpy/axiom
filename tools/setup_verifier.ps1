# tools/setup_verifier.ps1
# Set strict security boundaries for AXIOM verifier environment.

# Ensure script is run with administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator."
    Exit 1
}

$axiomStateRoot = "C:\axiom_state"
$axiomWorkspace = "C:\axiom"
$verifierUser = "axiom_verifier"

# Create directories
$subdirs = @(
    "mandates",
    "audit",
    "relay",
    "verifier_worktrees",
    "verifier_venv",
    "public_keys",
    "sqlite"
)

# 1. Create root directory if not exists
if (-not (Test-Path $axiomStateRoot)) {
    New-Item -Path $axiomStateRoot -ItemType Directory | Out-Null
    Write-Host "Created state root: $axiomStateRoot"
}

# 2. Setup ACLs on the state root directory
$acl = Get-Acl $axiomStateRoot
# Disable inheritance, do not copy existing rules ($true, $false)
$acl.SetAccessRuleProtection($true, $false)

# Define Access Rules
# System, Administrators, and the verifier user get full control.
$systemAr = New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$adminsAr = New-Object System.Security.AccessControl.FileSystemAccessRule("BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$verifierAr = New-Object System.Security.AccessControl.FileSystemAccessRule($verifierUser, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")

$acl.SetAccessRule($systemAr)
$acl.SetAccessRule($adminsAr)

# Note: The verifierUser must exist on the local system. If it doesn't,
# we log a warning but apply the ACLs for System/Admins first.
try {
    $acl.SetAccessRule($verifierAr)
    Write-Host "Configured full control permissions for $verifierUser."
} catch {
    Write-Warning "Failed to set ACL for user '$verifierUser'. Please ensure the local user exists (run 'New-LocalUser -Name $verifierUser' manually if needed)."
}

Set-Acl $axiomStateRoot $acl
Write-Host "Successfully secured $axiomStateRoot (Inheritance disabled, System & Administrators Full Control)."

# Create subdirectories (they will inherit the root's secure ACLs)
foreach ($dir in $subdirs) {
    $path = Join-Path $axiomStateRoot $dir
    if (-not (Test-Path $path)) {
        New-Item -Path $path -ItemType Directory | Out-Null
        Write-Host "Created secure subdirectory: $path"
    }
}

# 3. Grant Read/Execute permissions to the verifier user over the C:\axiom workspace
if (Test-Path $axiomWorkspace) {
    $workspaceAcl = Get-Acl $axiomWorkspace
    $verifierReadAr = New-Object System.Security.AccessControl.FileSystemAccessRule($verifierUser, "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")
    try {
        $workspaceAcl.AddAccessRule($verifierReadAr)
        Set-Acl $axiomWorkspace $workspaceAcl
        Write-Host "Granted Read/Execute permissions to $verifierUser over $axiomWorkspace."
    } catch {
        Write-Warning "Failed to grant read permissions for '$verifierUser' over $axiomWorkspace. Verify user exists."
    }
} else {
    Write-Warning "Workspace directory '$axiomWorkspace' does not exist."
}

Write-Host "AXIOM verifier environment setup sequence completed."
