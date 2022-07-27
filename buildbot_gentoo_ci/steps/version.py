# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os

from portage.versions import cpv_getversion, pkgsplit, catpkgsplit
from portage import _pms_eapi_re, eapi_is_supported, auxdbkeys

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import WARNINGS
from buildbot.process.results import SKIPPED
from buildbot.process import remotecommand
from buildbot.plugins import steps

def GetPythonVersion(pyprop):
    py_list = pyprop.replace(' ', '').replace('\n ', '').split('.')
    return '.'.join([py_list[0], py_list[1]]).lower()

def PersOutputOfGetEapi(rc, stdout, stderr):
    eapi = None
    # split the lines
    for line in stdout.split('\n'):
        if line.startswith('EAPI'):
            print(line[-1])
            m = _pms_eapi_re.match(line)
            if m is not None:
                eapi = m.group(2)
                print(eapi)
    if eapi is None or not eapi_is_supported(eapi):
        print('ERROR: invalid eapi or not found')
        eapi = False
    else:
        print(eapi)
    return {
        'eapi' : eapi
        }

def PersOutputOfGetAuxdb(rc, stdout, stderr):
    metadata = None
    NoSplit = ['DESCRIPTION']
    ignore_list = ['SRC_URI']
    #make dict of the stout
    index = 1
    metadata_line_dict = {}
    for text_line in stdout.splitlines():
        metadata_line_dict[index] = text_line
        index = index + 1
    if not stderr == '':
        print('stderr')
    # should have 22 lines
    if len(auxdbkeys) != index -1:
        # number of lines is incorrect.
        print('ERROR: Number of lines is incorrect')
        print(metadata_line_dict)
        return {
            'auxdb' : metadata
            }
    # split all keys to list instead of speces
    metadata = {}
    i = 1
    for key in auxdbkeys:
        if metadata_line_dict[i][-1] == '=' or key in ignore_list:
            metadata[key] = False
        else:
            if ' ' in metadata_line_dict[i] and key not in NoSplit:
                metadata[key] = metadata_line_dict[i].replace(key + '=', '').split(' ')
            else:
                metadata[key] = []
                metadata[key].append(metadata_line_dict[i].replace(key + '=', ''))
        i = i + 1
    return {
        'auxdb' : metadata
        }

class SetEnvForGetAuxdb(BuildStep):

    name = 'SetEnvForGetAuxdb'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        ebuild_commands = []
        ebuild_env = {}
        if not self.getProperty("eapi"):
            return FAILURE
        #Setup ENV
        category = yield catpkgsplit(self.getProperty("cpv"))[0]
        package = yield catpkgsplit(self.getProperty("cpv"))[1]
        version = yield catpkgsplit(self.getProperty("cpv"))[2]
        revision = yield catpkgsplit(self.getProperty("cpv"))[3]
        python_version = GetPythonVersion(self.getProperty("python_version"))
        portage_bin_path = yield os.path.join('/usr/lib/portage', python_version)
        ebuild_sh_bin = 'ebuild.sh'
        ebuild_sh_path = yield os.path.join(portage_bin_path, ebuild_sh_bin)
        ebuild_env['EAPI'] = self.getProperty("eapi")
        #ebuild_env['PORTAGE_DEBUG'] = '1'
        ebuild_env['EBUILD_PHASE'] = 'depend'
        ebuild_env['CATEGORY'] = category
        ebuild_env['P'] = package + '-' + version
        ebuild_env['PN'] = package
        ebuild_env['PR'] = revision
        ebuild_env['PV'] = version
        if revision == 'r0':
            ebuild_env['PF'] = ebuild_env['P']
            ebuild_env['PVR'] = version
        else:
            ebuild_env['PF'] = ebuild_env['P'] + '-' + revision
            ebuild_env['PVR'] = version + '-' + revision
        ebuild_env['PORTAGE_BIN_PATH'] = portage_bin_path
        ebuild_env['EBUILD'] = self.getProperty("ebuild_file")
        ebuild_env['PORTAGE_PIPE_FD'] = '1'
        ebuild_env['WORKDIR'] = yield os.path.join('/var/tmp/portage', 'portage', category, ebuild_env['PF'], 'work')
        #FIXME: get a list of repository_path
        ebuild_env['PORTAGE_ECLASS_LOCATIONS'] = self.getProperty("repository_path")
        yield self.build.addStepsAfterCurrentStep([steps.SetPropertyFromCommand(
                                                            name = 'RunGetAuxdb',
                                                            haltOnFailure = True,
                                                            flunkOnFailure = True,
                                                            command=[ebuild_sh_path, 'depend'],
                                                            env=ebuild_env,
                                                            workdir=self.getProperty("builddir"),
                                                            strip=False,
                                                            extract_fn=PersOutputOfGetAuxdb
                                                            )])
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
        self.version_data['file_hash'] = 'None'
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
        print(self.getProperty("change_data"))
        self.setProperty('commit_id', self.getProperty("change_data")['revision'], 'commit_id')
        return SUCCESS

#FIXME: use versions_metadata table
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
        if not auxdb or not isinstance(auxdb, list):
            self.version_keyword_dict = None
            self.setProperty('version_keyword_dict', self.version_keyword_dict, 'version_keyword_dict')
            return SUCCESS
        print(auxdb)
        for keyword in auxdb:
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

