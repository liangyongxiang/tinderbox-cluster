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

class KeywordsConnectorComponent(base.DBConnectorComponent):

    @defer.inlineCallbacks
    def getKeywordByName(self, name):
        def thd(conn):
            tbl = self.db.model.keywords
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
    def getKeywordById(self, id):
        def thd(conn):
            tbl = self.db.model.keywords
            q = tbl.select()
            q = q.where(tbl.c.id == id)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def addKeyword(self, name):
        def thd(conn, no_recurse=False):
            try:
                tbl = self.db.model.keywords
                q = tbl.insert()
                r = conn.execute(q, dict(name=name))
            except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
                uuid = None
            else:
                uuid = r.inserted_primary_key[0]
            return uuid
        res = yield self.db.pool.do(thd)
        return res

    def _row2dict(self, conn, row):
        return dict(
            id=row.id,
            name=row.name
            )
