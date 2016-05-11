#!/usr/bin/python

"""LogicMonitor Ansible module for managing Collectors, Hosts and Hostgroups
   Copyright (C) 2015  LogicMonitor

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA"""

try:
    import datetime
    import json
    import logging
    import os
    import platform
    import socket
    import subprocess
    import sys
    import urllib
    import urllib2
    from subprocess import Popen
    HAS_LIB = True
except:
    HAS_LIB = False

RETURN = '''
---
success:
    description: flag indicating that execution was successful
    returned: success
    type: boolean
    sample: True
...
'''


DOCUMENTATION = '''
---
module: logicmonitor
short_description: Manage your LogicMonitor account through Ansible Playbooks
description:
    - LogicMonitor is a hosted, full-stack, infrastructure monitoring platform.
    - >
        This module manages hosts, host groups, and collectors within your
        LogicMonitor account.
version_added: "2.2"
author: Ethan Culler-Mayeno, Jeff Wozniak
notes:
  - You must have an existing LogicMonitor account for this module to function.
requirements: ["An existing LogicMonitor account", "Linux"]
options:
    target:
        description:
            - The type of LogicMonitor object you wish to manage.
            - >
                Collector: Perform actions on a LogicMonitor collector
            - >
                Host: Perform actions on a host device
            - >
                Hostgroup:  Perform actions on a LogicMonitor host group
            - >
                NOTE Host and Hostgroup tasks should always be performed via
                local_action. There are no benefits to running these tasks on
                the remote host and doing so will typically cause problems.
            - >
                NOTE Collector tasks require superuser access for
                starting/stopping services. Be sure to run these tasks as root
                or set 'become: yes' for the task.
        required: true
        default: null
        choices: ['collector', 'host', 'datsource', 'hostgroup']
        version_added: "2.2"
    action:
        description:
            - The action you wish to perform on target
            - "Add: Add an object to your LogicMonitor account"
            - "Remove: Remove an object from your LogicMonitor account"
            - >
                "Update: Update properties, description, or groups
                (target=host) for an object in your LogicMonitor account"
            - >
                "SDT: Schedule downtime for an object in your
                LogicMonitor account"
        required: true
        default: null
        choices: ['add', 'remove', 'update', 'sdt']
        version_added: "2.2"
    company:
        description:
            - >
                The LogicMonitor account company name. If you would log in to
                your account at "superheroes.logicmonitor.com" you would
                use "superheroes"
        required: true
        default: null
        version_added: "2.2"
    user:
        description:
            - >
                A LogicMonitor user name. The module will authenticate and
                perform actions on behalf of this user
        required: true
        default: null
        version_added: "2.2"
    password:
        description:
            - The password of the specified LogicMonitor user
        required: true
        default: null
        version_added: "2.2"
    collector:
        description:
            - >
                The fully qualified domain name of a collector in your
                LogicMonitor account.
            - >
                This is required for the creation of a LogicMonitor host
                (target=host action=add)
            - >
                This is required for updating, removing or scheduling downtime
                for hosts if 'displayname' isn't specified
                (target=host action=update action=remove action=sdt)
        required: false
        default: null
        version_added: "2.2"
    hostname:
        description:
            - >
                The hostname of a host in your LogicMonitor account, or the
                desired hostname of a device to manage.
            - Optional for managing hosts (target=host)
        required: false
        default: 'hostname -f'
        version_added: "2.2"
    displayname:
        description:
            - >
                The display name of a host in your LogicMonitor account or the
                desired display name of a device to manage.
            - Optional for managing hosts (target=host)
        required: false
        default: 'hostname -f'
        version_added: "2.2"
    description:
        description:
            - >
                The long text description of the object in your
                LogicMonitor account
            - >
                Optional for managing hosts and host groups
                (target=host or target=hostgroup; action=add or action=update)
        required: false
        default: ""
        version_added: "2.2"
    properties:
        description:
            - >
                A dictionary of properties to set on the LogicMonitor
                host or host group.
            - >
                Optional for managing hosts and host groups
                (target=host or target=hostgroup; action=add or action=update)
            - >
                This parameter will add or update existing properties in your
                LogicMonitor account or
        required: false
        default: {}
        version_added: "2.2"
    groups:
        description:
            - A list of groups that the host should be a member of.
            - >
                Optional for managing hosts
                (target=host; action=add or action=update)
        required: false
        default: []
        version_added: "2.2"
    id:
        description:
            - ID of the datasource to target
            - >
                Required for management of LogicMonitor datasources
                (target=datasource)
        required: false
        default: null
        version_added: "2.2"
    fullpath:
        description:
            - The fullpath of the host group object you would like to manage
            - Recommend running on a single Ansible host
            - >
                Required for management of LogicMonitor host groups
                (target=hostgroup)
        required: false
        default: null
        version_added: "2.2"
    alertenable:
        description:
            - A boolean flag to turn alerting on or off for an object
            - Optional for managing all hosts (action=add or action=update)
        required: false
        default: true
        choices: [true, false]
        version_added: "2.2"
    starttime:
        description:
            - The time that the Scheduled Down Time (SDT) should begin
            - Optional for managing SDT (action=sdt)
            - Y-m-d H:M
        required: false
        default: Now
        version_added: "2.2"
    duration:
        description:
            - The duration (minutes) of the Scheduled Down Time (SDT)
            - Optional for putting an object into SDT (action=sdt)
        required: false
        default: 30
        version_added: "2.2"
...
'''
EXAMPLES = '''

    # example of adding a new LogicMonitor collector to these devices
    ---
    - hosts: collectors
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Deploy/verify LogicMonitor collectors
        become: yes
        logicmonitor:
            target=collector
            action=add
            company={{ company }}
            user={{ user }}
            password={{ password }}

    #example of adding a list of hosts into monitoring
    ---
    - hosts: hosts
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Deploy LogicMonitor Host
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=host
            action=add
            collector='mycompany-Collector'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            groups="/servers/production,/datacenter1"
            properties="{'snmp.community':'secret','dc':'1', 'type':'prod'}"

    #example of putting a datasource in SDT
    ---
    - hosts: localhost
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: SDT a datasource
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=datasource
            action=sdt
            id='123'
            duration=3000
            starttime='2017-03-04 05:06'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'

    #example of creating a hostgroup
    ---
    - hosts: localhost
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Create a host group
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=add
            fullpath='/servers/development'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            properties="{'snmp.community':'commstring', 'type':'dev'}"

    #example of putting a list of hosts into SDT
    ---
    - hosts: hosts
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: SDT hosts
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=host
            action=sdt
            duration=3000
            starttime='2016-11-10 09:08'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            collector='mycompany-Collector'

    #example of putting a host group in SDT
    ---
    - hosts: localhost
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: SDT a host group
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=sdt
            fullpath='/servers/development'
            duration=3000
            starttime='2017-03-04 05:06'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'

    #example of updating a list of hosts
    ---
    - hosts: hosts
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Update a list of hosts
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=host
            action=update
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            collector='mycompany-Collector'
            groups="/servers/production,/datacenter5"
            properties="{'snmp.community':'commstring','dc':'5'}"

    #example of updating a hostgroup
    ---
    - hosts: hosts
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Update a host group
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=update
            fullpath='/servers/development'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            properties="{'snmp.community':'hg', 'type':'dev', 'status':'test'}"

    #example of removing a list of hosts from monitoring
    ---
    - hosts: hosts
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Remove LogicMonitor hosts
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=host
            action=remove
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            collector='mycompany-Collector'

    #example of removing a host group
    ---
    - hosts: hosts
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Remove LogicMonitor development servers hostgroup
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=remove
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            fullpath='/servers/development'
      - name: Remove LogicMonitor servers hostgroup
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=remove
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            fullpath='/servers'
      - name: Remove LogicMonitor datacenter1 hostgroup
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=remove
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            fullpath='/datacenter1'
      - name: Remove LogicMonitor datacenter5 hostgroup
        # All tasks except for target=collector should use local_action
        local_action: >
            logicmonitor
            target=hostgroup
            action=remove
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            fullpath='/datacenter5'

    ### example of removing a new LogicMonitor collector to these devices
    ---
    - hosts: collectors
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Remove LogicMonitor collectors
        become: yes
        logicmonitor:
            target=collector
            action=remove
            company={{ company }}
            user={{ user }}
            password={{ password }}

    #complete example
    ---
    - hosts: localhost
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Create a host group
        local_action: >
            logicmonitor
            target=hostgroup
            action=add
            fullpath='/servers/production/database'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            properties="{'snmp.community':'commstring'}"
      - name: SDT a host group
      local_action: >
        logicmonitor
        target=hostgroup
        action=sdt
        fullpath='/servers/production/web'
        duration=3000
        starttime='2012-03-04 05:06'
        company='{{ company }}'
        user='{{ user }}'
        password='{{ password }}'

    - hosts: collectors
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: Deploy/verify LogicMonitor collectors
        logicmonitor:
            target: collector
            action: add
            company: {{ company }}
            user: {{ user }}
            password: {{ password }}
      - name: Place LogicMonitor collectors into 30 minute Scheduled downtime
        logicmonitor: target=collector action=sdt company={{ company }}
            user={{ user }} password={{ password }}
      - name: Deploy LogicMonitor Host
        local_action: >
            logicmonitor
            target=host
            action=add
            collector=agent1.ethandev.com
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            properties="{'snmp.community':'commstring', 'dc':'1'}"
            groups="/servers/production/collectors, /datacenter1"

    - hosts: database-servers
      remote_user: '{{ username }}'
      vars:
        company: 'mycompany'
        user: 'myusername'
        password: 'mypassword'
      tasks:
      - name: deploy logicmonitor hosts
        local_action: >
            logicmonitor
            target=host
            action=add
            collector=monitoring.dev.com
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
            properties="{'snmp.community':'commstring', 'type':'db', 'dc':'1'}"
            groups="/servers/production/database, /datacenter1"
      - name: schedule 5 hour downtime for 2012-11-10 09:08
        local_action: >
            logicmonitor
            target=host
            action=sdt
            duration=3000
            starttime='2012-11-10 09:08'
            company='{{ company }}'
            user='{{ user }}'
            password='{{ password }}'
'''


