#    Copyright 2013 Red Hat, Inc
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

# Origin https://github.com/openstack/nova/blob/master/nova/objects/flavor.py
# We have change the code so it will fit what we need.
# It need more cleaning.

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import utils as sqlalchemyutils
from oslo_utils import versionutils
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql import true

import gosbs.conf
from gosbs.db.sqlalchemy import api as db_api
from gosbs.db.sqlalchemy.api import require_context
from gosbs.db.sqlalchemy import models
from gosbs import exception
from gosbs import objects
from gosbs.objects import base
from gosbs.objects import fields

CONF = gosbs.conf.CONF
TASK_STATUSES = ['failed', 'completed', 'in-progress', 'waiting']

def _dict_with_extra_specs(task_model):
    extra_specs = {}
    return dict(task_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _task_create(context, values):
    db_task = models.Tasks()
    db_task.update(values)

    try:
        db_task.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'taskid' in e.columns:
            raise exception.ImagesIdExists(task_id=values['taskid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_task)


@db_api.main_context_manager.writer
def _task_destroy(context, task_id=None, taskid=None):
    query = context.session.query(models.Tasks)

    if task_id is not None:
        query.filter(models.Tasks.id == task_id).delete()
    else:
        query.filter(models.Tasks.taskid == taskid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Task(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid': fields.UUIDField(),
        'name': fields.StringField(),
        'service_uuid': fields.UUIDField(),
        'repet': fields.BooleanField(),
        'run': fields.DateTimeField(nullable=True),
        'status' : fields.EnumField(valid_values=TASK_STATUSES),
        'last' : fields.DateTimeField(nullable=True),
        'priority' : fields.IntegerField(default=5),
        }

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_projects = []

    def obj_make_compatible(self, primitive, target_version):
        super(Task, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, task, db_task, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        task._context = context
        for name, field in task.fields.items():
            value = db_task[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            task[name] = value
        
        task.obj_reset_changes()
        return task

    @staticmethod
    @db_api.main_context_manager.reader
    def _task_get_query_from_db(context):
        query = context.session.query(models.Tasks)
        return query

    @staticmethod
    @require_context
    def _task_get_from_db(context, uuid):
        """Returns a dict describing specific tasks."""
        result = Task._task_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(task_id=uuid)
        return result

    @staticmethod
    @require_context
    def _task_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Task._task_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(tasks_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Task, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Task, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_task = cls._task_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_task,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_task = cls._task_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_task,
                                   expected_attrs=[])

    @base.remotable_classmethod
    def get_by_server_uuid(cls, context, service_uuid, filters=None):
        filters = filters or {}
        db_task = Task._task_get_query_from_db(context)
        
        db_task = db_task.filter_by(service_uuid=service_uuid)
        if 'repet' in filters:
            db_task = db_task.filter(
                models.Tasks.repet == filters['repet'])
        if 'name' in filters:
            db_task = db_task.filter(
                models.Tasks.name == filters['name'])
        db_task = db_task.first()
        if not db_task:
            return None
        return cls._from_db_object(context, cls(context), db_task,
                                   expected_attrs=[])

    @staticmethod
    def _task_create(context, updates):
        return _task_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_task = self._task_create(context, updates)
        self._from_db_object(context, self, db_task)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a tasks.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_task = context.session.query(models.Tasks).\
            filter_by(uuid=self.uuid).first()
        if not db_task:
            raise exception.ImagesNotFound(task_id=self.uuid)
        db_task.update(values)
        db_task.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_task)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _task_destroy(context, task_id=None, taskid=None):
        _task_destroy(context, task_id=task_id, taskid=taskid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a tasks
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a tasks object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._task_destroy(context, task_id=self.uuid)
        else:
            self._task_destroy(context, taskid=self.taskid)
        #self._from_db_object(context, self, db_task)

@db_api.main_context_manager
def _task_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all taskss.
    """
    filters = filters or {}

    query = Task._task_get_query_from_db(context)

    if 'name' in filters:
        query = query.filter(
                models.Tasks.name == filters['name'])

    if 'service_uuid' in filters:
        query = query.filter(
                models.Tasks.service_uuid == filters['service_uuid'])

    if 'status' in filters:
        query = query.filter(
                models.Tasks.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = Task._task_get_query_from_db(context).\
                    filter_by(uuid=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Tasks,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class TaskList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Task'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_tasks = _task_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.task.Task,
                                  db_tasks,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Tasks).delete()
