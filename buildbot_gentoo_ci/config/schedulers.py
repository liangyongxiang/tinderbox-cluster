# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import schedulers, util

@util.renderer
def builderUpdateDbNames(props):
    builders = set()
    for f in props.files:
        if f.endswith('.ebuild'):
            builders.add('update_db_check')
    return list(builders)

@util.renderer
def getGitChanges(props):
    k = props.changes[0]
    change_data = {}
    print(k)
    change_data['cpvs'] = []
    for v in k['files']:
        if v.endswith('.ebuild'):
            c = v.split('/')[0]
            p = v.split('/')[1]
            pv = v.split('/')[2][:-7]
            cpv = c + '/' + pv
            change_data['cp'] = c + '/' + p
            change_data['cpvs'].append(cpv)
    if k['repository'].endswith('.git'):
        for v in k['repository'].split('/'):
            if v.endswith('.git'):
                # on gitlab we use gentoo-ci as fork of gentoo
                if v[:-4] == 'gentoo-ci':
                    change_data['repository'] = 'gentoo'
                else:
                    change_data['repository'] = v[:-4]
    change_data['author'] = k['author']
    change_data['committer'] = k['committer']
    change_data['comments'] = k['comments']
    change_data['revision'] = k['revision']
    change_data['timestamp'] = k['when_timestamp']
    change_data['branch'] = k['branch']
    return change_data

def gentoo_schedulers():
    scheduler_update_db = schedulers.SingleBranchScheduler(
        name='scheduler_update_db',
        treeStableTimer=0,
        properties = dict(
                        change_data = getGitChanges
                        ),
        builderNames = builderUpdateDbNames,
        change_filter=util.ChangeFilter(branch='master'),
    )
    create_stage4 = schedulers.ForceScheduler(
        name="create_stage4",
        buttonName="Create stage4",
        label="My nice create stage4 form",
        builderNames=['run_build_stage4_request'],
        # A completely customized property list.  The name of the
        # property is the name of the parameter
        properties=[
            util.StringParameter(name="project_uuid",
                    label="Project uuid",
                    default="e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd", size=36),
            util.StringParameter(name="worker",
                    label="New worker uuid",
                    default="a89c2c1a-46e0-4ded-81dd-c51afeb7fcfd", size=36),
            util.StringParameter(name="type",
                    label="type of worker",
                    default="docker", size=10),
        ])
    update_cpv_data = schedulers.Triggerable(name="update_cpv_data",
                               builderNames=["update_cpv_data"])
    update_repo_check = schedulers.Triggerable(name="update_repo_check",
                               builderNames=["update_repo_check"])
    update_v_data = schedulers.Triggerable(name="update_v_data",
                               builderNames=["update_v_data"])
    build_request_data = schedulers.Triggerable(name="build_request_data",
                               builderNames=["build_request_data"])
    run_build_request = schedulers.Triggerable(name="run_build_request",
                               builderNames=["run_build_request"])
    parse_build_log = schedulers.Triggerable(name="parse_build_log",
                               builderNames=["parse_build_log"])
    run_build_stage4_request = schedulers.Triggerable(name="run_build_stage4_request",
                               builderNames=["run_build_stage4_request"])
    s = []
    s.append(create_stage4)
    s.append(scheduler_update_db)
    s.append(update_repo_check)
    s.append(update_cpv_data)
    s.append(update_v_data)
    s.append(build_request_data)
    s.append(run_build_request)
    s.append(parse_build_log)
    return s
