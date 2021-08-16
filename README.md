# nodered-charm-k8s

## Description

[Node-RED](https://nodered.org) is a programming tool for wiring together 
hardware devices, APIs and online services in new and interesting ways. It 
provides a browser-based editor that makes it easy to wire together flows 
using the wide range of nodes in the palette that can be deployed to its 
runtime in a single-click.

This charm deploys a basic Node-Red server on the desired port. It provides
an [HTTP interface](https://github.com/juju-solutions/interface-http) with
basic configuration options.

## Development setup

For a local deployment set a [MicroK8s](https://microk8s.io/) environment:

```bash
# Install MicroK8s
$ sudo snap install --classic microk8s
# Wait for MicroK8s to be ready
$ sudo microk8s status --wait-ready
# Enable features required by Juju controller & charm
$ sudo microk8s enable storage dns ingress
# (Optional) Alias kubectl bundled with MicroK8s package
$ sudo snap alias microk8s.kubectl kubectl
# (Optional) Add current user to 'microk8s' group
# This avoid needing to use 'sudo' with the 'microk8s' command
$ sudo usermod -aG microk8s $(whoami)
# Activate the new group (in the current shell only)
# Log out and log back in to make the change system-wide
$ newgrp microk8s
# Install Charmcraft
$ sudo snap install charmcraft
# Install juju
$ sudo snap install --classic juju
# Bootstrap the Juju controller on MicroK8s
$ juju bootstrap microk8s micro
# Add a new model to Juju
$ juju add-model test
```

## Usage

First, get a package with charmcraft.

```bash
$ charmcraft pack
```

Now a .charm file should have been generated. Now juju can deploy the charm.


```bash
$ juju deploy ./nodered_ubuntu-20.04-amd64.charm --resource nodered-image=nodered/node-red:latest
```

Our charm waits for a ingress point. We can provide one using the 
[nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator) charm.


```bash
$ juju deploy nginx-ingress-integrator
$ juju relate nodered nginx-ingress-integrator
```

Check the current juju status.

```bash
$ juju status --color
Model  Controller  Cloud/Region        Version  SLA          Timestamp
test   micro       microk8s/localhost  2.9.10   unsupported  13:23:01+02:00

App                       Version  Status  Scale  Charm                     Store     Channel  Rev  OS          Address         Message
nginx-ingress-integrator           active      1  nginx-ingress-integrator  charmhub  stable    22  kubernetes  10.152.183.254  
nodered                            active      1  nodered                   local                9  kubernetes  10.152.183.9    

Unit                         Workload  Agent  Address       Ports  Message
nginx-ingress-integrator/0*  active    idle   10.1.250.244         Ingress with service IP(s): 10.152.183.115
nodered/0*                   active    idle   10.1.250.243  
```
When both applications are ready, NodeRED will be available on the ingress IP and the port indicated in
the configuration file.

## Actions

# Install-package

Install a node-red package through the node-red-admin API. For example, to install the node-red-dashboard package:

```
$ juju run-action nodered/0 install-package package=node-red-dashboard
Action queued with id: "14"
$ juju show-action-output 14
UnitId: nodered/0
id: "14"
log:
- 2021-08-16 12:23:01 +0200 CEST Module node-red-dashboard installed
results: {}
status: completed
timing:
  completed: 2021-08-16 10:23:01 +0000 UTC
  enqueued: 2021-08-16 10:22:54 +0000 UTC
  started: 2021-08-16 10:22:54 +0000 UTC
```

# Uninstall-package

Uninstall a node-red package through the node-red-admin API.
```
$ juju run-action nodered/0 uninstall-package package=node-red-dashboard
Action queued with id: "26"
$ juju show-action-output 26
UnitId: nodered/0
id: "26"
log:
- 2021-08-16 12:37:02 +0200 CEST Module node-red-dashboard uninstalled
results: {}
status: completed
timing:
  completed: 2021-08-16 10:37:02 +0000 UTC
  enqueued: 2021-08-16 10:36:57 +0000 UTC
  started: 2021-08-16 10:36:59 +0000 UTC
```


## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
