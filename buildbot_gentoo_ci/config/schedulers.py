# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import schedulers, util

@util.renderer
def builderUpdateDbNames(self, props):
    builders = set()
    for f in props.files:
        if f.endswith('.ebuild'):
            builders.add('update_db_check')
    return list(builders)

@util.renderer
def cpvUpdateDb(props):
    cpv_changes = []
    for f in props.files:
        if f.endswith('.ebuild'):
            cppv = f.split('.eb', 0)
            cpv = cppv.split('/', 0) + '/' + cppv.split('/', 2)
            if not cpv in cpv_changes:
                cpv_changes.append(cpv)
    return cpv_changes

def gentoo_schedulers():
    scheduler_update_db = schedulers.SingleBranchScheduler(
        name='scheduler_update_db',
        treeStableTimer=60,
        properties = {
                        'cpv_changes' : cpvUpdateDb,
                    },
        builderNames = builderUpdateDbNames,
        change_filter=util.ChangeFilter(branch='master'),
    )
    test_updatedb = schedulers.ForceScheduler(
        name="force",
        buttonName="pushMe!",
        label="My nice Force form",
        builderNames=['update_db_check'],
        # A completely customized property list.  The name of the
        # property is the name of the parameter
        properties=[
            util.NestedParameter(name="options", label="Build Options",
                    layout="vertical", fields=[
            util.StringParameter(name="cpv_changes",
                    label="Package to check",
                    default="dev-lang/python-3.8", size=80),
            util.StringParameter(name="repository",
                    label="repo",
                    default="gentoo", size=80),
            ])
    ])
    update_cpv_data = schedulers.Triggerable(name="update_cpv_data",
                               builderNames=["update_cpv_data"])
    update_v_data = schedulers.Triggerable(name="update_v_data",
                               builderNames=["update_v_data"])
    build_request_data = schedulers.Triggerable(name="build_request_data",
                               builderNames=["build_request_data"])
    s = []
    s.append(test_updatedb)
    #s.append(scheduler_update_db)
    s.append(update_cpv_data)
    s.append(update_v_data)
    s.append(build_request_data)
    return s
