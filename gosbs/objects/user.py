#    Copyright 2013 Red Hat, Inc
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not user this file except in compliance with the License. You may obtain
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

def _dict_with_extra_specs(userr_model):
    extra_specs = {}
    return dict(userr_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _userr_create(context, values):
    db_userr = models.Users()
    db_userr.update(values)

    try:
        db_userr.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'userrid' in e.columns:
            raise exception.ImagesIdExists(userr_id=values['userrid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return db_userr


@db_api.main_context_manager.writer
def _userr_destroy(context, userr_id=None, userrid=None):
    query = context.session.query(models.Users)

    if user_id is not None:
        query.filter(models.Users.uuid == user_id).delete()
    else:
        query.filter(models.Users.uuid == userid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class User(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'user_id': fields.IntegerField(),
        'name': fields.StringField(),
        }

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_users = []

    def obj_make_compatible(self, primitive, target_version):
        super(User, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, user, db_user, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        user._context = context
        for name, field in user.fields.items():
            value = db_user[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            user[name] = value
        
        user.obj_reset_changes()
        return user

    @staticmethod
    @db_api.main_context_manager.reader
    def _user_get_query_from_db(context):
        query = context.session.query(models.Users)
        return query

    @staticmethod
    @require_context
    def _user_get_from_db(context, id):
        """Returns a dict describing specific users."""
        result = User._user_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(user_id=id)
        return result

    @staticmethod
    @require_context
    def _user_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = User._user_get_query_from_db(context).\
                            filter_by(name=name).\
                            first()
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(User, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(User, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_user = cls._user_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_user,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_user = cls._user_get_by_name_from_db(context, name)
        if not db_user:
            return None
        return cls._from_db_object(context, cls(context), db_user,
                                   expected_attrs=[])

    @staticmethod
    def _user_create(context, updates):
        return _user_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_user = self._user_create(context, updates)
        self._from_db_object(context, self, db_user)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a users.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_user = context.session.query(models.Users).\
            filter_by(id=self.id).first()
        if not db_user:
            raise exception.ImagesNotFound(user_id=self.id)
        db_user.update(values)
        db_user.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_user)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _user_destroy(context, user_id=None, userid=None):
        _user_destroy(context, user_id=user_id, userid=userid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a users
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a users object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._user_destroy(context, user_id=self.id)
        else:
            self._user_destroy(context, userid=self.userid)
        #self._from_db_object(context, self, db_user)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        print('foo')
        db_user = User._user_get_query_from_db(context)
    
        if 'status' in filters:
            db_user = db_user.filter(
                models.Users.status == filters['status']).first()
        return cls._from_db_object(context, cls(context), db_user,
                                   expected_attrs=[])


@db_api.main_context_manager
def _user_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all userss.
    """
    filters = filters or {}

    query = User._user_get_query_from_db(context)

    if 'status' in filters:
            query = query.filter(
                models.Users.status == filters['status'])

    marker_row = None
    if marker is not None:
        marker_row = User._user_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Users,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class UseList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('User'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_users = _user_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.user.Use,
                                  db_users,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Users).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_user = context.session.query(models.Users).filter_by(auto=True)
        db_user.update(values)