class LogicMonitor(object):

    def __init__(self, module, **params):
        self.__version__ = "1.0-python"

        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Instantiating LogicMonitor object")

        self.check_mode = False
        self.company = params["company"]
        self.user = params["user"]
        self.password = params["password"]
        self.fqdn = socket.getfqdn()
        self.lm_url = "logicmonitor.com/santaba"

        # Grab the Ansible module if provided
        try:
            self.module = module
            self.urlopen = open_url  # use the ansible provided open_url
            self.__version__ = self.__version__ + "-ansible-module"
        except:
            self.module = None
            self.urlopen = urllib2.urlopen

    def rpc(self, action, params):
        """Make a call to the LogicMonitor RPC library
        and return the response"""
        logging.debug("Running LogicMonitor.rpc")

        param_str = urllib.urlencode(params)
        creds = urllib.urlencode(
            {"c": self.company,
                "u": self.user,
                "p": self.password})

        if param_str:
            param_str = param_str + "&"

        param_str = param_str + creds

        try:
            url = ("https://{0}.{1}/rpc/{2}?{3}"
                   .format(self.company, self.lm_url, action, param_str))

            # Set custom LogicMonitor header with version
            headers = {"X-LM-User-Agent": self.__version__}

            # Set headers dependent on Ansible or normal usage
            if self.module is not None:
                f = self.urlopen(url, headers=headers)
            else:
                req = urllib2.Request(url)
                req.add_header("X-LM-User-Agent", self.__version__)
                f = self.urlopen(req)

            raw = f.read()
            resp = json.loads(raw)
            if resp["status"] == 403:
                logging.debug("Authentication failed.")
                self.fail(msg="Error: {0}".format(resp["errmsg"]))
            else:
                return raw
        except IOError, ioe:
            logging.debug(ioe)
            self.fail(msg="Error: Unknown exception making RPC call")

    def do(self, action, params):
        """Make a call to the LogicMonitor
         server \"do\" function"""
        logging.debug("Running LogicMonitor.do...")

        param_str = urllib.urlencode(params)
        creds = (urllib.urlencode(
            {"c": self.company,
                "u": self.user,
                "p": self.password}))

        if param_str:
            param_str = param_str + "&"
        param_str = param_str + creds

        try:
            logging.debug("Attempting to open URL: " +
                          "https://{0}.{1}/do/{2}?{3}"
                          .format(self.company,
                                  self.lm_url,
                                  action,
                                  param_str))
            f = self.urlopen(
                "https://{0}.{1}/do/{2}?{3}"
                .format(self.company, self.lm_url, action, param_str))
            return f.read()
        except IOError, ioe:
            logging.debug("Error opening URL. {0}".format(ioe))
            self.fail("Unknown exception opening URL")

    def get_collectors(self):
        """Returns a JSON object containing a list of
        LogicMonitor collectors"""
        logging.debug("Running LogicMonitor.get_collectors...")

        logging.debug("Making RPC call to 'getAgents'")
        resp = self.rpc("getAgents", {})
        resp_json = json.loads(resp)

        if resp_json["status"] is 200:
            logging.debug("RPC call succeeded")
            return resp_json["data"]
        else:
            self.fail(msg=resp)

    def get_host_by_hostname(self, hostname, collector):
        """Returns a host object for the host matching the
        specified hostname"""
        logging.debug("Running LogicMonitor.get_host_by_hostname...")

        logging.debug("Looking for hostname {0}".format(hostname))
        logging.debug("Making RPC call to 'getHosts'")
        hostlist_json = json.loads(self.rpc("getHosts", {"hostGroupId": 1}))

        if collector:
            if hostlist_json["status"] == 200:
                logging.debug("RPC call succeeded")

                hosts = hostlist_json["data"]["hosts"]

                logging.debug(
                    "Looking for host matching: hostname {0} and collector {1}"
                    .format(hostname, collector["id"]))

                for host in hosts:
                    if (host["hostName"] == hostname and
                       host["agentId"] == collector["id"]):

                        logging.debug("Host match found")
                        return host
                logging.debug("No host match found")
                return None
            else:
                logging.debug("RPC call failed")
                logging.debug(hostlist_json)
        else:
            logging.debug("No collector specified")
            return None

    def get_host_by_displayname(self, displayname):
        """Returns a host object for the host matching the
        specified display name"""
        logging.debug("Running LogicMonitor.get_host_by_displayname...")

        logging.debug("Looking for displayname {0}".format(displayname))
        logging.debug("Making RPC call to 'getHost'")
        host_json = (json.loads(self.rpc("getHost",
                                {"displayName": displayname})))

        if host_json["status"] == 200:
            logging.debug("RPC call succeeded")
            return host_json["data"]
        else:
            logging.debug("RPC call failed")
            logging.debug(host_json)
            return None

    def get_collector_by_description(self, description):
        """Returns a JSON collector object for the collector
        matching the specified FQDN (description)"""
        logging.debug("Running LogicMonitor.get_collector_by_description...")

        collector_list = self.get_collectors()
        if collector_list is not None:
            logging.debug("Looking for collector with description {0}"
                          .format(description))
            for collector in collector_list:
                if collector["description"] == description:
                    logging.debug("Collector match found")
                    return collector
        logging.debug("No collector match found")
        return None

    def get_group(self, fullpath):
        """Returns a JSON group object for the group matching the
        specified path"""
        logging.debug("Running LogicMonitor.get_group...")

        logging.debug("Making RPC call to getHostGroups")
        resp = json.loads(self.rpc("getHostGroups", {}))

        if resp["status"] == 200:
            logging.debug("RPC called succeeded")
            groups = resp["data"]

            logging.debug("Looking for group matching {0}".format(fullpath))
            for group in groups:
                if group["fullPath"] == fullpath.lstrip('/'):
                    logging.debug("Group match found")
                    return group

            logging.debug("No group match found")
            return None
        else:
            logging.debug("RPC call failed")
            logging.debug(resp)

        return None

    def create_group(self, fullpath):
        """Recursively create a path of host groups.
        Returns the id of the newly created hostgroup"""
        logging.debug("Running LogicMonitor.create_group...")

        res = self.get_group(fullpath)
        if res:
            logging.debug("Group {0} exists.".format(fullpath))
            return res["id"]

        if fullpath == "/":
            logging.debug("Specified group is root. Doing nothing.")
            return 1
        else:
            logging.debug("Creating group named {0}".format(fullpath))
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            parentpath, name = fullpath.rsplit('/', 1)
            parentgroup = self.get_group(parentpath)

            parentid = 1

            if parentpath == "":
                parentid = 1
            elif parentgroup:
                parentid = parentgroup["id"]
            else:
                parentid = self.create_group(parentpath)

            h = None

            # Determine if we're creating a group from host or hostgroup class
            if hasattr(self, '_build_host_group_hash'):
                h = self._build_host_group_hash(
                    fullpath,
                    self.description,
                    self.properties,
                    self.alertenable)
                h["name"] = name
                h["parentId"] = parentid
            else:
                h = {"name": name,
                     "parentId": parentid,
                     "alertEnable": True,
                     "description": ""}

            logging.debug("Making RPC call to 'addHostGroup'")
            resp = json.loads(
                self.rpc("addHostGroup", h))

            if resp["status"] == 200:
                logging.debug("RPC call succeeded")
                return resp["data"]["id"]
            elif resp["errmsg"] == "The record already exists":
                logging.debug("The hostgroup already exists")
                group = self.get_group(fullpath)
                return group["id"]
            else:
                logging.debug("RPC call failed")
                self.fail(
                    msg="Error: unable to create new hostgroup \"{0}\".\n{1}"
                    .format(name, resp["errmsg"]))

    def fail(self, msg):
        logging.warning(msg)

        # Use Ansible module functions if provided
        try:
            self.module.fail_json(msg=msg, changed=self.change, failed=True)
        except:
            logging.debug(msg)

    def exit(self, changed):
        logging.debug("Changed: {0}".format(changed))

        # Use Ansible module functions if provided
        try:
            self.module.exit_json(changed=changed, success=True)
        except:
            print("Changed: {0}".format(changed))

    def output_info(self, info):
        try:
            logging.debug("Registering properties as Ansible facts")
            self.module.exit_json(changed=False, ansible_facts=info)
        except:
            logging.debug("Properties: {0}".format(info))


