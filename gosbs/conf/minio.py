#
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


minio_group = cfg.OptGroup(
    name='minio',
    title='MinIO Options',
    help='Configuration options for the MinIO service')

minio_opts = [
    cfg.StrOpt('url',
               default='',
               help=''),
    cfg.StrOpt('username',
               default='',
               help=''),
    cfg.StrOpt('password',
               secret=True,
               default='True',
               help=''),
]


def register_opts(conf):
    conf.register_group(minio_group)
    conf.register_opts(minio_opts, group=minio_group)


def list_opts():
    return {minio_group: minio_opts}
