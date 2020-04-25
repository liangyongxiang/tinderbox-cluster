# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from oslo_log import log as logging

from gosbs.common.portage_settings import get_portage_settings
from gosbs.scheduler.category import check_c_db
from gosbs.scheduler.package import check_cp_db, get_all_cp_from_repo
from gosbs.scheduler.project import get_project
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def rebuild_repo_db_thread(context, service_repo_db):
    project_db, project_metadata_db = get_project(context, service_repo_db)
    repo_db = objects.repo.Repo.get_by_uuid(context, service_repo_db.repo_uuid)
    mysettings, myportdb = get_portage_settings(context, project_metadata_db, project_db.name)
    repo_path = CONF.repopath + '/' + repo_db.name + '.git'
    LOG.debug("Rebuilding repo %s", repo_db.name)
    for cp in sorted(get_all_cp_from_repo(myportdb, repo_path)):
        category = cp.split('/')[0]
        succesc = check_c_db(context, category, repo_db)
        category_db = objects.category.Category.get_by_name(context, category)
        succesp = check_cp_db(context, myportdb, cp, repo_db, category_db)
    return True

def task(context, service_uuid):
    filters = {
               'service_uuid' : service_uuid,
               'status' : 'rebuild_db',
               }
    for service_repo_db in objects.service_repo.ServiceRepoList.get_all(context, filters=filters):
        service_repo_db.status = 'in-progress'
        service_repo_db.save(context)
        succes = rebuild_repo_db_thread(context, service_repo_db)
        if not succes:
            service_repo_db.status = 'failed'
        else:
            service_repo_db.status = 'completed'
        service_repo_db.save(context)
