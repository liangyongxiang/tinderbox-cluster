# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import datetime
import sys
from tbc.db_mapping import Configs, Logs, ConfigsMetaData, Jobs, BuildJobs, Packages, Ebuilds, Repos, Categories, \
	Uses, ConfigsEmergeOptions, EmergeOptions, HiLight, BuildLogs, BuildLogsConfig, BuildJobsUse, BuildJobsRedo, \
	HiLightCss, BuildLogsHiLight, BuildLogsEmergeOptions, BuildLogsErrors, ErrorsInfo, EmergeInfo, BuildLogsUse, \
	BuildJobsEmergeOptions, EbuildsMetadata, EbuildsIUse, Restrictions, EbuildsRestrictions, EbuildsKeywords, \
	Keywords, PackagesMetadata, Emails, PackagesEmails, Setups, BuildLogsRepoman, CategoriesMetadata, \
	PackagesRepoman, BuildLogsQa, TbcConfig
from tbc.log import write_log
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import and_, or_

# Guest Functions
def get_tbc_config(session):
	TbcConfigInfo = session.query(TbcConfig).one()
	return TbcConfigInfo

def get_config_id(session, setup, host):
	SetupInfo = session.query(Setups).filter_by(Setup = setup).one()
	ConfigInfo = session.query(Configs).filter_by(SetupId = SetupInfo.SetupId).filter_by(Hostname = host).one()
	return ConfigInfo.ConfigId

def get_config_id_fqdn(session, host):
	ConfigInfo = session.query(Configs).filter_by(Hostname = host).one()
	return ConfigInfo.ConfigId

def add_logs(session, log_msg, log_type, config_id):
	Add_Log = Logs(ConfigId = config_id, LogType = log_type, Msg = log_msg)
	session.add(Add_Log)
	session.commit()

def update_deamon_status(session, status, config_id):
	ConfigInfo = session.query(ConfigsMetaData).filter_by(ConfigId = config_id).one()
	ConfigInfo.Status = status
	session.commit()

def get_jobs(session, config_id):
	JobsInfo = session.query(Jobs).filter_by(Status = 'Waiting').filter_by(ConfigId = config_id).order_by(Jobs.JobId).all()
	if JobsInfo == []:
		return None
	return JobsInfo

def update_job_list(session, status, job_id):
	JobInfo = session.query(Jobs).filter_by(JobId = job_id).one()
	JobInfo.Status = status
	session.commit()

def get_config_all_info(session):
	return session.query(Configs).all()

def get_config_info(session, config_id):
	ConfigInfo = session.query(Configs).filter_by(ConfigId = config_id).one()
	return ConfigInfo

def get_setup_info(session, config_id):
	ConfigInfo = get_config_info(session, config_id)
	SetupInfo = session.query(Setups).filter_by(SetupId = ConfigInfo.SetupId).one()
	return SetupInfo

def update_buildjobs_status(session, build_job_id, status, config_id):
	BuildJobsInfo = session.query(BuildJobs).filter_by(BuildJobId = build_job_id).one()
	BuildJobsInfo.Status = status
	BuildJobsInfo.ConfigId = config_id
	session.commit()

def get_configmetadata_info(session, config_id):
	return session.query(ConfigsMetaData).filter_by(ConfigId = config_id).one()

def is_build_job_done(session, build_job_id):
	try:
		BuildJobsInfo = session.query(BuildJobs).filter_by(BuildJobId = build_job_id).one()
	except NoResultFound as e:
		return False
	return True

