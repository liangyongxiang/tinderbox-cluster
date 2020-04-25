# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import git
import re
import portage
import pdb
from portage.checksum import perform_checksum

from oslo_log import log as logging
from oslo_utils import uuidutils
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF

LOG = logging.getLogger(__name__)

def get_all_cpv_from_package(myportdb, cp, repo_path):
    mytree = []
    mytree.append(repo_path)
    return myportdb.cp_list(cp, use_cache=1, mytree=mytree)

def get_git_log_ebuild(repodir, ebuild_file):
    git_log_ebuild = ''
    g = git.Git(repodir)
    index = 1
    git_log_dict = {}
    for line in g.log('-n 1', ebuild_file).splitlines():
        git_log_dict[index] = line
        index = index + 1
    git_ebuild_commit = re.sub('commit ', '', git_log_dict[1])
    git_ebuild_commit_msg = re.sub('    ', '', git_log_dict[5])
    return git_ebuild_commit, git_ebuild_commit_msg

def get_ebuild_metadata(myportdb, cpv, repo):
    # Get the auxdbkeys infos for the ebuild
    try:
        ebuild_auxdb_list = myportdb.aux_get(cpv, portage.auxdbkeys, myrepo=repo)
    except:
        ebuild_auxdb_list = False
        LOG.error("Failed to get aux data for %s", cpv)
    else:
        for i in range(len(ebuild_auxdb_list)):
            if ebuild_auxdb_list[i] == '':
                ebuild_auxdb_list[i] = ''
    return ebuild_auxdb_list

def create_cpv_db(context, ebuild_version_tree, ebuild_version_checksum_tree, package_uuid):
    ebuild_version_db = objects.ebuild.Ebuild()
    ebuild_version_db.ebuild_uuid = uuidutils.generate_uuid()
    ebuild_version_db.version = ebuild_version_tree
    ebuild_version_db.checksum = ebuild_version_checksum_tree
    ebuild_version_db.package_uuid = package_uuid
    ebuild_version_db.create(context)
    return ebuild_version_db

def deleted_cpv_db(context, uuid):
    ebuild_version_db = objects.ebuild.Ebuild.get_by_uuid(context, uuid)
    ebuild_version_db.deleted = True
    ebuild_version_db.save(context)

def create_use_db(context, use):
    use_db = objects.use.Use()
    use_db.flag = use
    use_db.description = ''
    use_db.create(context)
    return use_db

def check_use_db(context, use):
    use_db = objects.use.Use.get_by_name(context, use)
    if use_db is None:
        use_db = create_use_db(context, use)
    return use_db.id

def create_cpv_use_db(context, ebuild_version_uuid, ebuild_version_metadata_tree):
    for iuse in ebuild_version_metadata_tree[10].split():
        print('iuse')
        print(iuse)
        status = False
        if iuse[0] in ["+"]:
            iuse = iuse[1:]
            status = True
        elif iuse[0] in ["-"]:
            iuse = iuse[1:]
        iuse_id = check_use_db(context, iuse)
        ebuild_iuse_db = objects.ebuild_iuse.EbuildIUse()
        ebuild_iuse_db.ebuild_uuid = ebuild_version_uuid
        ebuild_iuse_db.use_id = iuse_id
        ebuild_iuse_db.status = status
        ebuild_iuse_db.create(context)

def create_keyword_db(context, keyword):
    keyword_db = objects.keyword.Keyword()
    keyword_db.keyword = keyword
    keyword_db.create(context)
    return keyword_db

def check_keyword_db(context, keyword):
    keyword_db = objects.keyword.Keyword.get_by_name(context, keyword)
    if keyword_db is None:
        keyword_db = create_keyword_db(context, keyword)
    return keyword_db.id

def create_cpv_keyword_db(context, ebuild_version_uuid, ebuild_version_metadata_tree):
    for keyword in ebuild_version_metadata_tree[8].split():
        status = 'stable'
        if keyword[0] in ["~"]:
            keyword = keyword[1:]
            status = 'unstable'
        elif keyword[0] in ["-"]:
            keyword = keyword[1:]
            status = 'negative'
        keyword_id = check_keyword_db(context, keyword)
        ebuild_keyword_db = objects.ebuild_keyword.EbuildKeyword()
        ebuild_keyword_db.ebuild_uuid = ebuild_version_uuid
        ebuild_keyword_db.keyword_id = keyword_id
        ebuild_keyword_db.status = status
        ebuild_keyword_db.create(context)

def create_restriction_db(context, restriction):
    restriction_db = objects.restriction.Restriction()
    restriction_db.restriction = restriction
    restriction_db.create(context)
    return restriction_db

