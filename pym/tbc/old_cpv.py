# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import logging
from tbc.readconf import get_conf_settings
reader=get_conf_settings()
tbc_settings_dict=reader.read_tbc_settings_all()
# make a CM
from tbc.ConnectionManager import connectionManager
CM=connectionManager(tbc_settings_dict)
#selectively import the pgsql/mysql querys
if CM.getName()=='pgsql':
	from tbc.pgsql_querys import *

class tbc_old_cpv(object):
	
	def __init__(self, myportdb, mysettings):
		self._mysettings = mysettings
		self._myportdb = myportdb

	def mark_old_ebuild_db(self, package_id):
		conn=CM.getConnection()
		# Get the ebuild list for cp
		cp, repo = get_cp_repo_from_package_id(conn, package_id)
		mytree = []
		mytree.append(self._myportdb.getRepositoryPath(repo))
		ebuild_list_tree = self._myportdb.cp_list(cp, use_cache=1, mytree=mytree)
		# Get ebuild list on categories, package in the db
		ebuild_list_db = cp_list_db(conn, package_id)
		# Check if don't have the ebuild in the tree
		# Add it to the no active list
		old_ebuild_list = []
		for ebuild_line in ebuild_list_db:
			cpv_db = cp + "-" + ebuild_line[0]
			if not cpv_db in ebuild_list_tree:
				old_ebuild_list.append(ebuild_line)
			# Set no active on ebuilds in the db that no longer in tree
			if  old_ebuild_list != []:
				for old_ebuild in old_ebuild_list:
					logging.info("O %s/%s-%s", categories, package, old_ebuild[0])
					add_old_ebuild(conn,package_id, old_ebuild_list)
		# Check if we have older no activ ebuilds then 60 days
		ebuild_old_list_db = cp_list_old_db(conn,package_id)
		# Delete older ebuilds in the db
		if ebuild_old_list_db != []:
			for del_ebuild_old in ebuild_old_list_db:
				logging.info("D %s/%s-%s", categories, package, del_ebuild_old[1])
			del_old_ebuild(conn,ebuild_old_list_db)
		CM.putConnection(conn)

	def mark_old_package_db(self, package_id_list_tree):
		conn=CM.getConnection()
		# Get categories/package list from db
		package_list_db = cp_all_db(conn)
		old_package_id_list = []
		# Check if don't have the categories/package in the tree
		# Add it to the no active list
		for package_line in package_list_db:
			if not package_line in package_id_list_tree:
				old_package_id_list.append(package_line)
		# Set no active on categories/package and ebuilds in the db that no longer in tree
		if old_package_id_list != []:
			mark_old_list = add_old_package(conn,old_package_id_list)
			if mark_old_list != []:
				for x in mark_old_list:
					element = get_cp_from_package_id(conn,x)
					logging.info("O %s", element[0])
		# Check if we have older no activ categories/package then 60 days
		del_package_id_old_list = cp_all_old_db(conn,old_package_id_list)
		# Delete older  categories/package and ebuilds in the db
		if del_package_id_old_list != []:
			for i in del_package_id_old_list:
				element = get_cp_from_package_id(conn,i)
				logging.info("D %s", element)
			del_old_package(conn,del_package_id_old_list)
		CM.putConnection(conn)
		
	def mark_old_categories_db(self):
		conn=CM.getConnection()
		# Get categories list from the tree and db
		categories_list_tree = self._mysettings.categories
		categories_list_db =get_categories_db(conn)
		categories_old_list = []
		# Check if don't have the categories in the tree
		# Add it to the no active list
		for categories_line in categories_list_db:
			if not categories_line[0] in categories_list_tree:
				old_c = get_old_categories(conn,categories_line[0])
				if old_c is not None:
					categories_old_list.append(categories_line)
		# Delete older  categories in the db
		if categories_old_list != []:
			for real_old_categories in categories_old_list:
				del_old_categories(conn,real_old_categoriess)
				logging.info("D %s", real_old_categories)
		CM.putConnection(conn)