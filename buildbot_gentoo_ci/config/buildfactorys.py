# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import steps as buildbot_steps
from buildbot.plugins import util

from buildbot_gentoo_ci.steps import update_db
from buildbot_gentoo_ci.steps import category
from buildbot_gentoo_ci.steps import package
from buildbot_gentoo_ci.steps import version
from buildbot_gentoo_ci.steps import builders
from buildbot_gentoo_ci.steps import portage
from buildbot_gentoo_ci.steps import logs

def update_db_check():
    f = util.BuildFactory()
    # FIXME: 1
    # Get base project data from db
    #   return profile_repository, project
    f.addStep(update_db.GetDataGentooCiProject())
    # Check if needed path is there
    f.addStep(update_db.CheckPath())
    # update the repos
    f.addStep(update_db.UpdateRepos())
    # setup the profile
    f.addStep(portage.SetMakeProfileLocal())
    # setup repos.conf dir
    f.addStep(portage.SetReposConfLocal())
    # setup make.conf
    f.addStep(portage.SetMakeConfLocal())
    # Make a for loop and trigger new builders with cpv from git_changes
    #   return cpv, repository, project_data
    f.addStep(update_db.TriggerCheckForCPV())
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
    f.addStep(category.CheckC())
    # if package in db
    #   return package_data
    #   add check package path step at end
    # else
    #   add package to db step
    #   return package_data
    f.addStep(package.CheckP())
    # Trigger new builders with v from cpv
    #   return package_data, cpv, repository_data, project_data
    f.addStep(package.TriggerCheckForV())
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
    #NOTE: remove the symlink befor the dir
    f.addStep(buildbot_steps.ShellCommandNewStyle(
                        command=['rm', 'make.profile'],
                        workdir='/etc/portage/'
                        ))
    f.addStep(buildbot_steps.RemoveDirectory(dir="portage",
                                workdir='/etc/'))
    f.addStep(buildbot_steps.MakeDirectory(dir="portage",
                                workdir='/etc/'))
    # setup the profile
    #NOTE: pkgcheck do not support it as a dir
    #f.addStep(buildbot_steps.MakeDirectory(dir="make.profile",
    #                            workdir='/etc/portage/'))
    f.addStep(portage.SetMakeProfile())
    # setup repos.conf dir
    f.addStep(buildbot_steps.MakeDirectory(dir="repos.conf",
                                workdir='/etc/portage/'))
    f.addStep(portage.SetReposConf())
    # update the repositorys listed in project_repository
    f.addStep(builders.UpdateRepos())
    # setup make.conf
    f.addStep(portage.SetMakeConf())
    # setup env
    f.addStep(portage.SetEnvDefault())
    # setup package.*
    #f.addStep(portage.SetPackageDefault())
    # setup files in /etc if needed
    # run --regen if needed on repo
    # update packages before any tests
    # run pretend on packages update on worker
    f.addStep(builders.RunEmerge(step='pre-update'))
    #   look at the log to see if we need to do stuff
    #   run update package on worker
    f.addStep(builders.RunEmerge(step='update'))
    #   check log
    # run depclean if set
    #   depclean pretend
    f.addStep(builders.RunEmerge(step='pre-depclean'))
    #   look at the log to see if we need to do stuff
    #   depclean
    f.addStep(builders.RunEmerge(step='depclean'))
    # run @preserved-rebuild if needed
    f.addStep(builders.RunEmerge(step='preserved-libs'))
    #   check log
    #   depclean
    f.addStep(builders.RunEmerge(step='depclean'))
    #   check log
    # setup make.conf if build id has changes make.conf as dict from SetMakeConf
    # setup package.* env if build id has changes
    # setup pkgcheck.conf if needed
    #f.addStep(builders.SetPkgCheckConf())
    # run pkgcheck if wanted
    #   check log
    f.addStep(builders.RunPkgCheck())
    # check cpv match
    f.addStep(builders.RunEmerge(step='match'))
    # Add the needed steps for build
    f.addStep(builders.RunBuild())
    # clean up the worker
    f.addStep(builders.RunEmerge(step='pre-depclean'))
    #   look at the log to see if we need to do stuff
    #   run depclean and preserved-libs
    f.addStep(builders.RunEmerge(step='depclean'))
    f.addStep(builders.RunEmerge(step='preserved-libs'))
    f.addStep(builders.RunEmerge(step='depclean'))
    return f

def parse_build_log():
    f = util.BuildFactory()
    # FIXME: 6
    # set needed Propertys
    f.addStep(logs.SetupPropertys())
    # pers the build log for info qa errors
    f.addStep(logs.ParserBuildLog())
    # pers the log from pkg check
    #f.addStep(logs.ParserPkgCheckLog())
    # Upload the log to the cloud and remove the log
    #f.addStep(logs.Upload())
    # check the sum log if we need to make a issue/bug/pr report
    # set it SUCCESS/FAILURE/WARNINGS
    f.addStep(logs.MakeIssue())
    # add sum log to buildbot log
    f.addStep(logs.setBuildbotLog())
    # set BuildStatus
    f.addStep(logs.setBuildStatus())
    # setup things for the irc bot
    #f.addStep(logs.SetIrcInfo())
    return f
