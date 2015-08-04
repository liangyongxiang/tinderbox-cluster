# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import sys
import os

# Get the options from the config file set in tbc.readconf
from tbc.readconf import get_conf_settings
reader=get_conf_settings()
tbc_settings_dict=reader.read_tbc_settings_all()
config_profile = tbc_settings_dict['tbc_config']

from tbc.check_setup import check_make_conf
from tbc.sync import git_pull
from tbc.package import tbc_package
import portage
import multiprocessing

def add_cpv_query_pool(mysettings, myportdb, config_id, cp, repo):
	conn =0
	init_package = tbc_package(mysettings, myportdb)
	# FIXME: remove the check for tbc when in tree
	if cp != "dev-python/tbc":
		build_dict = {}
		packageDict = {}
		ebuild_id_list = []
		# split the cp to categories and package
		element = cp.split('/')
		categories = element[0]
		package = element[1]
		log_msg = "C %s:%s" % (cp, repo,)
		add_tbc_logs(conn, log_msg, "info", config_id)
		pkgdir = self._myportdb.getRepositoryPath(repo) + "/" + cp
		config_id_list = []
		config_id_list.append(config_id)
		config_cpv_listDict = init_package.config_match_ebuild(cp, config_id_list)
		if config_cpv_listDict != {}:
			cpv = config_cpv_listDict[config_id]['cpv']
			packageDict[cpv] = init_package.get_packageDict(pkgdir, cpv, repo)
			build_dict['checksum'] = packageDict[cpv]['ebuild_version_checksum_tree']
			build_dict['package_id'] = get_package_id(conn, categories, package, repo)
			build_dict['ebuild_version'] = packageDict[cpv]['ebuild_version_tree']
			ebuild_id = get_ebuild_id_db_checksum(conn, build_dict)
			if ebuild_id is not None:
				ebuild_id_list.append(ebuild_id)
				init_package.add_new_ebuild_buildquery_db(ebuild_id_list, packageDict, config_cpv_listDict)
		log_msg = "C %s:%s ... Done." % (cp, repo,)
		add_tbc_logs(conn, log_msg, "info", config_id)
	return

def add_buildquery_main(config_id):
	conn = 0
	config_setup = get_config(conn, config_id)
	log_msg = "Adding build jobs for: %s" % (config_setup,)
	add_tbc_logs(conn, log_msg, "info", config_id)
	check_make_conf()
	log_msg = "Check configs done"
	add_tbc_logs(conn, log_msg, "info", config_profile)
	# Get default config from the configs table  and default_config=1
	default_config_root = "/var/cache/tbc/" + tbc_settings_dict['tbc_gitreponame'] + "/" + config_setup + "/"
	# Set config_root (PORTAGE_CONFIGROOT)  to default_config_root
	mysettings = portage.config(config_root = default_config_root)
	myportdb = portage.portdbapi(mysettings=mysettings)
	init_package = tbc_package(mysettings, myportdb)
	log_msg = "Setting default config to: %s" % (config_setup)
	add_tbc_logs(conn, log_msg, "info", config_is)
	# Use all exept 2 cores when multiprocessing
	pool_cores= multiprocessing.cpu_count()
	if pool_cores >= 3:
		use_pool_cores = pool_cores - 2
	else:
		use_pool_cores = 1
	pool = multiprocessing.Pool(processes=use_pool_cores)

	repo_trees_list = myportdb.porttrees
	for repo_dir in repo_trees_list:
		repo = myportdb.getRepositoryName(repo_dir)
		repo_dir_list = []
		repo_dir_list.append(repo_dir)
		
		# Get the package list from the repo
		package_list_tree = myportdb.cp_all(trees=repo_dir_list)
		for cp in sorted(package_list_tree):
			pool.apply_async(add_cpv_query_pool, (mysettings, myportdb, config_id, cp, repo,))
	pool.close()
	pool.join()
	log_msg = "Adding build jobs for: %s ... Done." % (config_setup,)
	add_tbc_logs(conn, log_msg, "info", config_profile)
	return True

def del_buildquery_main(config_id):
	conn=0
	config_setup = get_config(conn, config_id)
	log_msg = "Removeing build jobs for: %s" % (config_setup,)
	add_tbc_logs(conn, log_msg, "info", config_id)
	build_job_id_list = get_build_jobs_id_list_config(conn, config_id)
	if build_job_id_list is not None:
		for build_job_id in build_job_id_list:
			del_old_build_jobs(conn, build_job_id)
	log_msg = "Removeing build jobs for: %s ... Done." % (config_setup,)
	add_tbc_logs(conn, log_msg, "info", config_id)
	return True
