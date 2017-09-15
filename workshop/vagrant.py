#!/usr/bin/env python2.7
"""
Vagrant external inventory script. Automatically finds the IP of the booted vagrant vm(s), and
returns it under the host group 'vagrant'

Example Vagrant configuration using this script:

    config.vm.provision :ansible do |ansible|
      ansible.playbook = "./provision/your_playbook.yml"
      ansible.inventory_file = "./provision/inventory/vagrant.py"
      ansible.verbose = true
    end
"""

# Copyright (C) 2013  Mark Mandel <mark@compoundtheory.com>
#               2015  Igor Khomyakov <homyakov@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Thanks to the spacewalk.py inventory script for giving me the basic structure
# of this.
#

import sys
import os
import os.path
import subprocess
import re
import datetime
from paramiko import SSHConfig
from cStringIO import StringIO
from optparse import OptionParser
from collections import defaultdict
try:
    import json
except:
    import simplejson as json

_group = 'vagrant'  # a default group
_ssh_to_ansible = [('user', 'ansible_ssh_user'),
                   ('hostname', 'ansible_ssh_host'),
                   ('identityfile', 'ansible_ssh_private_key_file'),
                   ('port', 'ansible_ssh_port')]

CACHE_FILE = '/tmp/.vagrant_status'
CACHE_FILE_LIFETIME = 300

# Options
# ------------------------------

parser = OptionParser(usage="%prog [options] --list | --host <machine>")
parser.add_option('--list', default=False, dest="list", action="store_true",
                  help="Produce a JSON consumable grouping of Vagrant servers for Ansible")
parser.add_option('--host', default=None, dest="host",
                  help="Generate additional host specific details for given host for Ansible")
(options, args) = parser.parse_args()

#
# helper functions
#


# get all the ssh configs for all boxes in an array of dictionaries.
def get_ssh_config():
    return dict((k, get_a_ssh_config(k)) for k in list_running_boxes())


# list all the running boxes
def list_running_boxes():

    if os.path.exists(CACHE_FILE) and (int(datetime.datetime.now().strftime('%s')) - os.path.getmtime(CACHE_FILE)) < CACHE_FILE_LIFETIME:
        with open(CACHE_FILE, 'r') as f:
            output = f.read()
    else:
        output = subprocess.check_output(["vagrant", "status"])
        with open(CACHE_FILE, 'w') as f:
            f.write(output)

    boxes = []

    for line in output.split('\n'):
        matcher = re.search("([^\s]+)[\s]+running \(.+", line)
        if matcher:
            boxes.append(matcher.group(1))

    return boxes


# get the ssh config for a single box
def get_a_ssh_config(box_name):
    """Gives back a map of all the machine's ssh configurations"""

    if os.path.exists('/tmp/.ssh_config_' + box_name) and (int(datetime.datetime.now().strftime('%s')) - os.path.getmtime('/tmp/.ssh_config_' + box_name)) < CACHE_FILE_LIFETIME:
        with open('/tmp/.ssh_config_' + box_name, 'r') as f:
            output = f.read()
    else:
        output = subprocess.check_output(["vagrant", "ssh-config", box_name])
        with open('/tmp/.ssh_config_' + box_name, 'w') as f:
            f.write(output)

    config = SSHConfig()
    config.parse(StringIO(output))
    host_config = config.lookup(box_name)

    # man 5 ssh_config:
    # > It is possible to have multiple identity files ...
    # > all these identities will be tried in sequence.
    for id in host_config['identityfile']:
        if os.path.isfile(id):
            host_config['identityfile'] = id


    result = []

    for k, v in _ssh_to_ansible:
        if k == 'port':
            result.append((v, int(host_config[k])))
        else:
            result.append((v, host_config[k]))
    return dict(result)

# List out servers that vagrant has running
# ------------------------------
if options.list:
    ssh_config = get_ssh_config()
    meta = defaultdict(dict)

    for host in ssh_config:
        meta['hostvars'][host] = ssh_config[host]

    print(json.dumps({_group: list(ssh_config.keys()), '_meta': meta}))
    sys.exit(0)

# Get out the host details
# ------------------------------
elif options.host:
    print(json.dumps(get_a_ssh_config(options.host)))
    sys.exit(0)

# Print out help
# ------------------------------
else:
    parser.print_help()
    sys.exit(0)
