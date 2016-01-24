# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import logging
module_logger = logging.getLogger('tbc.log')

def setup_logger( tbc_settings):
	# setupt the logger
	log_level = getattr(logging, tbc_settings['log_level'].upper(), None)
	format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	if not isinstance(log_level, int):
		raise ValueError('Invalid log level: %s' % tbc_settings['log_level'])
	logging.basicConfig()
	logger = logging.getLogger('tbc')
	logger.setLevel(log_level)
	if tbc_settings['log_file']:
		fh = logging.FileHandler(tbc_settings['log_file'])
	else:
		fh = logging.StreamHandler()
	formatter = logging.Formatter(format)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	return logger

def write_log(session, msg, level, config_id, function=False):
	if function:
		logger = logging.getLogger('tbc.' + function)
	else:
		logger = logging.getLogger('tbc')
	if level == 'info':
		logger.info(msg)
	if level == 'error':
		logger.error(msg)
	if level == 'debug':
		logger.debug(msg)
	if level == 'warning':
		logger.warning(msg)
