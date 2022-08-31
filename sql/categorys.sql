--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.5

-- Started on 2022-01-24 01:05:34 CET

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
-- TOC entry 2322 (class 0 OID 155903)
-- Dependencies: 200
-- Data for Name: categorys; Type: TABLE DATA; Schema: public; Owner: buildbot
--

INSERT INTO public.categorys VALUES ('75d87269-95b7-48ba-8847-6ecb6c8b0c88', 'dev-python');
INSERT INTO public.categorys VALUES ('5bc8446d-aef4-4bc6-9354-fd6a42239ee7', 'dev-lang');
INSERT INTO public.categorys VALUES ('e5de84ef-0eb8-447b-b70c-f8e46dabb68c', 'net-proxy');
INSERT INTO public.categorys VALUES ('59e21fda-4a73-4636-9c29-cc39dc8a9dda', 'dev-util');
INSERT INTO public.categorys VALUES ('42494578-5c7f-4a6c-a00d-84d932a735c8', 'media-libs');
INSERT INTO public.categorys VALUES ('cc4d09dc-45a5-4e56-9bac-64601ba202a1', 'app-emulation');
INSERT INTO public.categorys VALUES ('eb0d9ebd-d051-41b7-8626-92455757d59d', 'dev-ruby');
INSERT INTO public.categorys VALUES ('64669bb5-8248-43ab-b794-8359c334a5c4', 'net-vpn');
INSERT INTO public.categorys VALUES ('006793b6-fba0-4e25-aab0-c86e559f6bb6', 'acct-user');
INSERT INTO public.categorys VALUES ('ff46f8dc-62c3-4e20-9282-da0f76b6dffc', 'x11-terms');
INSERT INTO public.categorys VALUES ('d3de94ff-8daf-4076-8009-b99837f339f8', 'app-admin');
INSERT INTO public.categorys VALUES ('2995bd0d-a3e8-4e1d-9e7a-ed26331e5fec', 'media-sound');
INSERT INTO public.categorys VALUES ('0055cf05-7d41-49b4-a7b9-4c0ba2226496', 'net-mail');
INSERT INTO public.categorys VALUES ('bb08d30e-eb18-444a-b8f0-6521f2a27329', 'xfce-base');
INSERT INTO public.categorys VALUES ('fed00771-c9cd-416a-a2fc-2f642b8a27d3', 'app-emacs');
INSERT INTO public.categorys VALUES ('8632a067-a0e4-4734-b08c-02bc60fb9a14', 'net-p2p');
INSERT INTO public.categorys VALUES ('943b9245-1507-422e-9e02-f0a044b38fce', 'media-gfx');
INSERT INTO public.categorys VALUES ('a008cff5-d10b-4fa0-92c0-51c825bf9a25', 'app-crypt');
INSERT INTO public.categorys VALUES ('d5e83b4c-e314-48eb-89c3-8ec21db85edf', 'x11-wm');
INSERT INTO public.categorys VALUES ('78e08409-fd99-4de7-ae48-2acd598c1f06', 'x11-misc');
INSERT INTO public.categorys VALUES ('87c903c0-7ca9-4efb-ad0d-d879d25143f9', 'media-plugins');
INSERT INTO public.categorys VALUES ('c5474d4b-3f14-4d52-b9d4-f9169106223c', 'sys-auth');
INSERT INTO public.categorys VALUES ('7d05a9a2-3c67-42d1-96d8-641186fa74fc', 'net-analyzer');
INSERT INTO public.categorys VALUES ('984634c6-7c4c-4797-a4cc-83299e327b31', 'mail-mta');
INSERT INTO public.categorys VALUES ('aafe58e4-f76a-45db-bb73-284e5e2c0a51', 'net-wireless');
INSERT INTO public.categorys VALUES ('cbe2acfb-0292-4133-b407-55fb61b49077', 'sci-chemistry');
INSERT INTO public.categorys VALUES ('deaf6698-e383-4bca-9547-4d387a930bea', 'sys-kernel');
INSERT INTO public.categorys VALUES ('1b9bc702-9f9d-43e6-8a74-80d3e11921e7', 'games-emulation');
INSERT INTO public.categorys VALUES ('ec0b8a2b-3d2d-4e5a-87ed-b24d862e160e', 'mail-client');
INSERT INTO public.categorys VALUES ('73991eec-c792-4fa8-ad26-4128ee4dfb55', 'app-dicts');
INSERT INTO public.categorys VALUES ('967989b4-e090-472b-b655-bead1ddb9855', 'dev-vcs');
INSERT INTO public.categorys VALUES ('9db9d6f5-319a-4212-a44b-a8d041015561', 'dev-ml');
INSERT INTO public.categorys VALUES ('d9500f40-480b-4883-a082-7dd4d045e273', 'dev-libs');
INSERT INTO public.categorys VALUES ('072ba7b4-9361-4b9a-9ab0-0a5ae4dbc9bc', 'media-video');
INSERT INTO public.categorys VALUES ('e8bd6dfc-999f-4981-8bf7-1d3f0a250b33', 'app-text');
INSERT INTO public.categorys VALUES ('f9853fea-42a4-4c5b-a267-0dbc2233080a', 'dev-db');
INSERT INTO public.categorys VALUES ('2f511523-7d7d-40bb-b035-7425862f47d0', 'app-misc');
INSERT INTO public.categorys VALUES ('64735c4a-330a-4107-92e0-c50208a3853c', 'sci-mathematics');
INSERT INTO public.categorys VALUES ('54ad5dac-d7db-4aea-8b09-f5fe8e02a17e', 'sci-biology');
INSERT INTO public.categorys VALUES ('a573f9f8-bae1-42b1-bc8e-7dbbcd27a111', 'games-engines');
INSERT INTO public.categorys VALUES ('bb774dff-5deb-400e-a122-474157512b0c', 'net-libs');
INSERT INTO public.categorys VALUES ('b50e4391-d748-423a-8b0f-3b6534fd8c96', 'gnome-extra');
INSERT INTO public.categorys VALUES ('f4bb3174-d08b-46a5-a05d-d1aef2a846c5', 'app-editors');
INSERT INTO public.categorys VALUES ('f86efc4b-3543-4dd9-93b3-7cf909695cd0', 'lxde-base');
INSERT INTO public.categorys VALUES ('f9740190-a939-4701-b1ff-0ed1f6598b6e', 'app-portage');
INSERT INTO public.categorys VALUES ('0308f280-f325-4e4c-a0d7-cbe6ad97767d', 'dev-haskell');
INSERT INTO public.categorys VALUES ('9bd6667f-8912-49b3-8ed6-9b75b35acc51', 'x11-themes');
INSERT INTO public.categorys VALUES ('3ef6a04d-a0b5-446e-989d-225d21ec35b3', 'media-fonts');
INSERT INTO public.categorys VALUES ('73cbee99-3ed0-432e-900d-945e8820f832', 'app-arch');
INSERT INTO public.categorys VALUES ('6ccdcf0a-a90f-4cb8-8e5c-59476aa58591', 'x11-libs');
INSERT INTO public.categorys VALUES ('804494d0-9559-4de0-bc1f-a6849e6e3021', 'app-metrics');
INSERT INTO public.categorys VALUES ('093b3058-3c0d-4b7a-a2eb-6fa9bcf10282', 'x11-drivers');
INSERT INTO public.categorys VALUES ('11a011b4-4e79-4263-a04f-ed44aefcf36b', 'net-misc');
INSERT INTO public.categorys VALUES ('838c48fb-c30a-49c8-9e1f-ca67ade605da', 'net-firewall');
INSERT INTO public.categorys VALUES ('14bf8191-4637-438d-832e-6c7e8e83aebb', 'sci-libs');
INSERT INTO public.categorys VALUES ('7d3b76cb-11d2-4e67-8796-0912e0a3cd4f', 'sys-boot');
INSERT INTO public.categorys VALUES ('984d7721-2346-4def-9a7a-a5b430bb0bab', 'net-printeger');
INSERT INTO public.categorys VALUES ('f13f3439-85ce-4447-b072-a4b6f37f4960', 'sys-block');
INSERT INTO public.categorys VALUES ('6131886f-5efa-4b35-9ad1-58bf680820e7', 'net-dns');
INSERT INTO public.categorys VALUES ('633d8f41-c53f-4520-b357-9738dc05f6b1', 'games-util');
INSERT INTO public.categorys VALUES ('8426b431-4d2b-4915-8b41-dd383f3b11bb', 'app-shells');
INSERT INTO public.categorys VALUES ('c9671d80-caac-4a3d-a7a3-070ee81a4865', 'sys-apps');
INSERT INTO public.categorys VALUES ('18423760-77bb-441e-98d5-64f693c57f32', 'sys-cluster');
INSERT INTO public.categorys VALUES ('aedf1397-2c45-4f83-8c07-cd11d3c18ffe', 'dev-java');
INSERT INTO public.categorys VALUES ('c307f5ac-db63-4481-a617-b37c4aac5691', 'app-mobilephone');
INSERT INTO public.categorys VALUES ('a91517d7-e5a2-46df-8c12-06806cb7a99c', 'dev-scheme');
INSERT INTO public.categorys VALUES ('8c8b20b9-49fc-400b-abbd-a5b1eca99224', 'sci-physics');
INSERT INTO public.categorys VALUES ('d228e621-69f2-40fc-b962-6aa43a1e8529', 'sci-geosciences');
INSERT INTO public.categorys VALUES ('e9506084-eb58-43ea-9890-784c205c6aff', 'dev-php');
INSERT INTO public.categorys VALUES ('76152c5e-909d-48e1-b443-46bf0e59d7bd', 'net-im');
INSERT INTO public.categorys VALUES ('5c03408f-59a3-467d-b4f7-397829046020', 'www-apps');
INSERT INTO public.categorys VALUES ('ac7ed6ec-0563-4a3a-a882-53358b4d4271', 'gnome-base');
INSERT INTO public.categorys VALUES ('f5c0d334-04cf-46f8-91bd-fb0b296133b8', 'sys-process');
INSERT INTO public.categorys VALUES ('aebbd0af-6320-4ac9-b429-178621985050', 'dev-cpp');
INSERT INTO public.categorys VALUES ('46eceac7-2ce2-43ed-8906-d899dde626cd', 'sys-fs');
INSERT INTO public.categorys VALUES ('5cb874a4-70dc-452f-a109-5005e6156607', 'net-ftp');
INSERT INTO public.categorys VALUES ('ee282335-ee39-409a-9df8-155c9627efd3', 'sys-devel');
INSERT INTO public.categorys VALUES ('faa2aae2-dbd2-4181-a927-5221515ec460', 'gui-libs');
INSERT INTO public.categorys VALUES ('cc5b7d8e-04ec-4f0f-bf59-82bfd9e7ef7b', 'www-client');
INSERT INTO public.categorys VALUES ('757d0a41-7c01-497e-8ec7-4d0f03191bd8', 'app-vim');
INSERT INTO public.categorys VALUES ('06c509c9-4996-4e80-b420-22691a3d7bed', 'dev-perl');
INSERT INTO public.categorys VALUES ('287e38a8-5ba3-49b0-a993-c0965b934181', 'app-backup');
INSERT INTO public.categorys VALUES ('606039a5-a4bb-442b-b45a-777fa105394b', 'sys-libs');
INSERT INTO public.categorys VALUES ('c2176517-0078-469d-9eb9-8fbac39c8269', 'net-irc');
INSERT INTO public.categorys VALUES ('6c431c6f-ff42-4108-8b0c-132ba6c18ab3', 'xfce-extra');
INSERT INTO public.categorys VALUES ('981a8c8a-c66f-435d-a500-b74bebaad4c2', 'www-plugins');
INSERT INTO public.categorys VALUES ('51177961-26f5-4b4e-bacc-5adabb331ae3', 'dev-qt');
INSERT INTO public.categorys VALUES ('98176369-2d0a-44b5-a2af-736780605af0', 'virtual');
INSERT INTO public.categorys VALUES ('669413d8-88be-4c83-a9fa-f2c10d0ef662', 'media-radio');
INSERT INTO public.categorys VALUES ('8b8c2c89-cc94-49fa-a71b-cbd93d52a032', 'mail-filter');
INSERT INTO public.categorys VALUES ('f1d954cb-eb1c-4220-a35f-14523fd29f58', 'net-fs');
INSERT INTO public.categorys VALUES ('86ecd3e7-64f2-4ba6-8ba7-290a39713b98', 'net-nds');
INSERT INTO public.categorys VALUES ('5be9ac25-3c9f-40f3-9e7e-3e77f448a719', 'games-simulation');
INSERT INTO public.categorys VALUES ('69df5af0-6a9b-486e-b4c7-dcc219c84f84', 'gui-wm');
INSERT INTO public.categorys VALUES ('3a8929c1-69a3-4dcf-80ad-4fbf9f393db2', 'games-board');
INSERT INTO public.categorys VALUES ('6de09052-d880-4e10-ab3c-c1e5b81c44b4', 'app-benchmarks');
INSERT INTO public.categorys VALUES ('8b775181-516e-48de-8ce6-5c49158a07ce', 'dev-tcltk');
INSERT INTO public.categorys VALUES ('8bfce850-aa11-4a21-b319-c037e185350c', 'app-i18n');
INSERT INTO public.categorys VALUES ('b6674f60-00ac-43ee-91c3-01199059b731', 'www-servers');
INSERT INTO public.categorys VALUES ('26ff7bf8-467f-4e72-bf63-759dd912348a', 'acct-group');
INSERT INTO public.categorys VALUES ('d950112d-d8df-4570-9fdd-d5ad6e5f5043', 'app-laptop');
INSERT INTO public.categorys VALUES ('b69b3519-34d1-416f-a880-9f6e8c159b79', 'sci-electronics');
INSERT INTO public.categorys VALUES ('d8e7043c-98fc-45d1-b469-918499cd037e', 'dev-lisp');
INSERT INTO public.categorys VALUES ('4c136608-6f08-4179-b35a-eb955077ae88', 'app-office');
INSERT INTO public.categorys VALUES ('67216091-16fd-40cc-9a23-beb4e259a513', 'games-puzzle');
INSERT INTO public.categorys VALUES ('279e0374-9e18-4f57-8172-0075d84d6daa', 'net-dialup');
INSERT INTO public.categorys VALUES ('fff1aa8d-f1e3-4220-bf24-177cac8c3bf7', 'x11-plugins');
INSERT INTO public.categorys VALUES ('02b755c9-8726-463f-85cd-a52f80631393', 'dev-lua');
INSERT INTO public.categorys VALUES ('06d956b2-65de-47cd-9e20-1e6eb1ec5d68', 'media-tv');
INSERT INTO public.categorys VALUES ('c711efcf-9f8f-4fc7-902f-2e790bf10100', 'net-voip');
INSERT INTO public.categorys VALUES ('30328b52-128f-479c-b986-2fa89dc25ed5', 'app-eselect');
INSERT INTO public.categorys VALUES ('51ed29e2-1bba-431c-ac8e-ab1a1fe88920', 'games-strategy');
INSERT INTO public.categorys VALUES ('fb9ab672-3214-4b32-acc4-2bd87ce6a9ad', 'dev-ros');
INSERT INTO public.categorys VALUES ('b7a0e9e6-c1b5-459f-a2e6-ceaa8760fb19', 'dev-games');
INSERT INTO public.categorys VALUES ('fee08b2f-a30d-442a-928e-f6829f195a34', 'sci-visualization');
INSERT INTO public.categorys VALUES ('98e8e4cc-6112-485f-8dbe-aef230f679ab', 'app-forensics');
INSERT INTO public.categorys VALUES ('fe39f5c7-c466-4e44-a4b9-5d84eb9d35bf', 'app-accessibility');
INSERT INTO public.categorys VALUES ('c7c44a9d-c70e-4152-abd0-f77694c5f0ad', 'dev-tex');
INSERT INTO public.categorys VALUES ('0b836d6b-d7be-48f8-a8f5-025f0fa925f5', 'www-apache');
INSERT INTO public.categorys VALUES ('cfef4e2f-c465-4e29-a1b8-ecc1f421237d', 'www-misc');
INSERT INTO public.categorys VALUES ('fd81103e-ab50-417b-afd6-c3ea50041651', 'app-cdr');
INSERT INTO public.categorys VALUES ('b7edb223-0a8e-4549-8ac5-fc0b0437cf9b', 'games-arcade');
INSERT INTO public.categorys VALUES ('a65f3b64-b5a6-4cfb-97db-ccbaccc21f54', 'games-fps');
INSERT INTO public.categorys VALUES ('5e9d7b3d-185b-4c60-885b-87e302e22e39', 'games-action');
INSERT INTO public.categorys VALUES ('b6209bf5-9849-4198-ad3f-7821ed7c043f', 'dev-texlive');
INSERT INTO public.categorys VALUES ('4dfa2022-a8d0-457a-9efe-07f7e3a017ba', 'games-misc');
INSERT INTO public.categorys VALUES ('c610ddb0-d539-4564-95ca-65f198e4dc0f', 'kde-frameworks');
INSERT INTO public.categorys VALUES ('4f0b8d20-edbf-4146-9961-e9785723fbd5', 'kde-apps');
INSERT INTO public.categorys VALUES ('a6788379-d868-477e-b2f6-303266397acd', 'kde-plasma');
INSERT INTO public.categorys VALUES ('65a5fa8e-c384-4f10-ae4f-eea4938ca0e9', 'app-doc');
INSERT INTO public.categorys VALUES ('6bd59f0a-0a5f-4336-a2ef-47fde7ca2dce', 'sci-astronomy');
INSERT INTO public.categorys VALUES ('aa01d2e0-0fa7-403d-8de2-43d5fc42239b', 'dev-embedded');
INSERT INTO public.categorys VALUES ('f24d92bb-1d44-4898-8bc8-917314c01199', 'sci-misc');
INSERT INTO public.categorys VALUES ('350acdb0-74b7-43ea-98d9-4c3907de52e3', 'gui-apps');
INSERT INTO public.categorys VALUES ('795eb61e-7763-475e-ad8e-5968e5f76872', 'games-roguelike');
INSERT INTO public.categorys VALUES ('b956ccde-c49d-4ff7-9c19-488862785625', 'sys-firmware');
INSERT INTO public.categorys VALUES ('891340a7-b2c0-426d-ba2f-b061dce8da82', 'x11-apps');
INSERT INTO public.categorys VALUES ('af03c490-128c-4f61-b914-277ba1fc487d', 'mate-base');
INSERT INTO public.categorys VALUES ('2b31aad3-3c46-42e9-88f2-9b06777b2531', 'ros-meta');
INSERT INTO public.categorys VALUES ('3beffd83-a877-4a04-988a-7e6fddfb852b', 'kde-misc');
INSERT INTO public.categorys VALUES ('85b542d0-8b64-4289-a67c-e5f86fcb73f5', 'perl-core');
INSERT INTO public.categorys VALUES ('acce056e-d0dd-463f-8e5f-94e00558e6cb', 'sci-calculators');
INSERT INTO public.categorys VALUES ('46dd76c0-16e8-42f3-8526-c0e9b1abaeed', 'x11-base');
INSERT INTO public.categorys VALUES ('9c2ee466-e51c-457b-b8ca-999dcc7314c4', 'games-mud');
INSERT INTO public.categorys VALUES ('5f20c4b5-5358-4f59-b80b-4c11650f791a', 'games-rpg');
INSERT INTO public.categorys VALUES ('c2571651-1494-4e64-aca9-0226fab82cbd', 'games-sports');
INSERT INTO public.categorys VALUES ('e15d9f90-eebb-4569-b927-be72e34cb26a', 'sys-fabric');
INSERT INTO public.categorys VALUES ('1aed347d-5f97-4f77-af7a-5b8efb2c75c0', 'app-antivirus');
INSERT INTO public.categorys VALUES ('49c054a5-bca2-418c-ba22-943f4992cc1f', 'games-server');
INSERT INTO public.categorys VALUES ('bdc81442-110f-4ceb-a7b3-abd1ee5e1ca8', 'dev-ada');
INSERT INTO public.categorys VALUES ('e179034e-7e22-4925-ba5a-6920c54d1b75', 'mate-extra');
INSERT INTO public.categorys VALUES ('827a4523-104e-4e1f-8b6c-9914d4582548', 'gnustep-base');
INSERT INTO public.categorys VALUES ('2676457b-a2ff-4990-bedd-7236109c30ec', 'net-news');
INSERT INTO public.categorys VALUES ('f86c6039-8c81-4967-92f3-ae76ad650c09', 'net-print');
INSERT INTO public.categorys VALUES ('51e46568-f7cb-4ce3-86b0-9408c61875e3', 'dev-dotnet');
INSERT INTO public.categorys VALUES ('554524ec-5d4e-41b0-a09f-630466715f9c', 'dev-go');
INSERT INTO public.categorys VALUES ('dc2e1f83-1877-4fb3-bf2b-6ee88e3c8942', 'games-kids');
INSERT INTO public.categorys VALUES ('a9b623eb-026e-4d57-8dc2-9701b41d83d7', 'gnustep-libs');
INSERT INTO public.categorys VALUES ('5caf19d2-7bd9-46cd-aec0-a3749e658c3b', 'net-nntp');
INSERT INTO public.categorys VALUES ('aae288d1-f1a6-4ff4-9f02-32322400cda9', 'lxqt-base');
INSERT INTO public.categorys VALUES ('e5924fa1-9f98-41ae-b6f9-10e059ecd8f5', 'app-pda');
INSERT INTO public.categorys VALUES ('b0ff5450-696f-4743-a6ba-b18c4d23a51d', 'gnustep-apps');
INSERT INTO public.categorys VALUES ('75c7a2d3-6cc1-47f2-a2d9-1f6d2a8428bf', 'sys-power');
INSERT INTO public.categorys VALUES ('aa7dc37f-fae6-4814-b1b4-a6938a073fa0', 'sec-policy');
INSERT INTO public.categorys VALUES ('d94f440b-a0a0-4d9d-a4c2-9a1a52a72536', 'dev-erlang');
INSERT INTO public.categorys VALUES ('2fde80c3-da32-42b5-ab5e-dcef3231b842', 'app-officeext');
INSERT INTO public.categorys VALUES ('3e22d695-7391-4b80-aec0-c38495be775d', 'app-xemacs');
INSERT INTO public.categorys VALUES ('3c14f428-88c8-4477-accc-3a5cbfcc4e53', 'java-virtuals');
INSERT INTO public.categorys VALUES ('8d407bf2-74b3-4abf-9935-c5919c704bf3', 'sec-keys');
INSERT INTO public.categorys VALUES ('1a891ebb-2cd9-46bb-b348-de606574d5e6', 'app-containers');


-- Completed on 2022-01-24 01:05:34 CET

--
-- PostgreSQL database dump complete
--