def get_packages_to_build(session, config_id):
	SetupInfo = get_setup_info(session, config_id)
	BuildJobsTmp = session.query(BuildJobs).filter(BuildJobs.SetupId==SetupInfo.SetupId). \
		order_by(BuildJobs.BuildJobId).filter_by(Status = 'Waiting')
	if BuildJobsTmp.all() == []:
		return None
	elif BuildJobsTmp.filter_by(BuildNow = True).all() != []:
		BuildJobsInfo = BuildJobsTmp.filter_by(BuildNow = True).first()
	elif BuildJobsTmp.filter_by(BuildNow = False).all() != []:
		BuildJobsInfo = BuildJobsTmp.filter_by(BuildNow = False).first()
	else:
		return None
	update_buildjobs_status(session, BuildJobsInfo.BuildJobId, 'Looked', config_id)
	EbuildsInfo = session.query(Ebuilds).filter_by(EbuildId = BuildJobsInfo.EbuildId).one()
	PackagesInfo, CategoriesInfo = session.query(Packages, Categories).filter(Packages.PackageId==EbuildsInfo.PackageId).filter(Packages.CategoryId==Categories.CategoryId).one()
	ReposInfo = session.query(Repos).filter_by(RepoId = PackagesInfo.RepoId).one()
	uses={}
	for BuildJobsUseInfo, UsesInfo in session.query(BuildJobsUse, Uses).filter(BuildJobsUse.BuildJobId==BuildJobsInfo.BuildJobId).filter(BuildJobsUse.UseId==Uses.UseId).all():
		uses[UsesInfo.Flag] = BuildJobsUseInfo.Status
	if uses == {}:
		uses = None
	emerge_options_list = []
	for ConfigsEmergeOptionsInfo, EmergeOptionsInfo in session.query(ConfigsEmergeOptions, EmergeOptions). \
			filter(ConfigsEmergeOptions.ConfigId==config_id). \
			filter(ConfigsEmergeOptions.EOptionId==EmergeOptions.EmergeOptionId).all():
		emerge_options_list.append(EmergeOptionsInfo.EOption)
	build_dict={}
	build_dict['config_id'] = config_id
	build_dict['setup_id'] = BuildJobsInfo.SetupId
	build_dict['build_job_id'] = BuildJobsInfo.BuildJobId
	build_dict['ebuild_id']= EbuildsInfo.EbuildId
	build_dict['package_id'] = EbuildsInfo.PackageId
	build_dict['package'] = PackagesInfo.Package
	build_dict['category'] = CategoriesInfo.Category
	build_dict['repo'] = ReposInfo.Repo
	build_dict['removebin'] = BuildJobsInfo.RemoveBin
	build_dict['ebuild_version'] = EbuildsInfo.Version
	build_dict['checksum'] = EbuildsInfo.Checksum
	build_dict['cp'] = CategoriesInfo.Category + '/' + PackagesInfo.Package
	build_dict['cpv'] = build_dict['cp'] + '-' + EbuildsInfo.Version
	build_dict['build_useflags'] = uses
	build_dict['emerge_options'] = emerge_options_list
	return build_dict

def get_category_info(session, category):
	try:
		CategoryInfo = session.query(Categories).filter_by(Category = category).filter_by(Active = True).one()
	except NoResultFound as e:
		return False
	return CategoryInfo

def get_repo_info(session, repo):
	try:
		RepoInfo = session.query(Repos).filter_by(Repo = repo).one()
	except NoResultFound as e:
		return False
	return RepoInfo

def get_package_info(session, category, package, repo):
	CategoryInfo = get_category_info(session, category)
	RepoInfo = get_repo_info(session, repo)
	try:
		PackageInfo = session.query(Packages).filter_by(CategoryId = CategoryInfo.CategoryId). \
			filter_by(Package = package).filter_by(RepoId = RepoInfo.RepoId).filter_by(Active = True).one()
	except NoResultFound as e:
		return False
	return PackageInfo

def get_ebuild_info(session, build_dict):
	EbuildInfo = session.query(Ebuilds).filter_by(Version = build_dict['ebuild_version']).filter_by(Checksum = build_dict['checksum']).\
		filter_by(PackageId = build_dict['package_id']).filter_by(Active = True)
	if EbuildInfo.all() == []:
		return None, True
	try:
		EbuildInfo2 = EbuildInfo.one()
	except (MultipleResultsFound) as e:
		return EbuildInfo.all(), True
	return EbuildInfo2, False

def get_ebuild_info_ebuild_id(session, ebuild_id):
	return session.query(Ebuilds).filter_by(EbuildId = ebuild_id).filter_by(Active = True).one()

def get_build_job_id(session, build_dict):
	BuildJobsIdInfo = session.query(BuildJobs.BuildJobId).filter_by(EbuildId = build_dict['ebuild_id']).filter_by(ConfigId = build_dict['config_id']).all()
	if BuildJobsIdInfo == []:
		return None
	for build_job_id in BuildJobsIdInfo:
		BuildJobsUseInfo = session.query(BuildJobsUse).filter_by(BuildJobId = build_job_id.BuildJobId).all()
		useflagsdict = {}
		if BuildJobsUseInfo == []:
			useflagsdict = None
		else:
			for x in BuildJobsUseInfo:
				useflagsdict[x.UseId] = x.Status
		if useflagsdict == build_dict['build_useflags']:
			return build_job_id.BuildJobId
	return None

