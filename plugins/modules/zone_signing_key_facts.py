#!/usr/bin/python

# Copyright: (c) 2026, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class ZoneSigningKeys(BluecatModule):
    def __init__(self):
        self.module_args = dict(zone=dict(type='str', required=True),
                                configuration=dict(type='str', required=True))

        super(ZoneSigningKeys, self).__init__(self.module_args,
                                              supports_check_mode=True,
                                              is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(signing_keys=[]))
        configuration = self.module.params.get('configuration')
        zone = self.module.params.get('zone')
        collection_id = self.get_zone_by_fqdn(configuration, zone)['id']
        response = self.client.http_get(f'/zones/{collection_id}/signingKeys',
                                        params={'limit': self.module.params.get('limit'),
                                                'filter': self.module.params.get('filter'),
                                                'fields': self.module.params.get('fields')
                                                }
                                        )
        if response['count'] > 0:
            signing_keys = response['data']
            results['ansible_facts']['signing_keys'] = signing_keys
        return results

def main():
    ZoneSigningKeys()

if __name__ == '__main__':
    main()
