# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from oslo_log import log as logging

from gosbs import objects
import gosbs.conf
from gosbs.context import get_admin_context

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def check_build(settings, pkg, trees):
    context = get_admin_context()
    service_ref = objects.Service.get_by_host_and_topic(context, CONF.host, "builder")
    project_db = objects.project.Project.get_by_name(context, CONF.builder.project)
    project_metadata_db = objects.project_metadata.ProjectMetadata.get_by_uuid(context, project_db.uuid)
