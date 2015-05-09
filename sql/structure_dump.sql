-- phpMyAdmin SQL Dump
-- version 4.2.13
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: May 09, 2015 at 03:13 PM
-- Server version: 10.0.15-MariaDB-log
-- PHP Version: 5.6.5-pl0-gentoo

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `tbc`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`tbc`@`localhost` PROCEDURE `add_jobs_esync`()
    MODIFIES SQL DATA
BEGIN
  DECLARE in_config_id INT;
  DECLARE in_job_id INT;
  SET in_config_id = (SELECT config_id
    FROM configs WHERE default_config = True);
  SET in_job_id = (SELECT job_id FROM jobs 
    WHERE job_type = 'esync'
    AND config_id = in_config_id 
    AND status = 'Done'
    LIMIT 1);
  IF in_job_id >= 1 THEN
    UPDATE jobs SET user = 'cron', status = 'Waiting' WHERE job_type = 'esync';
  ELSE
  	SET in_job_id = 0;
  END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `build_jobs`
--

CREATE TABLE IF NOT EXISTS `build_jobs` (
`build_job_id` int(11) NOT NULL,
  `ebuild_id` int(11) NOT NULL,
  `setup_id` int(11) NOT NULL,
  `config_id` int(11) NOT NULL,
  `status` enum('Waiting','Building','Looked') NOT NULL DEFAULT 'Waiting',
  `build_now` tinyint(1) NOT NULL,
  `removebin` tinyint(1) NOT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='The build work list';

-- --------------------------------------------------------

--
-- Table structure for table `build_jobs_emerge_options`
--

CREATE TABLE IF NOT EXISTS `build_jobs_emerge_options` (
`id` int(11) NOT NULL,
  `build_job_id` int(11) NOT NULL,
  `eoption_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_jobs_redo`
--

CREATE TABLE IF NOT EXISTS `build_jobs_redo` (
`id` int(11) NOT NULL,
  `build_job_id` int(11) NOT NULL COMMENT 'build job id',
  `fail_times` int(1) NOT NULL COMMENT 'Fail times max 5',
  `fail_type` varchar(30) NOT NULL COMMENT 'Type of fail',
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Time'
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Build jobs that need to be redone';

-- --------------------------------------------------------

--
-- Table structure for table `build_jobs_use`
--

CREATE TABLE IF NOT EXISTS `build_jobs_use` (
`id` int(11) NOT NULL,
  `build_job_id` int(11) NOT NULL,
  `use_id` int(11) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs`
--

CREATE TABLE IF NOT EXISTS `build_logs` (
`build_log_id` int(11) NOT NULL,
  `ebuild_id` int(11) NOT NULL,
  `fail` tinyint(1) NOT NULL DEFAULT '0',
  `summery_text` longtext NOT NULL,
  `log_hash` varchar(100) NOT NULL,
  `bug_id` int(10) NOT NULL DEFAULT '0',
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Main log info for the builds';

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_config`
--

CREATE TABLE IF NOT EXISTS `build_logs_config` (
`log_id` int(11) NOT NULL,
  `build_log_id` int(11) NOT NULL,
  `config_id` int(11) NOT NULL,
  `einfo_id` int(11) NOT NULL,
  `logname` varchar(150) NOT NULL COMMENT 'filename of the log',
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_emerge_options`
--

CREATE TABLE IF NOT EXISTS `build_logs_emerge_options` (
`id` int(11) NOT NULL,
  `build_logs_id` int(11) NOT NULL,
  `eoption_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_errors`
--

CREATE TABLE IF NOT EXISTS `build_logs_errors` (
`id` int(11) NOT NULL,
  `build_log_id` int(11) NOT NULL,
  `error_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_hilight`
--

CREATE TABLE IF NOT EXISTS `build_logs_hilight` (
`id` int(11) NOT NULL,
  `log_id` int(11) NOT NULL,
  `start_line` int(11) NOT NULL,
  `end_line` int(11) NOT NULL,
  `hilight_css_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_qa`
--

CREATE TABLE IF NOT EXISTS `build_logs_qa` (
`id` int(11) NOT NULL,
  `build_log_id` int(11) NOT NULL,
  `summery_text` text NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_repoman`
--

CREATE TABLE IF NOT EXISTS `build_logs_repoman` (
`id` int(11) NOT NULL,
  `build_log_id` int(11) NOT NULL,
  `summery_text` text NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `build_logs_use`
--

CREATE TABLE IF NOT EXISTS `build_logs_use` (
`id` int(11) NOT NULL,
  `build_log_id` int(11) NOT NULL,
  `use_id` int(11) NOT NULL,
  `status` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE IF NOT EXISTS `categories` (
`category_id` int(11) NOT NULL,
  `category` varchar(50) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '0',
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Categories main table (C)';

-- --------------------------------------------------------

--
-- Table structure for table `configs`
--

CREATE TABLE IF NOT EXISTS `configs` (
`config_id` int(11) NOT NULL COMMENT 'Config index',
  `hostname` varchar(50) NOT NULL,
  `setup_id` int(11) NOT NULL COMMENT 'setup',
  `default_config` tinyint(1) NOT NULL COMMENT 'Host setup'
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Main config table';

-- --------------------------------------------------------

--
-- Table structure for table `configs_emerge_options`
--

CREATE TABLE IF NOT EXISTS `configs_emerge_options` (
`id` int(11) NOT NULL,
  `config_id` int(11) NOT NULL COMMENT 'config id',
  `eoption_id` int(11) NOT NULL COMMENT 'emerge option id'
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Emerge command options for the configs';

-- --------------------------------------------------------

--
-- Table structure for table `configs_metadata`
--

CREATE TABLE IF NOT EXISTS `configs_metadata` (
`id` int(11) NOT NULL,
  `config_id` int(11) NOT NULL,
  `profile` varchar(50) NOT NULL,
  `keyword_id` int(11) NOT NULL,
  `make_conf_text` text NOT NULL,
  `checksum` varchar(100) NOT NULL,
  `configsync` tinyint(1) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `config_error_text` text NOT NULL,
  `updateing` tinyint(1) NOT NULL,
  `status` enum('Waiting','Runing','Stoped') NOT NULL,
  `auto` tinyint(1) NOT NULL,
  `git_www` varchar(100) NOT NULL COMMENT 'git repo www wiev address',
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Config Status';

-- --------------------------------------------------------

--
-- Table structure for table `ebuilds`
--

CREATE TABLE IF NOT EXISTS `ebuilds` (
`ebuild_id` int(11) NOT NULL,
  `package_id` int(11) NOT NULL,
  `version` varchar(50) NOT NULL,
  `checksum` varchar(100) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '0',
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Version main table (V)';

-- --------------------------------------------------------

--
-- Table structure for table `ebuilds_iuse`
--

CREATE TABLE IF NOT EXISTS `ebuilds_iuse` (
`id` int(11) NOT NULL,
  `ebuild_id` int(11) NOT NULL,
  `use_id` int(11) NOT NULL,
  `status` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `ebuilds_keywords`
--

CREATE TABLE IF NOT EXISTS `ebuilds_keywords` (
`id` int(11) NOT NULL,
  `ebuild_id` int(11) NOT NULL,
  `keyword_id` int(11) NOT NULL,
  `status` enum('Stable','Unstable','Negative') NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `ebuilds_metadata`
--

CREATE TABLE IF NOT EXISTS `ebuilds_metadata` (
`id` int(11) NOT NULL,
  `ebuild_id` int(11) NOT NULL,
  `revision` varchar(10) NOT NULL COMMENT 'CVS revision'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `ebuilds_restrictions`
--

CREATE TABLE IF NOT EXISTS `ebuilds_restrictions` (
`id` int(11) NOT NULL,
  `ebuild_id` int(11) NOT NULL,
  `restriction_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `emails`
--

CREATE TABLE IF NOT EXISTS `emails` (
`email_id` int(11) NOT NULL,
  `email` varchar(150) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `emerge_info`
--

CREATE TABLE IF NOT EXISTS `emerge_info` (
`einfo_id` int(11) NOT NULL,
  `emerge_info_text` text NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `emerge_options`
--

CREATE TABLE IF NOT EXISTS `emerge_options` (
`eoption_id` int(11) NOT NULL COMMENT 'emerge command options id',
  `eoption` varchar(15) NOT NULL COMMENT 'emerge command options'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `errors_info`
--

CREATE TABLE IF NOT EXISTS `errors_info` (
`error_id` int(11) NOT NULL,
  `error_name` varchar(10) NOT NULL,
  `error_search` varchar(20) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `hilight`
--

CREATE TABLE IF NOT EXISTS `hilight` (
`hilight_id` int(11) NOT NULL,
  `hilight_search` varchar(30) NOT NULL,
  `hilight_search_end` varchar(30) NOT NULL,
  `hilight_search_pattern` varchar(30) NOT NULL,
  `hilight_css_id` int(11) NOT NULL,
  `hilight_start` int(11) NOT NULL,
  `hilight_end` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `hilight_css`
--

CREATE TABLE IF NOT EXISTS `hilight_css` (
`hilight_css_id` int(11) NOT NULL,
  `hilight_css_name` varchar(11) NOT NULL,
  `hilight_css_collor` varchar(10) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `jobs`
--

CREATE TABLE IF NOT EXISTS `jobs` (
`job_id` int(11) NOT NULL,
  `job_type` enum('esync','updatedb') NOT NULL,
  `status` enum('Runing','Done','Waiting') NOT NULL DEFAULT 'Waiting',
  `user` varchar(20) NOT NULL,
  `config_id` int(11) NOT NULL,
  `run_config_id` int(11) NOT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `keywords`
--

CREATE TABLE IF NOT EXISTS `keywords` (
`keyword_id` int(11) NOT NULL COMMENT 'keyword index',
  `keyword` varchar(15) NOT NULL COMMENT 'keyword'
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='KEYWORD';

-- --------------------------------------------------------

--
-- Table structure for table `logs`
--

CREATE TABLE IF NOT EXISTS `logs` (
`log_id` int(11) NOT NULL,
  `config_id` int(11) NOT NULL,
  `log_type` enum('info','error','debug','qa') NOT NULL,
  `msg` text NOT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `packages`
--

CREATE TABLE IF NOT EXISTS `packages` (
`package_id` int(11) NOT NULL,
  `category_id` int(11) NOT NULL,
  `package` varchar(50) NOT NULL,
  `repo_id` int(11) NOT NULL,
  `checksum` varchar(100) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Packages main table (P)';

-- --------------------------------------------------------

--
-- Table structure for table `packages_emails`
--

CREATE TABLE IF NOT EXISTS `packages_emails` (
`id` int(11) NOT NULL,
  `package_id` int(11) NOT NULL,
  `email_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `packages_metadata`
--

CREATE TABLE IF NOT EXISTS `packages_metadata` (
`id` int(11) NOT NULL,
  `package_id` int(11) NOT NULL,
  `checksum` varchar(100) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `repos`
--

CREATE TABLE IF NOT EXISTS `repos` (
`repo_id` int(11) NOT NULL,
  `repo` varchar(100) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Repo main table (repo)';

-- --------------------------------------------------------

--
-- Table structure for table `restrictions`
--

CREATE TABLE IF NOT EXISTS `restrictions` (
`restriction_id` int(11) NOT NULL,
  `restriction` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `setups`
--

CREATE TABLE IF NOT EXISTS `setups` (
`setup_id` int(11) NOT NULL,
  `setup` varchar(100) NOT NULL,
  `profile` varchar(150) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `uses`
--

CREATE TABLE IF NOT EXISTS `uses` (
`use_id` int(11) NOT NULL,
  `flag` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Use flags main table';

--
-- Indexes for dumped tables
--

--
-- Indexes for table `build_jobs`
--
ALTER TABLE `build_jobs`
 ADD PRIMARY KEY (`build_job_id`), ADD KEY `ebuild_id` (`ebuild_id`), ADD KEY `config_id` (`config_id`), ADD KEY `time_stamp` (`time_stamp`);

--
-- Indexes for table `build_jobs_emerge_options`
--
ALTER TABLE `build_jobs_emerge_options`
 ADD PRIMARY KEY (`id`), ADD KEY `build_job_id` (`build_job_id`), ADD KEY `eoption_id` (`eoption_id`);

--
-- Indexes for table `build_jobs_redo`
--
ALTER TABLE `build_jobs_redo`
 ADD PRIMARY KEY (`id`), ADD KEY `build_job_id` (`build_job_id`);

--
-- Indexes for table `build_jobs_use`
--
ALTER TABLE `build_jobs_use`
 ADD PRIMARY KEY (`id`), ADD KEY `build_job_id` (`build_job_id`), ADD KEY `use_id` (`use_id`);

--
-- Indexes for table `build_logs`
--
ALTER TABLE `build_logs`
 ADD PRIMARY KEY (`build_log_id`), ADD KEY `ebuild_id` (`ebuild_id`);

--
-- Indexes for table `build_logs_config`
--
ALTER TABLE `build_logs_config`
 ADD PRIMARY KEY (`log_id`), ADD KEY `config_id` (`config_id`), ADD KEY `build_log_id` (`build_log_id`), ADD KEY `einfo_id` (`einfo_id`);

--
-- Indexes for table `build_logs_emerge_options`
--
ALTER TABLE `build_logs_emerge_options`
 ADD PRIMARY KEY (`id`), ADD KEY `eoption_id` (`eoption_id`), ADD KEY `build_logs_id` (`build_logs_id`);

--
-- Indexes for table `build_logs_errors`
--
ALTER TABLE `build_logs_errors`
 ADD PRIMARY KEY (`id`), ADD KEY `build_log_id` (`build_log_id`), ADD KEY `error_id` (`error_id`);

--
-- Indexes for table `build_logs_hilight`
--
ALTER TABLE `build_logs_hilight`
 ADD PRIMARY KEY (`id`), ADD KEY `log_id` (`log_id`), ADD KEY `hilight_id` (`hilight_css_id`), ADD KEY `hilight_css_id` (`hilight_css_id`);

--
-- Indexes for table `build_logs_qa`
--
ALTER TABLE `build_logs_qa`
 ADD PRIMARY KEY (`id`), ADD KEY `build_log_id` (`build_log_id`);

--
-- Indexes for table `build_logs_repoman`
--
ALTER TABLE `build_logs_repoman`
 ADD PRIMARY KEY (`id`), ADD KEY `build_logs_id` (`build_log_id`);

--
-- Indexes for table `build_logs_use`
--
ALTER TABLE `build_logs_use`
 ADD PRIMARY KEY (`id`), ADD KEY `build_log_id` (`build_log_id`), ADD KEY `use_id` (`use_id`);

--
-- Indexes for table `categories`
--
ALTER TABLE `categories`
 ADD PRIMARY KEY (`category_id`);

--
-- Indexes for table `configs`
--
ALTER TABLE `configs`
 ADD PRIMARY KEY (`config_id`);

--
-- Indexes for table `configs_emerge_options`
--
ALTER TABLE `configs_emerge_options`
 ADD PRIMARY KEY (`id`), ADD KEY `config_id` (`config_id`), ADD KEY `eoption_id` (`eoption_id`);

--
-- Indexes for table `configs_metadata`
--
ALTER TABLE `configs_metadata`
 ADD PRIMARY KEY (`id`), ADD KEY `keyword_id` (`keyword_id`), ADD KEY `config_id` (`config_id`);

--
-- Indexes for table `ebuilds`
--
ALTER TABLE `ebuilds`
 ADD PRIMARY KEY (`ebuild_id`), ADD KEY `package_id` (`package_id`), ADD KEY `checksum` (`checksum`), ADD KEY `version` (`version`);

--
-- Indexes for table `ebuilds_iuse`
--
ALTER TABLE `ebuilds_iuse`
 ADD PRIMARY KEY (`id`), ADD KEY `ebuild_id` (`ebuild_id`), ADD KEY `use_id` (`use_id`);

--
-- Indexes for table `ebuilds_keywords`
--
ALTER TABLE `ebuilds_keywords`
 ADD PRIMARY KEY (`id`), ADD KEY `ebuild_id` (`ebuild_id`), ADD KEY `keyword_id` (`keyword_id`);

--
-- Indexes for table `ebuilds_metadata`
--
ALTER TABLE `ebuilds_metadata`
 ADD PRIMARY KEY (`id`), ADD KEY `ebuild_id` (`ebuild_id`);

--
-- Indexes for table `ebuilds_restrictions`
--
ALTER TABLE `ebuilds_restrictions`
 ADD PRIMARY KEY (`id`), ADD KEY `ebuild_id` (`ebuild_id`), ADD KEY `restriction_id` (`restriction_id`);

--
-- Indexes for table `emails`
--
ALTER TABLE `emails`
 ADD PRIMARY KEY (`email_id`);

--
-- Indexes for table `emerge_info`
--
ALTER TABLE `emerge_info`
 ADD UNIQUE KEY `einfo_id` (`einfo_id`);

--
-- Indexes for table `emerge_options`
--
ALTER TABLE `emerge_options`
 ADD PRIMARY KEY (`eoption_id`);

--
-- Indexes for table `errors_info`
--
ALTER TABLE `errors_info`
 ADD PRIMARY KEY (`error_id`);

--
-- Indexes for table `hilight`
--
ALTER TABLE `hilight`
 ADD PRIMARY KEY (`hilight_id`), ADD KEY `hilight_css_id` (`hilight_css_id`);

--
-- Indexes for table `hilight_css`
--
ALTER TABLE `hilight_css`
 ADD PRIMARY KEY (`hilight_css_id`);

--
-- Indexes for table `jobs`
--
ALTER TABLE `jobs`
 ADD PRIMARY KEY (`job_id`), ADD KEY `config_id` (`config_id`), ADD KEY `run_config_id` (`run_config_id`), ADD KEY `job_type_id` (`job_type`);

--
-- Indexes for table `keywords`
--
ALTER TABLE `keywords`
 ADD PRIMARY KEY (`keyword_id`);

--
-- Indexes for table `logs`
--
ALTER TABLE `logs`
 ADD PRIMARY KEY (`log_id`), ADD KEY `config_id` (`config_id`);

--
-- Indexes for table `packages`
--
ALTER TABLE `packages`
 ADD PRIMARY KEY (`package_id`), ADD KEY `category_id` (`category_id`), ADD KEY `repo_id` (`repo_id`), ADD KEY `checksum` (`checksum`), ADD KEY `package` (`package`);

--
-- Indexes for table `packages_emails`
--
ALTER TABLE `packages_emails`
 ADD PRIMARY KEY (`id`), ADD KEY `package_id` (`package_id`,`email_id`);

--
-- Indexes for table `packages_metadata`
--
ALTER TABLE `packages_metadata`
 ADD PRIMARY KEY (`id`), ADD KEY `package_id` (`package_id`);

--
-- Indexes for table `repos`
--
ALTER TABLE `repos`
 ADD PRIMARY KEY (`repo_id`);

--
-- Indexes for table `restrictions`
--
ALTER TABLE `restrictions`
 ADD PRIMARY KEY (`restriction_id`);

--
-- Indexes for table `setups`
--
ALTER TABLE `setups`
 ADD PRIMARY KEY (`setup_id`), ADD UNIQUE KEY `setup_id` (`setup_id`);

--
-- Indexes for table `uses`
--
ALTER TABLE `uses`
 ADD PRIMARY KEY (`use_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `build_jobs`
--
ALTER TABLE `build_jobs`
MODIFY `build_job_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_jobs_emerge_options`
--
ALTER TABLE `build_jobs_emerge_options`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_jobs_redo`
--
ALTER TABLE `build_jobs_redo`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_jobs_use`
--
ALTER TABLE `build_jobs_use`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs`
--
ALTER TABLE `build_logs`
MODIFY `build_log_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_config`
--
ALTER TABLE `build_logs_config`
MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_emerge_options`
--
ALTER TABLE `build_logs_emerge_options`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_errors`
--
ALTER TABLE `build_logs_errors`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_hilight`
--
ALTER TABLE `build_logs_hilight`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_qa`
--
ALTER TABLE `build_logs_qa`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_repoman`
--
ALTER TABLE `build_logs_repoman`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `build_logs_use`
--
ALTER TABLE `build_logs_use`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `categories`
--
ALTER TABLE `categories`
MODIFY `category_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `configs`
--
ALTER TABLE `configs`
MODIFY `config_id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Config index';
--
-- AUTO_INCREMENT for table `configs_emerge_options`
--
ALTER TABLE `configs_emerge_options`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `configs_metadata`
--
ALTER TABLE `configs_metadata`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ebuilds`
--
ALTER TABLE `ebuilds`
MODIFY `ebuild_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ebuilds_iuse`
--
ALTER TABLE `ebuilds_iuse`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ebuilds_keywords`
--
ALTER TABLE `ebuilds_keywords`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ebuilds_metadata`
--
ALTER TABLE `ebuilds_metadata`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ebuilds_restrictions`
--
ALTER TABLE `ebuilds_restrictions`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `emails`
--
ALTER TABLE `emails`
MODIFY `email_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `emerge_info`
--
ALTER TABLE `emerge_info`
MODIFY `einfo_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `emerge_options`
--
ALTER TABLE `emerge_options`
MODIFY `eoption_id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'emerge command options id';
--
-- AUTO_INCREMENT for table `errors_info`
--
ALTER TABLE `errors_info`
MODIFY `error_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `hilight`
--
ALTER TABLE `hilight`
MODIFY `hilight_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `hilight_css`
--
ALTER TABLE `hilight_css`
MODIFY `hilight_css_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `jobs`
--
ALTER TABLE `jobs`
MODIFY `job_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `keywords`
--
ALTER TABLE `keywords`
MODIFY `keyword_id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'keyword index';
--
-- AUTO_INCREMENT for table `logs`
--
ALTER TABLE `logs`
MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `packages`
--
ALTER TABLE `packages`
MODIFY `package_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `packages_emails`
--
ALTER TABLE `packages_emails`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `packages_metadata`
--
ALTER TABLE `packages_metadata`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `repos`
--
ALTER TABLE `repos`
MODIFY `repo_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `restrictions`
--
ALTER TABLE `restrictions`
MODIFY `restriction_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `setups`
--
ALTER TABLE `setups`
MODIFY `setup_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `uses`
--
ALTER TABLE `uses`
MODIFY `use_id` int(11) NOT NULL AUTO_INCREMENT;
DELIMITER $$
--
-- Events
--
CREATE DEFINER=`tbc`@`localhost` EVENT `add_esync_jobs` ON SCHEDULE EVERY 1 HOUR STARTS '2012-12-23 17:15:13' ON COMPLETION NOT PRESERVE ENABLE DO BEGIN
  CALL add_jobs_esync();
END$$

DELIMITER ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
