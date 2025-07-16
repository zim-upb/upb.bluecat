#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json

import ipaddress
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule


class TagGroup(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', required=True),
            userDefinedFields=dict(type='dict', default=None)
        )

        super(TagGroup, self).__init__(self.module_args,
                                       supports_check_mode=True)

    def exec_module(self, **kwargs):
        tag_group = self.get_tag_group()
        tag_group_id = tag_group.get('id')
        if self.module.params.get('state') == 'present':
            if tag_group:
                if self.compare_data(tag_group):
                    self.update_tag_group(tag_group_id)
            else:
                self.create_tag_group()
        else:
            if tag_group:
                self.delete_tag_group(tag_group_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_tag_group(self):
        filter = 'name:eq("{}")'.format(self.module.params.get('name'))
        tag_groups = self.client.http_get('/tagGroups',
                                          params={'limit': 1,
                                                  'filter': filter,
                                                  },
                                          headers=self.headers)
        if tag_groups['count'] == 0:
            return None
        else:
            return tag_groups['data'][0]

    def create_tag_group(self):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/tagGroups/',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_tag_group(self, tag_group_id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/tagGroups/{tag_group_id}',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_tag_group(self, tag_group_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/tagGroups/{tag_group_id}',
                                             headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data['userDefinedFields'] = self.module.params.get('userDefinedFields')
        data = json.dumps(data)
        return data

    def compare_data(self, tag_group):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key not in tag_group or tag_group[key] != value:
                return True
        return False


def main():
    TagGroup()


if __name__ == '__main__':
    main()
