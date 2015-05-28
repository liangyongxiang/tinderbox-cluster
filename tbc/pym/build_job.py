# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import re
import sys
import signal

from portage import _encodings
from portage import _unicode_decode
from portage.versions import cpv_getkey
from portage.dep import check_required_use
from tbc.depclean import do_depclean
from tbc.flags import tbc_use_flags
from tbc.qacheck import check_file_in_manifest
from tbc.main import emerge_main
from tbc.build_log import log_fail_queru
from tbc.actions import load_emerge_config
from tbc.sqlquerys import add_logs, get_packages_to_build, update_buildjobs_status, is_build_job_done

class build_job_action(object):

	def __init__(self, config_id, session):
		self._config_id = config_id
		self._session = session 

	def make_build_list(self, build_dict, settings, portdb):
		cp = build_dict['cp']
		repo = build_dict['repo']
		package = build_dict['package']
		cpv = build_dict['cpv']
		pkgdir = portdb.getRepositoryPath(repo) + "/" + cp
		build_use_flags_list = []
		try:
			ebuild_version_checksum_tree = portage.checksum.sha256hash(pkgdir + "/" + package + "-" + build_dict['ebuild_version'] + ".ebuild")[0]
		except:
			ebuild_version_checksum_tree = None
		if ebuild_version_checksum_tree == build_dict['checksum']:
			manifest_error = check_file_in_manifest(pkgdir, settings, portdb, cpv, build_use_flags_list, repo)
			if manifest_error is None:
				init_flags = tbc_use_flags(settings, portdb, cpv)
				build_use_flags_list = init_flags.comper_useflags(build_dict)
				log_msg = "build_use_flags_list %s" % (build_use_flags_list,)
				add_logs(self._session, log_msg, "info", self._config_id)
				manifest_error = check_file_in_manifest(pkgdir, settings, portdb, cpv, build_use_flags_list, repo)
			if manifest_error is None:
				build_dict['check_fail'] = False
				build_cpv_dict = {}
				build_cpv_dict[cpv] = build_use_flags_list
				log_msg = "build_cpv_dict: %s" % (build_cpv_dict,)
				add_logs(self._session, log_msg, "info", self._config_id)
				return build_cpv_dict
			build_dict['type_fail'] = "Manifest error"
			build_dict['check_fail'] = True
			log_msg = "Manifest error: %s:%s" % (cpv, manifest_error)
			add_logs(self._session, log_msg, "info", self._config_id)
		else:
			build_dict['type_fail'] = "Wrong ebuild checksum"
			build_dict['check_fail'] = True
		if build_dict['check_fail'] is True:
				log_fail_queru(self._session, build_dict, settings)
		return None

	def build_procces(self, buildqueru_cpv_dict, build_dict, settings, portdb):
		build_cpv_list = []
		depclean_fail = True
		for k, build_use_flags_list in buildqueru_cpv_dict.items():
			build_cpv_list.append("=" + k)
			if not build_use_flags_list == None:
				build_use_flags = ""
				for flags in build_use_flags_list:
					build_use_flags = build_use_flags + flags + " "
				filetext = '=' + k + ' ' + build_use_flags
				log_msg = "filetext: %s" % filetext
				add_logs(self._session, log_msg, "info", self._config_id)
				with open("/etc/portage/package.use/99_autounmask", "a") as f:
     					f.write(filetext)
     					f.write('\n')
     					f.close
		log_msg = "build_cpv_list: %s" % (build_cpv_list,)
		add_logs(self._session, log_msg, "info", self._config_id)

		# We remove the binary package if removebin is true
		if build_dict['removebin']:
			package = build_dict['package']
			pv = package + "-" + build_dict['ebuild_version']
			binfile = settings['PKGDIR'] + "/" + build_dict['category'] + "/" + pv + ".tbz2"
			try:
				os.remove(binfile)
			except:
				log_msg = "Binary file was not removed or found: %s" % (binfile,)
				add_logs(self._session, log_msg, "info", self._config_id)

		argscmd = []
		for emerge_option in build_dict['emerge_options']:
			if emerge_option == '--depclean':
				pass
			elif emerge_option == '--nodepclean':
				pass
			elif emerge_option == '--nooneshot':
				pass
			else:
				if not emerge_option in argscmd:
					argscmd.append(emerge_option)
		for build_cpv in build_cpv_list:
			argscmd.append(build_cpv)
		print("Emerge options: %s" % argscmd)
		log_msg = "argscmd: %s" % (argscmd,)
		add_logs(self._session, log_msg, "info", self._config_id)
		
		# Call main_emerge to build the package in build_cpv_list
		print("Build: %s" % build_dict)
		update_buildjobs_status(self._session, build_dict['build_job_id'], 'Building', self._config_id)
		build_fail = emerge_main(argscmd, build_dict, self._session)
		# Run depclean
		if  '--depclean' in build_dict['emerge_options'] and not '--nodepclean' in build_dict['emerge_options']:
			depclean_fail = do_depclean()
		try:
			os.remove("/etc/portage/package.use/99_autounmask")
			with open("/etc/portage/package.use/99_autounmask", "a") as f:
				f.close
		except:
			pass

		if is_build_job_done(self._session, build_dict['build_job_id']):
			update_buildjobs_status(self._session, build_dict['build_job_id'], 'Looked', self._config_id)
			log_msg = "build_job %s was not removed" % (build_dict['build_job_id'],)
			add_logs(self._session, log_msg, "info", self._config_id)
			print("qurery was not removed")
			build_dict['type_fail'] = "Querey was not removed"
			build_dict['check_fail'] = True
			log_fail_queru(self._session, build_dict, settings)
		if build_fail is True:
			build_dict['type_fail'] = "Emerge faild"
			build_dict['check_fail'] = True
			log_msg = "Emerge faild!"
			add_logs(self._session, log_msg, "info", self._config_id)
			return True
		return False

	def procces_build_jobs(self):
		build_dict = {}
		build_dict = get_packages_to_build(self._session, self._config_id)
		if build_dict is None:
			return
		print("build_dict: %s" % (build_dict,))
		log_msg = "build_dict: %s" % (build_dict,)
		add_logs(self._session, log_msg, "info", self._config_id)
		if not build_dict['ebuild_id'] is None and build_dict['checksum'] is not None:
			settings, trees, mtimedb = load_emerge_config()
			portdb = trees[settings["ROOT"]]["porttree"].dbapi
			buildqueru_cpv_dict = self.make_build_list(build_dict, settings, portdb)
			log_msg = "buildqueru_cpv_dict: %s" % (buildqueru_cpv_dict,)
			add_logs(self._session, log_msg, "info", self._config_id)
			if buildqueru_cpv_dict is None:
				return
			fail_build_procces = self.build_procces(buildqueru_cpv_dict, build_dict, settings, portdb)
			return
		if not build_dict['emerge_options'] is [] and build_dict['ebuild_id'] is None:
			return
		if not build_dict['ebuild_id'] is None and build_dict['emerge_options'] is None:
			pass
			# del_old_queue(self._session, build_dict['queue_id'])