def get_use_id(session, use_flag):
	try:
		UseIdInfo = session.query(Uses).filter_by(Flag = use_flag).one()
	except NoResultFound as e:
		return None
	return UseIdInfo.UseId

def get_hilight_info(session):
	return session.query(HiLight).all()

def get_error_info_list(session):
	return session.query(ErrorsInfo).all()

def add_e_info(session, emerge_info):
	AddEmergeInfo = EmergeInfo(EmergeInfoText = emerge_info)
	session.add(AddEmergeInfo)
	session.flush()
	EmergeInfoId = AddEmergeInfo.EInfoId
	session.commit()
	return EmergeInfoId

def del_old_build_jobs(session, build_job_id):
	session.query(BuildJobsUse).filter(BuildJobsUse.BuildJobId == build_job_id).delete()
	session.query(BuildJobsRedo).filter(BuildJobsRedo.BuildJobId == build_job_id).delete()
	session.query(BuildJobsEmergeOptions).filter(BuildJobsEmergeOptions.BuildJobId == build_job_id).delete()
	session.query(BuildJobs).filter(BuildJobs.BuildJobId == build_job_id).delete()
	session.commit()

def add_new_buildlog(session, build_dict, build_log_dict):
	build_log_id_list = session.query(BuildLogs.BuildLogId).filter_by(EbuildId = build_dict['ebuild_id']).all()

	def add_new_hilight(log_id, build_log_dict):
		for k, hilight_tmp in sorted(build_log_dict['hilight_dict'].items()):
			NewHiLight = BuildLogsHiLight(LogId = log_id, StartLine = hilight_tmp['startline'], EndLine = hilight_tmp['endline'], HiLightCssId = hilight_tmp['hilight_css_id'])
			session.add(NewHiLight)
			session.commit()

	def build_log_id_match(build_log_id_list, build_dict, build_log_dict):
		for build_log_id in build_log_id_list:
			log_hash = session.query(BuildLogs.LogHash).filter_by(BuildLogId = build_log_id[0]).one()
			use_list = session.query(BuildLogsUse).filter_by(BuildLogId = build_log_id[0]).all()
			useflagsdict = {}
			if use_list == []:
				useflagsdict = None
			else:
				for use in use_list:
					useflagsdict[use.UseId] = use.Status
			msg = 'Log_hash: %s Log_hash_sql: %s Build_log_id: %s' % (build_log_dict['log_hash'], log_hash[0], build_log_id,)
			write_log(session, msg, "debug", build_dict['config_id'], 'sqlquerys.add_new_buildlog.build_log_id_match')
			if log_hash[0] == build_log_dict['log_hash'] and build_dict['build_useflags'] == useflagsdict:
				if session.query(BuildLogsConfig).filter(BuildLogsConfig.ConfigId.in_([build_dict['config_id']])).filter_by(BuildLogId = build_log_id[0]):
					return None, True
				e_info_id = add_e_info(session, build_log_dict['emerge_info'])
				NewBuildLogConfig = BuildLogsConfig(BuildLogId = build_log_id[0], ConfigId = build_dict['config_id'], LogName = build_log_dict['logfilename'], EInfoId = e_info_id)
				session.add(NewBuildLogConfig)
				session.commit()
				return build_log_id[0], True
		return None, False

	def build_log_id_no_match(build_dict, build_log_dict):
		NewBuildLog = BuildLogs(EbuildId = build_dict['ebuild_id'], Fail = build_log_dict['fail'], SummeryText = build_log_dict['build_error'], LogHash = build_log_dict['log_hash'])
		session.add(NewBuildLog)
		session.flush()
		build_log_id = NewBuildLog.BuildLogId
		session.commit()
		if build_log_dict['summary_error_list'] != []:
			for error in build_log_dict['summary_error_list']:
				NewError = BuildLogsErrors(BuildLogId = build_log_id, ErrorId = error)
				session.add(NewError)
				session.commit()
		e_info_id = add_e_info(session, build_log_dict['emerge_info'])
		NewBuildLogConfig = BuildLogsConfig(BuildLogId = build_log_id, ConfigId = build_dict['config_id'], LogName = build_log_dict['logfilename'], EInfoId = e_info_id)
		session.add(NewBuildLogConfig)
		session.flush()
		log_id = NewBuildLogConfig.LogId
		session.commit()
		add_new_hilight(log_id, build_log_dict)
		if not build_dict['build_useflags'] is None:
			for use_id, status in  build_dict['build_useflags'].items():
				NewBuildLogUse = BuildLogsUse(BuildLogId = build_log_id, UseId = use_id, Status = status)
				session.add(NewBuildLogUse)
				session.flush()
			session.commit()
		return build_log_id

	msg = 'build_job_id: %s build_log_id_list: %s' % (build_dict['build_job_id'], build_log_id_list,)
	write_log(session, msg, "debug", build_dict['config_id'], 'sqlquerys.add_new_buildlog')
	if build_dict['build_job_id'] is None and build_log_id_list == []:
		build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		return build_log_id
	elif build_dict['build_job_id'] is None and build_log_id_list != []:
		build_log_id, match = build_log_id_match(build_log_id_list, build_dict, build_log_dict)
		if not match:
			build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		return build_log_id
	elif not build_dict['build_job_id'] is None and build_log_id_list != []:
		build_log_id, match = build_log_id_match(build_log_id_list, build_dict, build_log_dict)
		if not match:
			build_log_id = build_log_id_no_match(build_dict, build_log_dict)
			del_old_build_jobs(session, build_dict['build_job_id'])
		return build_log_id
	elif not build_dict['build_job_id'] is None and build_log_id_list == []:
		build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		del_old_build_jobs(session, build_dict['build_job_id'])
		return build_log_id

