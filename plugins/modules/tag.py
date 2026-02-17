#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Tag(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', required=True),
            tagGroup=dict(type='str'),
            tag=dict(type='str'),
        )

        self.mutually_exclusive = [
            ('tagGroup', 'tag'),
        ]

        self.required_one_of = [
            ('tagGroup', 'tag')
        ]

        super(Tag, self).__init__(self.module_args,
                                  mutually_exclusive=self.mutually_exclusive,
                                  required_one_of=self.required_one_of,
                                  supports_check_mode=True)

    def exec_module(self, **kwargs):
        tag = self.get_tag(self.module.params.get('name'))
        if self.module.params.get('state') == 'present':
            if not tag:
                if self.module.params.get('tag'):
                    parent = self.get_tag(self.module.params.get('tag'))
                elif self.module.params.get('tagGroup'):
                    parent = self.get_tag_group(self.module.params.get('tagGroup'))

                self.create_tag(parent.get('id'))
        else:
            if tag:
                tag_id = tag.get('id')
                self.delete_tag(tag_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def create_tag(self, parent_id):
        changed = True
        result = None
        collection = 'tagGroups'
        if self.module.params.get('tag'):
            collection = 'tags'
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post(f'/{collection}/{parent_id}/tags',
                                           data=data,
                                           headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_tag(self, tag_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/tags/{tag_id}',
                                             headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data = json.dumps(data)
        return data

    def compare_data(self, tag):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if key not in network and key not in network['_embedded']:
                continue
            elif network[key] != value:
                return True
        return False

def main():
    Tag()

if __name__ == '__main__':
    main()
