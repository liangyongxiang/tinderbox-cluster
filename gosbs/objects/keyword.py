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

def _dict_with_extra_specs(keyword_model):
    extra_specs = {}
    return dict(keyword_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _keyword_create(context, values):
    db_keyword = models.Keywords()
    db_keyword.update(values)

    try:
        db_keyword.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'keywordid' in e.columns:
            raise exception.ImagesIdExists(keyword_id=values['keywordid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_keyword)


@db_api.main_context_manager.writer
def _keyword_destroy(context, keyword_id=None, keywordid=None):
    query = context.session.query(models.Keywords)

    if keyword_id is not None:
        query.filter(models.Keywords.uuid == keyword_id).delete()
    else:
        query.filter(models.Keywords.uuid == keywordid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Keyword(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject2):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'keyword': fields.StringField(),
        }

    def __init__(self, *args, **kwargs):
        super(Keyword, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_keywords = []

    def obj_make_compatible(self, primitive, target_version):
        super(Keyword, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, keyword, db_keyword, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        keyword._context = context
        for name, field in keyword.fields.items():
            value = db_keyword[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            keyword[name] = value
        
        keyword.obj_reset_changes()
        return keyword

    @staticmethod
    @db_api.main_context_manager.reader
    def _keyword_get_query_from_db(context):
        query = context.session.query(models.Keywords)
        return query

    @staticmethod
    @require_context
    def _keyword_get_from_db(context, id):
        """Returns a dict describing specific keywords."""
        result = Keyword._keyword_get_query_from_db(context).\
                        filter_by(uuid=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(keyword_id=id)
        return result

    @staticmethod
    @require_context
    def _keyword_get_by_keyword_from_db(context, keyword):
        """Returns a dict describing specific flavor."""
        result = Keyword._keyword_get_query_from_db(context).\
                            filter_by(keyword=keyword).\
                            first()
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Keyword, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Keyword, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_keyword = cls._keyword_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_keyword,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, keyword):
        db_keyword = cls._keyword_get_by_keyword_from_db(context, keyword)
        if not db_keyword:
            return None
        return cls._from_db_object(context, cls(context), db_keyword,
                                   expected_attrs=[])

    @staticmethod
    def _keyword_create(context, updates):
        return _keyword_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_keyword = self._keyword_create(context, updates)
        self._from_db_object(context, self, db_keyword)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a keywords.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_keyword = context.session.query(models.Keywords).\
            filter_by(uuid=self.id).first()
        if not db_keyword:
            raise exception.ImagesNotFound(keyword_id=self.id)
        db_keyword.update(values)
        db_keyword.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_keyword)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _keyword_destroy(context, keyword_id=None, keywordid=None):
        _keyword_destroy(context, keyword_id=keyword_id, keywordid=keywordid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a keywords
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a keywords object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._keyword_destroy(context, keyword_id=self.id)
        else:
            self._keyword_destroy(context, keywordid=self.keywordid)
        #self._from_db_object(context, self, db_keyword)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        print('foo')
        db_keyword = Keyword._keyword_get_query_from_db(context)
    
        if 'status' in filters:
            db_keyword = db_keyword.filter(
                models.Keywords.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_keyword,
                                   expected_attrs=[])


@db_api.main_context_manager
def _keyword_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all keywordss.
    """
    filters = filters or {}

    query = Keyword._keyword_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Keywords.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = Keyword._keyword_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Keywords,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class KeywordList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Keyword'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_keywords = _keyword_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.keyword.Keyword,
                                  db_keywords,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Keywords).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_keyword = context.session.query(models.Keywords).filter_by(auto=True)
        db_keyword.update(values)
