# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from minio import Minio
from minio.error import ResponseError, BucketAlreadyOwnedByYou, BucketAlreadyExists

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE

#FIXME:
# get url, user from config
# get password from secret
url = ''
user = ''
password = ''

class putFileToMinio(BuildStep):

    name = 'putFileToMinio'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, filename, target, bucket, **kwargs):
        self.filename = filename
        self.bucket = bucket
        self.target = target
        super().__init__(**kwargs)

    def getMinioConnect(self, url, user, password):
        minioclient = Minio(
            url,
            access_key = user,
            secret_key = password,
            secure = False
            )
        return minioclient

    @defer.inlineCallbacks
    def pushFileToMinio(self):
        try:
            yield self.minio_connect.fput_object(self.bucket, self.target, self.filename)
        except ResponseError as err:
            print(err)
            return FAILURE
        return True

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.minio_connect = yield self.getMinioConnect(url, user, password)
        success = yield self.pushFileToMinio()
        return SUCCESS
