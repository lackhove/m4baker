#!/usr/bin/env python

from distutils.core import setup

from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None
setup(name = 'm4baker',
        version = '0.1.90',
        description = 'Bake full-featured m4b-audiobooks',
        author = 'Kilian Lackhove',
        author_email = '0crabman@gmail.com',
        url='http://code.google.com/p/m4baker/',
        classifiers = [
              'Programming Language :: Python :: 2',
           ],
        packages = ['m4baker',],
        package_dir = {'m4baker': 'm4baker',},
        scripts = ['scripts/m4baker'],
        data_files = [('/usr/share/applications', ['m4baker.desktop']),
                        ('/usr/share/pixmaps',  ['m4baker.png'])]
        )
