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

def _dict_with_extra_specs(package_model):
    extra_specs = {}
    return dict(package_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _package_create(context, values):
    db_package = models.PackagesEmails()
    db_package.update(values)

    try:
        db_package.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'packageid' in e.columns:
            raise exception.ImagesIdExists(package_id=values['packageid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_package)


@db_api.main_context_manager.writer
def _package_destroy(context, package_id=None, packageid=None):
    query = context.session.query(models.PackagesEmails)

    if package_id is not None:
        query.filter(models.PackagesEmails.id == package_id).delete()
    else:
        query.filter(models.PackagesEmails.id == packageid).delete()


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class PackageEmail(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'package_uuid': fields.UUIDField(),
        'email_id': fields.IntegerField(),
        }

    def __init__(self, *args, **kwargs):
        super(PackageEmail, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_packages = []

    def obj_make_compatible(self, primitive, target_version):
        super(PackageEmail, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, package, db_package, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        package._context = context
        for name, field in package.fields.items():
            value = db_package[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            package[name] = value
        
        package.obj_reset_changes()
        return package

    @staticmethod
    @db_api.main_context_manager.reader
    def _package_get_query_from_db(context):
        query = context.session.query(models.PackagesEmails)
        return query

    @staticmethod
    @require_context
    def _package_get_from_db(context, id):
        """Returns a dict describing specific packages."""
        result = PackageEmail._package_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(package_id=id)
        return result

    @staticmethod
    @require_context
    def _email_id_get_from_db(context, email_id):
        """Returns a dict describing specific packages."""
        result = PackageEmail._package_get_query_from_db(context).\
                        filter_by(email_id=email_id).\
                        first()
        return result

    @staticmethod
    @require_context
    def _package_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = PackageEmail._package_get_query_from_db(context).\
                            filter_by(name=email).\
                            first()
        if not result:
            raise exception.FlavorNotFoundByName(packages_name=name)
        return _dict_with_extra_specs(result)

    def obj_reset_changes(self, fields=None, recursive=False):
        super(PackageEmail, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(PackageEmail, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_id(cls, context, id, filters=None):
        db_package = cls._package_get_from_db(context, id)
        if 'package_uuid' in filters:
            db_package = db_package.filter(
                models.PackagesEmails.package_uuid == filters['package_uuid'])
        return cls._from_db_object(context, cls(context), db_package,
                                   expected_attrs=[])

    @base.remotable_classmethod
    def get_by_email_id(cls, context, email_id, filters=None):
        filters = filters or {}
        db_package = PackageEmail._package_get_query_from_db(context)
        db_package = db_package.filter_by(email_id=email_id)
        if 'package_uuid' in filters:
            db_package = db_package.filter(
                models.PackagesEmails.package_uuid == filters['package_uuid'])
        db_package = db_package.first()
        if not db_package:
            return None
        return cls._from_db_object(context, cls(context), db_package,
                                   expected_attrs=[])

    @base.remotable_classmethod
    def get_by_name(cls, context, name, filters=None):
        filters = filters or {}
        db_package = cls._package_get_by_name_from_db(context, name)
        if 'package_uuid' in filters:
            db_package = db_package.filter(
                models.PackagesEmails.package_uuid == filters['package_uuid'])
        return cls._from_db_object(context, cls(context), db_package,
                                   expected_attrs=[])

    @staticmethod
    def _package_create(context, updates):
        return _package_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_package = self._package_create(context, updates)
        self._from_db_object(context, self, db_package)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a packages.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_package = context.session.query(models.PackagesEmails).\
            filter_by(id=self.id).first()
        if not db_package:
            raise exception.ImagesNotFound(package_id=self.id)
        db_package.update(values)
        db_package.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_package)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _package_destroy(context, package_id=None, packageid=None):
        _package_destroy(context, package_id=package_id, packageid=packageid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a packages
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a packages object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            self._package_destroy(context, package_id=self.id)
        else:
            self._package_destroy(context, packageid=self.packageid)
        #self._from_db_object(context, self, db_package)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_package = PackageEmail._package_get_query_from_db(context)

        return cls._from_db_object(context, cls(context), db_package,
                                   expected_attrs=[])


@db_api.main_context_manager
def _package_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all packagess.
    """
    filters = filters or {}

    query = PackageEmail._package_get_query_from_db(context)

    marker_row = None
    if marker is not None:
        marker_row = PackageEmail._package_get_query_from_db(context).\
                    filter_by(id=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.PackageEmails,
                                           limit,
                                           [sort_key, 'id'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class PackageEmailList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('PackageEmail'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='id', sort_dir='asc', limit=None, marker=None):
        db_packages = _package_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.package.PackageEmail,
                                  db_packages,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.PackagesEmails).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_package = context.session.query(models.PackagesEmails).filter_by(auto=True)
        db_package.update(values)
