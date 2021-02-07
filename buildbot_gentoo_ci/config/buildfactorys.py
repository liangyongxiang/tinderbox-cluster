# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import steps as buildbot_steps
from buildbot.plugins import util

from buildbot_gentoo_ci.steps import update_db
from buildbot_gentoo_ci.steps import category
from buildbot_gentoo_ci.steps import package
from buildbot_gentoo_ci.steps import version
from buildbot_gentoo_ci.steps import builders

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
    # Trigger new builders with v from cpv
    #   return package_data, cpv, repository_data, project_data, config_root
    f.addStep(package.TriggerCheckVGentooCiProject())
    return f

def update_db_v():
    f = util.BuildFactory()
    # FIXME: 3
    # if version in db
    #   return version_data
    f.addStep(version.GetVData())
    #   check path and hash
    f.addStep(version.CheckPathHash())
    #   if not path
    #       if not hash
    #           add deleted stage att end
    #           add version to db stage
    #           add version metadata to db
    #           add version to build check
    #   else
    #       add deleted stage att end
    #       add version to build check stage att end
    # else
    #   add version to db
    #   add version metadata to db
    #   add version to build check
    f.addStep(version.CheckV())
    return f

def build_request_check():
    f = util.BuildFactory()
    # FIXME: 4
    # get project_data
    # check what tests to do
    # triggger build request
    f.addStep(builders.GetProjectRepositoryData())
    return f

def run_build_request():
    f = util.BuildFactory()
    # FIXME: 5
    # Move the etc/portage stuff to is own file
    # set needed Propertys
    f.addStep(builders.SetupPropertys())
    # Clean and add new /etc/portage
    f.addStep(buildbot_steps.RemoveDirectory(dir="portage",
                                workdir='/etc/'))
    f.addStep(buildbot_steps.MakeDirectory(dir="portage",
                                workdir='/etc/'))
    # setup the profile
    f.addStep(buildbot_steps.MakeDirectory(dir="make.profile",
                                workdir='/etc/portage/'))
    f.addStep(builders.SetMakeProfile())
    # setup repos.conf dir
    f.addStep(buildbot_steps.MakeDirectory(dir="repos.conf",
                                workdir='/etc/portage/'))
    f.addStep(builders.SetReposConf())
    # update the repositorys listed in project_repository
    f.addStep(builders.UpdateRepos())
    # setup make.conf
    f.addStep(builders.SetMakeConf())
    # setup package.*
    #f.addStep(portages.SetPackageUse())
    # setup env
    # setup files in /etc if needed
    # run --regen if needed on repo
    # update packages before any tests
    # run pretend on packages update on worker
    shell_commad_list = [
                    'emerge',
                    '-uDNv',
                    '--changed-deps',
                    '--changed-use',
                    '--pretend',
                    '@world'
                    ]
    f.addStep(buildbot_steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=builders.PersOutputOfEmerge,
                        workdir='/'
                        ))
    #   look at the log to see if we need to do stuff
    #   run update package on worker
    #   check log
    # run pretend @preserved-rebuild if needed
    #   look at the log to see if we need to do stuff
    #   run @preserved-rebuild
    #   check log
    # run depclean if set
    #   depclean pretend
    #   look at the log to see if we need to do stuff
    #   depclean
    #   check log
    # setup make.conf if build id has changes make.conf as dict from SetMakeConf
    # setup package.* env if build id has changes
    return f
