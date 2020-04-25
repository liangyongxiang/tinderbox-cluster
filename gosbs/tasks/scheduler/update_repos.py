# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from oslo_log import log as logging
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def task(context, service_uuid):
    LOG.info('Update Repos')
    objects.repo.RepoList.update_all(context)
