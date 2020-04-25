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


OPTIONAL_FIELDS = []
# Remove these fields in version 2.0 of the object.
DEPRECATED_FIELDS = ['deleted', 'deleted_at']

# Non-joined fields which can be updated.
MUTABLE_FIELDS = set(['description'])

CONF = gosbs.conf.CONF


def _dict_with_extra_specs(flavor_model):
    extra_specs = {}
    return dict(flavor_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _flavor_create(context, values):
    db_flavor = models.Flavors()
    db_flavor.update(values)

    try:
        db_flavor.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'flavorid' in e.columns:
            raise exception.FlavorIdExists(flavor_id=values['flavorid'])
        raise exception.FlavorExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_flavor)


@db_api.main_context_manager.writer
def _flavor_destroy(context, flavor_id=None, flavorid=None):
    query = context.session.query(models.Flavors)

    if flavor_id is not None:
        query = query.filter(models.Flavors.id == flavor_id)
    else:
        query = query.filter(models.Flavors.flavorid == flavorid)
    result = query.first()

    if not result:
        raise exception.FlavorNotFound(flavor_id=(flavor_id or flavorid))

    return result


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Flavor(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version
    # Version 1.1: Added save_projects(), save_extra_specs(), removed
    #              remotable from save()
    # Version 1.2: Added description field. Note: this field should not be
    #              persisted with the embedded instance.flavor.
    VERSION = '1.2'

    fields = {
        'id': fields.IntegerField(),
        'name': fields.StringField(nullable=True),
        'ram': fields.IntegerField(),
        'vcpus': fields.IntegerField(),
        'disk': fields.IntegerField(),
        'swap': fields.IntegerField(),
        'description': fields.StringField(nullable=True)
        }

    def __init__(self, *args, **kwargs):
        super(Flavor, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_projects = []

    def obj_make_compatible(self, primitive, target_version):
        super(Flavor, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)
        if target_version < (1, 2) and 'description' in primitive:
            del primitive['description']

    @staticmethod
    def _from_db_object(context, flavor, db_flavor, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        flavor._context = context
        for name, field in flavor.fields.items():
            if name in OPTIONAL_FIELDS:
                continue
            if name in DEPRECATED_FIELDS and name not in db_flavor:
                continue
            value = db_flavor[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            flavor[name] = value

        # NOTE(danms): This is to support processing the API flavor
        # model, which does not have these deprecated fields. When we
        # remove compatibility with the old InstanceType model, we can
        # remove this as well.
        if any(f not in db_flavor for f in DEPRECATED_FIELDS):
            flavor.deleted_at = None
            flavor.deleted = False

        flavor.obj_reset_changes()
        return flavor

    @staticmethod
    @db_api.main_context_manager.reader
    def _flavor_get_query_from_db(context):
        query = context.session.query(models.Flavors)
        return query

    @staticmethod
    @require_context
    def _flavor_get_from_db(context, id):
        """Returns a dict describing specific flavor."""
        result = Flavor._flavor_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.FlavorNotFound(flavor_id=id)
        return result


    def obj_reset_changes(self, fields=None, recursive=False):
        super(Flavor, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Flavor, self).obj_what_changed()
        return changes


    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_flavor = cls._flavor_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_flavor,
                                   expected_attrs=[])


    @staticmethod
    def _flavor_create(context, updates):
        return _flavor_create(context, updates)

    @base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_flavor = self._flavor_create(context, updates)
        self._from_db_object(context, self, db_flavor)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a flavor.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_flavor = context.session.query(models.Flavors).\
            filter_by(id=self.id).first()
        if not db_flavor:
            raise exception.FlavorNotFound(flavor_id=self.id)
        db_flavor.update(values)
        db_flavor.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_flavor)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _flavor_destroy(context, flavor_id=None, flavorid=None):
        return _flavor_destroy(context, flavor_id=flavor_id, flavorid=flavorid)

    @base.remotable
    def destroy(self):
        # NOTE(danms): Historically the only way to delete a flavor
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a flavor object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            db_flavor = self._flavor_destroy(self._context,
                                             flavor_id=self.id)
        else:
            db_flavor = self._flavor_destroy(self._context,
                                             flavorid=self.flavorid)
        self._from_db_object(self._context, self, db_flavor)
