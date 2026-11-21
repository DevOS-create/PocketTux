#!/data/data/com.termux/files/usr/bin/bash

set -Eeuo pipefail

readonly VERSION="0.1.0-beta"
readonly PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME="${HOME:-/data/data/com.termux/files/home}"

if [[ -t 1 ]]; then
    C_INFO=$'\033[1;36m'; C_OK=$'\033[1;32m'; C_WARN=$'\033[1;33m'
    C_ERR=$'\033[1;31m';  C_OFF=$'\033[0m'
else
    C_INFO=""; C_OK=""; C_WARN=""; C_ERR=""; C_OFF=""
fi

info()    { printf '%s%s%s\n' "$C_INFO" "$*" "$C_OFF"; }
success() { printf '%s%s%s\n' "$C_OK"   "$*" "$C_OFF"; }
warning() { printf '%s%s%s\n' "$C_WARN" "$*" "$C_OFF" >&2; }
die()     { printf '%s%s%s\n' "$C_ERR"  "$*" "$C_OFF" >&2; exit 1; }

on_err() {
    local code=$? line=$1
    printf '%sInstallation failed at line %s (exit code %s).%s\n' \
        "$C_ERR" "$line" "$code" "$C_OFF" >&2
}
trap 'on_err $LINENO' ERR

printf '\nPocketTux Bootstrap %s\n' "$VERSION"
printf 'Preparing Termux installation...\n\n'

info "Checking Termux environment..."

[[ "$(id -u)" -ne 0 ]] || die "Do not run this script as root."
[[ -d "$PREFIX" ]] || die "Invalid PREFIX: $PREFIX"
[[ -d "$HOME" && -w "$HOME" ]] || die "HOME is missing or not writable: $HOME"
command -v pkg >/dev/null 2>&1 || die "Termux package manager (pkg) not found."

success "Termux environment detected."

info "Checking Python..."

find_python() {
    command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}

PYTHON="$(find_python)"
if [[ -z "$PYTHON" ]]; then
    info "Installing Python..."
    pkg install -y python
    PYTHON="$(find_python)"
fi

[[ -n "$PYTHON" ]] || die "Python could not be installed."
success "Python is ready: $("$PYTHON" --version 2>&1)"

info "Locating project installer..."

INSTALLER=""
for candidate in \
    "$PROJECT_DIR/installer.py" \
    "$PROJECT_DIR/install.py" \
    "$PROJECT_DIR/scripts/install.py" \
    "$PROJECT_DIR/scripts/installer.py"
do
    if [[ -f "$candidate" ]]; then
        INSTALLER="$candidate"
        break
    fi
done

[[ -n "$INSTALLER" ]] || die "Python installer not found in $PROJECT_DIR."
success "Installer located: $INSTALLER"

export PREFIX
export POCKETTUX_PREFIX="$PREFIX"
export POCKETTUX_HOME="$HOME/.pockettux"
export POCKETTUX_VERSION="$VERSION"

mkdir -p -- "$POCKETTUX_HOME"

info "Installing PocketTux..."

"$PYTHON" "$INSTALLER" \
    --prefix "$PREFIX" \
    --home "$POCKETTUX_HOME"

success "PocketTux installation completed."

if [[ -x "$PREFIX/bin/pockettux" ]]; then
    success "Executable verified."
else
    die "Executable not found in $PREFIX/bin — installation is incomplete."
fi

printf '\nYou can now launch PocketTux using:\n\n'
printf '  pockettux\n\n'