def add_repoman_qa(session, build_log_dict, log_id):
	repoman_error = ""
	qa_error = ""
	if build_log_dict['repoman_error_list']:
		for repoman_text in build_log_dict['repoman_error_list']:
			repoman_error = repoman_error + repoman_text
		NewBuildLogRepoman = BuildLogsRepoman(BuildLogId = log_id, SummeryText = repoman_error)
		session.add(NewBuildLogRepoman)
		session.commit()
	if build_log_dict['qa_error_list']:
		for qa_text in build_log_dict['qa_error_list']:
			qa_error = qa_error + qa_text
		NewBuildLogQa = BuildLogsQa(BuildLogId = log_id, SummeryText = qa_error)
		session.add(NewBuildLogQa)
		session.commit()

def update_fail_times(session, FailInfo):
	NewBuildJobs = session.query(BuildJobs).filter_by(BuildJobId = FailInfo.BuildJobId).one()
	NewBuildJobs.TimeStamp = datetime.datetime.utcnow()
	session.commit()

def get_fail_times(session, build_dict):
	try:
		FailInfo = session.query(BuildJobsRedo).filter_by(BuildJobId = build_dict['build_job_id']).filter_by(FailType = build_dict['type_fail']).one()
	except NoResultFound as e:
		return False
	return True

def add_fail_times(session, fail_querue_dict):
	NewBuildJobsRedo = BuildJobsRedo(BuildJobId = fail_querue_dict['build_job_id'], FailType = fail_querue_dict['fail_type'], FailTimes = fail_querue_dict['fail_times'])
	session.add(NewBuildJobsRedo)
	session.commit()

def check_host_updatedb(session):
	jobs = False
	try:
		JobsInfo = session.query(Jobs).filter_by(Status = 'Done').filter_by(JobType = 'esync').one()
	except NoResultFound as e:
		jobs = True
	try:
		JobsInfo = session.query(Jobs).filter_by(Status = 'Done').filter_by(JobType = 'updatedb').one()
	except NoResultFound as e:
		jobs = True
	return jobs

# Host Functions
def update_repo_db(session, repo_list):
	for repo in repo_list:
		if not get_repo_info(session, repo):
			session.add(Repos(Repo = repo))
			session.commit()

def update_categories_db(session, category, categories_metadataDict):
	CategoryInfo = get_category_info(session, category)
	if not CategoryInfo:
		session.add(Categories(Category = category))
		session.commit()
		CategoryInfo = get_category_info(session, category)
	try:
		CategoriesMetadataInfo = session.query(CategoriesMetadata).filter_by(CategoryId = CategoryInfo.CategoryId).one()
	except NoResultFound as e:
		NewCategoriesMetadata = CategoriesMetadata(CategoryId = CategoryInfo.CategoryId, Checksum = categories_metadataDict['metadata_xml_checksum'], Descriptions = categories_metadataDict['metadata_xml_descriptions'])
		session.add(NewCategoriesMetadata)
		session.commit()
		return
	if CategoriesMetadataInfo.Checksum != categories_metadataDict['metadata_xml_checksum']:
		CategoriesMetadataInfo.Checksum = categories_metadataDict['metadata_xml_checksum']
		CategoriesMetadataInfo.Descriptions = categories_metadataDict['metadata_xml_descriptions']
		session.commit()

