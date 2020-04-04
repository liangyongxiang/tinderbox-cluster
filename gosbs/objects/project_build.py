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

BUILD_STATUS = ['failed', 'completed', 'in-progress', 'waiting']
def _dict_with_extra_specs(project_build_model):
    extra_specs = {}
    return dict(project_build_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _project_build_create(context, values):
    db_project_build = models.ProjectsBuilds()
    db_project_build.update(values)

    try:
        db_project_build.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'project_buildid' in e.columns:
            raise exception.ImagesIdExists(project_build_id=values['project_buildid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_project_build)


@db_api.main_context_manager.writer
def _project_build_destroy(context, project_build_uuid=None, project_builduuid=None):
    query = context.session.query(models.ProjectsBuilds)

    if project_build_id is not None:
        query.filter(models.ProjectsBuilds.uuid == project_build_uuid).delete()
    else:
        query.filter(models.ProjectsBuilds.uuid == project_builduuid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class ProjectBuild(base.NovaObject, base.NovaObjectDictCompat, ):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid': fields.UUIDField(),
        'user_id': fields.IntegerField(),
        'project_uuid': fields.UUIDField(),
        'ebuild_uuid': fields.UUIDField(),
        'status' : fields.EnumField(valid_values=BUILD_STATUS),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectBuild, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_project_builds = []

    def obj_make_compatible(self, primitive, target_version):
        super(ProjectBuild, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, project_build, db_project_build, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        project_build._context = context
        for name, field in project_build.fields.items():
            value = db_project_build[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            project_build[name] = value
        
        project_build.obj_reset_changes()
        return project_build

    @staticmethod
    @db_api.main_context_manager.reader
    def _project_build_get_query_from_db(context):
        query = context.session.query(models.ProjectsBuilds)
        return query

    @staticmethod
    @require_context
    def _project_build_get_from_db(context, uuid):
        """Returns a dict describing specific project_builds."""
        result = ProjectBuild._project_build_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(project_build_uuid=uuid)
        return result

    @staticmethod
    @require_context
    def _project_build_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = ProjectBuild._project_build_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(project_builds_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(ProjectBuild, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(ProjectBuild, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_project_build = cls._project_build_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_project_build,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_project_build = cls._project_build_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_project_build,
                                   expected_attrs=[])

    @staticmethod
    def _project_build_create(context, updates):
        return _project_build_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_project_build = self._project_build_create(context, updates)
        self._from_db_object(context, self, db_project_build)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a project_builds.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_project_build = context.session.query(models.ProjectsBuilds).\
            filter_by(id=self.id).first()
        if not db_project_build:
            raise exception.ImagesNotFound(project_build_id=self.id)
        db_project_build.update(values)
        db_project_build.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_project_build)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _project_build_destroy(context, project_build_id=None, project_buildid=None):
        _project_build_destroy(context, project_build_id=project_build_id, project_buildid=project_buildid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a project_builds
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a project_builds object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._project_build_destroy(context, project_build_id=self.id)
        else:
            self._project_build_destroy(context, project_buildid=self.project_buildid)
        #self._from_db_object(context, self, db_project_build)

    @base.remotable_classmethod
    def get_by_filters(cls, context, filters=None):
        filters = filters or {}
        db_project_build = ProjectBuild._project_build_get_query_from_db(context)
    
        if 'project_uuid' in filters:
            db_project_build = db_project_build.filter(
                models.ProjectsBuilds.project_uuid == filters['project_uuid'])
        if 'repo_uuid' in filters:
            db_project_build = db_project_build.filter(
                models.ProjectsBuilds.repo_uuid == filters['repo_uuid'])
        db_project_build = db_project_build.first()
        if not db_project_build:
            return None
        return cls._from_db_object(context, cls(context), db_project_build,
                                   expected_attrs=[])


@db_api.main_context_manager
def _project_build_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all project_buildss.
    """
    filters = filters or {}

    query = ProjectBuild._project_build_get_query_from_db(context)

    if 'project_uuid' in filters:
            query = query.filter(
                models.ProjectsBuilds.project_uuid == filters['project_uuid'])

    marker_row = None
    if marker is not None:
        marker_row = ProjectBuild._project_build_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.ProjectsBuilds,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class ProjectBuildList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('ProjectBuild'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_project_builds = _project_build_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.project_build.ProjectBuild,
                                  db_project_builds,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.ProjectsBuilds).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_project_build = context.session.query(models.ProjectsBuilds).filter_by(auto=True)
        db_project_build.update(values)
