# Copyright 1998-2020 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from _emerge.create_depgraph_params import create_depgraph_params
from _emerge.depgraph import backtrack_depgraph
import portage
portage.proxy.lazyimport.lazyimport(globals(),
    'gosbs._emerge.actions:load_emerge_config',
)
from portage.exception import PackageSetNotFound

from oslo_log import log as logging
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def build_mydepgraph(settings, trees, mtimedb, myopts, myparams, myaction, myfiles, spinner, build_job, context):
    try:
        success, mydepgraph, favorites = backtrack_depgraph(
        settings, trees, myopts, myparams, myaction, myfiles, spinner)
    except portage.exception.PackageSetNotFound as e:
        root_config = trees[settings["ROOT"]]["root_config"]
        display_missing_pkg_set(root_config, e.value)
        LOG.error('Dependencies fail')
    else:
        if not success:
            repeat = True
            repeat_times = 0
            while repeat:
                if mydepgraph._dynamic_config._needed_p_mask_changes:
                    LOG.debug('Mask package or dep')
                elif mydepgraph._dynamic_config._needed_use_config_changes:
                    mydepgraph._display_autounmask()
                    LOG.debug('Need use change')
                elif mydepgraph._dynamic_config._slot_conflict_handler:
                    LOG.debug('Slot blocking')
                elif mydepgraph._dynamic_config._circular_deps_for_display:
                    LOG.debug('Circular Deps')
                elif mydepgraph._dynamic_config._unsolvable_blockers:
                    LOG.debug('Blocking packages')
                else:
                    LOG.debug('Dep calc fail')
                mydepgraph.display_problems()
                if repeat_times is 2:
                    repeat = False
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
