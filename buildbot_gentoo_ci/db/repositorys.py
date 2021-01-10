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

import sqlalchemy as sa

from twisted.internet import defer

from buildbot.db import base

class RepositorysConnectorComponent(base.DBConnectorComponent):

    def getRepositorys(self):
        def thd(conn):
            tbl = self.db.model.repositorys
            q = tbl.select()
            q = q.where(tbl.c.enable == 1,
                    tbl.c.auto == 1
                    )
            r = conn.execute(q)
            return [dict(row) for row in r.fetchall()]
        return self.db.pool.do(thd)

    @defer.inlineCallbacks
    def getRepositoryByName(self, name):
        def thd(conn):
            tbl = self.db.model.repositorys
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
    def getRepositoryByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.repositorys
            q = tbl.select()
            q = q.where(tbl.c.uuid == uuid)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    def getRepositorysGitPoller(self):
        def thd(conn):
            tblr = self.db.model.repositorys
            tblrg = self.db.model.repository_gitpuller
            from_clause = tblr.join(tblg, tblr.c.uuid == tblrg.c.repository_uuid)
            q = sa.select([tblrg]).select_from(
                from_clause).where(tblr.c.enabled == 1,
                    tblr.c.auto == 1
                    )
            r = conn.execute(q)
            return [dict(row) for row in r.fetchall()]
        return self.db.pool.do(thd)

    def _row2dict(self, conn, row):
        return dict(
            uuid=row.uuid,
            name=row.name,
            description=row.description,
            mirror_url=row.mirror_url,
            auto=row.auto,
            enabled=row.enabled,
            ebuild=row.ebuild
            )
