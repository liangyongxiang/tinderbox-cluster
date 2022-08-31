--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:10:28 CET

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
-- TOC entry 2322 (class 0 OID 155906)
-- Dependencies: 201
-- Data for Name: keywords; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.keywords VALUES (1, 'amd64');
INSERT INTO public.keywords VALUES (2, 'alpha');
INSERT INTO public.keywords VALUES (3, 'arm');
INSERT INTO public.keywords VALUES (4, 'arm64');
INSERT INTO public.keywords VALUES (5, 'hppa');
INSERT INTO public.keywords VALUES (6, 'ia64');
INSERT INTO public.keywords VALUES (7, 'm68k');
INSERT INTO public.keywords VALUES (8, 'mips');
INSERT INTO public.keywords VALUES (9, 'ppc');
INSERT INTO public.keywords VALUES (10, 'ppc64');
INSERT INTO public.keywords VALUES (11, 'riscv');
INSERT INTO public.keywords VALUES (12, 's390');
INSERT INTO public.keywords VALUES (13, 'sparc');
INSERT INTO public.keywords VALUES (14, 'x86');
INSERT INTO public.keywords VALUES (15, 'x64-macos');
INSERT INTO public.keywords VALUES (16, 'x64-cygwin');
INSERT INTO public.keywords VALUES (17, 'amd64-linux');
INSERT INTO public.keywords VALUES (18, 'x86-linux');
INSERT INTO public.keywords VALUES (19, 'ppc-macos');
INSERT INTO public.keywords VALUES (20, 'sparc-solaris');
INSERT INTO public.keywords VALUES (21, 'sparc64-solaris');
INSERT INTO public.keywords VALUES (22, 'x64-solaris');
INSERT INTO public.keywords VALUES (23, 'x86-solaris');
INSERT INTO public.keywords VALUES (30, '*');
INSERT INTO public.keywords VALUES (38, 'x86-winnt');
INSERT INTO public.keywords VALUES (39, 'arm64-linux');
INSERT INTO public.keywords VALUES (40, 'ppc64-linux');
INSERT INTO public.keywords VALUES (41, 'arm-linux');
INSERT INTO public.keywords VALUES (42, 'loong');

-- Completed on 2022-01-24 01:10:28 CET

--
-- PostgreSQL database dump complete
--

