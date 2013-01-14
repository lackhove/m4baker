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
Module implementing MainWindow.
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Ui_mainWindow import Ui_MainWindow

from baseclasses import *
from splitDialog import splitDialog
from aboutDialog import aboutDialog

TITLE, CHAPTER, TRACK, DURATION, STARTTIME, FILENAME,  ENDTIME = range(7)

def makeClickable(widget):

    class clickFilter(QObject):

        clicked = pyqtSignal()

        def eventFilter(self, obj, event):

            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    self.clicked.emit()
                    return True

            return False

    filter = clickFilter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        class delkeyFilter(QObject):
            delkeyPressed = pyqtSignal()

            def eventFilter(self,  obj,  event):
                if event.type() == QEvent.KeyPress:
                    if event.key() == Qt.Key_Delete:
                        self.delkeyPressed.emit()
                        return True
                return False

        class returnkeyFilter(QObject):

            def eventFilter(self,  obj,  event):
                if event.type() == QEvent.KeyPress:
                    if event.key() == Qt.Key_Return:
                        current = obj.currentIndex()
                        current = obj.indexBelow(current)
                        obj.setCurrentIndex(current)
                return False


        self.audiobookList = audiobookContainer()

        self.currentDir = os.getcwd()

        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.stackedWidget.setCurrentWidget(self.infoPage)
        makeClickable(self.coverLabel).connect(self.on_coverLabel_clicked)

        self.model = audiobookTreeModel()
        self.dataTreeView.setModel(self.model)

        self.progessDelegate = progressBarDelegate()
        self.dataTreeView.setItemDelegateForColumn(1,  self.progessDelegate)

        self.connect(self.dataTreeView.selectionModel(),
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                            self.on_dataTreeView_currentItemChanged)
        self.connect(self.model,  SIGNAL('dataChanged(QModelIndex,QModelIndex)'),  self.dataChanged)
        self.connect(self.model,  SIGNAL('expand(QModelIndex)'),  self.dataTreeView.expand)
        #trying the new style of connecting signals
        self.model.processingDone.connect(self.on_processingDone)

        self.delfilter = delkeyFilter()
        self.dataTreeView.installEventFilter(self.delfilter)
        self.connect(self.delfilter, SIGNAL('delkeyPressed()'),
                                    self.on_actionRemove_triggered)

        self.returnFilter = returnkeyFilter()
        self.dataTreeView.installEventFilter(self.returnFilter)

        #allow only numbers in yearEdit
        self.yearEdit.setValidator(QRegExpValidator(QRegExp(r'\d*'), self))

        #set icons
        self.actionMoveDown.setIcon(QIcon.fromTheme('go-down'))
        self.actionMoveUp_2.setIcon(QIcon.fromTheme('go-up'))
        #TODO: clean the name of this action
        self.actionRemove.setIcon(QIcon.fromTheme('edit-delete'))
        self.actionAddAudiobook.setIcon(QIcon.fromTheme('address-book-new'))
        self.actionAddChapter.setIcon(QIcon.fromTheme('document-new'))
        self.action_About.setIcon(QIcon.fromTheme('help-about'))
        self.action_help.setIcon(QIcon.fromTheme('help-browser'))
        self.actionExit.setIcon(QIcon.fromTheme('application-exit'))
        self.actionProcess.setIcon(QIcon.fromTheme('system-run'))
        self.chapterFileButton.setIcon(QIcon.fromTheme('document-open'))
        self.outfileButton.setIcon(QIcon.fromTheme('document-open'))

        self.updateTree()


    def okToQuit(self):
        reply = QMessageBox.question(self,"M4Baker - really quit?", \
                "Really quit?",QMessageBox.Yes|QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Yes:
            return True


    def closeEvent(self, event):
        if not self.okToQuit():
            event.ignore()


    @pyqtSignature("")
    def on_actionAddAudiobook_triggered(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()

        formats = ["*%s" % format for format in supportedInputFiles]

        fnames = QFileDialog.getOpenFileNames(
                                              self,
                                               "Choose audio files to create audiobook from",
                                               self.currentDir,
                                               'audio files (%s)' % " ".join(formats))

        if fnames:
            #fnames = [unicode(element) for element in fnames]
            self.currentDir =  fnames[-1].section(os.sep,0,-2)
            newbook = audiobook([chapter(element) for element in fnames])
            self.model.addAudiobooks(newbook,  current)

            self.updateTree()

    @pyqtSignature("")
    def on_actionMoveDown_triggered(self):
        """
        Slot documentation goes here.
        """

        indexes = self.dataTreeView.selectionModel().selectedIndexes()
        #clean indexes list from double entries
        cleanIndexes = []
        for index in indexes:
            if index.column() == 0:
                cleanIndexes.append(index)
        indexes = cleanIndexes

        self.model.move(indexes,  'down')



    @pyqtSignature("")
    def on_actionRemove_triggered(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()

        indexes = self.dataTreeView.selectionModel().selectedIndexes()
        #clean indexes list from double entries
        cleanIndexes = []
        for index in indexes:
            if index.column() == 0:
                cleanIndexes.append(index)
        indexes = cleanIndexes

        self.model.remove(indexes)
        self.updateTree()


    @pyqtSignature("")
    def on_actionAddChapter_triggered(self):
        """
        Slot documentation goes here.
        """
        formats = ["*%s" % format for format in supportedInputFiles]
        fnames = QFileDialog.getOpenFileNames(
                                              self,
                                              "Choose audio files to append to audiobook",
                                              self.currentDir,
                                              'audio files (%s)' % " ".join(formats))


        if fnames:
            self.currentDir =  fnames[-1].section(os.sep,0,-2)
            #fnames = [unicode(element) for element in fnames]
            chaplist = [chapter(element) for element in fnames]
            current = self.dataTreeView.currentIndex()
            self.model.addChapters(chaplist,  current)
            self.updateTree()
            #TODO: maybe it is smarter to add the chapter after current item?


    @pyqtSignature("")
    def on_actionSortByFilename_triggered(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()
        self.model.sort(current,  'filename')
        self.updateTree()


    @pyqtSignature("")
    def on_actionSortByTracknumber_triggered(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()
        self.model.sort(current,  'trackNumber')
        self.updateTree()


    @pyqtSignature("")
    def on_actionProcess_triggered(self):
        """
        Slot documentation goes here.
        """
        uiElements = (self.actionAddChapter,  self.actionMoveDown,
                      self.actionMoveUp_2,  self.actionProcess, self.actionRemove,  self.actionSortByFilename,
                      self.actionSortByTracknumber,  self.actionSplit,  self.actionAddAudiobook)

        for element in uiElements:
            element.setEnabled(False)
        #switch to about docker to prevent data from being changed
        self.stackedWidget.setCurrentWidget(self.infoPage)
        #disable treeview
        self.dataTreeView.setEnabled(False)

        self.model.process()


    @pyqtSignature("")
    def on_actionMoveUp_2_triggered(self):
        """
        Slot documentation goes here.
        """

        indexes = self.dataTreeView.selectionModel().selectedIndexes()
        #clean indexes list from double entries
        cleanIndexes = []
        for index in indexes:
            if index.column() == 0:
                cleanIndexes.append(index)
        indexes = cleanIndexes

        self.model.move(indexes,  'up')



    def populateChapterProperties(self):

        #current must be a chapter, otherwise this method wont be called
        current = self.dataTreeView.currentIndex()

        title = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                         Qt.DisplayRole).toString()
        startTime = self.model.data(self.model.index(current.row(),  STARTTIME,  current.parent()),
                                                                                                  Qt.DisplayRole).toString()
        duration = self.model.data(self.model.index(current.row(),  DURATION,  current.parent()),
                                                                                                Qt.DisplayRole).toString()
        filename = self.model.data(self.model.index(current.row(),  FILENAME,  current.parent()),
                                                                                                Qt.DisplayRole).toString()
        endTime= self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                          Qt.UserRole)['endTime']
        endTime = u'%.2d:%.2d:%#06.3f' % secConverter(endTime)

        self.chapterTitleEdit.setText(title)
        self.startTimeEdit.setText(startTime)
        self.durationEdit.setText(duration)
        self.chapterFileEdit.setText(filename)
        self.endTimeEdit.setText(endTime)


    def populateAudiobookProperties(self):

        current = self.dataTreeView.currentIndex()

        title = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                        Qt.UserRole)['title']
        booknum = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                          Qt.UserRole)['booknum']
        author = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                         Qt.UserRole)['author']
        encodeString = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                                Qt.UserRole)['encodeString']
        outfileName = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                               Qt.UserRole)['outfileName']
        year = self.model.data(self.model.index(current.row(),  TITLE,  current.parent()),
                                                                                         Qt.UserRole)['year']

        self.authorEdit.setText(author)
        self.titleEdit.setText(title)
        self.yearEdit.setText(year)
        self.faacEdit.setText(encodeString)
        self.outfileEdit.setText(outfileName)

        pixmap = self.model.data(self.model.index(current.row(),  0,  current.parent()),  Qt.UserRole).get('cover')
        if pixmap:
            pixmap = self.model.data(self.model.index(current.row(),  0,  current.parent()),  Qt.UserRole)['cover']
            width = self.coverLabel.size().width()
            pixmap = pixmap.scaledToWidth(width)
            self.coverLabel.setPixmap(pixmap)
        else:
            self.coverLabel.setText('(click to change)')


    @pyqtSignature("QModelIndex*, QModelIndex*")
    def on_dataTreeView_currentItemChanged(self, current, previous):
        """
        Slot documentation goes here.
        """
        uiElements = (self.actionAddChapter,  self.actionMoveDown,
                      self.actionMoveUp_2,  self.actionProcess, self.actionRemove,  self.actionSortByFilename,
                      self.actionSortByTracknumber,  self.actionSplit)


        if not current.isValid():
            #current is rootItem
            for element in uiElements:
                element.setDisabled(True)
            return
        else:
            for element in uiElements:
                element.setEnabled(True)

        if not current.parent().isValid():
            #current is audiobook
            self.stackedWidget.setCurrentWidget(self.audiobookPropertiesPage)
            self.populateAudiobookProperties()
            if current.row() == 0:
                #current is first audiobook
                self.actionMoveUp_2.setEnabled(False)
            if current.row() == self.model.rowCount(current.parent()) -1:
                #current is last audiobook
                self.actionMoveDown.setEnabled(False)
        else:
            #current is chapter
            self.stackedWidget.setCurrentWidget(self.chapterPropertiesPage)
            self.populateChapterProperties()
            if current.row() == 0:
                #current is the first chapter of its book
                if current.parent().row() == 0:
                    #current is the first chapter of the first book
                    self.actionMoveUp_2.setEnabled(False)
            if current.row() == self.model.rowCount(current.parent()) -1:
                #current is the last chapter of its book
                if current.parent().row() == self.model.rowCount(current.parent().parent()) -1:
                    #current is the last chapter of the last book
                    self.actionMoveDown.setEnabled(False)


    @pyqtSignature("")
    def on_chapterFileButton_clicked(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()

        formats = ["*%s" % format for format in supportedInputFiles]
        fname = QFileDialog.getOpenFileName(
                                            self,
                                            "change chapter source file",
                                            self.currentDir,
                                            'audio files (%s)' % " ".join(formats))


        if  not fname.isEmpty():
            self.currentDir =  fname.section(os.sep,0,-2)
            self.model.setData(self.model.index(current.row(), FILENAME,  current.parent()), QVariant(fname))
            self.populateChapterProperties()


    @pyqtSignature("")
    def on_outfileButton_clicked(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()

        fname = QFileDialog.getSaveFileName(
                                            self,
                                            'choose audiobook output file',
                                            self.currentDir,
                                            "Audiobook files (*.m4b)")
        if not fname.isEmpty():
            self.currentDir =  fname.section(os.sep,0,-2)
            if not fname.endsWith('.m4b'):
                fname += ".m4b"
            self.model.setData(self.model.index(current.row(), FILENAME,  current.parent()), QVariant(fname))
            self.populateAudiobookProperties()


    @pyqtSignature("")
    def on_action_About_triggered(self):
        dialog = aboutDialog()
        if dialog.exec_():
            pass


    @pyqtSignature("")
    def on_actionSplit_triggered(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()

        if not current.parent().isValid():
            #audiobook
            pass
        else:
            #chapter
            current = current.parent()

        minSplitDuration = self.model.data(current,  Qt.UserRole)['minSplitDuration']
        hours,  minutes,  seconds = secConverter(minSplitDuration)
        minSplitDuration = QTime(hours,  minutes,  seconds+1)

        dialog = splitDialog(minSplitDuration)
        if dialog.exec_():
            maxSplitDuration = dialog.getMaxSplitDuration()
            self.model.split(current,  maxSplitDuration)
            self.updateTree()


    @pyqtSignature("")
    def on_coverLabel_clicked(self):

        current = self.dataTreeView.currentIndex()

        fname = QFileDialog.getOpenFileName(
                                            self,
                                            "Choose a cover file",
                                            self.currentDir,
                                            "image files (*.png *.jpg *.jpeg *.bmp *.gif *.pbm *.pgm *ppm *xpm *xpm)",
                                            "cover.png"
					    )


        if  not fname.isEmpty():
            self.currentDir =  fname.section(os.sep,0,-2)
            self.model.setData(self.model.index(current.row(),  0,  current.parent()),
                                                                                    {'cover':QPixmap(fname)},  Qt.UserRole)
            self.populateAudiobookProperties()


    def updateTree(self):

        for i in range(6):
            self.dataTreeView.resizeColumnToContents(i)


    def dataChanged(self,  topLeft,  bottomRight):
        current = self.dataTreeView.currentIndex()

        if not current.parent().isValid():
            #audiobook
            self.populateAudiobookProperties()
        else:
            #chapter
            self.populateChapterProperties()


    def on_processingDone(self):
        self.actionProcess.setEnabled(True)
        self.actionAddAudiobook.setEnabled(True)
        self.dataTreeView.setEnabled(True)
        self.dataTreeView.reset()


    @pyqtSignature("")
    def on_chapterTitleEdit_editingFinished(self):
        """
        Slot documentation goes here.
        """
        current = self.dataTreeView.currentIndex()
        text = self.chapterTitleEdit.text()
        self.model.setData(self.model.index(current.row(),  TITLE,  current.parent()), QVariant(text))

    @pyqtSignature("")
    def on_faacEdit_editingFinished(self):
        """
        Slot documentation goes here.
        """
        text = self.faacEdit.text()
        current = self.dataTreeView.currentIndex()
        value = {'encodeString':QVariant(text)}
        self.model.setData(self.model.index(current.row(),  0,  QModelIndex()), value,  Qt.UserRole)

    @pyqtSignature("")
    def on_titleEdit_editingFinished(self):
        """
        Slot documentation goes here.
        """
        text = self.titleEdit.text()
        current = self.dataTreeView.currentIndex()
        self.model.setData(self.model.index(current.row(),  TITLE,  QModelIndex()), QVariant(text))

    @pyqtSignature("")
    def on_yearEdit_editingFinished(self):
        """
        Slot documentation goes here.
        """
        text = self.titleEdit.text()
        current = self.dataTreeView.currentIndex()
        self.model.setData(self.model.index(current.row(),  TITLE,  QModelIndex()), QVariant(text))

    @pyqtSignature("")
    def on_authorEdit_editingFinished(self):
        """
        Slot documentation goes here.
        """
        text = self.authorEdit.text()
        current = self.dataTreeView.currentIndex()
        value = {'author':QVariant(text)}
        self.model.setData(self.model.index(current.row(),  0,  QModelIndex()), value,  Qt.UserRole)

    @pyqtSignature("")
    def on_action_help_triggered(self):
        """
        Slot documentation goes here.
        """
        self.stackedWidget.setCurrentWidget(self.infoPage)
