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
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF

LOG = logging.getLogger(__name__)

def create_email(context, email):
    email_db = objects.email.Email()
    email_db.email = email
    email_db.create(context)
    return email_db

def check_email_db(context, email):
    email_db = objects.email.Email.get_by_name(context, email)
    if email_db is None:
        email_db = create_email(context, email)
    else:
        if email_db.deleted is True:
            email_db.deleted = False
            email_db.save(context)
    return email_db.id
