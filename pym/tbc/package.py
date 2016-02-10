# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import re
import hashlib
import os
import git
import portage
import datetime
from portage.xml.metadata import MetaDataXML
from tbc.flags import tbc_use_flags
from tbc.text import get_ebuild_cvs_revision, get_log_text_dict
from tbc.flags import tbc_use_flags
from tbc.qachecks import check_repoman
from tbc.build_log import check_repoman_full
from tbc.log import write_log
from tbc.sqlquerys import get_package_info, get_config_info, \
	add_new_build_job, add_new_ebuild_sql, get_ebuild_id_list, add_old_ebuild, \
	get_package_metadata_sql, update_package_metadata, \
	get_package_info_from_package_id, get_config_all_info, add_new_package_sql, \
	get_ebuild_checksums, get_ebuild_id_db, get_configmetadata_info, get_setup_info, \
	get_ebuild_info_ebuild_id, get_ebuild_restrictions, add_old_package

class tbc_package(object):

	def __init__(self, session, mysettings, myportdb, config_id):
		self._session = session
		self._mysettings = mysettings
		self._myportdb = myportdb
		self._config_id = config_id

	def change_config(self, host_config, repopath):
		# Change config_root  config_setup = table config
		my_new_setup = repopath + "/" + host_config + "/"
		mysettings_setup = portage.config(config_root = my_new_setup)
		return mysettings_setup

	def config_match_ebuild(self, cp, config_list, repopath):
		config_cpv_dict ={}
		if config_list == []:
			return config_cpv_dict
		for config_id in config_list:
			ConfigInfo = get_config_info(self._session, config_id)
			ConfigsMetaData = get_configmetadata_info(self._session, config_id)
			if ConfigsMetaData.Auto and ConfigsMetaData.Active and ConfigsMetaData.Status != 'Stopped' and not ConfigInfo.SetupId in config_cpv_dict:
				SetupInfo = get_setup_info(self._session, config_id)
				mysettings_setup = self.change_config(ConfigInfo.Hostname + "/" + SetupInfo.Setup, repopath)
				myportdb_setup = portage.portdbapi(mysettings=mysettings_setup)

				# Get the latest cpv from portage with the config that we can build
				build_cpv = myportdb_setup.xmatch('bestmatch-visible', cp)

				# Check if could get cpv from portage and add it to the config_cpv_listDict.
				if build_cpv != "":

					# Get the iuse and use flags for that config/setup and cpv
					init_useflags = tbc_use_flags(mysettings_setup, myportdb_setup, build_cpv)
					iuse_flags_list, final_use_list = init_useflags.get_flags()
					iuse_flags_list2 = []
					for iuse_line in iuse_flags_list:
						iuse_flags_list2.append( init_useflags.reduce_flag(iuse_line))

					# Dict the needed info
					attDict = {}
					attDict['cpv'] = build_cpv
					attDict['useflags'] = final_use_list
					attDict['iuse'] = iuse_flags_list2
					config_cpv_dict[ConfigInfo.SetupId] = attDict

				# Clean some cache
				myportdb_setup.close_caches()
				portage.portdbapi.portdbapi_instances.remove(myportdb_setup)
		return config_cpv_dict

	def get_ebuild_metadata(self, cpv, repo):
		# Get the auxdbkeys infos for the ebuild
		try:
			ebuild_auxdb_list = self._myportdb.aux_get(cpv, portage.auxdbkeys, myrepo=repo)
		except:
			ebuild_auxdb_list = False
		else:
			for i in range(len(ebuild_auxdb_list)):
				if ebuild_auxdb_list[i] == '':
					ebuild_auxdb_list[i] = ''
			return ebuild_auxdb_list

	def get_git_log_ebuild(self, repodir, ebuild_file):
		git_log_ebuild = ''
		g = git.Git(repodir)
		for line in g.log('-n 1', ebuild_file).splitlines():
			if re.search('^commit', line):
				git_log_ebuild = re.sub('commit', '', line)
		return git_log_ebuild

	def get_packageDict(self, pkgdir, cpv, repo):

		#Get categories, package and version from cpv
		ebuild_version_tree = portage.versions.cpv_getversion(cpv)
		element = portage.versions.cpv_getkey(cpv).split('/')
		categories = element[0]
		package = element[1]
		ebuild_file = pkgdir + "/" + package + "-" + ebuild_version_tree + ".ebuild"
		# Make a checksum of the ebuild
		try:
			ebuild_version_checksum_tree = portage.checksum.sha256hash(ebuild_file)[0]
		except:
			ebuild_version_checksum_tree = "0"
			log_msg = "QA: Can't checksum the ebuild file. %s on repo %s" % (cpv, repo,)
			write_log(self._session, log_msg, "warning", self._config_id, 'packages.get_packageDict')
			log_msg = "C %s:%s ... Fail." % (cpv, repo)
			write_log(self._session, log_msg, "info", self._config_id, 'packages.get_packageDict')
			git_commit = '0'
		else:
			repodir =self._myportdb.getRepositoryPath(repo)
			git_commit = self.get_git_log_ebuild(repodir, ebuild_file)

		# Get the ebuild metadata
		ebuild_version_metadata_tree = self.get_ebuild_metadata(cpv, repo)
		# if there some error to get the metadata we add rubish to the
		# ebuild_version_metadata_tree and set ebuild_version_checksum_tree to 0
		# so it can be updated next time we update the db
		if not ebuild_version_metadata_tree:
			log_msg = " QA: %s have broken metadata on repo %s" % (cpv, repo)
			write_log(self._session, log_msg, "warning", self._config_id, 'packages.get_packageDict')
			ebuild_version_metadata_tree = ['','','','','','','','','','','','','','','','','','','','','','','','','']
			ebuild_version_checksum_tree = '0'

		# add the ebuild info to the dict packages
		PackageInfo = get_package_info(self._session, categories, package, repo)
		attDict = {}
		attDict['package_id'] = PackageInfo.PackageId
		attDict['repo'] = repo
		attDict['ebuild_version'] = ebuild_version_tree
		attDict['checksum']= ebuild_version_checksum_tree
		attDict['ebuild_version_metadata_tree'] = ebuild_version_metadata_tree
		#attDict['ebuild_version_text_tree'] = ebuild_version_text_tree[0]
		attDict['git_commit'] = git_commit
		attDict['new'] = False
		attDict['ebuild_version_descriptions_tree'] = ebuild_version_metadata_tree[7]
		return attDict

	def add_new_build_job_db(self, ebuild_id_list, packageDict, config_cpv_listDict):
		# Get the needed info from packageDict and config_cpv_listDict and put that in buildqueue
		# Only add it if ebuild_version in packageDict and config_cpv_listDict match
		if config_cpv_listDict is not None:
			# Unpack config_cpv_listDict
			for setup_id, v in config_cpv_listDict.items():
				build_cpv = v['cpv']
				iuse_flags_list = list(set(v['iuse']))
				use_enable= v['useflags']
				use_disable = list(set(iuse_flags_list).difference(set(use_enable)))
				# Make a dict with enable and disable use flags for ebuildqueuedwithuses
				use_flagsDict = {}
				for x in use_enable:
					use_flagsDict[x] = True
				for x in use_disable:
					use_flagsDict[x] = False
				# Unpack packageDict
				i = 0
				for k, v in packageDict.items():
					ebuild_id = ebuild_id_list[i]

					# Comper and add the cpv to buildqueue
					if build_cpv == k:
						restrictions_dict = get_ebuild_restrictions(self._session, ebuild_id)
						if restrictions_dict:
							if "test" in restrictions_dict and "test" in use_flagsDict:
								use_flagsDict['test'] = False
						add_new_build_job(self._session, ebuild_id, setup_id, use_flagsDict, self._config_id)
						# B = Build cpv use-flags config
						# FIXME log_msg need a fix to log the use flags corect.
						log_msg = "B %s:%s USE: %s Setup: %s" % (k, v['repo'], use_flagsDict, setup_id,)
						write_log(self._session, log_msg, "info", self._config_id, 'packages.add_new_build_job_db')
					i = i +1

	def get_git_changelog_text(self, repodir, cp):
		n = '5'
		git_log_pkg = ''
		g = git.Git(repodir)
		git_log_pkg = g.log('-n ' + n, '--grep=' + cp)
		return git_log_pkg

	def get_package_metadataDict(self, pkgdir, repodir, package_id, cp):
		# Make package_metadataDict
		attDict = {}
		package_metadataDict = {}
		md_email_list = []
		herd = None
		attDict['metadata_xml_email'] = False
		try:
			pkg_md = MetaDataXML(pkgdir + "/metadata.xml", herd)
		except:
			log_msg = "Metadata file %s is missing or has errors" % (pkgdir + "/metadata.xml")
			write_log(self._session, log_msg, "warning", self._config_id, 'packages.get_package_metadataDict')
		else:
			tmp_herds = pkg_md.herds()
			if tmp_herds != ():
				attDict['metadata_xml_herds'] = tmp_herds[0]
				md_email_list.append(attDict['metadata_xml_herds'] + '@gentoo.org')
			for maint in pkg_md.maintainers():
				md_email_list.append(maint.email)
			if md_email_list != []:
				attDict['metadata_xml_email'] = md_email_list
			else:
				log_msg = "Metadata file %s missing Email" % (pkgdir + "/metadata.xml")
				write_log(self._session, log_msg, "warning", self._config_id, 'packages.get_package_metadataDict')
		attDict['git_changlog'] = self.get_git_changelog_text(repodir, cp)
		attDict['metadata_xml_descriptions'] = ''
		package_metadataDict[package_id] = attDict
		return package_metadataDict

	def add_package(self, packageDict, package_metadataDict, package_id, new_ebuild_id_list, old_ebuild_id_list):
		# Use packageDict to update the db
		ebuild_id_list = add_new_ebuild_sql(self._session, packageDict)

		# Make old ebuilds unactive
		for ebuild_id in ebuild_id_list:
			new_ebuild_id_list.append(ebuild_id)
		for ebuild_id in get_ebuild_id_list(self._session, package_id):
			if not ebuild_id in new_ebuild_id_list:
				if not ebuild_id in old_ebuild_id_list:
					old_ebuild_id_list.append(ebuild_id)
		if not old_ebuild_id_list == []:
			add_old_ebuild(self._session, old_ebuild_id_list)

		# update package metadata
		update_package_metadata(self._session, package_metadataDict)

		# Get the best cpv for the configs and add it to config_cpv_listDict
		PackageInfo, CategoryInfo, RepoInfo = get_package_info_from_package_id(self._session, package_id)
		cp = CategoryInfo.Category + '/' + PackageInfo.Package
		config_all_info  = get_config_all_info(self._session)
		config_list = []
		for config in get_config_all_info(self._session):
			if config.Host is False:
				config_list.append(config.ConfigId)
		ConfigsMetaData = get_configmetadata_info(self._session, self._config_id)
		config_cpv_listDict = self.config_match_ebuild(cp, config_list, ConfigsMetaData.RepoPath)

		# Add the ebuild to the build jobs table if needed
		self.add_new_build_job_db(ebuild_id_list, packageDict, config_cpv_listDict)

	def add_new_package_db(self, cp, repo):
		# Add new categories package ebuild to tables package and ebuilds
		# C = Checking
		# N = New Package
		log_msg = "C %s:%s" % (cp, repo)
		write_log(self._session, log_msg, "info", self._config_id, 'packages.add_new_package_db')
		log_msg = "N %s:%s" % (cp, repo)
		write_log(self._session, log_msg, "info", self._config_id, 'packages.add_new_package_db')
		repodir = self._myportdb.getRepositoryPath(repo)
		mytree = []
		mytree.append(repodir)
		pkgdir = repodir + "/" + cp # Get RepoDIR + cp
		
		package_id = add_new_package_sql(self._session, cp, repo)

		# Check cp with repoman full
		status = check_repoman_full(self._session, pkgdir, package_id, self._config_id)
		if status:
			log_msg = "Repoman %s::%s ... Fail." % (cp, repo)
			write_log(self._session, log_msg, "warning", self._config_id, 'packages.add_new_package_db')

		package_metadataDict = self.get_package_metadataDict(pkgdir, repodir, package_id, cp)
		# Get the ebuild list for cp
		ebuild_list_tree = self._myportdb.cp_list(cp, use_cache=1, mytree=mytree)
		if ebuild_list_tree == []:
			log_msg = "QA: Can't get the ebuilds list. %s:%s" % (cp, repo,)
			write_log(self._session, log_msg, "error", self._config_id, 'packages.add_new_package_db')
			log_msg = "C %s:%s ... Fail." % (cp, repo)
			write_log(self._session, log_msg, "warning", self._config_id, 'packages.add_new_package_db')
			return None

		# Make the needed packageDict with ebuild infos so we can add it later to the db.
		packageDict ={}
		new_ebuild_id_list = []
		old_ebuild_id_list = []
		for cpv in sorted(ebuild_list_tree):
			packageDict[cpv] = self.get_packageDict(pkgdir, cpv, repo)

			# take package descriptions from the ebuilds
			if package_metadataDict[package_id]['metadata_xml_descriptions'] != packageDict[cpv]['ebuild_version_descriptions_tree']:
				package_metadataDict[package_id]['metadata_xml_descriptions'] = packageDict[cpv]['ebuild_version_descriptions_tree']

		packageDict[cpv]['new'] = True
		self.add_package(packageDict, package_metadataDict, package_id, new_ebuild_id_list, old_ebuild_id_list)
		log_msg = "C %s:%s ... Done." % (cp, repo)
		write_log(self._session, log_msg, "info", self._config_id, 'packages.add_new_package_db')

	def update_package_db(self, package_id):
		# Update the categories and package with new info
		# C = Checking
		PackageInfo, CategoryInfo, RepoInfo = get_package_info_from_package_id(self._session, package_id)
		cp = CategoryInfo.Category + '/' + PackageInfo.Package
		repo = RepoInfo.Repo
		log_msg = "C %s:%s" % (cp, repo)
		write_log(self._session, log_msg, "info", self._config_id, 'packages.update_package_db')
		repodir = self._myportdb.getRepositoryPath(repo)
		pkgdir = repodir + "/" + cp # Get RepoDIR + cp
		if not os.path.isdir(pkgdir):
			old_ebuild_id_list = get_ebuild_id_list(self._session, package_id)
			for ebuild_id in old_ebuild_id_list:
				EbuildInfo = get_ebuild_info_ebuild_id(self._session, ebuild_id)
				cpv = cp + "-" + EbuildInfo.Version
				# R =  remove ebuild
				log_msg = "R %s:%s" % (cpv, repo,)
				write_log(self._session, log_msg, "info", self._config_id, 'packages.update_package_db')
			add_old_ebuild(self._session, old_ebuild_id_list)
			add_old_package(self._session, package_id)
			log_msg = "C %s:%s ... Done." % (cp, repo)
			write_log(self._session, log_msg, "info", self._config_id, 'packages.update_package_db')
			return None
		
		mytree = []
		mytree.append(repodir)

		# Get the ebuild list for cp
		old_ebuild_id_list = []
		ebuild_list_tree = self._myportdb.cp_list(cp, use_cache=1, mytree=mytree)
		if ebuild_list_tree == []:
			log_msg = "QA: Can't get the ebuilds list. %s:%s" % (cp, repo,)
			write_log(self._session, log_msg, "error", self._config_id, 'packages.update_package_db')
			log_msg = "C %s:%s ... Fail." % (cp, repo)
			write_log(self._session, log_msg, "warning", self._config_id, 'packages.update_package_db')
			return None

		package_metadataDict = self.get_package_metadataDict(pkgdir, repodir, package_id, cp)
		packageDict ={}
		new_ebuild_id_list = []
		package_updated = False
		for cpv in sorted(ebuild_list_tree):

			# split out ebuild version
			ebuild_version_tree = portage.versions.cpv_getversion(cpv)

			# Get packageDict for cpv
			packageDict[cpv] = self.get_packageDict(pkgdir, cpv, repo)

			# take package descriptions from the ebuilds
			if package_metadataDict[package_id]['metadata_xml_descriptions'] != packageDict[cpv]['ebuild_version_descriptions_tree']:
				package_metadataDict[package_id]['metadata_xml_descriptions'] = packageDict[cpv]['ebuild_version_descriptions_tree']

			# Get the checksum of the ebuild in tree and db
			ebuild_version_checksum_tree = packageDict[cpv]['checksum']
			checksums_db, fail = get_ebuild_checksums(self._session, package_id, ebuild_version_tree)

			# check if we have dupes of the checksum from db
			if checksums_db is None:
				ebuild_version_manifest_checksum_db = None
			elif fail:
				dupe_ebuild_id_list = []
				for checksum in checksums_db:
					ebuilds_id , status = get_ebuild_id_db(self._session, checksum, package_id, ebuild_version_tree)
					for ebuild_id in ebuilds_id:
						log_msg = "U %s:%s:%s Dups of checksums" % (cpv, repo, ebuild_id,)
						write_log(self._session, log_msg, "warning", self._config_id, 'packages.update_package_db')
						dupe_ebuild_id_list.append(ebuild_id)
				add_old_ebuild(self._session, dupe_ebuild_id_list)
				ebuild_version_manifest_checksum_db = None
			else:
				ebuild_version_manifest_checksum_db = checksums_db

			# Check if the checksum have change
			if ebuild_version_manifest_checksum_db is None:
				# N = New ebuild
				log_msg = "N %s:%s" % (cpv, repo,)
				write_log(self._session, log_msg, "info", self._config_id, 'packages.update_package_db')
				packageDict[cpv]['new'] = True
				package_updated = True
			elif  ebuild_version_checksum_tree != ebuild_version_manifest_checksum_db:
				# U = Updated ebuild
				log_msg = "U %s:%s" % (cpv, repo,)
				write_log(self._session, log_msg, "info", self._config_id, 'packages.update_package_db')
				package_updated = True
			else:
				# Remove cpv from packageDict and add ebuild to new ebuils list
				del packageDict[cpv]
				ebuild_id , status = get_ebuild_id_db(self._session, ebuild_version_checksum_tree, package_id, ebuild_version_tree)
				new_ebuild_id_list.append(ebuild_id)
		self.add_package(packageDict, package_metadataDict, package_id, new_ebuild_id_list, old_ebuild_id_list)

		if package_updated:
			# Check cp with repoman full
			status = check_repoman_full(self._session, pkgdir, package_id, self._config_id)
			if status:
				log_msg = "Repoman %s::%s ... Fail." % (cp, repo)
				write_log(self._session, log_msg, "warning", self._config_id, 'packages.update_package_db')

		log_msg = "C %s:%s ... Done." % (cp, repo)
		write_log(self._session, log_msg, "info", self._config_id, 'packages.update_package_db')
