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
PROJECT_STATUS = ['failed', 'completed', 'in-progress', 'waiting', 'stopped']

def _dict_with_extra_specs(project_model):
    extra_specs = {}
    return dict(project_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _project_create(context, values):
    db_project = models.Projects()
    db_project.update(values)

    try:
        db_project.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'project_uuid' in e.columns:
            raise exception.ImagesIdExists(project_uuid=values['projectuuid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_project)


@db_api.main_context_manager.writer
def _project_destroy(context, project_uuid=None, projectuuid=None):
    query = context.session.query(models.Projects)

    if project_id is not None:
        query.filter(models.Projects.uuid == project_uuid).delete()
    else:
        query.filter(models.Projects.uuid == projectuuid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Project(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject2):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid': fields.UUIDField(),
        'name': fields.StringField(),
        'active' : fields.BooleanField(),
        'auto' : fields.BooleanField(),
        }

    def __init__(self, *args, **kwargs):
        super(Project, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_projects = []

    def obj_make_compatible(self, primitive, target_version):
        super(Project, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, project, db_project, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        project._context = context
        for name, field in project.fields.items():
            value = db_project[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            project[name] = value
        
        project.obj_reset_changes()
        return project

    @staticmethod
    @db_api.main_context_manager.reader
    def _project_get_query_from_db(context):
        query = context.session.query(models.Projects)
        return query

    @staticmethod
    @require_context
    def _project_get_from_db(context, uuid):
        """Returns a dict describing specific projects."""
        result = Project._project_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(project_uuid=uuid)
        return result

    @staticmethod
    @require_context
    def _project_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Project._project_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(projects_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Project, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Project, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_project = cls._project_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_project,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_project = cls._project_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_project,
                                   expected_attrs=[])

    @staticmethod
    def _project_create(context, updates):
        return _project_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_project = self._project_create(context, updates)
        self._from_db_object(context, self, db_project)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a projects.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_project = context.session.query(models.Projects).\
            filter_by(uuid=self.uuid).first()
        if not db_project:
            raise exception.ImagesNotFound(project_uuid=self.uuid)
        db_project.update(values)
        db_project.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_project)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _project_destroy(context, project_uuid=None, projectuuid=None):
        _project_destroy(context, project_uuid=project_uuid, projectuuid=projectuuid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a projects
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a projects object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'uuid' in self:
            self._project_destroy(context, project_uuid=self.uuid)
        else:
            self._project_destroy(context, projectuuid=self.projectuuid)
        #self._from_db_object(context, self, db_project)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_project = Project._project_get_query_from_db(context)
    
        if 'status' in filters:
            db_project = db_project.filter(
                models.Projects.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_project,
                                   expected_attrs=[])


@db_api.main_context_manager
def _project_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all projectss.
    """
    filters = filters or {}

    query = Project._project_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Projects.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = Project._project_get_query_from_db(context).\
                    filter_by(uuid=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Projects,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class ProjectList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Project'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_projects = _project_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.project.Project,
                                  db_projects,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Projects).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_project = context.session.query(models.Projects).filter_by(auto=True)
        db_project.update(values)
