--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:18:05 CET

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
-- TOC entry 2325 (class 0 OID 155960)
-- Dependencies: 219
-- Data for Name: projects_repositorys; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.projects_repositorys VALUES (2, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfa', 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb', true, 'package', true, false);
INSERT INTO public.projects_repositorys VALUES (1, 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcfd', 'e89c2c1a-46e0-4ded-81dd-c51afeb7fcbb', true, 'package', true, false);


--
-- TOC entry 2333 (class 0 OID 0)
-- Dependencies: 220
-- Name: projects_repositorys_id_seq; Type: SEQUENCE SET; Schema: public; Owner: buildbot
--

SELECT pg_catalog.setval('public.projects_repositorys_id_seq', 1, false);


-- Completed on 2022-01-24 01:18:08 CET

--
-- PostgreSQL database dump complete
--

