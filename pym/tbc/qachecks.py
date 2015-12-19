# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import os
import warnings
import sys
import codecs
from portage import os, _encodings, _unicode_decode
from portage.checksum import _hash_filter
from portage.exception import DigestException, FileNotFound
from portage.localization import _
from portage.manifest import Manifest
from portage import os, _encodings, _unicode_decode, _unicode_encode
from portage.exception import DigestException, FileNotFound, ParseError, PermissionDenied
from _emerge.Package import Package
from _emerge.RootConfig import RootConfig
from repoman.checks.ebuilds.checks import run_checks
from tbc.repoman import repoman_main
from tbc.sqlquerys import get_configmetadata_info, get_config_info, get_setup_info
import portage

def check_file_in_manifest(pkgdir, mysettings, portdb, cpv, build_use_flags_list, repo):
	myfetchlistdict = portage.FetchlistDict(pkgdir, mysettings, portdb)
	my_manifest = portage.Manifest(pkgdir, mysettings['DISTDIR'], fetchlist_dict=myfetchlistdict, manifest1_compat=False, from_scratch=False)
	ebuild_version = portage.versions.cpv_getversion(cpv)
	package = portage.versions.cpv_getkey(cpv).split("/")[1]
	if my_manifest.findFile(package + "-" + ebuild_version + ".ebuild") is None:
		return "Ebuild file not found.\n"
	tree = portdb.getRepositoryPath(repo)
	cpv_fetchmap = portdb.getFetchMap(cpv, useflags=build_use_flags_list, mytree=tree)
	mysettings.unlock()
	try:
		portage.fetch(cpv_fetchmap, mysettings, listonly=0, fetchonly=0, locks_in_subdir='.locks', use_locks=1, try_mirrors=1)
	except:
		mysettings.lock()
		return "Can't fetch the file.\n"
	finally:
		mysettings.lock()
	try:
		my_manifest.checkCpvHashes(cpv, checkDistfiles=True, onlyDistfiles=False, checkMiscfiles=True)
	except:
		return "Can't fetch the file or the hash failed.\n"
	try:
		portdb.fetch_check(cpv, useflags=build_use_flags_list, mysettings=mysettings, all=False)
	except:	
		return "Fetch check failed.\n"
	return

def check_repoman(mysettings, myportdb, cpv, repo):
	# We run repoman run_checks on the ebuild
	ebuild_version_tree = portage.versions.cpv_getversion(cpv)
	element = portage.versions.cpv_getkey(cpv).split('/')
	categories = element[0]
	package = element[1]
	pkgdir = myportdb.getRepositoryPath(repo) + "/" + categories + "/" + package
	full_path = pkgdir + "/" + package + "-" + ebuild_version_tree + ".ebuild"
	root = '/'
	trees = {
	root : {'porttree' : portage.portagetree(root, settings=mysettings)}
	}
	root_config = RootConfig(mysettings, trees[root], None)
	allvars = set(x for x in portage.auxdbkeys if not x.startswith("UNUSED_"))
	allvars.update(Package.metadata_keys)
	allvars = sorted(allvars)
	myaux = dict(zip(allvars, myportdb.aux_get(cpv, allvars, myrepo=repo)))
	pkg = Package(cpv=cpv, metadata=myaux, root_config=root_config, type_name='ebuild')
	fails = []
	try:
		# All ebuilds should have utf_8 encoding.
		f = codecs.open(_unicode_encode(full_path,
		encoding = _encodings['fs'], errors = 'strict'),
		mode = 'r', encoding = _encodings['repo.content'])
		try:
			for check_name, e in run_checks(f, pkg):
				fails.append(check_name + ": " + e + "\n")
		finally:
			f.close()
	except UnicodeDecodeError:
		# A file.UTF8 failure will have already been recorded above.
		pass
	# fails will have a list with repoman errors
	if fails == []:
		return False
	return fails

def repoman_full(session, pkgdir, config_id):
	ConfigsMetaData = get_configmetadata_info(session, config_id)
	ConfigInfo = get_config_info(session, config_id)
	SetupInfo = get_setup_info(session, config_id)
	config_root = ConfigsMetaData.RepoPath + '/' + ConfigInfo.Hostname + "/" + SetupInfo.Setup
	argscmd = []
	argscmd.append('--xmlparse')
	argscmd.append('full')
	qatracker, qawarnings = repoman_main(argscmd, config_root=config_root, pkgdir=pkgdir)
	adict = {}
	for key in qatracker.fails.items():
		alist = []
		for foo in key[1]:
			alist.append(foo)
			adict[key[0]] = alist
	if adict == {}:
		return False
	return adict

