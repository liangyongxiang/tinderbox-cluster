# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Keywords(Base):
	KeywordId = Column('keyword_id', Integer, primary_key=True)
	Keyword = Column('keyword', String)
	__tablename__ = 'keywords'

class Setups(Base):
	SetupId = Column('setup_id', Integer, primary_key=True)
	Setup = Column('setup', String(100))
	Profile = Column('profile', String(150))
	Test = Column('test', Boolean, default=False)
	Repoman = Column('repoman', Boolean, default=False)
	__tablename__ = 'setups'

class Configs(Base):
	ConfigId = Column('config_id', Integer, primary_key=True)
	Hostname = Column('hostname', String(150))
	SetupId = Column('setup_id', Integer, ForeignKey('setups.setup_id'))
	Host = Column('default_config', Boolean, default=False)
	__tablename__ = 'configs'

class Logs(Base):
	LogId = Column('log_id', Integer, primary_key=True)
	ConfigId = Column('config_id', Integer, ForeignKey('configs.config_id'))
	LogType = Column('log_type', Enum('info','error','debug','qa','repoman'))
	Msg = Column('msg', Text)
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'logs'

class Jobs(Base):
	JobId = Column('job_id', Integer, primary_key=True)
	JobType = Column('job_type', Enum('updatedb', 'esync', 'removeold_cpv'))
	Status = Column('status', Enum('Runing', 'Done', 'Waiting'))
	User = Column('user', String(50))
	ConfigId = Column('config_id', Integer, ForeignKey('configs.config_id'))
	RunConfigId = Column('run_config_id', Integer, ForeignKey('configs.config_id'))
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'jobs'

class ConfigsMetaData(Base):
	Id = Column('id', Integer, primary_key=True)
	ConfigId = Column('config_id', Integer, ForeignKey('configs.config_id'))
	KeywordId = Column('keyword_id', Integer, ForeignKey('keywords.keyword_id'))
	MakeConfText = Column('make_conf_text', Text)
	Checksum = Column('checksum', String(100))
	ConfigSync = Column('configsync', Boolean, default=False)
	Active = Column('active', Boolean, default=False)
	ConfigErrorText = Column('config_error_text', Text)
	Updateing = Column('updateing', Boolean, default=False)
	Status = Column('status', Enum('Stopped', 'Runing', 'Waiting'))
	Auto = Column('auto', Boolean, default=False)
	RepoPath = Column('repo_path', String(200))
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'configs_metadata'

class Categories(Base):
	CategoryId = Column('category_id', Integer, primary_key=True)
	Category = Column('category', String(150))
	Active = Column('active', Boolean, default=True)
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'categories'

class CategoriesMetadata(Base):
	Id = Column('id', Integer, primary_key=True)
	CategoryId = Column('category_id', Integer, ForeignKey('categories.category_id'))
	Checksum = Column('checksum', String(100))
	Descriptions = Column('descriptions', Text)
	__tablename__ = 'categories_metadata'

class Repos(Base):
	RepoId = Column('repo_id', Integer, primary_key=True)
	Repo = Column('repo', String(100))
	__tablename__ = 'repos'

class Packages(Base):
	PackageId = Column('package_id', Integer, primary_key=True)
	CategoryId = Column('category_id', Integer, ForeignKey('categories.category_id'))
	Package = Column('package',String(150))
	RepoId = Column('repo_id', Integer, ForeignKey('repos.repo_id'))
	Active = Column('active', Boolean, default=False)
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'packages'

class Emails(Base):
	EmailId = Column('email_id', Integer, primary_key=True)
	Email = Column('email', String(150))
	__tablename__ = 'emails'

class PackagesEmails(Base):
	Id = Column('id', Integer, primary_key=True)
	PackageId = Column('package_id', Integer, ForeignKey('packages.package_id'))
	EmailId = Column('email_id', Integer, ForeignKey('emails.email_id'))
	__tablename__ = 'packages_emails'

class PackagesMetadata(Base):
	Id = Column('id', Integer, primary_key=True)
	PackageId = Column('package_id', Integer, ForeignKey('packages.package_id'))
	Gitlog = Column('gitlog', Text)
	Descriptions = Column('descriptions', Text)
	New = Column('new', Boolean, default=False)
	__tablename__ = 'packages_metadata'

