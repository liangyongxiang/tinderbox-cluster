# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import pdb
from oslo_log import log as logging

from gosbs.common.portage_settings import get_portage_settings, clean_portage_settings
from gosbs.scheduler.package import check_cp_db
from gosbs.scheduler.project import get_project
from gosbs.tasks.scheduler.sub.build import build_sub_task
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def update_repo_db_multi_thread(context, myportdb, repo_db, package_db):
    category_db = objects.category.Category.get_by_uuid(context, package_db.category_uuid)
    cp = category_db.name + '/' + package_db.name
    succes, ebuild_version_tree_dict_new = check_cp_db(context, myportdb, cp, repo_db, category_db)
    # sub tasks
    succes = build_sub_task(context, cp, ebuild_version_tree_dict_new, repo_db)
    return True

def update_repo_db_thread(context, service_repo_db):
    project_db, project_metadata_db = get_project(context, service_repo_db)
    repo_db = objects.repo.Repo.get_by_uuid(context, service_repo_db.repo_uuid)
    mysettings, myportdb = get_portage_settings(context, project_metadata_db, project_db.name)
    succes = True
    filters = { 'repo_uuid' : repo_db.uuid,
                       'status' : 'waiting',
                    }
    for package_db in objects.package.PackageList.get_all(context, filters=filters):
        succes = update_repo_db_multi_thread(context, myportdb, repo_db, package_db)
    clean_portage_settings(myportdb)
    return succes

def task(context, service_uuid):
    filters = {
               'service_uuid' : service_uuid,
               'status' : 'update_db',
               }
    for service_repo_db in objects.service_repo.ServiceRepoList.get_all(context, filters=filters):
        service_repo_db.status = 'in-progress'
        service_repo_db.save(context)
        succes = update_repo_db_thread(context, service_repo_db)
        if not succes:
            service_repo_db.status = 'failed'
        else:
            service_repo_db.status = 'completed'
        service_repo_db.save(context)
