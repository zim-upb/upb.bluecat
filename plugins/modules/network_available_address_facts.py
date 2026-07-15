#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class NetworkAvailableAddressFacts(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            collection_id=dict(type='int'),
            range=dict(type='str')
        )
        super(NetworkAvailableAddressFacts, self).__init__(self.module_args,
                                            supports_check_mode=True,
                                            is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(networks=[]))
        collection_id = None
        range = self.module.params.get('range', None)
        if range:
            response = self.client.http_get("/networks",
                                            params={'filter': f"range:eq('{range}')"}
                                            )
            if response['count'] == 0:
                self.fail_json(f"No network with range {range} found!")
                return
            if response['count'] > 1:
                self.fail_json(f"More than one network with range {range} found!")
                return
            collection_id = response['data'][0]['id']

        else:
            collection_id = self.module.params.get('collection_id')
        url = f"/networks/{collection_id}/availableAddresses"
        response = self.client.http_get(url,
                                        params={'limit': self.module.params.get('limit'),
                                                'filter': self.module.params.get('filter'),
                                                'fields': self.module.params.get('fields')
                                                }
                                        )
        if response['count'] > 0:
            available_addresses = response['data']
            results['ansible_facts']['available_addresses'] = available_addresses
        return results

def main():
    NetworkAvailableAddressFacts()

if __name__ == '__main__':
    main()
