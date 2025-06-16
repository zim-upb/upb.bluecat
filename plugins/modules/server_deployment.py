#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class ServerDeployment(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            name=dict(required=True, type='str'),
            configuration=dict(required=True, type='str'),
            type=dict(required=True, type='str', choices=['FullDeployment', 'DifferentialDeployment']),
            service=dict(required=True, type='str', choices=['DNS', 'DHCPv4', 'DHCPv6']),
            x_bcn_force_zone_retransfer=dict(type='str', default='False', choices=['False', 'True'])
        )

        super(ServerDeployment, self).__init__(self.module_args,
                                               supports_check_mode=False)

    def exec_module(self, **kwargs):
        if self.module.params.get('type') == 'DifferentialDeployment' and self.module.params.get('service') != 'DNS':
            self.fail_json(msg='DHCP services do not allow Differential Deployments!')
        server_id = self.get_server_id(self.module.params.get('name'))
        data = self.build_data()
        self.headers['x-bcn-force-zone-retransfer'] = self.module.params.get('x_bcn_force_zone_retransfer')
        result = self.client.http_post(f'/servers/{server_id}/deployments',
                                       data=data,
                                       headers=self.headers)
        changed = True
        self.exit_json(changed=changed, result=str(result))

    def get_server_id(self, name):
        filter = 'configuration.name:eq("{}") and name:eq("{}")'.format(self.module.params.get('configuration'), name)
        servers = self.client.http_get('/servers',
                                       params={'limit': 1,
                                               'filter': filter,
                                               },
                                       headers=self.headers)
        if servers['count'] == 0:
            return None
        else:
            return servers['data'][0]['id']

    def build_data(self):
        data = dict()
        data['type'] = self.module.params.get('type')
        data['service'] = self.module.params.get('service')
        data = json.dumps(data)
        return data

def main():
    ServerDeployment()

if __name__ == '__main__':
    main()
