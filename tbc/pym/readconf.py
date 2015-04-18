# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import os
import sys
import re
from socket import getfqdn

class get_conf_settings(object):
# open the /etc/tbc/tbc.conf file and get the needed
# settings for tbc
	def __init__(self):
		self.configfile = "/etc/tbc/tbc.conf"

	def read_tbc_settings_all(self):
	# It will return a dict with options from the configfile
		try:
			open_conffile = open(self.configfile, 'r')
		except:
			sys.exit("Fail to open config file:" + self.configfile)
		textlines = open_conffile.readlines()
		for line in textlines:
			element = line.split('=')
			if element[0] == 'SQLBACKEND':		# Databas backend
				get_sql_backend = element[1]
			if element[0] == 'SQLDB':			# Database
				get_sql_db = element[1]
			if element[0] == 'SQLHOST':			# Host
				get_sql_host = element[1]
			if element[0] == 'SQLUSER':			# User
				get_sql_user = element[1]
			if element[0] == 'SQLPASSWD':		# Password
				get_sql_passwd = element[1]
			# Buildhost root (dir for host/setup on host)
			if element[0] == 'ZOBCSGITREPONAME':
				get_tbc_gitreponame = element[1]
			# Buildhost setup (host/setup on guest)
			if element[0] == 'ZOBCSCONFIG':
				get_tbc_config = element[1]
			# if element[0] == 'LOGFILE':
			#	get_tbc_logfile = element[1]
		open_conffile.close()

		tbc_settings_dict = {}
		tbc_settings_dict['sql_backend'] = get_sql_backend.rstrip('\n')
		tbc_settings_dict['sql_db'] = get_sql_db.rstrip('\n')
		tbc_settings_dict['sql_host'] = get_sql_host.rstrip('\n')
		tbc_settings_dict['sql_user'] = get_sql_user.rstrip('\n')
		tbc_settings_dict['sql_passwd'] = get_sql_passwd.rstrip('\n')
		tbc_settings_dict['tbc_gitreponame'] = get_tbc_gitreponame.rstrip('\n')
		tbc_settings_dict['tbc_config'] = get_tbc_config.rstrip('\n')
		tbc_settings_dict['hostname'] = getfqdn()
		# tbc_settings_dict['tbc_logfile'] = get_tbc_logfile.rstrip('\n')
		return tbc_settings_dict

def read_config_settings():
	reader = get_conf_settings()
	return reader.read_tbc_settings_all()
