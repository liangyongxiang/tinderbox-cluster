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
PROJECT_STATUS = ['failed', 'completed', 'in-progress', 'waiting']

def _dict_with_extra_specs(build_iuse_model):
    extra_specs = {}
    return dict(build_iuse_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _build_iuse_create(context, values):
    db_build_iuse = models.BuildsIUses()
    db_build_iuse.update(values)

    try:
        db_build_iuse.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'build_iuseid' in e.columns:
            raise exception.ImagesIdExists(build_iuse_id=values['build_iuseid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_build_iuse)


@db_api.main_context_manager.writer
def _build_iuse_destroy(context, build_iuse_id=None, build_iuseid=None):
    query = context.session.query(models.EbuildsIUses)

    if build_iuse_id is not None:
        query.filter(models.BuildsIUses.id == build_iuse_id).delete()
    else:
        query.filter(models.BuildsIUses.id == build_iuseid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class BuildIUse(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'build_uuid': fields.UUIDField(),
        'use_id': fields.IntegerField(),
        'status' : fields.BooleanField(),
        }

    def __init__(self, *args, **kwargs):
        super(BuildIUse, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_build_iuses = []

    def obj_make_compatible(self, primitive, target_version):
        super(BuildIUse, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, build_iuse, db_build_iuse, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        build_iuse._context = context
        for name, field in build_iuse.fields.items():
            value = db_build_iuse[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            build_iuse[name] = value
        
        build_iuse.obj_reset_changes()
        return build_iuse

    @staticmethod
    @db_api.main_context_manager.reader
    def _build_iuse_get_query_from_db(context):
        query = context.session.query(models.BuildsIUses)
        return query

    @staticmethod
    @require_context
    def _build_iuse_get_from_db(context, id):
        """Returns a dict describing specific build_iuses."""
        result = BuildIUse._build_iuse_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(build_iuse_id=id)
        return result

    @staticmethod
    @require_context
    def _build_iuse_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = BuildIUse._build_iuse_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(build_iuses_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(BuildIUse, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(BuildIUse, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_build_iuse = cls._build_iuse_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_build_iuse,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_build_iuse = cls._build_iuse_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_build_iuse,
                                   expected_attrs=[])

    @staticmethod
    def _build_iuse_create(context, updates):
        return _build_iuse_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_build_iuse = self._build_iuse_create(context, updates)
        self._from_db_object(context, self, db_build_iuse)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a build_iuses.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_build_iuse = context.session.query(models.BuildsIUses).\
            filter_by(id=self.id).first()
        if not db_build_iuse:
            raise exception.ImagesNotFound(build_iuse_id=self.id)
        db_build_iuse.update(values)
        db_build_iuse.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_build_iuse)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _build_iuse_destroy(context, build_iuse_id=None, build_iuseid=None):
        _build_iuse_destroy(context, build_iuse_id=build_iuse_id, build_iuseid=build_iuseid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a build_iuses
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a build_iuses object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._build_iuse_destroy(context, build_iuse_id=self.id)
        else:
            self._build_iuse_destroy(context, build_iuseid=self.build_iuseid)
        #self._from_db_object(context, self, db_build_iuse)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}

        db_build_iuse = BuildIUses._build_iuse_get_query_from_db(context)

        if 'status' in filters:
            db_build_iuse = db_build_iuse.filter(
                models.BuildsIUses.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_build_iuse,
                                   expected_attrs=[])


@db_api.main_context_manager
def _build_iuse_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all build_iusess.
    """
    filters = filters or {}

    query = BuildIUse._build_iuse_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.BuildsIUses.status == filters['status'])
    if 'build_uuid' in filters:
            query = query.filter(
                models.BuildsIUses.build_uuid == filters['build_uuid'])

    marker_row = None
    if marker is not None:
        marker_row = BuildIUse._build_iuse_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.BuildsIUses,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class BuildIUseList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('BuildIUse'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_build_iuses = _build_iuse_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.build_iuse.BuildIUse,
                                  db_build_iuses,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.BuildsIUses).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_build_iuse = context.session.query(models.BuildsIUses).filter_by(auto=True)
        db_build_iuse.update(values)
