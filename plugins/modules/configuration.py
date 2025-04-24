#!/usr/bin/python

# Copyright: (c) 2025, Philipp Fromme <philipp.fromme@uni-paderborn.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json

from ansible_collections.local.bluecat.plugins.module_utils.bc_util import BluecatModule

class Configuration(BluecatModule):
    def __init__(self):
        self.module_args = dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            description=dict(type='str', default=None),
            dnsFeedEnabled=dict(type='bool', default=False),
            dnsConfigurationValidationEnabled=dict(type='bool', default=False),
            dnsZoneValidationEnabled=dict(type='bool', default=False),
            checkIntegrityValidation=dict(type='str', default="NONE"),
            checkMxCnameValidation=dict(type='str', default="WARN"),
            checkMxValidation=dict(type='str', default="WARN"),
            checkNamesValidation=dict(type='str', default="WARN"),
            checkWildcardValidation=dict(type='str', default="WARN"),
            dhcpConfigurationValidationEnabled=dict(type='bool', default=False),
            checkNsValidation=dict(type='str', default="WARN"),
            dnsOptionInheritanceEnabled=dict(type='bool', default=True),
            checkSrvCnameValidation=dict(type='str', default="WARN"),
            keyAutoRegenerationEnabled=dict(type='bool', default=False),
            dataCheckerEnabled=dict(type='bool', default=False),
            serverMonitoringEnabled=dict(type='bool', default=True)
        )


        super(Configuration, self).__init__(self.module_args,
                                            supports_check_mode=True)

    def exec_module(self, **kwargs):
        config = self.get_configuration() or dict()
        id = config.get('id')
        state = self.module.params.get('state')
        if state == 'present':
            if id == None:
                self.create_configuration()
            elif self.compare_data(config):
                self.update_configuration(id)
        elif state == 'absent':
            self.delete_configuration(id)
        result = None
        changed = False
        self.exit_json(changed=changed, result=str(result))

    def get_configuration(self):
        filter = 'name:eq("{}")'.format(self.module.params.get('name'))
        configurations = self.client.http_get('/configurations',
                                              params={'limit': 100000,
                                                      'filter': filter
                                                     }
                                              )
        if configurations['count'] == 0:
            return None
        else:
            return configurations['data'][0]

    def create_configuration(self):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_post('/configurations',
                                            data=data,
                                            headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def update_configuration(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            data = self.build_data()
            result = self.client.http_put(f'/configurations/{id}',
                                          data=data,
                                          headers=self.headers)
        self.exit_json(changed=changed, result=str(result))

    def delete_configuration(self, id):
        changed = True
        result = None
        if not self.module.check_mode:
            result = self.client.http_delete(f'/configurations/{id}')
        self.exit_json(changed=changed, result=str(result))

    def build_data(self):
        data = dict()
        data['name'] = self.module.params.get('name')
        data['description'] = self.module.params.get('description')
        data['dnsFeedEnabled'] = self.module.params.get('dnsFeedEnabled')
        data['dnsConfigurationValidationEnabled'] = self.module.params.get('dnsConfigurationValidationEnabled')
        data['dnsZoneValidationEnabled'] = self.module.params.get('dnsZoneValidationEnabled')
        data['checkIntegrityValidation'] = self.module.params.get('checkIntegrityValidation')
        data['checkMxCnameValidation'] = self.module.params.get('checkMxCnameValidation')
        data['checkMxValidation'] = self.module.params.get('checkMxValidation')
        data['checkNamesValidation'] = self.module.params.get('checkNamesValidation')
        data['checkWildcardValidation'] = self.module.params.get('checkWildcardValidation')
        data['dhcpConfigurationValidationEnabled'] = self.module.params.get('dhcpConfigurationValidationEnabled')
        data['checkNsValidation'] = self.module.params.get('checkNsValidation')
        data['dnsOptionInheritanceEnabled'] = self.module.params.get('dnsOptionInheritanceEnabled')
        data['checkSrvCnameValidation'] = self.module.params.get('checkSrvCnameValidation')
        data['keyAutoRegenerationEnabled'] = self.module.params.get('keyAutoRegenerationEnabled')
        data['dataCheckerEnabled'] = self.module.params.get('dataCheckerEnabled')
        data['serverMonitoringEnabled'] = self.module.params.get('serverMonitoringEnabled')
        data = json.dumps(data)
        return data

    def compare_data(self, configuration):
        data = json.loads(self.build_data())
        for key, value in data.items():
            if configuration[key] != value:
                return True
        return False

def main():
    Configuration()

if __name__ == '__main__':
    main()
