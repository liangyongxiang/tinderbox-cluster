--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:21:23 CET

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
-- TOC entry 2325 (class 0 OID 155971)
-- Dependencies: 222
-- Data for Name: repositorys_gitpullers; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.repositorys_gitpullers VALUES (1, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb', 'gentoo', 'https://github.com/gentoo/gentoo.git', 'all', 240, 60, 120, 1634918051);


--
-- TOC entry 2333 (class 0 OID 0)
-- Dependencies: 223
-- Name: repositorys_gitpullers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: buildbot
--

SELECT pg_catalog.setval('public.repositorys_gitpullers_id_seq', 1, false);


-- Completed on 2022-01-24 01:21:24 CET

--
-- PostgreSQL database dump complete
--

