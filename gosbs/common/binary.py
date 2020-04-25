# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from oslo_log import log as logging
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def destroy_local_binary(context, build_job, project_db, service_uuid, mysettings):
    filters = {
        'ebuild_uuid' : build_job['ebuild'].uuid,
        'project_uuid' : project_db.uuid,
        'service_uuid' : service_uuid,
        }
    for local_binary_db in objects.local_binary.LocalBinaryList.get_all(context, filters=filters):
        local_binary_db.destroy(context)
        binfile = mysettings['PKGDIR'] + "/" + build_job['cpv'] + ".tbz2"
        try:
            os.remove(binfile)
        except:
            LOG.error("Package file was not removed or not found: %s" % binfile)

def destroy_objectstor_binary(context, build_job, project_db):
    filters = {
        'ebuild_uuid' : build_job['ebuild'].uuid,
        'project_uuid' : project_db.uuid,
        }
    for objectstor_binary_db in objects.objectstor_binary.ObjectStorBinaryList.get_all(context, filters=filters):
        objectstor_binary_db.destroy(context)
        # Fixme: remove the file on ObjectStor
