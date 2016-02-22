# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import multiprocessing
from datetime import datetime
from tbc.log import write_log
from sqlalchemy.orm import scoped_session, sessionmaker
from tbc.ConnectionManager import NewConnection
from tbc.readconf import  read_config_settings
from tbc.sqlquerys import get_category_list_info, get_package_list_info, get_ebuild_list_info, \
	get_build_job_all, del_old_build_jobs, del_old_ebuild, del_old_package, add_old_category

def remove_old_ebuilds(package_id, config_id, tbc_settings, cp):
	today = datetime.utcnow()
	session_factory = sessionmaker(bind=NewConnection(tbc_settings))
	Session = scoped_session(session_factory)
	session2 = Session()
	EbuildsInfo = get_ebuild_list_info(session2, package_id)
	for EbuildInfo in EbuildsInfo:
		cpv = cp + '-' + EbuildInfo.Version
		log_msg = "Checking: %s" % (cpv,)
		write_log(session2, log_msg, "info", config_id, 'old_cpv.remove_old_ebuilds')
		if not EbuildInfo.Active:
			duration = today - EbuildInfo.TimeStamp
			if duration.days > 30:
				log_msg = "Removing: %s" % (cpv,)
				write_log(session2, log_msg, "info", config_id, 'old_cpv.remove_old_ebuilds')
				build_job_id_list = get_build_job_all(session2, EbuildInfo.EbuildId)
				if build_job_id_list != []:
					for build_job in build_job_id_list:
						del_old_build_jobs(session2, build_job.BuildJobId)
				del_old_ebuild(session2, EbuildInfo.EbuildId)
	if not get_ebuild_list_info(session2, package_id):
		log_msg = "Removing: %s" % (cp,)
		write_log(session2, log_msg, "info", config_id, 'old_cpv.remove_old_cpv_ebuilds')
		del_old_package(session2, package_id)
	session2.close
	Session.remove()

def remove_old_cpv_main(session, config_id):
	tbc_settings = read_config_settings()
	# Use all cores when multiprocessing
	#pool_cores = multiprocessing.cpu_count()
	#pool = multiprocessing.Pool(processes = pool_cores)

	CategorysInfo = get_category_list_info(session)
	for CategoryInfo in CategorysInfo:
		log_msg = "Checking: %s" % (CategoryInfo.Category,)
		write_log(session2, log_msg, "info", config_id, 'old_cpv.remove_old_cpv_main')
		PackagesInfo = get_package_list_info(session, CategoryInfo.CategoryId)
		for PackageInfo in PackagesInfo:
			cp = CategoryInfo.Category + '/' + PackageInfo.Package
			# pool.apply_async( remove_old_ebuilds, (Package.PackageId, config_id, tbc_settings, cp,))
			# use this when debuging
			remove_old_ebuilds(PackageInfo.PackageId, config_id, tbc_settings, cp,)

		#close and join the multiprocessing pools
		# pool.close()
		# pool.join()
		if not get_package_list_info(session, CategoryInfo.CategoryId):
			 add_old_category(session, CategoryInfo.CategoryId)
