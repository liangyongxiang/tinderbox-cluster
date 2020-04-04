# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from datetime import datetime

from oslo_log import log as logging

from gosbs import objects
from gosbs.common.task import check_task_db

LOG = logging.getLogger(__name__)

def activete_all_tasks(context, service_uuid):
    # Tasks
    check_task_db(context, 'update_repos', datetime(1, 1, 1, 0, 15, 0, 0), True, service_uuid)
    check_task_db(context, 'update_git', datetime(1, 1, 1, 0, 5, 0, 0), True, service_uuid)
    check_task_db(context, 'update_db', datetime(1, 1, 1, 0, 5, 0, 0), True, service_uuid)
    check_task_db(context, 'rebuild_db', datetime(1, 1, 1, 0, 10, 0, 0), True, service_uuid)
