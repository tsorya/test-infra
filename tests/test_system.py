import socket
import paramiko
import libvirt
import subprocess
import os

import pytest

SSH_UESR = 'core'
SSH_KEY = 'ssh_key/key'


@pytest.fixture()
def exposed_services():
    yield {'bm-inventory': 6000, 'ocp-metal-ui': 6008}


@pytest.fixture()
def host_ip():
    yield socket.gethostbyname(socket.gethostname())


@pytest.fixture()
def ssh_conn():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    yield ssh

    ssh.close()


@pytest.fixture()
def communicate_minikube():
    def func(service_name):
        kubeconfig = os.path.expanduser('~/.kube/config')
        command = f'curl $(minikube ip):$(kubectl --kubeconfig={kubeconfig} \
                    get svc/{service_name} -n assisted-installer -o=jsonpath="{{.spec.ports[0].nodePort}}")'

        return subprocess.check_output(command, shell=True).decode()

    yield func


def test_exposed_ports(host_ip, exposed_services):
    for name, port in exposed_services.items():
        socket.create_connection((host_ip, port))


def test_connectivity_from_vms(communicate_minikube, ssh_conn,
                               host_ip, exposed_services):
    conn = libvirt.open('qemu:///system')

    for dom in filter(lambda dom: dom.name().startswith('test-infra-cluster'),
                      conn.listAllDomains()):
        interfaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
        ip = list(interfaces.values())[0]['addrs'][0]['addr']
        ssh_conn.connect(ip, username=SSH_UESR, key_filename=SSH_KEY)

        for name, port in exposed_services.items():
            ssh_stdin, ssh_stdout, ssh_stderr = ssh_conn.exec_command(f"curl {host_ip}:{port}")
            assert communicate_minikube(name) == ''.join(ssh_stdout.readlines())
