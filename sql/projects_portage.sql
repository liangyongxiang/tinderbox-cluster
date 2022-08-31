--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:14:57 CET

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
-- TOC entry 2324 (class 0 OID 155945)
-- Dependencies: 213
-- Data for Name: projects_portage; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.projects_portage VALUES (1, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 'make.profile', 'default/linux/amd64/17.1/systemd');
INSERT INTO public.projects_portage VALUES (2, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 'repos.conf', 'gentoo');
INSERT INTO public.projects_portage VALUES (3, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 'make.profile', 'default/linux/amd64/17.1/no-multilib');
INSERT INTO public.projects_portage VALUES (4, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 'repos.conf', 'gentoo');
INSERT INTO public.projects_portage VALUES (5, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 'make.profile', 'default/linux/amd64/17.1');
INSERT INTO public.projects_portage VALUES (6, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 'repos.conf', 'gentoo');


--
-- TOC entry 2332 (class 0 OID 0)
-- Dependencies: 214
-- Name: projects_portage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: buildbot
--

SELECT pg_catalog.setval('public.projects_portage_id_seq', 1, false);


-- Completed on 2022-01-24 01:14:57 CET

--
-- PostgreSQL database dump complete
--

