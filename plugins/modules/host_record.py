#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

import ipaddress
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class HostRecord(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            configuration=dict(required=True, type='str'),
            view=dict(required=True, type='str'),
            zone=dict(required=True, type='str'),
            reverseRecord=dict(type='bool', default=True),
            addresses=dict(type='list')
        )

        super(HostRecord, self).__init__(self.module_args,
                                         supports_check_mode=True)

    def exec_module(self, **kwargs):
        rr = self.get_resource_record() or dict()
        state = self.module.params.get('state')
        rr_id = rr.get('id')
        if state == 'present':
            if rr:
                if self.compare_data(rr):
                    self.update_host_record(rr_id)
            else:
                self.create_host_record()
        elif state =="absent":
            self.delete_host_record()

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_resource_record(self):
        absolute_name = '{}.{}'.format(self.module.params.get('name'), self.module.params.get('zone'))
        filter = 'configuration.name:eq("{}") and view.name:eq("{}") and absoluteName:eq("{}")'.format(
            self.module.params.get('configuration'), self.module.params.get('view'), absolute_name)
        rr = self.client.http_get('/resourceRecords',
                                     params={'limit': 1,
                                             'filter': filter,
                                             'fields': 'embed(addresses)'
                                             }
                                     )
        if rr['count'] == 0:
            return None
        else:
            return rr['data'][0]

    def get_zone_id(self):
        filter = 'configuration.name:eq("{}") and view.name:eq("{}") and absoluteName:eq("{}")'.format(
            self.module.params.get('configuration'), self.module.params.get('view'), self.module.params.get('zone'))
        zones = self.client.http_get('/zones',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if zones['count'] == 0:
            return None
        else:
            return zones['data'][0]['id']

    def create_host_record(self):
        changed = True
        result = None
        zone_id = self.get_zone_id()
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/zones/{zone_id}/resourceRecords',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_host_record(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/resourceRecords/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_host_record(self):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/resourceRecords/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data['type'] = "HostRecord"
        data['reverseRecord'] = self.module.params.get('reverseRecord')
        addresses = self.module.params.get('addresses')
        data_addresses = []
        for address in addresses:
            data_type = 'IPv6Address'
            if ipaddress.ip_address(address).version == 4:
                data_type = 'IPv4Address'
            data_id = self.get_address_id(address)
            if data_id:
                data_addresses.append({'type': data_type, 'id': data_id})
            else:
                data_addresses.append({'type': data_type, 'address': address})
        data['addresses'] = data_addresses
        data = json.dumps(data)
        return data

    def get_address_id(self, address):
        filter = 'configuration.name:eq("{}") and address:eq("{}")'.format(self.module.params.get('configuration'), address)
        addresses = self.client.http_get('/addresses',
                                     params={'limit': 1,
                                             'filter': filter
                                             }
                                     )
        if addresses['count'] == 0:
            return None
        else:
            return addresses['data'][0]['id']

    def compare_data(self, rr):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key == 'addresses':
                addresses = rr.get('_embedded').get('addresses')
                for address in addresses:
                    ip = address.get('address')
                    if ip not in self.module.params.get('addresses'):
                        return True
            elif rr[key] != value:
                return True
        return False

def main():
    HostRecord()

if __name__ == '__main__':
    main()
