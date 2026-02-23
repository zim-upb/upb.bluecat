#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

import ipaddress
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Network(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', default=''),
            range=dict(required=True, type='str'),
            configuration=dict(required=True, type='str'),
            defaultZonesInherited=dict(type='bool', default=True),
            defaultZones=dict(type='list', default=[]),
            restrictedZonesInherited=dict(type='bool', default=True),
            reverseZoneSigned=dict(type='bool', default=False),
            dynamicUpdateEnabled=dict(type='bool', default=False),
            gateway=dict(type='str', default=None),
            userDefinedFields=dict(type='dict')
        )


        super(Network, self).__init__(self.module_args,
                                      supports_check_mode=True)

    def exec_module(self, **kwargs):
        network = self.get_network() or dict()
        # TODO: check if range is actually ip_network
        state = self.module.params.get('state')
        network_id = network.get('id')
        # normalize for IPv6 ranges
        self.module.params['range'] = self.module.params.get('range').lower()
        ip_network = ipaddress.ip_network(self.module.params.get('range'))
        if ip_network.version == 6 and ip_network.prefixlen < 64:
            self.fail_json(msg=f"{self.module.params.get('range')} prefix length must be between /64 and /128')")
        if state == 'present':
            if network:
                if self.compare_data(network):
                    self.update_network(network_id)
            else:
                parent_id = self.get_block_id()
                self.create_network(parent_id)
        elif state =="absent":
            self.delete_network(network_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_network(self):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('range'))
        networks = self.client.http_get('/networks',
                                              params={'limit': 1,
                                                      'filter': filter,
                                                      'fields': 'embed(defaultZones)'
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]

    def get_block_id(self):
        range = self.module.params.get('range')
        network_address = range.split('/')[0]
        filter = 'configuration.name:eq("{}") and range:ge("{}") and range:contains("{}")'.format(self.module.params.get('configuration'), range, network_address)
        block = self.client.http_get('/blocks',
                                     params={'limit': 100,
                                             'filter': filter,
                                             'orderBy': "range"}
                                     )
        if block['count'] == 0:
            return None
        else:
            return block['data'][-1]['id']

    def get_zone_id(self, absolute_name):
        filter = 'configuration.name:eq("{}") and absoluteName:eq("{}")'.format(self.module.params.get('configuration'), absolute_name)
        networks = self.client.http_get('/zones',
                                        params={'limit': 1,
                                                'filter': filter
                                                }
                                        )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]['id']

    def create_network(self, parent_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/blocks/{parent_id}/networks',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_network(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/networks/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_network(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/networks/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        if self.module.params.get('name') == '':
            self.module.params['name'] = None
        data['name'] = self.module.params.get('name')
        data['range'] = self.module.params.get('range')
        data['restrictedZonesInherited'] = self.module.params.get('restrictedZonesInherited')
        data['reverseZoneSigned'] = self.module.params.get('reverseZoneSigned')
        data['type'] = 'IPv6Network'
        if ipaddress.ip_network(self.module.params.get('range')).version == 4:
            data['type'] = 'IPv4Network'
            if self.module.params.get('gateway') is None or self.module.params.get('gateway') == '':
                self.headers['x-bcn-no-gateway'] = "true"
                data['gateway'] = None
            else:
                data['gateway'] = self.module.params.get('gateway')
            data['dynamicUpdateEnabled'] = self.module.params.get('dynamicUpdateEnabled')
            data['defaultZonesInherited'] = self.module.params.get('defaultZonesInherited')
            if self.module.params.get('defaultZones'):
                data['defaultZones'] = []
                for zone in self.module.params.get('defaultZones'):
                    zone_id = self.get_zone_id(zone)
                    data['defaultZones'].append({'type': 'Zone',
                                                 'id': zone_id,
                                                 'absoluteName': zone})
        if self.module.params.get('userDefinedFields'):
            data['userDefinedFields'] = self.module.params.get('userDefinedFields')
        data = json.dumps(data)
        return data

    def compare_data(self, network):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key not in network and key not in network['_embedded']:
                continue
            if key == 'defaultZones':
                bam_defaultZone_ids = [x.get('id') for x in network['_embedded']['defaultZones']]
                data_defaultZone_ids = [x.get('id') for x in value]
                if data_defaultZone_ids != bam_defaultZone_ids:
                    return True
            elif key == 'userDefinedFields':
                for udf_key, udf_value in value.items():
                    if udf_value != network[key][udf_key]:
                        return True
            elif network[key] != value:
                return True
        return False

def main():
    Network()

if __name__ == '__main__':
    main()
