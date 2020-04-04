-- phpMyAdmin SQL Dump
-- version 4.7.7
-- https://www.phpmyadmin.net/
--
-- Värd: localhost
-- Tid vid skapande: 09 apr 2020 kl 05:18
-- Serverversion: 10.2.22-MariaDB
-- PHP-version: 7.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Databas: `gosbs`
--

-- --------------------------------------------------------

--
-- Tabellstruktur `builds_uses`
--

CREATE TABLE `builds_uses` (
  `id` int(11) NOT NULL,
  `build_uuid` varchar(36) NOT NULL,
  `use_id` int(11) NOT NULL,
  `status` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `categories`
--

CREATE TABLE `categories` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `status` enum('failed','completed','in-progress','waiting') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `categories_metadata`
--

CREATE TABLE `categories_metadata` (
  `id` int(11) NOT NULL,
  `category_uuid` varchar(36) NOT NULL,
  `checksum` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `ebuilds`
--

CREATE TABLE `ebuilds` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `version` varchar(255) NOT NULL,
  `checksum` varchar(255) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `package_uuid` varchar(36) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `ebuilds_keywords`
--

CREATE TABLE `ebuilds_keywords` (
  `id` int(11) NOT NULL,
  `ebuild_uuid` varchar(36) NOT NULL,
  `keyword_id` int(11) NOT NULL,
  `status` enum('stable','unstable','negative') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `ebuilds_metadata`
--

CREATE TABLE `ebuilds_metadata` (
  `id` int(11) NOT NULL,
  `ebuild_uuid` varchar(36) NOT NULL,
  `commit` varchar(255) NOT NULL,
  `commit_msg` text DEFAULT NULL,
  `description` text DEFAULT NULL,
  `slot` varchar(30) NOT NULL,
  `homepage` varchar(500) NOT NULL,
  `license` varchar(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `ebuilds_restrictions`
--

CREATE TABLE `ebuilds_restrictions` (
  `id` int(11) NOT NULL,
  `ebuild_uuid` varchar(36) NOT NULL,
  `restriction_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `ebuilds_uses`
--

CREATE TABLE `ebuilds_uses` (
  `id` int(11) NOT NULL,
  `ebuild_uuid` varchar(36) NOT NULL,
  `use_id` int(11) NOT NULL,
  `status` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `emails`
--

CREATE TABLE `emails` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `keywords`
--

CREATE TABLE `keywords` (
  `id` int(11) NOT NULL,
  `keyword` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `migrate_version`
--

CREATE TABLE `migrate_version` (
  `repository_id` varchar(250) NOT NULL,
  `repository_path` text DEFAULT NULL,
  `version` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `packages`
--

CREATE TABLE `packages` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `status` enum('failed','completed','in-progress','waiting') DEFAULT NULL,
  `category_uuid` varchar(36) NOT NULL,
  `repo_uuid` varchar(36) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `packages_emails`
--

CREATE TABLE `packages_emails` (
  `id` int(11) NOT NULL,
  `package_uuid` varchar(36) NOT NULL,
  `email_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `packages_metadata`
--

CREATE TABLE `packages_metadata` (
  `id` int(11) NOT NULL,
  `package_uuid` varchar(36) NOT NULL,
  `gitlog` text DEFAULT NULL,
  `description` text DEFAULT NULL,
  `checksum` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `projects`
--

CREATE TABLE `projects` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `auto` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `projects_builds`
--

CREATE TABLE `projects_builds` (
  `uuid` varchar(36) NOT NULL,
  `ebuild_uuid` varchar(36) NOT NULL,
  `project_uuid` varchar(36) NOT NULL,
  `user_id` int(10) NOT NULL,
  `status` enum('failed','completed','in-progress','waiting') NOT NULL,
  `priority` int(1) NOT NULL DEFAULT 5,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  `deleted_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `projects_metadata`
--

CREATE TABLE `projects_metadata` (
  `id` int(11) NOT NULL,
  `project_uuid` varchar(36) NOT NULL,
  `titel` varchar(50) NOT NULL,
  `description` text NOT NULL,
  `project_repo_uuid` varchar(36) NOT NULL,
  `project_profile` varchar(50) NOT NULL,
  `project_profile_repo_uuid` varchar(36) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `projects_repos`
--

CREATE TABLE `projects_repos` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `repo_uuid` varchar(36) DEFAULT NULL,
  `project_uuid` varchar(36) DEFAULT NULL,
  `build` tinyint(1) DEFAULT NULL,
  `test` tinyint(1) NOT NULL,
  `repoman` tinyint(1) NOT NULL,
  `qa` tinyint(1) NOT NULL,
  `depclean` tinyint(1) NOT NULL,
  `auto` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `repos`
--

CREATE TABLE `repos` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `src_url` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `auto` tinyint(1) DEFAULT NULL,
  `status` enum('failed','completed','in-progress','waiting') DEFAULT NULL,
  `repo_type` enum('project','ebuild') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `restrictions`
--

CREATE TABLE `restrictions` (
  `id` int(11) NOT NULL,
  `restriction` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `services`
--

CREATE TABLE `services` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `uuid` varchar(36) DEFAULT NULL,
  `host` varchar(255) DEFAULT NULL,
  `binary` varchar(255) DEFAULT NULL,
  `topic` varchar(255) DEFAULT NULL,
  `report_count` int(11) NOT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  `disabled_reason` varchar(255) DEFAULT NULL,
  `last_seen_up` datetime DEFAULT NULL,
  `forced_down` varchar(255) DEFAULT NULL,
  `version` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `services_repos`
--

CREATE TABLE `services_repos` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `repo_uuid` varchar(36) DEFAULT NULL,
  `service_uuid` varchar(36) DEFAULT NULL,
  `auto` tinyint(1) NOT NULL,
  `status` enum('failed','completed','in-progress','waiting','stopped','rebuild_db','update_db') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `tasks`
--

CREATE TABLE `tasks` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `service_uuid` varchar(36) DEFAULT NULL,
  `repet` tinyint(1) DEFAULT NULL,
  `run` datetime DEFAULT NULL,
  `status` enum('failed','completed','in-progress','waiting') DEFAULT NULL,
  `last` datetime DEFAULT NULL,
  `priority` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `users`
--

CREATE TABLE `users` (
  `id` int(10) NOT NULL,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellstruktur `uses`
--

CREATE TABLE `uses` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `flag` varchar(255) NOT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Index för dumpade tabeller
--

--
-- Index för tabell `builds_uses`
--
ALTER TABLE `builds_uses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `builds_uses_uuid_fkey` (`build_uuid`) USING BTREE,
  ADD KEY `builds_uses_use_id_fkey` (`use_id`) USING BTREE;

--
-- Index för tabell `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`uuid`);

--
-- Index för tabell `categories_metadata`
--
ALTER TABLE `categories_metadata`
  ADD PRIMARY KEY (`id`),
  ADD KEY `categories_metadata_uuid_fkey` (`category_uuid`) USING BTREE;

--
-- Index för tabell `ebuilds`
--
ALTER TABLE `ebuilds`
  ADD PRIMARY KEY (`uuid`),
  ADD KEY `ebuilds_package_uuid_fkey` (`package_uuid`);

--
-- Index för tabell `ebuilds_keywords`
--
ALTER TABLE `ebuilds_keywords`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ebuilds_keywords_keyword_id_fkey` (`keyword_id`),
  ADD KEY `ebuild_uuid` (`ebuild_uuid`) USING BTREE;

--
-- Index för tabell `ebuilds_metadata`
--
ALTER TABLE `ebuilds_metadata`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ebuild_uuid` (`ebuild_uuid`) USING BTREE;

--
-- Index för tabell `ebuilds_restrictions`
--
ALTER TABLE `ebuilds_restrictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ebuilds_restrictions_uuid_fkey` (`ebuild_uuid`),
  ADD KEY `ebuilds_restrictions_restriction_id_fkey` (`restriction_id`);

--
-- Index för tabell `ebuilds_uses`
--
ALTER TABLE `ebuilds_uses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ebuilds_uses_uuid_fkey` (`ebuild_uuid`),
  ADD KEY `ebuilds_uses_use_id_fkey` (`use_id`);

--
-- Index för tabell `emails`
--
ALTER TABLE `emails`
  ADD PRIMARY KEY (`id`);

--
-- Index för tabell `keywords`
--
ALTER TABLE `keywords`
  ADD PRIMARY KEY (`id`);

--
-- Index för tabell `migrate_version`
--
ALTER TABLE `migrate_version`
  ADD PRIMARY KEY (`repository_id`);

--
-- Index för tabell `packages`
--
ALTER TABLE `packages`
  ADD PRIMARY KEY (`uuid`),
  ADD KEY `packages_category_uuid_fkey` (`category_uuid`),
  ADD KEY `packages_repo_uuid_fkey` (`repo_uuid`);

--
-- Index för tabell `packages_emails`
--
ALTER TABLE `packages_emails`
  ADD PRIMARY KEY (`id`),
  ADD KEY `packages_email_email_id_fkey` (`email_id`),
  ADD KEY `package_uuid` (`package_uuid`) USING BTREE;

--
-- Index för tabell `packages_metadata`
--
ALTER TABLE `packages_metadata`
  ADD PRIMARY KEY (`id`),
  ADD KEY `packages_metadata_uuid_fkey` (`package_uuid`) USING BTREE;

--
-- Index för tabell `projects`
--
ALTER TABLE `projects`
  ADD PRIMARY KEY (`uuid`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Index för tabell `projects_builds`
--
ALTER TABLE `projects_builds`
  ADD PRIMARY KEY (`uuid`);

--
-- Index för tabell `projects_metadata`
--
ALTER TABLE `projects_metadata`
  ADD PRIMARY KEY (`id`),
  ADD KEY `projects_metadata_uuid_fkey` (`project_uuid`) USING BTREE,
  ADD KEY `project_repo_uuid` (`project_repo_uuid`),
  ADD KEY `project_profile_repo_uuid` (`project_profile_repo_uuid`);

--
-- Index för tabell `projects_repos`
--
ALTER TABLE `projects_repos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `projects_repos_repo_uuid_fkey` (`repo_uuid`),
  ADD KEY `projects_repos_project_uuid_fkey` (`project_uuid`);

--
-- Index för tabell `repos`
--
ALTER TABLE `repos`
  ADD PRIMARY KEY (`uuid`);

--
-- Index för tabell `restrictions`
--
ALTER TABLE `restrictions`
  ADD PRIMARY KEY (`id`);

--
-- Index för tabell `services`
--
ALTER TABLE `services`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_services0host0topic0deleted` (`host`,`topic`,`deleted`),
  ADD UNIQUE KEY `uniq_services0host0binary0deleted` (`host`,`binary`,`deleted`);

--
-- Index för tabell `services_repos`
--
ALTER TABLE `services_repos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `projects_repos_repo_uuid_fkey` (`repo_uuid`),
  ADD KEY `projects_repos_project_uuid_fkey` (`service_uuid`);

--
-- Index för tabell `tasks`
--
ALTER TABLE `tasks`
  ADD PRIMARY KEY (`uuid`),
  ADD UNIQUE KEY `uuid` (`uuid`);

--
-- Index för tabell `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- Index för tabell `uses`
--
ALTER TABLE `uses`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT för dumpade tabeller
--

--
-- AUTO_INCREMENT för tabell `builds_uses`
--
ALTER TABLE `builds_uses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `categories_metadata`
--
ALTER TABLE `categories_metadata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `ebuilds_keywords`
--
ALTER TABLE `ebuilds_keywords`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `ebuilds_metadata`
--
ALTER TABLE `ebuilds_metadata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `ebuilds_restrictions`
--
ALTER TABLE `ebuilds_restrictions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `ebuilds_uses`
--
ALTER TABLE `ebuilds_uses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `emails`
--
ALTER TABLE `emails`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `keywords`
--
ALTER TABLE `keywords`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `packages_emails`
--
ALTER TABLE `packages_emails`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `packages_metadata`
--
ALTER TABLE `packages_metadata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `projects_metadata`
--
ALTER TABLE `projects_metadata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `projects_repos`
--
ALTER TABLE `projects_repos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `restrictions`
--
ALTER TABLE `restrictions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `services`
--
ALTER TABLE `services`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `services_repos`
--
ALTER TABLE `services_repos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `users`
--
ALTER TABLE `users`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT för tabell `uses`
--
ALTER TABLE `uses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restriktioner för dumpade tabeller
--

--
-- Restriktioner för tabell `categories_metadata`
--
ALTER TABLE `categories_metadata`
  ADD CONSTRAINT `categories_metadata_ibfk_1` FOREIGN KEY (`category_uuid`) REFERENCES `categories` (`uuid`),
  ADD CONSTRAINT `categories_metadata_uuid_fkey` FOREIGN KEY (`category_uuid`) REFERENCES `categories` (`uuid`);

--
-- Restriktioner för tabell `ebuilds`
--
ALTER TABLE `ebuilds`
  ADD CONSTRAINT `ebuilds_ibfk_1` FOREIGN KEY (`package_uuid`) REFERENCES `packages` (`uuid`),
  ADD CONSTRAINT `ebuilds_package_uuid_fkey` FOREIGN KEY (`package_uuid`) REFERENCES `packages` (`uuid`);

--
-- Restriktioner för tabell `ebuilds_keywords`
--
ALTER TABLE `ebuilds_keywords`
  ADD CONSTRAINT `ebuilds_keywords_ibfk_1` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`),
  ADD CONSTRAINT `ebuilds_keywords_ibfk_2` FOREIGN KEY (`keyword_id`) REFERENCES `keywords` (`id`),
  ADD CONSTRAINT `ebuilds_keywords_keyword_id_fkey` FOREIGN KEY (`keyword_id`) REFERENCES `keywords` (`id`),
  ADD CONSTRAINT `ebuilds_keywords_uuid_fkey` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`);

--
-- Restriktioner för tabell `ebuilds_metadata`
--
ALTER TABLE `ebuilds_metadata`
  ADD CONSTRAINT `ebuilds_metadata_ibfk_1` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`);

--
-- Restriktioner för tabell `ebuilds_restrictions`
--
ALTER TABLE `ebuilds_restrictions`
  ADD CONSTRAINT `ebuilds_restrictions_ibfk_1` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`),
  ADD CONSTRAINT `ebuilds_restrictions_ibfk_2` FOREIGN KEY (`restriction_id`) REFERENCES `restrictions` (`id`),
  ADD CONSTRAINT `ebuilds_restrictions_restriction_id_fkey` FOREIGN KEY (`restriction_id`) REFERENCES `restrictions` (`id`),
  ADD CONSTRAINT `ebuilds_restrictions_uuid_fkey` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`);

--
-- Restriktioner för tabell `ebuilds_uses`
--
ALTER TABLE `ebuilds_uses`
  ADD CONSTRAINT `ebuilds_uses_ibfk_1` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`),
  ADD CONSTRAINT `ebuilds_uses_ibfk_2` FOREIGN KEY (`use_id`) REFERENCES `uses` (`id`),
  ADD CONSTRAINT `ebuilds_uses_use_id_fkey` FOREIGN KEY (`use_id`) REFERENCES `uses` (`id`),
  ADD CONSTRAINT `ebuilds_uses_uuid_fkey` FOREIGN KEY (`ebuild_uuid`) REFERENCES `ebuilds` (`uuid`);

--
-- Restriktioner för tabell `packages`
--
ALTER TABLE `packages`
  ADD CONSTRAINT `packages_category_uuid_fkey` FOREIGN KEY (`category_uuid`) REFERENCES `categories` (`uuid`),
  ADD CONSTRAINT `packages_ibfk_1` FOREIGN KEY (`category_uuid`) REFERENCES `categories` (`uuid`),
  ADD CONSTRAINT `packages_ibfk_2` FOREIGN KEY (`repo_uuid`) REFERENCES `repos` (`uuid`),
  ADD CONSTRAINT `packages_repo_uuid_fkey` FOREIGN KEY (`repo_uuid`) REFERENCES `repos` (`uuid`);

--
-- Restriktioner för tabell `packages_emails`
--
ALTER TABLE `packages_emails`
  ADD CONSTRAINT `packages_email_email_id_fkey` FOREIGN KEY (`email_id`) REFERENCES `emails` (`id`),
  ADD CONSTRAINT `packages_emails_ibfk_1` FOREIGN KEY (`package_uuid`) REFERENCES `packages` (`uuid`),
  ADD CONSTRAINT `packages_emails_ibfk_2` FOREIGN KEY (`email_id`) REFERENCES `emails` (`id`);

--
-- Restriktioner för tabell `packages_metadata`
--
ALTER TABLE `packages_metadata`
  ADD CONSTRAINT `packages_metadata_ibfk_1` FOREIGN KEY (`package_uuid`) REFERENCES `packages` (`uuid`),
  ADD CONSTRAINT `packages_metadata_uuid_fkey` FOREIGN KEY (`package_uuid`) REFERENCES `packages` (`uuid`);

--
-- Restriktioner för tabell `projects_metadata`
--
ALTER TABLE `projects_metadata`
  ADD CONSTRAINT `projects_metadata_ibfk_1` FOREIGN KEY (`project_uuid`) REFERENCES `projects` (`uuid`),
  ADD CONSTRAINT `projects_metadata_profile_repo_uuid_fkey` FOREIGN KEY (`project_profile_repo_uuid`) REFERENCES `repos` (`uuid`),
  ADD CONSTRAINT `projects_metadata_repo_uuid_fkey` FOREIGN KEY (`project_repo_uuid`) REFERENCES `repos` (`uuid`),
  ADD CONSTRAINT `projects_metadata_uuid_fkey` FOREIGN KEY (`project_uuid`) REFERENCES `projects` (`uuid`);

--
-- Restriktioner för tabell `projects_repos`
--
ALTER TABLE `projects_repos`
  ADD CONSTRAINT `projects_repos_ibfk_1` FOREIGN KEY (`repo_uuid`) REFERENCES `repos` (`uuid`),
  ADD CONSTRAINT `projects_repos_ibfk_2` FOREIGN KEY (`project_uuid`) REFERENCES `projects` (`uuid`),
  ADD CONSTRAINT `projects_repos_project_uuid_fkey` FOREIGN KEY (`project_uuid`) REFERENCES `projects` (`uuid`),
  ADD CONSTRAINT `projects_repos_repo_uuid_fkey` FOREIGN KEY (`repo_uuid`) REFERENCES `repos` (`uuid`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
