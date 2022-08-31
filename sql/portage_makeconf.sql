--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:11:29 CET

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
-- TOC entry 2323 (class 0 OID 155918)
-- Dependencies: 204
-- Data for Name: portages_makeconf; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.portages_makeconf VALUES (1, 'CFLAGS');
INSERT INTO public.portages_makeconf VALUES (2, 'FCFLAGS');
INSERT INTO public.portages_makeconf VALUES (3, 'EMERGE_DEFAULT_OPTS');
INSERT INTO public.portages_makeconf VALUES (4, 'FEATURES');
INSERT INTO public.portages_makeconf VALUES (5, 'CXXFLAGS');
INSERT INTO public.portages_makeconf VALUES (6, 'FFLAGS');
INSERT INTO public.portages_makeconf VALUES (7, 'ACCEPT_PROPERTIES');
INSERT INTO public.portages_makeconf VALUES (8, 'ACCEPT_RESTRICT');
INSERT INTO public.portages_makeconf VALUES (9, 'ACCEPT_LICENSE');
INSERT INTO public.portages_makeconf VALUES (10, 'PYTHON_TARGETS');
INSERT INTO public.portages_makeconf VALUES (11, 'RUBY_TARGETS');
INSERT INTO public.portages_makeconf VALUES (12, 'ABI_X86');
INSERT INTO public.portages_makeconf VALUES (13, 'CHOST');
INSERT INTO public.portages_makeconf VALUES (14, 'USE');
INSERT INTO public.portages_makeconf VALUES (15, 'LINGUAS');
INSERT INTO public.portages_makeconf VALUES (16, 'L10N');
INSERT INTO public.portages_makeconf VALUES (17, 'GENTOO_MIRRORS');
INSERT INTO public.portages_makeconf VALUES (18, 'DISTDIR');
INSERT INTO public.portages_makeconf VALUES (19, 'PORTAGE_TMPDIR');


--
-- TOC entry 2331 (class 0 OID 0)
-- Dependencies: 205
-- Name: portages_makeconf_id_seq; Type: SEQUENCE SET; Schema: public; Owner: buildbot
--

SELECT pg_catalog.setval('public.portages_makeconf_id_seq', 1, false);


-- Completed on 2022-01-24 01:11:30 CET

--
-- PostgreSQL database dump complete
--

