# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
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

# Origin https://github.com/openstack/nova/blob/master/nova/config.py

from oslo_log import log
from oslo_utils import importutils

from gosbs import middleware
import gosbs.conf
from gosbs.db.sqlalchemy import api as sqlalchemy_api
from gosbs import rpc
from gosbs import version

CONF = gosbs.conf.CONF

def parse_args(argv, default_config_files=None, configure_db=True,
               init_rpc=True):
    log.register_options(CONF)
    extra_default_log_levels = []

    log.set_defaults(default_log_levels=log.get_default_log_levels() +
                     extra_default_log_levels)
    rpc.set_defaults(control_exchange='gosbs')
    middleware.set_defaults()

    CONF(argv[1:],
         project='gosbs',
         version=version.version_string(),
         default_config_files=default_config_files)

    if init_rpc:
        rpc.init(CONF)

    if configure_db:
        sqlalchemy_api.configure(CONF)
