# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import errno

from portage.exception import DigestException, FileNotFound, ParseError, PermissionDenied
from tbc.text import get_file_text
from tbc.sqlquerys import get_config_all_info, add_logs, get_configmetadata_info, get_setup_info
from tbc.sync import git_pull

def check_make_conf(session, config_id):
	log_msg = "Checking configs for changes and errors"
	add_logs(session, log_msg, "info", config_id)
	HostConfigsMetaDataInfo = get_configmetadata_info(session, config_id)
	git_repo =  HostConfigsMetaDataInfo.RepoPath + "/"
	git_pull(session, git_repo, config_id)
	configsDict = {}
	for ConfigInfo in get_config_all_info(session):
		attDict={}
		# Set the config dir
		SetupInfo = get_setup_info(session, ConfigInfo.ConfigId)
		check_config_dir = git_repo + ConfigInfo.Hostname +"/" + SetupInfo.Setup + "/"
		make_conf_file = check_config_dir + "etc/portage/make.conf"
		ConfigsMetaDataInfo = get_configmetadata_info(session, ConfigInfo.ConfigId)
		# Check if we can take a checksum on it.
		# Check if we have some error in the file. (portage.util.getconfig)
		# Check if we envorment error with the config. (settings.validate)
		try:
			make_conf_checksum_tree = portage.checksum.sha256hash(make_conf_file)[0]
			portage.util.getconfig(make_conf_file, tolerant=0, allow_sourcing=True, expand=True)
			mysettings = portage.config(config_root = check_config_dir)
			mysettings.validate()
			# With errors we update the db on the config and disable the config
		except ParseError as e:
			ConfigsMetaDataInfo.ConfigErrorText = str(e)
			ConfigsMetaDataInfo.Active = False
			log_msg = "%s FAIL!" % (ConfigInfo.Hostname,)
			add_logs(session, log_msg, "info", config_id)
			session.commit()
		else:
			ConfigsMetaDataInfo.Active = True
			log_msg = "%s PASS" % (ConfigInfo.Hostname,)
			add_logs(session, log_msg, "info", config_id)
			session.commit()
		if make_conf_checksum_tree != ConfigsMetaDataInfo.Checksum:
			ConfigsMetaDataInfo.MakeConfText = get_file_text(make_conf_file)
			ConfigsMetaDataInfo.Checksum = make_conf_checksum_tree
			session.commit()
	log_msg = "Checking configs for changes and errors ... Done"
	add_logs(session, log_msg, "info", config_id)

def check_configure_guest(session, config_id):
	GuestConfigsMetaDataInfo = get_configmetadata_info(session, config_id)
	git_repo =  GuestConfigsMetaDataInfo.RepoPath + "/"
	git_pull(session, git_repo, config_id)
	make_conf_file = "/etc/portage/make.conf"
	# Check if we can open the file and close it
	# Check if we have some error in the file (portage.util.getconfig)
	# Check if we envorment error with the config (settings.validate)
	try:
		make_conf_checksum_tree = portage.checksum.sha256hash(make_conf_file)[0]
		portage.util.getconfig(make_conf_file, tolerant=0, allow_sourcing=True, expand=True)
		mysettings = portage.config(config_root = "/")
		mysettings.validate()
		# With errors we return false
	except Exception as e:
		return False
	if make_conf_checksum_tree != GuestConfigsMetaDataInfo.Checksum:
		return False
	return True
