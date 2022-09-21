--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3
-- Dumped by pg_dump version 13.5

-- Started on 2022-08-21 10:37:12 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2475 (class 1262 OID 155811)
-- Name: gentoo-ci; Type: DATABASE; Schema: -; Owner: buildbot
--

CREATE DATABASE "gentoo-ci" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'C.utf8';


ALTER DATABASE "gentoo-ci" OWNER TO buildbot;

\connect -reuse-previous=on "dbname='gentoo-ci'"

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 655 (class 1247 OID 155813)
-- Name: projects_builds_status; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_builds_status AS ENUM (
    'failed',
    'completed',
    'in-progress',
    'waiting',
    'warning'
);


ALTER TYPE public.projects_builds_status OWNER TO buildbot;

--
-- TOC entry 658 (class 1247 OID 155824)
-- Name: projects_pattern_search_type; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_pattern_search_type AS ENUM (
    'in',
    'startswith',
    'endswith',
    'search'
);


ALTER TYPE public.projects_pattern_search_type OWNER TO buildbot;

--
-- TOC entry 661 (class 1247 OID 155834)
-- Name: projects_pattern_status; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_pattern_status AS ENUM (
    'info',
    'warning',
    'error',
    'ignore'
);


ALTER TYPE public.projects_pattern_status OWNER TO buildbot;

--
-- TOC entry 664 (class 1247 OID 155844)
-- Name: projects_pattern_type; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_pattern_type AS ENUM (
    'info',
    'qa',
    'compile',
    'configure',
    'install',
    'postinst',
    'prepare',
    'setup',
    'test',
    'unpack',
    'ignore',
    'issues',
    'misc',
    'elog',
    'pretend'
);


ALTER TYPE public.projects_pattern_type OWNER TO buildbot;

--
-- TOC entry 667 (class 1247 OID 155868)
-- Name: projects_portage_directorys; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_portage_directorys AS ENUM (
    'make.profile',
    'repos.conf'
);


ALTER TYPE public.projects_portage_directorys OWNER TO buildbot;

--
-- TOC entry 761 (class 1247 OID 550221)
-- Name: projects_portage_package_directorys; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_portage_package_directorys AS ENUM (
    'use',
    'accept_keywords',
    'exclude',
    'env'
);


ALTER TYPE public.projects_portage_package_directorys OWNER TO buildbot;

--
-- TOC entry 670 (class 1247 OID 155874)
-- Name: projects_repositorys_pkgcheck; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_repositorys_pkgcheck AS ENUM (
    'package',
    'full',
    'none'
);


ALTER TYPE public.projects_repositorys_pkgcheck OWNER TO buildbot;

--
-- TOC entry 673 (class 1247 OID 155882)
-- Name: projects_status; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.projects_status AS ENUM (
    'stable',
    'all',
    'unstable'
);


ALTER TYPE public.projects_status OWNER TO buildbot;

--
-- TOC entry 777 (class 1247 OID 1708870)
-- Name: repositorys_method; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.repositorys_method AS ENUM (
    'clobber',
    'fresh',
    'clean',
    'copy'
);


ALTER TYPE public.repositorys_method OWNER TO postgres;

--
-- TOC entry 774 (class 1247 OID 1708856)
-- Name: repositorys_mode; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.repositorys_mode AS ENUM (
    'full',
    'incremental'
);


ALTER TYPE public.repositorys_mode OWNER TO postgres;

--
-- TOC entry 676 (class 1247 OID 155890)
-- Name: repositorys_type; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.repositorys_type AS ENUM (
    'git',
    'gitlab'
);


ALTER TYPE public.repositorys_type OWNER TO buildbot;

--
-- TOC entry 679 (class 1247 OID 155894)
-- Name: versions_keywords_status; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.versions_keywords_status AS ENUM (
    'stable',
    'unstable',
    'negative',
    'all'
);


