# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import util, steps
    
def f_update_db_packages():
    f = util.BuildFactory()
    # FIXME:
    # Get base project from db
    # Check if base project repo for is cloned
    # Check if gentoo repo is cloned
    # check if the profile link is there
    # check if etc/portage has no error
    # Get the repository some way
    repository=util.Property('repository')
    # For loop
    # for cpv in util.Property('cpv_changes')
    #   check if not categorys in db
    #       run update categorys db step
    #   check if not package in db
    #       run update package db step
    #       and get foo{cpv] with metadata back
    #       if new or updated package
    #   else 
    #       run update package db step in a pool of workers
    #       and get foo{cpv] with metadata back
    #       if new or updated package
    return f
