# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import util
    
def f_update_db_packages():
    f = util.BuildFactory()
    return f
