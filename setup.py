import os

try:
	from setuptools import setup
except ImportError:
	raise
	from ez_setup import use_setuptools
	use_setuptools()
	from setuptools import setup

version = os.path.split(os.path.abspath(__file__))[-2].split('-')[-1]

packages = ['btc']

package_dir = {'btc': 'btc/pym'}

setup(
	name="btc",
	version=version,
	author='Zorry',
	author_email='tinderbox-cluster@gentoo.org',
	url='https://anongit.gentoo.org/git/proj/tinderbox-cluster.git',
	description='Tinderbox cluster',
	platforms=["any"],
	license="GPL2",
	packages=packages,
	package_dir=package_dir,
)