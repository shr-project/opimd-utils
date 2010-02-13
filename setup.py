# -*- coding: utf-8 -*-
import sys
import os

from ez_setup import use_setuptools
use_setuptools('0.6c3')

from setuptools import setup, find_packages, Extension
from distutils.sysconfig import get_python_inc
from glob import glob
import commands


dist = setup( name='opimd-utils',
    version='0.0.3',
    author='dos',
    author_email='seba.dos1@gmail.com',
    description='Test scripts for freesmartphone.org opimd interface',
    url='http://freesmartphone.org/',
    download_url='http://git.shr-project.org/git/?p=opimd-utils.git',
    license='GNU GPL',
    packages=['opimd_utils'],
    scripts=['opimd-cli', 'opimd-notifier', 'opimd-messages', 'opimd-resolve', 'opimd-config', 'opimd-contacts', 'opimd-notes', 'opimd-dates'],
    data_files=[('applications', ['data/opimd-messages.desktop', 'data/opimd-contacts.desktop', 'data/opimd-notes.desktop', 'data/opimd-dates.desktop']),
		('pixmaps', ['data/opimd-notes.png', 'data/opimd-dates.png']),
		('pixmaps/opimd-utils', glob("data/icons/*.png")),
		('locale/de/LC_MESSAGES', ['data/po/de/opimd-dates.mo','data/po/de/opimd-contacts.mo','data/po/de/opimd-notifier.mo','data/po/de/opimd-notes.mo','data/po/de/opimd-messages.mo']),
		('locale/fr/LC_MESSAGES', ['data/po/fr/opimd-contacts.mo', 'data/po/fr/opimd-dates.mo', 'data/po/fr/opimd-messages.mo', 'data/po/fr/opimd-notes.mo', 'data/po/fr/opimd-notifier.mo']),
		('locale/ru/LC_MESSAGES', ['data/po/ru/opimd-contacts.mo', 'data/po/ru/opimd-dates.mo']),
		('locale/gl/LC_MESSAGES', ['data/po/gl/opimd-dates.mo','data/po/gl/opimd-contacts.mo','data/po/gl/opimd-notifier.mo','data/po/gl/opimd-notes.mo','data/po/gl/opimd-messages.mo']),
		('locale/es/LC_MESSAGES', ['data/po/es/opimd-dates.mo','data/po/es/opimd-contacts.mo','data/po/es/opimd-notifier.mo','data/po/es/opimd-notes.mo','data/po/es/opimd-messages.mo']),
		('locale/eo/LC_MESSAGES', ['data/po/eo/opimd-dates.mo','data/po/eo/opimd-contacts.mo','data/po/eo/opimd-notifier.mo','data/po/eo/opimd-notes.mo','data/po/eo/opimd-messages.mo']),
		('locale/gr/LC_MESSAGES', ['data/po/gr/opimd-dates.mo','data/po/gr/opimd-contacts.mo','data/po/gr/opimd-notifier.mo','data/po/gr/opimd-notes.mo','data/po/gr/opimd-messages.mo']),
		('../../etc/X11/Xsession.d', ['data/89opimd-notifier'])
  ]
)

installCmd = dist.get_command_obj(command="install_data")
installdir = installCmd.install_dir
installroot = installCmd.root

if not installroot:
    installroot = ""

if installdir:
    installdir = os.path.join(os.path.sep,
        installdir.replace(installroot, ""))