class Ebuilds(Base):
	EbuildId = Column('ebuild_id', Integer, primary_key=True)
	PackageId = Column('package_id', Integer, ForeignKey('packages.package_id'))
	Version = Column('version', String(150))
	Checksum = Column('checksum', String(100))
	Active = Column('active', Boolean, default=False)
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'ebuilds'

class EmergeOptions(Base):
	EmergeOptionId = Column('eoption_id', Integer, primary_key=True)
	EOption = Column('eoption', String(45))
	__tablename__ = 'emerge_options'

class ConfigsEmergeOptions(Base):
	ConfigId = Column('config_id', Integer, ForeignKey('configs.config_id'), primary_key=True)
	EOptionId = Column('eoption_id', Integer, ForeignKey('emerge_options.eoption_id'))
	__tablename__ = 'configs_emerge_options'

class BuildJobs(Base):
	BuildJobId = Column('build_job_id', Integer, primary_key=True)
	EbuildId = Column('ebuild_id', Integer, ForeignKey('ebuilds.ebuild_id'))
	SetupId = Column('setup_id', Integer, ForeignKey('setups.setup_id'))
	ConfigId = Column('config_id', Integer, ForeignKey('configs.config_id'))
	Status = Column('status', Enum('Waiting','Building','Looked',))
	BuildNow = Column('build_now', Boolean, default=False)
	RemoveBin = Column('removebin', Boolean ,default=False)
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'build_jobs'

