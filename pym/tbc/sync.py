# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import errno
import sys
import time
import re
import git

from tbc.sqlquerys import get_config_id_fqdn, add_logs, get_config_all_info, \
	get_configmetadata_info, get_config_info, get_setup_info
from tbc.readconf import read_config_settings
from tbc.log import write_log

def git_repos_list(myportdb):
	repo_trees_list = myportdb.porttrees
	repo_dir_list = []
	for repo_dir in repo_trees_list:
		repo_dir_list.append(repo_dir)
	return repo_dir_list

def git_fetch(repo):
	repouptodate = True
	remote = git.remote.Remote(repo, 'origin')
	info_list = remote.fetch()
	local_commit = repo.commit()
	remote_commit = info_list[0].commit
	if local_commit.hexsha != remote_commit.hexsha:
		repouptodate = False
	return info_list, repouptodate

def git_merge(repo, info):
	repo.git.merge(info.commit)

def git_sync_main(session):
	tbc_settings = read_config_settings()
	config_id = get_config_id_fqdn(session, tbc_settings['hostname'])
	ConfigsMetaDataInfo = get_configmetadata_info(session, config_id)
	ConfigInfo = get_config_info(session, config_id)
	SetupInfo = get_setup_info(session, ConfigInfo.SetupId)
	host_config = ConfigInfo.Hostname +"/" + SetupInfo.Setup
	default_config_root = ConfigsMetaDataInfo.RepoPath + "/" + host_config + "/"
	mysettings = portage.config(config_root = default_config_root)
	myportdb = portage.portdbapi(mysettings=mysettings)
	GuestBusy = True
	log_msg = "Waiting for Guest to be idel"
	write_log(session, log_msg, "info", config_id, 'sync.git_sync_main')
	guestid_list = []
	# check if the guests is idel
	for config in get_config_all_info(session):
		if not config.Host:
			guestid_list.append(config.ConfigId)
	while GuestBusy:
		Status_list = []
		for guest_id in guestid_list:
			ConfigMetadataGuest = get_configmetadata_info(session, guest_id)
			Status_list.append(ConfigMetadataGuest.Status)
		write_log(session, 'Guset status: %s' % (Status_list,), "debug", config_id, 'sync.git_sync_main')
		if not 'Runing' in Status_list:
			GuestBusy = False
		else:
			time.sleep(60)
	#remove the needed base profile clone
	try:
		os.remove(mysettings['PORTDIR'] + "/profiles/config/parent")
		os.rmdir(mysettings['PORTDIR'] + "/profiles/config")
	except:
		pass

	# check git diffs witch get updated and pass that to a dict
	# fetch and merge the repo
	repo_cp_dict = {}
	search_list = [ '^metadata', '^eclass', '^licenses', '^profiles', '^scripts',]
	for repo_dir in git_repos_list(myportdb):
		reponame = myportdb.getRepositoryName(repo_dir)
		repo = git.Repo(repo_dir)
		log_msg = "Checking repo %s" % (reponame)
		write_log(session, log_msg, "info", config_id, 'sync.git_sync_main')
		info_list, repouptodate = git_fetch(repo)
		if not repouptodate:
			cp_list = []
			attr = {}
			# We check for dir changes and add the package to a list
			repo_diff = repo.git.diff('origin', '--name-only')
			write_log(session, 'Git dir diff:\n%s' % (repo_diff,), "debug", config_id, 'sync.git_sync_main')
			for diff_line in repo_diff.splitlines():
                                find_search = True
                                for search_line in search_list:
                                        if re.search(search_line, diff_line):
                                                find_search = False
                                if find_search:
                                        splited_diff_line = re.split('/', diff_line)
                                        cp = splited_diff_line[0] + '/' + splited_diff_line[1]
                                        if not cp in cp_list:
                                                cp_list.append(cp)
			attr['cp_list'] = cp_list
			write_log(session, 'Git CP Diff: %s' % (cp_list,), "debug", config_id, 'sync.git_sync_main')
			repo_cp_dict[reponame] = attr
			git_merge(repo, info_list[0])
		else:
			log_msg = "Repo %s is up to date" % (reponame)
			write_log(session, log_msg, "info", config_id, 'sync.git_sync_main')
		log_msg = "Checking repo %s Done" % (reponame)
		write_log(session, log_msg, "info", config_id, 'sync.git_sync_main')
	# Need to add a clone of profiles/base for reading the tree
	try:
		os.mkdir(mysettings['PORTDIR'] + "/profiles/config", 0o777)
		with open(mysettings['PORTDIR'] + "/profiles/config/parent", "w") as f:
			f.write("../base\n")
			f.close()
	except:
		pass

	log_msg = "Repo sync ... Done."
	write_log(session, log_msg, "info", config_id, 'sync.git_sync_main')
	write_log(session, 'Updated Packages: %s' % (repo_cp_dict,), "debug", config_id, 'sync.git_sync_main')
	return repo_cp_dict

def git_pull(session, repo_dir, config_id):
	log_msg = "Git pull"
	write_log(session, log_msg, "info", config_id, 'sync.git_pull')
	repo = git.Repo(repo_dir)
	info_list, repouptodate = git_fetch(repo)
	if not repouptodate:
		git_merge(repo, info_list[0])
	log_msg = "Git pull ... Done"
	write_log(session, log_msg, "info", config_id, 'sync.git_pull')
	return True
