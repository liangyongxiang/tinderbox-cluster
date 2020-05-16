# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
from portage.checksum import perform_checksum

from oslo_log import log as logging
from gosbs import objects
from gosbs._emerge.actions import load_emerge_config
from gosbs._emerge.main import emerge_main
from gosbs.common.flags import get_build_use
from gosbs.builder.binary import destroy_local_binary
from gosbs.builder.depclean import do_depclean
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def get_build_job(context, project_db):
    filters = {
               'project_uuid' : project_db.uuid,
               'status' : 'waiting',
               'deleted' : False,
               }
    project_build_db = objects.project_build.ProjectBuild.get_by_filters(context, filters)
    if project_build_db is None:
        return True, {}
    ebuild_db = objects.ebuild.Ebuild.get_by_uuid(context, project_build_db.ebuild_uuid)
    package_db = objects.package.Package.get_by_uuid(context, ebuild_db.package_uuid)
    repo_db = objects.repo.Repo.get_by_uuid(context, package_db.repo_uuid)
    category_db = objects.category.Category.get_by_uuid(context, package_db.category_uuid)
    cp = category_db.name + '/' + package_db.name
    cpv = cp + '-' + ebuild_db.version
    repo_path = CONF.repopath + '/' + repo_db.name + '.git'
    ebuild_file = repo_path + "/" + cp + "/" + package_db.name + "-" + ebuild_db.version + ".ebuild"
    if not os.path.isfile(ebuild_file):
            LOG.error("File %s is not found for %s", ebuild_file, cpv)
            project_build_db.status = 'failed'
            project_build_db.save(context)
            return False, {}
    ebuild_tree_checksum = perform_checksum(ebuild_file, "SHA256")[0]
    if ebuild_tree_checksum != ebuild_db.checksum:
        LOG.error("File %s with wrong checksum", ebuild_file)
        project_build_db.status = 'failed'
        project_build_db.save(context)
        return False, {}
    build_job = {}
    build_job['ebuild'] = ebuild_db
    build_job['build'] = project_build_db
    build_job['cpv'] = cpv
    build_job['repo'] = repo_db
    build_job['category'] = category_db
    build_job['package'] = package_db
    return True, build_job

def check_build_use(context, build_job, mysettings, myportdb):
    build_tree_use, usemasked = get_build_use(build_job['cpv'], mysettings, myportdb)
    filters = {
        'build_uuid' : build_job['build'].uuid,
        }
    build_db_use = {}
    for build_use_db in objects.build_iuse.BuildIUseList.get_all(context, filters=filters):
        use_db = objects.use.Use.get_by_id(context, build_use_db.use_id)
        build_db_use[use_db.flag] = build_use_db.status
    build_use_flags = {}
    for k, v in build_tree_use.items():
        if build_db_use[k] != v:
            if build_db_use[k]:
                build_use_flags[k] = True
            else:
                build_use_flags[k] = False
    return build_use_flags

def set_features_packages(context, build_job, build_use, mysettings):
    restrictions = {}
    filters = {
        'ebuild_uuid' : build_job['ebuild'].uuid,
        }
    for ebuild_restriction_db in objects.ebuild_restriction.EbuildRestrictionList.get_all(context, filters=filters):
        restriction_db = objects.restriction.Restriction.get_by_id(context, ebuild_restriction_db.restriction_id)
        restrictions[restriction_db.restriction] = True
    if 'test' in restrictions or "test" in build_use or "test" in mysettings.features:
        enable_test_features = False
        disable_test_features = False
        if 'test' in restrictions and 'test' in mysettings.features:
            disable_test_features = True
        if "test" in build_use:
            if build_use['test'] is False and "test" in mysettings.features:
                disable_test_features = True
            if build_use['test'] is True and not disable_test_features and "test" not in mysettings.features:
                enable_test_features = True
        if disable_test_features or enable_test_features:
            filetext = '=' + build_job['cpv'] + ' '
            if disable_test_features:
                filetext = filetext + 'notest.conf'
            if enable_test_features:
                filetext = filetext + 'test.conf'    
            LOG.debug("features filetext: %s" % filetext)
            with open("/etc/portage/package.env/99_env", "a") as f:
                f.write(filetext)
                f.write('\n')
                f.close
    return True

def set_use_packages(context, build_job, build_use):
    if build_use != {}:
        filetext = '=' + build_job['cpv']
        for k, v in build_use.items():
            if v:
                filetext = filetext + ' ' + k
            else:
                filetext = filetext + ' -' + k
        LOG.debug("use filetext: %s" % filetext)
        with open("/etc/portage/package.use/99_autounmask", "a") as f:
            f.write(filetext)
            f.write('\n')
            f.close
    return True

def destroy_binary(context, build_job, mysettings, project_db, service_uuid):
    destroy_local_binary(context, build_job, project_db, service_uuid, mysettings)
    #destroy_objectstor_binary(context, build_job, project_db)

def emeerge_cmd_options(context, build_job, project_options_db):
    argscmd = []
    if project_options_db.oneshot:
        argscmd.append('--oneshot')
    if project_options_db.usepkg:
        argscmd.append('--usepkg')
    if project_options_db.buildpkg:
        argscmd.append('--buildpkg')
    argscmd.append('=' + build_job['cpv'])
    return argscmd

def touch_package_settings():
    try:
        os.remove("/etc/portage/package.use/99_autounmask")
        with open("/etc/portage/package.use/99_autounmask", "a") as f:
            f.close
        os.remove("/etc/portage/package.env/99_env")
        with open("/etc/portage/package.env/99_env/", "a") as f:
            f.close
    except:
        pass

def task(context, service_uuid):
    project_db = objects.project.Project.get_by_name(context, CONF.builder.project)
    project_metadata_db = objects.project_metadata.ProjectMetadata.get_by_uuid(context, project_db.uuid)
    project_options_db = objects.project_option.ProjectOption.get_by_uuid(context, project_db.uuid)
    succes, build_job = get_build_job(context, project_db)
    if succes and build_job == {}:
        return
    elif not succes and build_job == {}:
        return
    elif succes and build_job != {}:
        mysettings, trees, mtimedb = load_emerge_config()
        myportdb = trees[mysettings["ROOT"]]["porttree"].dbapi
        build_use = check_build_use(context, build_job, mysettings, myportdb)
        succes = set_features_packages(context, build_job, build_use, mysettings)
        succes = set_use_packages(context, build_job, build_use)
        if project_options_db.removebin:
            destroy_binary(context, build_job, mysettings, project_db, service_uuid)
        argscmd = emeerge_cmd_options(context, build_job, project_options_db)
        build_fail = emerge_main(context, build_job, args=argscmd)
        if project_options_db.depclean:
            depclean_fail = do_depclean(context)
        touch_package_settings()
    return