class BuildJobsEmergeOptions(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildJobId = Column('build_job_id', Integer, ForeignKey('build_jobs.build_job_id'))
	EOption = Column('eoption_id', Integer, ForeignKey('emerge_options.eoption_id'))
	__tablename__ = 'build_jobs_emerge_options'

class BuildJobsRedo(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildJobId = Column('build_job_id', Integer, ForeignKey('build_jobs.build_job_id'))
	FailTimes = Column('fail_times', Integer)
	FailType = Column('fail_type', String(50))
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'build_jobs_redo'

class Uses(Base):
	UseId = Column('use_id', Integer, primary_key=True)
	Flag = Column('flag', String(150))
	__tablename__ = 'uses'

class BuildJobsUse(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildJobId = Column('build_job_id', Integer, ForeignKey('build_jobs.build_job_id'))
	UseId = Column('use_id', Integer, ForeignKey('uses.use_id'))
	Status = Column('status', Boolean, default=False)
	__tablename__ = 'build_jobs_use'

class HiLightCss(Base):
	HiLightCssId = Column('hilight_css_id', Integer, primary_key=True)
	HiLightCssName = Column('hilight_css_name', String(30))
	HiLightCssCollor = Column('hilight_css_collor', String(30))
	__tablename__ = 'hilight_css'

class HiLight(Base):
	HiLightId = Column('hilight_id', Integer, primary_key=True)
	HiLightSearch = Column('hilight_search', String(50))
	HiLightSearchEnd = Column('hilight_search_end', String(50))
	HiLightSearchPattern = Column('hilight_search_pattern', String(50))
	HiLightCssId = Column('hilight_css_id', Integer, ForeignKey('hilight_css.hilight_css_id'))
	HiLightStart = Column('hilight_start', Integer)
	HiLightEnd = Column('hilight_end', Integer)
	__tablename__ = 'hilight'

class BuildLogs(Base):
	BuildLogId = Column('build_log_id', Integer, primary_key=True)
	EbuildId = Column('ebuild_id', Integer, ForeignKey('ebuilds.ebuild_id'))
	Fail = Column('fail', Boolean, default=False)
	SummeryText = Column('summery_text', Text)
	LogHash = Column('log_hash', String(100))
	BugId = Column('bug_id', Integer, default=0)
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'build_logs'

class EmergeInfo(Base):
	EInfoId = Column('einfo_id', Integer, primary_key=True)
	EmergeInfoText = Column('emerge_info_text', Text)
	__tablename__ = 'emerge_info'

class BuildLogsConfig(Base):
	LogId = Column('log_id', Integer, primary_key=True)
	BuildLogId = Column('build_log_id', Integer, ForeignKey('build_logs.build_log_id'))
	ConfigId = Column('config_id', Integer, ForeignKey('configs.config_id'))
	EInfoId = Column('einfo_id', Integer, ForeignKey('emerge_info.einfo_id'))
	LogName = Column('logname', String(450))
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__  = 'build_logs_config'

class BuildLogsHiLight(Base):
	BuildLogHiLightId = Column('id', Integer, primary_key=True)
	LogId = Column('log_id', Integer, ForeignKey('build_logs_config.log_id'))
	StartLine = Column('start_line', Integer)
	EndLine = Column('end_line', Integer)
	HiLightCssId = Column('hilight_css_id', Integer, ForeignKey('hilight_css.hilight_css_id'))
	__tablename__ = 'build_logs_hilight'

class BuildLogsEmergeOptions(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildLogId = Column('build_log_id', Integer, ForeignKey('Build_logs.Build_log_id'))
	EmergeOptionId = Column('eoption_id', Integer, ForeignKey('emerge_options.eoption_id'))
	__tablename__ = 'build_logs_emerge_options'

class BuildLogsUse(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildLogId = Column('build_log_id', Integer, ForeignKey('build_logs.build_log_id'))
	UseId = Column('use_id', Integer, ForeignKey('uses.use_id'))
	Status = Column('status', Boolean, default=False)
	__tablename__ = 'build_logs_use'

class BuildLogsRepoman(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildLogId = Column('build_log_id', Integer, ForeignKey('build_logs.build_log_id'))
	SummeryText = Column('summery_text', Text)
	__tablename__ = 'build_logs_repoman'

class BuildLogsQa(Base):
	Id = Column('id', Integer, primary_key=True)
	BuildLogId = Column('build_log_id', Integer, ForeignKey('build_logs.build_log_id'))
	SummeryText = Column('summery_text', Text)
	__tablename__ = 'build_logs_qa'

class PackagesRepoman(Base):
	Id = Column('id', Integer, primary_key=True)
	PackageId = Column('package_id', Integer, ForeignKey('packages.package_id'))
	RepomanText = Column('repoman_text', Text)
	RepomanHash = Column('repoman_hash', String(100))
	TimeStamp = Column('time_stamp', DateTime, nullable=False, default=datetime.datetime.utcnow)
	__tablename__ = 'packages_repoman'

class ErrorsInfo(Base):
	ErrorId = Column('error_id', Integer, primary_key=True)
	ErrorName = Column('error_name', String)
	ErrorSearch = Column('error_search', String)
	__tablename__ = 'errors_info'

class BuildLogsErrors(Base):
	BuildLogErrorId =  Column('id', Integer, primary_key=True)
	BuildLogId = Column('build_log_id', Integer, ForeignKey('build_logs.build_log_id'))
	ErrorId = Column('error_id', Integer, ForeignKey('errors_info.error_id'))
	__tablename__ = 'build_logs_errors'

class Restrictions(Base):
	RestrictionId = Column('restriction_id', Integer, primary_key=True)
	Restriction = Column('restriction', String(150))
	__tablename__ = 'restrictions'

class EbuildsRestrictions(Base):
	Id =  Column('id', Integer, primary_key=True)
	EbuildId = Column('ebuild_id', ForeignKey('ebuilds.ebuild_id'))
	RestrictionId = Column('restriction_id', ForeignKey('restrictions.restriction_id'))
	__tablename__ = 'ebuilds_restrictions'

class EbuildsIUse(Base):
	Id =  Column('id', Integer, primary_key=True)
	EbuildId = Column('ebuild_id', ForeignKey('ebuilds.ebuild_id'))
	UseId = Column('use_id', ForeignKey('uses.use_id'))
	Status = Column('status', Boolean, default=False)
	__tablename__= 'ebuilds_iuse'

class EbuildsKeywords(Base):
	Id =  Column('id', Integer, primary_key=True)
	EbuildId = Column('ebuild_id', ForeignKey('ebuilds.ebuild_id'))
	KeywordId = Column('keyword_id', ForeignKey('keywords.keyword_id'))
	Status = Column('status', Enum('Stable','Unstable','Negative'))
	__tablename__ = 'ebuilds_keywords'

class EbuildsMetadata(Base):
	Id =  Column('id', Integer, primary_key=True)
	EbuildId = Column('ebuild_id', ForeignKey('ebuilds.ebuild_id'))
	Commit = Column('commit', String(100))
	New = Column('new', Boolean, default=False)
	Updated = Column('updated', Boolean, default=False)
	Descriptions = Column('descriptions', Text)
	__tablename__ = 'ebuilds_metadata'

class TbcConfig(Base):
	Id =  Column('id', Integer, primary_key=True)
	WebIrker = Column('webirker', String)
	HostIrker = Column('hostirker', String)
	WebBug = Column('webbug', String)
	__tablename__ = 'tbc_config'
