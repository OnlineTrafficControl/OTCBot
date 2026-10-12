
$LOG_PREFIX = "[OTCBot]"
$LOG_SUFFIX = ""

function log_info {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Message)

    Write-Host "$LOG_PREFIX $($Message -join ' ') $LOG_SUFFIX" -ForegroundColor Green
}

function log_error {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Message)

    Write-Host "$LOG_PREFIX $($Message -join ' ') $LOG_SUFFIX" -ForegroundColor Red
}


# Require dot-sourcing.
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "$LOG_PREFIX This script must be dot-sourced." -ForegroundColor Red
    Write-Host "Usage: . .\bin\setup.ps1" -ForegroundColor Red
    exit 1
}


function main {
    $current_dir = (Get-Location).Path

    if ((Split-Path $current_dir -Leaf) -ne "OTCBot") {
        log_error "You must run this script from the OTCBot repository root."
        return 1
    }

    # Validate Git and repository root.
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        log_error "Git is not available."
        return 1
    }

    $repo_root = git rev-parse --show-toplevel 2>$null

    if ($LASTEXITCODE -ne 0 -or -not $repo_root) {
        log_error "The current directory is not inside a Git repository."
        return 1
    }

    $repo_root = (Resolve-Path $repo_root).Path

    if ($current_dir -ne $repo_root) {
        log_error "You must run this script from the repository root."
        return 1
    }

    # Find a working Python 3 interpreter.
    $python = $null

    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -c "import sys; sys.exit(sys.version_info.major != 3)" 2>$null

        if ($LASTEXITCODE -eq 0) {
            $python = "py"
        }
    }

    if (-not $python -and (Get-Command python -ErrorAction SilentlyContinue)) {
        python -c "import sys; sys.exit(sys.version_info.major != 3)" 2>$null

        if ($LASTEXITCODE -eq 0) {
            $python = "python"
        }
    }

    if (-not $python) {
        log_error "Python 3 is not available."
        return 1
    }

    log_info "Python 3 is available."

    # Validate the virtual environment.
    $venv = Join-Path $current_dir ".venv"
    $activate = Join-Path $venv "Scripts\Activate.ps1"

    if ((Test-Path $venv) -and -not (Test-Path $venv -PathType Container)) {
        log_error ".venv exists but is not a directory."
        return 1
    }

    if (Test-Path $venv -PathType Container) {
        if (-not (Test-Path $activate -PathType Leaf)) {
            log_error ".venv exists but does not contain Scripts\Activate.ps1."
            return 1
        }

        log_info "Virtual environment already exists."
    }
    else {
        log_info "Creating virtual environment."

        if ($python -eq "py") {
            py -3 -m venv $venv
        }
        else {
            python -m venv $venv
        }

        if ($LASTEXITCODE -ne 0) {
            log_error "Failed to create the virtual environment."
            return 1
        }

        if (-not (Test-Path $activate -PathType Leaf)) {
            log_error "Virtual environment activation script was not created."
            return 1
        }
    }

    log_info "Activating virtual environment."

    try {
        . $activate
    }
    catch {
        log_error "Failed to activate the virtual environment: $_"
        return 1
    }

    if ($env:VIRTUAL_ENV -ne $venv) {
        log_error "Virtual environment activation could not be verified."
        return 1
    }

    log_info "Virtual environment created and activated."
    return 0
}


$setup_result = main

if ($setup_result -ne 0) {
    Write-Host "$LOG_PREFIX Setup failed with code $setup_result." -ForegroundColor Red
}
