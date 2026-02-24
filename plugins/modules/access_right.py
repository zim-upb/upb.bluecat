#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class AccessRight(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            type=dict(type='str', default='AccessRight', choices=['AccessRight', 'AdministrativeAccessRight']),
            userScope_name=dict(type='str', required=True),
            userScope_type=dict(type='str', choices=['User', 'UserGroup'], required=True),
            resource=dict(type='str'),
            resource_type=dict(type='str', choices=['networks', 'blocks', 'zones']),
            configuration=dict(type='str'),
            defaultAccessLevel=dict(type='str', choices=['VIEW', 'CHANGE', 'ADD', 'FULL'], required=True),
            admin_event_right=dict(type='str', choices=['VIEW', 'HIDE', 'FULL'], default='HIDE'),
            admin_log_right=dict(type='str', choices=['VIEW', 'HIDE', 'FULL'], default='HIDE'),
            admin_report_right=dict(type='str', choices=['VIEW', 'HIDE', 'FULL'], default='HIDE'),
            deploymentsAllowed=dict(type='bool', default=False),
            quickDeploymentsAllowed=dict(type='bool', default=False),
            selectiveDeploymentsAllowed=dict(type='bool', default=False),
            workflowLevel=dict(type='str', choices=['NONE', 'RECOMMEND', 'APPROVE'], default='NONE'),
            accessOverrides=dict(type='list', default=[])
            )

        self.required_together = [
            ('resource', 'resource_type', 'configuration')
        ]

        super(AccessRight, self).__init__(self.module_args,
                                          supports_check_mode=True)

    def exec_module(self, **kwargs):
        # find ID of resource we want to add the access right to
        resource = self.module.params.get('resource')
        resource_type = self.module.params.get('resource_type')
        configuration = self.module.params.get('configuration')
        resource_id = None
        # check if we need to create an access right for a resource
        # or a default/administrative one
        if configuration:
            if resource_type == 'networks':
                network = self.get_network_by_range(configuration, resource)
                if network is None:
                    self.fail_json(f'Could not find network with range {resource}'
                                   f'in configuration {configuration}')
                resource_id = network.get('id')
            elif resource_type == 'blocks':
                block = self.get_block_by_range(configuration, resource)
                if block is None:
                    self.fail_json(f'Could not find block with range {resource}'
                                   f'in configuration {configuration}')
                resource_id = block.get('id')
            elif resource_type == 'zones':
                zone = self.get_zone_by_fqdn(configuration, resource)
                if zone is None:
                    self.fail_json(f'Could not find zone with FQDN {resource}'
                                   f'in configuration {configuration}')
                resource_id = zone.get('id')

        # find ID of user/group we want to give this access right
        userScope_name = self.module.params.get('userScope_name')
        userScope_type = self.module.params.get('userScope_type')
        if userScope_type == 'User':
            userScope = self.get_user_by_name(userScope_name)
        elif userScope_type == 'UserGroup':
            userScope = self.get_group_by_name(userScope_name)

        if userScope == None:
            self.fail_json(f'Could not find UserScope with name {userScope_name}'
                           f'and type {userScope_type}')
        userScope_id = userScope.get('id')


        type = self.module.params.get('type')
        if type == 'AdministrativeAccessRight':
            access_right = self.get_administrative_access_right(userScope_id)
        else:
            access_right = self.get_access_right_by_resource_id(resource_id, userScope_id)

        access_right_id = None
        if access_right:
            access_right_id = access_right.get('id')

        state = self.module.params.get('state')
        if state == 'present':
            data = self.build_data(userScope_id, resource_id)
            if access_right_id:
                if self.compare_data(access_right, data):
                    self.update_access_right(access_right_id, data)
            else:
                self.create_access_right(data)
        else:
            if access_right_id:
                self.delete_access_right(access_right_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def create_access_right(self, data):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_post(f'/accessRights',
                                           data=data,
                                           headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def delete_access_right(self, access_right_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/accessRights/{access_right_id}',
                                             headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def update_access_right(self, access_right_id, data):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_put(f'/accessRights/{access_right_id}',
                                          data=data,
                                          headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def build_data(self, userScope_id, resource_id):
        data = dict()
        data['type'] = self.module.params.get('type')
        data['userScope'] = dict()
        data['userScope']['id'] = userScope_id
        data['userScope']['type'] = self.module.params.get('userScope_type')
        if self.module.params.get('type') == 'AdministrativeAccessRight':
            event_right = self.module.params.get('admin_event_right')
            log_right = self.module.params.get('admin_log_right')
            report_right = self.module.params.get('admin_report_right')
            data['administrativeAccessRights'] = [{'accessLevel': f'{event_right}',
                                                   'resourceType': 'Event'},
                                                  {'accessLevel': f'{log_right}',
                                                   'resourceType': 'Log'},
                                                  {'accessLevel': f'{report_right}',
                                                   'resourceType': 'Report'}]
        else:
            data['defaultAccessLevel'] = self.module.params.get('defaultAccessLevel')
            data['deploymentsAllowed'] = self.module.params.get('deploymentsAllowed')
            data['quickDeploymentsAllowed'] =  self.module.params.get('quickDeploymentsAllowed')
            data['selectiveDeploymentsAllowed'] = self.module.params.get('selectiveDeploymentsAllowed')
            data['workflowLevel'] = self.module.params.get('workflowLevel')
            data['accessOverrides'] = self.module.params.get('accessOverrides')
        if resource_id:
            data['resource'] = {'id': resource_id}
        data = json.dumps(data)
        return data

    def compare_data(self, access_right, data):
        data = json.loads(data)
        for key, value in data.items():
            if key == 'userScope':
                continue
            if value != access_right[key]:
                return True
        return False

def main():
    AccessRight()

if __name__ == '__main__':
    main()
