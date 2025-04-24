#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

import ipaddress
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Address(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            configuration=dict(required=True, type='str'),
            address=dict(required=True, type='str'),
            name=dict(type='str', default=None),
            network=dict(type='str'),
            address_state=dict(type='str', default='STATIC', choices=['STATIC', 'RESERVED', 'DHCP_RESERVED']),
            mac_address=dict(type='str', default=None),
            create_reverse_record=dict(type='bool', default=True)
        )
        self.required_if = [
            ('address_state', 'DHCP_RESERVED', ['mac_address'])
        ]

        super(Address, self).__init__(self.module_args,
                                      supports_check_mode=True)

    def exec_module(self, **kwargs):
        address = self.get_address() or dict()
        # TODO: check if range is actually ip_network
        state = self.module.params.get('state')
        address_id = address.get('id')
        if self.module.params.get('address_state') == 'RESERVED' and ipaddress.ip_address(self.module.params.get('address')).version == 6:
            self.fail_json(msg='IPv6 address cannot have state RESERVED')
        if state == 'present':
            if address:
                if self.compare_data(address):
                    self.update_address(address_id)
            else:
                if self.module.params.get('network'):
                    network_id = self.get_network_id()
                else:
                    network_id = self.find_network_id()
                self.create_address(network_id)
        elif state =="absent":
            self.delete_address(address_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_network_id(self):
        filter = 'configuration.name:eq("{}") and range:contains("{}")'.format(self.module.params.get('configuration'), self.module.params.get('address'))
        networks = self.client.http_get('/networks',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]['id']

    def find_network_id(self):
        filter = 'configuration.name:eq("{}") and range:contains("{}")'.format(self.module.params.get('configuration'), self.module.params.get('address'))
        networks = self.client.http_get('/networks',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]['id']

    def get_address(self):
        filter = 'configuration.name:eq("{}") and address:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('address'))
        networks = self.client.http_get('/addresses',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]

    def create_address(self, parent_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/networks/{parent_id}/addresses',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_address(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/addresses/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_address(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/addresses/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['address'] = self.module.params.get('address')
        data['name'] = self.module.params.get('name')
        data['state'] = self.module.params.get('address_state')
        if self.module.params.get('mac_address'):
            data['macAddress'] = {'type': 'MACAddress',
                                  'address': self.module.params.get('mac_address')}
        else:
            data['macAddress'] = None
        data['type'] = 'IPv6Address'
        if ipaddress.ip_address(self.module.params.get('address')).version == 4:
            data['type'] = 'IPv4Address'
        data = json.dumps(data)
        return data

    def compare_data(self, address):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key == 'macAddress' and address[key] and value and address[key]['address'] == value['address']:
                continue
            elif address[key] != value:
                return True
        return False

def main():
    Address()

if __name__ == '__main__':
    main()
