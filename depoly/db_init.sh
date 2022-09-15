#!/bin/bash

set -x
set -e

SQL_URL="${SQL_URL:-http://90.231.13.235:8000}"

DB_IP_ADDRESS="${DB_IP_ADDRESS:-localhost}"
GENTOOCI_DB="${GENTOOCI_DB:-gentoo-ci}"
BUILDBOT_DB="${BUILDBOT_DB:-buildbot}"
BUILDBOT_USER="${BUILDBOT_USER:-buildbot}"
PASSWORD="${PASSWORD:-bu1ldbOt}"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

echo "GENTOOCI_DB:  $GENTOOCI_DB"
echo "BUILDBOT_DB:  $BUILDBOT_DB"
echo "BUILDBOT_USER $BUILDBOT_USER"

sudo -u postgres dropdb --if-exists ${GENTOOCI_DB}
sudo -u postgres dropdb --if-exists ${BUILDBOT_DB}
sudo -u postgres dropuser --if-exists ${BUILDBOT_USER}
sudo -u postgres psql -c "CREATE USER ${BUILDBOT_USER} WITH PASSWORD '${PASSWORD}';"
sudo -u postgres createdb --owner ${BUILDBOT_USER} ${BUILDBOT_DB}

# TODO: gentoo_ci_schema request GENTOOCI_DB name is gentoo-ci
sudo -u postgres psql -v ON_ERROR_STOP=1 -f "sql/gentoo_ci_schema.sql" > /dev/null

sudo -u postgres psql -v ON_ERROR_STOP=1 -U${BUILDBOT_USER} -d${GENTOOCI_DB} <<-EOSQL > /dev/null
    CREATE SEQUENCE public.projects_portages_package_id_seq
        AS bigint START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
    ALTER TABLE public.projects_portages_package_id_seq OWNER TO buildbot;
    ALTER SEQUENCE public.projects_portages_package_id_seq OWNED BY public.projects_portages_package.id;
    ALTER TABLE ONLY public.projects_portages_package ALTER COLUMN id SET DEFAULT nextval('public.projects_portages_package_id_seq'::regclass);

    CREATE SEQUENCE public.projects_workers_id_seq
        AS bigint START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
    ALTER TABLE public.projects_workers_id_seq OWNER TO buildbot;
    ALTER SEQUENCE public.projects_workers_id_seq OWNED BY public.projects_workers.id;
    ALTER TABLE ONLY public.projects_workers ALTER COLUMN id SET DEFAULT nextval('public.projects_workers_id_seq'::regclass);

EOSQL

sql_dbs=(
    keywords.sql
    categorys.sql
    portage_makeconf.sql
)
for db in ${sql_dbs[@]}; do
    if [ ! -f "sql/$db" ]; then
        echo "$db not exists"
        wget --output-document "sql/$db" "$SQL_URL/$db"
    fi
    sudo -u postgres psql -v ON_ERROR_STOP=1 -U${BUILDBOT_USER} -d${GENTOOCI_DB} -f "sql/$db" >/dev/null
done

