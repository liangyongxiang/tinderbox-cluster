# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import re
import os
import platform
import hashlib
import logging

from portage.versions import catpkgsplit, cpv_getversion
import portage
from portage.util import writemsg, \
	writemsg_level, writemsg_stdout
from portage import _encodings
from portage import _unicode_encode

from _emerge.main import parse_opts

portage.proxy.lazyimport.lazyimport(globals(),
	'tbc.actions:action_info,load_emerge_config',
)
from tbc.irk import send_irk
from tbc.qachecks import check_repoman, repoman_full
from tbc.text import get_log_text_dict
from tbc.readconf import read_config_settings
from tbc.flags import tbc_use_flags
from tbc.ConnectionManager import NewConnection
from tbc.sqlquerys import get_config_id, get_ebuild_id_db, add_new_buildlog, \
	get_package_info, get_build_job_id, get_use_id, get_config_info, get_hilight_info, get_error_info_list, \
	add_e_info, get_fail_times, add_fail_times, update_fail_times, del_old_build_jobs, add_old_ebuild, \
	update_buildjobs_status, add_repoman_qa, get_config_id_fqdn, get_setup_info, \
	add_repoman_log,  get_tbc_config
from tbc.log import write_log

from sqlalchemy.orm import sessionmaker

def check_repoman_full(session, pkgdir, package_id, config_id, cpv=False):
	# Check cp with repoman repoman full
	write_log(session, 'Repoman Check', "info", config_id, 'build_log.check_repoman_full')
	status = repoman_full(session, pkgdir, config_id)
	repoman_hash = hashlib.sha256()
	if cpv:
		ebuild_version_tree = portage.versions.cpv_getversion(cpv)
	if status:
		repoman_dict = {}
		for k, v in status.items():
			repoman_log2 = []
			for line in v:
				if cpv:
					if re.search(ebuild_version_tree, line):
						repoman_log2.append(line)
				else: 
					repoman_log2.append(line)
			if not repoman_log2 == []:
				repoman_dict[k] = repoman_log2
		if not repoman_dict == {}:
			repoman_log = ""
			for k, v in repoman_dict.items():
				repoman_log = repoman_log + k + "\n"
				repoman_hash.update(k.encode('utf-8'))
				for line in v:
					repoman_log = repoman_log + line + "\n"
					repoman_hash.update(line.encode('utf-8'))
			add_repoman_log(session, package_id, repoman_log, repoman_hash.hexdigest())
			write_log(session, 'Repoman Check Fail\n' + repoman_log, "warning", config_id, 'build_log.check_repoman_full')
			return repoman_log
	write_log(session, 'Repoman Check Pass', "info", config_id, 'build_log.check_repoman_full')
	return False

def get_build_dict_db(session, config_id, settings, tbc_settings_dict, pkg):
	myportdb = portage.portdbapi(mysettings=settings)
	cpvr_list = catpkgsplit(pkg.cpv, silent=1)
	categories = cpvr_list[0]
	package = cpvr_list[1]
	repo = pkg.repo
	ebuild_version = cpv_getversion(pkg.cpv)
	log_msg = "Setting up logging for %s:%s" % (pkg.cpv, repo,)
	write_log(session, log_msg, "info", config_id, 'build_log.get_build_dict_db')
	PackageInfo = get_package_info(session, categories, package, repo)
	build_dict = {}
	build_dict['ebuild_version'] = ebuild_version
	build_dict['package_id'] = PackageInfo.PackageId
	build_dict['cpv'] = pkg.cpv
	build_dict['categories'] = categories
	build_dict['package'] = package
	build_dict['repo'] = repo
	build_dict['config_id'] = config_id
	init_useflags = tbc_use_flags(settings, myportdb, pkg.cpv)
	iuse_flags_list, final_use_list = init_useflags.get_flags_pkg(pkg, settings)
	iuse = []
	for iuse_line in iuse_flags_list:
		iuse.append(init_useflags.reduce_flag(iuse_line))
	iuse_flags_list2 = list(set(iuse))
	use_enable = final_use_list
	use_disable = list(set(iuse_flags_list2).difference(set(use_enable)))
	use_flagsDict = {}
	for x in use_enable:
		use_id = get_use_id(session, x)
		use_flagsDict[use_id] = True
	for x in use_disable:
		use_id = get_use_id(session, x)
		use_flagsDict[use_id] = False
	if use_enable == [] and use_disable == []:
		build_dict['build_useflags'] = None
	else:
		build_dict['build_useflags'] = use_flagsDict
	pkgdir = myportdb.getRepositoryPath(repo) + "/" + categories + "/" + package
	ebuild_version_checksum_tree = portage.checksum.sha256hash(pkgdir+ "/" + package + "-" + ebuild_version + ".ebuild")[0]
	build_dict['checksum'] = ebuild_version_checksum_tree
	ebuild_id_list, status = get_ebuild_id_db(session, build_dict['checksum'], build_dict['package_id'], build_dict['ebuild_version'])
	if status:
		if ebuild_id_list is None:
			log_msg = "%s:%s Don't have any ebuild_id!" % (pkg.cpv, repo,)
			write_log(session, log_msg, "error", config_id, 'build_log.get_build_dict_db')
		else:
			old_ebuild_id_list = []
			for ebuild_id in ebuild_id_list:
				log_msg = "%s:%s:%s Dups of checksums" % (pkg.cpv, repo, ebuild_id,)
				write_log(session, log_msg, "error", config_id, 'build_log.get_build_dict_db')
				old_ebuild_id_list.append(ebuild_id)
			add_old_ebuild(session, old_ebuild_id_list)
		return
	build_dict['ebuild_id'] = ebuild_id_list

	build_job_id = get_build_job_id(session, build_dict)
	if build_job_id is None:
		build_dict['build_job_id'] = None
	else:
		build_dict['build_job_id'] = build_job_id
	return build_dict

