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
CATEGORY_STATUS = ['failed', 'completed', 'in-progress', 'waiting']

def _dict_with_extra_specs(category_model):
    extra_specs = {}
    return dict(category_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _category_create(context, values):
    db_category = models.Categories()
    db_category.update(values)

    try:
        db_category.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'categoryid' in e.columns:
            raise exception.ImagesIdExists(category_id=values['categoryid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_category)


@db_api.main_context_manager.writer
def _category_destroy(context, category_id=None, categoryid=None):
    query = context.session.query(models.Categories)

    if category_id is not None:
        query.filter(models.Categories.uuid == category_id).delete()
    else:
        query.filter(models.Categories.uuid == categoryid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Category(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid': fields.UUIDField(),
        'name': fields.StringField(),
        'status' : fields.EnumField(valid_values=CATEGORY_STATUS),
        }

    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_categorys = []

    def obj_make_compatible(self, primitive, target_version):
        super(Project, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, category, db_category, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        category._context = context
        for name, field in category.fields.items():
            value = db_category[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            category[name] = value
        
        category.obj_reset_changes()
        return category

    @staticmethod
    @db_api.main_context_manager.reader
    def _category_get_query_from_db(context):
        query = context.session.query(models.Categories)
        return query

    @staticmethod
    @require_context
    def _category_get_from_db(context, uuid):
        """Returns a dict describing specific categorys."""
        result = Category._category_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(category_uuid=uuid)
        return result

    @staticmethod
    @require_context
    def _category_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Category._category_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Category, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Category, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_category = cls._category_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_category,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_category = cls._category_get_by_name_from_db(context, name)
        if not db_category:
            return None
        return cls._from_db_object(context, cls(context), db_category,
                                   expected_attrs=[])

    @staticmethod
    def _category_create(context, updates):
        return _category_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_category = self._category_create(context, updates)
        self._from_db_object(context, self, db_category)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a categorys.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_category = context.session.query(models.Categories).\
            filter_by(uuid=self.uuid).first()
        if not db_category:
            raise exception.ImagesNotFound(category_id=self.uuid)
        db_category.update(values)
        db_category.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_category)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _category_destroy(context, category_id=None, categoryid=None):
        _category_destroy(context, category_id=category_id, categoryid=categoryid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a categorys
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a categorys object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._category_destroy(context, category_id=self.uuid)
        else:
            self._category_destroy(context, categoryid=self.categoryid)
        #self._from_db_object(context, self, db_category)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_category = Category._category_get_query_from_db(context)
    
        if 'status' in filters:
            db_category = db_category.filter(
                models.Categories.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_category,
                                   expected_attrs=[])


@db_api.main_context_manager
def _category_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all categoryss.
    """
    filters = filters or {}

    query = Category._category_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Categories.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = Category._category_get_query_from_db(context).\
                    filter_by(uuid=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Categories,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class CategoryList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Category'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_categorys = _category_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.category.Category,
                                  db_categorys,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Categories).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_category = context.session.query(models.Categories).filter_by(auto=True)
        db_category.update(values)
