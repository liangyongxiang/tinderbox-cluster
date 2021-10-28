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

    @defer.inlineCallbacks
    def getProjectByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects
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
    def getProjectRepositorysByUuid(self, uuid, auto=True):
        def thd(conn):
            tbl = self.db.model.projects_repositorys
            q = tbl.select()
            q = q.where(tbl.c.repository_uuid == uuid)
            q = q.where(tbl.c.auto == auto)
            return [self._row2dict_projects_repositorys(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getRepositorysByProjectUuid(self, uuid, auto=True):
        def thd(conn):
            tbl = self.db.model.projects_repositorys
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            q = q.where(tbl.c.auto == auto)
            return [self._row2dict_projects_repositorys(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getAllProjectPortageByUuidAndDirectory(self, uuid, directory):
        def thd(conn):
            tbl = self.db.model.projects_portage
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            q = q.where(tbl.c.directorys == directory)
            return [self._row2dict_projects_portage(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectPortageByUuidAndDirectory(self, uuid, directory):
        def thd(conn):
            tbl = self.db.model.projects_portage
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            q = q.where(tbl.c.directorys == directory)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict_projects_portage(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectMakeConfById(self, uuid, id):
        def thd(conn):
            tbl = self.db.model.projects_portages_makeconf
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            q = q.where(tbl.c.makeconf_id == id)
            return [self._row2dict_projects_portages_makeconf(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectPortageEnvByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_portages_env
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            return [self._row2dict_projects_portages_env(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectPortagePackageByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_portages_package
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            return [self._row2dict_projects_portages_package(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectPortagePackageByUuidAndExclude(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_portages_package
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            q = q.where(tbl.c.directory == 'exclude')
            return [self._row2dict_projects_portages_package(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectEmergeOptionsByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_emerge_options
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            res = conn.execute(q)
            row = res.fetchone()
            if not row:
                return None
            return self._row2dict_projects_emerge_options(conn, row)
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectLogSearchPatternByUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_pattern
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            return [self._row2dict_projects_pattern(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getProjectLogSearchPatternByUuidAndIgnore(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_pattern
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            q = q.where(tbl.c.status == 'ignore')
            return [self._row2dict_projects_pattern(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    @defer.inlineCallbacks
    def getWorkersByProjectUuid(self, uuid):
        def thd(conn):
            tbl = self.db.model.projects_workers
            q = tbl.select()
            q = q.where(tbl.c.project_uuid == uuid)
            return [self._row2dict_projects_workers(conn, row)
                for row in conn.execute(q).fetchall()]
        res = yield self.db.pool.do(thd)
        return res

    def _row2dict(self, conn, row):
        return dict(
            uuid=row.uuid,
            name=row.name,
            description=row.description,
            profile=row.profile,
            profile_repository_uuid=row.profile_repository_uuid,
            keyword_id=row.keyword_id,
            status=row.status,
            auto=row.auto,
            enabled=row.enabled,
            use_default=row.use_default,
            created_by=row.created_by
            )

    def _row2dict_projects_repositorys(self, conn, row):
        if row.pkgcheck == 'none':
            pkgcheck = False
        else:
            pkgcheck=row.pkgcheck
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            repository_uuid=row.repository_uuid,
            auto=row.auto,
            pkgcheck=pkgcheck,
            build=row.build,
            test=row.test
            )

    def _row2dict_projects_workers(self, conn, row):
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            worker_uuid=row.worker_uuid,
            )

    def _row2dict_projects_portage(self, conn, row):
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            directorys=row.directorys,
            value=row.value
            )

    def _row2dict_projects_portages_makeconf(self, conn, row):
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            makeconf_id=row.makeconf_id,
            value=row.value,
            build_id=0
            )

    def _row2dict_projects_portages_env(self, conn, row):
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            makeconf_id=row.makeconf_id,
            name=row.name,
            value=row.value
            )

    def _row2dict_projects_portages_package(self, conn, row):
        if row.value == '':
            value = None
        else:
            value = row.value
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            directory=row.directory,
            package=row.package,
            value=value
            )

    def _row2dict_projects_emerge_options(self, conn, row):
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            oneshot=row.oneshot,
            depclean=row.depclean,
            preserved_libs=row.preserved_libs
            )

    def _row2dict_projects_pattern(self, conn, row):
        return dict(
            id=row.id,
            project_uuid=row.project_uuid,
            search=row.search,
            search_type=row.search_type,
            start=row.start,
            end=row.end,
            status=row.status,
            type=row.type
            )
