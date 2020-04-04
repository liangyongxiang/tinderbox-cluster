# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
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

# Origin https://github.com/openstack/nova/blob/master/nova/compute/manager.py
# We have change the code so it will fit what we need.
# It need more cleaning.

"""Handles all processes relating to instances (guest vms).

The :py:class:`ComputeManager` class is a :py:class:`nova.manager.Manager` that
handles RPC calls relating to creating instances.  It is responsible for
building a disk image, launching it via the underlying virtualization driver,
responding to calls to check its state, attaching persistent storage, and
terminating it.

"""
#import functools
#import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from importlib import import_module
import pytz
import sys

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import periodic_task
from oslo_utils import timeutils
from openstack import connection

from gosbs.scheduler import rpcapi as scheduler_rpcapi
from gosbs import rpc
#from gosbs import exception_wrapper
from gosbs import manager
from gosbs import objects
from gosbs.objects import base as obj_base
from gosbs.objects import fields
from gosbs.tasks import scheduler as scheduler_tasks
from gosbs.common.task import run_task

import gosbs.conf

CONF = gosbs.conf.CONF

LOG = logging.getLogger(__name__)

#get_notifier = functools.partial(rpc.get_notifier, service='scheduler')
#wrap_exception = functools.partial(exception_wrapper.wrap_exception,
#                                   get_notifier=get_notifier,
#                                   binary='gobs-scheduler')

class SchedulerManager(manager.Manager):
    """Manages the running instances from creation to destruction."""

    #target = messaging.Target(version='1.0')

    def __init__(self, *args, **kwargs):
        """Load configuration options and connect to the hypervisor."""
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()

        super(SchedulerManager, self).__init__(service_name="scheduler",
                                             *args, **kwargs)


    def init_host(self):
        context = gosbs.context.get_admin_context()

    def pre_start_hook(self):
        context = gosbs.context.get_admin_context()
        self.openstack_conn = connection.Connection(
            region_name = CONF.keystone.region_name,
            auth=dict(
                auth_url = CONF.keystone.auth_url,
                username = CONF.keystone.username,
                password = CONF.keystone.password,
                project_id = CONF.keystone.project_id,
                user_domain_id = CONF.keystone.user_domain_name),
            scheduler_api_version = CONF.keystone.auth_version,
            identity_interface= CONF.keystone.identity_interface)
        self.service_ref = objects.Service.get_by_host_and_topic(
            context, self.host, "scheduler")
        scheduler_tasks.activete_all_tasks(context, self.service_ref.uuid)

    def reset(self):
        LOG.info('Reloading scheduler RPC API')
        scheduler_rpcapi.LAST_VERSION = None
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()

    @periodic_task.periodic_task
    def update_repo_task(self, context):
        task_name = 'update_repos'
        LOG.debug("Runing task %s", task_name)
        filters = { 'status' : 'waiting', 
                    'name' : task_name,
                    'service_uuid' : self.service_ref.uuid,
                }
        run_task(context, filters, self.service_ref)

    @periodic_task.periodic_task
    def update_git_task(self, context):
        task_name = 'update_git'
        LOG.debug("Runing task %s", task_name)
        filters = { 'status' : 'waiting', 
                    'name' : task_name,
                    'service_uuid' : self.service_ref.uuid,
                }
        run_task(context, filters, self.service_ref)

    @periodic_task.periodic_task
    def rebuild_db_task(self, context):
        task_name = 'rebuild_db'
        LOG.debug("Runing task %s", task_name)
        filters = { 'status' : 'waiting', 
                    'name' : task_name,
                    'service_uuid' : self.service_ref.uuid,
                }
        run_task(context, filters, self.service_ref)

    @periodic_task.periodic_task
    def update_db_task(self, context):
        task_name = 'update_db'
        LOG.debug("Runing task %s", task_name)
        filters = { 'status' : 'waiting', 
                    'name' : task_name,
                    'service_uuid' : self.service_ref.uuid,
                }
        run_task(context, filters, self.service_ref)