class Service(object):
    @staticmethod
    def getStatus(name):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Retrieving status of service {0}".format(name))

        ret = -1

        startType = Service._getType(name)

        # Determine how to get the status of the service
        if startType == "init.d":
            p = (Popen(["/etc/init.d/{0}".format(name), "status"],
                       stdout=subprocess.PIPE))
            ret, err = p.communicate()
        elif startType == "service":
            p = (Popen(["service", name, "status"],
                       stdout=subprocess.PIPE))
            ret, err = p.communicate()
        else:
            ret = "Unknown error getting status for service {0}".format(name)

        return ret

    @staticmethod
    def doAction(name, action):
        logging.debug("Performing {0} on service {1}".format(action, name))

        startType = Service._getType(name)

        ret = -1

        # Determine how to perform the action on the service
        if startType == "init.d":
            p = (Popen(["/etc/init.d/{0}".format(name), action],
                       stdout=subprocess.PIPE))
            msg = p.communicate()
            ret = p.returncode
        elif startType == "service":
            p = (Popen(["service", name, action],
                       stdout=subprocess.PIPE))
            msg = p.communicate()
            ret = p.returncode

        else:
            ret = ("Unknown error performing '{0}' on service {1}"
                   .format(action, name))

        return (ret, msg)

    @staticmethod
    def _getType(name):
        logging.debug("Getting service {0} control type".format(name))

        try:
            p = (Popen(["/etc/init.d/{0}".format(name), "status"],
                       stdout=subprocess.PIPE))
            ret = p.communicate()
            result = p.returncode

            if result == 0 or result == 1:
                logging.debug("Service control is via init.d")
                return "init.d"
        except:
            result = -1

        try:
            p = (Popen(["service", name, "status"],
                       stdout=subprocess.PIPE))
            ret = p.communicate()
            result = p.returncode

            if result == 0 or result == 1:
                logging.debug("Service control is via service")
                return "service"
        except:
            ret = result

        return ret


