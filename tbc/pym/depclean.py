# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
from portage._sets.base import InternalPackageSet
from _emerge.main import parse_opts
from tbc.actions import load_emerge_config, action_depclean, calc_depclean

def do_depclean():
	mysettings, mytrees, mtimedb = load_emerge_config()
	myroot = mysettings["ROOT"]
	root_config = mytrees[myroot]["root_config"]
	psets = root_config.setconfig.psets
	args_set = InternalPackageSet(allow_repo=True)
	spinner=None
	scheduler=None
	tmpcmdline = []
	tmpcmdline.append("--depclean")
	tmpcmdline.append("--pretend")
	print("depclean",tmpcmdline)
	myaction, myopts, myfiles = parse_opts(tmpcmdline, silent=False)
	if myfiles:
		args_set.update(myfiles)
		matched_packages = False
		for x in args_set:
			if vardb.match(x):
				matched_packages = True
		if not matched_packages:
			return 0

	rval, cleanlist, ordered, req_pkg_count, unresolvable = calc_depclean(mysettings, mytrees, mtimedb["ldpath"], myopts, myaction, args_set, spinner)
	print('rval, cleanlist, ordered, req_pkg_count, unresolvable', rval, cleanlist, ordered, req_pkg_count, unresolvable)
	if unresolvable != []:
		return True
	if cleanlist != []:
		conflict_package_list = []
		for depclean_cpv in cleanlist:
			if portage.versions.cpv_getkey(depclean_cpv) in list(psets["system"]):
				conflict_package_list.append(depclean_cpv)
			if portage.versions.cpv_getkey(depclean_cpv) in list(psets['selected']):
				conflict_package_list.append(depclean_cpv)
		print('conflict_package_list', conflict_package_list)
		if conflict_package_list == []:
			tmpcmdline = []
			tmpcmdline.append("--depclean")
			myaction, myopts, myfiles = parse_opts(tmpcmdline, silent=False)
			rval = action_depclean(mysettings, mytrees, mtimedb["ldpath"], myopts, myaction, myfiles, spinner, scheduler=None)
			return True
		else:
			print("conflicting packages: %s", conflict_package_list)
			return True
	return True