def get_keyword_id(session, keyword):
	try:
		KeywordsInfo = session.query(Keywords).filter_by(Keyword = keyword).one()
	except NoResultFound as e:
		return None
	return KeywordsInfo.KeywordId

def add_new_ebuild_metadata_sql(session, ebuild_id, keywords, restrictions, iuse_list):
	for restriction in restrictions:
		if restriction in ["!"]:
			restriction = restriction[1:]
		if restriction in ["?"]:
			restriction = restriction[:1]
		if restriction != '(' or restriction != ')':
			try:
				RestrictionInfo = session.query(Restrictions).filter_by(Restriction = restriction).one()
			except NoResultFound as e:
				session.add(Restrictions(Restriction = restriction))
				session.commit()
				RestrictionInfo = session.query(Restrictions).filter_by(Restriction = restriction).one()
			session.add(EbuildsRestrictions(EbuildId = ebuild_id, RestrictionId = RestrictionInfo.RestrictionId))
			session.commit()
	for iuse in iuse_list:
		status = False
		if iuse[0] in ["+"]:
			iuse = iuse[1:]
			status = True
		elif iuse[0] in ["-"]:
			iuse = iuse[1:]
		use_id = get_use_id(session, iuse)
		if use_id is None:
			session.add(Uses(Flag = iuse))
			session.commit()
			use_id = get_use_id(session, iuse)
		session.add(EbuildsIUse(EbuildId = ebuild_id, UseId = use_id, Status = status))
		session.commit()
	for keyword in keywords:
		status = 'Stable'
		if keyword[0] in ["~"]:
			keyword = keyword[1:]
			status = 'Unstable'
		elif keyword[0] in ["-"]:
			keyword = keyword[1:]
			status = 'Negative'
		keyword_id = get_keyword_id(session, keyword)
		if keyword_id is None:
			session.add(Keywords(Keyword = keyword))
			session.commit()
			keyword_id = get_keyword_id(session, keyword)
		session.add(EbuildsKeywords(EbuildId = ebuild_id, KeywordId = keyword_id, Status = status)) 
		session.commit()

def add_new_ebuild_sql(session, packageDict):
	ebuild_id_list = []
	for k, v in packageDict.items():
		session.add(Ebuilds(PackageId = v['package_id'], Version = v['ebuild_version'], Checksum = v['checksum'], Active = True))
		session.flush()
		try:
			EbuildInfo = session.query(Ebuilds).filter_by(Version = v['ebuild_version']).filter_by(Checksum = v['checksum']).\
				filter_by(PackageId = v['package_id']).filter_by(Active = True).one()
		except (MultipleResultsFound) as e:
			for x in session.query(Ebuilds).filter_by(Version = v['ebuild_version']).filter_by(Checksum = v['checksum']).\
				filter_by(PackageId = v['package_id']).filter_by(Active = True).all():
				x.Checksum = 0
				x.Active = False
				session.commit()
			try:
				EbuildInfo = session.query(Ebuilds).filter_by(Version = v['ebuild_version']).filter_by(Checksum = v['checksum']).\
					filter_by(PackageId = v['package_id']).filter_by(Active = True).one()
			except (MultipleResultsFound) as e:
				# FIXME
				sys.exit()
		session.add(EbuildsMetadata(EbuildId = EbuildInfo.EbuildId, New = v['new'], Updated = v['updated'], = v['git_commit'], Descriptions = v['ebuild_version_descriptions_tree']))
		session.commit()
		ebuild_id_list.append(EbuildInfo.EbuildId)
		restrictions = []
		keywords = []
		iuse = []
		for i in v['ebuild_version_metadata_tree'][4].split():
			restrictions.append(i)
		for i in v['ebuild_version_metadata_tree'][8].split():
			keywords.append(i)
		for i in v['ebuild_version_metadata_tree'][10].split():
			iuse.append(i)
		add_new_ebuild_metadata_sql(session, EbuildInfo.EbuildId, keywords, restrictions, iuse)
	return ebuild_id_list

