# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
from tbc.sync import git_repo_sync_main
#from tbc.buildquerydb import add_buildquery_main, del_buildquery_main
from tbc.updatedb import update_db_main
from tbc.sqlquerys import get_config_id, add_logs, get_jobs, update_job_list

def jobs_main(session, config_id):
	JobsInfo = get_jobs(session, config_id)
	if JobsInfo is None:
		return
	for JobInfo in JobsInfo:
		job = JobInfo.JobType
		run_config_id = JobInfo.RunConfigId
		job_id = JobInfo.JobId
		log_msg = "Job: %s Type: %s" % (job_id, job,)
		add_logs(session, log_msg, "info", config_id)
		if job == "addbuildquery":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_logs(session, log_msg, "info", config_id)
			#result =  add_buildquery_main(run_config_id)
			#if result is True:
			#	update_job_list(session, "Done", job_id)
			#	log_msg = "Job %s is done.." % (job_id,)
			#	add_logs(session, log_msg, "info", config_id)
			#else:
			#	update_job_list(session, "Fail", job_id)
			#	log_msg = "Job %s did fail." % (job_id,)
			#	add_logs(session, log_msg, "info", config_id)
		elif job == "delbuildquery":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_logs(session, log_msg, "info", config_id)
			#result =  del_buildquery_main(config_id)
			#if result is True:
			#	update_job_list(session, "Done", job_id)
			#	log_msg = "Job %s is done.." % (job_id,)
			#	add_logs(session, log_msg, "info", config_id)
			#else:
			#	update_job_list(session, "Fail", job_id)
			#	log_msg = "Job %s did fail." % (job_id,)
			#	add_logs(session, log_msg, "info", config_id)
		elif job == "esync":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_logs(session, log_msg, "info", config_id)
			if update_db_main(session, git_repo_sync_main(session), config_id):
				update_job_list(session, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_logs(session, log_msg, "info", config_id)
		elif job == "updatedb":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_logs(session, log_msg, "info", config_id)
			if update_db_main(session, None, config_id):
				update_job_list(session, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_logs(session, log_msg, "info", config_id)
	return