def search_buildlog(session, logfile_text_dict, max_text_lines):
	log_search_list = get_hilight_info(session)
	hilight_list = []
	for index, text_line in logfile_text_dict.items():
		for search_pattern in log_search_list:
			if re.search(search_pattern.HiLightSearch, text_line):
				hilight_tmp = {}
				hilight_tmp['startline'] = index - search_pattern.HiLightStart
				hilight_tmp['hilight'] = search_pattern.HiLightCssId
				if search_pattern.HiLightSearchEnd == "":
					hilight_tmp['endline'] = index + search_pattern.HiLightEnd
					if hilight_tmp['endline'] > max_text_lines:
						hilight_tmp['endline'] = max_text_lines
				elif not search_pattern.HiLightSearchEnd == "" and (index + 1) >= max_text_lines:
						hilight_tmp['endline'] = max_text_lines
				else:
					i = index + 1
					match = True
					while match:
						if i >= max_text_lines:
							match = False
							break
						if re.search(search_pattern.HiLightSearchPattern, logfile_text_dict[i]) and re.search(search_pattern.HiLightSearchPattern, logfile_text_dict[i + 1]):
							for search_pattern2 in log_search_list:
								if re.search(search_pattern2.HiLightSearch, logfile_text_dict[i]):
									match = False
							if match:
								i = i + 1
						elif re.search(search_pattern.HiLightSearchPattern, logfile_text_dict[i]) and re.search(search_pattern.HiLightSearchEnd, logfile_text_dict[i + 1]):
							i = i + 1
							match = False
						else:
							match = False
					if i >= max_text_lines:
						hilight_tmp['endline'] = max_text_lines
					if re.search(search_pattern.HiLightSearchEnd, logfile_text_dict[i]):
						hilight_tmp['endline'] = i
					else:
						hilight_tmp['endline'] = i - 1
				hilight_list.append(hilight_tmp)

	new_hilight_dict = {}
	for hilight_tmp in hilight_list:
		add_new_hilight = True
		add_new_hilight_middel = None
		for k, v in sorted(new_hilight_dict.items()):
			if hilight_tmp['startline'] == hilight_tmp['endline']:
				if v['endline'] == hilight_tmp['startline'] or v['startline'] == hilight_tmp['startline']:
					add_new_hilight = False
				if hilight_tmp['startline'] > v['startline'] and hilight_tmp['startline'] < v['endline']:
					add_new_hilight = False
					add_new_hilight_middel = k
			else:
				if v['endline'] == hilight_tmp['startline'] or v['startline'] == hilight_tmp['startline']:
					add_new_hilight = False
				if hilight_tmp['startline'] > v['startline'] and hilight_tmp['startline'] < v['endline']:
					add_new_hilight = False
		if add_new_hilight is True:
			adict = {}
			adict['startline'] = hilight_tmp['startline']
			adict['hilight_css_id'] = hilight_tmp['hilight']
			adict['endline'] = hilight_tmp['endline']
			new_hilight_dict[hilight_tmp['startline']] = adict
		if not add_new_hilight_middel is None:
			adict1 = {}
			adict2 = {}
			adict3 = {}
			adict1['startline'] = new_hilight_dict[add_new_hilight_middel]['startline']
			adict1['endline'] = hilight_tmp['startline'] -1
			adict1['hilight_css_id'] = new_hilight_dict[add_new_hilight_middel]['hilight']
			adict2['startline'] = hilight_tmp['startline']
			adict2['hilight_css_id'] = hilight_tmp['hilight']
			adict2['endline'] = hilight_tmp['endline']
			adict3['startline'] = hilight_tmp['endline'] + 1
			adict3['hilight_css_id'] = new_hilight_dict[add_new_hilight_middel]['hilight']
			adict3['endline'] = new_hilight_dict[add_new_hilight_middel]['endline']
			del new_hilight_dict[add_new_hilight_middel]
			new_hilight_dict[adict1['startline']] = adict1
			new_hilight_dict[adict2['startline']] = adict2
			new_hilight_dict[adict3['startline']] = adict3
	return new_hilight_dict

