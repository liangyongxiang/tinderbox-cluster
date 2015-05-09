# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import errno
import sys
import time
from pygit2 import Repository, GIT_MERGE_ANALYSIS_FASTFORWARD, GIT_MERGE_ANALYSIS_NORMAL, \
        GIT_MERGE_ANALYSIS_UP_TO_DATE

from _emerge.main import emerge_main
from tbc.sqlquerys import get_config_id, add_tbc_logs, get_config_all_info, get_configmetadata_info
from tbc.updatedb import update_db_main
from tbc.readconf import read_config_settings

def sync_tree(session):
	tbc_settings_dict = read_config_settings()
	_hostname = tbc_settings_dict['hostname']
	_config = tbc_settings_dict['tbc_config']
	config_id = get_config_id(session, _config, _hostname)
	host_config = _hostname +"/" + _config
	default_config_root = tbc_settings_dict['tbc_gitrepopath']  + "/" + host_config + "/"
	mysettings = portage.config(config_root = default_config_root)
	GuestBusy = True
	log_msg = "Waiting for Guest to be idel"
	add_tbc_logs(session, log_msg, "info", config_id)
	guestid_list = []
	for config in get_config_all_info(session):
		if not config.Host:
			guestid_list.append(config.ConfigId)
	while GuestBusy:
		Status_list = []
		for guest_id in guestid_list:
			ConfigMetadata = get_configmetadata_info(session, guest_id)
			Status_list.append(ConfigMetadata.Status)
		if not 'Runing' in Status_list:
			GuestBusy = False
		time.sleep(30)
	try:
		os.remove(mysettings['PORTDIR'] + "/profiles/config/parent")
		os.rmdir(mysettings['PORTDIR'] + "/profiles/config")
	except:
		pass
	tmpcmdline = []
	tmpcmdline.append("--sync")
	tmpcmdline.append("--quiet")
	tmpcmdline.append("--config-root=" + default_config_root)
	log_msg = "Emerge --sync"
	add_tbc_logs(session, log_msg, "info", config_id)
	fail_sync = emerge_main(args=tmpcmdline)
	if fail_sync:
		log_msg = "Emerge --sync fail!"
		add_tbc_logs(session, log_msg, "error", config_id)
		return False
	else:
		# Need to add a config dir so we can use profiles/base for reading the tree.
		# We may allready have the dir on local repo when we sync.
		try:
			os.mkdir(mysettings['PORTDIR'] + "/profiles/config", 0o777)
			with open(mysettings['PORTDIR'] + "/profiles/config/parent", "w") as f:
				f.write("../base\n")
				f.close()
		except:
			pass
		log_msg = "Emerge --sync ... Done."
		add_tbc_logs(session, log_msg, "info", config_id)
	return True

def git_pull(session, git_repo, config_id):
	log_msg = "Git pull"
	add_zobcs_logs(session, log_msg, "info", config_id)
	repo = Repository(git_repo + ".git")
	remote = repo.remotes["origin"]
	remote.fetch()
	remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
	merge_result, _ = repo.merge_analysis(remote_master_id)
	if merge_result & GIT_MERGE_ANALYSIS_UP_TO_DATE:
		log_msg = "Repo is up to date"
		add_zobcs_logs(session, log_msg, "info", config_id)
	elif merge_result & GIT_MERGE_ANALYSIS_FASTFORWARD:
		repo.checkout_tree(repo.get(remote_master_id))
		master_ref = repo.lookup_reference('refs/heads/master')
		master_ref.set_target(remote_master_id)
		repo.head.set_target(remote_master_id)
	elif merge_result & GIT_MERGE_ANALYSIS_NORMAL:
		repo.merge(remote_master_id)
		assert repo.index.conflicts is None, 'Conflicts, ahhhh!'
		user = repo.default_signature
		tree = repo.index.write_tree()
		commit = repo.create_commit('HEAD',
			user,
			user,
			'Merge!',
			tree,
			[repo.head.target, remote_master_id])
		repo.state_cleanup()
	else:
		raise AssertionError('Unknown merge analysis result')
	log_msg = "Git pull ... Done"
	add_zobcs_logs(session, log_msg, "info", config_id)
	return True
