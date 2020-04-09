# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.
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

# Origin https://github.com/openstack/nova/blob/master/nova/db/sqlalchemy/models.py
# Only small part is left from the origin

"""
SQLAlchemy models for gosbs data.
"""

import uuid

from oslo_config import cfg
from oslo_db.sqlalchemy import models
from oslo_utils import timeutils
from sqlalchemy import (Column, Index, Integer, BigInteger, Enum, String,
                        schema, Unicode)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float, Time

from gosbs.db.sqlalchemy import types

CONF = cfg.CONF
BASE = declarative_base()


def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')


class NovaBase(models.ModelBase):
    metadata = None

    def __copy__(self):
        """Implement a safe copy.copy().

        SQLAlchemy-mapped objects travel with an object
        called an InstanceState, which is pegged to that object
        specifically and tracks everything about that object.  It's
        critical within all attribute operations, including gets
        and deferred loading.   This object definitely cannot be
        shared among two instances, and must be handled.

        The copy routine here makes use of session.merge() which
        already essentially implements a "copy" style of operation,
        which produces a new instance with a new InstanceState and copies
        all the data along mapped attributes without using any SQL.

        The mode we are using here has the caveat that the given object
        must be "clean", e.g. that it has no database-loaded state
        that has been updated and not flushed.   This is a good thing,
        as creating a copy of an object including non-flushed, pending
        database state is probably not a good idea; neither represents
        what the actual row looks like, and only one should be flushed.

        """
        session = orm.Session()

        copy = session.merge(self, load=False)
        session.expunge(copy)
        return copy


class Service(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents a running service on a host."""

    __tablename__ = 'services'
    __table_args__ = (
        schema.UniqueConstraint("host", "topic", "deleted",
                                name="uniq_services0host0topic0deleted"),
        schema.UniqueConstraint("host", "binary", "deleted",
                                name="uniq_services0host0binary0deleted"),
        Index('services_uuid_idx', 'uuid', unique=True),
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=True)
    host = Column(String(255))
    binary = Column(String(255))
    topic = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)
    disabled_reason = Column(String(255))
    last_seen_up = Column(DateTime, nullable=True)
    forced_down = Column(Boolean(), default=False)
    version = Column(Integer, default=0)


class Tasks(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents an image in the datastore."""
    __tablename__ = 'tasks'
    __table_args__ = (
    )
    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))
    service_uuid = Column(String(36), nullable=True)
    repet = Column(Boolean(), default=False)
    run = Column(DateTime)
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting'),
                            nullable=True)
    last = Column(DateTime, default=timeutils.now)
    priority = Column(Integer, default=5)

class Projects(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents an image in the datastore."""
    __tablename__ = 'projects'
    __table_args__ = (
    )
    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))
    active = Column(Boolean(), default=False)
    auto = Column(Boolean(), default=False)

class ProjectsMetadata(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'projects_metadata'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    project_uuid = Column(String(36), ForeignKey('projects.uuid'),
                default=lambda: str(uuid.uuid4()))
    project_repo_uuid = Column(String(36), ForeignKey('repos.uuid'),
                default=lambda: str(uuid.uuid4()))
    project_profile = Column(String(255))
    project_profile_repo_uuid = Column(String(36), ForeignKey('repos.uuid'),
                default=lambda: str(uuid.uuid4()))
    titel = Column(String(255))
    description = Column(Text)

class ProjectsRepos(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'projects_repos'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    project_uuid = Column(String(36), ForeignKey('projects.uuid'),
                default=lambda: str(uuid.uuid4()))
    repo_uuid = Column(String(36), ForeignKey('repos.uuid'),
                default=lambda: str(uuid.uuid4()))
    build = Column(Boolean(), default=False)
    test = Column(Boolean(), default=False)
    repoman = Column(Boolean(), default=False)
    qa = Column(Boolean(), default=False)
    auto = Column(Boolean(), default=False)
    depclean = Column(Boolean(), default=False)

class ProjectsBuilds(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents an image in the datastore."""
    __tablename__ = 'projects_builds'
    __table_args__ = (
    )
    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    project_uuid = Column(String(36), ForeignKey('projects.uuid'),
                default=lambda: str(uuid.uuid4()))
    ebuild_uuid = Column(String(36), ForeignKey('ebuilds.uuid'),
                default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'),)
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting'),
                            nullable=True)
    priority = Column(Integer, default=5)


class BuildsIUses(BASE, NovaBase):
    __tablename__ = 'builds_uses'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    build_uuid = Column(String(36), ForeignKey('projects_builds.uuid'),
                default=lambda: str(uuid.uuid4()))
    use_id = Column(Integer, ForeignKey('users.user_id'),)
    status = Column(Boolean, default=False)


class Users(BASE, NovaBase):
    __tablename__ = 'users'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String(255))


class Repos(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents an image in the datastore."""
    __tablename__ = 'repos'
    __table_args__ = (
    )

    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting'),
                            nullable=True)
    description = Column(Text)
    src_url = Column(String(255))
    auto = Column(Boolean(), default=False)
    repo_type = Column(Enum('project', 'ebuild'), nullable=True)


class Categories(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents an image in the datastore."""
    __tablename__ = 'categories'
    __table_args__ = (
    )

    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting'),
                            nullable=True)

