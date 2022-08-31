--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3
-- Dumped by pg_dump version 13.5

-- Started on 2022-06-11 10:52:36 CEST

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
-- TOC entry 2324 (class 0 OID 155923)
-- Dependencies: 206
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.projects VALUES ('e89c2c1a-46e0-4ded-81dd-c51afeb7fcff', 'gosbsbase', 'Gentoo Ci base project', 'profiles/default/linux/amd64', 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb', 1, 'all', true, true, 1, false, NULL);
INSERT INTO public.projects VALUES ('e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 'defamd6417_1unstable', 'Default amd64 17.1 Unstable', 'profiles/default/linux/amd64/17.1', 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb', 1, 'unstable', true, true, 1, true, 'stage3-amd64-openrc-latest');
INSERT INTO public.projects VALUES ('e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 'gosbstest', 'Gentoo Ci test project', 'profiles/default/linux/amd64/17.1/systemd', 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb', 1, 'unstable', true, false, 1, true, 'stage3-amd64-systemd-latest');


-- Completed on 2022-06-11 10:52:36 CEST

--
-- PostgreSQL database dump complete
--

