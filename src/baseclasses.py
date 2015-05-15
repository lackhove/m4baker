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

'''the classes shared by the CLI and the GUI interface'''

import os, re,  codecs
from PyQt4.QtGui import *
from PyQt4.QtCore import *

version = QString('0.1.91')
TITLE, CHAPTER, TRACK, DURATION, STARTTIME, FILENAME,  ENDTIME = range(7)
VERBOSE = False


def secConverter(seconds):
    '''converts 'seconds' from 'SS.ms' to 'HH:MM:SS.ms' format'''
    hours, remain = divmod(seconds, 3600)
    minutes, seconds = divmod(remain, 60)
    return (hours,  minutes,  seconds)

def findSupportedInputFiles():
    '''gets the supported input files from sox help'''
    soxProc = QProcess()
    soxProc.start('sox',  ['-h',])
    if soxProc.waitForFinished():
        soxHelp = str(soxProc.readAllStandardOutput())
        soxProc.deleteLater()
    filetypes = re.search(r'AUDIO FILE FORMATS:(.*)',  soxHelp).groups(0)
    filetypes = filetypes[0].split()
    return ['.'+ unicode(element) for element in filetypes]

supportedInputFiles = findSupportedInputFiles()


def verboseOutput(standardOutput, errorOutput,  name):
    if not VERBOSE:
        return
    standardOutput = standardOutput.strip()
    errorOutput = errorOutput.strip()
    if standardOutput:
        print name.decode('utf-8') + ': ' + standardOutput.decode('utf-8')
    if errorOutput:
        print 'ERROR: ' + name.decode('utf-8') + ': ' + errorOutput.decode('utf-8')


class chapter:
    '''This class represents one chapter of an audiobook    '''

    def __init__(self,  filename = QString(),  audiobook = QString()):
        '''init the chapter with standard minimum data'''

        if not filename.isEmpty():
            self.setFile(filename)
            return
        self.audiobook = audiobook
        self.duration = 0
        self.title = QString('unknown chapter title')
        self.trackNumber = 0
        self.startTime = 0


    def setFile(self, filename):
        '''associate chapter with a file'''
        self.filename = filename

        #get fileinfo using soxi
        #FIXME: soxi seems to have problems with files conatining more than one dot
        soxiProc = QProcess()
        soxiProc.start('soxi',  [self.filename,])
        if soxiProc.waitForFinished():
            # some weird encoding magic to deal with special characters
            soxioutput = str(soxiProc.readAllStandardOutput()).decode('utf-8')
            self.__soxioutput = soxioutput
            soxiProc.deleteLater()


        #calculate duration in seconds
        regexp = QRegExp(r'''(\d\d):(\d\d):(\d\d.\d\d)''')
        regexp.indexIn(self.__soxioutput)
        (hours, minutes,  seconds) = (regexp.cap(1).toFloat()[0],  regexp.cap(2).toFloat()[0],  regexp.cap(3).toFloat()[0])
        self.duration = float(seconds) + 60.0*float(minutes) + 60*60.0*float(hours)

        #get title from soxi
        regexp = QRegExp(r"""Title=(.*)\n""")
        regexp.setMinimal(1)
        pos = regexp.indexIn(self.__soxioutput)
        if pos >= 0:
            self.title = regexp.cap(1)
        else:
        #if self.title.size() == 0:
            # guess the title if it wasn t found in metadata
            self.title = filename.section(os.sep,-1,-1).section('.',0,-2)

        #get tracknumber from soxi
        regexp = QRegExp(r"""Tracknumber=(.*)\n""")
        regexp.setMinimal(1)
        pos = regexp.indexIn(self.__soxioutput)
        if pos >= 0:
            (self.trackNumber,  OK) = regexp.cap(1).toInt()
        else:
        #if not OK:
            # get tracknumber from filename
            basename = filename.section(os.sep,-1,-1).section('.',0,0)
            regexp = QRegExp(r"""(\d+)""")
            pos = regexp.indexIn(basename)
            if pos >= 0:
                (self.trackNumber,  OK) = regexp.cap(1).toInt()
            else:
            #if not OK:
                self.trackNumber = 0

        #set peliminary value for the startTime
        self.startTime = self.duration


    def getBookdata(self):
        '''get books metadata from chapterfile'''
        regexp = QRegExp(r"""Album=(.*)\n""")
        regexp.setMinimal(1)
        pos = regexp.indexIn(self.__soxioutput)
        if pos >= 0:
            bookTitle = regexp.cap(1)
        else:
            bookTitle = self.title

        regexp = QRegExp(r"""Artist=(.*)\n""")
        regexp.setMinimal(1)
        pos = regexp.indexIn(self.__soxioutput)
        if pos >= 0:
            author = regexp.cap(1)
        else:
            author  = 'Unknown Author'

        regexp = QRegExp(r"""Year=(.*)\n""")
        regexp.setMinimal(1)
        pos = regexp.indexIn(self.__soxioutput)
        if pos >= 0:
            year = regexp.cap(1)
        else:
            year  = '0000'

        return (bookTitle,  author,   year)


