from ansible.module_utils.basic import AnsibleModule
from bluecat_libraries.address_manager.apiv2 import Client, MediaType

class BluecatModule():
    def __init__(self, module_args, required_if=None, bypass_checks=False,
                 no_log=False, mutually_exclusive=None, required_together=None,
                 required_one_of=None, add_file_common_args=False,
                 supports_check_mode=False, is_fact=False):

        argument_spec = dict(bc_address=dict(type='str'),
                             bc_api_username=dict(type='str'),
                             bc_api_password=dict(type='str', no_log=True)
                             )
        if is_fact:
            fact_argument_spec = dict(
                filter=dict(required=True, type='str'),
                fields=dict(type='str'),
                limit=dict(type='int', default=100)
            )
            argument_spec.update(fact_argument_spec)
        argument_spec.update(module_args)
        self.module = AnsibleModule(argument_spec=argument_spec,
                                    required_if=required_if,
                                    bypass_checks=bypass_checks,
                                    no_log=no_log,
                                    mutually_exclusive=mutually_exclusive,
                                    required_together=required_together,
                                    required_one_of=required_one_of,
                                    add_file_common_args=add_file_common_args,
                                    supports_check_mode=supports_check_mode)
        self.check_mode = self.module.check_mode
        self.headers = {"Content-Type": MediaType.JSON}
        self.client = None
        self.login(self.module.params)
        result = self.exec_module(**self.module.params)
        self.exit_json(**result)

    def login(self, params):
        self.client = Client(params.get('bc_address'))
        self.client.login(params.get('bc_api_username'), params.get('bc_api_password'))

    def logout(self):
        self.client.logout()

    def exec_module(self):
        self.fail_json(msg='Override in sub-module. Called from: {}'.format(self.__class__.__name__))

    def fail_json(self, msg, **kwargs):
        self.logout()
        self.module.fail_json(msg=msg, **kwargs)

    def exit_json(self, **kwargs):
        self.logout()
        self.module.exit_json(**kwargs)

    def get_administrative_access_right(self, userscope_id):
        filter = 'type:eq("{}") and userScope.id:eq({})'.format('AdministrativeAccessRight', userscope_id)
        access_rights = self.client.http_get('/accessRights',
                                             params={'limit': 10000,
                                                     'filter': filter
                                                     }
                                             )
        if access_rights['count'] == 0:
            return None
        else:
            return access_rights['data'][0]

    def get_access_right_by_resource_id(self, resource_id, userscope_id):
        if resource_id is None:
            resource_id = 'null'
        filter = 'resource.id:eq({}) and userScope.id:eq({})'.format(resource_id, userscope_id)
        # even though we should filter in a way that only returns one resource
        # to begin with, we have to set a pretty high limit, otherwise we don't
        # get a return value
        access_rights = self.client.http_get('/accessRights',
                                             params={'limit': 10000,
                                                     'filter': filter
                                                     }
                                             )
        if access_rights['count'] == 0:
            return None
        else:
            return access_rights['data'][0]

    def get_authenticator_by_name(self, name):
        filter = 'name:eq("{}")'.format(name)
        authenticators = self.client.http_get('/authenticators',
                                              params={'limit': 1,
                                                      'filter': filter
                                                      }
                                              )

        if authenticators['count'] == 0:
            return None
        else:
            return authenticators['data'][0]

    def get_block_by_range(self, configuration, range):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(configuration, range)
        blocks = self.client.http_get('/blocks',
                                       params={'limit': 1,
                                               'filter': filter
                                              }
                                       )
        if blocks['count'] == 0:
            return None
        else:
            return blocks['data'][0]

    def get_configuration_by_name(self, name):
        filter = f'name:eq("{name}")'
        configurations = self.client.http_get('/configurations',
                                              params={'limit': 1,
                                                      'filter': filter
                                                      }
                                              )
        if configurations['count'] == 0:
            return None
        else:
            return configurations['data'][0]


    def get_network_by_range(self, configuration, range):
        filter = 'configuration.name:eq("{}") and range:eq("{}")'.format(configuration, range)
        networks = self.client.http_get('/networks',
                                        params={'limit': 1,
                                                'filter': filter
                                               }
                                        )
        if networks['count'] == 0:
            return None
        else:
            return networks['data'][0]

    def get_zone_by_fqdn(self, configuration, fqdn):
        filter = 'configuration.name:eq("{}") and absoluteName:eq("{}")'.format(configuration, fqdn)
        zones = self.client.http_get('/zones',
                                     params={'limit': 1,
                                             'filter': filter
                                            }
                                     )
        if zones['count'] == 0:
            return None
        else:
            return zones['data'][0]

    def get_tag(self, name):
        filter = 'name:eq("{}")'.format(name)
        rr = self.client.http_get(f'/tags',
                                  params={'limit': 1,
                                          'filter': filter
                                          }
                                  )
        if rr['count'] == 0:
            return None
        else:
            return rr['data'][0]

    def get_tag_in_tag(self, name, parent):
        filter = 'name:eq("{}")'.format(name)
        parent
        rr = self.client.http_get(f'/tags/{parent_id}/tags',
                                  params={'limit': 1,
                                          'filter': filter
                                          }
                                  )
        if rr['count'] == 0:
            return None
        else:
            return rr['data'][0]

    def get_tag_in_tag_group(self, name, parent):
        filter = 'name:eq("{}")'.format(name)
        rr = self.client.http_get(f'/tagGroups/{parent_id}/tags',
                                  params={'limit': 1,
                                          'filter': filter
                                          }
                                  )
        if rr['count'] == 0:
            return None
        else:
            return rr['data'][0]

    def get_tag_group(self, name):
        filter = 'name:eq("{}")'.format(name)
        rr = self.client.http_get(f'/tagGroups',
                                  params={'limit': 1,
                                          'filter': filter
                                          }
                                  )
        if rr['count'] == 0:
            return None
        else:
            return rr['data'][0]

    def get_group_by_name(self, name):
        filter = 'name:eq("{}")'.format(name)
        groups = self.client.http_get(f'/groups',
                                      params={'limit': 1,
                                              'filter': filter
                                              }
                                      )

        if groups['count'] == 0:
            return None
        else:
            return groups['data'][0]

    def get_user_by_name(self, name):
        filter = 'name:eq("{}")'.format(name)
        users = self.client.http_get(f'/users',
                                     params={'limit': 1,
                                             'filter': filter
                                             }
                                     )

        if users['count'] == 0:
            return None
        else:
            return users['data'][0]

    def get_view_by_name(self, configuration, name):
        filter = (f'configuration.name:eq("{configuration}") and '
                  f'name:eq("{name}")')
        views = self.client.http_get('/views',
                                      params={'limit': 1,
                                              'filter': filter
                                             }
                                      )
        if views['count'] == 0:
            return None
        else:
            return views['data'][0]