ALTER TYPE public.versions_keywords_status OWNER TO buildbot;

--
-- TOC entry 767 (class 1247 OID 698031)
-- Name: versions_metadata_type; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.versions_metadata_type AS ENUM (
    'iuse',
    'properties',
    'required use',
    'restrict',
    'keyword'
);


ALTER TYPE public.versions_metadata_type OWNER TO buildbot;

--
-- TOC entry 758 (class 1247 OID 488393)
-- Name: workers_type; Type: TYPE; Schema: public; Owner: buildbot
--

CREATE TYPE public.workers_type AS ENUM (
    'default',
    'local',
    'latent',
    'chroot',
    'docker'
);


ALTER TYPE public.workers_type OWNER TO buildbot;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 200 (class 1259 OID 155903)
-- Name: categorys; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.categorys (
    uuid character varying(36) NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.categorys OWNER TO buildbot;

--
-- TOC entry 201 (class 1259 OID 155906)
-- Name: keywords; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.keywords (
    id integer NOT NULL,
    name character varying(50) NOT NULL
);


ALTER TABLE public.keywords OWNER TO buildbot;

--
-- TOC entry 202 (class 1259 OID 155909)
-- Name: migrate_version; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.migrate_version (
    repository_id character varying(250) NOT NULL,
    repository_path text,
    version integer
);


ALTER TABLE public.migrate_version OWNER TO buildbot;

--
-- TOC entry 203 (class 1259 OID 155915)
-- Name: packages; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.packages (
    name character varying(100) NOT NULL,
    category_uuid character varying(36),
    repository_uuid character varying(36),
    deleted boolean,
    deleted_at integer,
    uuid character varying(36) NOT NULL
);


ALTER TABLE public.packages OWNER TO buildbot;

--
-- TOC entry 204 (class 1259 OID 155918)
-- Name: portages_makeconf; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.portages_makeconf (
    id integer NOT NULL,
    variable character varying(50) NOT NULL
);


ALTER TABLE public.portages_makeconf OWNER TO buildbot;

--
-- TOC entry 205 (class 1259 OID 155921)
-- Name: portages_makeconf_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.portages_makeconf_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.portages_makeconf_id_seq OWNER TO buildbot;

--
-- TOC entry 2477 (class 0 OID 0)
-- Dependencies: 205
-- Name: portages_makeconf_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.portages_makeconf_id_seq OWNED BY public.portages_makeconf.id;


--
-- TOC entry 206 (class 1259 OID 155923)
-- Name: projects; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects (
    uuid character varying(36) NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    profile character varying(255) NOT NULL,
    profile_repository_uuid character varying(36) NOT NULL,
    keyword_id integer,
    status public.projects_status,
    auto boolean,
    enabled boolean,
    created_by integer NOT NULL,
    use_default boolean,
    image character varying(255),
    git_project_name character varying(255)
);


ALTER TABLE public.projects OWNER TO buildbot;

--
-- TOC entry 207 (class 1259 OID 155929)
-- Name: projects_builds; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_builds (
    id integer NOT NULL,
    project_uuid character varying(36),
    version_uuid character varying(36),
    build_id integer NOT NULL,
    buildbot_build_id integer DEFAULT 0,
    status public.projects_builds_status,
    requested boolean,
    created_at integer,
    updated_at integer,
    deleted_at integer,
    deleted boolean
);


ALTER TABLE public.projects_builds OWNER TO buildbot;

--
-- TOC entry 208 (class 1259 OID 155933)
-- Name: projects_builds_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_builds_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_builds_id_seq OWNER TO buildbot;

--
-- TOC entry 2478 (class 0 OID 0)
-- Dependencies: 208
-- Name: projects_builds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_builds_id_seq OWNED BY public.projects_builds.id;


--
-- TOC entry 209 (class 1259 OID 155935)
-- Name: projects_emerge_options; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_emerge_options (
    id integer NOT NULL,
    project_uuid character varying(36),
    oneshot boolean,
    depclean boolean,
    preserved_libs boolean
);


ALTER TABLE public.projects_emerge_options OWNER TO buildbot;

--
-- TOC entry 210 (class 1259 OID 155938)
-- Name: projects_emerge_options_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_emerge_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_emerge_options_id_seq OWNER TO buildbot;

--
-- TOC entry 2479 (class 0 OID 0)
-- Dependencies: 210
-- Name: projects_emerge_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_emerge_options_id_seq OWNED BY public.projects_emerge_options.id;


--
-- TOC entry 211 (class 1259 OID 155940)
-- Name: projects_pattern; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_pattern (
    id integer NOT NULL,
    project_uuid character varying(36),
    search character varying(100) NOT NULL,
    start integer,
    "end" integer,
    type public.projects_pattern_type,
    status public.projects_pattern_status,
    search_type public.projects_pattern_search_type
);


ALTER TABLE public.projects_pattern OWNER TO buildbot;

--
-- TOC entry 212 (class 1259 OID 155943)
-- Name: projects_pattern_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_pattern_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_pattern_id_seq OWNER TO buildbot;

--
-- TOC entry 2480 (class 0 OID 0)
-- Dependencies: 212
-- Name: projects_pattern_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_pattern_id_seq OWNED BY public.projects_pattern.id;


--
-- TOC entry 213 (class 1259 OID 155945)
-- Name: projects_portage; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_portage (
    id integer NOT NULL,
    project_uuid character varying(36),
    directorys public.projects_portage_directorys,
    value character varying(255) NOT NULL
);


ALTER TABLE public.projects_portage OWNER TO buildbot;

--
-- TOC entry 214 (class 1259 OID 155948)
-- Name: projects_portage_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_portage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_portage_id_seq OWNER TO buildbot;

--
-- TOC entry 2481 (class 0 OID 0)
-- Dependencies: 214
-- Name: projects_portage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_portage_id_seq OWNED BY public.projects_portage.id;


--
-- TOC entry 215 (class 1259 OID 155950)
-- Name: projects_portages_env; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_portages_env (
    id integer NOT NULL,
    project_uuid character varying(36),
    makeconf_id integer,
    name character varying(50) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.projects_portages_env OWNER TO buildbot;

--
-- TOC entry 216 (class 1259 OID 155953)
-- Name: projects_portages_env_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_portages_env_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_portages_env_id_seq OWNER TO buildbot;

--
-- TOC entry 2482 (class 0 OID 0)
-- Dependencies: 216
-- Name: projects_portages_env_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_portages_env_id_seq OWNED BY public.projects_portages_env.id;


--
-- TOC entry 217 (class 1259 OID 155955)
-- Name: projects_portages_makeconf; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_portages_makeconf (
    id integer NOT NULL,
    project_uuid character varying(36),
    makeconf_id integer,
    value character varying(255) NOT NULL
);


ALTER TABLE public.projects_portages_makeconf OWNER TO buildbot;

--
-- TOC entry 218 (class 1259 OID 155958)
-- Name: projects_portages_makeconf_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_portages_makeconf_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_portages_makeconf_id_seq OWNER TO buildbot;

--
-- TOC entry 2483 (class 0 OID 0)
-- Dependencies: 218
-- Name: projects_portages_makeconf_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_portages_makeconf_id_seq OWNED BY public.projects_portages_makeconf.id;


--
-- TOC entry 230 (class 1259 OID 550229)
-- Name: projects_portages_package; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_portages_package (
    id bigint NOT NULL,
    project_uuid character varying(36),
    directory public.projects_portage_package_directorys,
    package character varying(50),
    value character varying(10)
);


ALTER TABLE public.projects_portages_package OWNER TO buildbot;

--
-- TOC entry 219 (class 1259 OID 155960)
-- Name: projects_repositorys; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_repositorys (
    id integer NOT NULL,
    project_uuid character varying(36),
    repository_uuid character varying(36),
    auto boolean,
    pkgcheck public.projects_repositorys_pkgcheck,
    build boolean,
    test boolean,
    test_mr boolean
);


ALTER TABLE public.projects_repositorys OWNER TO buildbot;

--
-- TOC entry 220 (class 1259 OID 155963)
-- Name: projects_repositorys_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.projects_repositorys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_repositorys_id_seq OWNER TO buildbot;

--
-- TOC entry 2484 (class 0 OID 0)
-- Dependencies: 220
-- Name: projects_repositorys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.projects_repositorys_id_seq OWNED BY public.projects_repositorys.id;


--
-- TOC entry 229 (class 1259 OID 484107)
-- Name: projects_workers; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.projects_workers (
    id bigint NOT NULL,
    project_uuid character varying(36),
    worker_uuid character varying(36)
);


ALTER TABLE public.projects_workers OWNER TO buildbot;

--
-- TOC entry 221 (class 1259 OID 155965)
-- Name: repositorys; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.repositorys (
    name character varying(255) NOT NULL,
    description text,
    url character varying(255),
    auto boolean,
    enabled boolean,
    ebuild boolean,
    type public.repositorys_type,
    uuid character varying(36) NOT NULL,
    branch character varying(255),
    mode public.repositorys_mode,
    method public.repositorys_method,
    alwaysuselatest boolean,
    merge boolean,
    sshprivatekey character varying(50),
    sshhostkey character varying(50)
);


ALTER TABLE public.repositorys OWNER TO buildbot;

--
-- TOC entry 222 (class 1259 OID 155971)
-- Name: repositorys_gitpullers; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.repositorys_gitpullers (
    id integer NOT NULL,
    repository_uuid character varying(36),
    project character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    branches character varying(255) NOT NULL,
    poll_interval integer NOT NULL,
    poll_random_delay_min integer NOT NULL,
    poll_random_delay_max integer NOT NULL,
    updated_at integer DEFAULT 0
);


ALTER TABLE public.repositorys_gitpullers OWNER TO buildbot;

--
-- TOC entry 223 (class 1259 OID 155978)
-- Name: repositorys_gitpullers_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.repositorys_gitpullers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.repositorys_gitpullers_id_seq OWNER TO buildbot;

--
-- TOC entry 2485 (class 0 OID 0)
-- Dependencies: 223
-- Name: repositorys_gitpullers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.repositorys_gitpullers_id_seq OWNED BY public.repositorys_gitpullers.id;


--
-- TOC entry 224 (class 1259 OID 155980)
-- Name: users; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.users (
    uid integer NOT NULL,
    email character varying(255) NOT NULL,
    bb_username character varying(128) DEFAULT NULL::character varying,
    bb_password character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public.users OWNER TO buildbot;

--
-- TOC entry 225 (class 1259 OID 155988)
-- Name: users_uid_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.users_uid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_uid_seq OWNER TO buildbot;

--
-- TOC entry 2486 (class 0 OID 0)
-- Dependencies: 225
-- Name: users_uid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: buildbot
--

ALTER SEQUENCE public.users_uid_seq OWNED BY public.users.uid;


--
-- TOC entry 226 (class 1259 OID 155990)
-- Name: versions; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.versions (
    uuid character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    package_uuid character varying(36),
    file_hash character varying(255) NOT NULL,
    commit_id character varying(255) NOT NULL,
    deleted boolean,
    deleted_at integer
);


ALTER TABLE public.versions OWNER TO buildbot;

--
-- TOC entry 227 (class 1259 OID 155996)
-- Name: versions_keywords; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.versions_keywords (
    uuid character varying(36) NOT NULL,
    keyword_id integer NOT NULL,
    version_uuid character varying(36),
    status public.versions_keywords_status
);


ALTER TABLE public.versions_keywords OWNER TO buildbot;

--
-- TOC entry 232 (class 1259 OID 702199)
-- Name: versions_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: buildbot
--

CREATE SEQUENCE public.versions_metadata_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.versions_metadata_id_seq OWNER TO buildbot;

--
-- TOC entry 231 (class 1259 OID 698041)
-- Name: versions_metadata; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.versions_metadata (
    version_uuid character varying(36),
    metadata public.versions_metadata_type,
    value character varying(255),
    id integer DEFAULT nextval('public.versions_metadata_id_seq'::regclass) NOT NULL
);


ALTER TABLE public.versions_metadata OWNER TO buildbot;

--
-- TOC entry 228 (class 1259 OID 484104)
-- Name: workers; Type: TABLE; Schema: public; Owner: buildbot
--

CREATE TABLE public.workers (
    uuid character varying(36),
    enable boolean,
    type public.workers_type
);


ALTER TABLE public.workers OWNER TO buildbot;

--
-- TOC entry 2228 (class 2604 OID 155999)
-- Name: portages_makeconf id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.portages_makeconf ALTER COLUMN id SET DEFAULT nextval('public.portages_makeconf_id_seq'::regclass);


--
-- TOC entry 2230 (class 2604 OID 156000)
-- Name: projects_builds id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_builds ALTER COLUMN id SET DEFAULT nextval('public.projects_builds_id_seq'::regclass);


--
-- TOC entry 2231 (class 2604 OID 156001)
-- Name: projects_emerge_options id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_emerge_options ALTER COLUMN id SET DEFAULT nextval('public.projects_emerge_options_id_seq'::regclass);


--
-- TOC entry 2232 (class 2604 OID 156002)
-- Name: projects_pattern id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_pattern ALTER COLUMN id SET DEFAULT nextval('public.projects_pattern_id_seq'::regclass);


--
-- TOC entry 2233 (class 2604 OID 156003)
-- Name: projects_portage id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portage ALTER COLUMN id SET DEFAULT nextval('public.projects_portage_id_seq'::regclass);


--
-- TOC entry 2234 (class 2604 OID 156004)
-- Name: projects_portages_env id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_env ALTER COLUMN id SET DEFAULT nextval('public.projects_portages_env_id_seq'::regclass);


--
-- TOC entry 2235 (class 2604 OID 156005)
-- Name: projects_portages_makeconf id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_makeconf ALTER COLUMN id SET DEFAULT nextval('public.projects_portages_makeconf_id_seq'::regclass);


--
-- TOC entry 2236 (class 2604 OID 156006)
-- Name: projects_repositorys id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_repositorys ALTER COLUMN id SET DEFAULT nextval('public.projects_repositorys_id_seq'::regclass);


--
-- TOC entry 2238 (class 2604 OID 156007)
-- Name: repositorys_gitpullers id; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.repositorys_gitpullers ALTER COLUMN id SET DEFAULT nextval('public.repositorys_gitpullers_id_seq'::regclass);


--
-- TOC entry 2241 (class 2604 OID 156008)
-- Name: users uid; Type: DEFAULT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.users ALTER COLUMN uid SET DEFAULT nextval('public.users_uid_seq'::regclass);


--
-- TOC entry 2244 (class 2606 OID 156010)
-- Name: categorys categorys_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.categorys
    ADD CONSTRAINT categorys_pkey PRIMARY KEY (uuid);


--
-- TOC entry 2246 (class 2606 OID 156012)
-- Name: categorys categorys_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.categorys
    ADD CONSTRAINT categorys_unique UNIQUE (uuid);


--
-- TOC entry 2248 (class 2606 OID 156014)
-- Name: keywords keywords_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.keywords
    ADD CONSTRAINT keywords_pkey PRIMARY KEY (id);


--
-- TOC entry 2250 (class 2606 OID 156016)
-- Name: keywords keywords_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.keywords
    ADD CONSTRAINT keywords_unique UNIQUE (id);


--
-- TOC entry 2252 (class 2606 OID 156018)
-- Name: migrate_version migrate_version_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.migrate_version
    ADD CONSTRAINT migrate_version_pkey PRIMARY KEY (repository_id);


--
-- TOC entry 2254 (class 2606 OID 156020)
-- Name: packages packages_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.packages
    ADD CONSTRAINT packages_pkey PRIMARY KEY (uuid);


--
-- TOC entry 2256 (class 2606 OID 156022)
-- Name: packages packages_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.packages
    ADD CONSTRAINT packages_unique UNIQUE (uuid);


--
-- TOC entry 2258 (class 2606 OID 156024)
-- Name: portages_makeconf portages_makeconf_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.portages_makeconf
    ADD CONSTRAINT portages_makeconf_pkey PRIMARY KEY (id);


--
-- TOC entry 2260 (class 2606 OID 156026)
-- Name: portages_makeconf portages_makeconf_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.portages_makeconf
    ADD CONSTRAINT portages_makeconf_unique UNIQUE (id);


--
-- TOC entry 2266 (class 2606 OID 156028)
-- Name: projects_builds projects_builds_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_builds
    ADD CONSTRAINT projects_builds_pkey PRIMARY KEY (id);


--
-- TOC entry 2268 (class 2606 OID 156030)
-- Name: projects_builds projects_builds_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_builds
    ADD CONSTRAINT projects_builds_unique UNIQUE (id);


--
-- TOC entry 2270 (class 2606 OID 156032)
-- Name: projects_emerge_options projects_emerge_options_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_emerge_options
    ADD CONSTRAINT projects_emerge_options_pkey PRIMARY KEY (id);


--
-- TOC entry 2272 (class 2606 OID 156034)
-- Name: projects_emerge_options projects_emerge_options_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_emerge_options
    ADD CONSTRAINT projects_emerge_options_unique UNIQUE (id);


--
-- TOC entry 2274 (class 2606 OID 156036)
-- Name: projects_pattern projects_pattern_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_pattern
    ADD CONSTRAINT projects_pattern_pkey PRIMARY KEY (id);


--
-- TOC entry 2276 (class 2606 OID 156038)
-- Name: projects_pattern projects_pattern_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_pattern
    ADD CONSTRAINT projects_pattern_unique UNIQUE (id);


--
-- TOC entry 2262 (class 2606 OID 156040)
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (uuid);


--
-- TOC entry 2316 (class 2606 OID 550233)
-- Name: projects_portages_package projects_portage_package_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_package
    ADD CONSTRAINT projects_portage_package_pkey PRIMARY KEY (id);


--
-- TOC entry 2278 (class 2606 OID 156042)
-- Name: projects_portage projects_portage_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portage
    ADD CONSTRAINT projects_portage_pkey PRIMARY KEY (id);


--
-- TOC entry 2280 (class 2606 OID 156044)
-- Name: projects_portage projects_portage_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portage
    ADD CONSTRAINT projects_portage_unique UNIQUE (id);


--
-- TOC entry 2282 (class 2606 OID 156046)
-- Name: projects_portages_env projects_portages_env_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_env
    ADD CONSTRAINT projects_portages_env_pkey PRIMARY KEY (id);


--
-- TOC entry 2284 (class 2606 OID 156048)
-- Name: projects_portages_env projects_portages_env_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_env
    ADD CONSTRAINT projects_portages_env_unique UNIQUE (id);


--
-- TOC entry 2286 (class 2606 OID 156050)
-- Name: projects_portages_makeconf projects_portages_makeconf_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_makeconf
    ADD CONSTRAINT projects_portages_makeconf_pkey PRIMARY KEY (id);


--
-- TOC entry 2288 (class 2606 OID 156052)
-- Name: projects_portages_makeconf projects_portages_makeconf_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_makeconf
    ADD CONSTRAINT projects_portages_makeconf_unique UNIQUE (id);


--
-- TOC entry 2290 (class 2606 OID 156054)
-- Name: projects_repositorys projects_repositorys_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_repositorys
    ADD CONSTRAINT projects_repositorys_pkey PRIMARY KEY (id);


--
-- TOC entry 2292 (class 2606 OID 156056)
-- Name: projects_repositorys projects_repositorys_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_repositorys
    ADD CONSTRAINT projects_repositorys_unique UNIQUE (id);


--
-- TOC entry 2264 (class 2606 OID 156058)
-- Name: projects projects_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_unique UNIQUE (uuid);


--
-- TOC entry 2314 (class 2606 OID 484111)
-- Name: projects_workers projects_workers_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_workers
    ADD CONSTRAINT projects_workers_pkey PRIMARY KEY (id);


--
-- TOC entry 2298 (class 2606 OID 156060)
-- Name: repositorys_gitpullers repositorys_gitpullers_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.repositorys_gitpullers
    ADD CONSTRAINT repositorys_gitpullers_pkey PRIMARY KEY (id);


--
-- TOC entry 2300 (class 2606 OID 156062)
-- Name: repositorys_gitpullers repositorys_gitpullers_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.repositorys_gitpullers
    ADD CONSTRAINT repositorys_gitpullers_unique UNIQUE (id);


--
-- TOC entry 2294 (class 2606 OID 156064)
-- Name: repositorys repositorys_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.repositorys
    ADD CONSTRAINT repositorys_pkey PRIMARY KEY (uuid);


--
-- TOC entry 2296 (class 2606 OID 156066)
-- Name: repositorys repositorys_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.repositorys
    ADD CONSTRAINT repositorys_unique UNIQUE (uuid);


--
-- TOC entry 2302 (class 2606 OID 156068)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (uid);


--
-- TOC entry 2304 (class 2606 OID 156070)
-- Name: users users_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_unique UNIQUE (uid);


--
-- TOC entry 2310 (class 2606 OID 156072)
-- Name: versions_keywords versions_keywords_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions_keywords
    ADD CONSTRAINT versions_keywords_pkey PRIMARY KEY (uuid);


--
-- TOC entry 2312 (class 2606 OID 156074)
-- Name: versions_keywords versions_keywords_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions_keywords
    ADD CONSTRAINT versions_keywords_unique UNIQUE (uuid);


--
-- TOC entry 2318 (class 2606 OID 698703)
-- Name: versions_metadata versions_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions_metadata
    ADD CONSTRAINT versions_metadata_pkey PRIMARY KEY (id);


--
-- TOC entry 2306 (class 2606 OID 156076)
-- Name: versions versions_pkey; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions
    ADD CONSTRAINT versions_pkey PRIMARY KEY (uuid);


--
-- TOC entry 2308 (class 2606 OID 156078)
-- Name: versions versions_unique; Type: CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions
    ADD CONSTRAINT versions_unique UNIQUE (uuid);


--
-- TOC entry 2319 (class 2606 OID 156079)
-- Name: packages category_uuid_fk; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.packages
    ADD CONSTRAINT category_uuid_fk FOREIGN KEY (category_uuid) REFERENCES public.categorys(uuid) NOT VALID;


--
-- TOC entry 2321 (class 2606 OID 156084)
-- Name: projects keywords_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT keywords_fkey FOREIGN KEY (keyword_id) REFERENCES public.keywords(id) NOT VALID;


--
-- TOC entry 2336 (class 2606 OID 156089)
-- Name: versions_keywords keywords_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions_keywords
    ADD CONSTRAINT keywords_fkey FOREIGN KEY (keyword_id) REFERENCES public.keywords(id) NOT VALID;


--
-- TOC entry 2328 (class 2606 OID 156094)
-- Name: projects_portages_env makeconf_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_env
    ADD CONSTRAINT makeconf_fkey FOREIGN KEY (makeconf_id) REFERENCES public.portages_makeconf(id) NOT VALID;


--
-- TOC entry 2330 (class 2606 OID 156099)
-- Name: projects_portages_makeconf makeconf_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_makeconf
    ADD CONSTRAINT makeconf_fkey FOREIGN KEY (makeconf_id) REFERENCES public.portages_makeconf(id) NOT VALID;


--
-- TOC entry 2335 (class 2606 OID 156104)
-- Name: versions packages_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions
    ADD CONSTRAINT packages_fkey FOREIGN KEY (package_uuid) REFERENCES public.packages(uuid) NOT VALID;


--
-- TOC entry 2322 (class 2606 OID 156109)
-- Name: projects profile_repositorys_uuid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT profile_repositorys_uuid_fkey FOREIGN KEY (profile_repository_uuid) REFERENCES public.repositorys(uuid) NOT VALID;


--
-- TOC entry 2338 (class 2606 OID 550234)
-- Name: projects_portages_package project_portage_package_pkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_package
    ADD CONSTRAINT project_portage_package_pkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2323 (class 2606 OID 156114)
-- Name: projects_builds projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_builds
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2325 (class 2606 OID 156119)
-- Name: projects_emerge_options projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_emerge_options
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2326 (class 2606 OID 156124)
-- Name: projects_pattern projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_pattern
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2327 (class 2606 OID 156129)
-- Name: projects_portage projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portage
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2329 (class 2606 OID 156134)
-- Name: projects_portages_env projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_env
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2331 (class 2606 OID 156139)
-- Name: projects_portages_makeconf projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_portages_makeconf
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2332 (class 2606 OID 156144)
-- Name: projects_repositorys projects_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_repositorys
    ADD CONSTRAINT projects_fkey FOREIGN KEY (project_uuid) REFERENCES public.projects(uuid) NOT VALID;


--
-- TOC entry 2333 (class 2606 OID 156149)
-- Name: projects_repositorys repositorys_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_repositorys
    ADD CONSTRAINT repositorys_fkey FOREIGN KEY (repository_uuid) REFERENCES public.repositorys(uuid) NOT VALID;


--
-- TOC entry 2334 (class 2606 OID 156154)
-- Name: repositorys_gitpullers repositorys_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.repositorys_gitpullers
    ADD CONSTRAINT repositorys_fkey FOREIGN KEY (repository_uuid) REFERENCES public.repositorys(uuid) NOT VALID;


--
-- TOC entry 2320 (class 2606 OID 156159)
-- Name: packages repositorys_uuid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.packages
    ADD CONSTRAINT repositorys_uuid_fkey FOREIGN KEY (repository_uuid) REFERENCES public.repositorys(uuid) NOT VALID;


--
-- TOC entry 2324 (class 2606 OID 156164)
-- Name: projects_builds versions_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.projects_builds
    ADD CONSTRAINT versions_fkey FOREIGN KEY (version_uuid) REFERENCES public.versions(uuid) NOT VALID;


--
-- TOC entry 2337 (class 2606 OID 156169)
-- Name: versions_keywords versions_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions_keywords
    ADD CONSTRAINT versions_fkey FOREIGN KEY (version_uuid) REFERENCES public.versions(uuid) NOT VALID;


--
-- TOC entry 2339 (class 2606 OID 698046)
-- Name: versions_metadata versions_metadata_version_uuid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: buildbot
--

ALTER TABLE ONLY public.versions_metadata
    ADD CONSTRAINT versions_metadata_version_uuid_fkey FOREIGN KEY (version_uuid) REFERENCES public.versions(uuid);


--
-- TOC entry 2476 (class 0 OID 0)
-- Dependencies: 3
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO buildbot;


-- Completed on 2022-08-21 10:37:13 CEST

--
-- PostgreSQL database dump complete
--

