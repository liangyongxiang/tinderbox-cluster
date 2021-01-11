# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import steps as buildbot_steps
from buildbot.plugins import util

from buildbot_gentoo_ci.steps import update_db
from buildbot_gentoo_ci.steps import category
from buildbot_gentoo_ci.steps import package

def update_db_check():
    f = util.BuildFactory()
    # FIXME: 1
    # Get base project data from db
    #   return project_repository, profile_repository,
    #       project
    f.addStep(update_db.GetDataGentooCiProject())
    # Check if base project repo is cloned
    # Check if profile repo is cloned
    # check if the profile link is there
    # check if the repository is cloned
    f.addStep(update_db.CheckPathGentooCiProject())
    # check if etc/portage has no error
    #   return config_root
    f.addStep(update_db.CheckProjectGentooCiProject())
    # Make a for loop and trigger new builders with cpv from cpv_changes
    #   return cpv, repository, project_data, config_root
    f.addStep(update_db.CheckCPVGentooCiProject())
    return f

def update_db_cp():
    f = util.BuildFactory()
    # FIXME: 2
    # if categorys in db
    #   return category_data
    #   add check category path step at end
    # else
    #   add category to db step
    #   return category_data
    f.addStep(category.CheckCGentooCiProject())
    # if package in db
    #   return package_data
    #   add check package path step at end
    # else
    #   add package to db step
    #   return package_data
    f.addStep(package.CheckPGentooCiProject())
    # Make a for loop and trigger new builders with v from cpv
    #   return package_data, cpv, repository, project_data, config_root
    #f.addStep(package.TriggerVGentooCiProject())
    return f
