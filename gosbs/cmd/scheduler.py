# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

# Origin https://github.com/openstack/nova/blob/master/nova/cmd/compute.py
# Removed code that was not needed

"""Starter script for Gosbs Scheduler."""

import shlex
import sys

from oslo_log import log as logging

from gosbs.scheduler import rpcapi as scheduler_rpcapi
import gosbs.conf
from gosbs import config
from gosbs import objects
from gosbs.objects import base as objects_base
from gosbs import service

CONF = gosbs.conf.CONF

def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, 'gosbs')
    objects.register_all()

    objects.Service.enable_min_version_cache()
    server = service.Service.create(binary='gosbs-scheduler',
                                    topic=scheduler_rpcapi.RPC_TOPIC)
    service.serve(server)
    service.wait()
