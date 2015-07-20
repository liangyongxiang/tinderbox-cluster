# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import sys
import os
import multiprocessing
import time
import portage
from portage.xml.metadata import MetaDataXML
from sqlalchemy.orm import scoped_session, sessionmaker
from tbc.ConnectionManager import NewConnection
from tbc.sqlquerys import add_logs, get_package_info, update_repo_db, \
	update_categories_db, get_configmetadata_info, get_config_all_info, add_new_build_job, \
	get_config_info, get_setup_info
from tbc.check_setup import check_make_conf
from tbc.package import tbc_package
# Get the options from the config file tbc.conf
from tbc.readconf import  read_config_settings

def init_portage_settings(session, config_id):
	# check config setup
	check_make_conf(session, config_id)
	log_msg = "Check configs done"
	add_logs(session, log_msg, "info", config_id)

	# setup default root
	ConfigsMetaDataInfo = get_configmetadata_info(session, config_id)
	ConfigInfo = get_config_info(session, config_id)
	SetupInfo = get_setup_info(session, ConfigInfo.SetupId)
	host_config = ConfigInfo.Hostname +"/" + SetupInfo.Setup
	default_config_root = ConfigsMetaDataInfo.RepoPath + "/" + host_config + "/"

	# Set config_root (PORTAGE_CONFIGROOT)  to default_config_root
	mysettings = portage.config(config_root = default_config_root)
	log_msg = "Setting default config to: %s" % (host_config,)
	add_logs(session, log_msg, "info", config_id)
	return mysettings

def get_categories_metadataDict(pkgdir):
		# Make categories_metadataDict
		categories_metadataDict = {}
		pkg_md = MetaDataXML(pkgdir + "/metadata.xml", None)
		metadata_xml_descriptions_tree = re.sub('\t', '', pkg_md.descriptions()[0])
        categories_metadataDict['metadata_xml_descriptions'] = re.sub('\n', '', metadata_xml_descriptions_tree)
		categories_metadataDict['metadata_xml_checksum'] =  portage.checksum.sha256hash(pkgdir + "/metadata.xml")[0]
		return categories_metadataDict

def update_cpv_db_pool(mysettings, myportdb, cp, repo, tbc_settings, config_id):
	session_factory = sessionmaker(bind=NewConnection(tbc_settings))
	Session = scoped_session(session_factory)
	session2 = Session()
	init_package = tbc_package(session2, mysettings, myportdb, config_id)

	# split the cp to categories and package
	element = cp.split('/')
	categories = element[0]
	package = element[1]

	# update the categories table
	repodir = self._myportdb.getRepositoryPath('gentoo')
	pkgdir = repodir + "/" + categories
	categories_metadataDict = get_categories_metadataDict(pkgdir)
	update_categories_db(session2, categories, categories_metadataDict)

	# Check if we have the cp in the package table
	PackagesInfo = get_package_info(session2, categories, package, repo)
	if PackagesInfo:  
		# Update the packages with ebuilds
		init_package.update_package_db(PackagesInfo.PackageId)
	else:
		# Add new package with ebuilds
		init_package.add_new_package_db(cp, repo)
	session2.close
	Session.remove()

def update_cpv_db(session, repo_cp_dict, config_id, tbc_settings):
	GuestBusy = True
	log_msg = "Waiting for Guest to be idel"
	add_logs(session, log_msg, "info", config_id)
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
			break
		time.sleep(30)

	log_msg = "Checking categories, package, ebuilds"
	add_logs(session, log_msg, "info", config_id)
	new_build_jobs_list = []

	# Setup settings, portdb and pool
	mysettings =  init_portage_settings(session, config_id)
	myportdb = portage.portdbapi(mysettings=mysettings)
	
	# Use all cores when multiprocessing
	pool_cores = multiprocessing.cpu_count()
	pool = multiprocessing.Pool(processes = pool_cores)

	# Get packages and repo
	if repo_cp_dict is None:
		repo_list = []
		repos_trees_list = []

		# Get the repos and update the repos db
		repo_list = myportdb.getRepositories()
		update_repo_db(session, repo_list)

		# Get the rootdirs for the repos
		repo_trees_list = myportdb.porttrees
		for repo_dir in repo_trees_list:
			repo = myportdb.getRepositoryName(repo_dir)
			repo_dir_list = []
			repo_dir_list.append(repo_dir)

			# Get the package list from the repo
			package_list_tree = myportdb.cp_all(trees=repo_dir_list)

			# Run the update package for all package in the list and in a multiprocessing pool
			for cp in sorted(package_list_tree):
				# pool.apply_async(update_cpv_db_pool, (mysettings, myportdb, cp, repo, tbc_settings, config_id,))
				# use this when debuging
				update_cpv_db_pool(mysettings, myportdb, cp, repo, tbc_settings, config_id)
	else:
		# Update needed repos and packages in the dict
		for repo, v in repo_cp_dict.items():
			# Get the repos and update the repos db
			repo_list = []
			repo_list.append(repo)
			update_repo_db(session, repo_list)

			# Run the update package for all package in the list and in a multiprocessing pool
			for cp in v['cp_list']:
				# pool.apply_async(update_cpv_db_pool, (mysettings, myportdb, cp, repo, tbc_settings, config_id,))
				# use this when debuging
				update_cpv_db_pool(mysettings, myportdb, cp, repo, tbc_settings, config_id)


	#close and join the multiprocessing pools
	# pool.close()
	# pool.join()
	log_msg = "Checking categories, package and ebuilds ... done"
	add_logs(session, log_msg, "info", config_id)

def update_db_main(session, repo_cp_dict, config_id):
	# Main
	if repo_cp_dict == {}:
		return True
	# Logging
	tbc_settings = read_config_settings()
	log_msg = "Update db started."
	add_logs(session, log_msg, "info", config_id)

	# Update the cpv db
	update_cpv_db(session, repo_cp_dict, config_id, tbc_settings)
	log_msg = "Update db ... Done."
	add_logs(session, log_msg, "info", config_id)
	return True
