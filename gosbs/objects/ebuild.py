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
PROJECT_STATUS = ['failed', 'completed', 'in-progress', 'waiting']

def _dict_with_extra_specs(ebuild_model):
    extra_specs = {}
    return dict(ebuild_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _ebuild_create(context, values):
    db_ebuild = models.Ebuilds()
    db_ebuild.update(values)

    try:
        db_ebuild.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'ebuildid' in e.columns:
            raise exception.ImagesIdExists(ebuild_id=values['ebuildid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_ebuild)


@db_api.main_context_manager.writer
def _ebuild_destroy(context, ebuild_id=None, ebuildid=None):
    query = context.session.query(models.Ebuilds)

    if ebuild_id is not None:
        query.filter(models.Ebuilds.uuid == ebuild_id).delete()
    else:
        query.filter(models.Ebuilds.uuid == ebuildid).delete()


@base.NovaObjectRegistry.register
class Ebuild(base.NovaObject, base.NovaObjectDictCompat, base.NovaPersistentObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'uuid': fields.UUIDField(),
        'package_uuid': fields.UUIDField(),
        'version' : fields.StringField(nullable=True),
        'checksum': fields.StringField(nullable=True),
        }

    def __init__(self, *args, **kwargs):
        super(Ebuild, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_ebuilds = []

    def obj_make_compatible(self, primitive, target_version):
        super(Ebuild, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, ebuild, db_ebuild, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        ebuild._context = context
        for name, field in ebuild.fields.items():
            value = db_ebuild[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            ebuild[name] = value
        
        ebuild.obj_reset_changes()
        return ebuild

    @staticmethod
    @db_api.main_context_manager.reader
    def _ebuild_get_query_from_db(context):
        query = context.session.query(models.Ebuilds)
        return query

    @staticmethod
    @require_context
    def _ebuild_get_from_db(context, uuid):
        """Returns a dict describing specific ebuilds."""
        result = Ebuild._ebuild_get_query_from_db(context).\
                        filter_by(uuid=uuid).\
                        first()
        if not result:
            raise exception.ImagesNotFound(ebuild_id=uuid)
        return result

    @staticmethod
    @require_context
    def _ebuild_get_by_name_from_db(context, name):
        """Returns a dict describing specific flavor."""
        result = Ebuild._ebuild_get_query_from_db(context).\
                            filter_by(version=name).\
                            first()
        if not result:
            return None
        return result

    def obj_reset_changes(self, fields=None, recursive=False):
        super(Ebuild, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Ebuild, self).obj_what_changed()
        return changes

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        db_ebuild = cls._ebuild_get_from_db(context, uuid)
        return cls._from_db_object(context, cls(context), db_ebuild,
                                   expected_attrs=[])
    @base.remotable_classmethod
    def get_by_name(cls, context, version, filters=None):
        filters = filters or {}
        db_ebuild = Ebuild._ebuild_get_query_from_db(context)
        db_ebuild = db_ebuild.filter_by(version=version)
        if 'deleted' in filters:
            db_ebuild = db_ebuild.filter(
                models.Ebuilds.deleted == filters['deleted'])
        if 'package_uuid' in filters:
            db_ebuild = db_ebuild.filter(
                models.Ebuilds.package_uuid == filters['package_uuid'])
        db_ebuild = db_ebuild.first()
        if not db_ebuild:
            return None
        return cls._from_db_object(context, cls(context), db_ebuild,
                                   expected_attrs=[])

    @staticmethod
    def _ebuild_create(context, updates):
        return _ebuild_create(context, updates)

    #@base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_ebuild = self._ebuild_create(context, updates)
        self._from_db_object(context, self, db_ebuild)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a ebuilds.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_ebuild = context.session.query(models.Ebuilds).\
            filter_by(uuid=self.uuid).first()
        if not db_ebuild:
            raise exception.ImagesNotFound(ebuild_id=self.uuid)
        db_ebuild.update(values)
        db_ebuild.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_ebuild)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _ebuild_destroy(context, ebuild_id=None, ebuildid=None):
        _ebuild_destroy(context, ebuild_id=ebuild_id, ebuildid=ebuildid)

    #@base.remotable
    def destroy(self, context):
        # NOTE(danms): Historically the only way to delete a ebuilds
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a ebuilds object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'uuid' in self:
            self._ebuild_destroy(context, ebuild_id=self.uuid)
        else:
            self._ebuild_destroy(context, ebuildid=self.ebuildid)
        #self._from_db_object(context, self, db_ebuild)

    @base.remotable_classmethod
    def get_by_filters_first(cls, context, filters=None):
        filters = filters or {}
        db_ebuild = Ebuild._ebuild_get_query_from_db(context)
    
        return cls._from_db_object(context, cls(context), db_ebuild,
                                   expected_attrs=[])


@db_api.main_context_manager
def _ebuild_get_all_from_db(context, inactive, filters, sort_key, sort_dir,
                            limit, marker):
    """Returns all ebuildss.
    """
    filters = filters or {}

    query = Ebuild._ebuild_get_query_from_db(context)

    if 'deleted' in filters:
            query = query.filter(
                models.Ebuilds.deleted == filters['deleted'])
    if 'package_uuid' in filters:
            query = query.filter(
                models.Ebuilds.package_uuid == filters['package_uuid'])

    marker_row = None
    if marker is not None:
        marker_row = Ebuild._ebuild_get_query_from_db(context).\
                    filter_by(uuid=marker).\
                    first()
        if not marker_row:
            raise exception.MarkerNotFound(marker=marker)

    query = sqlalchemyutils.paginate_query(query, models.Ebuilds,
                                           limit,
                                           [sort_key, 'uuid'],
                                           marker=marker_row,
                                           sort_dir=sort_dir)
    return [_dict_with_extra_specs(i) for i in query.all()]


@base.NovaObjectRegistry.register
class EbuildList(base.ObjectListBase, base.NovaObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Ebuild'),
        }

    @base.remotable_classmethod
    def get_all(cls, context, inactive=False, filters=None,
                sort_key='uuid', sort_dir='asc', limit=None, marker=None):
        db_ebuilds = _ebuild_get_all_from_db(context,
                                                 inactive=inactive,
                                                 filters=filters,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir,
                                                 limit=limit,
                                                 marker=marker)
        return base.obj_make_list(context, cls(context), objects.ebuild.Ebuild,
                                  db_ebuilds,
                                  expected_attrs=[])

    @db_api.main_context_manager.writer
    def destroy_all(context):
        context.session.query(models.Ebuilds).delete()

    @db_api.main_context_manager.writer
    def update_all(context):
        values = {'status': 'waiting', }
        db_ebuild = context.session.query(models.Ebuilds).filter_by(auto=True)
        db_ebuild.update(values)
