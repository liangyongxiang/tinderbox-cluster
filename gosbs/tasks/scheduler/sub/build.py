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

from oslo_log import log as logging

from gosbs.common.portage_settings import get_portage_settings, clean_portage_settings
from gosbs.common.flags import get_all_cpv_use, filter_flags, get_iuse, reduce_flags
from gosbs import objects

LOG = logging.getLogger(__name__)

def build_sub_task(context, cp, ebuild_version_tree_dict_new, repo_db):
    user_db = objects.user.User.get_by_name(context, 'scheduler')
    filters = { 'build' : True,
               'repo_uuid' : repo_db.uuid,
               }
    for project_repo_db in objects.project_repo.ProjectRepoList.get_all(context, filters=filters):
        project_db = objects.project.Project.get_by_uuid(context, project_repo_db.project_uuid)
        if project_db.active and project_db.auto:
            project_metadata_db = objects.project_metadata.ProjectMetadata.get_by_uuid(context, project_db.uuid)
            mysettings, myportdb = get_portage_settings(context, project_metadata_db, project_db.name)
            build_cpv = myportdb.xmatch('bestmatch-visible', cp)
            if build_cpv != "" and build_cpv in ebuild_version_tree_dict_new:
                (final_use, use_expand_hidden, usemasked, useforced) = \
                    get_all_cpv_use(build_cpv, myportdb, mysettings)
                iuse_flags = filter_flags(get_iuse(build_cpv, myportdb), use_expand_hidden,
                            usemasked, useforced, mysettings)
                final_flags = filter_flags(final_use,  use_expand_hidden,
                            usemasked, useforced, mysettings)
                iuse_flags2 = reduce_flags(iuse_flags)
                iuse_flags_list = list(set(iuse_flags2))
                use_disable = list(set(iuse_flags_list).difference(set(final_flags)))
                # Make a dict with enable and disable use flags for ebuildqueuedwithuses
                use_flagsDict = {}
                for x in final_flags:
                    use_flagsDict[x] = True
                for x in use_disable:
                    use_flagsDict[x] = False
                enable_test = False
                if project_repo_db.test and not "test" in usemasked:
                    enable_test = True
                restrictions_filters = { 'ebuild_uuid' : ebuild_version_tree_dict_new[build_cpv], }
                restrictions_list = objects.ebuild_restriction.EbuildRestrictionList.get_all(context, filters=restrictions_filters)
                if not restrictions_list is None:
                    if ("test" in restrictions_list or "fetch" in restrictions_list) and "test" in use_flagsDict:
                        enable_test = False
                if "test" in use_flagsDict and enable_test:
                    use_flagsDict['test'] = True
                project_build_db = objects.project_build.ProjectBuild()
                project_build_db.project_uuid = project_db.uuid
                project_build_db.ebuild_uuid = ebuild_version_tree_dict_new[build_cpv]
                project_build_db.status = 'waiting'
                project_build_db.user_id = user_db.id
                project_build_db.create(context)
                for k, v in use_flagsDict.items():
                    iuse_db = objects.use.Use.get_by_name(context, k)
                    build_iuse_db = objects.build_iuse.BuildIUse()
                    build_iuse_db.build_uuid = project_build_db.uuid
                    build_iuse_db.use_id = iuse_db.id
                    build_iuse_db.status = v
                    build_iuse_db.create(context)
            clean_portage_settings(myportdb)
    return True
