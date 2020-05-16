# Copyright 1998-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os

from portage import _trees_dict, const
import portage.proxy.lazyimport
import portage.proxy as proxy
proxy.lazyimport.lazyimport(globals(),
    'gosbs.portage.dbapi.bintree:bindbapi,binarytree',
    'portage.package.ebuild.config:autouse,best_from_dict,' + \
        'check_config_instance,config',
    'portage.dbapi.vartree:dblink,merge,unmerge,vardbapi,vartree',
    'portage.dbapi.porttree:close_portdbapi_caches,FetchlistDict,' + \
        'portagetree,portdbapi',
    
    )

def create_trees(config_root=None, target_root=None, trees=None, env=None,
    sysroot=None, eprefix=None):

    if trees is None:
        trees = _trees_dict()
    elif not isinstance(trees, _trees_dict):
        # caller passed a normal dict or something,
        # but we need a _trees_dict instance
        trees = _trees_dict(trees)

    if env is None:
        env = os.environ

    settings = config(config_root=config_root, target_root=target_root,
        env=env, sysroot=sysroot, eprefix=eprefix)
    settings.lock()

    depcachedir = settings.get('PORTAGE_DEPCACHEDIR')
    trees._target_eroot = settings['EROOT']
    myroots = [(settings['EROOT'], settings)]
    if settings["ROOT"] == "/" and settings["EPREFIX"] == const.EPREFIX:
        trees._running_eroot = trees._target_eroot
    else:

        # When ROOT != "/" we only want overrides from the calling
        # environment to apply to the config that's associated
        # with ROOT != "/", so pass a nearly empty dict for the env parameter.
        clean_env = {}
        for k in ('PATH', 'PORTAGE_GRPNAME', 'PORTAGE_REPOSITORIES', 'PORTAGE_USERNAME',
            'PYTHONPATH', 'SSH_AGENT_PID', 'SSH_AUTH_SOCK', 'TERM',
            'ftp_proxy', 'http_proxy', 'https_proxy', 'no_proxy',
            '__PORTAGE_TEST_HARDLINK_LOCKS'):
            v = settings.get(k)
            if v is not None:
                clean_env[k] = v
        if depcachedir is not None:
            clean_env['PORTAGE_DEPCACHEDIR'] = depcachedir
        settings = config(config_root=None, target_root="/",
            env=clean_env, sysroot="/", eprefix=None)
        settings.lock()
        trees._running_eroot = settings['EROOT']
        myroots.append((settings['EROOT'], settings))

    for myroot, mysettings in myroots:
        trees[myroot] = portage.util.LazyItemsDict(trees.get(myroot, {}))
        trees[myroot].addLazySingleton("virtuals", mysettings.getvirtuals)
        trees[myroot].addLazySingleton(
            "vartree", vartree, categories=mysettings.categories,
                settings=mysettings)
        trees[myroot].addLazySingleton("porttree",
            portagetree, settings=mysettings)
        trees[myroot].addLazySingleton("bintree",
            binarytree, pkgdir=mysettings["PKGDIR"], settings=mysettings)
    return trees
