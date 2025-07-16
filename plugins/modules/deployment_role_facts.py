#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class DeploymentRoleFacts(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            collection=dict(type='str', choices=['blocks', 'networks', 'zones']),
            resource=dict(type='str'),
            configuration=dict(type='str')
        )
        self.required_together = [
            ('collection', 'resource', 'configuration')
        ]
        super(DeploymentRoleFacts, self).__init__(self.module_args,
                                                  supports_check_mode=True,
                                                  required_together=self.required_together,
                                                  is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(deploymentRoles=[]))
        collection_id = None
        if self.module.params.get('collection') == 'blocks':
            collection_id = self.get_block_id()
        elif self.module.params.get('collection') == 'networks':
            collection_id = self.get_network_id()
        elif self.module.params.get('collection') == 'zones':
            collection_id = self.get_zone_id()

        if collection_id:
            response = self.client.http_get(f'/{self.module.params.get("collection")}/{collection_id}/deploymentRoles',
                                            params={'limit': self.module.params.get('limit'),
                                                    'filter': self.module.params.get('filter'),
                                                    'fields': self.module.params.get('fields')
                                                    }
                                            )
        else:
            response = self.client.http_get('/deploymentRoles',
                                            params={'limit': self.module.params.get('limit'),
                                                    'filter': self.module.params.get('filter'),
                                                    'fields': self.module.params.get('fields')
                                                    }
                                            )
        if response['count'] > 0:
            deploymentRoles = response['data']
            results['ansible_facts']['deploymentRoles'] = deploymentRoles
        return results

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

def main():
    DeploymentRoleFacts()

if __name__ == '__main__':
    main()
