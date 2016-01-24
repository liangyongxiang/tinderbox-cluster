# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import os
import sys
import re
from socket import getfqdn

configfile = "/etc/tbc/tbc.conf"

def read_config_settings():
# It will return a dict with options from the configfile
	log_file= False
	tbc_settings = {}
	try:
		open_conffile = open(configfile, 'r')
	except:
		sys.exit("Fail to open config file:" + configfile)
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
		if element[0] == 'LOG':		# Log level
			tbc_settings['log_level'] = element[1].rstrip('\n')
		if element[0] == 'LOGFILE':		# Log level
			log_file = element[1].rstrip('\n')
	open_conffile.close()

	tbc_settings['sql_backend'] = get_sql_backend.rstrip('\n')
	tbc_settings['sql_db'] = get_sql_db.rstrip('\n')
	tbc_settings['sql_host'] = get_sql_host.rstrip('\n')
	tbc_settings['sql_user'] = get_sql_user.rstrip('\n')
	tbc_settings['sql_passwd'] = get_sql_passwd.rstrip('\n')
	tbc_settings['hostname'] = getfqdn()
	tbc_settings['log_file'] = log_file
	return tbc_settings
