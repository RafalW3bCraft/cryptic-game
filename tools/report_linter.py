#!/usr/bin/env bash
# scripts/preflight.sh
# Run as root (sudo). Blocks outbound access from docker lab bridge network.
set -euo pipefail

LAB_SUBNET="172.28.0.0/16"   # set to the lab-net CIDR used in docker-compose.override.yml
DOCKER_USER_RULE_EXISTS=$(iptables -L DOCKER-USER -n --line-numbers 2>/dev/null || true)

echo "[*] Applying preflight egress block for lab subnet: $LAB_SUBNET"

# Ensure DOCKER-USER exists (docker creates it when starting)
if ! iptables -L DOCKER-USER >/dev/null 2>&1; then
  iptables -N DOCKER-USER || true
fi

# Remove any previous rule matching our marker
iptables -D DOCKER-USER -s "$LAB_SUBNET" -j DROP 2>/dev/null || true

# Insert rule at top to DROP any outbound traffic from lab subnet
iptables -I DOCKER-USER 1 -s "$LAB_SUBNET" -j DROP -m comment --comment "TheFool lab egress block"

echo "[+] Inserted DOCKER-USER DROP for $LAB_SUBNET"

# Verify
echo "[*] DOCKER-USER rules:"
iptables -L DOCKER-USER -n --line-numbers
echo "[*] Preflight complete. To remove egress block: sudo iptables -D DOCKER-USER 1"
