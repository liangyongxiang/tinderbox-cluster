# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
# Origin https://gitweb.gentoo.org/proj/portage.git/tree/pym/portage/api/flag.py?h=public_api

"""Provides support functions for USE flag settings and analysis"""


__all__ = (
    'get_iuse',
    'get_installed_use',
    'reduce_flag',
    'reduce_flags',
    'filter_flags',
    'get_all_cpv_use',
    'get_flags'
)

import portage


def get_iuse(cpv, portdb):
    """Gets the current IUSE flags from the tree

    To be used when a gentoolkit package object is not needed
    @type: cpv: string 
    @param cpv: cat/pkg-ver
    @type root: string
    @param root: tree root to use
    @param settings: optional portage config settings instance.
        defaults to portage.api.settings.default_settings
    @rtype list
    @returns [] or the list of IUSE flags
    """
    return portdb.aux_get(cpv, ["IUSE"])[0].split()


def reduce_flag(flag):
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


def reduce_flags(the_list):
    """Absolute value function for a USE flag list

    @type the_list: list
    @param the_list: the use flags to absolute.
    @rtype: list
    @return absolute USE flags
    """
    reduced = []
    for member in the_list:
        reduced.append(reduce_flag(member))
    return reduced


def filter_flags(use, use_expand_hidden, usemasked,
        useforced, settings):
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
    @param settings: optional portage config settings instance.
        defaults to portage.api.settings.default_settings
    @rtype: list
    @return the filtered USE flags.
    """
    # clean out some environment flags, since they will most probably
    # be confusing for the user
    for flag in use_expand_hidden:
        flag = flag.lower() + "_"
        for expander in use:
            if flag in expander:
                use.remove(expander)
    # clean out any arch's
    archlist = settings["PORTAGE_ARCHLIST"].split()
    for key in use[:]:
        if key in archlist:
            use.remove(key)
    # dbl check if any from usemasked  or useforced are still there
    masked = usemasked + useforced
    for flag in use[:]:
        if flag in masked:
            use.remove(flag)
    # clean out any abi_ flag
    for a in use[:]:
        if a.startswith("abi_"):
            use.remove(a)
    # clean out any python_ flag
    for a in use[:]:
        if a.startswith("python_"):
            use.remove(a)
    # clean out any ruby_targets_ flag
    for a in use[:]:
        if a.startswith("ruby_targets_"):
            use.remove(a)
    return use


def get_all_cpv_use(cpv, portdb, settings):
    """Uses portage to determine final USE flags and settings for an emerge

    @type cpv: string
    @param cpv: eg cat/pkg-ver
    @type root: string
    @param root: tree root to use
    @param settings: optional portage config settings instance.
        defaults to portage.api.settings.default_settings
    @rtype: lists
    @return  use, use_expand_hidden, usemask, useforce
    """
    use = None
    settings.unlock()
    try:
        settings.setcpv(cpv, use_cache=None, mydb=portdb)
        use = settings['PORTAGE_USE'].split()
        use_expand_hidden = settings["USE_EXPAND_HIDDEN"].split()
        usemask = list(settings.usemask)
        useforce =  list(settings.useforce)
    except KeyError:
        settings.reset()
        settings.lock()
        return [], [], [], []
    # reset cpv filter
    settings.reset()
    settings.lock()
    return use, use_expand_hidden, usemask, useforce


def get_flags(cpv, portdb, settings, final_setting=False):
    """Retrieves all information needed to filter out hidden, masked, etc.
    USE flags for a given package.

    @type cpv: string
    @param cpv: eg. cat/pkg-ver
    @type final_setting: boolean
    @param final_setting: used to also determine the final
        enviroment USE flag settings and return them as well.
    @type root: string
    @param root: pass through variable needed, tree root to use
        for other function calls.
    @param settings: optional portage config settings instance.
        defaults to portage.api.settings.default_settings
    @rtype: list or list, list
    @return IUSE or IUSE, final_flags
    """
    (final_use, use_expand_hidden, usemasked, useforced) = \
        get_all_cpv_use(cpv, portdb, settings)
    iuse_flags = filter_flags(get_iuse(cpv), use_expand_hidden,
        usemasked, useforced, settings)
    #flags = filter_flags(use_flags, use_expand_hidden,
        #usemasked, useforced, settings)
    if final_setting:
        final_flags = filter_flags(final_use,  use_expand_hidden,
            usemasked, useforced, settings)
        return iuse_flags, final_flags
    return iuse_flags


def get_use_flag_dict(portdir):
    """ Get all the use flags and return them as a dictionary
    
    @param portdir: the path to the repository
    @rtype dictionary of:
        key = use flag forced to lowercase
        data = list[0] = 'local' or 'global'
            list[1] = 'package-name'
            list[2] = description of flag
    """
    use_dict = {}

    # process standard use flags

    _list = portage.grabfile(portdir + '/profiles/use.desc')
    for item in _list:
        index = item.find(' - ')
        use_dict[item[:index].strip().lower()] = ['global', '', item[index+3:]]

    # process local (package specific) use flags

    _list = portage.grabfile(portdir + '/profiles/use.local.desc')
    for item in _list:
        index = item.find(' - ')
        data = item[:index].lower().split(':')
        try: 
            use_dict[data[1].strip()] = ['local', data[0].strip(), item[index+3:]]
        except:
            pass
            #debug.dprint("FLAG: get_use_flag_dict();"
                #"error in index??? data[0].strip, item[index:]")
            #debug.dprint(data[0].strip())
            #debug.dprint(item[index:])
    return use_dict

def get_build_use(cpv, mysettings, myportdb):
    (final_use, use_expand_hidden, usemasked, useforced) = get_all_cpv_use(cpv, myportdb, mysettings)
    iuse_flags = filter_flags(get_iuse(cpv, myportdb), use_expand_hidden, usemasked, useforced, mysettings)
    final_flags = filter_flags(final_use,  use_expand_hidden, usemasked, useforced, mysettings)
    iuse_flags2 = reduce_flags(iuse_flags)
    iuse_flags_list = list(set(iuse_flags2))
    use_disable = list(set(iuse_flags_list).difference(set(final_flags)))
    use_flagsDict = {}
    for x in final_flags:
        use_flagsDict[x] = True
    for x in use_disable:
        use_flagsDict[x] = False
    return use_flagsDict, usemasked
