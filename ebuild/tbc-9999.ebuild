# Copyright 1999-2016 Gentoo Foundation
# Distributed under theterms of the GNU General Public License v2
# $Id$

EAPI="5"
PYTHON_COMPAT=( python{2_7,3_4})

inherit distutils-r1 git-2

DESCRIPTION="TBC"
HOMEPAGE="https://wiki.gentoo.org/wiki/Project:Tinderbox-cluster"
SRC_URI=""
LICENSE="GPL-2"
KEYWORDS="~amd64"
SLOT="0"
IUSE="+mysql"

RDEPEND=">=sys-apps/portage-2.2.27[${PYTHON_USEDEP}]
        dev-python/sqlalchemy[${PYTHON_USEDEP}]
        dev-python/git-python[${PYTHON_USEDEP}]
        mysql? ( dev-python/mysql-connector-python[${PYTHON_USEDEP}] )"

DEPEND="${RDEPEND}
        dev-python/setuptools[${PYTHON_USEDEP}]"

EGIT_REPO_URI="https://anongit.gentoo.org/git/proj/tinderbox-cluster.git"
PATCHES=(
        "${S}"/patches/portage.patch
)

python_prepare_all() {
        python_setup
        einfo "Copying needed files from portage"
        cp $(python_get_sitedir)/_emerge/actions.py ${S}/pym/tbc
        cp $(python_get_sitedir)/_emerge/main.py ${S}/pym/tbc
        cp $(python_get_sitedir)/_emerge/Scheduler.py ${S}/pym/tbc
        cp $(python_get_sitedir)/repoman/main.py ${S}/pym/tbc/repoman.py
        einfo "Done."
        distutils-r1_python_prepare_all
}

src_install() {
        dodir etc/tbc
        insinto /etc/tbc
        doins ${S}/conf/tbc.conf
        dosbin ${S}/bin/tbc_host_jobs
        dosbin  ${S}/bin/tbc_guest_jobs

        distutils-r1_src_install
}