def get_ebuild_id_list(session, package_id):
	ebuild_id_list = []
	for EbuildInfo in session.query(Ebuilds).filter_by(PackageId = package_id).filter_by(Active = True).all():
		ebuild_id_list.append(EbuildInfo.EbuildId)
	return ebuild_id_list

def get_build_job_all(session, ebuild_id):
	return session.query(BuildJobs).filter_by(EbuildId = ebuild_id).all()

def add_old_ebuild(session, old_ebuild_list):
	for ebuild_id in  old_ebuild_list:
		EbuildInfo = session.query(Ebuilds).filter_by(EbuildId = ebuild_id).one()
		EbuildInfo.Active = False
		session.commit()
		build_job_id_list = get_build_job_all(session, ebuild_id)
		if build_job_id_list != []:
			for build_job in build_job_id_list:
				del_old_build_jobs(session, build_job.BuildJobId)

def add_old_package(session, package_id):
	PackagesInfo = session.query(Packages).filter_by(PackageId = package_id).one()
	PackagesInfo.Active = False
	session.commit()

def add_new_package_sql(session, cp, repo):
	element = cp.split('/')
	categories = element[0]
	package = element[1]
	RepoInfo =get_repo_info(session, repo)
	repo_id = RepoInfo.RepoId
	CategoriesInfo = get_category_info(session, categories)
	category_id = CategoriesInfo.CategoryId
	session.add(Packages(Package = package, CategoryId = category_id, RepoId = repo_id, Active = True))
	session.commit()
	PackageInfo = get_package_info(session, categories, package, repo)
	return PackageInfo.PackageId

def get_package_metadata_sql(session, package_id):
	try:
		PackagesMetadataInfo = session.query(PackagesMetadata).filter_by(PackageId = package_id).one()
	except NoResultFound as e:
		return False
	return PackagesMetadataInfo

def update_email_info(session, email):
	try:
		EmailInfo = session.query(Emails).filter_by(Email = email).one()
	except NoResultFound as e:
		session.add(Emails(Email = email))
		session.commit()
		EmailInfo = session.query(Emails).filter_by(Email = email).one()
	return EmailInfo

def update_package_email_info(session, email_id, package_id):
	try:
		PackagesEmailInfo = session.query(PackagesEmails).filter_by(EmailId = email_id).filter_by(PackageId = package_id).one()
	except NoResultFound as e:
		session.add(PackagesEmails(EmailId = email_id, PackageId = package_id))
		session.commit()
		PackagesEmailInfo = session.query(PackagesEmails).filter_by(EmailId = email_id).filter_by(PackageId = package_id).one()
	return PackagesEmailInfo

def update_package_metadata(session, package_metadataDict):
	for k, v in package_metadataDict.items():
		try:
			PackagesMetadataInfo = session.query(PackagesMetadata).filter_by(PackageId = k).one()
		except NoResultFound as e:
			session.add(PackagesMetadata(PackageId = k, Gitlog = v['git_changlog'], Descriptions = v['metadata_xml_descriptions'], v['new']))
			session.commit()
		else:
			PackagesMetadataInfo.Gitlog = v['git_changlog']
			PackagesMetadataInfo.Descriptions = v['metadata_xml_descriptions']
			session.commit()
		if v['metadata_xml_email']:
			for email in v['metadata_xml_email']:
				EmailInfo = update_email_info(session, email)
				PackagesEmailInfo = update_package_email_info(session, EmailInfo.EmailId, k)

def get_package_info_from_package_id(session, package_id):
	PackageInfo = session.query(Packages).filter_by(PackageId = package_id).one()
	CategoryInfo = session.query(Categories).filter_by(CategoryId = PackageInfo.CategoryId).one()
	RepoInfo = session.query(Repos).filter_by(RepoId = PackageInfo.RepoId).one()
	return PackageInfo, CategoryInfo, RepoInfo

def add_new_build_job(session, ebuild_id, setup_id, use_flagsDict, config_id):
	NewBuildJobs =BuildJobs(EbuildId = ebuild_id, SetupId = setup_id, ConfigId = config_id, Status = 'Waiting', BuildNow = False, RemoveBin = True)
	session.add(NewBuildJobs)
	session.flush()
	build_job_id = NewBuildJobs.BuildJobId
	session.commit()
	for k, v in use_flagsDict.items():
		use_id = get_use_id(session, k)
		session.add(BuildJobsUse(BuildJobId = build_job_id, UseId = use_id, Status = v))
		session.commit()

