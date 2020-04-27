#!/usr/bin/env bash
set -e
set -o pipefail

source create_full_environment.sh
source scripts/assisted_deployment.sh

echo "Starting cluster"
export SET_DNS="y"
export CLUSTER_NAME := ${CLUSTER_NAME:-"test-infra-cluster"}
run_without_os_envs "run_full_flow_with_install"
set_dns
wait_for_cluster