def get_buildlog_info(session, settings, pkg, build_dict, config_id):
	myportdb = portage.portdbapi(mysettings=settings)
	logfile_text_dict, max_text_lines = get_log_text_dict(settings.get("PORTAGE_LOG_FILE"))
	hilight_dict = search_buildlog(session, logfile_text_dict, max_text_lines)
	error_log_list = []
	qa_error_list = []
	repoman_error_list = []
	sum_build_log_list = []
	error_info_list = get_error_info_list(session)
	for k, v in sorted(hilight_dict.items()):
		if v['startline'] == v['endline']:
			error_log_list.append(logfile_text_dict[k])
			if v['hilight_css_id'] == 3: # qa = 3
				qa_error_list.append(logfile_text_dict[k])
		else:
			i = k
			while i != (v['endline'] + 1):
				error_log_list.append(logfile_text_dict[i])
				if v['hilight_css_id'] == 3: # qa = 3
					qa_error_list.append(logfile_text_dict[i])
				i = i +1

	# Run repoman full
	element = portage.versions.cpv_getkey(build_dict['cpv']).split('/')
	categories = element[0]
	package = element[1]
	pkgdir = myportdb.getRepositoryPath(build_dict['repo']) + "/" + categories + "/" + package
	repoman_error_list = check_repoman_full(session, pkgdir, build_dict['package_id'], config_id, build_dict['cpv'])
	build_log_dict = {}
	error_search_line = "^ \\* ERROR: "
	build_log_dict['fail'] = False
	if repoman_error_list:
		sum_build_log_list.append(1) # repoman = 1
		build_log_dict['fail'] = True
	if qa_error_list != []:
		sum_build_log_list.append(2) # qa = 2
		build_log_dict['fail'] = True
	else:
		qa_error_list = False
	for error_log_line in error_log_list:
		if re.search(error_search_line, error_log_line):
			build_log_dict['fail'] = True
			for error_info in error_info_list:
				if re.search(error_info.ErrorSearch, error_log_line):
					sum_build_log_list.append(error_info.ErrorId)
	build_log_dict['repoman_error_list'] = repoman_error_list
	build_log_dict['qa_error_list'] = qa_error_list
	build_log_dict['error_log_list'] = error_log_list
	build_log_dict['summary_error_list'] = sum_build_log_list
	build_log_dict['hilight_dict'] = hilight_dict
	return build_log_dict

def get_emerge_info_id(settings, trees, session, config_id):
	args = []
	args.append("--info")
	myaction, myopts, myfiles = parse_opts(args, silent=True)
	status, emerge_info_list = action_info(settings, trees, myopts, myfiles)
	emerge_info = ""
	return "\n".join(emerge_info_list)

