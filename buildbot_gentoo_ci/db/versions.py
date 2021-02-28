# This file has parts from Buildbot and is modifyed by Gentoo Authors. 
# Buildbot is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members
# Origins: buildbot.db.*
# Modifyed by Gentoo Authors.
# Copyright 2021 Gentoo Authors

import uuid
import sqlalchemy as sa

from twisted.internet import defer

from buildbot.db import base
from buildbot.util import epoch2datetime

class VersionsConnectorComponent(base.DBConnectorComponent):

    @defer.inlineCallbacks
    def getVersionByName(self, name):
        def thd(conn):
            tbl = self.db.model.versions
            q = tbl.select()
            q = q.where(tbl.c.name == name)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getVersionByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.versions
            q = tbl.select()
            q = q.where(tbl.c.uuid == uuid)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def addVersion(self, name, package_uuid, file_hash, commit_id):
        def thd(conn, no_recurse=False):
            try:
                tbl = self.db.model.versions
                q = tbl.insert()
                r = conn.execute(q, dict(name=name,
                                         package_uuid=package_uuid,
                                         file_hash=file_hash,
                                         commit_id=commit_id))
            except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
                uuid = None
            else:
                uuid = r.inserted_primary_key[0]
            return uuid
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def delVersion(self, uuid):
        deleted_at = epoch2datetime(int(self.master.reactor.seconds()))
        def thd(conn, no_recurse=False):
        
                tbl = self.db.model.versions
                q = tbl.update()
                q = q.where(tbl.c.uuid == uuid)
                conn.execute(q, deleted=True,
                                deleted_at=deleted_at)
        yield self.db.pool.do(thd)

    @defer.inlineCallbacks
    def addKeyword(self, version_uuid, keyword_id, status):
        def thd(conn, no_recurse=False):
            try:
                tbl = self.db.model.versions_keywords
                q = tbl.insert()
                r = conn.execute(q, dict(version_uuid=version_uuid,
                                         keyword_id=keyword_id,
                                         status=status))
            except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
                uuid = None
            else:
                uuid = r.inserted_primary_key[0]
            return uuid
        res = yield self.db.pool.do(thd)
        return res

    def _row2dict(self, conn, row):
        return dict(
            uuid=row.uuid,
            name=row.name,
            package_uuid=row.package_uuid,
            file_hash=row.file_hash,
            commit_id=row.commit_id,
            deleted=row.deleted,
            deleted_at=row.deleted_at
            )
