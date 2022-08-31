--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:20:01 CET

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
-- TOC entry 2322 (class 0 OID 155965)
-- Dependencies: 221
-- Data for Name: repositorys; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.repositorys VALUES ('gentoo', 'Gentoo main repo', 'https://github.com/gentoo/gentoo.git', true, true, true, 'gitpuller', 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb');


-- Completed on 2022-01-24 01:20:01 CET

--
-- PostgreSQL database dump complete
--

