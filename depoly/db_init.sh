#!/bin/bash

set -x
set -e

SQL_URL="${SQL_URL:-http://90.231.13.235:8000}"
DB_IP_ADDRESS="${DB_IP_ADDRESS:-localhost}"
GENTOOCI_DB="${GENTOOCI_DB:-gentoo-ci}"
PASSWORD="${PASSWORD:-bu1ldbOt}"
TEST_ARCH="${TEST_ARCH:-riscv}"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

mkdir -p sql

# delete the database and run away, 删库跑路
# TODO: check db if exists
sudo -u postgres dropdb --if-exists ${GENTOOCI_DB} #>/dev/null
sudo -u postgres dropdb --if-exists buildbot #>/dev/null
sudo -u postgres dropuser --if-exists buildbot #>/dev/null

sudo -u postgres psql -c "CREATE USER buildbot WITH PASSWORD '\${PASSWORD}';"
sudo -u postgres createdb --owner buildbot buildbot
#sudo -u postgres createdb --owner buildbot ${GENTOOCI_DB} --template template0
sudo -u postgres psql -f "sql/gentoo_ci_schema.sql"
sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -f "sql/search_pattern.sql"

# FIXME: Configure data of gentoo-ci db instead of just importing them
# import gentoo-ci db
sql_dbs=(
    keywords.sql
    categorys.sql
    repositorys.sql
    project.sql
    portage_makeconf.sql
    projects_emerge_options.sql

    workers.sql

    projects_env.sql
    projects_makeconf.sql
    projects_package.sql
    projects_pattern.sql
    projects_portage.sql
    projects_repositorys.sql
    projects_workers.sql

    repositorys_gitpullers.sql
)
for db in ${sql_dbs[@]}; do
    if [ ! -f "sql/$db" ]; then
        echo "$db not exists"
        wget --output-document "sql/$db" "$SQL_URL/$db"
    fi
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -f "sql/$db" >/dev/null
done

if [ "${TEST_ARCH}" = 'riscv' ]; then
    # projects_portage
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE projects_portage SET value='default/linux/riscv/20.0/rv64gc/lp64d/systemd' WHERE id = 1"
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE projects_portage SET value='default/linux/riscv/20.0/rv64gc/lp64d/desktop' WHERE id = 3"
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE projects_portage SET value='default/linux/riscv/20.0/rv64gc/lp64d' WHERE id = 5"
    # projects
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE projects SET profile='profiles/default/linux/riscv', keyword_id='11' WHERE uuid = 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff'"
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE projects SET name='defriscv20_0unstable', description='Default riscv 20.0 Unstable', profile='profiles/default/linux/riscv/20.0/rv64gc/lp64d', keyword_id='11', image='stage3-rv64_lp64d-openrc-latest' WHERE uuid = 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa'"
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE projects SET profile='profiles/default/linux/riscv/20.0/rv64gc/lp64d/systemd', keyword_id='11', enabled='t', image='stage3-rv64_lp64d-systemd-latest' WHERE uuid = 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd'"
    # projects_portages_makeconf
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "UPDATE public.projects_portages_makeconf set value='riscv64-unknown-linux-gnu' WHERE id = 2;"
    sudo -u postgres psql -Ubuildbot -d${GENTOOCI_DB} -c "INSERT INTO public.projects_portages_makeconf VALUES (63, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--jobs');"
fi

# migrate version_control
migrate version_control postgresql://buildbot:${PASSWORD}@${DB_IP_ADDRESS}/${GENTOOCI_DB} buildbot_gentoo_ci/db/migrate 0

