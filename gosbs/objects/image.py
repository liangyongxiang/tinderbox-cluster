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


def _dict_with_extra_specs(image_model):
    extra_specs = {}
    return dict(image_model, extra_specs=extra_specs)


@db_api.main_context_manager.writer
def _image_create(context, values):
    db_image = models.Images()
    db_image.update(values)

    try:
        db_image.save(context.session)
    except db_exc.DBDuplicateEntry as e:
        if 'imageid' in e.columns:
            raise exception.ImagesIdExists(image_id=values['imageid'])
        raise exception.ImagesExists(name=values['name'])
    except Exception as e:
        raise db_exc.DBError(e)

    return _dict_with_extra_specs(db_image)


@db_api.main_context_manager.writer
def _image_destroy(context, image_id=None, imageid=None):
    query = context.session.query(models.Images)

    if image_id is not None:
        query = query.filter(models.Images.id == image_id)
    else:
        query = query.filter(models.Images.imageid == imageid)
    result = query.first()

    if not result:
        raise exception.ImagesNotFound(image_id=(image_id or imageid))

    return result


# TODO(berrange): Remove NovaObjectDictCompat
# TODO(mriedem): Remove NovaPersistentObject in version 2.0
@base.NovaObjectRegistry.register
class Image(base.NovaObject, base.NovaObjectDictCompat):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'id': fields.UUIDField(),
        'name': fields.StringField(),
        'min_ram': fields.IntegerField(),
        'min_disk': fields.IntegerField(),
        'size': fields.IntegerField(),
        'status': fields.StringField()
        }

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self._orig_extra_specs = {}
        self._orig_projects = []

    def obj_make_compatible(self, primitive, target_version):
        super(Image, self).obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)


    @staticmethod
    def _from_db_object(context, image, db_image, expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = []
        image._context = context
        for name, field in image.fields.items():
            value = db_image[name]
            if isinstance(field, fields.IntegerField):
                value = value if value is not None else 0
            image[name] = value
        
        image.obj_reset_changes()
        return image

    @staticmethod
    @db_api.main_context_manager.reader
    def _image_get_query_from_db(context):
        query = context.session.query(models.Images)
        return query

    @staticmethod
    @require_context
    def _image_get_from_db(context, id):
        """Returns a dict describing specific image."""
        result = Image._image_get_query_from_db(context).\
                        filter_by(id=id).\
                        first()
        if not result:
            raise exception.ImagesNotFound(image_id=id)
        return result


    def obj_reset_changes(self, fields=None, recursive=False):
        super(Image, self).obj_reset_changes(fields=fields,
                recursive=recursive)

    def obj_what_changed(self):
        changes = super(Image, self).obj_what_changed()
        return changes


    @base.remotable_classmethod
    def get_by_id(cls, context, id):
        db_image = cls._image_get_from_db(context, id)
        return cls._from_db_object(context, cls(context), db_image,
                                   expected_attrs=[])


    @staticmethod
    def _image_create(context, updates):
        return _image_create(context, updates)

    @base.remotable
    def create(self, context):
        #if self.obj_attr_is_set('id'):
        #    raise exception.ObjectActionError(action='create',
        #reason='already created')
        updates = self.obj_get_changes()
        db_image = self._image_create(context, updates)
        self._from_db_object(context, self, db_image)


    # NOTE(mriedem): This method is not remotable since we only expect the API
    # to be able to make updates to a image.
    @db_api.main_context_manager.writer
    def _save(self, context, values):
        db_image = context.session.query(models.Images).\
            filter_by(id=self.id).first()
        if not db_image:
            raise exception.ImagesNotFound(image_id=self.id)
        db_image.update(values)
        db_image.save(context.session)
        # Refresh ourselves from the DB object so we get the new updated_at.
        self._from_db_object(context, self, db_image)
        self.obj_reset_changes()

    def save(self, context):
        updates = self.obj_get_changes()
        if updates:
            self._save(context, updates)

    @staticmethod
    def _image_destroy(context, image_id=None, imageid=None):
        return _image_destroy(context, image_id=image_id, imageid=imageid)

    @base.remotable
    def destroy(self):
        # NOTE(danms): Historically the only way to delete a image
        # is via name, which is not very precise. We need to be able to
        # support the light construction of a image object and subsequent
        # delete request with only our name filled out. However, if we have
        # our id property, we should instead delete with that since it's
        # far more specific.
        if 'id' in self:
            db_image = self._image_destroy(self._context,
                                             image_id=self.id)
        else:
            db_image = self._image_destroy(self._context,
                                             imageid=self.imageid)
        self._from_db_object(self._context, self, db_image)
