# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
from _emerge.create_depgraph_params import create_depgraph_params
from _emerge.depgraph import backtrack_depgraph
import portage
portage.proxy.lazyimport.lazyimport(globals(),
	'tbc.actions:load_emerge_config',
)
from portage.exception import PackageSetNotFound

from tbc.build_log import log_fail_queru

def build_mydepgraph(settings, trees, mtimedb, myopts, myparams, myaction, myfiles, spinner, build_dict, session):
	try:
		success, mydepgraph, favorites = backtrack_depgraph(
		settings, trees, myopts, myparams, myaction, myfiles, spinner)
	except portage.exception.PackageSetNotFound as e:
		root_config = trees[settings["ROOT"]]["root_config"]
		display_missing_pkg_set(root_config, e.value)
		build_dict['type_fail'] = "depgraph fail\n"
		build_dict['check_fail'] = True
	else:
		if not success:
			repeat = True
			repeat_times = 0
			while repeat:
				if mydepgraph._dynamic_config._needed_p_mask_changes:
					build_dict['type_fail'] = "Mask package or dep\n"
					build_dict['check_fail'] = True
				elif mydepgraph._dynamic_config._needed_use_config_changes:
					mydepgraph._display_autounmask()
					build_dict['type_fail'] = "Need use change\n"
					build_dict['check_fail'] = True
				elif mydepgraph._dynamic_config._slot_conflict_handler:
					build_dict['type_fail'] = "Slot blocking\n"
					build_dict['check_fail'] = True
				elif mydepgraph._dynamic_config._circular_deps_for_display:
					build_dict['type_fail'] = "Circular Deps\n"
					build_dict['check_fail'] = True
				elif mydepgraph._dynamic_config._unsolvable_blockers:
					build_dict['type_fail'] = "Blocking packages\n"
					build_dict['check_fail'] = True
				else:
					build_dict['type_fail'] = "Dep calc fail\n"
					build_dict['check_fail'] = True
				mydepgraph.display_problems()
				if repeat_times is 2:
					repeat = False
					log_fail_queru(session, build_dict, settings)
				else:
					repeat_times = repeat_times + 1
					settings, trees, mtimedb = load_emerge_config()
					myparams = create_depgraph_params(myopts, myaction)
					try:
						success, mydepgraph, favorites = backtrack_depgraph(
						settings, trees, myopts, myparams, myaction, myfiles, spinner)
					except portage.exception.PackageSetNotFound as e:
						root_config = trees[settings["ROOT"]]["root_config"]
						display_missing_pkg_set(root_config, e.value)
					if success:
						repeat = False

	return success, settings, trees, mtimedb, mydepgraph
