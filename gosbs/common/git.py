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

import re
import git
import os

from oslo_log import log as logging
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def fetch(repo):
    remote = git.remote.Remote(repo, 'origin')
    info_list = remote.fetch()
    local_commit = repo.commit()
    remote_commit = info_list[0].commit
    if local_commit.hexsha != remote_commit.hexsha:
        return info_list, False
    return info_list, True

def merge(repo, info):
    repo.git.merge(info.commit)

def update_git_repo_db(repo_dict):
    # check git diffs witch get updated and pass that to objects Packages
    # fetch and merge the repo
    search_list = [ '^metadata', '^eclass', '^licenses', '^profiles', '^scripts', '^skel.', '^header.txt']
    repo = git.Repo(repo_dict['repo_path'])
    cp_list = []
    info_list, repo_uptodate = fetch(repo)
    if repo_uptodate:
        return True, cp_list
    # We check for dir changes and add the package to a list
    repo_diff = repo.git.diff('origin', '--name-only'
    #write_log(session, 'Git dir diff:\n%s' % (repo_diff,), "debug", config_id, 'sync.git_sync_main')
    for diff_line in repo_diff.splitlines():
        find_search = True
        for search_line in search_list:
            if re.search(search_line, diff_line):
                find_search = False
        if find_search:
            splited_diff_line = re.split('/', diff_line)
            c = splited_diff_line[0]
            p = splited_diff_line[1]
            cp = c + '/' + p
            if not cp in cp_list:
                cp_list.append(cp)
            #write_log(session, 'Git CP Diff: %s' % (cp_list,), "debug", config_id, 'sync.git_sync_main')
    merge(repo, info_list[0])
    return True, cp_list

def update_git_repo(repo_dict):
    repo = git.Repo(repo_dict['repo_path'])
    try:
        repo.git.pull()
    except:
        return False
    return True

def create_git_repo(repo_dict):
    try:
        os.mkdir(repo_dict['repo_path'])
    except OSError:  
        LOG.error("Creation of the directory %s failed" % repo_dict['repo_path'])
        return False
    try:
        if not repo_dict['history']:
            git.Repo.clone_from(repo_dict['repo_url'], repo_dict['repo_path'], 'depth=1')
        else:
            git.Repo.clone_from(repo_dict['repo_url'], repo_dict['repo_path'],)
    except:
        return False
    return True
    
def check_git_repo_db(repo_dict):
    if not os.path.isdir(repo_dict['repo_path']):
        succes = create_git_repo(repo_dict)
        return succes, None
    succes, cp_list = update_git_repo_db(repo_dict)
    return succes, cp_list

def check_git_repo(repo_dict):
    if not os.path.isdir(repo_dict['repo_path']):
        succes = create_git_repo(repo_dict)
    else:
        succes = update_git_repo(repo_dict)
    return succes
