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

import re
import os
from portage.xml.metadata import MetaDataXML
from portage.checksum import perform_checksum

from oslo_log import log as logging
from oslo_utils import uuidutils
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def get_category_metadata_tree(c_path):
    # Make categories_metadataDict
    categories_metadataDict = {}
    try: 
        metadata_xml_checksum = perform_checksum(c_path + "/metadata.xml", "SHA256")[0]
    except Exception as e:
        return None
    categories_metadataDict['metadata_xml_checksum'] = metadata_xml_checksum
    pkg_md = MetaDataXML(c_path + "/metadata.xml", None)
    if pkg_md.descriptions():
        metadata_xml_descriptions_tree = re.sub('\t', '', pkg_md.descriptions()[0])
        metadata_xml_descriptions_tree = re.sub('\n', '', metadata_xml_descriptions_tree)
    else:
        metadata_xml_descriptions_tree = ''
    categories_metadataDict['metadata_xml_descriptions'] = metadata_xml_descriptions_tree
    return categories_metadataDict

def create_cm_db(context, category_db, category_metadata_tree):
    category_metadata_db = objects.category_metadata.CategoryMetadata()
    category_metadata_db.category_uuid = category_db.uuid
    category_metadata_db.description = category_metadata_tree['metadata_xml_descriptions']
    category_metadata_db.checksum = category_metadata_tree['metadata_xml_checksum']
    category_metadata_db.create(context)
    return category_metadata_db

def create_c_db(context, category):
    category_db = objects.category.Category()
    category_db.uuid = uuidutils.generate_uuid()
    category_db.name = category
    category_db.status = 'in-progress'
    category_db.create(context)
    return category_db

def update_cm_db(context, category_metadata_db, category_metadata_tree):
    category_metadata_db.description = category_metadata_tree['metadata_xml_descriptions']
    category_metadata_db.checksum = category_metadata_tree['metadata_xml_checksum']
    category_metadata_db.save(context)

def check_c_db(context, category, repo_db):
    LOG.debug("Checking %s", category)
    c_path = CONF.repopath + '/' + repo_db.name + '.git/' + category
    category_db = objects.category.Category.get_by_name(context, category)
    if not os.path.isdir(c_path):
        LOG.error("Path %s is not found for %s", c_path, category)
        if category_db is not None:
            category_db.deleted = True
            category_db.save(context)
            LOG.info("Deleting %s in the database", category)
            return True
        return False
    if category_db is None:
        LOG.info("Adding %s to the database", category)
        category_db = create_c_db(context, category)
    #if category_db.status == 'in-progress':
    #    return True
    category_db.status = 'in-progress'
    category_db.save(context)
    category_metadata_tree = get_category_metadata_tree(c_path)
    if category_metadata_tree is None:
        category_db.status = 'failed'
        category_db.save(context)
        LOG.error("Failed to get metadata for %s", category)
        return False
    category_metadata_db = objects.category_metadata.CategoryMetadata.get_by_uuid(context, category_db.uuid)
    if category_metadata_db is None:
        category_metadata_db = create_cm_db(context, category_db, category_metadata_tree)
    if category_metadata_db.checksum != category_metadata_tree['metadata_xml_checksum']:
        update_cm_db(context, category_metadata_db, category_metadata_tree)
        LOG.debug("Update %s metadata", category)
    category_db.status = 'completed'
    category_db.save(context)
    return True

def destroy_c_db(context, category):
    category_db = objects.category.Category.get_by_name(context, category)
    category_db.destroy(context)
    return True

def remove_c_db(context, category):
    category_db = objects.category.Category.get_by_name(context, category)
    if category_db.deleted is True:
        category_metadata_db = objects.category_metadata.CategoryMetadata.get_by_uuid(context, category_db.uuid)
        category_metadata_db.remove(context)
        category_db.remove(context)
    else:
        return False
    return True
