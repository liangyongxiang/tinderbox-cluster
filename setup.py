import os

try:
	from setuptools import setup
except ImportError:
	raise
	from ez_setup import use_setuptools
	use_setuptools()
	from setuptools import setup

def find_packages():
	for dirpath, dirnames, filenames in os.walk('pym'):
		if '__init__.py' in filenames:
			yield os.path.relpath(dirpath, 'pym')

setup(
	version = os.path.split(os.path.abspath(__file__))[-2].split('-')[-1],
	packages = list(find_packages()),
	package_dir = {'': 'pym'},
	name="tbc",
	author='Zorry',
	author_email='tinderbox-cluster@gentoo.org',
	url='https://anongit.gentoo.org/git/proj/tinderbox-cluster.git',
	description='Tinderbox cluster',
	platforms=["any"],
	license="GPL2",
)
