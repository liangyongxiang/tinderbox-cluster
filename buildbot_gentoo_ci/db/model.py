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
# Origins: buildbot.db.model.py
# Modifyed by Gentoo Authors.
# Copyright 2020 Gentoo Authors

import uuid
import migrate
import migrate.versioning.repository
import sqlalchemy as sa
from migrate import exceptions  # pylint: disable=ungrouped-imports

from twisted.internet import defer
from twisted.python import log
from twisted.python import util

from buildbot.db import base
from buildbot.db.migrate_utils import test_unicode
from buildbot.util import sautils

try:
    from migrate.versioning.schema import ControlledSchema  # pylint: disable=ungrouped-imports
except ImportError:
    ControlledSchema = None


class Model(base.DBConnectorComponent):
    #
    # schema
    #

    metadata = sa.MetaData()

    # NOTES

    # * server_defaults here are included to match those added by the migration
    #   scripts, but they should not be depended on - all code accessing these
    #   tables should supply default values as necessary.  The defaults are
    #   required during migration when adding non-nullable columns to existing
    #   tables.
    #
    # * dates are stored as unix timestamps (UTC-ish epoch time)
    #
    # * sqlalchemy does not handle sa.Boolean very well on MySQL or Postgres;
    #   use sa.SmallInteger instead

    # Tables related to gentoo-ci-cloud
    # -------------------------

    repositorys = sautils.Table(
        "repositorys", metadata,
        # unique id per repository
        sa.Column('uuid', sa.String(36), primary_key=True,
                  default=lambda: str(uuid.uuid4()),
                  ),
        # repository's name
        sa.Column('name', sa.String(255), nullable=False),
        # description of the repository
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('mirror_url', sa.String(255), nullable=True),
        sa.Column('auto', sa.Boolean, default=False),
        sa.Column('enabled', sa.Boolean, default=False),
        sa.Column('ebuild', sa.Boolean, default=False),
    )

    # Use by GitPoller
    repository_gitpuller = sautils.Table(
        "repository_gitpuller", metadata,
        # unique id per repository
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('repository_uuid', sa.String(36),
                  sa.ForeignKey('repositorys.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('project', sa.String(255), nullable=False, default='gentoo'),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('branche', sa.String(255), nullable=False, default='master'),
    )

    projects = sautils.Table(
        "projects", metadata,
        # unique id per project
        sa.Column('uuid', sa.String(36), primary_key=True,
                  default=lambda: str(uuid.uuid4()),
                  ),
        # project's name
        sa.Column('name', sa.String(255), nullable=False),
        # description of the project
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('project_repository_uuid', sa.String(36),
                  sa.ForeignKey('repositorys.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('profile', sa.String(255), nullable=False),
        sa.Column('profile_repository_uuid', sa.String(36),
                  sa.ForeignKey('repositorys.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('keyword_id', sa.Integer,
                  sa.ForeignKey('keywords.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('status', sa.Enum('stable','unstable','all'), nullable=False),
        sa.Column('auto', sa.Boolean, default=False),
        sa.Column('enabled', sa.Boolean, default=False),
        sa.Column('created_by', sa.Integer,
                  sa.ForeignKey('users.uid', ondelete='CASCADE'),
                  nullable=False),
    )

    # What repository's use by projects
    projects_repositorys = sautils.Table(
        "projects_repositorys", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('repository_uuid', sa.String(36),
                  sa.ForeignKey('repositorys.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('auto', sa.Boolean, default=False),
        sa.Column('pkgcheck', sa.Enum('package','full','none'), default='none'),
        sa.Column('build', sa.Boolean, default=False),
    )

    # projects etc/portage settings
    projects_portage = sautils.Table(
        "projects_portage", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('directorys', sa.Enum('make.profile', 'repos.conf'), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
    )

    portages_makeconf = sautils.Table(
        "portages_makeconf", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('variable', sa.String(255), nullable=False),
    )

    projects_portages_makeconf = sautils.Table(
        "projects_portages_makeconf", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('makeconf_id', sa.String(255),
                  sa.ForeignKey('portages_makeconf.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
    )

    # projects etc/portage/env settings
    projects_portages_env = sautils.Table(
        "projects_portages_env", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('makeconf_id', sa.String(255),
                  sa.ForeignKey('portages_makeconf.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
    )

    # projects etc/portage/package.* settings
    projects_portage_package = sautils.Table(
        "projects_portage_package", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('directorys', sa.Enum('use', 'accept_keywords', 'env'), nullable=False),
        sa.Column('value1', sa.String(255), nullable=False),
        sa.Column('value2', sa.String(255), nullable=True),
    )

    projects_emerge_options = sautils.Table(
        "projects_emerge_options", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('oneshot', sa.Boolean, default=True),
        sa.Column('depclean', sa.Boolean, default=True),
        sa.Column('preserved_libs', sa.Boolean, default=True),
    )

    projects_builds = sautils.Table(
        "projects_builds", metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('build_id', sa.Integer),
        sa.Column('project_uuid', sa.String(36),
                  sa.ForeignKey('projects.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version_uuid', sa.String(36),
                  sa.ForeignKey('versions.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('buildbot_build_id', sa.Integer),
        sa.Column('status', sa.Enum('failed','completed','in-progress','waiting', 'warning'), nullable=False),
        sa.Column('requested', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    keywords = sautils.Table(
        "keywords", metadata,
        # unique uuid per keyword
        sa.Column('id', sa.Integer, primary_key=True),
        # project's name
        sa.Column('name', sa.String(255), nullable=False),
    )

    categorys = sautils.Table(
        "categorys", metadata,
        sa.Column('uuid', sa.String(36), primary_key=True,
                  default=lambda: str(uuid.uuid4())
                  ),
        sa.Column('name', sa.String(255), nullable=False),
    )

    packages = sautils.Table(
        "packages", metadata,
        sa.Column('uuid', sa.String(36), primary_key=True,
                  default=lambda: str(uuid.uuid4()),
                  ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category_uuid', sa.String(36),
                  sa.ForeignKey('categorys.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('repository_uuid', sa.String(36),
                  sa.ForeignKey('repositorys.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    versions = sautils.Table(
        "versions", metadata,
        sa.Column('uuid', sa.String(36), primary_key=True,
                  default=lambda: str(uuid.uuid4()),
                  ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('package_uuid', sa.String(36),
                  sa.ForeignKey('packages.uuid', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('file_hash', sa.String(255), nullable=False),
        sa.Column('commit_id', sa.String(255), nullable=False),
        sa.Column('deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    versions_keywords = sautils.Table(
        "versions_keywords", metadata,
        # unique id per project
        sa.Column('uuid', sa.String(36), primary_key=True,
                  default=lambda: str(uuid.uuid4()),
                  ),
        # project's name
        sa.Column('keyword_id', sa.Integer,
                  sa.ForeignKey('keywords.id', ondelete='CASCADE')),
        sa.Column('version_uuid', sa.String(36),
                  sa.ForeignKey('versions.uuid', ondelete='CASCADE')),
        sa.Column('status', sa.Enum('stable','unstable','negative','all'), nullable=False),
    )

    # Tables related to users
    # -----------------------

    # This table identifies individual users, and contains buildbot-specific
    # information about those users.
    users = sautils.Table(
        "users", metadata,
        # unique user id number
        sa.Column("uid", sa.Integer, primary_key=True),

        # identifier (nickname) for this user; used for display
        sa.Column("identifier", sa.String(255), nullable=False),

        # username portion of user credentials for authentication
        sa.Column("bb_username", sa.String(128)),

        # password portion of user credentials for authentication
        sa.Column("bb_password", sa.String(128)),
    )

    # Indexes
    # -------

   

    # MySQL creates indexes for foreign keys, and these appear in the
    # reflection.  This is a list of (table, index) names that should be
    # expected on this platform

    implied_indexes = [
    ]

    # Migration support
    # -----------------

    # this is a bit more complicated than might be expected because the first
    # seven database versions were once implemented using a homespun migration
    # system, and we need to support upgrading masters from that system.  The
    # old system used a 'version' table, where SQLAlchemy-Migrate uses
    # 'migrate_version'

    repo_path = util.sibpath(__file__, "migrate")

    @defer.inlineCallbacks
    def is_current(self):
        if ControlledSchema is None:
            # this should have been caught earlier by enginestrategy.py with a
            # nicer error message
            raise ImportError("SQLAlchemy/SQLAlchemy-Migrate version conflict")

        def thd(engine):
            # we don't even have to look at the old version table - if there's
            # no migrate_version, then we're not up to date.
            repo = migrate.versioning.repository.Repository(self.repo_path)
            repo_version = repo.latest
            try:
                # migrate.api doesn't let us hand in an engine
                schema = ControlledSchema(engine, self.repo_path)
                db_version = schema.version
            except exceptions.DatabaseNotControlledError:
                return False

            return db_version == repo_version
        ret = yield self.db.pool.do_with_engine(thd)
        return ret

    # returns a Deferred that returns None
    def create(self):
        # this is nice and simple, but used only for tests
        def thd(engine):
            self.metadata.create_all(bind=engine)
        return self.db.pool.do_with_engine(thd)

    @defer.inlineCallbacks
    def upgrade(self):

        # here, things are a little tricky.  If we have a 'version' table, then
        # we need to version_control the database with the proper version
        # number, drop 'version', and then upgrade.  If we have no 'version'
        # table and no 'migrate_version' table, then we need to version_control
        # the database.  Otherwise, we just need to upgrade it.

        def table_exists(engine, tbl):
            try:
                r = engine.execute("select * from {} limit 1".format(tbl))
                r.close()
                return True
            except Exception:
                return False

        # http://code.google.com/p/sqlalchemy-migrate/issues/detail?id=100
        # means  we cannot use the migrate.versioning.api module.  So these
        # methods perform similar wrapping functions to what is done by the API
        # functions, but without disposing of the engine.
        def upgrade(engine):
            schema = ControlledSchema(engine, self.repo_path)
            changeset = schema.changeset(None)
            with sautils.withoutSqliteForeignKeys(engine):
                for version, change in changeset:
                    log.msg('migrating schema version {} -> {}'.format(version, version + 1))
                    schema.runchange(version, change, 1)

        def check_sqlalchemy_migrate_version():
            # sqlalchemy-migrate started including a version number in 0.7; we
            # support back to 0.6.1, but not 0.6.  We'll use some discovered
            # differences between 0.6.1 and 0.6 to get that resolution.
            version = getattr(migrate, '__version__', 'old')
            if version == 'old':
                try:
                    from migrate.versioning import schemadiff
                    if hasattr(schemadiff, 'ColDiff'):
                        version = "0.6.1"
                    else:
                        version = "0.6"
                except Exception:
                    version = "0.0"
            version_tup = tuple(map(int, version.split('-', 1)[0].split('.')))
            log.msg("using SQLAlchemy-Migrate version {}".format(version))
            if version_tup < (0, 6, 1):
                raise RuntimeError(("You are using SQLAlchemy-Migrate {}. "
                                    "The minimum version is 0.6.1.").format(version))

        def version_control(engine, version=None):
            ControlledSchema.create(engine, self.repo_path, version)

        # the upgrade process must run in a db thread
        def thd(engine):
            # if the migrate_version table exists, we can just let migrate
            # take care of this process.
            if table_exists(engine, 'migrate_version'):
                r = engine.execute(
                    "select version from migrate_version limit 1")
                old_version = r.scalar()
                if old_version < 40:
                    raise EightUpgradeError()
                try:
                    upgrade(engine)
                except sa.exc.NoSuchTableError as e:  # pragma: no cover
                    if 'migration_tmp' in str(e):
                        log.err('A serious error has been encountered during the upgrade. The '
                                'previous upgrade has been likely interrupted. The database has '
                                'been damaged and automatic recovery is impossible.')
                        log.err('If you believe this is an error, please submit a bug to the '
                                'Buildbot project.')
                    raise

            # if the version table exists, then we can version_control things
            # at that version, drop the version table, and let migrate take
            # care of the rest.
            elif table_exists(engine, 'version'):
                raise EightUpgradeError()

            # otherwise, this db is new, so we don't bother using the migration engine
            # and just create the tables, and put the version directly to
            # latest
            else:
                # do some tests before getting started
                test_unicode(engine)

                log.msg("Initializing empty database")
                Model.metadata.create_all(engine)
                repo = migrate.versioning.repository.Repository(self.repo_path)

                version_control(engine, repo.latest)

        check_sqlalchemy_migrate_version()
        yield self.db.pool.do_with_engine(thd)
