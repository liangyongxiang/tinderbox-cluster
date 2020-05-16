# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from datetime import datetime
import os
import pytz

import portage
from portage.cache.mappings import slot_dict_class

from oslo_log import log as logging
from gosbs import objects
import gosbs.conf

CONF = gosbs.conf.CONF
LOG = logging.getLogger(__name__)

def destroy_local_binary(context, build_job, project_db, service_uuid, mysettings):
    filters = {
        'ebuild_uuid' : build_job['ebuild'].uuid,
        'project_uuid' : project_db.uuid,
        'service_uuid' : service_uuid,
        }
    for local_binary_db in objects.binary.BinaryList.get_all(context, filters=filters):
        local_binary_db.destroy(context)
        binfile = mysettings['PKGDIR'] + "/" + build_job['cpv'] + ".tbz2"
        try:
            os.remove(binfile)
        except:
            LOG.error("Package file was not removed or not found: %s" % binfile)

def touch_pkg_in_db(context, pkg, objectsstor=False):
    if objectsstor:
        service_ref = objects.Service.get_by_topic(context, 'scheduler')
    else:
        service_ref = objects.Service.get_by_host_and_topic(context, CONF.host, 'builder')
    filters = { 'build_id' : pkg.cpv.build_id,
            'service_uuid' : service_ref.uuid,
            }
    local_binary_db = objects.Binary.get_by_cpv(context, pkg.cpv, filters=filters)
    if local_binary_db is None:
        return
    local_binary_db.updated_at = datetime.now().replace(tzinfo=pytz.UTC)
    local_binary_db.save(context)
    LOG.info('Touching %s in the binary database', pkg.cpv)

