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

class AddPackage(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        self.setProperty("config_root", self.getProperty("config_root"), 'config_root')
        self.setProperty("project_data", self.getProperty("project_data"), 'project_data')
        self.setProperty("repository_data", self.getProperty("repository_data"), 'repository_data')
        self.setProperty("cpv", self.getProperty("cpv"), 'cpv')
        return SUCCESS

class CheckPGentooCiProject(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.package = yield catpkgsplit(self.getProperty("cpv"))[1]
        print(self.package)
        self.package_data = yield self.gentooci.db.packages.getPackageByName(self.package)
        self.setProperty("config_root", self.getProperty("config_root"), 'config_root')
        self.setProperty("project_data", self.getProperty("project_data"), 'project_data')
        self.setProperty("repository_data", self.getProperty("repository_data"), 'repository_data')
        self.setProperty("cpv", self.getProperty("cpv"), 'cpv')
        print(self.package_data)
        if self.package_data is None:
            self.setProperty("category_data", self.getProperty("category_data"), 'category_data')
            self.setProperty("package", self.package, 'package')
            yield self.build.addStepsAfterCurrentStep([AddPackage()])
            #yield self.build.addStepsAfterLastStep([AddMetadataPackage()])
            return SUCCESS
        self.setProperty("package_data", self.package_data, 'package_data')
        #yield self.build.addStepsAfterLastStep([CheckPathPackage()])
        return SUCCESS
