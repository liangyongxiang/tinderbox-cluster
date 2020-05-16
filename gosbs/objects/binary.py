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
from oslo_versionedobjects import fields
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

CONF = gosbs.conf.CONF

def _dict_with_extra_specs(model):
    extra_specs = {}
    return dict(model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _binary_create(context, values):
    db_binary = models.Binarys()
    db_binary.update(values)

    try:
        db_binary.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'local_binaryuuid' in e.columns:
            raise exception.ImagesIdExists(binary_uuid=values['binaryuuid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_binary)


@db_api.main_context_manager.writer
def _binary_destroy(context, binary_uuid=None, binaryuuid=None):
    query = context.session.query(models.Binarys)

    if binary_uuid is not None:
        query.filter(models.Binarys.uuid == binary_uuid).delete()
    else:
        query.filter(models.Binarys.uuid == binaryuuid).delete()


@base.NovaObjectRegistry.register
class Binary(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid' : fields.UUIDField(),
        'project_uuid' : fields.UUIDField(),
        'service_uuid' : fields.UUIDField(),
        'ebuild_uuid' : fields.UUIDField(),
        'repository' : fields.StringField(nullable=True),
        'cpv' : fields.StringField(nullable=True),
        'restrictions' : fields.StringField(nullable=True),
        'depend' : fields.StringField(nullable=True),
        'bdepend' : fields.StringField(nullable=True),
        'rdepend' : fields.StringField(nullable=True),
        'pdepend' : fields.StringField(nullable=True),
        'mtime' : fields.IntegerField(),
        'license' : fields.StringField(nullable=True),
        'chost' : fields.StringField(nullable=True),
        'sha1' : fields.StringField(nullable=True),
        'defined_phases' : fields.StringField(nullable=True),
        'size' : fields.IntegerField(),
        'eapi' : fields.StringField(nullable=True),
        'path' : fields.StringField(nullable=True),
        'build_id' : fields.IntegerField(),
        'slot' : fields.StringField(nullable=True),
        'md5' : fields.StringField(nullable=True),
        'build_time' : fields.IntegerField(),
        'iuses' : fields.StringField(nullable=True),
        'uses' : fields.StringField(nullable=True),
        'provides' : fields.StringField(nullable=True),
        'keywords' : fields.StringField(nullable=True),
        'requires' : fields.StringField(nullable=True),
        'looked' : fields.BooleanField(),
        }

    def __init__(self, *args, **kwargs):
        super(Binary, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_binary = []

    def obj_make_compatible(self, primitive, target_version):
        super(Binary, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, binary, db_binary, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        binary._context = context
        for name, field in binary.fields.items():
            value = db_binary[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            binary[name] = value
        
        binary.obj_reset_changes()
        return binary

    @staticmethod
    @db_api.main_context_manager.reader
    def _binary_get_query_from_db(context):
        query = context.session.query(models.Binarys)
        return query

    @staticmethod
    @require_context
    def _binary_get_from_db(context, uuid):
        """Returns a dict describing specific binaryss."""
        result = Binary._binary_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(binary_uuid=uuid)
        return result

    @staticmethod
    @require_context
    def _binarys_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Binary._binary_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(binarys_name=name)
        return _dict_with_extra_specs(result)

    @staticmethod
    @require_context
    def _binary_get_by_uuid_from_db(context, uuid):
        """Returns a dict describing specific flavor."""
        result = Binary._binary_get_query_from_db(context).\
                            filter_by(uuid=uuid).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(binarys_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Binary, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Binary, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_binary = cls._binary_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_binary,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_binary = cls._binary_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_binary,
                                   expected_attrs=[])

    @base.remotable_classmethod
    def get_by_cpv(cls, context, cpv, filters=None):
        filters = filters or {}
        db_binary = cls._binary_get_query_from_db(context)
        db_binary = db_binary.filter_by(cpv=cpv)
        if 'service_uuid' in filters:
            db_binary = db_binary.filter(
                models.Binarys.service_uuid == filters['service_uuid'])
        if 'cpv' in filters:
            db_binary = db_binary.filter(
                models.Binarys.cpv == filters['cpv'])
        if 'build_id' in filters:
            db_binary = db_binary.filter(
                models.Binarys.build_id == filters['build_id'])
        db_binary = db_binary.first()
        if not db_binary:
            return None
        return cls._from_db_object(context, cls(context), db_binary,
                                   expected_attrs=[])
    
    @staticmethod
    def _binary_create(context, updates):
        return _binary_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_binary = self._binary_create(context, updates)
        self._from_db_object(context, self, db_binary)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a binaryss.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_binary = context.session.query(models.Binarys).\
            filter_by(uuid=self.uuid).first()
        if not db_binary:
            raise exception.ImagesNotFound(binary_uuid=self.uuid)
        db_binary.update(values)
        db_binary.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_binary)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _binary_destroy(context, binary_uuid=None, binaryuuid=None):
        _binary_destroy(context, binary_uuid=binary_uuid, binaryuuid=binaryuuid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a binaryss
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a binaryss object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'uuid' in self:
            self._binary_destroy(context, binary_uuid=self.uuid)
        else:
            self._binary_destroy(context, binaryuuid=self.binaryuuid)
        #self._from_db_object(context, self, db_binary)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        query = Binary._binary_get_query_from_db(context)
        if not query:
            return None
        print(query)
        #return None
        if 'service_uuid' in filters:
            query = query.filter(
                models.Binarys.service_uuid == filters['service_uuid'])
        if 'cpv' in filters:
            query = query.filter(
                models.Binarys.cpv == filters['cpv'])
        if 'build_id' in filters:
            query = query.filter(
                models.Binarys.build_id == filters['build_id'])
        if not query:
            return None

        return cls._from_db_object(context, cls(context), query,
                                   expected_attrs=[])

@db_api.main_context_manager
def _binary_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all binarys.
    """
    filters = filters or {}

    query = Binary._binary_get_query_from_db(context)

    if 'ebuild_uuid' in filters:
            query = query.filter(
                models.Binarys.ebuild_uuid == filters['ebuild_uuid'])
    if 'project_uuid' in filters:
            query = query.filter(
                models.Binarys.project_uuid == filters['project_uuid'])
    if 'service_uuid' in filters:
            query = query.filter(
                models.Binarys.service_uuid == filters['service_uuid'])
    if 'cpv' in filters:
            query = query.filter(
                models.Binarys.cpv == filters['cpv'])
    if 'build_id' in filters:
        query = query.filter(
                models.Binarys.build_id == filters['build_id'])
    marker_row = None
    if marker is not None:
        marker_row = Binary._binary_get_query_from_db(context).\
                    filter_by(uuid=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Binarys,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class BinaryList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Binary'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_binarys = _binary_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.binary.Binary,
                                  db_binarys,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Binarys).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_binary = context.session.query(models.Binarys).filter_by(auto=True)
        db_binary.update(values)
