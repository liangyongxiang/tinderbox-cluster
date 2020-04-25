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
KEYWORD_STATUS = ['stable','unstable','negative']

def _dict_with_extra_specs(ebuild_keyword_model):
    extra_specs = {}
    return dict(ebuild_keyword_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _ebuild_keyword_create(context, values):
    db_ebuild_keyword = models.EbuildsKeywords()
    db_ebuild_keyword.update(values)

    try:
        db_ebuild_keyword.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'ebuild_keywordid' in e.columns:
            raise exception.ImagesIdExists(ebuild_keyword_id=values['ebuild_keywordid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_ebuild_keyword)


@db_api.main_context_manager.writer
def _ebuild_keyword_destroy(context, ebuild_keyword_id=None, ebuild_keywordid=None):
    query = context.session.query(models.EbuildsKeywords)

    if ebuild_keyword_id is not None:
        query.filter(models.EbuildsKeywords.id == ebuild_keyword_id).delete()
    else:
        query.filter(models.EbuildsKeywords.id == ebuild_keywordid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class EbuildKeyword(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'ebuild_uuid': fields.UUIDField(),
        'keyword_id': fields.IntegerField(),
        'status' : fields.EnumField(valid_values=KEYWORD_STATUS),
        }

    def __init__(self, *args, **kwargs):
        super(EbuildKeyword, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_ebuild_keywords = []

    def obj_make_compatible(self, primitive, target_version):
        super(EbuildKeyword, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, ebuild_keyword, db_ebuild_keyword, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        ebuild_keyword._context = context
        for name, field in ebuild_keyword.fields.items():
            value = db_ebuild_keyword[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            ebuild_keyword[name] = value
        
        ebuild_keyword.obj_reset_changes()
        return ebuild_keyword

    @staticmethod
    @db_api.main_context_manager.reader
    def _ebuild_keyword_get_query_from_db(context):
        query = context.session.query(models.EbuildsKeywords)
        return query

    @staticmethod
    @require_context
    def _ebuild_keyword_get_from_db(context, id):
        """Returns a dict describing specific ebuild_keywords."""
        result = EbuildKeyword._ebuild_keyword_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(ebuild_keyword_id=id)
        return result

    @staticmethod
    @require_context
    def _ebuild_keyword_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = EbuildKeyword._ebuild_keyword_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(ebuild_keywords_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(EbuildKeyword, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(EbuildKeyword, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_ebuild_keyword = cls._ebuild_keyword_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_ebuild_keyword,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_ebuild_keyword = cls._ebuild_keyword_get_by_name_from_db(context, name)
        return cls._from_db_object(context, cls(context), db_ebuild_keyword,
                                   expected_attrs=[])

    @staticmethod
    def _ebuild_keyword_create(context, updates):
        return _ebuild_keyword_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_ebuild_keyword = self._ebuild_keyword_create(context, updates)
        self._from_db_object(context, self, db_ebuild_keyword)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a ebuild_keywords.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_ebuild_keyword = context.session.query(models.EbuildsKeywords).\
            filter_by(id=self.id).first()
        if not db_ebuild_keyword:
            raise exception.ImagesNotFound(ebuild_keyword_id=self.id)
        db_ebuild_keyword.update(values)
        db_ebuild_keyword.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_ebuild_keyword)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _ebuild_keyword_destroy(context, ebuild_keyword_id=None, ebuild_keywordid=None):
        _ebuild_keyword_destroy(context, ebuild_keyword_id=ebuild_keyword_id, ebuild_keywordid=ebuild_keywordid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a ebuild_keywords
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a ebuild_keywords object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._ebuild_keyword_destroy(context, ebuild_keyword_id=self.id)
        else:
            self._ebuild_keyword_destroy(context, ebuild_keywordid=self.ebuild_keywordid)
        #self._from_db_object(context, self, db_ebuild_keyword)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        print('foo')
        db_ebuild_keyword = EbuildKeywords._ebuild_keyword_get_query_from_db(context)
    
        if 'status' in filters:
            db_ebuild_keyword = db_ebuild_keyword.filter(
                models.EbuildsKeywords.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_ebuild_keyword,
                                   expected_attrs=[])


@db_api.main_context_manager
def _ebuild_keyword_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all ebuild_keywordss.
    """
    filters = filters or {}

    query = EbuildKeyword._ebuild_keyword_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.EbuildsKeywords.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = EbuildKeyword._ebuild_keyword_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.EbuildsKeywords,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class EbuildKeywordList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('EbuildKeyword'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_ebuild_keywords = _ebuild_keyword_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.ebuild_keyword.EbuildKeyword,
                                  db_ebuild_keywords,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.EbuildsKeywords).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_ebuild_keyword = context.session.query(models.EbuildsKeywords).filter_by(auto=True)
        db_ebuild_keyword.update(values)
