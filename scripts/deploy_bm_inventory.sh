#!/usr/bin/env bash
set -euo pipefail

source scripts/utils.sh

export INVENTORY_URL=$(get_main_ip)
export INVENTORY_PORT=${INVENTORY_PORT:-6000}
export KUBECONFIG=${KUBECONFIG:-$HOME/.kube/config}
export SERVICE_NAME=bm-inventory
export SERVICE=${SERVICE:-}
export OBJEXP=${OBJEXP:-}
export GIT_REVISION=${GIT_REVISION:-}

print_log "Config firewall"
sudo systemctl start firewalld
sudo firewall-cmd --zone=public --permanent --add-port=${INVENTORY_PORT}/tcp
sudo firewall-cmd --zone=libvirt --permanent --add-port=${INVENTORY_PORT}/tcp
sudo firewall-cmd --reload

print_log "Updating bm_inventory params"
discovery-infra/update_bm_inventory_cm.py
make -C bm-inventory/ deploy-all

print_log "Wait till ${SERVICE_NAME} api is ready"
wait_for_url_and_run "$(minikube service ${SERVICE_NAME} --url -n assisted-installer)" "echo \"waiting for ${SERVICE_NAME}\""

print_log "Starting port forwarding for deployment/${SERVICE_NAME}"

wait_for_url_and_run "http://${INVENTORY_URL}:${INVENTORY_PORT}" "spawn_port_forwarding_command ${SERVICE_NAME} ${INVENTORY_PORT}"

print_log "${SERVICE_NAME} can be reached at http://${INVENTORY_URL}:${INVENTORY_PORT} "
print_log "Done"
