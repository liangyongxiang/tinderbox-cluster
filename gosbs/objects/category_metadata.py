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

def _dict_with_extra_specs(category_metadata_model):
    extra_specs = {}
    return dict(category_metadata_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _category_metadata_create(context, values):
    db_category_metadata = models.CategoriesMetadata()
    db_category_metadata.update(values)

    try:
        db_category_metadata.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'category_metadataid' in e.columns:
            raise exception.ImagesIdExists(category_metadata_id=values['category_metadataid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_category_metadata)


@db_api.main_context_manager.writer
def _category_metadata_destroy(context, category_metadata_id=None, category_metadataid=None):
    query = context.session.query(models.CategoriesMetadata)

    if category_metadata_id is not None:
        query.filter(models.CategoriesMetadata.id == category_metadata_id).delete()
    else:
        query.filter(models.CategoriesMetadata.id == category_metadataid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class CategoryMetadata(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'category_uuid': fields.UUIDField(),
        'description' : fields.StringField(),
        'checksum': fields.StringField(),
        }

    def __init__(self, *args, **kwargs):
        super(CategoryMetadata, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_category_metadatas = []

    def obj_make_compatible(self, primitive, target_version):
        super(CategoryMetadata, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, category_metadata, db_category_metadata, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        category_metadata._context = context
        for name, field in category_metadata.fields.items():
            value = db_category_metadata[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            category_metadata[name] = value
        
        category_metadata.obj_reset_changes()
        return category_metadata

    @staticmethod
    @db_api.main_context_manager.reader
    def _category_metadata_get_query_from_db(context):
        query = context.session.query(models.CategoriesMetadata)
        return query

    @staticmethod
    @require_context
    def _category_metadata_get_from_db(context, uuid):
        """Returns a dict describing specific category_metadatas."""
        result = CategoryMetadata._category_metadata_get_query_from_db(context).\
                        filter_by(category_uuid=uuid).\
                        first()
        return result

    @staticmethod
    @require_context
    def _category_metadata_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = CategoryMetadata._category_metadata_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(category_metadatas_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(CategoryMetadata, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(CategoryMetadata, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_category_metadata = cls._category_metadata_get_from_db(context, uuid)
        if not db_category_metadata:
            return None
        return cls._from_db_object(context, cls(context), db_category_metadata,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_category_metadata = cls._category_metadata_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_category_metadata,
                                   expected_attrs=[])

    @staticmethod
    def _category_metadata_create(context, updates):
        return _category_metadata_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_category_metadata = self._category_metadata_create(context, updates)
        self._from_db_object(context, self, db_category_metadata)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a category_metadatas.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_category_metadata = context.session.query(models.CategoriesMetadata).\
            filter_by(id=self.id).first()
        if not db_category_metadata:
            raise exception.ImagesNotFound(category_metadata_id=self.id)
        db_category_metadata.update(values)
        db_category_metadata.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_category_metadata)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _category_metadata_destroy(context, category_metadata_id=None, category_metadataid=None):
        _category_metadata_destroy(context, category_metadata_id=category_metadata_id, category_metadataid=category_metadataid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a category_metadatas
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a category_metadatas object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._category_metadata_destroy(context, category_metadata_id=self.id)
        else:
            self._category_metadata_destroy(context, category_metadataid=self.category_metadataid)
        #self._from_db_object(context, self, db_category_metadata)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_category_metadata = CategoryMetadata._category_metadata_get_query_from_db(context)
    
        if 'status' in filters:
            db_category_metadata = db_category_metadata.filter(
                models.CategoriesMetadata.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_category_metadata,
                                   expected_attrs=[])


@db_api.main_context_manager
def _category_metadata_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all category_metadatass.
    """
    filters = filters or {}

    query = CategoryMetadata._category_metadata_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.CategoriesMetadata.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = CategoryMetadata._category_metadata_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.CategoriesMetadata,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class CategoryMetadataList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('CategoryMetadata'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_category_metadatas = _category_metadata_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.category_metadata.CategoryMetadata,
                                  db_category_metadatas,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.CategoriesMetadata).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_category_metadata = context.session.query(models.CategoriesMetadata).filter_by(auto=True)
        db_category_metadata.update(values)
