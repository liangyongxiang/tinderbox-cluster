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

from oslo_config import cfg

scheduler_group = cfg.OptGroup(name="scheduler",
                               title="Scheduler configuration")

scheduler_opts = [
    cfg.StrOpt(
        'git_mirror_url',
        help="""
Explicitly specify the mirror git url.
"""),
    cfg.StrOpt(
        'db_project_repo',
        help="""
Explicitly specify the database project repo.
"""),
]

def register_opts(conf):
    conf.register_group(scheduler_group)
    conf.register_opts(scheduler_opts, group=scheduler_group)

def list_opts():
    return {scheduler_group: scheduler_opts}
