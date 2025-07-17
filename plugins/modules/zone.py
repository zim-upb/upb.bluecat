#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Zone(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            configuration=dict(required=True, type='str'),
            view=dict(required=True, type='str'),
            zone=dict(type='str'),
            deploymentEnabled=dict(type='bool', default=True),
            dynamicUpdateEnabled=dict(type='bool', default=False),
            signed=dict(type='bool', default=False),
            move_dotted_resource_records=dict(type='bool', default=False)
        )


        super(Zone, self).__init__(self.module_args,
                                   supports_check_mode=True)

    def exec_module(self, **kwargs):
        zone = self.get_zone() or dict()
        state = self.module.params.get('state')
        zone_id = zone.get('id')
        if state == 'present':
            if zone:
                if self.compare_data(zone):
                    self.update_zone(zone_id)
            else:
                if self.module.params['zone']:
                    parent_id = self.get_parent_id()
                    self.create_sub_zone(parent_id)
                else:
                    self.create_top_zone()
        elif state =="absent":
            self.delete_zone(zone_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_zone(self):
        absolute_name = self.module.params.get('name')
        if self.module.params.get('zone'):
            absolute_name = '{}.{}'.format(self.module.params.get('name'), self.module.params.get('zone'))
        filter = 'configuration.name:eq("{}") and absoluteName:eq("{}")'.format(self.module.params.get('configuration'), absolute_name)
        networks = self.client.http_get('/zones',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]

    def get_view_id(self):
        filter = 'configuration.name:eq("{}") and name:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('view'))
        views = self.client.http_get('/views',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if views['count'] == 0:
            return None
        else:
            return views['data'][0]['id']

    def get_parent_id(self):
        filter = 'configuration.name:eq("{}") and absoluteName:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('zone'))
        block = self.client.http_get('/zones',
                                     params={'limit': 1,
                                             'filter': filter}
                                     )
        if block['count'] == 0:
            return None
        else:
            return block['data'][0]['id']

    def create_top_zone(self):
        changed = True
        result = None
        view_id = self.get_view_id()
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/views/{view_id}/zones',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def create_sub_zone(self, parent_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/zones/{parent_id}/zones',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_zone(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/zones/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_zone(self, zone_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/zones/{zone_id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data['deploymentEnabled'] = self.module.params.get('deploymentEnabled')
        data['dynamicUpdateEnabled'] = self.module.params.get('dynamicUpdateEnabled')
        data['signed'] = self.module.params.get('signed')
        data['type'] = 'Zone'
        data = json.dumps(data)
        return data

    def compare_data(self, block):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key == 'move_dotted_resource_records':
                continue
            if block[key] != value:
                return True
        return False

def main():
    Zone()

if __name__ == '__main__':
    main()
