# Ansible workshop

## Setup

1. Download and install [Vagrant](https://www.vagrantup.com/) for your platform from [here](https://www.vagrantup.com/downloads.html)
2. Download and install [Virtualbox](https://www.virtualbox.org) for your platform from [here](https://www.virtualbox.org/wiki/Downloads)
3. [Install](https://docs.ansible.com/ansible/latest/intro_installation.html) Ansible for your platform
4. Clone this repository and run "vagrant up"

## Infrastructure

There are 3 [VyOS](https://vyos.io) hosts available:

* hub - 10.0.0.1
* spoke1 - 10.0.0.11
* spoke2 - 10.0.0.12

Run "vagrant ssh <host>" for connecting to specific host.