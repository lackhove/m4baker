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
"""
Module implementing splitDialog.
"""

from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignature

from Ui_splitDialog import Ui_splitDialog

class splitDialog(QDialog, Ui_splitDialog):
    """
    Class documentation goes here.
    """
    def __init__(self,  minSplitDuration,  parent = None,):
        """
        Constructor, minSplitDuration is a QTime
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.splitTimeEdit.setTime(minSplitDuration)
        self.splitTimeEdit.setMinimumTime(minSplitDuration)

    def getMaxSplitDuration(self):
        maxSplitDuration = (self.splitTimeEdit.time().hour()*60 + self.splitTimeEdit.time().minute())*60+ self.splitTimeEdit.time().second()
        return maxSplitDuration