class AddVersionRestrictions(BuildStep):

    name = 'AddVersionRestrictions'
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
        auxdb = self.getProperty("auxdb")['RESTRICT']
        if not auxdb or not isinstance(auxdb, list):
            return SKIPPED
        for restrict in auxdb:
            version_metadata_data = {}
            version_metadata_data['version_uuid'] = self.getProperty("version_data")['uuid']
            version_metadata_data['metadata'] = 'restrict'
            version_metadata_data['value'] = restrict
            version_metadata_data['id'] = yield self.gentooci.db.versions.addMetadata(
                                                version_metadata_data['version_uuid'],
                                                version_metadata_data['metadata'],
                                                version_metadata_data['value'])
        return SUCCESS

class AddVersionIUse(BuildStep):

    name = 'AddVersionIUse'
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
        auxdb = self.getProperty("auxdb")['IUSE']
        if not auxdb or not isinstance(auxdb, list):
            return SKIPPED
        for iuse in auxdb:
            version_metadata_data = {}
            version_metadata_data['version_uuid'] = self.getProperty("version_data")['uuid']
            version_metadata_data['metadata'] = 'iuse'
            version_metadata_data['value'] = iuse
            version_metadata_data['id'] = yield self.gentooci.db.versions.addMetadata(
                                                version_metadata_data['version_uuid'],
                                                version_metadata_data['metadata'],
                                                version_metadata_data['value'])
        return SUCCESS

class CheckPath(BuildStep):

    name = 'CheckPath'
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
        self.repository_basedir = yield os.path.join(self.getProperty("rootworkdir"), self.getProperty('portage_repos_path')[1:])
        self.repository_path = yield os.path.join(self.repository_basedir, self.getProperty("repository_data")['name'])
        self.cp_path = yield pkgsplit(self.getProperty("cpv"))[0]
        self.file_name = yield self.getProperty("package_data")['name'] + '-' + self.getProperty("version") + '.ebuild'
        self.ebuild_file = yield os.path.join(self.repository_path, self.cp_path, self.file_name)
        print(self.ebuild_file)
        cmd = remotecommand.RemoteCommand('stat', {'file': self.ebuild_file})
        yield self.runCommand(cmd)
        if cmd.didFail():
            self.ebuild_file = None
        #self.ebuild_file_hash = None
        self.setProperty('ebuild_file', self.ebuild_file, 'ebuild_file')
        #self.setProperty('ebuild_file_hash', self.ebuild_file_hash, 'ebuild_file_hash')
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

class SetupPropertys(BuildStep):

    name = 'Setup propertys for checking V'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.setProperty('portage_repos_path', '/repositorys', 'portage_repos_path')
        self.setProperty('rootworkdir', '/var/lib/buildbot_worker', 'rootworkdir')
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        print(self.getProperty("cpv"))
        self.version = yield cpv_getversion(self.getProperty("cpv"))
        print(self.version)
        self.old_version_data = yield self.gentooci.db.versions.getVersionByName(self.version, self.getProperty("package_data")['uuid'])
        print(self.old_version_data)
        self.setProperty("old_version_data", self.old_version_data, 'old_version_data')
        self.setProperty("version", self.version, 'version')
        return SUCCESS

class SetupStepsForCheckV(BuildStep):
    
    name = 'Setup steps for Checking V'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        addStepVData = []
        print(self.getProperty("ebuild_file"))
        print(self.getProperty("old_version_data"))
        #print(self.getProperty("ebuild_file_hash"))
        if self.getProperty("ebuild_file") is None:
            addStepVData.append(TriggerBuildCheck())
            if self.getProperty("old_version_data") is None:
                return WARNINGS
            else:
                addStepVData.append(DeleteOldVersion())
        else:
            if self.getProperty("old_version_data") is not None:
                addStepVData.append(DeleteOldVersion())
            # get ebuild aux metadata
            addStepVData.append(steps.SetPropertyFromCommand(
                                                            name = 'RunGetEAPI',
                                                            haltOnFailure = True,
                                                            flunkOnFailure = True,
                                                            command=['head', '-n', '8', self.getProperty("ebuild_file")],
                                                            strip=False,
                                                            extract_fn=PersOutputOfGetEapi
                                                            ))
            addStepVData.append(steps.SetPropertyFromCommand(
                                                            name = 'GetPythonVersion',
                                                            haltOnFailure = True,
                                                            flunkOnFailure = True,
                                                            command=['python', '-V'],
                                                            strip=False,
                                                            property="python_version"
                                                            ))
            addStepVData.append(SetEnvForGetAuxdb())
            # get commit data
            addStepVData.append(GetCommitdata())
            # add version to db
            addStepVData.append(AddVersion())
            # add metadata to db
            addStepVData.append(AddVersionKeyword())
            addStepVData.append(AddVersionRestrictions())
            addStepVData.append(AddVersionIUse())
            # Trigger build_request_check
            addStepVData.append(TriggerBuildCheck())
        yield self.build.addStepsAfterCurrentStep(addStepVData)
        return SUCCESS
