# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import util
from buildbot_gentoo_ci.config import buildfactorys

def gentoo_builders(b=[]):
    # FIXME: get workers from db
    b.append(util.BuilderConfig(
        name='update_db_check',
        workername='updatedb_1',
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_check()
        )
    )
    # FIXME: get workers from db
    # Use multiplay workers depend on Property(cpv)
    # if cp do not match next one, use diffrent worker then
    # or first cp have done its buildsteps.
    b.append(util.BuilderConfig(
        name='update_cpv_data',
        workername='updatedb_1',
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_cp()
        )
    )
    # FIXME: get workers from db
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='update_v_data',
        workername='updatedb_1',
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_v()
        )
    )
    # FIXME: get workers from db
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='build_request_data',
        workername='updatedb_1',
        collapseRequests=False,
        factory=buildfactorys.build_request_check()
        )
    )
    # FIXME: get workers from db
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='run_build_request',
        workername='bot-test',
        collapseRequests=False,
        factory=buildfactorys.run_build_request()
        )
    )
    # FIXME: get workers from db
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='parse_build_log',
        workername='updatedb_1',
        collapseRequests=False,
        factory=buildfactorys.parse_build_log()
        )
    )
    return b
