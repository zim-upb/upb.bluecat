#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Group(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', required=True),
            groupType=dict(type='str', choices=['LDAP', 'ADDRESS_MANAGER'], required=True),
            authenticator_name=dict(type='str'),
            administratorPrivilege=dict(type='bool', default=False)
        )

        self.required_if = [
            ('groupType', 'LDAP', ['authenticator_name'])
        ]

        super(Group, self).__init__(self.module_args,
                                    required_if=self.required_if,
                                    supports_check_mode=True)

    def exec_module(self, **kwargs):
        group_type = self.module.params.get('groupType')
        authenticator_id = None
        authenticator_type = None
        if group_type == "LDAP":
            # get authenticator id
            authenticator_name = self.module.params.get('authenticator_name')
            authenticator_type = "LDAPAuthenticator"
            authenticator = self.get_authenticator_by_name(authenticator_name)
            if not authenticator:
                self.fail_json(f'Could not find authenticator {authenticator_name}'
                               f'of type {authenticator_type}')
            authenticator_id = authenticator.get('id')

        name = self.module.params.get('name')
        group = self.get_group_by_name(name)
        group_id = None
        if group:
            group_id = group.get('id')

        state = self.module.params.get('state')
        if state == 'present':
            if group_id:
                data = self.build_data(authenticator_id, authenticator_type)
                if self.compare_data(group, data):
                    self.update_group(group_id, data)
            else:
                self.create_group(data)
        else:
            if group_id:
                self.delete_group(group_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def create_group(self, data):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_post(f'/groups',
                                           data=data,
                                           headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def update_group(self, group_id, data):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_put(f'/groups/{group_id}',
                                          data=data,
                                          headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def delete_group(self, group_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/groups/{group_id}',
                                             headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def compare_data(self, group, data):
        data = json.loads(data)
        for key, value in data.items():
            if key == 'authenticator':
                continue
            if value != group[key]:
                return True
        return False

    def build_data(self, authenticator_id=None, authenticator_type=None):
        data = dict()
        data['name'] = self.module.params.get('name')
        data['groupType'] = self.module.params.get('groupType')
        data['administratorPrivilege'] = self.module.params.get('administratorPrivilege')
        if authenticator_id:
            data['authenticator'] = {'id': authenticator_id,
                                     'type': authenticator_type}
        data = json.dumps(data)
        return data

def main():
    Group()

if __name__ == '__main__':
    main()
