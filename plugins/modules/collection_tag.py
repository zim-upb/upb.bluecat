#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class CollectionTag(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            resource=dict(type='str', required=True),
            collection=dict(type='str', required=True, choices=['networks', 'blocks']),
            configuration=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            tag=dict(type='str'),
            tagGroup=dict(type='str')
            )

        self.mutually_exclusive = [
            ('tagGroup', 'tag'),
        ]

        self.required_one_of = [
            ('tagGroup', 'tag')
        ]


        super(CollectionTag, self).__init__(self.module_args,
                                         mutually_exclusive=self.mutually_exclusive,
                                         required_one_of=self.required_one_of,
                                         supports_check_mode=True)

    def exec_module(self, **kwargs):
        if self.module.params.get('tag'):
            parent = self.get_tag(self.module.params.get('tag'))
        else:
            parent = self.get_tag_group(self.module.params.get('tagGroup'))

        if parent == None:
            self.fail_json(msg='Could not find parent of tag!')
        parent_id = parent.get('id')

        collection = self.module.params.get('collection')
        collection_id = None
        if collection == 'networks':
            network = self.get_network_by_range(self.module.params.get('configuration'),
                                                self.module.params.get('resource'))
            if network == None:
                self.fail_json(msg='Could not find network resource!')
            collection_id = network.get('id')
        elif collection == 'blocks':
            block = self.get_block_by_range(self.module.params.get('configuration'),
                                            self.module.params.get('resource'))
            if block == None:
                self.fail_json(msg='Could not find block resource!')
            collection_id = block.get('id')

        current_tags = self.get_linked_tags(collection, collection_id)
        current_tag_ids = []
        if current_tags:
            current_tag_ids = [x.get('id') for x in current_tags]

        tag = self.get_tag(self.module.params.get('name'))
        if tag == None:
            self.fail_json(msg='Tag does not exist!')

        tag_id = tag.get('id')
        if self.module.params.get('state') == 'present':
            if tag_id not in current_tag_ids:
                self.link_resource(collection, collection_id, tag_id)
        else:
            if tag_id in current_tag_ids:
                self.unlink_resource(collection, collection_id, tag_id)

        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_linked_tags(self, collection, collection_id):
        tags = self.client.http_get(f'/{collection}/{collection_id}/tags')
        if tags['count'] == 0:
            return None
        else:
            return tags['data']

    def link_resource(self, collection, collection_id, tag_id):
        changed = True
        result = None
        data = self.build_data(tag_id)
        if not self.module.check_mode:
            result = self.client.http_post(f'/{collection}/{collection_id}/tags',
                                           data=data,
                                           headers=self.headers)

        self.exit_json(changed=changed, result=str(result))

    def unlink_resource(self, collection, collection_id, tag_id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/{collection}/{collection_id}/tags/{tag_id}')

        self.exit_json(changed=changed, result=str(result))

    def build_data(self, tag_id):
        data = dict()
        data['id'] = tag_id
        data = json.dumps(data)
        return data

def main():
    CollectionTag()

if __name__ == '__main__':
    main()
