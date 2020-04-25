# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from _emerge.clear_caches import clear_caches
from _emerge.main import parse_opts
from _emerge.unmerge import unmerge
import portage
from portage._sets.base import InternalPackageSet
from portage.util._async.SchedulerInterface import SchedulerInterface
from portage.util._eventloop.global_event_loop import global_event_loop

from oslo_log import log as logging
from gosbs._emerge.actions import load_emerge_config, action_depclean, calc_depclean
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def do_depclean(context):
    mysettings, mytrees, mtimedb = load_emerge_config()
    root_config = mytrees[mysettings['EROOT']]['root_config']
    vardb = root_config.trees['vartree'].dbapi
    psets = root_config.setconfig.psets
    args_set = InternalPackageSet(allow_repo=True)
    spinner=None
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
    clear_caches(mytrees)
    if unresolvable != []:
        return True
    if cleanlist != []:
        conflict_package_list = []
        max_jobs = myopts.get("--jobs", 1)
        background = (max_jobs is True or max_jobs > 1 or
            "--quiet" in myopts or myopts.get("--quiet-build") == "y")
        sched_iface = SchedulerInterface(global_event_loop(),
            is_background=lambda: background)

        if background:
            settings.unlock()
            settings["PORTAGE_BACKGROUND"] = "1"
            settings.backup_changes("PORTAGE_BACKGROUND")
            settings.lock()

        for depclean_cpv in cleanlist:
            if portage.versions.cpv_getkey(depclean_cpv) in list(psets["system"]):
                conflict_package_list.append(depclean_cpv)
            if portage.versions.cpv_getkey(depclean_cpv) in list(psets['selected']):
                conflict_package_list.append(depclean_cpv)
        print('conflict_package_list', conflict_package_list)
        if conflict_package_list == []:
            rval = unmerge(root_config, myopts, "unmerge", cleanlist, mtimedb["ldpath"], ordered=ordered, scheduler=sched_iface)
        set_atoms = {}
        for k in ("profile", "system", "selected"):
            try:
                set_atoms[k] = root_config.setconfig.getSetAtoms(k)
            except portage.exception.PackageSetNotFound:
                # A nested set could not be resolved, so ignore nested sets.
                set_atoms[k] = root_config.sets[k].getAtoms()

        print("Packages installed:   " + str(len(vardb.cpv_all())))
        print("Packages in world:    %d" % len(set_atoms["selected"]))
        print("Packages in system:   %d" % len(set_atoms["system"]))
        if set_atoms["profile"]:
            print("Packages in profile:  %d" % len(set_atoms["profile"]))
        print("Required packages:    "+str(req_pkg_count))
        print("Number removed:       "+str(len(cleanlist)))
    return True
