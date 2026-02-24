#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class CollectionAccessRightFacts(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            resource=dict(type='str', required=True),
            collection=dict(type='str', required=True, choices=['networks', 'blocks', 'zones', 'views', 'configurations']),
            configuration=dict(type='str')
        )

        self.required_if = [
            ('collection', 'blocks', ['configuration']),
            ('collection', 'networks', ['configuration']),
            ('collection', 'zones', ['configuration']),
            ('collection', 'views', ['configuration']),
        ]

        super(CollectionAccessRightFacts, self).__init__(self.module_args,
                                                         supports_check_mode=True,
                                                         required_if=self.required_if,
                                                         is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(collection_access_rights=[]))
        collection = self.module.params.get('collection')
        collection_id = None
        configuration = self.module.params.get('configuration')
        resource = self.module.params.get('resource')
        if collection == 'networks':
            network = self.get_network_by_range(configuration, resource)
            if network == None:
                self.fail_json(f'Could not find network with range {resource} '
                               f'in configuration {configuration}')
            collection_id = network.get('id')
        elif collection == 'blocks':
            block = self.get_block_by_range(configuration, resource)
            if block == None:
                self.fail_json(f'Could not find block with range {resource} '
                               f'in configuration {configuration}')
            collection_id = block.get('id')
        elif collection == 'zones':
            zone = self.get_zone_by_fqdn(configuration, resource)
            if zone is None:
                self.fail_json(f'Could not find zone with FQDN {resource} '
                               f'in configuration {configuration}')
            collection_id = zone.get('id')
        elif collection == 'views':
            view = self.get_view_by_name(configuration, resource)
            if view is None:
                self.fail_json(f'Could not find view with name {resource} '
                               f'in configuration {configuration}')
            collection_id = view.get('id')
        elif collection == 'configurations':
            configuration = self.get_configuration_by_name(resource)
            if configuration is None:
                self.fail_json(f'Could not find configuration with name {resource}')
            collection_id = configuration.get('id')

        response = self.client.http_get(f'/{collection}/{collection_id}/accessRights',
                                        params={'limit': self.module.params.get('limit'),
                                                'filter': self.module.params.get('filter'),
                                                'fields': self.module.params.get('fields')
                                                }
                                        )
        if response['count'] > 0:
            collection_access_rights = response['data']
            results['ansible_facts']['collection_access_rights'] = collection_access_rights
        return results

def main():
    CollectionAccessRightFacts()

if __name__ == '__main__':
    main()
