#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class SigningPoliciesAppliedResources(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', required=True),
            resource=dict(type='str'),
            resource_type=dict(type='str', choices=['Zone', 'Block', 'Network']),
            configuration=dict(type='str')
            )

        super(SigningPoliciesAppliedResources, self).__init__(self.module_args,
                                                              supports_check_mode=True)

    def exec_module(self, **kwargs):
        # find ID of resource we want to add the access right to
        resource = self.module.params.get('resource')
        resource_type = self.module.params.get('resource_type')
        configuration = self.module.params.get('configuration')
        resource_id = None
        # check if we need to create an access right for a resource
        # or a default/administrative one
        if resource_type == 'Network':
            network = self.get_network_by_range(configuration, resource)
            if not network:
                self.fail_json(f'Could not find network with range {resource}'
                               f'in configuration {configuration}')
            resource_id = network.get('id')
        elif resource_type == 'Block':
            block = self.get_block_by_range(configuration, resource)
            if not block:
                self.fail_json(f'Could not find block with range {resource}'
                               f'in configuration {configuration}')
            resource_id = block.get('id')
        elif resource_type == 'Zone':
            zone = self.get_zone_by_fqdn(configuration, resource)
            if not zone:
                self.fail_json(f'Could not find zone with FQDN {resource}'
                               f'in configuration {configuration}')
            resource_id = zone.get('id')

        signing_policy = self.get_signing_policy_by_name(self.module.params.get('name'))
        if not signing_policy:
            self.fail_json(f'Could not find signingPolicy with name {self.module.params.get("name")}')
        signing_policy_id = signing_policy.get('id')

        state = self.module.params.get('state')
        resource_signing_policy = self.get_signing_policy_for_resource(signing_policy_id, resource_id)
        if state == 'present':
            if not resource_signing_policy:
                data = self.build_data(resource_id)
                self.set_signing_policy(signing_policy_id, data)
        else:
            if resource_signing_policy:
                self.unset_signing_policy(signing_policy_id, resource_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def set_signing_policy(self, signing_policy_id, data):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_post(f'/signingPolicies/{signing_policy_id}/appliedResources',
                                           data=data,
                                           headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def unset_signing_policy(self, signing_policy_id, resource_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/signingPolicies/{signing_policy_id}/appliedResources/{resource_id}',
                                             headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def get_signing_policy_for_resource(self, signing_policy_id, resource_id):
        filter = 'type:eq("{}") and id:eq({})'.format(self.module.params.get('resource_type'), resource_id)
        resource_signing_policy = self.client.http_get(f'/signingPolicies/{signing_policy_id}/appliedResources',
                                                        params={'limit': 1,
                                                                'filter': filter
                                                                }
                                                      )
        if resource_signing_policy['count'] == 0:
            return None
        else:
            return resource_signing_policy['data'][0]

    def build_data(self, resource_id):
        data = dict()
        data['type'] = self.module.params.get('resource_type')
        data['id'] = resource_id
        data = json.dumps(data)
        return data

def main():
    SigningPoliciesAppliedResources()

if __name__ == '__main__':
    main()
