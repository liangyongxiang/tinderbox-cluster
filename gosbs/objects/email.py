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

def _dict_with_extra_specs(email_model):
    extra_specs = {}
    return dict(email_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _email_create(context, values):
    db_email = models.Emails()
    db_email.update(values)

    try:
        db_email.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'emailid' in e.columns:
            raise exception.ImagesIdExists(email_id=values['emailid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_email)


@db_api.main_context_manager.writer
def _email_destroy(context, email_id=None, emailid=None):
    query = context.session.query(models.Emails)

    if email_id is not None:
        query.filter(models.Emails.id == email_id).delete()
    else:
        query.filter(models.Emails.id == emailid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Email(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'email': fields.StringField(),
        }

    def __init__(self, *args, **kwargs):
        super(Email, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_emails = []

    def obj_make_compatible(self, primitive, target_version):
        super(Email, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, email, db_email, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        email._context = context
        for name, field in email.fields.items():
            value = db_email[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            email[name] = value
        
        email.obj_reset_changes()
        return email

    @staticmethod
    @db_api.main_context_manager.reader
    def _email_get_query_from_db(context):
        query = context.session.query(models.Emails)
        return query

    @staticmethod
    @require_context
    def _email_get_from_db(context, id):
        """Returns a dict describing specific emails."""
        result = Email._email_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(email_id=id)
        return result

    @staticmethod
    @require_context
    def _email_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Email._email_get_query_from_db(context).\
                            filter_by(email=name).\
                            first()
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Email, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Email, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_email = cls._email_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_email,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        db_email = cls._email_get_by_name_from_db(context, name)
        if not db_email:
            return None
        return cls._from_db_object(context, cls(context), db_email,
                                   expected_attrs=[])

    @staticmethod
    def _email_create(context, updates):
        return _email_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_email = self._email_create(context, updates)
        self._from_db_object(context, self, db_email)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a emails.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_email = context.session.query(models.Emails).\
            filter_by(uuid=self.id).first()
        if not db_email:
            raise exception.ImagesNotFound(email_id=self.id)
        db_email.update(values)
        db_email.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_email)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _email_destroy(context, email_id=None, emailid=None):
        _email_destroy(context, email_id=email_id, emailid=emailid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a emails
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a emails object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._email_destroy(context, email_id=self.id)
        else:
            self._email_destroy(context, emailid=self.emailid)
        #self._from_db_object(context, self, db_email)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_email = Email._email_get_query_from_db(context)

        return cls._from_db_object(context, cls(context), db_email,
                                   expected_attrs=[])


@db_api.main_context_manager
def _email_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all emailss.
    """
    filters = filters or {}

    query = Email._email_get_query_from_db(context)

    marker_row = None
    if marker is not None:
        marker_row = Email._email_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Emails,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class EmailList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Email'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_emails = _email_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.email.Email,
                                  db_emails,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Emails).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_email = context.session.query(models.Emails).filter_by(auto=True)
        db_email.update(values)
