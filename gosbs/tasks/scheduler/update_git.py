# Copyright 1999-2020 Gentoo Authors
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

import sys

from oslo_log import log as logging
from gosbs import objects
from gosbs.common.git import check_git_repo, check_git_repo_db
from gosbs.scheduler.category import check_c_db
from gosbs.scheduler.package import create_cp_db
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def update_repo_git_thread(context, service_uuid, repo_db):
    repo_dict = { 'repo_uuid' : repo_db.uuid,
               'repo_name' : repo_db.name,
               'repo_url' : repo_db.src_url,
               'repo_type' : repo_db.repo_type,
               'repo_path' : CONF.repopath + '/' + repo_db.name + '.git',
               'history' : True,
                   }
    repo_db.status = 'in-progress'
    repo_db.save(context)
    filters = {
               'repo_uuid' : repo_db.uuid,
               'service_uuid' : service_uuid,
               }
    service_repo_db = objects.service_repo.ServiceRepo.get_by_filters(context, filters=filters)
    if service_repo_db is None:
        service_repo_db = objects.service_repo.ServiceRepo()
        service_repo_db.repo_uuid = repo_db.uuid
        service_repo_db.service_uuid = service_uuid
        service_repo_db.auto = repo_db.auto
        service_repo_db.status = 'in-progress'
        service_repo_db.create(context)
    else:
        service_repo_db.status = 'in-progress'
        service_repo_db.save(context)
    cp_list = []
    if repo_db.repo_type == 'project':
        succes = check_git_repo(repo_dict)
    else:
        succes, cp_list = check_git_repo_db(repo_dict)
    if not succes:
        repo_db.status = 'failed'
        repo_db.save(context)
        service_repo_db.status = 'failed'
        service_repo_db.save(context)
        return False
    repo_db.status = 'completed'
    repo_db.save(context)
    if cp_list is None:
        service_repo_db.status = 'rebuild_db'
        service_repo_db.save(context)
        return True
    if cp_list == []:
        service_repo_db.status = 'completed'
        service_repo_db.save(context)
        return True
    for cp in cp_list:
        category = cp.split('/')[0]
        package = cp.split('/')[1]
        succesc = check_c_db(context, category, repo_db)
        category_db = objects.category.Category.get_by_name(context, category)
        filters = { 'repo_uuid' : repo_dict['repo_uuid'],
                   'category_uuid' : category_db.uuid,
                }
        package_db = objects.package.Package.get_by_name(context, package, filters=filters)
        if package_db is None:
            LOG.info("Adding %s to the database", package)
            package_db = create_cp_db(context, package, repo_db, category_db)
        package_db.status = 'waiting'
        package_db.save(context)
    service_repo_db.status = 'update_db'
    service_repo_db.save(context)
    return True

def task(context, service_uuid):
    filters = { 'status' : 'waiting',
               'deleted' : False,
               }
    for repo_db in objects.repo.RepoList.get_all(context, filters=filters):
        if repo_db is None:
            return
        succes = update_repo_git_thread(context, service_uuid, repo_db)
    return
    #with futurist.GreenThreadPoolExecutor(max_workers=1) as executor:
        # Start the load operations and mark each future with its URL
    #    for cp in cp_list:
    #        future = executor.submit(update_cpv_db_thread, context, cp, repo_uuid, project_uuid)
    #        print(future.result())
