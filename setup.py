from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in bezzie/__init__.py
from bezzie import __version__ as version

setup(
	name="bezzie",
	version=version,
	description="A Frappe app to integarte Bezzie e-commerce mobile application with ERPNext",
	author="D-codE",
	author_email="mailtodecode@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
