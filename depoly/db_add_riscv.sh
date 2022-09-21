#!/bin/bash

set -x
set -e

GENTOOCI_DB="${GENTOOCI_DB:-gentoo-ci}"
BUILDBOT_USER="${BUILDBOT_USER:-buildbot}"
ARCH="${ARCH:-riscv}"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

_uuidgen() {
    local uuid
    local re='^[0-9]+'
    while : ; do
        uuid="$(uuidgen)"
        if ! [[ $uuid =~ $re ]]; then
            echo "$uuid"
            break
        fi
    done

}

function insert_repositorys () {
    local name="${1}"
    local git="${2}"
    local uuid="${3}"
    local description="${4}"

    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM repositorys WHERE url = '$git';
        INSERT INTO repositorys(
            name, description, url,
            auto, enabled, ebuild, type,
            uuid, branch, mode, method,
            alwaysuselatest, merge, sshprivatekey, sshhostkey
        )
        VALUES (
            '$name', '$description', '$git',
            true, true, true, 'git',
            '$uuid', NULL, 'incremental', 'fresh',
            NULL, NULL, NULL, NULL);
EOSQL
}

function insert_workers () {
    local uuid=${1}
    local enable=${2:-true}
    local type=${3:-default}
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM workers WHERE uuid = '$uuid';
        INSERT INTO workers(
            uuid, enable, type
        )
        VALUES (
            '$uuid', $enable, $type
        );
EOSQL
}

function insert_projects() {
    local uuid="${1}"
    local name="${2}"
    local description="${3}"
    local profile="${4}"
    local repository_uuid="${5}"
    local status=${6}
    local use_default=${7}
    local image=${8}
    local git_project_name=${9}
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects WHERE uuid = '$uuid';
        INSERT INTO projects(
            uuid, name, description,
            profile, profile_repository_uuid, keyword_id,
            status, auto, enabled, created_by,
            use_default, image, git_project_name
        )
        VALUES (
            '$uuid', '$name', '$description',
            '$profile', '$repository_uuid', (SELECT id FROm keywords where name = 'riscv'),
            '$status', true, true, 1,
            '$use_default', '$image', '$git_project_name');
EOSQL
}

function insert_projects_workers() {
    local project_uuid="${1}"
    local worker_uuid="${2}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_workers WHERE project_uuid = '$project_uuid' and worker_uuid = '$worker_uuid';
        INSERT INTO projects_workers(project_uuid, worker_uuid) VALUES ('$project_uuid', '$worker_uuid');
EOSQL
}

function insert_projects_repositorys() {
    local project_uuid="${1}"
    local repository_uuid="${2}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_repositorys WHERE repository_uuid = '$repository_uuid';
        INSERT INTO projects_repositorys(
            project_uuid, repository_uuid,
            auto, pkgcheck, build, test, test_mr
        )
        VALUES (
            '$project_uuid', '$repository_uuid',
            true, 'package', true, false, false
        );
EOSQL
}

function insert_projects_emerge_options() {
    local project_uuid="${1}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_emerge_options WHERE project_uuid = '$project_uuid';
        INSERT INTO projects_emerge_options(
            project_uuid, oneshot, depclean, preserved_libs
        )
        VALUES (
            '$project_uuid', true, true, true
        );
EOSQL
}

function insert_projects_portage() {
    local project_uuid="${1}"
    local directorys="${2}"
    local value="${3}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_portage WHERE project_uuid = '$project_uuid' and directorys = '$directorys';
        INSERT INTO projects_portage(
            project_uuid, directorys, value
        )
        VALUES (
            '$project_uuid', '$directorys', '$value'
        );
EOSQL
}

function insert_projects_portages_env() {
    local project_uuid="${1}"
    local variable="${2}"
    local name="${3}"
    local value="${4}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_portages_env
            WHERE project_uuid = '$project_uuid' and makeconf_id = (SELECT id FROM portages_makeconf where variable = '$variable') and name = '$name';
        INSERT INTO projects_portages_env(
            project_uuid, makeconf_id, name, value
        )
        VALUES (
            '$project_uuid',
            (SELECT id FROM portages_makeconf where variable = '$variable'), '$name', '$value'
        );
EOSQL
}

function insert_projects_portages_package() {
    local project_uuid="${1}"
    local directory="${2}"
    local package="${3}"
    local value="${4:-}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_portages_package WHERE project_uuid = '$project_uuid' and directory = '$directory' and package = '$package';
        INSERT INTO projects_portages_package(
            project_uuid, directory, package, value
        )
        VALUES (
            '$project_uuid', '$directory', '$package', '$value'
        );
EOSQL
}

function insert_projects_portages_makeconf_one() {
    local project_uuid="${1}"
    local variable="${2}"
    local value="${3}"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_portages_makeconf
            WHERE project_uuid = '$project_uuid' and makeconf_id = (SELECT id FROM portages_makeconf where variable = '$variable');
EOSQL
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        INSERT INTO projects_portages_makeconf(
            project_uuid, makeconf_id, value
        )
        VALUES (
            '$project_uuid', (SELECT id FROM portages_makeconf where variable = '$variable'), '$value'
        );
EOSQL
}