def add_buildlog_main(settings, pkg, trees):
	tbc_settings = read_config_settings()
	Session = sessionmaker(bind=NewConnection(tbc_settings))
	session = Session()
	config_id = get_config_id_fqdn(session, tbc_settings['hostname'])
	ConfigInfo = get_config_info(session, config_id)
	SetupInfo = get_setup_info(session, ConfigInfo.SetupId)
	host_config = ConfigInfo.Hostname +"/" + SetupInfo.Setup
	if pkg.type_name == "binary":
		build_dict = None
	else:
		build_dict = get_build_dict_db(session, config_id, settings, tbc_settings, pkg)
	if build_dict is None:
		log_msg = "Package %s:%s is NOT logged." % (pkg.cpv, pkg.repo,)
		write_log(session, log_msg, "info", config_id, 'build_log.add_buildlog_main')
		session.close
		return
	build_log_dict = {}
	build_log_dict = get_buildlog_info(session, settings, pkg, build_dict, config_id)
	error_log_list = build_log_dict['error_log_list']
	build_log_dict['logfilename'] = settings.get("PORTAGE_LOG_FILE").split(host_config)[1]
	build_error = ""
	log_hash = hashlib.sha256()
	build_error = ""
	if error_log_list != []:
		for log_line in error_log_list:
			if not re.search(build_log_dict['logfilename'], log_line):
				build_error = build_error + log_line
		log_hash.update(build_error.encode('utf-8'))
	build_log_dict['build_error'] = build_error
	build_log_dict['log_hash'] = log_hash.hexdigest()
	log_msg = "Logfile name: %s" % (settings.get("PORTAGE_LOG_FILE"),)
	write_log(session, log_msg, "info", config_id, 'build_log.add_buildlog_main')
	build_log_dict['emerge_info'] = get_emerge_info_id(settings, trees, session, config_id)
	log_id = add_new_buildlog(session, build_dict, build_log_dict)

	if log_id is None:
		log_msg = "Package %s:%s is NOT logged." % (pkg.cpv, pkg.repo,)
		write_log(session, log_msg, "info", config_id, 'build_log.add_buildlog_main')
	else:
		add_repoman_qa(session, build_log_dict, log_id)
		os.chmod(settings.get("PORTAGE_LOG_FILE"), 0o664)
		log_msg = "Package: %s:%s is logged." % (pkg.cpv, pkg.repo,)
		write_log(session, log_msg, "info", config_id, 'build_log.add_buildlog_main')
		build_msg = "BUILD: PASS"
		qa_msg = "QA: PASS"
		repoman_msg = "REPOMAN: PASS"
		if build_log_dict['fail']:
			for error_id in build_log_dict['summary_error_list']:
				if error_id == 1:
					repoman_msg = "REPOMAN: FAILD"
				elif error_id ==2:
					qa_msg = "QA: FAILD"
				else:
					build_msg = "BUILD: FAILD"
		tbc_config =  get_tbc_config(session)
		msg = "Package: %s Repo: %s %s %s %s Weblink http://%s/new/logs/build/%s\n" % (pkg.cpv, pkg.repo, build_msg, repoman_msg, qa_msg, tbc_config.WebIrker, log_id,)
		write_log(session, msg, "info", config_id, 'build_log.add_buildlog_main')
		send_irk(msg, tbc_config.HostIrker)
	session.close

def log_fail_queru(session, build_dict, settings):
	config_id = build_dict['config_id']
	if get_fail_times(session, build_dict):
		fail_querue_dict = {}
		fail_querue_dict['build_job_id'] = build_dict['build_job_id']
		fail_querue_dict['fail_type'] = build_dict['type_fail']
		fail_querue_dict['fail_times'] = 1
		add_fail_times(session, fail_querue_dict)
		update_buildjobs_status(session, build_dict['build_job_id'], 'Waiting', config_id)
	else:
		build_log_dict = {}
		error_log_list = []
		sum_build_log_list = []
		sum_build_log_list.append(3) # Others errors
		error_log_list.append(build_dict['type_fail'])
		build_log_dict['summary_error_list'] = sum_build_log_list
		if build_dict['type_fail'] == 'merge fail':
			error_log_list = []
			for k, v in build_dict['failed_merge'].items():
				error_log_list.append(v['fail_msg'])
		build_log_dict['error_log_list'] = error_log_list
		build_error = ""
		if error_log_list != []:
			for log_line in error_log_list:
				build_error = build_error + log_line
		build_log_dict['build_error'] = build_error
		build_log_dict['log_hash'] = '0'
		useflagsdict = {}
		if build_dict['build_useflags'] == {}:
			for k, v in build_dict['build_useflags'].items():
				use_id = get_use_id(session, k)
				useflagsdict[use_id] = v
				build_dict['build_useflags'] = useflagsdict
		else:
			build_dict['build_useflags'] = None
		if settings.get("PORTAGE_LOG_FILE") is not None:
			ConfigInfo= get_config_info(session, config_id)
			host_config = ConfigInfo.Hostname +"/" + ConfigInfo.Config
			build_log_dict['logfilename'] = settings.get("PORTAGE_LOG_FILE").split(host_config)[1]
			os.chmod(settings.get("PORTAGE_LOG_FILE"), 0o664)
		else:
			build_log_dict['logfilename'] = ""
			build_log_dict['hilight_dict'] = {}
		settings2, trees, tmp = load_emerge_config()
		build_log_dict['emerge_info'] = get_emerge_info_id(settings2, trees, session, config_id)
		build_log_dict['fail'] = True
		log_id = add_new_buildlog(session, build_dict, build_log_dict)
		del_old_build_jobs(session, build_dict['build_job_id'])
