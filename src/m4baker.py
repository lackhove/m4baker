#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# M4Baker
# Copyright (C) 2010 Kilian Lackhove
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import sys
from optparse import OptionParser
from PyQt4 import QtCore, QtGui

from mainWindow import MainWindow
import baseclasses


# The following  "which()" function was taken from Stack Overflow
#http://stackoverflow.com/questions/377017
#answer by "Jay"  http://stackoverflow.com/users/20840/jay
#Thanks, Jay!
def which(program):
    import os
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def main():
    parser = OptionParser()
    parser = OptionParser(usage= 'usage: %prog [options]',
                    version = baseclasses.version)
    parser.add_option('--verbose',  action='store_true',  dest='VERBOSE',  default=False,
                      help= 'Be more verbose')
    (options, args) = parser.parse_args(sys.argv)

    app = QtGui.QApplication(sys.argv)
    ui = MainWindow()
    #check for dependencies
    for dependency in ['faac',  'sox',  'soxi',  'mp4chaps',  'mp4tags',  'mp4art']:
        if which(dependency) == None:
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setText('Missing dependency: '+dependency+
                ' is not properly installed. \nPlease read INSTALL.txt \nExiting.')
            msgBox.exec_()
            sys.exit(2)
    ui.show()
    baseclasses.VERBOSE = options.VERBOSE
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
