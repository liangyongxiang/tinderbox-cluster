# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

# Origin flags.py from portage public api repo
from __future__ import print_function
import portage
import os

class tbc_use_flags(object):
	
	def __init__(self, mysettings, myportdb, cpv):
		self._mysettings = mysettings
		self._myportdb = myportdb
		self._cpv = cpv
	
	def get_iuse(self):
		"""Gets the current IUSE flags from the tree
		To be used when a gentoolkit package object is not needed
		@type: cpv: string 
		@param cpv: cat/pkg-ver
		@rtype list
		@returns [] or the list of IUSE flags
		"""
		return self._myportdb.aux_get(self._cpv, ["IUSE"])[0].split()
		
	def reduce_flag(self, flag):
		"""Absolute value function for a USE flag
		@type flag: string
		@param flag: the use flag to absolute.
		@rtype: string
		@return absolute USE flag
		"""
		if flag[0] in ["+","-"]:
			return flag[1:]
		else:
			return flag

	def reduce_flags(self, the_list):
		"""Absolute value function for a USE flag list
		@type the_list: list
		@param the_list: the use flags to absolute.
		@rtype: list
		@return absolute USE flags
		"""
		r=[]
		for member in the_list:
			r.append(self.reduce_flag(member))
		return r

	def filter_flags(self, use, use_expand_hidden, usemasked, useforced):
		"""Filter function to remove hidden or otherwise not normally
		visible USE flags from a list.
		@type use: list
		@param use: the USE flag list to be filtered.
		@type use_expand_hidden: list
		@param  use_expand_hidden: list of flags hidden.
		@type usemasked: list
		@param usemasked: list of masked USE flags.
		@type useforced: list
		@param useforced: the forced USE flags.
		@rtype: list
		@return the filtered USE flags.
		"""
		# clean out some environment flags, since they will most probably
		# be confusing for the user
		for f in use_expand_hidden:
			f=f.lower() + "_"
			for x in use:
				if f in x:
					use.remove(x)
		# clean out any arch's
		archlist = self._mysettings["PORTAGE_ARCHLIST"].split()
		for a in use[:]:
			if a in archlist:
				use.remove(a)
		# clean out any abi_ flag
		for a in use[:]:
			if a.startswith("abi_"):
				use.remove(a)
		# clean out any python_ flag
		for a in use[:]:
			if a.startswith("python_"):
				use.remove(a)

		# dbl check if any from usemasked  or useforced are still there
		masked = usemasked + useforced
		for a in use[:]:
			if a in masked:
				use.remove(a)
		return use

	def get_all_cpv_use(self):
		"""Uses portage to determine final USE flags and settings for an emerge
		@type cpv: string
		@param cpv: eg cat/pkg-ver
		@rtype: lists
		@return  use, use_expand_hidden, usemask, useforce
		"""
		use = None
		self._mysettings.unlock()
		try:
			self._mysettings.setcpv(self._cpv, use_cache=None, mydb=self._myportdb)
			use = self._mysettings['PORTAGE_USE'].split()
			use_expand_hidden = self._mysettings["USE_EXPAND_HIDDEN"].split()
			usemask = list(self._mysettings.usemask)
			useforce =  list(self._mysettings.useforce)
		except KeyError:
			self._mysettings.reset()
			self._mysettings.lock()
			return [], [], [], []
		# reset cpv filter
		self._mysettings.reset()
		self._mysettings.lock()
		return use, use_expand_hidden, usemask, useforce

	def get_all_cpv_use_looked(self):
		"""Uses portage to determine final USE flags and settings for an emerge
		@type cpv: string
		@param cpv: eg cat/pkg-ver
		@rtype: lists
		@return  use, use_expand_hidden, usemask, useforce
		"""
		# use = self._mysettings['PORTAGE_USE'].split()
		use = os.environ['USE'].split()
		use_expand_hidden = self._mysettings["USE_EXPAND_HIDDEN"].split()
		usemask = list(self._mysettings.usemask)
		useforce = list(self._mysettings.useforce)
		return use, use_expand_hidden, usemask, useforce

	def get_all_cpv_use_pkg(self, pkg, settings):
		"""Uses portage to determine final USE flags and settings for an emerge
		@type cpv: string
		@param cpv: eg cat/pkg-ver
		@rtype: lists
		@return  use, use_expand_hidden, usemask, useforce
		"""
		# use = self._mysettings['PORTAGE_USE'].split()
		use_list = list(pkg.use.enabled)
		use_expand_hidden = settings["USE_EXPAND_HIDDEN"].split()
		usemask = list(settings.usemask)
		useforced = list(settings.useforce)
		return use_list, use_expand_hidden, usemask, useforced

	def get_flags(self):
		"""Retrieves all information needed to filter out hidden, masked, etc.
		USE flags for a given package.

		@type cpv: string
		@param cpv: eg. cat/pkg-ver
		@type final_setting: boolean
		@param final_setting: used to also determine the final
		enviroment USE flag settings and return them as well.
		@rtype: list or list, list
		@return IUSE or IUSE, final_flags
		"""
		final_use, use_expand_hidden, usemasked, useforced = self.get_all_cpv_use()
		iuse_flags = self.filter_flags(self.get_iuse(), use_expand_hidden, usemasked, useforced)
		#flags = filter_flags(use_flags, use_expand_hidden, usemasked, useforced)
		final_flags = self.filter_flags(final_use, use_expand_hidden, usemasked, useforced)
		return iuse_flags, final_flags, usemasked

	def get_flags_looked(self):
		"""Retrieves all information needed to filter out hidden, masked, etc.
		USE flags for a given package.

		@type cpv: string
		@param cpv: eg. cat/pkg-ver
		@type final_setting: boolean
		@param final_setting: used to also determine the final
		enviroment USE flag settings and return them as well.
		@rtype: list or list, list
		@return IUSE or IUSE, final_flags
		"""
		final_use, use_expand_hidden, usemasked, useforced = self.get_all_cpv_use_looked()
		iuse_flags = self.filter_flags(self.get_iuse(), use_expand_hidden, usemasked, useforced)
		#flags = filter_flags(use_flags, use_expand_hidden, usemasked, useforced)
		final_flags = self.filter_flags(final_use, use_expand_hidden, usemasked, useforced)
		return iuse_flags, final_flags

	def get_flags_pkg(self, pkg, settings):
		"""Retrieves all information needed to filter out hidden, masked, etc.
		USE flags for a given package.
		@type cpv: string
		@param cpv: eg. cat/pkg-ver
		@type final_setting: boolean
		@param final_setting: used to also determine the final
		enviroment USE flag settings and return them as well.
		@rtype: list or list, list
		@return IUSE or IUSE, final_flags
		"""
		final_use, use_expand_hidden, usemasked, useforced = self.get_all_cpv_use_pkg(pkg, settings)
		iuse_flags = self.filter_flags(list(pkg.iuse.all), use_expand_hidden, usemasked, useforced)
		#flags = filter_flags(use_flags, use_expand_hidden, usemasked, useforced)
		final_flags = self.filter_flags(final_use, use_expand_hidden, usemasked, useforced)
		return iuse_flags, final_flags

	def comper_useflags(self, build_dict):
		iuse_flags, use_enable = self.get_flags()
		iuse = []
		build_use_flags_dict = build_dict['build_useflags']
		build_use_flags_list = []
		if use_enable == []:
			if build_use_flags_dict is None:
				return None
		for iuse_line in iuse_flags:
			iuse.append(self.reduce_flag(iuse_line))
		iuse_flags_list = list(set(iuse))
		use_disable = list(set(iuse_flags_list).difference(set(use_enable)))
		use_flagsDict = {}
		for x in use_enable:
			use_flagsDict[x] = True
		for x in use_disable:
			use_flagsDict[x] = False
		for k, v in use_flagsDict.items():
			if build_use_flags_dict[k] != v:
				if build_use_flags_dict[k]:
					build_use_flags_list.append(k)
				else:
					build_use_flags_list.append("-" + k)
		if build_use_flags_list == []:
			build_use_flags_list = None
		return build_use_flags_list
