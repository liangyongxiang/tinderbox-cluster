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
def _binary_header_create(context, values):
    db_binary_header = models.BinarysHeaders()
    db_binary_header.update(values)

    try:
        db_binary_header.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'local_binary_headeruuid' in e.columns:
            raise exception.ImagesIdExists(binary_header_uuid=values['binary_header_headeruuid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_binary_header)


@db_api.main_context_manager.writer
def _binary_header_header_destroy(context, binary_header_header_uuid=None, binary_header_headeruuid=None):
    query = context.session.query(models.BinarysHeaders)

    if binary_header_header_uuid is not None:
        query.filter(models.BinarysHeaders.uuid == binary_header_header_uuid).delete()
    else:
        query.filter(models.BinarysHeaders.uuid == binary_header_headeruuid).delete()


@base.NovaObjectRegistry.register
class BinaryHeader(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid' : fields.UUIDField(),
        'project_uuid' : fields.UUIDField(),
        'service_uuid' : fields.UUIDField(),
        'repository' : fields.StringField(nullable=True),
        'arch' : fields.StringField(nullable=True),
        'accept_keywords' : fields.StringField(nullable=True),
        'accept_license' : fields.StringField(nullable=True),
        'accept_properties' : fields.StringField(nullable=True),
        'accept_restrict' : fields.StringField(nullable=True),
        'cbuild' : fields.StringField(nullable=True),
        'config_protect' : fields.StringField(nullable=True),
        'config_protect_mask' : fields.StringField(nullable=True),
        'accept_keywords' : fields.StringField(nullable=True),
        'features' : fields.StringField(nullable=True),
        'gentoo_mirrors' : fields.StringField(nullable=True),
        #'install_mask' : fields.StringField(nullable=True),
        'iuse_implicit' : fields.StringField(nullable=True),
        'use' : fields.StringField(nullable=True),
        'use_expand' : fields.StringField(nullable=True),
        'use_expand_hidden' : fields.StringField(nullable=True),
        'use_expand_implicit' : fields.StringField(nullable=True),
        'use_expand_unprefixed' : fields.StringField(nullable=True),
        'use_expand_values_arch' : fields.StringField(nullable=True),
        'use_expand_values_elibc' : fields.StringField(nullable=True),
        'use_expand_values_kernel' : fields.StringField(nullable=True),
        'use_expand_values_userland' : fields.StringField(nullable=True),
        'elibc' : fields.StringField(nullable=True),
        'kernel' : fields.StringField(nullable=True),
        'userland' : fields.StringField(nullable=True),
        'packages' : fields.IntegerField(),
        'profile' : fields.StringField(nullable=True),
        'version' : fields.StringField(nullable=True),
        'looked' : fields.BooleanField(),
        }

    def __init__(self, *args, **kwargs):
        super(BinaryHeader, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_binary_header_header = []

    def obj_make_compatible(self, primitive, target_version):
        super(BinaryHeader, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, binary_header, db_binary_header, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        binary_header._context = context
        for name, field in binary_header.fields.items():
            value = db_binary_header[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            binary_header[name] = value
        
        binary_header.obj_reset_changes()
        return binary_header

    @staticmethod
    @db_api.main_context_manager.reader
    def _binary_header_get_query_from_db(context):
        query = context.session.query(models.BinarysHeaders)
        return query

    @staticmethod
    @require_context
    def _binary_header_get_from_db(context, uuid):
        """Returns a dict describing specific binary_headerss."""
        result = BinaryHeader._binary_header_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(binary_header_uuid=uuid)
        return result

    @staticmethod
    @require_context
    def _binary_headers_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = BinaryHeader._binary_header_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(binary_headers_name=name)
        return _dict_with_extra_specs(result)

    @staticmethod
    @require_context
    def _binary_header_get_by_service_from_db(context, uuid):
        """Returns a dict describing specific flavor."""
        result = BinaryHeader._binary_header_get_query_from_db(context).\
                            filter_by(service_uuid=uuid).\
                            first()
        if not result:
            return None
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(BinaryHeader, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(BinaryHeader, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_binary_header = cls._binary_header_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_binary_header,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_service_uuid(cls, context, uuid):
        db_binary_header = cls._binary_header_get_by_service_from_db(context, uuid)
        if db_binary_header is None:
            return None
        return cls._from_db_object(context, cls(context), db_binary_header,
                                   expected_attrs=[])

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_binary_header = cls._binary_header_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_binary_header,
                                   expected_attrs=[])

    @base.remotable_classmethod
    def get_by_cpv(cls, context, cpv, filters=None):
        filters = filters or {}
        db_binary_header = cls._binary_header_get_query_from_db(context)
        db_binary_header = db_binary_header.filter_by(cpv=cpv)
        if 'service_uuid' in filters:
            db_binary_header = db_binary_header.filter(
                models.BinarysHeaders.service_uuid == filters['service_uuid'])
        if 'cpv' in filters:
            db_binary_header = db_binary_header.filter(
                models.BinarysHeaders.cpv == filters['cpv'])
        if 'build_id' in filters:
            db_binary_header = db_binary_header.filter(
                models.BinarysHeaders.build_id == filters['build_id'])
        db_binary_header = db_binary_header.first()
        if not db_binary_header:
            return None
        return cls._from_db_object(context, cls(context), db_binary_header,
                                   expected_attrs=[])
    
    @staticmethod
    def _binary_header_create(context, updates):
        return _binary_header_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_binary_header = self._binary_header_create(context, updates)
        self._from_db_object(context, self, db_binary_header)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a binary_headerss.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_binary_header = context.session.query(models.BinarysHeaders).\
            filter_by(uuid=self.uuid).first()
        if not db_binary_header:
            raise exception.ImagesNotFound(binary_header_uuid=self.uuid)
        db_binary_header.update(values)
        db_binary_header.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_binary_header)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _binary_header_destroy(context, binary_header_uuid=None, binary_headeruuid=None):
        _binary_header_destroy(context, binary_header_uuid=binary_header_uuid, binary_headeruuid=binary_headeruuid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a binary_headerss
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a binary_headerss object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'uuid' in self:
            self._binary_header_destroy(context, binary_header_uuid=self.uuid)
        else:
            self._binary_header_destroy(context, binary_headeruuid=self.binary_headeruuid)
        #self._from_db_object(context, self, db_binary_header)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        query = BinaryHeader._binary_header_get_query_from_db(context)
        if not query:
            return None
        print(query)
        #return None
        if 'service_uuid' in filters:
            query = query.filter(
                models.BinarysHeaders.service_uuid == filters['service_uuid'])
        if 'cpv' in filters:
            query = query.filter(
                models.BinarysHeaders.cpv == filters['cpv'])
        if 'build_id' in filters:
            query = query.filter(
                models.BinarysHeaders.build_id == filters['build_id'])
        if not query:
            return None

        return cls._from_db_object(context, cls(context), query,
                                   expected_attrs=[])

@db_api.main_context_manager
def _binary_header_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all binary_headers.
    """
    filters = filters or {}

    query = BinaryHeader._binary_header_get_query_from_db(context)

    if 'ebuild_uuid' in filters:
            query = query.filter(
                models.BinarysHeaders.ebuild_uuid == filters['ebuild_uuid'])
    if 'project_uuid' in filters:
            query = query.filter(
                models.BinarysHeaders.project_uuid == filters['project_uuid'])
    if 'service_uuid' in filters:
            query = query.filter(
                models.BinarysHeaders.service_uuid == filters['service_uuid'])
    if 'cpv' in filters:
            query = query.filter(
                models.BinarysHeaders.cpv == filters['cpv'])
    if 'build_id' in filters:
        query = query.filter(
                models.BinarysHeaders.build_id == filters['build_id'])
    marker_row = None
    if marker is not None:
        marker_row = BinaryHeader._binary_header_get_query_from_db(context).\
                    filter_by(uuid=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.BinarysHeaders,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class BinaryHeaderList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('BinaryHeader'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_binary_headers = _binary_header_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.binary_header.BinaryHeader,
                                  db_binary_headers,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.BinarysHeaders).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_binary_header = context.session.query(models.BinarysHeaders).filter_by(auto=True)
        db_binary_header.update(values)
