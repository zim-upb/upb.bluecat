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
        configuration_name = self.module.params.get('configuration')
        configuration = self.get_configuration_by_name(configuration_name)
        if configuration is None:
            self.fail_json('No configuration with name {} found!'.format(self.module.params.get('configuration')))
        configuration_id = configuration.get('id')

        name = self.module.params.get('name')
        view = self.get_view_by_name(configuration_name, name)
        view_id = None
        if view:
            view_id = view.get('id')

        state = self.module.params.get('state')
        if state == 'present':
            data = self.build_data()
            if view_id:
                if self.compare_data(view, data):
                    self.update_view(view_id)
            else:
                self.create_view(configuration_id, data)
        elif state == 'absent':
            self.delete_view(view_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))


    def create_view(self, configuration_id, data):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/configurations/{configuration_id}/views',
                                            data=data,
                                            headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def update_view(self, view_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/views/{view_id}',
                                          data=data,
                                          headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def delete_view(self, view_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/views/{view_id}')

        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data = json.dumps(data)
        return data

    def compare_data(self, view, data):
        data = json.loads(data)
        for key, value in data.items():
            if view[key] != value:
                return True
        return False

def main():
    View()

if __name__ == '__main__':
    main()
