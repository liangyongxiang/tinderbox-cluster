# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
from datetime import datetime
from tbc.log import write_log
from tbc.sqlquerys import get_category_list_info, get_package_list_info, get_ebuild_list_info, \
	get_build_job_all, del_old_build_jobs, del_old_ebuild, del_old_package, add_old_category

def remove_old_ebuilds(session, package_id, config_id, cp, today):
	EbuildsInfo = get_ebuild_list_info(session, package_id)
	for EbuildInfo in EbuildsInfo:
		cpv = cp + '-' + EbuildInfo.Version
		log_msg = "Checking: %s" % (cpv,)
		write_log(session, log_msg, "info", config_id, 'old_cpv.remove_old_ebuilds')
		if not EbuildInfo.Active:
			duration = today - EbuildInfo.TimeStamp
			if duration.days > 30:
				log_msg = "Removing: %s" % (cpv,)
				write_log(session, log_msg, "info", config_id, 'old_cpv.remove_old_ebuilds')
				build_job_id_list = get_build_job_all(session, EbuildInfo.EbuildId)
				if build_job_id_list != []:
					for build_job in build_job_id_list:
						del_old_build_jobs(session, build_job.BuildJobId)
				del_old_ebuild(session, EbuildInfo.EbuildId)
	if get_ebuild_list_info(session, package_id) == []:
		log_msg = "Removing: %s" % (cp,)
		write_log(session, log_msg, "info", config_id, 'old_cpv.remove_old_cpv_ebuilds')
		del_old_package(session, package_id)

def remove_old_cpv_main(session, config_id):
	today = datetime.utcnow()
	CategorysInfo = get_category_list_info(session)
	for CategoryInfo in CategorysInfo:
		log_msg = "Checking: %s" % (CategoryInfo.Category,)
		write_log(session, log_msg, "info", config_id, 'old_cpv.remove_old_cpv_main')
		PackagesInfo = get_package_list_info(session, CategoryInfo.CategoryId)
		for PackageInfo in PackagesInfo:
			cp = CategoryInfo.Category + '/' + PackageInfo.Package
			remove_old_ebuilds(session, PackageInfo.PackageId, config_id, cp, today)

		if get_package_list_info(session, CategoryInfo.CategoryId) == []:
			 add_old_category(session, CategoryInfo.CategoryId)
