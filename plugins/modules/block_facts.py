#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class BlockFacts(BluecatModule):
    def __init__(self):
        self.module_args = dict()
        super(BlockFacts, self).__init__(self.module_args,
                                         supports_check_mode=True,
                                         is_fact=True)

    def exec_module(self, **kwargs):
        results = dict(ansible_facts=dict(blocks=[]))
        response = self.client.http_get('/blocks',
                                        params={'limit': self.module.params.get('limit'),
                                                'filter': self.module.params.get('filter'),
                                                'fields': self.module.params.get('fields')
                                                }
                                        )
        if response['count'] > 0:
            blocks = response['data']
            results['ansible_facts']['blocks'] = blocks
        return results

def main():
    BlockFacts()

if __name__ == '__main__':
    main()
