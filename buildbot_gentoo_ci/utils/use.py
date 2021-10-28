# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

def getIUseValue(auxdb_iuse):
    status = False
    if auxdb_iuse[0] in ['+']:
        status = True
    if auxdb_iuse[0] in ['+'] or auxdb_iuse[0] in ['-']:
        iuse = auxdb_iuse[1:]
    else:
        iuse = auxdb_iuse
    return iuse, status
