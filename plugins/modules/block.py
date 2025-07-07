#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

import ipaddress
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Block(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', default=''),
            range=dict(required=True, type='str'),
            configuration=dict(required=True, type='str'),
            defaultZonesInherited=dict(type='bool', default=True),
            restrictedZonesInherited=dict(type='bool', default=True),
            reverseZoneSigned=dict(type='bool', default=False),
            userDefinedFields=dict(type='dict')
        )


        super(Block, self).__init__(self.module_args,
                                    supports_check_mode=True)

    def exec_module(self, **kwargs):
        block = self.get_block() or dict()
        # TODO: check if range is actually ip_network
        state = self.module.params.get('state')
        block_id = block.get('id')
        if state == 'present':
            if block:
                if self.compare_data(block):
                    self.update_block(block_id)
            else:
                parent_id = self.find_parent_id()
                if parent_id:
                    self.create_sub_block(parent_id)
                else:
                    self.create_top_block()
        elif state =="absent":
            self.delete_block(block_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_block(self):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('range'))
        blocks = self.client.http_get('/blocks',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if blocks['count'] == 0:
            return None
        else:
            return blocks['data'][0]

    def get_configuration_id(self):
        filter = 'name:eq("{}")'.format(self.module.params.get('configuration'))
        configurations = self.client.http_get('/configurations',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if configurations['count'] == 0:
            self.fail_json('No configuration with name {} found!'.format(self.module.params.get('configuration')))
        else:
            return configurations['data'][0]['id']

    def find_parent_id(self):
        range = self.module.params.get('range')
        network_address = range.split('/')[0]
        filter = 'configuration.name:eq("{}") and range:contains("{}")'.format(self.module.params.get('configuration'), network_address)
        block = self.client.http_get('/blocks',
                                     params={'limit': 100,
                                             'filter': filter}
                                     )
        if block['count'] == 0:
            return None
        else:
            return block['data'][0]['id']

    def create_top_block(self):
        changed = True
        result = None
        config_id = self.get_configuration_id()
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/configurations/{config_id}/blocks',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def create_sub_block(self, parent_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/blocks/{parent_id}/blocks',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_block(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/blocks/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_block(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/blocks/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        range = self.module.params.get('range')
        name = self.module.params.get('name')
        if name == '':
            name = None
        data['name'] = name
        data['range'] = range
        if self.module.params.get('userDefinedFields'):
            data['userDefinedFields'] = self.module.params.get('userDefinedFields')
        if ipaddress.ip_network(range).version == 4:
            data['defaultZonesInherited'] = self.module.params.get('defaultZonesInherited')
            data['restrictedZonesInherited'] = self.module.params.get('restrictedZonesInherited')
            data['reverseZoneSigned'] = self.module.params.get('reverseZoneSigned')
        data['type'] = 'IPv6Block'
        if ipaddress.ip_network(self.module.params.get('range')).version == 4:
            data['type'] = 'IPv4Block'
        data = json.dumps(data)
        return data

    def compare_data(self, block):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if block[key] != value:
                return True
        return False

def main():
    Block()

if __name__ == '__main__':
    main()
