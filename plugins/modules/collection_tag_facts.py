#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class CollectionTagFacts(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            resource=dict(type='str', required=True),
            collection=dict(type='str', required=True, choices=['networks', 'blocks']),
            configuration=dict(required=True, type='str')
        )
        super(CollectionTagFacts, self).__init__(self.module_args,
                                            supports_check_mode=True,
                                            is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(collection_tags=[]))
        collection = self.module.params.get('collection')
        collection_id = None
        resource = self.module.params.get('resource')
        if collection == 'networks':
            network = self.get_network(self.module.params.get('configuration'),
                                       self.module.params.get('resource'))
            if network == None:
                self.fail_json(msg='Could not find network resource!')
            collection_id = network.get('id')
        elif collection == 'blocks':
            block = self.get_block(self.module.params.get('configuration'),
                                   self.module.params.get('resource'))
            if block == None:
                self.fail_json(msg='Could not find block resource!')
            collection_id = block.get('id')
        response = self.client.http_get(f'/{collection}/{collection_id}/tags',
                                        params={'limit': self.module.params.get('limit'),
                                                'filter': self.module.params.get('filter'),
                                                'fields': self.module.params.get('fields')
                                                }
                                        )
        if response['count'] > 0:
            collection_tags = response['data']
            results['ansible_facts']['collection_tags'] = collection_tags
        return results

def main():
    CollectionTagFacts()

if __name__ == '__main__':
    main()