class CategoriesMetadata(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'categories_metadata'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    category_uuid = Column(String(36), ForeignKey('categories.uuid'),
                default=lambda: str(uuid.uuid4()))
    checksum = Column(String(255))
    description = Column(Text)

class Packages(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents an image in the datastore."""
    __tablename__ = 'packages'
    __table_args__ = (
    )

    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting'),
                            nullable=True)
    category_uuid = Column(String(36), ForeignKey('categories.uuid'), nullable=False,
                   default=lambda: str(uuid.uuid4()))
    repo_uuid = Column(String(36), ForeignKey('repos.uuid'), nullable=False,
                   default=lambda: str(uuid.uuid4()))

class PackagesMetadata(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'packages_metadata'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    package_uuid = Column(String(36), ForeignKey('packages.uuid'),
                default=lambda: str(uuid.uuid4()))
    description = Column(Text)
    gitlog = Column(Text)
    checksum = Column(String(200))

class PackagesEmails(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'packages_emails'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    package_uuid = Column(String(36), ForeignKey('packages.uuid'),
                default=lambda: str(uuid.uuid4()))
    email_id = Column(Integer, ForeignKey('emails.id'))

class Emails(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'emails'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    email = Column(String(255))

class Uses(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'uses'
    __table_args__ = (
    )

    id = Column(Integer, primary_key=True)
    flag = Column(String(255))
    description = Column(Text)

class Restrictions(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'restrictions'
    __table_args__ = (
    )

    id = Column(Integer, primary_key=True)
    restriction = Column(String(255))
    
class Keywords(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'keywords'
    __table_args__ = (
    )

    id = Column(Integer, primary_key=True)
    keyword = Column(String(255))

class Ebuilds(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    __tablename__ = 'ebuilds'
    __table_args__ = (
    )
    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    package_uuid = Column(String(36), ForeignKey('packages.uuid'),
                default=lambda: str(uuid.uuid4()))
    version = Column(String(100))
    checksum = Column(String(200))

class EbuildsMetadata(BASE, NovaBase):
    __tablename__ = 'ebuilds_metadata'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    ebuild_uuid = Column(String(36), ForeignKey('ebuilds.uuid'),
                default=lambda: str(uuid.uuid4()))
    commit = Column(String(100))
    commit_msg = Column(Text)
    description = Column(Text)
    slot = Column(String(10))
    homepage = Column(String(200))
    license = Column(String(200))

class EbuildsRestrictions(BASE, NovaBase):
    __tablename__ = 'ebuilds_restrictions'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    ebuild_uuid = Column(String(36), ForeignKey('ebuilds.uuid'),
                default=lambda: str(uuid.uuid4()))
    restriction_id = Column(Integer, ForeignKey('restrictions.id'),)

class EbuildsIUses(BASE, NovaBase):
    __tablename__ = 'ebuilds_uses'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    ebuild_uuid = Column(String(36), ForeignKey('ebuilds.uuid'),
                default=lambda: str(uuid.uuid4()))
    use_id = Column(Integer, ForeignKey('uses.id'),)
    status = Column(Boolean, default=False)

class EbuildsKeywords(BASE, NovaBase):
    __tablename__ = 'ebuilds_keywords'
    __table_args__ = (
    )
    id = Column(Integer, primary_key=True)
    ebuild_uuid = Column(String(36), ForeignKey('ebuilds.uuid'),
                default=lambda: str(uuid.uuid4()))
    keyword_id = Column(Integer, ForeignKey('keywords.id'),)
    status = Column(Enum('stable','unstable','negative'))


class Images(BASE, NovaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'images'
    __table_args__ = (
    )

    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))
    size = Column(BigInteger().with_variant(Integer, "sqlite"))
    status = Column(Integer, nullable=False)
    min_disk = Column(Integer, nullable=False, default=0)
    min_ram = Column(Integer, nullable=False, default=0)

class Flavors(BASE, NovaBase):
    """Represents possible flavors for instances"""
    __tablename__ = 'flavors'
    __table_args__ = (
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    ram = Column(Integer, nullable=False)
    vcpus = Column(Integer, nullable=False)
    disk = Column(Integer)
    swap = Column(Integer, nullable=False, default=0)
    description = Column(Text)

class Instances(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents a guest VM."""
    __tablename__ = 'instances'
    __table_args__ = (
    )

    uuid = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    image_uuid = Column(String(36), ForeignKey('images.uuid'),
                default=lambda: str(uuid.uuid4()))
    flavor_uuid = Column(String(36), ForeignKey('flavors.uuid'),
                default=lambda: str(uuid.uuid4()))
    project_uuid = Column(String(36), ForeignKey('projects.uuid'),
                default=lambda: str(uuid.uuid4()))
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting'),
                            nullable=True)

class ServicesRepos(BASE, NovaBase, models.TimestampMixin, models.SoftDeleteMixin):
    """Represents a guest VM."""
    __tablename__ = 'services_repos'
    __table_args__ = (
    )

    id = Column(Integer, primary_key=True)
    service_uuid = Column(String(36), ForeignKey('services.uuid'),
                default=lambda: str(uuid.uuid4()))
    repo_uuid = Column(String(36), ForeignKey('repos.uuid'),
                default=lambda: str(uuid.uuid4()))
    auto = Column(Boolean(), default=False)
    status = Column(Enum('failed', 'completed', 'in-progress', 'waiting', 'update_db', 'rebuild_db'),
                            nullable=True)
