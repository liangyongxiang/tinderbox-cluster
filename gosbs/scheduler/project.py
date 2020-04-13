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

from oslo_log import log as logging

from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def get_project(context, service_repo_db):
    project_db = objects.project.Project.get_by_name(context, CONF.builder.project)
    project_metadata_db = objects.project_metadata.ProjectMetadata.get_by_uuid(context, project_db.uuid)
    print(project_db)
    filters = { 'project_uuid' : project_db.uuid, 
               'repo_uuid' : service_repo_db.repo_uuid,
               }
    project_repo_db = objects.project_repo.ProjectRepo.get_by_filters(context, filters=filters)
    if project_repo_db is None:
        project_repo_db = objects.project_repo.ProjectRepo()
        project_repo_db.project_uuid = project_db.uuid
        project_repo_db.repo_uuid = service_repo_db.repo_uuid
        project_repo_db.build = False
        project_repo_db.create(context)
    return project_db, project_metadata_db
