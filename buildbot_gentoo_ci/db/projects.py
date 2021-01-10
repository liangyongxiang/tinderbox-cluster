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

class ProjectsConnectorComponent(base.DBConnectorComponent):

    @defer.inlineCallbacks
    def getProjects(self):
        def thd(conn):
            tbl = self.db.model.projects
            q = tbl.select()
            q = q.where(tbl.c.enable == True,
                    tbl.c.auto == True
                    )
            return [self._row2dict(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    #FIXME:join project_repository and profile_repository info
    @defer.inlineCallbacks
    def getProjectByName(self, name):
        def thd(conn):
            tbl = self.db.model.projects
            q = tbl.select()
            q = q.where(tbl.c.name == name)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    def _row2dict(self, conn, row):
        return dict(
            uuid=row.uuid,
            name=row.name,
            description=row.description,
            project_repository_uuid=row.project_repository_uuid,
            profile=row.profile,
            profile_repository_uuid=row.profile_repository_uuid,
            keyword_id=row.keyword_id,
            unstable=row.unstable,
            auto=row.auto,
            enabled=row.enabled,
            created_by=row.created_by
            )
