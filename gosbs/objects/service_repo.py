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
REPO_STATUSES = ['failed', 'completed', 'in-progress', 'waiting', 'update_db', 'rebuild_db']

def _dict_with_extra_specs(service_repo_model):
    extra_specs = {}
    return dict(service_repo_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _service_repo_create(context, values):
    db_service_repo = models.ServicesRepos()
    db_service_repo.update(values)

    try:
        db_service_repo.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'service_repoid' in e.columns:
            raise exception.ImagesIdExists(service_repo_id=values['service_repoid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_service_repo)


@db_api.main_context_manager.writer
def _service_repo_destroy(context, service_repo_id=None, service_repoid=None):
    query = context.session.query(models.ServicesRepos)

    if service_repo_id is not None:
        query.filter(models.ServicesRepos.id == service_repo_id).delete()
    else:
        query.filter(models.ServicesRepos.id == service_repoid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class ServiceRepo(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject2,):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(read_only=True),
        'repo_uuid': fields.UUIDField(),
        'service_uuid': fields.UUIDField(),
        'auto' : fields.BooleanField(),
        'status' : fields.EnumField(valid_values=REPO_STATUSES),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceRepo, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_service_repos = []

    def obj_make_compatible(self, primitive, target_version):
        super(ServiceRepo, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, service_repo, db_service_repo, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        service_repo._context = context
        for name, field in service_repo.fields.items():
            value = db_service_repo[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            service_repo[name] = value
        
        service_repo.obj_reset_changes()
        return service_repo

    @staticmethod
    @db_api.main_context_manager.reader
    def _service_repo_get_query_from_db(context):
        query = context.session.query(models.ServicesRepos)
        return query

    @staticmethod
    @require_context
    def _service_repo_get_from_db(context, id):
        """Returns a dict describing specific service_repos."""
        result = ServiceRepo._service_repo_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(service_repo_id=id)
        return result

    @staticmethod
    @require_context
    def _service_repo_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = ServiceRepo._service_repo_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(service_repos_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(ServiceRepo, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(ServiceRepo, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_service_repo = cls._service_repo_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_service_repo,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_service_repo = cls._service_repo_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_service_repo,
                                   expected_attrs=[])

    @staticmethod
    def _service_repo_create(context, updates):
        return _service_repo_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_service_repo = self._service_repo_create(context, updates)
        self._from_db_object(context, self, db_service_repo)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a service_repos.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_service_repo = context.session.query(models.ServicesRepos).\
            filter_by(id=self.id).first()
        if not db_service_repo:
            raise exception.ImagesNotFound(service_repo_id=self.id)
        db_service_repo.update(values)
        db_service_repo.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_service_repo)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _service_repo_destroy(context, service_repo_id=None, service_repoid=None):
        _service_repo_destroy(context, service_repo_id=service_repo_id, service_repoid=service_repoid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a service_repos
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a service_repos object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._service_repo_destroy(context, service_repo_id=self.id)
        else:
            self._service_repo_destroy(context, service_repoid=self.service_repoid)
        #self._from_db_object(context, self, db_service_repo)

    @base.remotable_classmethod
    def get_by_filters(cls, context, filters=None):
        filters = filters or {}
        db_service_repo = ServiceRepo._service_repo_get_query_from_db(context)
    
        if 'status' in filters:
            db_service_repo = db_service_repo.filter(
                models.ServicesRepos.status == filters['status'])
        if 'repo_uuid' in filters:
            db_service_repo = db_service_repo.filter(
                models.ServicesRepos.repo_uuid == filters['repo_uuid'])
        if 'service_uuid' in filters:
            db_service_repo = db_service_repo.filter(
                models.ServicesRepos.service_uuid == filters['service_uuid'])
        db_service_repo = db_service_repo.first()
        if not db_service_repo:
            return None
        return cls._from_db_object(context, cls(context), db_service_repo,
                                   expected_attrs=[])


@db_api.main_context_manager
def _service_repo_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all service_reposs.
    """
    filters = filters or {}

    query = ServiceRepo._service_repo_get_query_from_db(context)

    if 'service_uuid' in filters:
            query = query.filter(
                models.ServicesRepos.service_uuid == filters['service_uuid'])
    if 'status' in filters:
            query = query.filter(
                models.ServicesRepos.status == filters['status'])
    if 'repo_uuid' in filters:
            query = query.filter(
                models.ServicesRepos.repo_uuid == filters['repo_uuid'])
    if not query:
        return None
    marker_row = None
    if marker is not None:
        marker_row = ServiceRepo._service_repo_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.ServicesRepos,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class ServiceRepoList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('ServiceRepo'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_service_repos = _service_repo_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.service_repo.ServiceRepo,
                                  db_service_repos,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.ServicesRepos).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_service_repo = context.session.query(models.ServicesRepos).filter_by(auto=True)
        db_service_repo.update(values)
