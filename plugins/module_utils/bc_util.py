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

