# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

class SetPackageDefault(BuildStep):

    name = 'SetPackageDefault'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        aftersteps_list = []
        packagedir_list = []
        packagedir_list.append('env')
        #FIXME:
        # get list what dir we need to make from db
        # create the dirs
        for packagedir in packagedir_list:
            aftersteps_list.append(steps.MakeDirectory(dir='package.' + packagedir,
                                workdir='/etc/portage/'))
        #FIXME:
        # add the needed package.* settings from db
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class SetEnvDefault(BuildStep):

    name = 'SetEnvDefault'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def getPortageEnv(self, portage_env_data, portage_env_dict = {}):
        for project_portage_env in portage_env_data:
            if not project_portage_env['name'] in portage_env_dict:
                portage_env_dict[project_portage_env['name']] = {
                    project_portage_env['makeconf_id'] : []
                    }
            if not project_portage_env['makeconf_id'] in portage_env_dict[project_portage_env['name']]:
                portage_env_dict[project_portage_env['name']][project_portage_env['makeconf_id']] = []
            portage_env_dict[project_portage_env['name']][project_portage_env['makeconf_id']].append(project_portage_env['value'])
        return portage_env_dict

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        default_project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project'])
        aftersteps_list = []
        separator1 = '\n'
        separator2 = ' '
        # create the dir
        aftersteps_list.append(steps.MakeDirectory(dir='env',
                                workdir='/etc/portage/'))
        #FIXME:
        # add env settings from the db
        default_project_portage_env_data = yield self.gentooci.db.projects.getProjectPortageEnvByUuid(default_project_data['uuid'])
        project_portage_env_data = yield self.gentooci.db.projects.getProjectPortageEnvByUuid(project_data['uuid'])
        project_portage_env_dict = yield self.getPortageEnv(default_project_portage_env_data, portage_env_dict = {})
        project_portage_env_dict = yield self.getPortageEnv(project_portage_env_data, portage_env_dict = project_portage_env_dict)
        print(project_portage_env_dict)
        for k, v in project_portage_env_dict.items():
            env_strings = []
            for a, b in v.items():
                variable_data = yield self.gentooci.db.portages.getVariableById(a)
                env_variable_string = variable_data['variable'] + '="' + separator2.join(b) + '"'
                env_strings.append(env_variable_string)
            yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(separator1.join(env_strings) + separator1,
                                workerdest=k + '.conf',
                                workdir='/etc/portage/env/')
            ])
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS
