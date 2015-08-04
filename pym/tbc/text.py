# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import sys
import re
import os
import errno
from portage.util import grablines

def  get_file_text(filename):
	# Return the filename contents
	try:
		textfile = open(filename, encoding='utf-8')
	except:
		return "No file", filename
	text = ""
	for line in textfile:
		text += line
	textfile.close()
	return text

def  get_ebuild_cvs_revision(filename):
	"""Return the ebuild contents"""
	try:
		ebuildfile = open(filename, encoding='utf-8')
	except:
		return "No Ebuild file there"
	text = ""
	dataLines = ebuildfile.readlines()
	for i in dataLines:
		text = text + i + " "
	line2 = dataLines[2]
	field = line2.split(" ")
	ebuildfile.close()
	try:
		cvs_revision = field[3]
	except:
		cvs_revision = ''
	return cvs_revision

def  get_log_text_dict(filename):
	"""Return the log contents as a dict"""
	logfile_dict = {}
	index = 1
	for text_line in grablines(filename):
		logfile_dict[index] = text_line
		index = index + 1
	return logfile_dict, index - 1
