#!/usr/bin/python2.6

# encoding: utf-8
'''
untitled.py

Created by Mitchell Ferguson on 2009-12-11.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
'''

import sys
import os
from mutagen.id3 import ID3NoHeaderError
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3
import database

class song(object):
	'''Class that reads and contains metadata about a media file.'''
	def __init__(self, location):
		self.meta = dict()
		self.trackmetas = ['ID', 'title', 'album', 'artist', 'date', 'genre', 'length', 'description']

		if os.path.splitext(location)[1].lower() == u'.mp3':
			try:
				self.file = EasyID3(location)
				self.mp3 = MP3(location)
			except ID3NoHeaderError:
				pass
			self.fileType = 'mp3'
				
		elif os.path.splitext(location)[1].lower() == '.flac':
			self.file = FLAC(location)
			self.fileType = 'flac'
		elif os.path.splitext(location)[1].lower() == '.ogg': 
			self.file = OggVorbis(location)
			self.fileType = 'ogg'
		self.meta['location'] = location
		for item in self.trackmetas:
			self.readTag(item)
		
	def readTag(self, tagname):
		'''Reads a tab from the file loaded. Some hacks for unusual cases'''
		try:
			self.meta[tagname] = self.file[tagname][0]
		except:
			if tagname == 'name':
				self.meta[tagname] = os.path.split(location)[1]
			else:
				self.meta[tagname] = "Unknown"
		#hacks
		if self.fileType == 'ogg' or self.fileType == 'flac':
			if tagname == 'length':
				self.meta[tagname] = self.file.info.length
		elif self.fileType == 'mp3' and tagname == 'length':
			try:
				self.meta[tagname] = self.mp3.info.length
			except AttributeError:
				self.meta[tagname] = "Unknown"

			
		#print tagname, self.meta[tagname]
	def __str__(self):

		returnString = []
		for item in self.trackmetas:
			returnString.append(item)
			returnString.append(unicode(self.meta[item]))
			
		finalString = ''
		finalString.join(returnString)
		return finalString
		

class scanMachine(object):
	def __init__(self, dbName):
		self.db = dbName
	def scanForFiles(self, startDirectory, fileTypes, dontvisit=None):
		"""scans a selected directory downwards recursively for all files of a specified type.
		Arguments:
			startDirectory: Pass a unicode string of the full unescaped pathname of the directory to start scanning in.
			fileTypes: Pass a tuple or list of filetypes to allow, unicode, no period (E.g. mp3 not .mp3)
			dontvisit: Pass a tuple or list of directories to be ignored. Do not append a slash to the end of each path"""
			
		try:
			dirStack = [startDirectory]
			doNotVisit = []
			if dontvisit:
				for item in dontvisit:
					doNotVisit.append(item)
			toBeScanned = []

			while True:
				try:
					visitingNow = dirStack.pop()
					if visitingNow not in doNotVisit:
						os.chdir(visitingNow)
						doNotVisit.append(visitingNow)
						currentDir = os.listdir(os.getcwdu())
						for item in currentDir:
							if item.split('.')[-1] in fileTypes:
								toBeScanned.append(os.path.join(os.getcwdu(), item))
							elif os.path.isdir(item) and os.path.join(os.getcwdu(), item) not in doNotVisit:
								dirStack.append(os.path.join(os.getcwdu(), item))
				except IndexError:
					break
		except OSError:
			print "Start directory not found/invalid. Check your config file!"
			quit()
		return toBeScanned
	def addToDatabase(self, songList):
		'''Sends the selected songs to the database, destroying anything before it.
		Pass a list of filenames to add.'''	
		self.db.killAll()
		print 'Database primed and ready, time to parse some music!'
		self.dbInsertList = []
		for item in songList:
			songdata = song(item)
			self.dbInsertList.append((songdata.meta['title'], songdata.meta['album'], songdata.meta['artist'], songdata.meta['date'], songdata.meta['genre'], songdata.meta['location'], songdata.meta['length']))
		self.db.insertData(self.dbInsertList)
		sess = self.db.sessionMaker()
		print sess.query(database.songfromdb).count(), 'songs in the library.'
		sess.commit()

def main():
	scanr = scanMachine()
	songList = scanr.scanForFiles(startDirectory=searchPath, fileTypes=[u'mp3', u'ogg', u'flac'])
	scanr.addToDatabase(songList)
if __name__ == '__main__':
	print 'Don\'t run me! I\'m just a module file! Run player.py and type \"rescan\" to remake the db!'
#	main()

#the graveyard
#	self.trackmetas2ID3 = { 
#	'ID':'ID', 
#	'title':'TIT2', 
#	'album':'TALB', 
#	'artist':'TPE1', 
#	'date':'TDRC', 
#	'genre':'TCON', 
#	'length':'length', 
#	'description':"COMM"}
#return u'Track number: ' + codecs.encode(self.track, 'utf-8') + u'\nTrack name: ' + codecs.encode(self.name, 'utf-8') + u'\nTrack artist: ' + codecs.encode(self.artist, 'utf-8') + u'\nTrack genre: ' + codecs.encode(self.genre, 'utf-8')
#		print u'Track ID: ', self.meta['ID']
#		print u'Track Location: ', self.meta['location']
#		print u'Track number: ' + self.meta['track'] + u'\nTrack name: ' + self.meta['name'] + u'\nTrack artist: ' + self.meta['artist'] + u'\nTrack genre: ' + self.meta['genre'] + u'\nTrack Length in seconds: ' + self.meta['length']
#class library(object):
#	'''A class that maintains a list of all songs.'''
#	def __init__(self):
#		self.library = []
#	def __str__(self):
#		returnString = ''
#		for item in self.library:
#			print item
#		return ''
#	def addSpecificItem(self, trackLocation):
#		self.library.append(song(trackLocation))
#	def printNumber(self, printNo='all'):
#		'''Prints a specified number of entries, from beginning to end in current sort pattern. Defaults to a full print.
#		Don't print me! Will append None to the print, just run the function.'''
#		if printNo == 'all':
#			printNo = len(self.library)
#			print printNo
#		iterator = 0
#		while iterator < printNo:
#			try:
#				testy = self.library[iterator]
#				print 'Track number:', self.library[iterator].meta['track'] 
#				print 'Track name: ', self.library[iterator].meta['title']
#				print 'Track artist: ', self.library[iterator].meta['artist']
#				print 'Track genre: ', self.library[iterator].meta['genre']
#				iterator += 1
#			except IndexError:
#				iterator = printNo
#				return 'Premature stop.'
#				break
#			return 
#	def initalDatabaseSave(self):
#		'''Sends the current library to a database, destroying anything before it'''
#		db = database.database('/Users/ripdog/Working/PyPlayer2/songBase.sqlite')
#		db.killAll()
#		db.createDatabase()
#		for item in self.library:
#			
#			data = (item.meta['ID'], item.meta['title'], item.meta['album'], item.meta['artist'], item.meta['date'], item.meta['genre'], item.meta['location'], item.meta['length'])
#			db.insertData(data)
#			
#		print len(db.c.execute('select * from library').fetchall()), 'items in library.'
#		db.endSession()
#		db = database.database()
#		db.c.execute('select * from library').fetchall()
#		db.endSession()
#		self.library = None
#		
#	def addScannedItems(self, songs):
#		print u'Beginning scan'
#		while True:
#			try:
#				item = songs.pop()
#				self.addSpecificItem(os.path.join(os.getcwdu(), item))
#			except IndexError:
#				print u'Indexing Complete!'
#				break