class Collector(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor Collector object"""
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Instantiating Collector object")
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **params)

        if self.params['description']:
            self.description = self.params['description']
        else:
            self.description = self.fqdn

        self.info = self._get()
        self.installdir = "/usr/local/logicmonitor"
        self.platform = platform.system()
        self.is_64bits = sys.maxsize > 2**32
        self.duration = self.params['duration']
        self.starttime = self.params['starttime']

        if self.info is None:
            self.id = None
        else:
            self.id = self.info["id"]

    def create(self):
        """Idempotent function to make sure that there is
        a running collector installed and registered"""
        logging.debug("Running Collector.create...")

        self._create()
        self.get_installer_binary()
        self.install()
        self.start()

    def remove(self):
        """Idempotent function to make sure that there is
        not a running collector installed and registered"""
        logging.debug("Running Collector.destroy...")

        self.stop()
        self._unreigster()
        self.uninstall()

    def get_installer_binary(self):
        """Download the LogicMonitor collector installer binary"""
        logging.debug("Running Collector.get_installer_binary...")

        arch = 32

        if self.is_64bits:
            logging.debug("64 bit system")
            arch = 64
        else:
            logging.debug("32 bit system")

        if self.platform == "Linux" and self.id is not None:
            logging.debug("Platform is Linux")
            logging.debug("Agent ID is {0}".format(self.id))

            installfilepath = (self.installdir +
                               "/logicmonitorsetup" +
                               str(self.id) + "_" + str(arch) +
                               ".bin")

            logging.debug("Looking for existing installer at {0}"
                          .format(installfilepath))
            if not os.path.isfile(installfilepath):
                logging.debug("No previous installer found")
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                logging.debug("Downloading installer file")
                try:
                    f = open(installfilepath, "w")
                    installer = (self.do("logicmonitorsetup",
                                         {"id": self.id,
                                          "arch": arch}))
                    f.write(installer)
                    f.closed
                except:
                    self.fail(msg="Unable to open installer file for writing")
                    f.closed
            else:
                logging.debug("Collector installer already exists")
                return installfilepath

        elif self.id is None:
            self.fail(
                msg="Error: There is currently no collector " +
                    "associated with this device. To download " +
                    " the installer, first create a collector " +
                    "for this device.")
        elif self.platform != "Linux":
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device.")
        else:
            self.fail(
                msg="Error: Unable  to retrieve the installer from the server")

    def install(self):
        """Execute the LogicMonitor installer if not
        already installed"""
        logging.debug("Running Collector.install...")

        if self.platform == "Linux":
            logging.debug("Platform is Linux")

            installer = self.get_installer_binary()

            if self.info is None:
                logging.debug("Retriving collector information")
                self.info = self._get()

            if not os.path.exists(self.installdir + "/agent"):
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                logging.debug("Setting installer file permissions")
                os.chmod(installer, 0744)

                logging.debug("Executing installer")
                p = (Popen([installer, "-y"],
                           stdout=subprocess.PIPE))
                ret, err = p.communicate()

                if p.returncode != 0:
                    (self.fail(
                        msg="Error: Unable to install collector: {0}"
                            .format(err)))
                else:
                    logging.debug("Collector installed successfully")
            else:
                logging.debug("Collector already installed")
        else:
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device")

    def uninstall(self):
        """Uninstall LogicMontitor collector from the system"""
        logging.debug("Running Collector.uninstall...")

        uninstallfile = self.installdir + "/agent/bin/uninstall.pl"

        if os.path.isfile(uninstallfile):
            logging.debug("Collector uninstall file exists")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            logging.debug("Running collector uninstaller")
            p = (Popen([uninstallfile],
                       stdout=subprocess.PIPE))
            ret, err = p.communicate()

            if p.returncode != 0:
                self.fail(
                    msg="Error: Unable to uninstall collector: {0}"
                    .format(err))
            else:
                logging.debug("Collector successfully uninstalled")
        else:
            if os.path.exists(self.installdir + "/agent"):
                (self.fail(
                    msg="Unable to uninstall LogicMonitor " +
                    "Collector. Can not find LogicMonitor " +
                    "uninstaller."))

    def start(self):
        """Start the LogicMonitor collector"""
        logging.debug("Running Collector.start")

        if self.platform == "Linux":
            logging.debug("Platform is Linux")

            output = Service.getStatus("logicmonitor-agent")
            if "is running" not in output:
                logging.debug("Service logicmonitor-agent is not running")
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                logging.debug("Starting logicmonitor-agent service")
                (output, err) = Service.doAction("logicmonitor-agent", "start")

                if output != 0:
                    self.fail(
                        msg="Error: Failed starting logicmonitor-agent " +
                            "service. {0}".format(err))

            output = Service.getStatus("logicmonitor-watchdog")

            if "is running" not in output:
                logging.debug("Service logicmonitor-watchdog is not running")
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                logging.debug("Starting logicmonitor-watchdog service")
                (output, err) = Service.doAction("logicmonitor-watchdog",
                                                 "start")

                if output != 0:
                    self.fail(
                        msg="Error: Failed starting logicmonitor-watchdog " +
                            "service. {0}".format(err))
        else:
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device.")

    def restart(self):
        """Restart the LogicMonitor collector"""
        logging.debug("Running Collector.restart...")

        if self.platform == "Linux":
            logging.debug("Platform is Linux")

            logging.debug("Restarting logicmonitor-agent service")
            (output, err) = Service.doAction("logicmonitor-agent", "restart")

            if output != 0:
                self.fail(
                    msg="Error: Failed starting logicmonitor-agent " +
                        "service. {0}".format(err))

            logging.debug("Restarting logicmonitor-watchdog service")
            (output, err) = Service.doAction("logicmonitor-watchdog",
                                             "restart")

            if output != 0:
                self.fail(
                    msg="Error: Failed starting logicmonitor-watchdog " +
                        "service. {0}".format(err))
        else:
            (self.fail(
                msg="Error: LogicMonitor Collector must be installed " +
                    "on a Linux device."))

    def stop(self):
        """Stop the LogicMonitor collector"""
        logging.debug("Running Collector.stop...")

        if self.platform == "Linux":
            logging.debug("Platform is Linux")

            output = Service.getStatus("logicmonitor-agent")

            if "is running" in output:
                logging.debug("Service logicmonitor-agent is running")
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                logging.debug("Stopping service logicmonitor-agent")
                (output, err) = Service.doAction("logicmonitor-agent", "stop")

                if output != 0:
                    self.fail(
                        msg="Error: Failed stopping logicmonitor-agent " +
                            "service. {0}".format(err))

            output = Service.getStatus("logicmonitor-watchdog")

            if "is running" in output:
                logging.debug("Service logicmonitor-watchdog is running")
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                logging.debug("Stopping service logicmonitor-watchdog")
                (output, err) = Service.doAction("logicmonitor-watchdog",
                                                 "stop")

                if output != 0:
                    self.fail(
                        msg="Error: Failed stopping logicmonitor-watchdog " +
                            "service. {0}".format(err))
        else:
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device.")

    def sdt(self):
        """Create a scheduled down time
        (maintenance window) for this host"""
        logging.debug("Running Collector.sdt...")

        logging.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        duration = self.duration
        starttime = self.starttime
        offsetstart = starttime

        if starttime:
            logging.debug("Start time specified")
            start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            offsetstart = start
        else:
            logging.debug("No start time specified. Using default.")
            start = datetime.datetime.utcnow()

            # Use user UTC offset
            logging.debug("Making RPC call to 'getTimeZoneSetting'")
            accountresp = json.loads(self.rpc("getTimeZoneSetting", {}))

            if accountresp["status"] == 200:
                logging.debug("RPC call succeeded")

                offset = accountresp["data"]["offset"]
                offsetstart = start + datetime.timedelta(0, offset)
            else:
                self.fail(msg="Error: Unable to retrieve timezone offset")

        offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

        h = {"agentId": self.id,
             "type": 1,
             "notifyCC": True,
             "year": offsetstart.year,
             "month": offsetstart.month-1,
             "day": offsetstart.day,
             "hour": offsetstart.hour,
             "minute": offsetstart.minute,
             "endYear": offsetend.year,
             "endMonth": offsetend.month-1,
             "endDay": offsetend.day,
             "endHour": offsetend.hour,
             "endMinute": offsetend.minute}

        logging.debug("Making RPC call to 'setAgentSDT'")
        resp = json.loads(self.rpc("setAgentSDT", h))

        if resp["status"] == 200:
            logging.debug("RPC call succeeded")
            return resp["data"]
        else:
            logging.debug("RPC call failed")
            self.fail(msg=resp["errmsg"])

    def site_facts(self):
        """Output current properties information for the Collector"""
        logging.debug("Running Collector.site_facts...")

        if self.info:
            logging.debug("Collector exists")
            props = self.get_properties(True)

            self.output_info(props)
        else:
            self.fail(msg="Error: Collector doesn't exit.")

    def _get(self):
        """Returns a JSON object representing this collector"""
        logging.debug("Running Collector._get...")
        collector_list = self.get_collectors()

        if collector_list is not None:
            logging.debug("Collectors returned")
            for collector in collector_list:
                if collector["description"] == self.description:
                    return collector
        else:
            logging.debug("No collectors returned")
            return None

    def _create(self):
        """Create a new collector in the associated
        LogicMonitor account"""
        logging.debug("Running Collector._create...")

        if self.platform == "Linux":
            logging.debug("Platform is Linux")
            ret = self.info or self._get()

            if ret is None:
                self.change = True
                logging.debug("System changed")

                if self.check_mode:
                    self.exit(changed=True)

                h = {"autogen": True,
                     "description": self.description}

                logging.debug("Making RPC call to 'addAgent'")
                create = (json.loads(self.rpc("addAgent", h)))

                if create["status"] is 200:
                    logging.debug("RPC call succeeded")
                    self.info = create["data"]
                    self.id = create["data"]["id"]
                    return create["data"]
                else:
                    self.fail(msg=create["errmsg"])
            else:
                self.info = ret
                self.id = ret["id"]
                return ret
        else:
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device.")

    def _unreigster(self):
        """Delete this collector from the associated
        LogicMonitor account"""
        logging.debug("Running Collector._unreigster...")

        if self.info is None:
            logging.debug("Retrieving collector information")
            self.info = self._get()

        if self.info is not None:
            logging.debug("Collector found")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            logging.debug("Making RPC call to 'deleteAgent'")
            delete = json.loads(self.rpc("deleteAgent",
                                         {"id": self.id}))

            if delete["status"] is 200:
                logging.debug("RPC call succeeded")
                return delete
            else:
                # The collector couldn't unregister. Start the service again
                logging.debug("Error unregistering collecting. {0}"
                              .format(delete["errmsg"]))
                logging.debug("The collector service will be restarted")

                self.start()
                self.fail(msg=delete["errmsg"])
        else:
            logging.debug("Collector not found")
            return None


class Host(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor host object"""
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Instantiating Host object")
        self.change = False
        self.params = params
        self.collector = None

        LogicMonitor.__init__(self, module, **self.params)

        if self.params["hostname"]:
            logging.debug("Hostname is {0}".format(self.params["hostname"]))
            self.hostname = self.params['hostname']
        else:
            logging.debug("No hostname specified. Using {0}".format(self.fqdn))
            self.hostname = self.fqdn

        if self.params["displayname"]:
            logging.debug("Display name is {0}"
                          .format(self.params["displayname"]))
            self.displayname = self.params['displayname']
        else:
            logging.debug("No display name specified. Using {0}"
                          .format(self.fqdn))
            self.displayname = self.fqdn

        # Attempt to host information via display name of host name
        logging.debug("Attempting to find host by displayname {0}"
                      .format(self.displayname))
        info = self.get_host_by_displayname(self.displayname)

        if info is not None:
            logging.debug("Host found by displayname")
            # Used the host information to grab the collector description
            # if not provided
            if (not hasattr(self.params, "collector") and
               "agentDescription" in info):
                logging.debug("Setting collector from host response. " +
                              "Collector {0}".format(info["agentDescription"]))
                self.params["collector"] = info["agentDescription"]
        else:
            logging.debug("Host not found by displayname")

        # At this point, a valid collector description is required for success
        # Check that the description exists or fail
        if self.params["collector"]:
            logging.debug("Collector specified is {0}"
                          .format(self.params["collector"]))
            self.collector = (self.get_collector_by_description(
                              self.params["collector"]))
        else:
            self.fail(msg="No collector specified.")

        # If the host wasn't found via displayname, attempt by hostname
        if info is None:
            logging.debug("Attempting to find host by hostname {0}"
                          .format(self.hostname))
            info = self.get_host_by_hostname(self.hostname, self.collector)

        self.info = info
        self.properties = self.params["properties"]
        self.description = self.params["description"]
        self.starttime = self.params["starttime"]
        self.duration = self.params["duration"]
        self.alertenable = self.params["alertenable"]
        if self.params["groups"] is not None:
            self.groups = self._strip_groups(self.params["groups"])
        else:
            self.groups = None

    def create(self):
        """Idemopotent function to create if missing,
        update if changed, or skip"""
        logging.debug("Running Host.create...")

        self.update()

    def get_properties(self):
        """Returns a hash of the properties
        associated with this LogicMonitor host"""
        logging.debug("Running Host.get_properties...")

        if self.info:
            logging.debug("Making RPC call to 'getHostProperties'")
            properties_json = (json.loads(self.rpc("getHostProperties",
                                          {'hostId': self.info["id"],
                                           "filterSystemProperties": True})))

            if properties_json["status"] == 200:
                logging.debug("RPC call succeeded")
                return properties_json["data"]
            else:
                logging.debug("Error: there was an issue retrieving the " +
                              "host properties")
                logging.debug(properties_json["errmsg"])

                self.fail(msg=properties_json["status"])
        else:
            logging.debug("Unable to find LogicMonitor host which " +
                          "matches {0} ({1})"
                          .format(self.displayname, self.hostname))
            return None

    def set_properties(self, propertyhash):
        """update the host to have the properties
        contained in the property hash"""
        logging.debug("Running Host.set_properties...")
        logging.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        logging.debug("Assigning property hash to host object")
        self.properties = propertyhash

    def add(self):
        """Add this device to monitoring
        in your LogicMonitor account"""
        logging.debug("Running Host.add...")

        if self.collector and not self.info:
            logging.debug("Host not registered. Registering.")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            h = self._build_host_hash(
                self.hostname,
                self.displayname,
                self.collector,
                self.description,
                self.groups,
                self.properties,
                self.alertenable)

            logging.debug("Making RPC call to 'addHost'")
            resp = json.loads(self.rpc("addHost", h))

            if resp["status"] == 200:
                logging.debug("RPC call succeeded")
                return resp["data"]
            else:
                logging.debug("RPC call failed")
                logging.debug(resp)
                return resp["errmsg"]
        elif self.collector is None:
            self.fail(msg="Specified collector doesn't exist")
        else:
            logging.debug("Host already registered")

    def update(self):
        """This method takes changes made to this host
        and applies them to the corresponding host
        in your LogicMonitor account."""
        logging.debug("Running Host.update...")

        if self.info:
            logging.debug("Host already registed")
            if self.is_changed():
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                h = (self._build_host_hash(
                     self.hostname,
                     self.displayname,
                     self.collector,
                     self.description,
                     self.groups,
                     self.properties,
                     self.alertenable))
                h["id"] = self.info["id"]
                h["opType"] = "replace"

                logging.debug("Making RPC call to 'updateHost'")
                resp = json.loads(self.rpc("updateHost", h))

                if resp["status"] == 200:
                    logging.debug("RPC call succeeded")
                else:
                    logging.debug("RPC call failed")
                    self.fail(msg="Error: unable to update the host.")
            else:
                logging.debug("Host properties match supplied properties. " +
                              "No changes to make.")
                return self.info
        else:
            logging.debug("Host not registed. Registering")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            return self.add()

    def remove(self):
        """Remove this host from your LogicMonitor account"""
        logging.debug("Running Host.remove...")

        if self.info:
            logging.debug("Host registered")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            logging.debug("Making RPC call to 'deleteHost'")
            resp = json.loads(self.rpc("deleteHost",
                                       {"hostId": self.info["id"],
                                        "deleteFromSystem": True,
                                        "hostGroupId": 1}))

            if resp["status"] == 200:
                logging.debug(resp)
                logging.debug("RPC call succeeded")
                return resp
            else:
                logging.debug("RPC call failed")
                logging.debug(resp)
                self.fail(msg=resp["errmsg"])

        else:
            logging.debug("Host not registered")

    def is_changed(self):
        """Return true if the host doesn't
        match the LogicMonitor account"""
        logging.debug("Running Host.is_changed")

        ignore = ['system.categories', 'snmp.version']

        hostresp = self.get_host_by_displayname(self.displayname)

        if hostresp is None:
            hostresp = self.get_host_by_hostname(self.hostname, self.collector)

        if hostresp:
            logging.debug("Comparing simple host properties")
            if hostresp["alertEnable"] != self.alertenable:
                return True

            if hostresp["description"] != self.description:
                return True

            if hostresp["displayedAs"] != self.displayname:
                return True

            if (self.collector and
               hasattr(self.collector, "id") and
               hostresp["agentId"] != self.collector["id"]):
                return True

            logging.debug("Comparing groups.")
            if self._compare_groups(hostresp) is True:
                return True

            propresp = self.get_properties()

            if propresp:
                logging.debug("Comparing properties.")
                if self._compare_props(propresp, ignore) is True:
                    return True
            else:
                self.fail(
                    msg="Error: Unknown error retrieving host properties")

            return False
        else:
            self.fail(msg="Error: Unknown error retrieving host information")

    def sdt(self):
        """Create a scheduled down time
        (maintenance window) for this host"""
        logging.debug("Running Host.sdt...")
        if self.info:
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            duration = self.duration
            starttime = self.starttime
            offset = starttime

            if starttime:
                logging.debug("Start time specified")
                start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
                offsetstart = start
            else:
                logging.debug("No start time specified. Using default.")
                start = datetime.datetime.utcnow()

                # Use user UTC offset
                logging.debug("Making RPC call to 'getTimeZoneSetting'")
                accountresp = (json.loads(self.rpc("getTimeZoneSetting", {})))

                if accountresp["status"] == 200:
                    logging.debug("RPC call succeeded")

                    offset = accountresp["data"]["offset"]
                    offsetstart = start + datetime.timedelta(0, offset)
                else:
                    self.fail(
                        msg="Error: Unable to retrieve timezone offset")

            offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

            h = {"hostId": self.info["id"],
                 "type": 1,
                 "year": offsetstart.year,
                 "month": offsetstart.month - 1,
                 "day": offsetstart.day,
                 "hour": offsetstart.hour,
                 "minute": offsetstart.minute,
                 "endYear": offsetend.year,
                 "endMonth": offsetend.month - 1,
                 "endDay": offsetend.day,
                 "endHour": offsetend.hour,
                 "endMinute": offsetend.minute}

            logging.debug("Making RPC call to 'setHostSDT'")
            resp = (json.loads(self.rpc("setHostSDT", h)))

            if resp["status"] == 200:
                logging.debug("RPC call succeeded")
                return resp["data"]
            else:
                logging.debug("RPC call failed")
                self.fail(msg=resp["errmsg"])
        else:
            self.fail(msg="Error: Host doesn't exit.")

    def site_facts(self):
        """Output current properties information for the Host"""
        logging.debug("Running Host.site_facts...")

        if self.info:
            logging.debug("Host exists")
            props = self.get_properties()

            self.output_info(props)
        else:
            self.fail(msg="Error: Host doesn't exit.")

    def _build_host_hash(self,
                         hostname,
                         displayname,
                         collector,
                         description,
                         groups,
                         properties,
                         alertenable):
        """Return a property formated hash for the
        creation of a host using the rpc function"""
        logging.debug("Running Host._build_host_hash...")

        h = {}
        h["hostName"] = hostname
        h["displayedAs"] = displayname
        h["alertEnable"] = alertenable

        if collector:
            logging.debug("Collector property exists")
            h["agentId"] = collector["id"]
        else:
            self.fail(
                msg="Error: No collector found. Unable to build host hash.")

        if description:
            h["description"] = description

        if groups is not None and groups is not []:
            logging.debug("Group property exists")
            groupids = ""

            for group in groups:
                groupids = groupids + str(self.create_group(group)) + ","

            h["hostGroupIds"] = groupids.rstrip(',')

        if properties is not None and properties is not {}:
            logging.debug("Properties hash exists")
            propnum = 0
            for key, value in properties.iteritems():
                h["propName{0}".format(str(propnum))] = key
                h["propValue{0}".format(str(propnum))] = value
                propnum = propnum + 1

        return h

    def _verify_property(self, propname):
        """Check with LogicMonitor server to
        verify property is unchanged"""
        logging.debug("Running Host._verify_property...")

        if self.info:
            logging.debug("Host is registered")
            if propname not in self.properties:
                logging.debug("Property {0} does not exist".format(propname))
                return False
            else:
                logging.debug("Property {0} exists".format(propname))
                h = {"hostId": self.info["id"],
                     "propName0": propname,
                     "propValue0": self.properties[propname]}

                logging.debug("Making RCP call to 'verifyProperties'")
                resp = json.loads(self.rpc('verifyProperties', h))

                if resp["status"] == 200:
                    logging.debug("RPC call succeeded")
                    return resp["data"]["match"]
                else:
                    self.fail(
                        msg="Error: unable to get verification " +
                            "from server.\n%s" % resp["errmsg"])
        else:
            self.fail(
                msg="Error: Host doesn't exist. Unable to verify properties")

    def _compare_groups(self, hostresp):
        """Function to compare the host's current
        groups against provided groups"""
        logging.debug("Running Host._compare_groups")

        g = []
        fullpathinids = hostresp["fullPathInIds"]
        logging.debug("Building list of groups")
        for path in fullpathinids:
            if path != []:
                h = {'hostGroupId': path[-1]}

                hgresp = json.loads(self.rpc("getHostGroup", h))

                if (hgresp["status"] == 200 and
                   hgresp["data"]["appliesTo"] == ""):

                    g.append(path[-1])

        if self.groups is not None:
            logging.debug("Comparing group lists")
            for group in self.groups:
                groupjson = self.get_group(group)

                if groupjson is None:
                    logging.debug("Group mismatch. No result.")
                    return True
                elif groupjson['id'] not in g:
                    logging.debug("Group mismatch. ID doesn't exist.")
                    return True
                else:
                    g.remove(groupjson['id'])

            if g != []:
                logging.debug("Group mismatch. New ID exists.")
                return True
            logging.debug("Groups match")

    def _compare_props(self, propresp, ignore):
        """Function to compare the host's current
        properties against provided properties"""
        logging.debug("Running Host._compare_props...")
        p = {}

        logging.debug("Creating list of properties")
        for prop in propresp:
            if prop["name"] not in ignore:
                if ("*******" in prop["value"] and
                   self._verify_property(prop["name"])):
                    p[prop["name"]] = self.properties[prop["name"]]
                else:
                    p[prop["name"]] = prop["value"]

        logging.debug("Comparing properties")
        # Iterate provided properties and compare to received properties
        for prop in self.properties:
            if (prop not in p or
               p[prop] != self.properties[prop]):
                logging.debug("Properties mismatch")
                return True
        logging.debug("Properties match")

    def _strip_groups(self, groups):
        """Function to strip whitespace from group list.
        This function provides the user some flexibility when
        formatting group arguments """
        logging.debug("Running Host._strip_groups...")
        return map(lambda x: x.strip(), groups)


class Datasource(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor Datasource object"""
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Instantiating Datasource object")
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **params)

        self.id = self.params["id"]
        self.starttime = self.params["starttime"]
        self.duration = self.params["duration"]

    def sdt(self):
        """Create a scheduled down time
        (maintenance window) for this host"""
        logging.debug("Running Datasource.sdt...")

        logging.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        duration = self.duration
        starttime = self.starttime
        offsetstart = starttime

        if starttime:
            logging.debug("Start time specified")
            start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            offsetstart = start
        else:
            logging.debug("No start time specified. Using default.")
            start = datetime.datetime.utcnow()

            # Use user UTC offset
            logging.debug("Making RPC call to 'getTimeZoneSetting'")
            accountresp = json.loads(self.rpc("getTimeZoneSetting", {}))

            if accountresp["status"] == 200:
                logging.debug("RPC call succeeded")

                offset = accountresp["data"]["offset"]
                offsetstart = start + datetime.timedelta(0, offset)
            else:
                self.fail(msg="Error: Unable to retrieve timezone offset")

        offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

        h = {"hostDataSourceId": self.id,
             "type": 1,
             "notifyCC": True,
             "year": offsetstart.year,
             "month": offsetstart.month-1,
             "day": offsetstart.day,
             "hour": offsetstart.hour,
             "minute": offsetstart.minute,
             "endYear": offsetend.year,
             "endMonth": offsetend.month-1,
             "endDay": offsetend.day,
             "endHour": offsetend.hour,
             "endMinute": offsetend.minute}

        logging.debug("Making RPC call to 'setHostDataSourceSDT'")
        resp = json.loads(self.rpc("setHostDataSourceSDT", h))

        if resp["status"] == 200:
            logging.debug("RPC call succeeded")
            return resp["data"]
        else:
            logging.debug("RPC call failed")
            self.fail(msg=resp["errmsg"])


class Hostgroup(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor host object"""
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Instantiating Hostgroup object")
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **self.params)

        self.fullpath = self.params["fullpath"]
        self.info = self.get_group(self.fullpath)
        self.properties = self.params["properties"]
        self.description = self.params["description"]
        self.starttime = self.params["starttime"]
        self.duration = self.params["duration"]
        self.alertenable = self.params["alertenable"]

    def create(self):
        """Wrapper for self.update()"""
        logging.debug("Running Hostgroup.create...")
        self.update()

    def get_properties(self, final=False):
        """Returns a hash of the properties
        associated with this LogicMonitor host"""
        logging.debug("Running Hostgroup.get_properties...")

        if self.info:
            logging.debug("Group found")

            logging.debug("Making RPC call to 'getHostGroupProperties'")
            properties_json = json.loads(self.rpc(
                "getHostGroupProperties",
                {'hostGroupId': self.info["id"],
                 "finalResult": final}))

            if properties_json["status"] == 200:
                logging.debug("RPC call succeeded")
                return properties_json["data"]
            else:
                logging.debug("RPC call failed")
                self.fail(msg=properties_json["status"])
        else:
            logging.debug("Group not found")
            return None

    def set_properties(self, propertyhash):
        """Update the host to have the properties
        contained in the property hash"""
        logging.debug("Running Hostgroup.set_properties")

        logging.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        logging.debug("Assigning property has to host object")
        self.properties = propertyhash

    def add(self):
        """Idempotent function to ensure that the host
        group exists in your LogicMonitor account"""
        logging.debug("Running Hostgroup.add")

        if self.info is None:
            logging.debug("Group doesn't exist. Creating.")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            self.create_group(self.fullpath)
            self.info = self.get_group(self.fullpath)

            logging.debug("Group created")
            return self.info
        else:
            logging.debug("Group already exists")

    def update(self):
        """Idempotent function to ensure the host group settings
        (alertenable, properties, etc) in the
        LogicMonitor account match the current object."""
        logging.debug("Running Hostgroup.update")

        if self.info:
            if self.is_changed():
                logging.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                h = self._build_host_group_hash(
                    self.fullpath,
                    self.description,
                    self.properties,
                    self.alertenable)
                h["opType"] = "replace"

                if self.fullpath != "/":
                    h["id"] = self.info["id"]

                logging.debug("Making RPC call to 'updateHostGroup'")
                resp = json.loads(self.rpc("updateHostGroup", h))

                if resp["status"] == 200:
                    logging.debug("RPC call succeeded")
                    return resp["data"]
                else:
                    logging.debug("RPC call failed")
                    self.fail(
                        msg="Error: Unable to update the " +
                            "host.\n{0}".format(resp["errmsg"]))
            else:
                logging.debug("Group properties match supplied properties. " +
                              "No changes to make")
                return self.info
        else:
            logging.debug("Group doesn't exist. Creating.")

            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            return self.add()

    def remove(self):
        """Idempotent function to ensure the host group
        does not exist in your LogicMonitor account"""
        logging.debug("Running Hostgroup.remove...")

        if self.info:
            logging.debug("Group exists")
            logging.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            logging.debug("Making RPC call to 'deleteHostGroup'")
            resp = json.loads(self.rpc("deleteHostGroup",
                                       {"hgId": self.info["id"]}))

            if resp["status"] == 200:
                logging.debug(resp)
                logging.debug("RPC call succeeded")
                return resp
            elif resp["errmsg"] == "No such group":
                logging.debug("Group doesn't exist")
            else:
                logging.debug("RPC call failed")
                logging.debug(resp)
                self.fail(msg=resp["errmsg"])
        else:
            logging.debug("Group doesn't exist")

    def is_changed(self):
        """Return true if the host doesn't match
        the LogicMonitor account"""
        logging.debug("Running Hostgroup.is_changed...")

        ignore = []
        group = self.get_group(self.fullpath)
        properties = self.get_properties()

        if properties is not None and group is not None:
            logging.debug("Comparing simple group properties")
            if (group["alertEnable"] != self.alertenable or
               group["description"] != self.description):

                return True

            p = {}

            logging.debug("Creating list of properties")
            for prop in properties:
                if prop["name"] not in ignore:
                    if ("*******" in prop["value"] and
                       self._verify_property(prop["name"])):

                        p[prop["name"]] = (
                            self.properties[prop["name"]])
                    else:
                        p[prop["name"]] = prop["value"]

            logging.debug("Comparing properties")
            if set(p) != set(self.properties):
                return True
        else:
            logging.debug("No property information received")
            return False

    def sdt(self, duration=30, starttime=None):
        """Create a scheduled down time
        (maintenance window) for this host"""
        logging.debug("Running Hostgroup.sdt")

        logging.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        duration = self.duration
        starttime = self.starttime
        offset = starttime

        if starttime:
            logging.debug("Start time specified")
            start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            offsetstart = start
        else:
            logging.debug("No start time specified. Using default.")
            start = datetime.datetime.utcnow()

            # Use user UTC offset
            logging.debug("Making RPC call to 'getTimeZoneSetting'")
            accountresp = json.loads(self.rpc("getTimeZoneSetting", {}))

            if accountresp["status"] == 200:
                logging.debug("RPC call succeeded")

                offset = accountresp["data"]["offset"]
                offsetstart = start + datetime.timedelta(0, offset)
            else:
                self.fail(
                    msg="Error: Unable to retrieve timezone offset")

        offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

        h = {"hostGroupId": self.info["id"],
             "type": 1,
             "year": offsetstart.year,
             "month": offsetstart.month-1,
             "day": offsetstart.day,
             "hour": offsetstart.hour,
             "minute": offsetstart.minute,
             "endYear": offsetend.year,
             "endMonth": offsetend.month-1,
             "endDay": offsetend.day,
             "endHour": offsetend.hour,
             "endMinute": offsetend.minute}

        logging.debug("Making RPC call to setHostGroupSDT")
        resp = json.loads(self.rpc("setHostGroupSDT", h))

        if resp["status"] == 200:
            logging.debug("RPC call succeeded")
            return resp["data"]
        else:
            logging.debug("RPC call failed")
            self.fail(msg=resp["errmsg"])

    def site_facts(self):
        """Output current properties information for the Hostgroup"""
        logging.debug("Running Hostgroup.site_facts...")

        if self.info:
            logging.debug("Group exists")
            props = self.get_properties(True)

            self.output_info(props)
        else:
            self.fail(msg="Error: Group doesn't exit.")

    def _build_host_group_hash(self,
                               fullpath,
                               description,
                               properties,
                               alertenable):
        """Return a property formated hash for the
        creation of a hostgroup using the rpc function"""
        logging.debug("Running Hostgroup._build_host_hash")

        h = {}
        h["alertEnable"] = alertenable

        if fullpath == "/":
            logging.debug("Group is root")
            h["id"] = 1
        else:
            logging.debug("Determining group path")
            parentpath, name = fullpath.rsplit('/', 1)
            parent = self.get_group(parentpath)

            h["name"] = name

            if parent:
                logging.debug("Parent group {0} found.".format(parent["id"]))
                h["parentID"] = parent["id"]
            else:
                logging.debug("No parent group found. Using root.")
                h["parentID"] = 1

        if description:
            logging.debug("Description property exists")
            h["description"] = description

        if properties != {}:
            logging.debug("Properties hash exists")
            propnum = 0
            for key, value in properties.iteritems():
                h["propName{0}".format(str(propnum))] = key
                h["propValue{0}".format(str(propnum))] = value
                propnum = propnum + 1

        return h

    def _verify_property(self, propname):
        """Check with LogicMonitor server
        to verify property is unchanged"""
        logging.debug("Running Hostgroup._verify_property")

        if self.info:
            logging.debug("Group exists")
            if propname not in self.properties:
                logging.debug("Property {0} does not exist".format(propname))
                return False
            else:
                logging.debug("Property {0} exists".format(propname))
                h = {"hostGroupId": self.info["id"],
                     "propName0": propname,
                     "propValue0": self.properties[propname]}

                logging.debug("Making RCP call to 'verifyProperties'")
                resp = json.loads(self.rpc('verifyProperties', h))

                if resp["status"] == 200:
                    logging.debug("RPC call succeeded")
                    return resp["data"]["match"]
                else:
                    self.fail(
                        msg="Error: unable to get verification " +
                            "from server.\n%s" % resp["errmsg"])
        else:
            self.fail(
                msg="Error: Group doesn't exist. Unable to verify properties")


def selector(module):
    """Figure out which object and which actions
    to take given the right parameters"""

    if module.params["target"] == "collector":
        target = Collector(module.params, module)
    elif module.params["target"] == "host":
        # Make sure required parameter collector is specified
        if ((module.params["action"] == "add" or
            module.params["displayname"] is None) and
           module.params["collector"] is None):
            module.fail_json(
                msg="Parameter 'collector' required.")

        target = Host(module.params, module)
    elif module.params["target"] == "datasource":
        # Validate target specific required parameters
        if module.params["id"] is not None:
            # make sure a supported action was specified
            if module.params["action"] == "sdt":
                target = Datasource(module.params, module)
            else:
                errmsg = ("Error: Unexpected action \"{0}\" was specified."
                          .format(module.params["action"]))
                module.fail_json(msg=errmsg)

    elif module.params["target"] == "hostgroup":
        # Validate target specific required parameters
        if module.params["fullpath"] is not None:
            target = Hostgroup(module.params, module)
        else:
            module.fail_json(
                msg="Parameter 'fullpath' required for target 'hostgroup'")
    else:
        module.fail_json(
            msg="Error: Unexpected target \"{0}\" was specified."
            .format(module.params["target"]))

    if module.params["action"].lower() == "add":
        action = target.create
    elif module.params["action"].lower() == "remove":
        action = target.remove
    elif module.params["action"].lower() == "sdt":
        action = target.sdt
    elif module.params["action"].lower() == "update":
        action = target.update
    else:
        errmsg = ("Error: Unexpected action \"{0}\" was specified."
                  .format(module.params["action"]))
        module.fail_json(msg=errmsg)

    action()
    module.exit_json(changed=target.change)


def main():
    if HAS_LIB is not True:
        module.fail_json(msg="Unable to import required libraries")

    TARGETS = [
        "collector",
        "host",
        "datasource",
        "hostgroup"]

    ACTIONS = [
        "add",
        "remove",
        "sdt",
        "update"]

    module = AnsibleModule(
        argument_spec=dict(
            target=dict(required=True, default=None, choices=TARGETS),
            action=dict(required=True, default=None, choices=ACTIONS),
            company=dict(required=True, default=None),
            user=dict(required=True, default=None),
            password=dict(required=True, default=None, no_log=True),

            collector=dict(required=False, default=None),
            hostname=dict(required=False, default=None),
            displayname=dict(required=False, default=None),
            id=dict(required=False, default=None),
            description=dict(required=False, default=""),
            fullpath=dict(required=False, default=None),
            starttime=dict(required=False, default=None),
            duration=dict(required=False, default=30),
            properties=dict(required=False, default={}, type="dict"),
            groups=dict(required=False, default=[], type="list"),
            alertenable=dict(required=False, default=True, choices=BOOLEANS)
        ),
        supports_check_mode=True
    )

    selector(module)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *


if __name__ == "__main__":
    main()
