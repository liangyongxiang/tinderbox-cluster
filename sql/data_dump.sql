-- phpMyAdmin SQL Dump
-- version 4.2.13
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Feb 13, 2016 at 02:37 PM
-- Server version: 10.0.22-MariaDB-log
-- PHP Version: 5.6.16-pl0-gentoo

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `tbc`
--

--
-- Dumping data for table `configs`
--

INSERT INTO `configs` (`config_id`, `hostname`, `setup_id`, `default_config`) VALUES
(1, 'sandra.ume.nu', 1, 1),
(2, 'virtual1.ume.nu', 2, 0),
(3, 'virtual2.ume.nu', 3, 0),
(4, 'virtual3.ume.nu', 3, 0),
(5, 'virtual4.ume.nu', 3, 0),
(6, 'virtual5.ume.nu', 3, 0);

--
-- Dumping data for table `configs_emerge_options`
--

INSERT INTO `configs_emerge_options` (`id`, `config_id`, `eoption_id`) VALUES
(1, 2, 1),
(2, 2, 2),
(3, 2, 5),
(4, 2, 6),
(5, 3, 1),
(6, 3, 2),
(7, 3, 5),
(8, 3, 6),
(9, 4, 1),
(10, 4, 2),
(11, 4, 5),
(12, 4, 6),
(13, 5, 1),
(14, 5, 2),
(15, 5, 5),
(16, 5, 6),
(17, 6, 1),
(18, 6, 2),
(19, 6, 5),
(20, 6, 6);

--
-- Dumping data for table `configs_metadata`
--

