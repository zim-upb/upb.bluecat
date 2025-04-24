#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class View(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            configuration=dict(required=True, type='str')
        )


        super(View, self).__init__(self.module_args,
                                   supports_check_mode=True)

    def exec_module(self, **kwargs):
        view = self.get_view() or dict()
        # TODO: check if range is actually ip_network
        state = self.module.params.get('state')
        view_id = view.get('id')
        if state == 'present':
            if view:
                if self.compare_data(view):
                    self.update_view(view_id)
            else:
                config_id = self.get_configuration_id()
                self.create_view(config_id)
        elif state =="absent":
            self.delete_network(view_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

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

    def get_view(self):
        filter = 'configuration.name:eq("{}") and name:eq("{}")'.format(self.module.params.get('configuration'), self.module.params.get('name'))
        networks = self.client.http_get('/views',
                                              params={'limit': 1,
                                                      'filter': filter
                                                     }
                                              )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]

    def create_view(self, configuration_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/configurations/{configuration_id}/views',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_view(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/views/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_view(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/views/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data = json.dumps(data)
        return data

    def compare_data(self, network):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if network[key] != value:
                return True
        return False

def main():
    View()

if __name__ == '__main__':
    main()
