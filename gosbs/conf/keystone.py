#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Origin https://github.com/openstack/nova/blob/master/nova/conf/keystone.py

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg

from gosbs.conf import utils as confutils


DEFAULT_SERVICE_TYPE = 'identity'

keystone_group = cfg.OptGroup(
    'keystone',
    title='Keystone Options',
    help='Configuration options for the identity service')

keystone_opts = [
    cfg.StrOpt('auth_version',
               default='3',
               help='API version of the admin Identity API endpoint. (string value)'),
    cfg.StrOpt('identity_interface',
               default='',
               help=''),
    cfg.StrOpt('auth_url',
               default='',
               help=''),
    cfg.StrOpt('project_domain_name',
               default='',
               help=''),
    cfg.StrOpt('user_domain_name',
               default='',
               help=''),
    cfg.StrOpt('project_id',
               default='',
               help=''),
    cfg.StrOpt('username',
               default='',
               help=''),
    cfg.StrOpt('password',
               secret=True,
               default='',
               help=''),
]


def register_opts(conf):
    conf.register_group(keystone_group)
    confutils.register_ksa_opts(conf, keystone_group.name,
                                DEFAULT_SERVICE_TYPE, include_auth=True)
    conf.register_opts(keystone_opts, group=keystone_group)


def list_opts():
    return {
        keystone_group: (
            ks_loading.get_session_conf_options() +
            confutils.get_ksa_adapter_opts(DEFAULT_SERVICE_TYPE) +
            keystone_opts
        )
    }
