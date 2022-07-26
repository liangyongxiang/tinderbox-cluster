# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import re
import os

from portage.xml.metadata import MetaDataXML
from portage.checksum import perform_checksum
from portage.versions import catpkgsplit

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

class SetupPropertys(BuildStep):
    name = 'Setup propertys for CPV check'
    description = 'Running'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        # set this in config
        super().__init__(**kwargs)

    #@defer.inlineCallbacks
    def run(self):
        self.setProperty('portage_repos_path', '/repositorys', 'portage_repos_path')
        self.setProperty('rootworkdir', '/var/lib/buildbot_worker', 'rootworkdir')
        return SUCCESS

class AddPackage(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    name = 'AddPackage'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.package_data = {}
        self.package_data['name'] = self.getProperty("package")
        self.package_data['repository_uuid'] = self.getProperty("repository_data")['uuid']
        self.package_data['category_uuid'] = self.getProperty("category_data")['uuid']
        self.package_data['uuid'] = yield self.gentooci.db.packages.addPackage(
                                            self.package_data['name'],
                                            self.package_data['repository_uuid'],
                                            self.package_data['category_uuid']
                                            )
        print(self.package_data)
        self.setProperty("package_data", self.package_data, 'package_data')
        return SUCCESS

class CheckP(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    name = 'CheckP'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.package = self.getProperty("change_data")['cp'].split('/')[1]
        print(self.package)
        self.package_data = yield self.gentooci.db.packages.getPackageByName(self.package,
                                                                            self.getProperty("category_data")['uuid'],
                                                                            self.getProperty("repository_data")['uuid'])
        print(self.package_data)
        if self.package_data is None:
            self.setProperty("package", self.package, 'package')
            yield self.build.addStepsAfterCurrentStep([AddPackage()])
            #yield self.build.addStepsAfterLastStep([AddMetadataPackage()])
            return SUCCESS
        self.setProperty("package_data", self.package_data, 'package_data')
        #yield self.build.addStepsAfterLastStep([CheckPathPackage()])
        return SUCCESS

class TriggerCheckForV(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    name = 'TriggerCheckForV'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    @defer.inlineCallbacks
    def run(self):
        addStepUpdateVData = []
        for cpv in self.getProperty("change_data")['cpvs']:
            print(cpv)
            addStepUpdateVData.append(
                steps.Trigger(
                    schedulerNames=['update_v_data'],
                    waitForFinish=False,
                    updateSourceStamp=False,
                    set_properties={
                        'cpv' : cpv,
                        'package_data' : self.getProperty("package_data"),
                        'repository_data' : self.getProperty("repository_data"),
                        'category_data' : self.getProperty("category_data"),
                        'change_data' : self.getProperty("change_data"),
                        'project_data' : self.getProperty("project_data"),
                        'cp_worker' : self.getProperty('workername'),
                    }
                )
            )
        yield self.build.addStepsAfterCurrentStep(addStepUpdateVData)
        return SUCCESS
