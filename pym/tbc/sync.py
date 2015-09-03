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
	add_logs(session, log_msg, "info", config_id)
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

	# check git diffs witch Manifests get updated and pass that to a dict
	# fetch and merge the repo
	repo_cp_dict = {}
	for repo_dir in git_repos_list(myportdb):
		reponame = myportdb.getRepositoryName(repo_dir)
		repo = git.Repo(repo_dir)
		log_msg = "Checking repo %s" % (reponame)
		add_logs(session, log_msg, "info", config_id)
		info_list, repouptodate = git_fetch(repo)
		if not repouptodate:
			cp_list = []
			attr = {}
			# We check for Manifest changes and add the package to a list
			for diff_line in repo.git.diff('origin', '--name-only').splitlines():
				if re.search("Manifest$", diff_line):
						cp = re.sub('/Manifest', '', diff_line)
						cp_list.append(cp)
			attr['cp_list'] = cp_list
			repo_cp_dict[reponame] = attr
			git_merge(repo, info_list[0])
		else:
			log_msg = "Repo %s is up to date" % (reponame)
			add_logs(session, log_msg, "info", config_id)
		log_msg = "Checking repo %s Done" % (reponame)
		add_logs(session, log_msg, "info", config_id)
	# Need to add a clone of profiles/base for reading the tree
	try:
		os.mkdir(mysettings['PORTDIR'] + "/profiles/config", 0o777)
		with open(mysettings['PORTDIR'] + "/profiles/config/parent", "w") as f:
			f.write("../base\n")
			f.close()
	except:
		pass

	log_msg = "Repo sync ... Done."
	add_logs(session, log_msg, "info", config_id)
	return repo_cp_dict

def git_pull(session, repo_dir, config_id):
	log_msg = "Git pull"
	add_logs(session, log_msg, "info", config_id)
	repo = git.Repo(repo_dir)
	info_list, repouptodate = git_fetch(repo)
	if not repouptodate:
		git_merge(repo, info_list[0])
	log_msg = "Git pull ... Done"
	add_logs(session, log_msg, "info", config_id)
	return True