class audiobook:

    def __init__(self,  chapters,  sortBy = 'filename'):
        '''init audiobook from given chapters, sort them and calculate chapters start times'''

        self.chapters = []
        for element in chapters:
            self.addChap(element)

        self.sort(sortBy)

        #get book metadata from first chapter file
        (self.title,  self.author,  self.year) = chapters[0].getBookdata()

        #set preliminary value for outfileName and encodestring
        self.outfileName = self.author + ' - ' + self.title + QString('.m4b')
        self.encodeString =QString('faac -o <output_file>' )

        self.progress = 0

    def sort(self,  sortBy = 'filename'):
        '''sort chapters of audiobook and calculate chapters starttime'''

        if sortBy == 'filename':
            self.chapters = sorted(self.chapters, key=lambda k: k.filename)

        if sortBy == 'trackNumber':
            self.chapters = sorted(self.chapters, key=lambda k: k.trackNumber)

        self.update()

    def update(self):
        '''update audiobook. things like total time calculation go here'''
        position = 0
        for i in range(0, len(self.chapters)):
            self.chapters[i].startTime = position
            position = position + self.chapters[i].duration

    def addChap(self,  chapter,  number=None):
        '''add a single chapter to the audiobook'''
        chapter.audiobook = self
        if number==None:
            self.chapters.append(chapter)
        else:
            self.chapters[number:number] = [chapter,  ]

        self.update()

    def remChaps(self, indexList):
        '''remove a list of chapters,  specified by a list of chapter indexes from the audiobook'''
        newChapters = list()
        for i in range(0,  len(self.chapters)):
            if i not in indexList:
                newChapters.append(self.chapters[i])
        self.chapters = newChapters

        self.update()

    def encode(self):
        '''encode the entire book to one file'''
        soxcommand = [u'sox',  ]
        for i in range(0, len(self.chapters)):
            soxcommand.append(self.chapters[i].filename)
        soxcommand += [u'-t',  u'.wav',  u'-']

        faaccommand = QString(self.encodeString)
        faaccommand = faaccommand.trimmed()
        #faaccommand needs to be a QString for the regex below
        faaccommand = faaccommand.split(' ')
        #we do this after splitting the string to avoid splitting the filename
        faaccommand = [element.replace(QString('<output_file>'),
                                       self.outfileName) for element in faaccommand]
        faaccommand.append(u'-')

        self.soxProc = QProcess()
        self.faacProc = QProcess()
        self.soxProc.setStandardOutputProcess(self.faacProc)

        #when faac has output to read it will emit the signal "readyReadStandardError():
        # for the gui use:
        #self.connect(self.faacProc, SIGNAL("readyReadStandardError()"), self.readOutput)
        #and     def readOutput(self):  print self.faacProc.readAllStandardError()

        self.soxProc.start(soxcommand[0],  soxcommand[1:])
        self.faacProc.start(faaccommand[0],  faaccommand[1:])


    def tagChapters(self):
        '''create a chapterfile for mp4chaps and make it write the chapters to the outfileName , remove chapterfile'''

        #trim the file extension
        trimmedOutfileName = self.outfileName.section('.',0,-2)
        chapfileName = trimmedOutfileName + QString('.chapters.txt')
        #we need codecs.open because this file can contain non ascii characters
        chapfile = codecs.open(unicode(chapfileName),  encoding='utf-8',  mode='w')
        for element in self.chapters:
            hours,  minutes,  seconds = secConverter(element.startTime)
            chapfile.write('%.2d:%.2d:%#06.3f %s - %s\n' % (hours, minutes,
                                                            seconds, self.chapters.index(element)+1, element.title))
        chapfile.close()

        taggerProc = QProcess()
        taggerProc.start('mp4chaps',  ['-i',  self.outfileName])
        if taggerProc.waitForFinished():
            verboseOutput(str(taggerProc.readAllStandardOutput()), str(taggerProc.readAllStandardError()),
                                                                                                        'MP4CHAPS')
            taggerProc.deleteLater()

        if not VERBOSE:
            os.remove(chapfile.name)
            #clean up only when we are not in verbose mode,
            #otherwise the file might be helpful

    def tagMeta(self):
        '''add tags from audiobokk to final outfileName'''
        taggerProc = QProcess()
        taggerProc.start('mp4tags',  ['-A',  self.title,  '-a',  self.author,  '-g',  'Audiobook',  '-s',
                    self.title,  '-y',  self.year,  self.outfileName])
        if taggerProc.waitForFinished():
            verboseOutput(str(taggerProc.readAllStandardOutput()), str(taggerProc.readAllStandardError()),  'MP4TAGS')
            taggerProc.deleteLater()


        if hasattr(self,  u'cover'):
            #a coverfile was specified
            pixmap = self.cover
            #rescale the cover so the ipod can handle it
            pixmap = pixmap.scaledToHeight(480)
            pixmap.save(self.outfileName + u'.png')
            taggerProc = QProcess()
            taggerProc.start(u'mp4art',  [u'--add',  self.outfileName + u'.png',  self.outfileName])
            if taggerProc.waitForFinished():
                verboseOutput(str(taggerProc.readAllStandardOutput()), str(taggerProc.readAllStandardError()),  u'MP4ART')
                taggerProc.deleteLater()
            if not VERBOSE:
                #same as above, file might be helpful in verbose mode
                os.remove(unicode(self.outfileName) + u'.png')


    def getMinSplitDuration(self):
        '''determine the minimal audiobook ength after split, depending on the longest chapter'''
        minSplitDuration = 0
        for chapter in self.chapters:
            if chapter.duration >= minSplitDuration:
                minSplitDuration = chapter.duration
        return minSplitDuration


