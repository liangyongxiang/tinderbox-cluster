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

import os
from pathlib import Path

import portage

from oslo_log import log as logging

from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def check_profile(context, project_repopath, project_metadata_db):
    profile_repo_db = objects.repo.Repo.get_by_uuid(context, project_metadata_db.project_profile_repo_uuid)
    profile_repopath = CONF.repopath + '/' + profile_repo_db.name + '.git/' + 'profiles/'
    if not Path(project_repopath + 'etc/portage/make.profile').is_symlink():
        Path(project_repopath + 'etc/portage/make.profile').symlink_to(profile_repopath + project_metadata_db.project_profile)
    else:
        if Path(project_repopath + 'etc/portage/make.profile').resolve() != project_repopath + project_metadata_db.project_profile:
            pass

def get_portage_settings(context, project_metadata_db, project_repo_name):
    settings_repo_db = objects.repo.Repo.get_by_uuid(context, project_metadata_db.project_repo_uuid)
    project_repopath = CONF.repopath + '/' + settings_repo_db.name + '.git/' + project_repo_name + '/'
    if Path(project_repopath).exists():
        check_profile(context, project_repopath, project_metadata_db)
        # Set config_root (PORTAGE_CONFIGROOT) to project_repopath
        mysettings = portage.config(config_root = project_repopath)
        myportdb = portage.portdbapi(mysettings=mysettings)
        return mysettings, myportdb

def clean_portage_settings(myportdb):
    myportdb.close_caches()
    portage.portdbapi.portdbapi_instances.remove(myportdb)