def get_ebuild_checksums(session, package_id, ebuild_version):
	ebuild_checksum_list = []
	try:
		EbuildInfo = session.query(Ebuilds).filter_by(PackageId = package_id).filter_by(Version = ebuild_version).filter_by(Active = True).one()
	except NoResultFound as e:
		return None, False
	except MultipleResultsFound as e:
		EbuildInfo2 = session.query(Ebuilds).filter_by(PackageId = package_id).filter_by(Version = ebuild_version).filter_by(Active = True).all()
		for Ebuild in EbuildInfo2:
			ebuild_checksum_list.append(Ebuild.Checksum)
		return ebuild_checksum_list, True
	return EbuildInfo.Checksum, False

def get_ebuild_id_db(session, checksum, package_id, ebuild_version):
	try:
		EbuildInfos = session.query(Ebuilds).filter_by(PackageId = package_id).filter_by(Checksum = checksum).filter_by(Version = ebuild_version).filter_by(Active = True).one()
	except NoResultFound as e:
		return None, True
	except MultipleResultsFound as e:
		EbuildInfos = session.query(Ebuilds).filter_by(PackageId = package_id).filter_by(Checksum = checksum).filter_by(Version = ebuild_version).filter_by(Active = True).all()
		ebuilds_id = []
		for EbuildInfo in EbuildInfos:
			ebuilds_id.append(EbuildInfo.EbuildId)
		return ebuilds_id, True
	return EbuildInfos.EbuildId, False

def get_ebuild_restrictions(session, ebuild_id):
	restrictions = []
	EbuildsRestrictionsInfos = session.query(EbuildsRestrictions).filter_by(EbuildId = ebuild_id).all()
	if EbuildsRestrictionsInfos == []:
		return False
	for EbuildsRestrictionsInfo in EbuildsRestrictionsInfos:
		RestrictionsInfo = session.query(Restrictions).filter_by(RestrictionId = EbuildsRestrictionsInfo.RestrictionId).one()
		restrictions.append(RestrictionsInfo.Restriction)
	return restrictions

def add_repoman_log(session, package_id, repoman_log, repoman_hash):
	try:
		PackagesRepomanInfo = session.query(PackagesRepoman).filter_by(PackageId = package_id).one()
	except NoResultFound as e:
		session.add(PackagesRepoman(PackageId = package_id, RepomanText = repoman_log, RepomanHash = repoman_hash))
		session.commit()
	else:
		if PackagesRepomanInfo.RepomanHash != repoman_hash:
			PackagesRepomanInfo.RepomanHash = repoman_hash
			PackagesRepomanInfo.RepomanText = repoman_log
			session.commit()

def get_category_list_info(session):
	return session.query(Categories).all()

def get_package_list_info(session, category_id):
	return session.query(Packages).filter_by(CategoryId = category_id).all()

def get_ebuild_list_info(session, package_id):
	return session.query(Ebuilds).filter_by(PackageId = package_id).all()

def del_old_ebuild(session, ebuild_id):
	session.query(EbuildsRestrictions).filter(EbuildsRestrictions.EbuildId == ebuild_id).delete()
	session.query(EbuildsIUse).filter(EbuildsIUse.EbuildId == ebuild_id).delete()
	session.query(EbuildsKeywords).filter(EbuildsKeywords.EbuildId == ebuild_id).delete()
	session.query(EbuildsMetadata).filter(EbuildsMetadata.EbuildId == ebuild_id).delete()
	session.query(Ebuilds).filter(Ebuilds.EbuildId == ebuild_id).delete()
	session.commit()

def del_old_package(session, package_id):
	session.query(PackagesRepoman).filter(PackagesRepoman.PackageId == package_id).delete()
	session.query(PackagesEmails).filter(PackagesEmails.PackageId== package_id).delete()
	session.query(PackagesMetadata).filter(PackagesMetadata.PackageId == package_id).delete()
	session.query(Packages).filter(Packages.PackageId == package_id).delete()
	session.commit()

def add_old_category(session, category_id):
	CategorysInfo = session.query(Categories).filter_by(CategoryId = category_id).one()
	CategorysInfo.Active = False
	session.commit()
