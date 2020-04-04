# Copyright 1999-2020 Gentoo Authors
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import git

import portage
from portage.xml.metadata import MetaDataXML
from portage.checksum import perform_checksum

from oslo_log import log as logging
from oslo_utils import uuidutils

from gosbs import objects
from gosbs.scheduler.email import check_email_db
from gosbs.scheduler.ebuild import check_cpv_db, deleted_cpv_db
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def get_all_cp_from_repo(myportdb, repopath):
    repo_dir_list = []
    repo_dir_list.append(repopath)
    # Get the package list from the repo
    return myportdb.cp_all(trees=repo_dir_list)

def get_git_changelog_text(repodir, cp):
    n = '5'
    git_log_pkg = ''
    g = git.Git(repodir)
    git_log_pkg = g.log('-n ' + n, '--grep=' + cp)
    return git_log_pkg

def get_package_metadataDict(repodir, cp):
    # Make package_metadataDict
    package_metadataDict = {}
    try:
        package_metadataDict['metadata_xml_checksum'] = perform_checksum(repodir + "/" + cp + "/metadata.xml", "SHA256")[0]
    except Exception as e:
        package_metadataDict['metadata_xml_checksum'] = False
        return package_metadataDict
    md_email_list = []
    pkg_md = MetaDataXML(repodir + "/" + cp + "/metadata.xml", None)
    tmp_descriptions = pkg_md.descriptions()
    if tmp_descriptions:
        package_metadataDict['metadata_xml_descriptions'] = tmp_descriptions[0]
    else:
        package_metadataDict['metadata_xml_descriptions'] = ''
    tmp_herds = pkg_md.herds()
    if tmp_herds:
        package_metadataDict['metadata_xml_herds'] = tmp_herds[0]
        md_email_list.append(package_metadataDict['metadata_xml_herds'] + '@gentoo.org')
    for maint in pkg_md.maintainers():
        md_email_list.append(maint.email)
    if md_email_list != []:
        package_metadataDict['metadata_xml_email'] = md_email_list
    else:
        md_email_list.append('maintainer-needed@gentoo.org')
        package_metadataDict['metadata_xml_email'] = md_email_list
            #log_msg = "Metadata file %s missing Email. Setting it to maintainer-needed" % (pkgdir + "/metadata.xml")
            #write_log(self._session, log_msg, "warning", self._config_id, 'packages.get_package_metadataDict')
    package_metadataDict['git_changlog'] = get_git_changelog_text(repodir, cp)
    return package_metadataDict

def update_cp_metadata_db(context, cp, repo_name, package_metadata_db):
    repodir = CONF.repopath + '/' + repo_name + '.git'
    package_metadataDict = get_package_metadataDict(repodir, cp)
    if not package_metadataDict['metadata_xml_checksum']:
        return False
    package_metadata_db.gitlog = package_metadataDict['git_changlog']
    package_metadata_db.description = package_metadataDict['metadata_xml_descriptions']
    package_metadata_db.checksum = package_metadataDict['metadata_xml_checksum']
    package_metadata_db.save(context)
    return package_metadataDict['metadata_xml_email']
    
def create_cp_metadata_db(context, cp, repo_name, package_uuid):
    repodir = CONF.repopath + '/' + repo_name + '.git'
    package_metadataDict = get_package_metadataDict(repodir, cp)
    if not package_metadataDict['metadata_xml_checksum']:
        return False
    package_metadata_db = objects.package_metadata.PackageMetadata()
    package_metadata_db.package_uuid = package_uuid
    package_metadata_db.gitlog = package_metadataDict['git_changlog']
    package_metadata_db.description = package_metadataDict['metadata_xml_descriptions']
    package_metadata_db.checksum = package_metadataDict['metadata_xml_checksum']
    package_metadata_db.create(context)
    return package_metadataDict['metadata_xml_email']

def create_cp_email_db(context, email_id, package_uuid):
    package_email_db = objects.package_email.PackageEmail()
    package_email_db.package_uuid = package_uuid
    package_email_db.email_id = email_id
    package_email_db.create(context)

def check_cp_email_db(context, metadata_xml_email, package_uuid):
    filters = { 'package_uuid' : package_uuid }
    for package_email in metadata_xml_email:
        email_id = check_email_db(context, package_email)
        package_email_db = objects.package_email.PackageEmail.get_by_email_id(context, email_id, filters=filters)
        if package_email_db is None:
            create_cp_email_db(context, email_id, package_uuid)
    return True

def check_cp_metadata_db(context, cp, repo_name, package_uuid):
    repodir = CONF.repopath + '/' + repo_name + '.git'
    succes = True
    package_metadata_db = objects.package_metadata.PackageMetadata.get_by_uuid(context, package_uuid)
    if package_metadata_db is None:
        LOG.debug("Adding %s metadata", cp)
        metadata_xml_email = create_cp_metadata_db(context, cp, repo_name, package_uuid)
        succes = check_cp_email_db(context, metadata_xml_email, package_uuid)
    else:
        package_metadata_tree_checksum = perform_checksum(repodir + "/" + cp + "/metadata.xml", "SHA256")[0]
        if package_metadata_tree_checksum != package_metadata_db.checksum:
            LOG.debug("Update %s metadata", cp)
            metadata_xml_email = update_cp_metadata_db(context, cp, repo_name, package_metadata_db)
            succes = check_cp_email_db(context, metadata_xml_email, package_uuid)
    return succes

def deleted_cp_db(context, package_db):
    filters = { 'deleted' : False,
                'package_uuid' : package_db.uuid,
            }
    for ebuild_db in objects.ebuild.EbuildList.get_all(context, filters=filters):
        LOG.info("Deleting %s in the database", ebuild_db.version)
        deleted_cpv_db(context, ebuild_db.uuid)
    package_db.deleted = True
    package_db.status = 'completed'
    package_db.save(context)

def create_cp_db(context, package, repo_db, category_db):
    package_db = objects.package.Package()
    package_db.uuid = uuidutils.generate_uuid()
    package_db.name = package
    package_db.status = 'in-progress'
    package_db.category_uuid = category_db.uuid
    package_db.repo_uuid = repo_db.uuid
    package_db.create(context)
    return package_db
    
def check_cp_db(context, myportdb, cp, repo_db, category_db):
    package = cp.split('/')[1]
    cp_path = CONF.repopath + '/' + repo_db.name + '.git/' + cp
    filters = { 'repo_uuid' : repo_db.uuid,
               'category_uuid' : category_db.uuid,
               'deleted' : False,
            }
    package_db = objects.package.Package.get_by_name(context, package, filters=filters)
    if not os.path.isdir(cp_path) and package_db is None:
        LOG.error("Path %s is not found for %s", cp_path, cp)
        return False, {}
    elif not os.path.isdir(cp_path) and package_db is not None:
        LOG.info("Deleting %s in the database", cp)
        deleted_cp_db(context, package_db)
        return True, {}
    elif os.path.isdir(cp_path) and package_db is None:
        LOG.info("Adding %s to the database", cp)
        package_db = create_cp_db(context, package, repo_db, category_db)
    package_db.status = 'in-progress'
    package_db.save(context)
    succes1 = check_cp_metadata_db(context, cp, repo_db.name, package_db.uuid)
    succes2, ebuild_version_tree_dict_new = check_cpv_db(context, myportdb, cp, repo_db, package_db.uuid)
    if not succes1 or not succes2:
        package_db.status = 'faild'
        package_db.save(context)
        return False, ebuild_version_tree_dict_new
    package_db.status = 'completed'
    package_db.save(context)
    return True, ebuild_version_tree_dict_new
