#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class AliasRecord(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            configuration=dict(required=True, type='str'),
            view=dict(required=True, type='str'),
            zone=dict(required=True, type='str'),
            linked_record=dict(required=True, type='str'),
        )

        super(AliasRecord, self).__init__(self.module_args,
                                         supports_check_mode=True)

    def exec_module(self, **kwargs):
        zone_id = self.get_zone_id()
        rr = self.get_resource_record(zone_id) or dict()
        state = self.module.params.get('state')
        rr_id = rr.get('id')
        if state == 'present':
            if rr:
                if self.compare_data(rr):
                    self.update_alias_record(rr_id)
            else:
                self.create_alias_record(zone_id)
        elif state =="absent":
            self.delete_alias_record(rr_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_resource_record(self, zone_id):
        filter = 'name:eq("{}")'.format(self.module.params.get('name'))
        rr = self.client.http_get(f'/zones/{zone_id}/resourceRecords',
                                     params={'limit': 1,
                                             'filter': filter,
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

    def create_alias_record(self, zone_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/zones/{zone_id}/resourceRecords',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_alias_record(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/resourceRecords/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_alias_record(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/resourceRecords/{id}',
                                             headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def get_host_record(self, name):
        filter = 'absoluteName:eq("{}")'.format(name)
        rr = self.client.http_get('/resourceRecords',
                                     params={'limit': 1,
                                             'filter': filter,
                                             }
                                     )
        if rr['count'] == 0:
            self.fail_json(msg=f"Did not find {name}")
            return None

        data = dict()
        data['id'] = rr['data'][0]['id']
        data['type'] = rr['data'][0]['type']
        return data

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data['type'] = "AliasRecord"
        data['linkedRecord'] = self.get_host_record(self.module.params.get('linked_record'))
        data = json.dumps(data)
        return data

    def compare_data(self, rr):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key == "linkedRecord":
                if rr[key]['id'] != value['id']:
                    return True
            elif rr[key] != value:
                return True
        return False

def main():
    AliasRecord()

if __name__ == '__main__':
    main()
