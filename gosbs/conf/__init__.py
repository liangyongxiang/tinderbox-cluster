# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
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

# This package got introduced during the Mitaka cycle in 2015 to
# have a central place where the config options of Nova can be maintained.
# For more background see the blueprint "centralize-config-options"

# Origin https://github.com/openstack/nova/blob/master/nova/conf/__init__.py
# Import only what we need on gosbs

from oslo_config import cfg

from gosbs.conf import base
from gosbs.conf import database
from gosbs.conf import keystone
from gosbs.conf import netconf
from gosbs.conf import notifications
from gosbs.conf import paths
from gosbs.conf import rpc
from gosbs.conf import scheduler
from gosbs.conf import service
from gosbs.conf import upgrade_levels

CONF = cfg.CONF

base.register_opts(CONF)
database.register_opts(CONF)
keystone.register_opts(CONF)
netconf.register_opts(CONF)
notifications.register_opts(CONF)
paths.register_opts(CONF)
rpc.register_opts(CONF)
scheduler.register_opts(CONF)
service.register_opts(CONF)
upgrade_levels.register_opts(CONF)
