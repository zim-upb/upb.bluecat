#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class ResourceRecordFacts(BluecatModule):
    def __init__(self):
        self.module_args = dict()

        super(ResourceRecordFacts, self).__init__(self.module_args,
                                           supports_check_mode=True,
                                           is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(resource_records=[]))
        response = self.client.http_get('/resource_records',
                                        params={'limit': self.module.params.get('limit'),
                                                'filter': self.module.params.get('filter'),
                                                'fields': self.module.params.get('fields')
                                                }
                                        )
        if response['count'] > 0:
            resource_records = response['data']
            results['ansible_facts']['resource_records'] = resource_records
        return results

def main():
    ResourceRecordFacts()

if __name__ == '__main__':
    main()
