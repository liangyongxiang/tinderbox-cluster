--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3
-- Dumped by pg_dump version 13.5

-- Started on 2022-06-11 11:06:49 CEST

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
-- TOC entry 2325 (class 0 OID 155955)
-- Dependencies: 217
-- Data for Name: projects_portages_makeconf; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.projects_portages_makeconf VALUES (1, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 12, '64');
INSERT INTO public.projects_portages_makeconf VALUES (2, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 13, 'x86_64-pc-linux-gnu');
INSERT INTO public.projects_portages_makeconf VALUES (3, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 14, 'X');
INSERT INTO public.projects_portages_makeconf VALUES (4, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 14, 'caps');
INSERT INTO public.projects_portages_makeconf VALUES (5, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 14, 'xattr');
INSERT INTO public.projects_portages_makeconf VALUES (6, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 14, 'seccomp');
INSERT INTO public.projects_portages_makeconf VALUES (7, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 4, 'xattr');
INSERT INTO public.projects_portages_makeconf VALUES (8, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 4, 'sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (10, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 10, 'python3_9');
INSERT INTO public.projects_portages_makeconf VALUES (13, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 9, '*');
INSERT INTO public.projects_portages_makeconf VALUES (15, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 11, 'ruby26');
INSERT INTO public.projects_portages_makeconf VALUES (16, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 11, 'ruby27');
INSERT INTO public.projects_portages_makeconf VALUES (17, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 11, 'ruby30');
INSERT INTO public.projects_portages_makeconf VALUES (18, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 10, 'python3_10');
INSERT INTO public.projects_portages_makeconf VALUES (19, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 4, 'cgroup');
INSERT INTO public.projects_portages_makeconf VALUES (20, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 4, '-news');
INSERT INTO public.projects_portages_makeconf VALUES (21, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 4, '-collision-protect');
INSERT INTO public.projects_portages_makeconf VALUES (22, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 4, 'split-log');
INSERT INTO public.projects_portages_makeconf VALUES (23, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 4, 'compress-build-logs');
INSERT INTO public.projects_portages_makeconf VALUES (24, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--buildpkg=y');
INSERT INTO public.projects_portages_makeconf VALUES (26, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--rebuild-if-new-rev=y');
INSERT INTO public.projects_portages_makeconf VALUES (27, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--rebuilt-binaries=y');
INSERT INTO public.projects_portages_makeconf VALUES (28, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--usepkg=y');
INSERT INTO public.projects_portages_makeconf VALUES (29, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--binpkg-respect-use=y');
INSERT INTO public.projects_portages_makeconf VALUES (30, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--binpkg-changed-deps=y');
INSERT INTO public.projects_portages_makeconf VALUES (31, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--nospinner');
INSERT INTO public.projects_portages_makeconf VALUES (32, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--color=n');
INSERT INTO public.projects_portages_makeconf VALUES (33, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--ask=n');
INSERT INTO public.projects_portages_makeconf VALUES (34, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--quiet-build=y');
INSERT INTO public.projects_portages_makeconf VALUES (35, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 3, '--quiet-fail=y');
INSERT INTO public.projects_portages_makeconf VALUES (36, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 7, '-interactive');
INSERT INTO public.projects_portages_makeconf VALUES (37, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 8, '-fetch');
INSERT INTO public.projects_portages_makeconf VALUES (38, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 4, '-ipc-sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (39, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 4, '-network-sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (50, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 4, '-cgroup');
INSERT INTO public.projects_portages_makeconf VALUES (40, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 4, '-pid-sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (41, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 14, 'X');
INSERT INTO public.projects_portages_makeconf VALUES (42, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 14, 'elogind');
INSERT INTO public.projects_portages_makeconf VALUES (51, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 10, 'python3_10');
INSERT INTO public.projects_portages_makeconf VALUES (52, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 10, 'python3_9');
INSERT INTO public.projects_portages_makeconf VALUES (53, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 10, 'python3_8');
INSERT INTO public.projects_portages_makeconf VALUES (11, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 14, '-elogind');
INSERT INTO public.projects_portages_makeconf VALUES (12, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 14, 'systemd');
INSERT INTO public.projects_portages_makeconf VALUES (54, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 4, '-cgroup');
INSERT INTO public.projects_portages_makeconf VALUES (55, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 4, '-ipc-sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (56, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 4, '-network-sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (57, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 4, '-pid-sandbox');
INSERT INTO public.projects_portages_makeconf VALUES (58, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 11, 'ruby31');
INSERT INTO public.projects_portages_makeconf VALUES (59, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 10, 'python3_11');
INSERT INTO public.projects_portages_makeconf VALUES (60, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 11, 'ruby30');
INSERT INTO public.projects_portages_makeconf VALUES (61, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 9, '*');
INSERT INTO public.projects_portages_makeconf VALUES (62, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 11, 'ruby29');


--
-- TOC entry 2333 (class 0 OID 0)
-- Dependencies: 218
-- Name: projects_portages_makeconf_id_seq; Type: SEQUENCE SET; Schema: public; Owner: buildbot
--

SELECT pg_catalog.setval('public.projects_portages_makeconf_id_seq', 18, true);


-- Completed on 2022-06-11 11:06:49 CEST

--
-- PostgreSQL database dump complete
--

