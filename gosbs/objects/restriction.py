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

def _dict_with_extra_specs(restriction_model):
    extra_specs = {}
    return dict(restriction_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _restriction_create(context, values):
    db_restriction = models.Restrictions()
    db_restriction.update(values)

    try:
        db_restriction.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'restrictionid' in e.columns:
            raise exception.ImagesIdExists(restriction_id=values['restrictionid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_restriction)


@db_api.main_context_manager.writer
def _restriction_destroy(context, restriction_id=None, restrictionid=None):
    query = context.session.query(models.Restrictions)

    if restriction_id is not None:
        query.filter(models.Restrictions.id == restriction_id).delete()
    else:
        query.filter(models.Restrictions.id == restrictionid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Restriction(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'restriction': fields.StringField(),
        }

    def __init__(self, *args, **kwargs):
        super(Restriction, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_restrictions = []

    def obj_make_compatible(self, primitive, target_version):
        super(Restriction, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, restriction, db_restriction, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        restriction._context = context
        for name, field in restriction.fields.items():
            value = db_restriction[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            restriction[name] = value
        
        restriction.obj_reset_changes()
        return restriction

    @staticmethod
    @db_api.main_context_manager.reader
    def _restriction_get_query_from_db(context):
        query = context.session.query(models.Restrictions)
        return query

    @staticmethod
    @require_context
    def _restriction_get_from_db(context, id):
        """Returns a dict describing specific restrictions."""
        result = Restriction._restriction_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(restriction_id=id)
        return result

    @staticmethod
    @require_context
    def _restriction_get_by_restriction_from_db(context, restriction):
        """Returns a dict describing specific flavor."""
        result = Restriction._restriction_get_query_from_db(context).\
                            filter_by(restriction=restriction).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(restrictions_restriction=restriction)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Restriction, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Restriction, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_restriction = cls._restriction_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_restriction,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, restriction):
        db_restriction = Restriction._restriction_get_query_from_db(context)
        db_restriction = db_restriction.filter_by(restriction=restriction)
        db_restriction = db_restriction.first()
        if not db_restriction:
            return None
        return cls._from_db_object(context, cls(context), db_restriction,
                                   expected_attrs=[])

    @staticmethod
    def _restriction_create(context, updates):
        return _restriction_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_restriction = self._restriction_create(context, updates)
        self._from_db_object(context, self, db_restriction)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a restrictions.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_restriction = context.session.query(models.Restrictions).\
            filter_by(id=self.id).first()
        if not db_restriction:
            raise exception.ImagesNotFound(restriction_id=self.id)
        db_restriction.update(values)
        db_restriction.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_restriction)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _restriction_destroy(context, restriction_id=None, restrictionid=None):
        _restriction_destroy(context, restriction_id=restriction_id, restrictionid=restrictionid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a restrictions
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a restrictions object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._restriction_destroy(context, restriction_id=self.id)
        else:
            self._restriction_destroy(context, restrictionid=self.restrictionid)
        #self._from_db_object(context, self, db_restriction)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        print('foo')
        db_restriction = Restriction._restriction_get_query_from_db(context)
    
        if 'status' in filters:
            db_restriction = db_restriction.filter(
                models.Restrictions.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_restriction,
                                   expected_attrs=[])


@db_api.main_context_manager
def _restriction_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all restrictionss.
    """
    filters = filters or {}

    query = Restriction._restriction_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Restrictions.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = Restriction._restriction_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Restrictions,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class RestrictionList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Restriction'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_restrictions = _restriction_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.restriction.Restriction,
                                  db_restrictions,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Restrictions).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_restriction = context.session.query(models.Restrictions).filter_by(auto=True)
        db_restriction.update(values)
