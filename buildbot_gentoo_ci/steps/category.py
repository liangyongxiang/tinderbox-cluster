# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import re
import os

from portage.xml.metadata import MetaDataXML
from portage.checksum import perform_checksum

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE

class AddCategory(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.category = self.getProperty("category")
        self.category_data = {}
        self.category_data['name'] = self.category
        self.category_data['uuid'] = yield self.gentooci.db.categorys.addCategory(self.category)
        print(self.category_data)
        self.setProperty("category_data", self.category_data, 'category_data')
        self.setProperty("config_root", self.getProperty("config_root"), 'config_root')
        self.setProperty("project_data", self.getProperty("project_data"), 'project_data')
        self.setProperty("repository", self.getProperty("repository"), 'repository')
        self.setProperty("cpv", self.getProperty("cpv"), 'cpv')
        return SUCCESS

class CheckCGentooCiProject(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.category = yield self.getProperty("cpv").split('/')[0]
        print(self.category)
        self.category_data = yield self.gentooci.db.categorys.getCategoryByName(self.category)
        self.setProperty("config_root", self.getProperty("config_root"), 'config_root')
        self.setProperty("project_data", self.getProperty("project_data"), 'project_data')
        self.setProperty("repository", self.getProperty("repository"), 'repository')
        self.setProperty("cpv", self.getProperty("cpv"), 'cpv')
        print(self.category_data)
        if self.category_data is None:
            self.setProperty("category", self.category, 'category')
            yield self.build.addStepsAfterCurrentStep([AddCategory()])
            #yield self.build.addStepsAfterLastStep([AddMetadataCategory()])
            return SUCCESS
        self.setProperty("category_data", self.category_data, 'category_data')
        #yield self.build.addStepsAfterLastStep([CheckPathCategory()])
        return SUCCESS