def check_restriction_db(context, restriction):
    restriction_db = objects.restriction.Restriction.get_by_name(context, restriction)
    if restriction_db is None:
        restriction_db = create_restriction_db(context, restriction)
    return restriction_db.id

def create_cpv_restriction_db(context, ebuild_version_uuid, ebuild_version_metadata_tree):
    for restriction in ebuild_version_metadata_tree[4].split():
        print('restriction')
        print(restriction)
        if restriction in ["!"]:
            restriction = restriction[1:]
        if restriction in ["?"]:
            restriction = restriction[:1]
        if restriction != '(' or restriction != ')':
            restriction_id = check_restriction_db(context, restriction)
            ebuild_restriction_db = objects.ebuild_restriction.EbuildRestriction()
            ebuild_restriction_db.ebuild_uuid = ebuild_version_uuid
            ebuild_restriction_db.restriction_id = restriction_id
            ebuild_restriction_db.create(context)

def create_cpv_metadata_db(context, myportdb, cpv, ebuild_file, ebuild_version_db, repo_db):
    repo_path = CONF.repopath + '/' + repo_db.name + '.git'
    git_commit, git_commit_msg = get_git_log_ebuild(repo_path, ebuild_file)
    ebuild_version_metadata_tree = get_ebuild_metadata(myportdb, cpv, repo_db.name)
    print(ebuild_version_metadata_tree)
    ebuild_metadata_db = objects.ebuild_metadata.EbuildMetadata()
    ebuild_metadata_db.ebuild_uuid = ebuild_version_db.uuid
    ebuild_metadata_db.commit = git_commit
    ebuild_metadata_db.commit_msg = git_commit_msg
    ebuild_metadata_db.description = ebuild_version_metadata_tree[7]
    ebuild_metadata_db.slot = ebuild_version_metadata_tree[2]
    ebuild_metadata_db.homepage = ebuild_version_metadata_tree[5]
    ebuild_metadata_db.license = ebuild_version_metadata_tree[6]
    ebuild_metadata_db.create(context)
    create_cpv_restriction_db(context, ebuild_version_db.uuid, ebuild_version_metadata_tree)
    create_cpv_use_db(context, ebuild_version_db.uuid, ebuild_version_metadata_tree)
    create_cpv_keyword_db(context, ebuild_version_db.uuid, ebuild_version_metadata_tree)
    return True

def check_cpv_db(context, myportdb, cp, repo_db, package_uuid):
    repo_path = CONF.repopath + '/' + repo_db.name + '.git'
    filters = { 'deleted' : False,
                'package_uuid' : package_uuid,
            }
    ebuild_version_tree_list = []
    ebuild_version_tree_dict_new = {}
    succes = True
    #pdb.set_trace()
    for cpv in sorted(get_all_cpv_from_package(myportdb, cp, repo_path)):
        LOG.debug("Checking %s", cpv)
        print(cpv)
        ebuild_version_tree = portage.versions.cpv_getversion(cpv)
        package = portage.versions.catpkgsplit(cpv)[1]
        ebuild_file = repo_path + "/" + cp + "/" + package + "-" + ebuild_version_tree + ".ebuild"
        if not os.path.isfile(ebuild_file):
            LOG.error("File %s is not found for %s", ebuild_file, cpv)
            return False, ebuild_version_tree_dict_new
        ebuild_version_checksum_tree = perform_checksum(ebuild_file, "SHA256")[0]
        ebuild_version_db = objects.ebuild.Ebuild.get_by_name(context, ebuild_version_tree, filters=filters)
        if ebuild_version_db is None or ebuild_version_db.checksum != ebuild_version_checksum_tree:
            if ebuild_version_db is not None and ebuild_version_db.checksum != ebuild_version_checksum_tree:
                LOG.debug("Update %s", cpv)
                deleted_cpv_db(context, ebuild_version_db.uuid)
            else:
                LOG.info("Adding %s to the database", cpv)
            ebuild_version_db = create_cpv_db(context, ebuild_version_tree, ebuild_version_checksum_tree, package_uuid)
            succes = create_cpv_metadata_db(context, myportdb, cpv, ebuild_file, ebuild_version_db, repo_db)
            ebuild_version_tree_dict_new[cpv] = ebuild_version_db.uuid
        ebuild_version_tree_list.append(ebuild_version_tree)
    print('check old ebuilds')
    for ebuild_db in objects.ebuild.EbuildList.get_all(context, filters=filters):
        if not ebuild_db.version in ebuild_version_tree_list:
            LOG.info("Deleting %s in the database", ebuild_db.version)
            deleted_cpv_db(context, ebuild_db.uuid)
    return succes, ebuild_version_tree_dict_new
