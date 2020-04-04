# Copyright 1999-2020 Gentoo Authors
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
from importlib import import_module

from oslo_utils import uuidutils

from gosbs import objects

def time_to_run_task(task_db):
    task_time_now = datetime.now().replace(tzinfo=pytz.UTC)
    task_time_when = task_db.last + relativedelta(years=+(task_db.run.year - 1))
    task_time_when = task_time_when + relativedelta(months=+(task_db.run.month - 1))
    task_time_when = task_time_when + relativedelta(days=+(task_db.run.day -1))
    task_time_when = task_time_when + relativedelta(hours=+task_db.run.hour)
    task_time_when = task_time_when + relativedelta(minutes=+task_db.run.minute)
    if task_time_when < task_time_now:
        return True
    else:
        return False

def create_task_db(context, name, run, repet, service_uuid):
    task_db = objects.task.Task()
    task_db.uuid = uuidutils.generate_uuid()
    task_db.name = name
    task_db.service_uuid = service_uuid
    task_db.run = run
    task_db.repet = repet
    task_db.status = 'waiting'
    task_db.last = datetime.now().replace(tzinfo=pytz.UTC)
    task_db.create(context)
    return task_db

def check_task_db(context, name, run, repet, service_uuid):
    filters = { 
                   'name' : name,
                   'repet' : repet,
                   }
    task_db = objects.task.Task.get_by_server_uuid(context, service_uuid, filters=filters)
    if task_db is None:
        task_db = create_task_db(context, name, run, repet, service_uuid)
    task_db.status = 'waiting'
    task_db.save(context)

def run_task(context, filters, service_ref):
    for task_db in objects.task.TaskList.get_all(context, filters=filters, sort_key='priority'):
        if time_to_run_task(task_db):
            task_db.status = 'in-progress'
            task_db.save(context)
            module_to_run = import_module('.' + task_db.name , 'gosbs.tasks.' + service_ref.topic)
            module_to_run.task(context, service_ref.uuid)
            if task_db.repet:
                task_db.status = 'waiting'
                task_db.last = datetime.now().replace(tzinfo=pytz.UTC)
                task_db.save(context)
            else:
                task_db.destroy(context)
