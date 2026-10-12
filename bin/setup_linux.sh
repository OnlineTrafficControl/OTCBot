#!/usr/bin/env bash


LOG_PREFIX="[OTCBot]"
LOG_SUFFIX=""

LOG_INFO_COLOR='\033[32m'
LOG_ERROR_COLOR='\033[31m'
LOG_RESET='\033[0m'


log_info() {
    printf '%b%s%b %s%s\n' \
        "$LOG_INFO_COLOR" "$LOG_PREFIX" "$LOG_RESET" "$*" "$LOG_SUFFIX"
}


log_error() {
    printf '%b%s%b %s%s\n' \
        "$LOG_ERROR_COLOR" "$LOG_PREFIX" "$LOG_RESET" "$*" "$LOG_SUFFIX" >&2
}


# Refuse execution without exiting the user's shell.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    log_error "This script must be sourced, not executed." >&2
    log_error "Usage: source ./bin/setup.sh" >&2
    exit 1
fi


main() {
    local current_dir
    local repo_root

    current_dir="$(pwd -P)" || {
        log_error "Unable to determine the current directory."
        return 1
    }

    if [[ "${current_dir##*/}" != "OTCBot" ]]; then
        log_error "You must run this script from the OTCBot repository root."
        return 1
    fi

    if ! command -v git >/dev/null 2>&1; then
        log_error "Git is not available."
        return 1
    fi

    repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
        log_error "The current directory is not inside a Git repository."
        return 1
    }

    if [[ "$current_dir" != "$(cd "$repo_root" && pwd -P)" ]]; then
        log_error "You must run this script from the repository root."
        return 1
    fi

    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is not available."
        return 1
    fi

    if ! python3 -c \
        'import sys; sys.exit(sys.version_info.major != 3)'; then
        log_error "Python 3 could not be executed."
        return 1
    fi

    log_info "Python 3 is available."

    if [[ -e ".venv" && ! -d ".venv" ]]; then
        log_error ".venv exists but is not a directory."
        return 1
    fi

    if [[ -d ".venv" && ! -f ".venv/bin/activate" ]]; then
        log_error ".venv exists but does not contain an activation script."
        return 1
    fi

    if [[ ! -d ".venv" ]]; then
        log_info "Creating virtual environment."

        if ! python3 -m venv .venv; then
            log_error "Failed to create the virtual environment."
            return 1
        fi
    else
        log_info "Virtual environment already exists."
    fi

    log_info "Installing dependencies."

    if ! .venv/bin/pip install --upgrade pip 1>/dev/null ; then
        log_error "Failed to update pip."
        return 1
    fi

    if ! .venv/bin/pip install -r requirements.txt 1>/dev/null ; then
        log_error "Failed to install dependencies."
        return 1
    fi

    log_info "Activating virtual environment."

    if ! source .venv/bin/activate; then
        log_error "Failed to activate the virtual environment."
        return 1
    fi

    log_info "Virtual environment activated successfully."
}


main
return $?
