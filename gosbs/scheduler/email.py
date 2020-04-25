# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

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
    return email_db.id
