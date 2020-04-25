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

def _dict_with_extra_specs(project_repo_model):
    extra_specs = {}
    return dict(project_repo_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _project_repo_create(context, values):
    db_project_repo = models.ProjectsRepos()
    db_project_repo.update(values)

    try:
        db_project_repo.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'project_repoid' in e.columns:
            raise exception.ImagesIdExists(project_repo_id=values['project_repoid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_project_repo)


@db_api.main_context_manager.writer
def _project_repo_destroy(context, project_repo_id=None, project_repoid=None):
    query = context.session.query(models.ProjectsRepos)

    if project_repo_id is not None:
        query.filter(models.ProjectsRepos.uuid == project_repo_id).delete()
    else:
        query.filter(models.ProjectsRepos.uuid == project_repoid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class ProjectRepo(base.NovaObject, base.NovaObjectDictCompat, ):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'repo_uuid': fields.UUIDField(),
        'project_uuid': fields.UUIDField(),
        'auto' : fields.BooleanField(),
        'build' : fields.BooleanField(),
        'test' : fields.BooleanField(),
        'qa' : fields.BooleanField(),
        'repoman' : fields.BooleanField(),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectRepo, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_project_repos = []

    def obj_make_compatible(self, primitive, target_version):
        super(ProjectRepo, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, project_repo, db_project_repo, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        project_repo._context = context
        for name, field in project_repo.fields.items():
            value = db_project_repo[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            project_repo[name] = value
        
        project_repo.obj_reset_changes()
        return project_repo

    @staticmethod
    @db_api.main_context_manager.reader
    def _project_repo_get_query_from_db(context):
        query = context.session.query(models.ProjectsRepos)
        return query

    @staticmethod
    @require_context
    def _project_repo_get_from_db(context, id):
        """Returns a dict describing specific project_repos."""
        result = ProjectRepo._project_repo_get_query_from_db(context).\
                        filter_by(uuid=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(project_repo_id=id)
        return result

    @staticmethod
    @require_context
    def _project_repo_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = ProjectRepo._project_repo_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(project_repos_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(ProjectRepo, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(ProjectRepo, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_project_repo = cls._project_repo_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_project_repo,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_project_repo = cls._project_repo_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_project_repo,
                                   expected_attrs=[])

    @staticmethod
    def _project_repo_create(context, updates):
        return _project_repo_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_project_repo = self._project_repo_create(context, updates)
        self._from_db_object(context, self, db_project_repo)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a project_repos.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_project_repo = context.session.query(models.ProjectsRepos).\
            filter_by(uuid=self.id).first()
        if not db_project_repo:
            raise exception.ImagesNotFound(project_repo_id=self.id)
        db_project_repo.update(values)
        db_project_repo.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_project_repo)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _project_repo_destroy(context, project_repo_id=None, project_repoid=None):
        _project_repo_destroy(context, project_repo_id=project_repo_id, project_repoid=project_repoid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a project_repos
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a project_repos object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._project_repo_destroy(context, project_repo_id=self.id)
        else:
            self._project_repo_destroy(context, project_repoid=self.project_repoid)
        #self._from_db_object(context, self, db_project_repo)

    @base.remotable_classmethod
    def get_by_filters(cls, context, filters=None):
        filters = filters or {}
        db_project_repo = ProjectRepo._project_repo_get_query_from_db(context)
    
        if 'project_uuid' in filters:
            db_project_repo = db_project_repo.filter(
                models.ProjectsRepos.project_uuid == filters['project_uuid'])
        if 'repo_uuid' in filters:
            db_project_repo = db_project_repo.filter(
                models.ProjectsRepos.repo_uuid == filters['repo_uuid'])
        db_project_repo = db_project_repo.first()
        if not db_project_repo:
            return None
        return cls._from_db_object(context, cls(context), db_project_repo,
                                   expected_attrs=[])


@db_api.main_context_manager
def _project_repo_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all project_reposs.
    """
    filters = filters or {}

    query = ProjectRepo._project_repo_get_query_from_db(context)

    if 'project_uuid' in filters:
            query = query.filter(
                models.ProjectsRepos.project_uuid == filters['project_uuid'])
    if 'repo_uuid' in filters:
            query = query.filter(
                models.ProjectsRepos.repo_uuid == filters['repo_uuid'])
    if 'build' in filters:
            query = query.filter(
                models.ProjectsRepos.build == filters['build'])

    marker_row = None
    if marker is not None:
        marker_row = ProjectRepo._project_repo_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.ProjectsRepos,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class ProjectRepoList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('ProjectRepo'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_project_repos = _project_repo_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.project_repo.ProjectRepo,
                                  db_project_repos,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.ProjectsRepos).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_project_repo = context.session.query(models.ProjectsRepos).filter_by(auto=True)
        db_project_repo.update(values)
