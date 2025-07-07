#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class UserDefinedLink(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            name=dict(required=True, type='str'),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            description=dict(type='str', default=''),
            source=dict(required=True, type='str'),
            source_type=dict(type='str', required=True, choices=['addresses', 'blocks', 'devices', 'ipGroups',
                                                                'macAddresses', 'macPools', 'networks', 'ranges',
                                                                'serverGroups', 'servers', 'views', 'zones']),
            destination=dict(required=True, type='str'),
            destination_type=dict(required=True, type='str', choices=['addresses', 'blocks', 'devices', 'ipGroups',
                                                                      'macAddresses', 'macPools', 'networks', 'ranges',
                                                                      'serverGroups', 'servers', 'views', 'zones']),
            configuration=dict(required=True, type='str')
        )

        self.udl_definition_id = None
        self.destination_id = None

        super(UserDefinedLink, self).__init__(self.module_args,
                                              supports_check_mode=True)

    def exec_module(self, **kwargs):
        self.udl_definition_id = self.get_udl_definition_id()

        source_id = None
        if self.module.params.get('source_type') == 'networks':
            source_id = self.get_network_id(self.module.params.get('source'))
        else:
            self.fail_json(msg=f'{self.module.params.get("source_type")} not yet implemented.')

        if self.module.params.get('destination_type') == 'networks':
            self.destination_id = self.get_network_id(self.module.params.get('destination'))
        else:
            self.fail_json(msg=f'{self.module.params.get("destination_type")} not yet implemented.')

        udl = self.get_udl(source_id, self.destination_id)
        if self.module.params.get('state') == 'present':
            if not udl:
                self.create_udl(source_id)
        else:
            # it seems 9.6 cannot delete UDLs yet, we have to wait until 10.0/25.1 to have the ability to find out
            # the entityLinkId to reference the UDL we want to delete
            self.fail_json(msg='Deletion can not yet be implemented')
            self.delete_udl(source_id, udl)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def create_udl(self, source_id):
        result = None
        changed = True
        data = self.build_data()
        if not self.module.check_mode:
            result = self.client.http_post(f'/{self.module.params.get("source_type")}/{source_id}/userDefinedLinks',
                                         data=data,
                                         headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_udl(self, source_id, entity_link_id):
        result = None
        changed = True
        data = self.build_data()
        if not self.module.check_mode:
            result = self.client.http_delete(f'/{self.module.params.get("source_type")}/{str(source_id)}/userDefinedLinks/{entity_link_id}',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def get_udl(self, source_id, destination_id):
        filter = 'id:eq({})'.format(destination_id)
        udls = self.client.http_get(f'/{self.module.params.get("source_type")}/{source_id}/userDefinedLinks',
                                    params={'limit': 1,
                                            'filter': filter
                                            }
                                    )
        if udls['count'] == 0:
            return None
        else:
            return udls['data'][0]

    def get_udl_definition_id(self):
        filter = 'displayName:eq("{}")'.format(self.module.params.get('name'))
        udls = self.client.http_get('/userDefinedLinkDefinitions',
                                    params={'limit': 1,
                                            'filter': filter
                                            }
                                    )
        if udls['count'] == 0:
            return None
        else:
            return udls['data'][0]['id']

    def get_network_id(self, range):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(self.module.params.get('configuration'), range)
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

    def build_data(self):
        data = dict()
        data['id'] = self.destination_id
        data['linkDescription'] = None
        if self.module.params.get('description'):
            data['linkDescription'] = self.module.params.get('description')
        data['linkDefinition'] = dict()
        data['linkDefinition']['id'] = self.udl_definition_id
        data['linkDefinition']['type'] = 'UserDefinedLinkDefinition'
        data = json.dumps(data)
        return data

    def compare_data(self, udl):
        data = json.loads(self.build_data())
        if 'id' not in udl or data['id'] != udl['id']:
            return True
        # do not test for this for now since we cannot update UDLs at this time
        #if 'linkDescription' not in udl or data['linkDescription'] != udl['linkDescription']:
        #    return True
        if 'linkDefinition' not in udl or data['linkDefinition']['id'] != udl['linkDefinition']['id']:
            return True
        return False

def main():
    UserDefinedLink()

if __name__ == '__main__':
    main()
