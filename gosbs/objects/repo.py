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
REPO_STATUSES = ['failed', 'completed', 'in-progress', 'waiting']
REPO2_STATUSES = ['failed', 'completed', 'in-progress', 'waiting', 'db_rebuild']
REPO_TYPE = ['ebuild', 'project']

def _dict_with_extra_specs(repo_model):
    extra_specs = {}
    return dict(repo_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _repo_create(context, values):
    db_repo = models.Repos()
    db_repo.update(values)

    try:
        db_repo.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'repoid' in e.columns:
            raise exception.ImagesIdExists(repo_id=values['repoid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_repo)


@db_api.main_context_manager.writer
def _repo_destroy(context, repo_id=None, repoid=None):
    query = context.session.query(models.Repos)

    if repo_id is not None:
        query.filter(models.Repos.uuid == repo_uuid).delete()
    else:
        query.filter(models.Repos.repouuid == repouuid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Repo(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject2):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid': fields.UUIDField(),
        'name': fields.StringField(),
        'status' : fields.EnumField(valid_values=REPO_STATUSES),
        'description' : fields.StringField(),
        'src_url': fields.StringField(),
        'auto' : fields.BooleanField(),
        'repo_type' : fields.EnumField(valid_values=REPO_TYPE),
        }

    def __init__(self, *args, **kwargs):
        super(Repo, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_projects = []

    def obj_make_compatible(self, primitive, target_version):
        super(Repo, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, repo, db_repo, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        repo._context = context
        for name, field in repo.fields.items():
            value = db_repo[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            repo[name] = value
        
        repo.obj_reset_changes()
        return repo

    @staticmethod
    @db_api.main_context_manager.reader
    def _repo_get_query_from_db(context):
        query = context.session.query(models.Repos)
        return query

    @staticmethod
    @require_context
    def _repo_get_from_db(context, uuid):
        """Returns a dict describing specific repos."""
        result = Repo._repo_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(repo_id=uuid)
        return result

    @staticmethod
    @require_context
    def _repo_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Repo._repo_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(repos_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Repo, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Repo, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_repo = cls._repo_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_repo,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_repo = cls._repo_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_repo,
                                   expected_attrs=[])

    @staticmethod
    def _repo_create(context, updates):
        return _repo_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_repo = self._repo_create(context, updates)
        self._from_db_object(context, self, db_repo)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a repos.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_repo = context.session.query(models.Repos).\
            filter_by(uuid=self.uuid).first()
        if not db_repo:
            raise exception.ImagesNotFound(repo_uuid=self.uuid)
        db_repo.update(values)
        db_repo.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_repo)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _repo_destroy(context, repo_uuid=None, repouuid=None):
        _repo_destroy(context, repo_uuid=repo_uuid, repouuid=repouuid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a repos
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a repos object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'uuid' in self:
            self._repo_destroy(context, repo_uuid=self.uuid)
        else:
            self._repo_destroy(context, repouuid=self.repouuid)
        #self._from_db_object(context, self, db_repo)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_repo = Repo._repo_get_query_from_db(context)
    
        if 'status' in filters:
            db_repo = db_repo.filter(
                models.Repos.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_repo,
                                   expected_attrs=[])


@db_api.main_context_manager
def _repo_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all reposs.
    """
    filters = filters or {}

    query = Repo._repo_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Repos.status == filters['status'])
    if 'repo_type' in filters:
            query = query.filter(
                models.Repos.repo_type == filters['repo_type'])
    if 'deleted' in filters:
            query = query.filter(
                models.Repos.deleted == filters['deleted'])

    marker_row = None
    if marker is not None:
        marker_row = Repo._repo_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Repos,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class RepoList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Repo'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_repos = _repo_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.repo.Repo,
                                  db_repos,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Repos).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_repo = context.session.query(models.Repos).filter_by(auto=True)
        db_repo.update(values)
