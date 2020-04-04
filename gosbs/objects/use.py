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

def _dict_with_extra_specs(use_model):
    extra_specs = {}
    return dict(use_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _use_create(context, values):
    db_use = models.Uses()
    db_use.update(values)

    try:
        db_use.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'useid' in e.columns:
            raise exception.ImagesIdExists(use_id=values['useid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return db_use


@db_api.main_context_manager.writer
def _use_destroy(context, use_id=None, useid=None):
    query = context.session.query(models.Uses)

    if use_id is not None:
        query.filter(models.Uses.uuid == use_id).delete()
    else:
        query.filter(models.Uses.uuid == useid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Use(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'flag': fields.StringField(),
        'description' : fields.StringField(nullable=True),
        }

    def __init__(self, *args, **kwargs):
        super(Use, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_uses = []

    def obj_make_compatible(self, primitive, target_version):
        super(Use, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, use, db_use, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        use._context = context
        for name, field in use.fields.items():
            value = db_use[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            use[name] = value
        
        use.obj_reset_changes()
        return use

    @staticmethod
    @db_api.main_context_manager.reader
    def _use_get_query_from_db(context):
        query = context.session.query(models.Uses)
        return query

    @staticmethod
    @require_context
    def _use_get_from_db(context, id):
        """Returns a dict describing specific uses."""
        result = Use._use_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(use_id=id)
        return result

    @staticmethod
    @require_context
    def _use_get_by_flag_from_db(context, flag):
        """Returns a dict describing specific flavor."""
        result = Use._use_get_query_from_db(context).\
                            filter_by(flag=flag).\
                            first()
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Use, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Use, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_use = cls._use_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_use,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, flag):
        db_use = cls._use_get_by_flag_from_db(context, flag)
        if not db_use:
            return None
        return cls._from_db_object(context, cls(context), db_use,
                                   expected_attrs=[])

    @staticmethod
    def _use_create(context, updates):
        return _use_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_use = self._use_create(context, updates)
        self._from_db_object(context, self, db_use)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a uses.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_use = context.session.query(models.Uses).\
            filter_by(uuid=self.id).first()
        if not db_use:
            raise exception.ImagesNotFound(use_id=self.id)
        db_use.update(values)
        db_use.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_use)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _use_destroy(context, use_id=None, useid=None):
        _use_destroy(context, use_id=use_id, useid=useid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a uses
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a uses object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._use_destroy(context, use_id=self.id)
        else:
            self._use_destroy(context, useid=self.useid)
        #self._from_db_object(context, self, db_use)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        print('foo')
        db_use = Use._use_get_query_from_db(context)
    
        if 'status' in filters:
            db_use = db_use.filter(
                models.Uses.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_use,
                                   expected_attrs=[])


@db_api.main_context_manager
def _use_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all usess.
    """
    filters = filters or {}

    query = Use._use_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Uses.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = Use._use_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Uses,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class UseList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Use'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_uses = _use_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.use.Use,
                                  db_uses,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Uses).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_use = context.session.query(models.Uses).filter_by(auto=True)
        db_use.update(values)
