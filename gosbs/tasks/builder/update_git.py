# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import sys

from oslo_log import log as logging
from gosbs import objects
from gosbs.common.git import check_git_repo
from gosbs.common.portage_settings import check_profile, check_portage
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def update_repo_git_thread(context, service_uuid, repo_db):
    repo_dict = { 'repo_uuid' : repo_db.uuid,
               'repo_name' : repo_db.name,
               'repo_url' : CONF.builder.git_mirror_url + '/' + repo_db.name + '.git',
               'repo_type' : repo_db.repo_type,
               'repo_path' : CONF.repopath + '/' + repo_db.name + '.git',
               'history' : False,
                   }
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
        service_repo_db.status = 'waiting'
        service_repo_db.create(context)
    if service_repo_db.status == 'waiting':
        service_repo_db.status = 'in-progress'
        service_repo_db.save(context)
        succes = check_git_repo(repo_dict)
        if succes:
            service_repo_db.status = 'completed'
        else:
            service_repo_db.status = 'failed'
        service_repo_db.save(context)
        return succes
    return True

def task(context, service_uuid):
    project_db = objects.project.Project.get_by_name(context, CONF.builder.project)
    project_metadata_db = objects.project_metadata.ProjectMetadata.get_by_uuid(context, project_db.uuid)
    repo_db = objects.repo.Repo.get_by_uuid(context, project_metadata_db.project_repo_uuid)
    succes = update_repo_git_thread(context, service_uuid, repo_db)
    filters = {
               'project_uuid' : project_db.uuid,
               }
    if succes:
        project_repopath = CONF.repopath + '/' + repo_db.name + '.git/' + CONF.builder.project + '/'
        check_portage(context, project_repopath)
        check_profile(context, project_repopath, project_metadata_db)
        for project_repo_db in objects.project_repo.ProjectRepoList.get_all(context, filters):
            repo_db = objects.repo.Repo.get_by_uuid(context, project_repo_db.repo_uuid)
            succes = update_repo_git_thread(context, service_uuid, repo_db)
    return
    #with futurist.GreenThreadPoolExecutor(max_workers=1) as executor:
        # Start the load operations and mark each future with its URL
    #    for cp in cp_list:
    #        future = executor.submit(update_cpv_db_thread, context, cp, repo_uuid, project_uuid)
    #        print(future.result())
