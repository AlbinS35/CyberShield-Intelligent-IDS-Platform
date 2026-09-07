#!/usr/bin/env bash
# =============================================================================
# CyberShield — Live NIDS Activation Script
# =============================================================================
# Usage (on Linux / WSL2):
#   chmod +x scripts/setup_live_nids.sh
#   bash scripts/setup_live_nids.sh
#
# What it does:
#   1. Detects the active primary network interface (eth0 > docker0 > wlan0)
#   2. Updates suricata/suricata.yaml af-packet interface
#   3. Generates SURICATA_API_TOKEN via Django management shell
#   4. Extracts DEFAULT_TENANT_ID from the first active Tenant record
#   5. Patches .env in-place (idempotent — safe to re-run)
#   6. Boots: docker compose --profile nids --profile watcher up -d
#   7. Prints a health summary
#
# Requirements:
#   - Docker with Compose v2 installed
#   - Python 3 + Django environment configured (pip install -r backend/requirements.txt)
#   - Running on Linux or WSL2 (Suricata AF_PACKET requires Linux host networking)
# =============================================================================

set -euo pipefail

# -- Colour helpers -----------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}=== $* ===${RESET}"; }

# -- Resolve project root (script lives in <root>/scripts/) ------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
ENV_FILE="${PROJECT_ROOT}/.env"
SURICATA_YAML="${PROJECT_ROOT}/suricata/suricata.yaml"

cd "${PROJECT_ROOT}"

# -- Platform check -----------------------------------------------------------
header "Platform Check"
if [[ "$(uname -s)" != "Linux" ]]; then
    error "Suricata AF_PACKET requires Linux host networking."
    error "On Windows: open WSL2, navigate to this project directory, and re-run."
    exit 1
fi

if grep -qEi "microsoft|wsl" /proc/version 2>/dev/null; then
    warn "Running inside WSL2. Docker Desktop must be running on the Windows host."
    warn "Suricata will sniff the WSL2 virtual eth0 interface (Docker bridge traffic only)."
fi
success "Linux environment confirmed"

# -- Docker check -------------------------------------------------------------
header "Docker Check"
if ! command -v docker &>/dev/null; then
    error "Docker not found. Install Docker Engine or Docker Desktop first."
    exit 1
fi
if ! docker compose version &>/dev/null; then
    error "Docker Compose v2 not found. Update Docker or install the compose plugin."
    exit 1
fi
success "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
success "Compose $(docker compose version --short)"

# -- Step 1: Detect primary network interface ---------------------------------
header "Step 1 - Detecting Primary Network Interface"

detect_interface() {
    # Prefer the interface with the default route
    local iface
    iface=$(ip route show default 2>/dev/null | awk '/default/ {print $5}' | head -1)
    if [[ -n "$iface" ]]; then
        echo "$iface"
        return
    fi
    # Fallback: first UP non-loopback interface
    for candidate in eth0 ens3 ens4 enp0s3 docker0 wlan0 wlp2s0; do
        if ip link show "$candidate" &>/dev/null && \
           [[ "$(cat /sys/class/net/${candidate}/operstate 2>/dev/null)" == "up" ]]; then
            echo "$candidate"
            return
        fi
    done
    # Last resort: any non-loopback UP interface
    ip -o link show up | awk -F': ' '{print $2}' | grep -v lo | head -1
}

IFACE=$(detect_interface)
if [[ -z "$IFACE" ]]; then
    error "Could not detect a primary network interface."
    error "Set it manually in suricata/suricata.yaml under af-packet.interface"
    exit 1
fi
success "Primary interface: ${BOLD}${IFACE}${RESET}"

# -- Step 2: Patch suricata.yaml interface ------------------------------------
header "Step 2 - Patching suricata/suricata.yaml"
if [[ -f "$SURICATA_YAML" ]]; then
    sed -i "s/^  - interface: .*/  - interface: ${IFACE}/" "$SURICATA_YAML"
    success "af-packet interface set to: ${IFACE}"
else
    warn "suricata/suricata.yaml not found -- skipping interface patch"
fi

# -- Step 3: Generate Django service-account JWT ------------------------------
header "Step 3 - Generating Suricata Service-Account JWT"

SURICATA_TOKEN=$(cd "${BACKEND_DIR}" && python - <<'PYEOF'
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")
django.setup()

from authentication.models import User, Tenant
from rest_framework_simplejwt.tokens import RefreshToken
import datetime

email = "suricata@internal"
try:
    tenant = Tenant.objects.filter(is_active=True).first()
    if not tenant:
        print("ERROR:no_active_tenant", file=sys.stderr)
        sys.exit(1)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": "Suricata",
            "last_name":  "Sensor",
            "role":       User.Role.ANALYST,
            "tenant":     tenant,
            "is_active":  True,
        }
    )
    if created:
        user.set_unusable_password()
        user.save()

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    access.set_exp(lifetime=datetime.timedelta(days=365))
    print(str(access))

