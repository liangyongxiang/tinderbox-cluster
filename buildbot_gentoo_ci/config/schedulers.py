# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import schedulers, util

@util.renderer
def builderUpdateDbNames(self, props):
    builders = set()
    for f in props.files:
        if f.endswith('.ebuild'):
            builders.add('update_db_packages')
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
        builderNames=['update_db_packages'],
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
    s = []
    s.append(test_updatedb)
    #s.append(scheduler_update_db)
    return s
