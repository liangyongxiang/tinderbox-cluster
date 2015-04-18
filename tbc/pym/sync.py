# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import errno
import sys
import time

from _emerge.main import emerge_main
from tbc.readconf import get_conf_settings
from tbc.sqlquerys import get_config_id, add_tbc_logs, get_config_all_info, get_configmetadata_info
from tbc.updatedb import update_db_main
from tbc.readconf import read_config_settings

def sync_tree(session):
	tbc_settings_dict = read_config_settings()
	_hostname = tbc_settings_dict['hostname']
	_config = tbc_settings_dict['tbc_config']
	config_id = get_config_id(session, _config, _hostname)
	host_config = _hostname +"/" + _config
	default_config_root = "/var/cache/tbc/" + tbc_settings_dict['tbc_gitreponame'] + "/" + host_config + "/"
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
	result = update_db_main(session, config_id)
	if result:
		return True
	else:
		log_msg = "Updatedb fail"
		add_tbc_logs(session, log_msg, "info", config_id)