except Exception as e:
    print(f"ERROR:{e}", file=sys.stderr)
    sys.exit(1)
PYEOF
)

if [[ "$SURICATA_TOKEN" == ERROR:* ]] || [[ -z "$SURICATA_TOKEN" ]]; then
    error "Failed to generate JWT: ${SURICATA_TOKEN}"
    error "Make sure Django migrations are applied: cd backend && python manage.py migrate"
    exit 1
fi
success "JWT generated (${#SURICATA_TOKEN} chars)"

# -- Step 4: Extract DEFAULT_TENANT_ID ----------------------------------------
header "Step 4 - Extracting Default Tenant UUID"

TENANT_ID=$(cd "${BACKEND_DIR}" && python - <<'PYEOF'
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")
django.setup()
from authentication.models import Tenant
t = Tenant.objects.filter(is_active=True).first()
if not t:
    print("ERROR:no_tenant", file=sys.stderr)
    sys.exit(1)
print(str(t.id))
PYEOF
)

if [[ "$TENANT_ID" == ERROR:* ]] || [[ -z "$TENANT_ID" ]]; then
    error "Failed to extract tenant ID. Is the database bootstrapped?"
    error "  cd backend && python bootstrap_db.py"
    exit 1
fi
success "Default tenant UUID: ${TENANT_ID}"

# -- Step 5: Patch .env file --------------------------------------------------
header "Step 5 - Patching .env"

env_set() {
    local key="$1" value="$2"
    if grep -qE "^${key}=" "${ENV_FILE}" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
        info "Updated  ${key}"
    else
        echo "${key}=${value}" >> "${ENV_FILE}"
        info "Appended ${key}"
    fi
}

if [[ ! -f "$ENV_FILE" ]]; then
    warn ".env not found -- copying from .env.example"
    cp "${PROJECT_ROOT}/.env.example" "${ENV_FILE}"
fi

env_set "SURICATA_API_TOKEN"  "${SURICATA_TOKEN}"
env_set "DEFAULT_TENANT_ID"   "${TENANT_ID}"

success ".env patched successfully"

# -- Step 6: Boot the sensor stack --------------------------------------------
header "Step 6 - Starting Sensor Stack (nids + watcher profiles)"
info "docker compose --profile nids --profile watcher up -d"

docker compose --profile nids --profile watcher up -d
COMPOSE_EXIT=$?

if [[ $COMPOSE_EXIT -ne 0 ]]; then
    error "docker compose failed (exit ${COMPOSE_EXIT})"
    error "Check logs: docker compose logs suricata suricata-watcher"
    exit $COMPOSE_EXIT
fi
success "Sensor stack started"

# -- Step 7: Health summary ---------------------------------------------------
header "Step 7 - Health Summary"

sleep 5

check_container() {
    local name="$1"
    local state
    state=$(docker inspect --format='{{.State.Status}}' "$name" 2>/dev/null || echo "missing")
    if [[ "$state" == "running" ]]; then
        success "Container ${name}: running"
    else
        warn "Container ${name}: ${state}"
    fi
}

check_container cybershield_suricata
check_container cybershield_suricata_watcher
check_container cybershield_backend
check_container cybershield_celery
check_container cybershield_beat

echo ""
echo -e "${BOLD}${GREEN}+==================================================+${RESET}"
echo -e "${BOLD}${GREEN}|  CyberShield Live NIDS -- Activation Complete    |${RESET}"
echo -e "${BOLD}${GREEN}+==================================================+${RESET}"
echo ""
echo -e "  Interface:  ${BOLD}${IFACE}${RESET}"
echo -e "  Tenant ID:  ${BOLD}${TENANT_ID}${RESET}"
echo -e "  API Token:  ${BOLD}[set in .env as SURICATA_API_TOKEN]${RESET}"
echo ""
echo -e "  Health endpoint:"
echo -e "  ${CYAN}http://localhost:8000/api/ingestion/status/${RESET}"
echo ""
echo -e "  Live Suricata events:"
echo -e "  ${CYAN}http://localhost:8000/api/ingestion/network-events/?event_source=SURICATA${RESET}"
echo ""
echo -e "  Run end-to-end demo:"
echo -e "  ${BOLD}python scripts/run_live_demo.py${RESET}"
echo ""
echo -e "  Watch live logs:"
echo -e "  ${BOLD}docker compose logs -f suricata suricata-watcher${RESET}"
