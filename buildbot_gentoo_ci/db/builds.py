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

class BuildsConnectorComponent(base.DBConnectorComponent):

    #@defer.inlineCallbacks
    def addBuild(self, project_build_data):
        created_at = int(self.master.reactor.seconds())
        def thd(conn, no_recurse=False):
            tbl = self.db.model.projects_builds
            # get the highest current number
            r = conn.execute(sa.select([sa.func.max(tbl.c.build_id)],
                                       whereclause=(tbl.c.project_uuid == project_build_data['project_uuid'])))
            number = r.scalar()
            new_number = 1 if number is None else number + 1
            try:
                q = tbl.insert()
                r = conn.execute(q, dict(project_uuid=project_build_data['project_uuid'],
                                         version_uuid=project_build_data['version_uuid'],
                                         buildbot_build_id=project_build_data['buildbot_build_id'],
                                         status=project_build_data['status'],
                                         requested=project_build_data['requested'],
                                         created_at=created_at,
                                         build_id=new_number))
            except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
                id = None
                new_number = None
            else:
                id = r.inserted_primary_key[0]
            return id, new_number
        return self.db.pool.do(thd)

    @defer.inlineCallbacks
    def setSatusBuilds(self, build_id, project_uuid, status):
        updated_at = int(self.master.reactor.seconds())
        def thd(conn, no_recurse=False):
        
                tbl = self.db.model.projects_builds
                q = tbl.update()
                q = q.where(tbl.c.build_id == build_id)
                q = q.where(tbl.c.project_uuid == project_uuid)
                conn.execute(q, updated_at=updated_at,
                                status=status)
        yield self.db.pool.do(thd)

    @defer.inlineCallbacks
    def setBuildbotBuildIdBuilds(self, build_id, project_uuid, buildbot_build_id):
        updated_at = int(self.master.reactor.seconds())
        def thd(conn, no_recurse=False):
        
                tbl = self.db.model.projects_builds
                q = tbl.update()
                q = q.where(tbl.c.build_id == build_id)
                q = q.where(tbl.c.project_uuid == project_uuid)
                conn.execute(q, updated_at=updated_at,
                                buildbot_build_id=buildbot_build_id)
        yield self.db.pool.do(thd)
