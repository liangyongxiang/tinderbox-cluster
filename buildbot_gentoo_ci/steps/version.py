# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import re
import os
import git

from portage.xml.metadata import MetaDataXML
from portage.checksum import perform_checksum
from portage.versions import cpv_getversion, pkgsplit, catpkgsplit

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

from buildbot_gentoo_ci.steps import portage as portage_steps

class GetVData(BuildStep):
    
    name = 'GetVData'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        # set cwd to builddir
        yield os.chdir(self.getProperty("builddir"))
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.version = yield cpv_getversion(self.getProperty("cpv"))
        print(self.version)
        self.old_version_data = yield self.gentooci.db.versions.getVersionByName(self.version)
        print(self.old_version_data)
        self.setProperty("old_version_data", self.old_version_data, 'old_version_data')
        self.setProperty("version", self.version, 'version')
        return SUCCESS

class AddVersion(BuildStep):
    
    name = 'AddVersion'
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
        self.version_data = {}
        self.version_data['name'] = self.getProperty("version")
        self.version_data['package_uuid'] = self.getProperty("package_data")['uuid']
        self.version_data['file_hash'] = self.getProperty("ebuild_file_hash")
        self.version_data['commit_id'] = self.getProperty("commit_id")
        self.version_data['uuid'] = yield self.gentooci.db.versions.addVersion(
                                            self.version_data['name'],
                                            self.version_data['package_uuid'],
                                            self.version_data['file_hash'],
                                            self.version_data['commit_id']
                                            )
        print(self.version_data)
        self.setProperty("version_data", self.version_data, 'version_data')
        return SUCCESS



class GetCommitdata(BuildStep):

    name = 'GetCommitdata'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    #@defer.inlineCallbacks
    def run(self):
        print(self.getProperty("revision_data"))
        self.setProperty('commit_id', self.getProperty("revision_data")['revision'], 'commit_id')
        return SUCCESS

class AddVersionKeyword(BuildStep):

    name = 'AddVersionKeyword'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @defer.inlineCallbacks
    def add_keyword_data(self, keyword):
        keyword_data = {}
        keyword_data['keyword'] = keyword
        keyword_data['id'] = yield self.gentooci.db.keywords.addKeyword(keyword_data['keyword'])
        return keyword_data
    
    @defer.inlineCallbacks
    def check_keyword_data(self, keyword):
        keyword_data = yield self.gentooci.db.keywords.getKeywordByName(keyword)
        if keyword_data is None:
            keyword_data = yield self.add_keyword_data(keyword)
        return keyword_data['id']

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.version_keyword_dict = {}
        auxdb = self.getProperty("auxdb")['KEYWORDS']
        if auxdb is None or not isinstance(auxdb, list):
            self.version_keyword_dict = None
            self.setProperty('version_keyword_dict', self.version_keyword_dict, 'version_keyword_dict')
            return SUCCESS
        print(auxdb)
        for keyword in auxdb:
            print(keyword)
            status = 'stable'
            if keyword[0] in ["~"]:
                keyword = keyword[1:]
                status = 'unstable'
            elif keyword[0] in ["-"]:
                keyword = keyword[1:]
                status = 'negative'
            elif keyword[0] in ["*"]:
                keyword = keyword[1:]
                status = 'all'
            version_keyword_data = {}
            version_keyword_data['version_uuid'] = self.getProperty("version_data")['uuid']
            version_keyword_data['keyword_id'] = yield self.check_keyword_data(keyword)
            version_keyword_data['status'] = status
            version_keyword_data['uuid'] = yield self.gentooci.db.versions.addKeyword(
                                                version_keyword_data['version_uuid'],
                                                version_keyword_data['keyword_id'],
                                                version_keyword_data['status'])
            self.version_keyword_dict[keyword] = version_keyword_data
        self.setProperty('version_keyword_dict', self.version_keyword_dict, 'version_keyword_dict')
        return SUCCESS

class CheckPathHash(BuildStep):
    
    name = 'CheckPathHash'
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
        self.repository_basedir = self.gentooci.config.project['repository_basedir']
        self.repository_path = yield os.path.join(self.repository_basedir, self.getProperty("repository_data")['name'])
        self.cp_path = yield pkgsplit(self.getProperty("cpv"))[0]
        self.file_name = yield self.getProperty("package_data")['name'] + '-' + self.getProperty("version") + '.ebuild'
        self.ebuild_file = yield os.path.join(self.repository_path, self.cp_path, self.file_name)
        if os.path.isfile(self.ebuild_file):
            self.ebuild_file_hash = yield perform_checksum(self.ebuild_file, "SHA256")[0]
        else:
            self.ebuild_file = None
            self.ebuild_file_hash = None
        self.setProperty('ebuild_file', self.ebuild_file, 'ebuild_file')
        self.setProperty('ebuild_file_hash', self.ebuild_file_hash, 'ebuild_file_hash')
        self.setProperty('repository_path', self.repository_path, 'repository_path')
        return SUCCESS

class TriggerBuildCheck(BuildStep):
    
    name = 'TriggerBuildCheck'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        yield self.build.addStepsAfterCurrentStep([steps.Trigger(
                schedulerNames=['build_request_data'],
                        waitForFinish=False,
                        updateSourceStamp=False,
                        set_properties={
                            'cpv' : self.getProperty("cpv"),
                            'version_data' : self.getProperty("version_data"),
                            'version_keyword_dict' : self.getProperty('version_keyword_dict'),
                            'repository_data' : self.getProperty("repository_data"),
                        }
                )])
        return SUCCESS

class DeleteOldVersion(BuildStep):

    name = 'DeleteOldVersion'
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
        yield self.gentooci.db.versions.delVersion(self.getProperty("old_version_data")['uuid'])
        return SUCCESS

class CheckV(BuildStep):
    
    name = 'CheckV'
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
        self.old_version_data = self.getProperty("old_version_data")
        self.ebuild_file = self.getProperty("ebuild_file")
        addStepVData = []
        print(self.ebuild_file)
        print(self.old_version_data)
        print(self.getProperty("ebuild_file_hash"))
        if self.getProperty("ebuild_file") is None and self.getProperty("old_version_data") is not None:
            addStepVData.append(TriggerBuildCheck())
            addStepVData.append(DeleteOldVersion())
        if self.getProperty("ebuild_file") is not None and self.getProperty("old_version_data") is not None:
            if self.getProperty("ebuild_file_hash") != self.getProperty("old_version_data")['file_hash']:
                addStepVData.append(GetCommitdata())
                addStepVData.append(portage_steps.SetEnvForEbuildSH())
                addStepVData.append(AddVersion())
                addStepVData.append(AddVersionKeyword())
                addStepVData.append(TriggerBuildCheck())
                addStepVData.append(DeleteOldVersion())
            else:
                return SUCCESS
        if self.getProperty("ebuild_file") is not None and self.getProperty("old_version_data") is None:
            addStepVData.append(GetCommitdata())
            addStepVData.append(portage_steps.SetEnvForEbuildSH())
            addStepVData.append(AddVersion())
            addStepVData.append(AddVersionKeyword())
            addStepVData.append(TriggerBuildCheck())
        yield self.build.addStepsAfterCurrentStep(addStepVData)
        return SUCCESS
