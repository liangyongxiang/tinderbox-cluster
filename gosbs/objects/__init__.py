#    Copyright 2013 IBM Corp.
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

# Origin https://github.com/openstack/nova/blob/master/nova/objects/__init__.py

# NOTE(comstud): You may scratch your head as you see code that imports
# this module and then accesses attributes for objects such as Instance,
# etc, yet you do not see these attributes in here. Never fear, there is
# a little bit of magic. When objects are registered, an attribute is set
# on this module automatically, pointing to the newest/latest version of
# the object.


def register_all():
    # NOTE(danms): You must make sure your object gets imported in this
    # function in order for it to be registered by services that may
    # need to receive it via RPC.
    __import__('gosbs.objects.build_iuse')
    __import__('gosbs.objects.category')
    __import__('gosbs.objects.category_metadata')
    __import__('gosbs.objects.ebuild')
    __import__('gosbs.objects.ebuild_metadata')
    __import__('gosbs.objects.ebuild_iuse')
    __import__('gosbs.objects.ebuild_keyword')
    __import__('gosbs.objects.ebuild_restriction')
    __import__('gosbs.objects.email')
    __import__('gosbs.objects.keyword')
    __import__('gosbs.objects.package')
    __import__('gosbs.objects.package_metadata')
    __import__('gosbs.objects.package_email')
    __import__('gosbs.objects.project')
    __import__('gosbs.objects.project_metadata')
    __import__('gosbs.objects.project_build')
    __import__('gosbs.objects.project_repo')
    __import__('gosbs.objects.repo')
    __import__('gosbs.objects.restriction')
    __import__('gosbs.objects.task')
    __import__('gosbs.objects.service')
    __import__('gosbs.objects.service_repo')
    __import__('gosbs.objects.use')
    __import__('gosbs.objects.user')
