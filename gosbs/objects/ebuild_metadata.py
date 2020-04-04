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
# We have change the code so it fit what we need.
# I need more cleaning.

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

def _dict_with_extra_specs(ebuild_metadata_model):
    extra_specs = {}
    return dict(ebuild_metadata_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _ebuild_metadata_create(context, values):
    db_ebuild_metadata = models.EbuildsMetadata()
    db_ebuild_metadata.update(values)

    try:
        db_ebuild_metadata.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'ebuild_metadataid' in e.columns:
            raise exception.ImagesIdExists(ebuild_metadata_id=values['ebuild_metadataid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_ebuild_metadata)


@db_api.main_context_manager.writer
def _ebuild_metadata_destroy(context, ebuild_metadata_id=None, ebuild_metadataid=None):
    query = context.session.query(models.EbuildsMetadata)

    if ebuild_metadata_id is not None:
        query.filter(models.EbuildsMetadata.uuid == ebuild_metadata_id).delete()
    else:
        query.filter(models.EbuildsMetadata.uuid == ebuild_metadataid).delete()


@base.NovaObjectRegistry.register
class EbuildMetadata(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'ebuild_uuid': fields.UUIDField(),
        'commit': fields.StringField(nullable=True),
        'commit_msg' : fields.StringField(nullable=True),
        'description' : fields.StringField(nullable=True),
        'slot': fields.StringField(nullable=True),
        'homepage': fields.StringField(nullable=True),
        'license': fields.StringField(nullable=True),
        }

    def __init__(self, *args, **kwargs):
        super(EbuildMetadata, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_ebuild_metadatas = []

    def obj_make_compatible(self, primitive, target_version):
        super(EbuildMetadata, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, ebuild_metadata, db_ebuild_metadata, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        ebuild_metadata._context = context
        for name, field in ebuild_metadata.fields.items():
            value = db_ebuild_metadata[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            ebuild_metadata[name] = value
        
        ebuild_metadata.obj_reset_changes()
        return ebuild_metadata

    @staticmethod
    @db_api.main_context_manager.reader
    def _ebuild_metadata_get_query_from_db(context):
        query = context.session.query(models.EbuildsMetadata)
        return query

    @staticmethod
    @require_context
    def _ebuild_metadata_get_from_db(context, uuid):
        """Returns a dict describing specific ebuild_metadatas."""
        result = EbuildMetadata._ebuild_metadata_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        return result

    @staticmethod
    @require_context
    def _ebuild_metadata_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = EbuildMetadata._ebuild_metadata_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(EbuildMetadata, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(EbuildMetadata, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_ebuild_metadata = cls._ebuild_metadata_get_from_db(context, uuid)
        if not db_ebuild_metadata:
            return None
        return cls._from_db_object(context, cls(context), db_ebuild_metadata,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_ebuild_metadata = cls._ebuild_metadata_get_by_name_from_db(context, name)
        if not db_ebuild_metadata:
            return None
        return cls._from_db_object(context, cls(context), db_ebuild_metadata,
                                   expected_attrs=[])

    @staticmethod
    def _ebuild_metadata_create(context, updates):
        return _ebuild_metadata_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_ebuild_metadata = self._ebuild_metadata_create(context, updates)
        self._from_db_object(context, self, db_ebuild_metadata)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a ebuild_metadatas.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_ebuild_metadata = context.session.query(models.EbuildsMetadata).\
            filter_by(uuid=self.id).first()
        if not db_ebuild_metadata:
            raise exception.ImagesNotFound(ebuild_metadata_id=self.id)
        db_ebuild_metadata.update(values)
        db_ebuild_metadata.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_ebuild_metadata)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _ebuild_metadata_destroy(context, ebuild_metadata_id=None, ebuild_metadataid=None):
        _ebuild_metadata_destroy(context, ebuild_metadata_id=ebuild_metadata_id, ebuild_metadataid=ebuild_metadataid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a ebuild_metadatas
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a ebuild_metadatas object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._ebuild_metadata_destroy(context, ebuild_metadata_id=self.id)
        else:
            self._ebuild_metadata_destroy(context, ebuild_metadataid=self.ebuild_metadataid)
        #self._from_db_object(context, self, db_ebuild_metadata)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        print('foo')
        db_ebuild_metadata = EbuildMetadata._ebuild_metadata_get_query_from_db(context)
    
        if 'status' in filters:
            db_ebuild_metadata = db_ebuild_metadata.filter(
                models.EbuildsMetadata.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_ebuild_metadata,
                                   expected_attrs=[])


@db_api.main_context_manager
def _ebuild_metadata_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all ebuild_metadatass.
    """
    filters = filters or {}

    query = EbuildMetadata._ebuild_metadata_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.EbuildsMetadata.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = EbuildMetadata._ebuild_metadata_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.EbuildsMetadata,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class EbuildMetadataList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('EbuildMetadata'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_ebuild_metadatas = _ebuild_metadata_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.ebuild_metadata.EbuildMetadata,
                                  db_ebuild_metadatas,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.EbuildsMetadata).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_ebuild_metadata = context.session.query(models.EbuildsMetadata).filter_by(auto=True)
        db_ebuild_metadata.update(values)
