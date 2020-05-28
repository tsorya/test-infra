#!/usr/bin/python3

import argparse
import os
import time
import utils
import consts
import bm_inventory_api
from logger import log


def run_validate_install_flow(client, cluster_id, kubeconfig_path, kubeconfig_installed_path):
    log.info("Verifying cluster exists")
    cluster = client.cluster_get(cluster_id)
    log.info("Verifying cluster is in %s status", consts.ClusterStatus.INSTALLED)
    if cluster.status != consts.ClusterStatus.INSTALLED:
        log.error("Cluster %s supposed to be in %s status but current status is %s",
                  cluster_id, consts.ClusterStatus.INSTALLED, cluster.status)
        exit(1)

    log.info("Verifying all hosts are in %s status", consts.NodesStatus.INSTALLED)
    masters = [host for host in cluster.hosts if host.role == consts.NodeRoles.MASTER]
    if any(master for master in masters if master.status != consts.NodesStatus.INSTALLED):
        log.error("All masters supposed to be in %s status.\n Failes hosts are: %s ",
                  consts.NodesStatus.INSTALLED,
                  [(master.id, master.status) for master in masters if master.status != consts.NodesStatus.INSTALLED])
        exit(1)
    # TODO add wait for
    log.info("Sleeping for one minute to ")
    time.sleep(30)
    log.info("Downloading kubeconfig from cluster %s", cluster_id)
    client.download_kubeconfig(cluster_id=cluster_id, kubeconfig_path=kubeconfig_installed_path)

    log.info("Verify kubeconfig is ok by running kubectl get nodes")
    kubectl_masters = utils.run_command("kubectl --kubeconfig=%s get nodes | grep master" % kubeconfig_installed_path,
                                        shell=True).splitlines()
    assert(len(kubectl_masters) == len(masters))
    assert(os.path.getsize(kubeconfig_installed_path) > os.path.getsize(kubeconfig_path))


def main():
    if not utils.folder_exists(args.kubeconfig_path_installed):
        log.error("Path to %s doesn't exists. Please create it" % args.kubeconfig_path_installed)
        exit(1)
    if not utils.file_exists(args.kubeconfig_path):
        log.error("Kubeconfig %s doesn't exists." % args.kubeconfig_path)
        exit(1)
    log.info("Creating bm inventory client")
    # if not cluster id is given, reads it from latest run
    if not args.cluster_id:
        args.cluster_id = utils.get_tfvars()["cluster_inventory_id"]
    client = bm_inventory_api.create_client(wait_for_url=False)
    run_validate_install_flow(client=client, cluster_id=args.cluster_id,
                              kubeconfig_path=args.kubeconfig_path,
                              kubeconfig_installed_path=args.kubeconfig_path_installed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run discovery flow')
    parser.add_argument('-id', '--cluster-id', help='Cluster id to install', type=str, default=None)
    parser.add_argument('-k', '--kubeconfig-path', help='Path to debug kubeconfig', type=str,
                        default="build/kubeconfig")
    parser.add_argument('-i', '--kubeconfig-path-installed', help='Path to kubeconfig after installation', type=str,
                        default="build/kubeconfig_installed")
    args = parser.parse_args()
    main()