INSERT INTO `configs_metadata` (`id`, `config_id`, `keyword_id`, `make_conf_text`, `checksum`, `configsync`, `active`, `config_error_text`, `updateing`, `status`, `auto`, `repo_path`, `time_stamp`) VALUES
(1, 1, 1, '# This is for the base config\nCHOST="x86_64-pc-linux-gnu"\nACCEPT_KEYWORDS=""\nARCH="amd64"\nFEATURES="-metadata-transfer -news distlocks"\nACCEPT_LICENSE="*"\nPORTAGE_TMPDIR=/var/tmp\nDISTDIR=/var/cache/portage/distfiles\nPORT_LOGDIR="/var/log/portage"\nGENTOO_MIRRORS="ftp://ftp.sunet.se/pub/Linux/distributions/gentoo http://distfiles.gentoo.org http://www.ibiblio.org/pub/Linux/distributions/gentoo"\nPORTAGE_TMPFS="/dev/shm"\nPORTAGE_ELOG_CLASSES=""\nPORTAGE_ELOG_SYSTEM=""\nPORTDIR_OVERLAY=""\nsource /var/cache/layman/make.conf\n', 'd29a21ae48f047f5036cb17c278ad96a8c7818bbcda29b2e766a8cc6a34a358f', 0, 1, '', 0, 'Waiting', 1, '/var/cache/gobs/tinderboxs_configs', '2015-07-17 22:54:09'),
(2, 2, 1, 'CFLAGS="-O2 -pipe -march=native"\nCXXFLAGS="-O2 -pipe -march=native"\nCHOST="x86_64-pc-linux-gnu"\nUSE="qt3support xattr semantic-desktop"\nACCEPT_KEYWORDS="~amd64 amd64"\nACCEPT_LICENSE="*"\nPORTAGE_TMPDIR=/var/tmp\nDISTDIR="/var/cache/portage/distfiles"\nPORT_LOGDIR="/var/cache/portage/logs/virtual1.ume.nu/amd64_hardened_unstable"\nPKGDIR="/var/cache/portage/packages/virtual1.ume.nu/amd64_hardened_unstable"\nGENTOO_MIRRORS="ftp://mirror.mdfnet.se/gentoo http://distfiles.gentoo.org"\nEMERGE_DEFAULT_OPTS="-v --binpkg-respect-use=y --rebuild-if-new-rev=y --rebuilt-binaries=y --autounmask=y --autounmask-write=y --jobs=3 --load-average=5.0"\nMAKEOPTS="-j6"\nAUTOCLEAN="yes"\nNOCOLOR="true"\nPORTAGE_TMPFS="/dev/shm"\nFEATURES="sandbox distlocks parallel-fetch strict -news test test-fail-continue"\nPORTAGE_ELOG_CLASSES=""\nPORTAGE_ELOG_SYSTEM="save"\nPORTDIR_OVERLAY="/usr/local/portage"\nLINGUAS="en"\nINPUT_DEVICES="keyboard mouse synaptics evdev"\nVIDEO_CARDS="radeon"\nALSA_CARDS="hda-intel intel8x0 
intel8x0m"\nALSA_PCM_PLUGINS="adpcm alaw asym copy dmix dshare dsnoop empty extplug file hooks iec958 ioplug ladspa lfloat linear meter mmap_emul mulaw multi null plug rate route share shm softvol"\nCONFIG_PROTECT_MASK="/etc/portage/package.use/99_autounmask"\n\n# for layman stuff\nsource /var/cache/layman/make.conf\n', '91820213d60929995132060b1d917740ff3b23af2a0745fde592df26ef58b5d7', 0, 1, '', 0, 'Stoped', 0, '', '2015-03-23 22:21:39'),
(3, 3, 1, 'CFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCXXFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCHOST="x86_64-pc-linux-gnu"\nUSE="X qt3support"\nACCEPT_KEYWORDS="~amd64 amd64"\nABI_X86="32 64"\nCPU_FLAGS_X86=""\nACCEPT_LICENSE="*"\nPYTHON_TARGETS="python2_7 python3_4 python3_5"\nRUBY_TARGETS="ruby20 ruby21 ruby22"\nPORTAGE_TMPDIR=/var/tmp\nDISTDIR="/var/cache/portage/distfiles"\nGENTOO_MIRRORS="ftp://mirror.mdfnet.se/gentoo ftp://trumpetti.atm.tut.fi/gentoo/ http://distfiles.gentoo.org"\nEMERGE_DEFAULT_OPTS="-v --binpkg-respect-use=y --rebuild-if-new-rev=y --rebuilt-binaries=y --binpkg-changed-deps=y --autounmask=y --autounmask-write=y --jobs=3 --load-average=5.0"\nMAKEOPTS="-j6"\nAUTOCLEAN="yes"\nNOCOLOR="true"\nPORTAGE_TMPFS="/dev/shm"\nFEATURES="sandbox distlocks parallel-fetch strict -news test-fail-continue fail-clean"\nPORTAGE_ELOG_CLASSES=""\nPORTAGE_ELOG_SYSTEM="save"\nPORTDIR_OVERLAY="/usr/local/portage"\nLINGUAS="en"\nINPUT_DEVICES="keyboard mouse synaptics evdev"\
nVIDEO_CARDS="radeon"\nALSA_CARDS="hda-intel intel8x0 intel8x0m"\nALSA_PCM_PLUGINS="adpcm alaw asym copy dmix dshare dsnoop empty extplug file hooks iec958 ioplug ladspa lfloat linear meter mmap_emul mulaw multi null plug rate route share shm softvol"\nCONFIG_PROTECT_MASK="/etc/portage/package.use/99_autounmask"\nGRUB_PLATFORMS="pc"\n\n# is in the host.conf\n#PORT_LOGDIR="/var/cache/portage/logs/host/setup"\n#PKGDIR="/var/cache/portage/packages/host/setup"\nsource host.conf\n\n# for layman stuff\n#source /var/cache/layman/make.conf\n', '35c38a4f7f2b4873cf6b6df9b21ca390602c1146b61cd514ca5b146a9d3000d0', 1, 1, '', 0, 'Runing', 1, '/var/cache/zobcs/tinderboxs_configs', '2016-02-13 14:36:20'),
(4, 4, 1, 'CFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCXXFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCHOST="x86_64-pc-linux-gnu"\nUSE="X qt3support"\nACCEPT_KEYWORDS="~amd64 amd64"\nABI_X86="32 64"\nCPU_FLAGS_X86=""\nACCEPT_LICENSE="*"\nPYTHON_TARGETS="python2_7 python3_4 python3_5"\nRUBY_TARGETS="ruby20 ruby21 ruby22"\nPORTAGE_TMPDIR=/var/tmp\nDISTDIR="/var/cache/portage/distfiles"\nGENTOO_MIRRORS="ftp://mirror.mdfnet.se/gentoo ftp://trumpetti.atm.tut.fi/gentoo/ http://distfiles.gentoo.org"\nEMERGE_DEFAULT_OPTS="-v --binpkg-respect-use=y --rebuild-if-new-rev=y --rebuilt-binaries=y --binpkg-changed-deps=y --autounmask=y --autounmask-write=y --jobs=3 --load-average=5.0"\nMAKEOPTS="-j6"\nAUTOCLEAN="yes"\nNOCOLOR="true"\nPORTAGE_TMPFS="/dev/shm"\nFEATURES="sandbox distlocks parallel-fetch strict -news test-fail-continue fail-clean"\nPORTAGE_ELOG_CLASSES=""\nPORTAGE_ELOG_SYSTEM="save"\nPORTDIR_OVERLAY="/usr/local/portage"\nLINGUAS="en"\nINPUT_DEVICES="keyboard mouse synaptics evdev"\
nVIDEO_CARDS="radeon"\nALSA_CARDS="hda-intel intel8x0 intel8x0m"\nALSA_PCM_PLUGINS="adpcm alaw asym copy dmix dshare dsnoop empty extplug file hooks iec958 ioplug ladspa lfloat linear meter mmap_emul mulaw multi null plug rate route share shm softvol"\nCONFIG_PROTECT_MASK="/etc/portage/package.use/99_autounmask"\nGRUB_PLATFORMS="pc"\n\n# is in the host.conf\n#PORT_LOGDIR="/var/cache/portage/logs/host/setup"\n#PKGDIR="/var/cache/portage/packages/host/setup"\nsource host.conf\n\n# for layman stuff\n#source /var/cache/layman/make.conf\n', '35c38a4f7f2b4873cf6b6df9b21ca390602c1146b61cd514ca5b146a9d3000d0', 1, 1, '', 0, 'Runing', 1, '/var/cache/zobcs/tinderboxs_configs', '2016-02-13 14:36:20'),
(5, 5, 1, 'CFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCXXFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCHOST="x86_64-pc-linux-gnu"\nUSE="X qt3support"\nACCEPT_KEYWORDS="~amd64 amd64"\nABI_X86="32 64"\nCPU_FLAGS_X86=""\nACCEPT_LICENSE="*"\nPYTHON_TARGETS="python2_7 python3_4 python3_5"\nRUBY_TARGETS="ruby20 ruby21 ruby22"\nPORTAGE_TMPDIR=/var/tmp\nDISTDIR="/var/cache/portage/distfiles"\nGENTOO_MIRRORS="ftp://mirror.mdfnet.se/gentoo ftp://trumpetti.atm.tut.fi/gentoo/ http://distfiles.gentoo.org"\nEMERGE_DEFAULT_OPTS="-v --binpkg-respect-use=y --rebuild-if-new-rev=y --rebuilt-binaries=y --binpkg-changed-deps=y --autounmask=y --autounmask-write=y --jobs=3 --load-average=5.0"\nMAKEOPTS="-j6"\nAUTOCLEAN="yes"\nNOCOLOR="true"\nPORTAGE_TMPFS="/dev/shm"\nFEATURES="sandbox distlocks parallel-fetch strict -news test-fail-continue fail-clean"\nPORTAGE_ELOG_CLASSES=""\nPORTAGE_ELOG_SYSTEM="save"\nPORTDIR_OVERLAY="/usr/local/portage"\nLINGUAS="en"\nINPUT_DEVICES="keyboard mouse synaptics evdev"\
nVIDEO_CARDS="radeon"\nALSA_CARDS="hda-intel intel8x0 intel8x0m"\nALSA_PCM_PLUGINS="adpcm alaw asym copy dmix dshare dsnoop empty extplug file hooks iec958 ioplug ladspa lfloat linear meter mmap_emul mulaw multi null plug rate route share shm softvol"\nCONFIG_PROTECT_MASK="/etc/portage/package.use/99_autounmask"\nGRUB_PLATFORMS="pc"\n\n# is in the host.conf\n#PORT_LOGDIR="/var/cache/portage/logs/host/setup"\n#PKGDIR="/var/cache/portage/packages/host/setup"\nsource host.conf\n\n# for layman stuff\n#source /var/cache/layman/make.conf\n', '35c38a4f7f2b4873cf6b6df9b21ca390602c1146b61cd514ca5b146a9d3000d0', 1, 1, '', 0, 'Runing', 1, '/var/cache/zobcs/tinderboxs_configs', '2016-02-13 14:36:25'),
(6, 6, 1, 'CFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCXXFLAGS="-O2 -pipe -march=native -fno-diagnostics-color"\nCHOST="x86_64-pc-linux-gnu"\nUSE="X qt3support"\nACCEPT_KEYWORDS="~amd64 amd64"\nABI_X86="32 64"\nCPU_FLAGS_X86=""\nACCEPT_LICENSE="*"\nPYTHON_TARGETS="python2_7 python3_4 python3_5"\nRUBY_TARGETS="ruby20 ruby21 ruby22"\nPORTAGE_TMPDIR=/var/tmp\nDISTDIR="/var/cache/portage/distfiles"\nGENTOO_MIRRORS="ftp://mirror.mdfnet.se/gentoo ftp://trumpetti.atm.tut.fi/gentoo/ http://distfiles.gentoo.org"\nEMERGE_DEFAULT_OPTS="-v --binpkg-respect-use=y --rebuild-if-new-rev=y --rebuilt-binaries=y --binpkg-changed-deps=y --autounmask=y --autounmask-write=y --jobs=3 --load-average=5.0"\nMAKEOPTS="-j6"\nAUTOCLEAN="yes"\nNOCOLOR="true"\nPORTAGE_TMPFS="/dev/shm"\nFEATURES="sandbox distlocks parallel-fetch strict -news test-fail-continue fail-clean"\nPORTAGE_ELOG_CLASSES=""\nPORTAGE_ELOG_SYSTEM="save"\nPORTDIR_OVERLAY="/usr/local/portage"\nLINGUAS="en"\nINPUT_DEVICES="keyboard mouse synaptics evdev"\
nVIDEO_CARDS="radeon"\nALSA_CARDS="hda-intel intel8x0 intel8x0m"\nALSA_PCM_PLUGINS="adpcm alaw asym copy dmix dshare dsnoop empty extplug file hooks iec958 ioplug ladspa lfloat linear meter mmap_emul mulaw multi null plug rate route share shm softvol"\nCONFIG_PROTECT_MASK="/etc/portage/package.use/99_autounmask"\nGRUB_PLATFORMS="pc"\n\n# is in the host.conf\n#PORT_LOGDIR="/var/cache/portage/logs/host/setup"\n#PKGDIR="/var/cache/portage/packages/host/setup"\nsource host.conf\n\n# for layman stuff\n#source /var/cache/layman/make.conf\n', '35c38a4f7f2b4873cf6b6df9b21ca390602c1146b61cd514ca5b146a9d3000d0', 1, 1, '', 0, 'Runing', 1, '/var/cache/zobcs/tinderboxs_configs', '2016-02-13 14:36:02');

--
-- Dumping data for table `emerge_options`
--

INSERT INTO `emerge_options` (`eoption_id`, `eoption`) VALUES
(1, '--oneshot'),
(2, '--depclean'),
(3, '--nodepclean'),
(4, '--nooneshot'),
(5, '--buildpkg'),
(6, '--usepkg');

--
-- Dumping data for table `errors_info`
--

INSERT INTO `errors_info` (`error_id`, `error_name`, `error_search`) VALUES
(1, 'repoman', 'repoman'),
(2, 'qa', 'qa'),
(3, 'others', 'others'),
(4, 'configure', 'configure phase'),
(5, 'test', 'test phase'),
(6, 'install', 'install phase'),
(7, 'prepare', 'prepare phase'),
(8, 'compile', 'compile phase'),
(9, 'setup', 'setup phase');

--
-- Dumping data for table `hilight`
--

INSERT INTO `hilight` (`hilight_id`, `hilight_search`, `hilight_search_end`, `hilight_search_pattern`, `hilight_css_id`, `hilight_start`, `hilight_end`) VALUES
(3, '^ \\* QA Notice:', '^ \\* ', '^ \\* ', 3, 0, 0),
(4, '^ \\* Package:', '', '', 2, 0, 4),
(5, '>>> Unpacking', '', '', 1, 0, 0),
(6, '\\[ ok ]', '', '', 2, 0, 0),
(7, '\\[ !! ]', '', '', 5, 0, 0),
(8, '>>> Source', '', '', 1, 0, 0),
(9, '>>> Preparing', '', '', 1, 0, 0),
(10, '^ \\* Applying', '', '', 2, 0, 0),
(11, '>>> Configuring', '', '', 1, 0, 0),
(12, '^ \\* econf', '', '', 1, 0, 0),
(13, '>>> Compiling', '', '', 1, 0, 0),
(14, '>>> Done.', '', '', 1, 0, 0),
(15, '>>> Merging', '', '', 1, 0, 0),
(16, '>>> Safely', '', '', 1, 0, 0),
(17, '>>> Original', '', '', 1, 0, 0),
(18, 'merged.$', '', '', 1, 0, 0),
(19, '>>> Extracting info', '', '', 1, 0, 0),
(20, '>>> Extracting (?!info)', '', '', 1, 0, 0),
(21, '>>> Regenerating', '', '', 1, 0, 0),
(22, '>>> Installing', '', '', 1, 0, 0),
(23, '>>> Test phase', '', '', 1, 0, 0),
(24, '^ \\* Running', '', '', 1, 0, 0),
(25, '>>> Install', '', '', 1, 0, 0),
(26, '>>> Completed installing', '', '', 1, 0, 0),
(27, '^ \\* ERROR:', '^ \\* S:', '^ \\* (?!S:)', 5, 0, 0),
(28, ' Error 1', '', '', 5, 2, 1),
(29, 'undefined reference to', '', '', 5, 0, 0),
(30, '^ \\* Generating', '', '', 1, 0, 0),
(31, ': fatal error:', '', '', 5, 0, 0),
(32, '^ \\* Done', '', '', 2, 0, 0),
(33, '.patch ...$', '', '', 2, 0, 0),
(35, '^ \\* Disabling', '', '', 2, 0, 0),
(37, '^ \\* abi_x86_', '', '', 2, 0, 0),
(38, '^ \\* >>> SetUID:', '', '', 1, 0, 0),
(39, '^ \\* >>> SetGID:', '', '', 1, 0, 0),
(40, 'CMake Error', '', '', 5, 0, 1),
(41, 'No such file or directory$', '', '', 5, 0, 0),
(43, '^ \\* Updating', '', '', 1, 0, 0),
(44, '^strip:', '', '', 1, 0, 0),
(45, '^ \\* checking', '', '', 1, 0, 0),
(46, 'files checked ...$', '', '', 1, 0, 0),
(49, '^ \\* Installing', '', '', 1, 0, 0),
(48, '^SyntaxError: invalid syntax', '', '', 5, 3, 0),
(50, '^ \\* Skipping make', '', '', 1, 0, 0),
(51, 'command not found$', '', '', 5, 0, 0);

--
-- Dumping data for table `hilight_css`
--

INSERT INTO `hilight_css` (`hilight_css_id`, `hilight_css_name`, `hilight_css_collor`) VALUES
(1, 'info1', '#7FFF00'),
(2, 'info2', 'Green'),
(3, 'qa1', 'Yellow'),
(5, 'fail1', 'Red');

--
-- Dumping data for table `jobs`
--

INSERT INTO `jobs` (`job_id`, `job_type`, `status`, `user`, `config_id`, `run_config_id`, `time_stamp`) VALUES
(1, 'updatedb', 'Done', 'cron', 1, 1, '2016-01-27 17:54:38'),
(3, 'esync', 'Done', 'cron', 1, 1, '2016-02-13 14:35:58');

--
-- Dumping data for table `setups`
--

INSERT INTO `setups` (`setup_id`, `setup`, `profile`) VALUES
(1, 'base', 'base'),
(2, 'amd64_hardened_unstable', 'hardened/linux/amd64'),
(3, 'amd64_default_unstable', 'default/linux/amd64/13.0');

--
-- Dumping data for table `tbc_config`
--

INSERT INTO `tbc_config` (`id`, `webinker`, `webbug`) VALUES
(1, '77.110.8.76', 'bugs.gentoo.org');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
