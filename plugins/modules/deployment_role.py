#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class DeploymentRole(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            type=dict(type='str', required=True, choices=['DNSDeploymentRole', 'DHCPDeploymentRole', 'TFTPDeploymentRole']),
            roleType=dict(type='str', required=True, choices=['PRIMARY', 'SECONDARY', 'TFTP', 'NONE']),
            collection=dict(type='str', required=True, choices=['blocks', 'networks', 'zones']),
            resource=dict(type='str', required=True),
            interface=dict(type='str', required=True),
            configuration=dict(required=True, type='str')
        )

        self.interface_id = None

        super(DeploymentRole, self).__init__(self.module_args,
                                             supports_check_mode=True)

    def exec_module(self, **kwargs):
        if self.module.params.get('collection') == 'blocks':
            collection_id = self.get_block_id()
        elif self.module.params.get('collection') == 'networks':
            collection_id = self.get_network_id()
        elif self.module.params.get('collection') == 'zones':
            collection_id = self.get_zone_id()

        if collection_id == None:
            self.fail_json(msg='Could not find resource!')

        self.interface_id = self.get_interface_id()
        deployment_roles = self.get_deployment_roles(collection_id)
        if self.module.params.get('state') == 'present':
            if self.compare_data(deployment_roles):
                self.create_deployment_role(collection_id)
        else:
            deployment_role_id = self.find_deployment_role_id(deployment_roles)
            if deployment_role_id:
                self.delete_deployment_role(deployment_role_id)
            else:
                self.fail_json(msg='Could not find a matching deployment role to delete!')

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_interface_id(self):
        filter = 'configuration.name:eq("{}") and name:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('interface'))
        interfaces = self.client.http_get('/interfaces',
                                       params={'limit': 1,
                                               'filter': filter,
                                               },
                                       headers=self.headers)
        if interfaces['count'] == 0:
            return None
        else:
            return interfaces['data'][0]['id']

    def find_deployment_role_id(self, deployment_roles):
        for role in deployment_roles:
            if (self.module.params.get('type') == role['type'] and
                self.module.params.get('roleType') == role['roleType']):
                for int in role['_embedded']['interfaces']:
                    if int['id'] == self.interface_id:
                        return role['id']
        return None

    def get_deployment_roles(self, collection_id):
        filter = 'configuration.name:eq("{}")'.format(self.module.params.get('configuration'))
        deployment_roles = self.client.http_get(f'/{self.module.params.get("collection")}/{collection_id}/deploymentRoles',
                                                params={'limit': 100,
                                                        'filter': filter,
                                                        'fields': 'embed(interfaces)'})
        if deployment_roles['count'] == 0:
            return list()
        else:
            return deployment_roles['data']

    def get_block_id(self):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('resource'))
        blocks = self.client.http_get('/blocks',
                                              params={'limit': 1,
                                                      'filter': filter,
                                                      'fields': 'embed(defaultZones)'
                                                     }
                                              )
        if blocks['count'] == 0:
            return None
        else:
            return blocks['data'][0]['id']

    def get_network_id(self):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('resource'))
        networks = self.client.http_get('/networks',
                                              params={'limit': 1,
                                                      'filter': filter,
                                                      'fields': 'embed(userDefinedLinks)'
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]['id']

    def get_zone_id(self):
        filter = 'configuration.name:eq("{}") and absoluteName:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('resource'))
        networks = self.client.http_get('/zones',
                                        params={'limit': 1,
                                                'filter': filter
                                                }
                                        )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]['id']

    def create_deployment_role(self, collection_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/{self.module.params.get("collection")}/{collection_id}/deploymentRoles',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_deployment_role(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/deploymentRoles/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_deployment_role(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/deploymentRoles/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['type'] = self.module.params.get('type')
        data['roleType'] = self.module.params.get('roleType')
        data['interfaces'] = list()
        interface = dict()
        interface['id'] = self.interface_id
        interface['type'] = 'NetworkInterface'
        data['interfaces'].append(interface)
        data = json.dumps(data)
        return data

    def compare_data(self, deployment_roles):
        data = json.loads(self.build_data())
        for role in deployment_roles:
            if '_inheritedFrom' in role and role['_inheritedFrom']:
                continue
            if (data['type'] == role['type'] and
                data['roleType'] == role['roleType']):
                for int in role['_embedded']['interfaces']:
                    if data['interfaces'][0]['id'] == int['id']:
                        return False
        return True

def main():
    DeploymentRole()

if __name__ == '__main__':
    main()