function insert_projects_portages_makeconf() {
    local project_uuid="${1}"
    local variable="${2}"
    local values=("${3}")
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        DELETE FROM projects_portages_makeconf
            WHERE project_uuid = '$project_uuid' and makeconf_id = (SELECT id FROM portages_makeconf where variable = '$variable');
EOSQL
    for value in ${values[@]}; do
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" > /dev/null <<-EOSQL
        INSERT INTO projects_portages_makeconf(
            project_uuid, makeconf_id, value
        )
        VALUES (
            '$project_uuid', (SELECT id FROM portages_makeconf where variable = '$variable'), '$value'
        );
EOSQL
    done
}

function insert_projects_pattern() {
    local uuid=${1}

    local tmp_file=$(mktemp)
    chmod +wr $tmp_file

    cp sql/search_pattern.sql $tmp_file
    sed -i "s|e89c2c1a-46e0-4ded-81dd-c51afeb7fcff|$uuid|" $tmp_file
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" -c "truncate projects_pattern"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U"${BUILDBOT_USER}" -d"${GENTOOCI_DB}" -f "$tmp_file" > /dev/null

    rm $tmp_file
}

function select_repo_gentoo_uuid() {
    repo_gentoo_uuid=$(sudo -u postgres psql -Aqt -Ubuildbot -d gentoo-ci -c "SELECT uuid FROM repositorys;")
    if [ -z "$repo_gentoo_uuid" ]; then
        repo_gentoo_uuid=$(_uuidgen)
        insert_repositorys gentoo "https://github.com/gentoo/gentoo.git" "$repo_gentoo_uuid" "Gentoo main tree"
    fi
}

function select_project_base_uuid() {
    project_base_uuid=$(sudo -u postgres psql -Aqt -Ubuildbot -d gentoo-ci -c "SELECT uuid FROM projects where name = 'gentoo-riscv-base'")
    if [ -z "$project_base_uuid" ]; then
        project_base_uuid=$(_uuidgen)
        insert_projects "$project_base_uuid" "gentoo-riscv-base" "Gentoo CI base project" "$project_base_profile" "$repo_gentoo_uuid" "all" "false" "NULL" "NULL"
    fi

    project_systemd_uuid=$(sudo -u postgres psql -Aqt -Ubuildbot -d gentoo-ci -c "SELECT uuid FROM projects where name = 'gentoo-riscv-systemd'")
    if [ -z "$project_systemd_uuid" ]; then
        project_systemd_uuid=$(_uuidgen)
        insert_projects "$project_systemd_uuid" "gentoo-riscv-systemd" "Gentoo CI systemd project" "$project_systemd_profile" "$repo_gentoo_uuid" "unstable" "true" "stage3-rv64_lp64d-systemd" "NULL"
    fi
}

select_repo_gentoo_uuid
select_project_base_uuid

project_base_profile="default/linux/riscv/20.0/rv64gc/lp64d"
project_systemd_profile="default/linux/riscv/20.0/rv64gc/lp64d/systemd"

builder_workers=(
    "riscv-systemd-qemu-user-node-0"
    "riscv-systemd-qemu-user-node-1"
)

insert_projects_emerge_options       "$project_base_uuid"
insert_projects_portage              "$project_base_uuid"    "make.profile"  "$project_base_profile"
insert_projects_portage              "$project_base_uuid"    "repos.conf"    "gentoo"
insert_projects_portages_package     "$project_base_uuid"    "exclude"       "sys-kernel/gentoo-kernel-bin" ""
insert_workers                       "riscv-systemd-updatedb"
insert_projects_workers              "$project_base_uuid"    "riscv-systemd-updatedb"

insert_projects_portages_makeconf    "$project_base_uuid"    "EMERGE_DEFAULT_OPTS" "--buildpkg=y --rebuild-if-new-rev=y --rebuilt-binaries=y --usepkg=y --binpkg-respect-use=y --binpkg-changed-deps=y --nospinner --color=n --ask=n --quiet-build=y --quiet-fail=y"
insert_projects_portages_makeconf    "$project_base_uuid"    "FEATURES" "cgroup -news -collision-protect split-log compress-build-logs -ipc-sandbox -network-sandbox -cgroup -pid-sandbox xattr sandbox -cgroup -ipc-sandbox -network-sandbox -pid-sandbox"
insert_projects_portages_makeconf    "$project_base_uuid"    "RUBY_TARGETS" "ruby26 ruby27 ruby30 ruby31"
insert_projects_portages_makeconf    "$project_base_uuid"    "PYTHON_TARGETS" "python3_9 python3_10"
insert_projects_portages_makeconf    "$project_base_uuid"    "USE" "X caps xattr seccomp -elogind systemd"
insert_projects_portages_makeconf_one "$project_base_uuid"   "ACCEPT_LICENSE" "*"

insert_projects_pattern              $project_base_uuid

insert_projects_repositorys          "$project_systemd_uuid" "$repo_gentoo_uuid"
insert_projects_emerge_options       "$project_systemd_uuid"
insert_projects_portage              "$project_systemd_uuid" "make.profile"  "$project_systemd_profile"
insert_projects_portage              "$project_systemd_uuid" "repos.conf"    "gentoo"
insert_projects_portages_env         "$project_systemd_uuid" "FEATURES"      "test" "test test-fail-continue"
insert_projects_portages_env         "$project_systemd_uuid" "FEATURES"      "notest" "-test"
for bw in ${builder_workers[@]}; do
    insert_workers                   "$bw"
    insert_projects_workers          "$project_systemd_uuid" "$bw"
done

