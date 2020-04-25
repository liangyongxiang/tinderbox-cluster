# Copyright 2013 Red Hat, Inc.
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

"""
Client side of the scheduler RPC API.
"""

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_serialization import jsonutils

import gosbs.conf
from gosbs import context
from gosbs import exception
from gosbs.i18n import _
from gosbs import objects
from gosbs.objects import base as objects_base
from gosbs.objects import service as service_obj
from gosbs import profiler
from gosbs import rpc

CONF = gosbs.conf.CONF
RPC_TOPIC = "scheduler"

LOG = logging.getLogger(__name__)
LAST_VERSION = None

@profiler.trace_cls("rpc")
class SchedulerAPI(object):
    '''Client side of the compute rpc API.

        * 5.0  - Remove 4.x compatibility
    '''

    VERSION_ALIASES = {
        'rocky': '1.0',
    }

    def __init__(self):
        super(SchedulerAPI, self).__init__()
        target = messaging.Target(topic=RPC_TOPIC, version='1.0')
        upgrade_level = CONF.upgrade_levels.scheduler
        if upgrade_level == 'auto':
            version_cap = self._determine_version_cap(target)
        else:
            version_cap = self.VERSION_ALIASES.get(upgrade_level,
                                                   upgrade_level)
        serializer = objects_base.NovaObjectSerializer()

        # NOTE(danms): We need to poke this path to register CONF options
        # that we use in self.get_client()
        rpc.get_client(target, version_cap, serializer)

        default_client = self.get_client(target, version_cap, serializer)
        self.router = rpc.ClientRouter(default_client)

    def _determine_version_cap(self, target):
        global LAST_VERSION
        if LAST_VERSION:
            return LAST_VERSION
        service_version = objects.Service.get_minimum_version(
            context.get_admin_context(), 'gosbs-scheduler')

        history = service_obj.SERVICE_VERSION_HISTORY

        # NOTE(johngarbutt) when there are no nova-compute services running we
        # get service_version == 0. In that case we do not want to cache
        # this result, because we will get a better answer next time.
        # As a sane default, return the current version.
        if service_version == 0:
            LOG.debug("Not caching compute RPC version_cap, because min "
                      "service_version is 0. Please ensure a nova-compute "
                      "service has been started. Defaulting to current "
                      "version.")
            return history[service_obj.SERVICE_VERSION]['scheduler_rpc']

        try:
            version_cap = history[service_version]['scheduler_rpc']
        except IndexError:
            LOG.error('Failed to extract compute RPC version from '
                      'service history because I am too '
                      'old (minimum version is now %(version)i)',
                      {'version': service_version})
            raise exception.ServiceTooOld(thisver=service_obj.SERVICE_VERSION,
                                          minver=service_version)
        except KeyError:
            LOG.error('Failed to extract compute RPC version from '
                      'service history for version %(version)i',
                      {'version': service_version})
            return target.version
        LAST_VERSION = version_cap
        LOG.info('Automatically selected compute RPC version %(rpc)s '
                 'from minimum service version %(service)i',
                 {'rpc': version_cap,
                  'service': service_version})
        return version_cap

    # Cells overrides this
    def get_client(self, target, version_cap, serializer):
        if CONF.rpc_response_timeout > rpc.HEARTBEAT_THRESHOLD:
            # NOTE(danms): If the operator has overridden RPC timeout
            # to be longer than rpc.HEARTBEAT_THRESHOLD then configure
            # the call monitor timeout to be the threshold to keep the
            # failure timing characteristics that our code likely
            # expects (from history) while allowing healthy calls
            # to run longer.
            cmt = rpc.HEARTBEAT_THRESHOLD
        else:
            cmt = None
        return rpc.get_client(target,
                              version_cap=version_cap,
                              serializer=serializer,
                              call_monitor_timeout=cmt)