class PackageIndex(object):

    def __init__(self,
        allowed_pkg_keys=None,
        default_header_data=None,
        default_pkg_data=None,
        inherited_keys=None,
        translated_keys=None,
        objectsstor=False,
        context=None,
        ):

        self._pkg_slot_dict = None
        if allowed_pkg_keys is not None:
            self._pkg_slot_dict = slot_dict_class(allowed_pkg_keys)

        self._default_header_data = default_header_data
        self._default_pkg_data = default_pkg_data
        self._inherited_keys = inherited_keys
        self._write_translation_map = {}
        self._read_translation_map = {}
        if translated_keys:
            self._write_translation_map.update(translated_keys)
            self._read_translation_map.update(((y, x) for (x, y) in translated_keys))
        self.header = {}
        if self._default_header_data:
            self.header.update(self._default_header_data)
        self.packages = []
        self.modified = True
        self.context = context
        self.project_ref = objects.Project.get_by_name(self.context, CONF.builder.project)
        if objectsstor:
            self.service_ref = objects.Service.get_by_topic(self.context, 'scheduler')
        else:
            self.service_ref = objects.Service.get_by_host_and_topic(self.context, CONF.host, 'builder')

    def _read_header_from_db(self):
        binary_header_db = objects.BinaryHeader.get_by_service_uuid(self.context, self.service_ref.uuid)
        if binary_header_db is None:
            return self.header
        header = {}
        header['repository'] = binary_header_db.repository
        header['ARCH'] = binary_header_db.arch
        header['ACCEPT_KEYWORDS'] = binary_header_db.accept_keywords
        header['ACCEPT_LICENSE'] = binary_header_db.accept_license
        header['ACCEPT_PROPERTIES'] = binary_header_db.accept_properties
        header['ACCEPT_RESTRICT'] = binary_header_db.accept_restrict
        header['CBUILD'] = binary_header_db.cbuild
        header['CONFIG_PROTECT'] = binary_header_db.config_protect
        header['CONFIG_PROTECT_MASK'] = binary_header_db.config_protect_mask
        header['FEATURES'] = binary_header_db.features
        header['GENTOO_MIRRORS'] = binary_header_db.gentoo_mirrors
        #binary_header_db.install_mask = header[]
        header['IUSE_IMPLICIT'] = binary_header_db.iuse_implicit
        header['USE'] = binary_header_db.use
        header['USE_EXPAND'] = binary_header_db.use_expand
        header['USE_EXPAND_HIDDEN'] = binary_header_db.use_expand_hidden
        header['USE_EXPAND_IMPLICIT'] = binary_header_db.use_expand_implicit
        header['USE_EXPAND_UNPREFIXED'] = binary_header_db.use_expand_unprefixed
        header['USE_EXPAND_VALUES_ARCH'] = binary_header_db.use_expand_values_arch
        header['USE_EXPAND_VALUES_ELIBC'] = binary_header_db.use_expand_values_elibc
        header['USE_EXPAND_VALUES_KERNEL'] = binary_header_db.use_expand_values_kernel
        header['USE_EXPAND_VALUES_USERLAND'] = binary_header_db.use_expand_values_userland
        header['ELIBC'] = binary_header_db.elibc
        header['KERNEL'] = binary_header_db.kernel
        header['USERLAND'] = binary_header_db.userland
        header['PACKAGES'] = binary_header_db.packages
        header['PROFILE'] = binary_header_db.profile
        header['VERSION'] = binary_header_db.version
        header['TIMESTAMP'] = binary_header_db.updated_at
        return header

    def _read_pkg_from_db(self, binary_db):
        pkg = {}
        pkg['repository'] = binary_db.repository
        pkg['CPV'] = binary_db.cpv
        pkg['RESTRICT'] = binary_db.restrictions
        pkg['DEPEND'] = binary_db.depend
        pkg['BDEPEND'] = binary_db.bdepend
        pkg['RDEPEND'] = binary_db.rdepend
        pkg['PDEPEND'] = binary_db.pdepend
        pkg['_mtime_'] = binary_db.mtime
        pkg['LICENSE'] = binary_db.license
        pkg['CHOST'] = binary_db.chost
        pkg['SHA1'] = binary_db.sha1
        pkg['DEFINED_PHASES'] = binary_db.defined_phases
        pkg['SIZE'] = binary_db.size
        pkg['EAPI'] = binary_db.eapi
        pkg['PATH'] = binary_db.path
        pkg['BUILD_ID'] = binary_db.build_id
        pkg['SLOT'] = binary_db.slot
        pkg['MD5'] = binary_db.md5
        pkg['BUILD_TIME'] = binary_db.build_time
        pkg['IUSE'] = binary_db.iuses
        pkg['PROVIDES'] = binary_db.provides
        pkg['KEYWORDS'] = binary_db.keywords
        pkg['REQUIRES'] = binary_db.requires
        pkg['USE'] = binary_db.uses
        return pkg

    def read(self):
        self.readHeader()
        self.readBody()

    def readHeader(self):
        self.header.update(self._read_header_from_db())

    def readBody(self):
        filters = {
            'service_uuid' : self.service_ref.uuid,
            }
        for binary_db in objects.BinaryList.get_all(self.context, filters=filters):
            self.packages.append(self._read_pkg_from_db(binary_db))

    def _write_header_to_db(self):
        binary_header_db = objects.BinaryHeader()
        binary_header_db.project_uuid = self.project_ref.uuid
        binary_header_db.service_uuid = self.service_ref.uuid
        binary_header_db.repository = self.header['repository']
        binary_header_db.arch = self.header['ARCH']
        binary_header_db.accept_keywords = self.header['ACCEPT_KEYWORDS']
        binary_header_db.accept_license = self.header['ACCEPT_LICENSE']
        binary_header_db.accept_properties = self.header['ACCEPT_PROPERTIES']
        binary_header_db.accept_restrict = self.header['ACCEPT_RESTRICT']
        binary_header_db.cbuild = self.header['CBUILD']
        binary_header_db.config_protect = self.header['CONFIG_PROTECT']
        binary_header_db.config_protect_mask = self.header['CONFIG_PROTECT_MASK']
        binary_header_db.features = self.header['FEATURES']
        binary_header_db.gentoo_mirrors = self.header['GENTOO_MIRRORS']
        #binary_header_db.install_mask = header[]
        binary_header_db.iuse_implicit = self.header['IUSE_IMPLICIT']
        binary_header_db.use = self.header['USE']
        binary_header_db.use_expand = self.header['USE_EXPAND']
        binary_header_db.use_expand_hidden = self.header['USE_EXPAND_HIDDEN']
        binary_header_db.use_expand_implicit = self.header['USE_EXPAND_IMPLICIT']
        binary_header_db.use_expand_unprefixed = self.header['USE_EXPAND_UNPREFIXED']
        binary_header_db.use_expand_values_arch = self.header['USE_EXPAND_VALUES_ARCH']
        binary_header_db.use_expand_values_elibc = self.header['USE_EXPAND_VALUES_ELIBC']
        binary_header_db.use_expand_values_kernel = self.header['USE_EXPAND_VALUES_KERNEL']
        binary_header_db.use_expand_values_userland = self.header['USE_EXPAND_VALUES_USERLAND']
        binary_header_db.elibc = self.header['ELIBC']
        binary_header_db.kernel = self.header['KERNEL']
        binary_header_db.userland = self.header['USERLAND']
        binary_header_db.packages = self.header['PACKAGES']
        binary_header_db.profile = self.header['PROFILE']
        binary_header_db.version = self.header['VERSION']
        binary_header_db.updated_at = datetime.now().replace(tzinfo=pytz.UTC)
        binary_header_db.create(self.context)

    def _update_header_in_db(self, binary_header_db):
        binary_header_db.repository = self.header['repository']
        binary_header_db.arch = self.header['ARCH']
        binary_header_db.accept_keywords = self.header['ACCEPT_KEYWORDS']
        binary_header_db.accept_license = self.header['ACCEPT_LICENSE']
        binary_header_db.accept_properties = self.header['ACCEPT_PROPERTIES']
        binary_header_db.accept_restrict = self.header['ACCEPT_PROPERTIES']
        binary_header_db.cbuild = self.header['CBUILD']
        binary_header_db.config_protect = self.header['CONFIG_PROTECT']
        binary_header_db.config_protect_mask = self.header['CONFIG_PROTECT_MASK']
        binary_header_db.features = self.header['FEATURES']
        binary_header_db.gentoo_mirrors = self.header['GENTOO_MIRRORS']
        #binary_header_db.install_mask = header[]
        binary_header_db.iuse_implicit = self.header['IUSE_IMPLICIT']
        binary_header_db.use = self.header['USE']
        binary_header_db.use_expand = self.header['USE_EXPAND']
        binary_header_db.use_expand_hidden = self.header['USE_EXPAND_HIDDEN']
        binary_header_db.use_expand_implicit = self.header['USE_EXPAND_IMPLICIT']
        binary_header_db.use_expand_unprefixed = self.header['USE_EXPAND_UNPREFIXED']
        binary_header_db.use_expand_values_arch = self.header['USE_EXPAND_VALUES_ARCH']
        binary_header_db.use_expand_values_elibc = self.header['USE_EXPAND_VALUES_ELIBC']
        binary_header_db.use_expand_values_kernel = self.header['USE_EXPAND_VALUES_KERNEL']
        binary_header_db.use_expand_values_userland = self.header['USE_EXPAND_VALUES_USERLAND']
        binary_header_db.elibc = self.header['ELIBC']
        binary_header_db.kernel = self.header['KERNEL']
        binary_header_db.userland = self.header['USERLAND']
        binary_header_db.packages = self.header['PACKAGES']
        binary_header_db.profile = self.header['PROFILE']
        binary_header_db.version = self.header['VERSION']
        binary_header_db.save(self.context)

    def _update_header_packages(self):
        header = self.header
        header['PACKAGES'] = len(self.packages)
        return header

    def _update_header(self):
        self.header.update(self._update_header_packages())
        binary_header_db = objects.BinaryHeader.get_by_service_uuid(self.context, self.service_ref.uuid)
        if binary_header_db is None:
            self._write_header_to_db()
            LOG.info('Adding header to the binary database')
            return
        self._update_header_in_db(binary_header_db)
        LOG.info('Update header in the binary database')

    def _write_pkg_to_db(self, pkg):
        ebuild_version_tree = portage.versions.cpv_getversion(pkg['CPV'])
        cp = portage.versions.cpv_getkey(pkg['CPV']).split('/')
        category_db = objects.category.Category.get_by_name(self.context, cp[0])
        repo_db = objects.repo.Repo.get_by_name(self.context, pkg['repository'])
        filters = { 'repo_uuid' : repo_db.uuid,
            'category_uuid' : category_db.uuid,
            }
        package_db = objects.package.Package.get_by_name(self.context, cp[1], filters=filters)
        filters = { 'package_uuid' : package_db.uuid,
            }
        ebuild_db = objects.ebuild.Ebuild.get_by_name(self.context, ebuild_version_tree, filters=filters)
        local_binary_db = objects.binary.Binary()
        local_binary_db.ebuild_uuid = ebuild_db.uuid
        local_binary_db.repository = pkg['repository']
        local_binary_db.project_uuid = self.project_ref.uuid
        local_binary_db.service_uuid = self.service_ref.uuid
        local_binary_db.cpv = pkg['CPV']
        local_binary_db.restrictions = pkg['RESTRICT']
        local_binary_db.depend = pkg['DEPEND']
        local_binary_db.bdepend = pkg['BDEPEND']
        local_binary_db.rdepend = pkg['RDEPEND']
        local_binary_db.pdepend = pkg['PDEPEND']
        local_binary_db.mtime = pkg['_mtime_']
        local_binary_db.license = pkg['LICENSE']
        local_binary_db.chost = pkg['CHOST']
        local_binary_db.sha1 = pkg['SHA1']
        local_binary_db.defined_phases = pkg['DEFINED_PHASES']
        local_binary_db.size = pkg['SIZE']
        local_binary_db.eapi = pkg['EAPI']
        local_binary_db.path = pkg['PATH']
        local_binary_db.build_id = pkg['BUILD_ID']
        local_binary_db.slot = pkg['SLOT']
        local_binary_db.md5 = pkg['MD5']
        local_binary_db.build_time = pkg['BUILD_TIME']
        local_binary_db.iuses = pkg['IUSE']
        local_binary_db.uses = pkg['USE']
        local_binary_db.provides = pkg['PROVIDES']
        local_binary_db.keywords = pkg['KEYWORDS']
        local_binary_db.requires = pkg['REQUIRES']
        local_binary_db.updated_at = datetime.now().replace(tzinfo=pytz.UTC)
        local_binary_db.create(self.context)

    def write(self, pkg):
        self._update_header()
        if pkg is not None:
            filters = { 'build_id' : pkg['BUILD_ID'],
                'service_uuid' : self.service_ref.uuid,
                }
            local_binary_db = objects.Binary.get_by_cpv(self.context, pkg['CPV'], filters=filters)
            if local_binary_db is None:
                self._write_pkg_to_db(pkg)
                LOG.info('Adding %s to the binary database', pkg['CPV'])
                return
            LOG.info('%s is already in the binary database', pkg['CPV'])