class audiobookContainer(list):

    percentageChanged = pyqtSignal(int,  int)

    def split(self,  booknum,  maxDuration):
        '''splits audiobook booknum into pieces of the duration maxDuration'''

        from copy import deepcopy

        worklist = [deepcopy(self[booknum]),  ]
        sumDuration = 0
        splitNumber = 2

        for i in range(0,  len(self[booknum].chapters)):
            sumDuration += self[booknum].chapters[i].duration
            if sumDuration >= maxDuration:
                #is longer, book needs to be split chapter i
                #copy the audiobook to the worklist
                worklist.append(deepcopy(self[booknum]))
                worklist[-1].title += str(splitNumber)
                worklist[-1].outfileName = worklist[-1].outfileName[0:-4]+ str(splitNumber) + '.m4b'

                #trim last chapters
                worklist[-2].remChaps(range(len(worklist[-2].chapters) -
                                    (len(self[booknum].chapters) - i ),  len(worklist[-2].chapters)))
                #trim first chapters
                worklist[-1].remChaps(range(0,  i))

                sumDuration = self[booknum].chapters[i].duration
                splitNumber += 1

        self.pop(booknum)
        self[booknum:booknum] = worklist


class audiobookTreeModel(QAbstractItemModel):

    processingDone = pyqtSignal()

    def __init__(self, parent=None):

        self.audiobookList = audiobookContainer()
        QAbstractItemModel.__init__(self, parent)

        self.processBooknum = 0


    def columnCount(self, parent):
        return 6


    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            #parent points to root
            return len(self.audiobookList)
        elif not parent.parent().isValid():
            # parent points to a audiobook
            booknum = parent.row()
            return len(self.audiobookList[booknum].chapters)
        else:
            #parent points to a chapter
            return 0


    def data(self, index, role):

        if role == Qt.DisplayRole:

            column = index.column()

            if index.parent().isValid():
                # index points to a chapter
                booknum = index.parent().row()
                chapnum = index.row()

                chapter = self.audiobookList[booknum].chapters[chapnum]

                if column == TITLE:
                    return QVariant(chapter.title)
                if column == CHAPTER:
                    return QVariant(u'%.2d' % (chapnum+1))
                if column == TRACK:
                    return QVariant(u'%.2d' % chapter.trackNumber)
                if column == DURATION:
                    duration = u'%.2d:%.2d:%#06.3f' % secConverter(chapter.duration)
                    return QVariant(duration)
                if column == STARTTIME:
                    startTime = u'%.2d:%.2d:%#06.3f' % secConverter(chapter.startTime)
                    return QVariant(startTime)
                if column == FILENAME:
                    filename = chapter.filename
                    return QVariant(filename)
                if column == ENDTIME:
                    endTime = u'%.2d:%.2d:%#06.3f' % secConverter(chapter.duration + chapter.startTime)
                    return QVariant(endTime)
            else:
                #index points to a audiobook
                booknum = index.row()
                audiobook = self.audiobookList[booknum]
                if column == TITLE:
                    return QVariant(audiobook.title)
                if column == FILENAME:
                    filename = audiobook.outfileName
                    return QVariant(filename)
                if column == CHAPTER:
                    return QVariant(audiobook.progress)

        elif role == Qt.UserRole:

            if index.parent().isValid():
                #index points to a chapter
                booknum = index.parent().row()
                chapnum = index.row()
                chapter = self.audiobookList[booknum].chapters[chapnum]
                #we must return a dict here because we need to return more values than columns
                value = {'title': chapter.title,  'chapnum': chapnum, 'trackNumber':chapter.trackNumber,
                        'duration':chapter.duration,  'startTime':chapter.startTime,  'filename':chapter.filename,
                        'endTime':(chapter.startTime + chapter.duration)}
                return value

            else:
                #audiobook
                booknum = index.row()
                audiobook = self.audiobookList[booknum]

                value = {'title':audiobook.title, 'booknum':booknum, 'author':audiobook.author,
                        'encodeString':audiobook.encodeString,  'outfileName':audiobook.outfileName,
                        'year':audiobook.year,  'minSplitDuration':audiobook.getMinSplitDuration()}
                #TODO: store minsplitduration in audiobook and calculate it only on update() so it isnt recalculated al the time

                if hasattr(audiobook,  'faacProc'):
                    value['faacProc'] = audiobook.faacProc

                if hasattr(audiobook,  'cover'):
                    value['cover']= audiobook.cover

                return value

        return QVariant()


    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == TITLE:
                return QVariant("Audiobook / Chapter")
            if section == CHAPTER:
                return QVariant("Chapter #")
            if section == TRACK:
                return QVariant("Track #")
            if section == DURATION:
                return QVariant("Duration")
            if section == STARTTIME:
                return QVariant("Start Time")
            if section == FILENAME:
                return QVariant("Filename")
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            column = index.column()
            if index.parent().isValid():
                # for chapters
                booknum = index.parent().row()
                chapnum = index.row()
                chapter = self.audiobookList[booknum].chapters[chapnum]

                if column == TITLE:
                    chapter.title = value.toString()
                if column == FILENAME:
                    chapter.filename = value.toString()
            else:
                #for audiobooks
                booknum = index.row()
                audiobook = self.audiobookList[booknum]
                if column == TITLE:
                    audiobook.title = value.toString()
                if column == FILENAME:
                    audiobook.outfileName = value.toString()
                if column == CHAPTER:
                    audiobook.progress,  ok = value.toInt()

        elif role == Qt.UserRole:
            column = index.column()
            if index.parent().isValid():
                #chapter (currently, there is nothing not captured by the columns we need to save in a chapter)
                pass
            else:
                #audiobook, value is a dict
                if value.get('cover'):
                    self.audiobookList[index.row()].cover = value['cover']
                if value.get('author'):
                    self.audiobookList[index.row()].author = value['author'].toString()
                if value.get('year'):
                    self.audiobookList[index.row()].year = value['year'].toString()
                if value.get('encodeString'):
                    self.audiobookList[index.row()].encodeString= value['encodeString'].toString()


        self.dirty = True
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
        return True


    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def index(self, row, column, parent):
        '''int, int, QModelIndex'''
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QModelIndex()

        if not parent.isValid():
            #audiobook, parent is root
            booknum = row
            return self.createIndex(row,  column,  self.audiobookList[booknum])
        else:
            #chapter, parent is a audiobook
            booknum = parent.row()
            chapnum = row
            return self.createIndex(row,  column,  self.audiobookList[booknum].chapters[chapnum])

        return QModelIndex()


    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        if hasattr(childItem,  'chapters'):
            #is a audiobook
            return QModelIndex()
        else:
            #is a chapter
            booknum = self.audiobookList.index(childItem.audiobook)
            return self.createIndex(booknum,  0,  self.audiobookList[booknum])


    def addAudiobooks(self,  newbook,  current):

        parent = QModelIndex()

        booknum = self.rowCount(parent)

        self.beginInsertRows(parent,  booknum,   booknum)
        self.audiobookList.append(newbook)
        self.endInsertRows()

        self.emit(SIGNAL('expand(QModelIndex)'),  self.index(booknum ,  0,  parent))

        return True


    def addChapters(self,  chaplist,  current):

        if current.parent().isValid():
            # current is a audiobook
            current = current.parent()

        booknum = current.row()
        chapnum = self.rowCount(current.parent())

        self.beginInsertRows(current.parent(),  chapnum,   chapnum + len(chaplist))
        for element in chaplist:
            self.audiobookList[booknum ].addChap(element)
        self.endInsertRows()

        self.emit(SIGNAL('expand(QModelIndex)'),  current)

        return True

    def remove(self,  indexes):

        audiobookIndexes = []
        chapterIndexes = []

        #find audiobooks in indexes
        for index in indexes:
            if not index.parent().isValid():
                #audiobook
                audiobookIndexes.append(index)

        #list chapters that are not already presented by a audiobook in audiobookIndexes
        for index in indexes:
            if (not index.parent() in audiobookIndexes) and (not index in audiobookIndexes):
                chapterIndexes.append(index)

        #remove audiobooks
        if len(audiobookIndexes) != 0:
            first = audiobookIndexes[0].row()
            last = audiobookIndexes[-1].row()
            self.beginRemoveRows(QModelIndex(),  first ,  last)
            for i in range(first, last+1):
                self.audiobookList.pop(first)
            self.endRemoveRows()

        #remove chapters
        #if there are single chapters they can only be from the same audiobook, this is ensured by the gui
        if len(chapterIndexes) !=0:
            first = chapterIndexes[0].row()
            last = chapterIndexes[-1].row()
            parent = chapterIndexes[0].parent()
            self.beginRemoveRows(parent,  first,  last)
            self.audiobookList[parent.row()].remChaps(range(first,  last+1))
            self.endRemoveRows()

    def move(self,  indexes,  direction):
        '''this method moves only the given chapters up and doesnt touch
        audiobooks as this would not make sense'''

        #strip audiobooks from indexes
        chapterIndexes = []
        for index in indexes:
            if index.parent().isValid():
                #index points to a chapter
                chapterIndexes.append(index)
        indexes = chapterIndexes

        #extract chapnums
        sortedChapnums = {}
        for index in indexes:
            booknum = index.parent().row()
            chapnum = index.row()
            if sortedChapnums.get(booknum) == None:
                # the audiobook hast been added yet
                sortedChapnums[booknum] = [chapnum,  ]
            else:
                sortedChapnums[booknum].append(chapnum)

        if direction == 'up':
            #move chapters up
            for booknum in sortedChapnums.iterkeys():
                if 0 in sortedChapnums[booknum]:
                    # the first chapter will be moved up
                    oldParent = indexes[0].parent()
                    newParent = self.index(booknum -1,  0, oldParent.parent())
                    self.beginMoveRows(oldParent,  indexes[0].row(),  indexes[0].row(),
                                       newParent,   self.rowCount(newParent))
                    self.emit(SIGNAL('expand(QModelIndex)'), newParent )

                    tempchap = self.audiobookList[booknum].chapters.pop(0)
                    self.audiobookList[booknum -1].addChap(tempchap)
                else:
                    self.beginMoveRows(indexes[0].parent(),  indexes[0].row(),  indexes[-1].row(),
                                        indexes[0].parent(),  indexes[0].row()-1)

                    for chapnum in sortedChapnums[booknum]:
                        self.audiobookList[booknum].chapters[chapnum - 1: chapnum - 1] = \
                                    [self.audiobookList[booknum].chapters.pop(chapnum), ]

        if direction == 'down':
            #move chapters down
            for booknum in sortedChapnums.iterkeys():
                lastchap = (len(self.audiobookList[booknum].chapters)-1)
                if lastchap in sortedChapnums[booknum]:
                    # the last chapter will be moved down
                    oldParent = indexes[-1].parent()
                    newParent = self.index(booknum +1,  0, oldParent.parent())
                    self.beginMoveRows(oldParent,  indexes[-1].row(),  indexes[-1].row(),
                                       newParent,   0)
                    self.emit(SIGNAL('expand(QModelIndex)'), newParent)

                    tempchap = self.audiobookList[booknum].chapters.pop(lastchap)
                    self.audiobookList[booknum +1].addChap(tempchap,  0)
                else:
                    self.beginMoveRows(indexes[0].parent(),  indexes[0].row(),  indexes[-1].row(),
                                        indexes[0].parent(),  indexes[-1].row() +2)

                    #the list has to be reversed because it changes everytime pop is used
                    sortedChapnums[booknum].reverse()
                    for chapnum in sortedChapnums[booknum]:
                        self.audiobookList[booknum].chapters[chapnum + 1: chapnum + 1] = \
                                    [self.audiobookList[booknum].chapters.pop(chapnum), ]

        self.endMoveRows()


    def sort(self, parent,  sortBy = 'filename'):
        '''sort the selected audiobook'''

        if not parent.parent().isValid():
            #parent is a audiobook
            pass
        else:
            #parent ia a chapter
            parent = parent.parent()

        booknum = parent.row()
        self.audiobookList[booknum].sort(sortBy)
        self.emit(SIGNAL('layoutChanged()'))
        return True


    def split(self,  index,  maxSplitDuration):

        if not index.parent().isValid():
            #audiobook
            pass
        else:
            #chapter
            index = index.parent()
        booknum = index.row()
        self.beginResetModel()
        self.audiobookList.split(booknum,  maxSplitDuration)
        self.endResetModel()


    def process(self):
        #code for skipping empty audiobooks
        if len(self.audiobookList[self.processBooknum].chapters) == 0:
            i = self.processBooknum +1
            if len(self.audiobookList) == i:
                self.emit(SIGNAL('processingDone()'))
                return
            else:
                self.processBooknum += 1
                self.process()
                return

        self.audiobookList[self.processBooknum].encode()
        self.connect(self.audiobookList[self.processBooknum].faacProc,
                     SIGNAL("readyReadStandardError()"), self.__updateProgress)
        self.connect(self.audiobookList[self.processBooknum].faacProc,
                     SIGNAL("finished(int)"),  self.__encFinished)


    def __updateProgress(self):
        errorString = str(self.audiobookList[self.processBooknum].soxProc.readAllStandardError())
        standardString = str(self.audiobookList[self.processBooknum].soxProc.readAllStandardOutput())
        verboseOutput(standardString,  errorString,  'SOX')

        errorString = str(self.audiobookList[self.processBooknum].faacProc.readAllStandardError())
        standardString = str(self.audiobookList[self.processBooknum].faacProc.readAllStandardOutput())
        #faac writes everything to Error, so we use the error output as a standard output
        verboseOutput(errorString,  standardString,  'FAAC')
        try:
            percent = int(re.search('\(.*?(\d*?)\%\)', errorString).group(1))
        except:
            return
        self.setData(self.index(self.processBooknum,  1,  QModelIndex()),  QVariant(percent))


    def __encFinished(self,  exitCode):
        self.audiobookList[self.processBooknum].tagChapters()
        self.audiobookList[self.processBooknum].tagMeta()
        self.disconnect(self.audiobookList[self.processBooknum].faacProc, SIGNAL("readyReadStandardError()"), self.__updateProgress)
        self.disconnect(self.audiobookList[self.processBooknum].faacProc,  SIGNAL("finished(int)"),  self.__encFinished)
        self.audiobookList[self.processBooknum].faacProc.deleteLater()
        self.audiobookList[self.processBooknum].soxProc.deleteLater()

        self.setData(self.index(self.processBooknum,  1,  QModelIndex()),  QVariant(100))

        if self.processBooknum != len(self.audiobookList) -1:
            #check if there are more books to process
            self.processBooknum += 1
            self.process()
        else:
            self.emit(SIGNAL('processingDone()'))


class progressBarDelegate(QItemDelegate):

    def sizeHint(self, option, index):
        return QSize(120, 16)

    def paint(self, painter, option, index):
        if index.parent().isValid():
            #chapter
            QItemDelegate.paint(self, painter, option, index)
        else:
            options = QStyleOptionProgressBarV2()
            options.rect = option.rect
            options.minimum = 1
            options.maximum = 100
            options.textVisible = True
            percent, ok = index.model().data(index, Qt.DisplayRole).toInt()
            if not ok:
                percent = 0
            if percent ==0:
                return
            else:
                options.progress = percent
                options.text = QString('%d%%'%percent)
                QApplication.style().drawControl(QStyle.CE_ProgressBar, options, painter)
