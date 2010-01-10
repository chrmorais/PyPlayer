#!/usr/bin/python2.6

# encoding: utf-8
"""
database.py

"""

import sys
import os
import unittest
import glob
import random
import sys
import urllib
import urlparse
import xml.sax.saxutils as saxutils
import io
import scanner
import sqlalchemy
import sqlalchemy.ext.declarative as dec
from xml.etree.ElementTree import parse
from xml.parsers.expat import ExpatError
decBase = dec.declarative_base()
class songfromdb(decBase):
	__tablename__ = 'library'
	ID = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	title = sqlalchemy.Column(sqlalchemy.String)
	album = sqlalchemy.Column(sqlalchemy.String)
	artist = sqlalchemy.Column(sqlalchemy.String)
	year = sqlalchemy.Column(sqlalchemy.String)
	genre = sqlalchemy.Column(sqlalchemy.String)
	location = sqlalchemy.Column(sqlalchemy.String)
	length = sqlalchemy.Column(sqlalchemy.Integer)
	
	def __init__(self, ID, title, album, artist, year, genre, location, length):
		self.ID = ID
		self.title = title
		self.album = album
		self.artist = artist
		self.year = year
		self.genre = genre
		self.location = location
		self.length = length
	
	def __str__(self):
		returnstring = 'ID: ' + str(self.ID) + ' Title: ' + self.title.encode('utf-8') + ' Album: ' + self.album.encode('utf-8')
		return returnstring

class database(object):
	def isDBThere(self):
		sess = self.sessionMaker()
		try:
			results = sess.query(songfromdb).count()
			if results < 1:
				return False
			return True
		except sqlalchemy.exc.OperationalError:
			return False
		finally:
			sess.commit()
			sess.close()
	def __init__(self, dbLocation):
		self.conn = sqlalchemy.create_engine(dbLocation)
		self.sessionMaker = sqlalchemy.orm.sessionmaker(bind=self.conn)
		self.metadata = decBase.metadata

	def __str__(self):
		sess = self.sessionMaker()
		for song in sess.query(songfromdb):
			print song

	def insertData(self, data):
		"""inserts a list of items to the database. Pass in a list of song dataz, [[title, album, artist, year, genre, location, length], [title...]]
		This function creates the database if necessary."""
		sess = self.sessionMaker()
		try:
			songID = sess.query(songfromdb).count() + 1
		except sqlalchemy.exc.OperationalError:
			songID = 1
		insertList = []
		for item in data:
			insertList.append(songfromdb(songID, item[0], item[1], item[2], item[3], item[4], item[5], item[6]))
			songID += 1
		sess.add_all(insertList)
		sess.commit()
		sess.close()
	def killAll(self):
		sess = self.sessionMaker()
		try:
			for item in sess.query(songfromdb).all():
				sess.delete(item)
		except sqlalchemy.exc.OperationalError:
			pass
		sess.commit()
		sess.close()
		print u'Destruction complete.'
	#def noOfSongs(self):
	#	sess = self.sessionMaker()
	#	sess.query()
	def lookupSongByID(self, songID):
		sess = self.sessionMaker()
	 	result = sess.query(songfromdb).filter(songfromdb.ID == int(songID)).one()
		result = {'ID':result.ID, \
		'title':unicode(result.title).encode('utf-8'), \
		'album':unicode(result.album).encode('utf-8'), \
		'artist':unicode(result.artist).encode('utf-8'), \
		'year':unicode(result.year).encode('utf-8'), \
		'genre':unicode(result.genre).encode('utf-8'), \
		'location':unicode(result.location).encode('utf-8'), \
		'length':float(result.length)}
		sess.commit()
		sess.close()
		return result
	def lookupSongByLocation(self, location):
		sess = self.sessionMaker()
		if type(location) == str:
			location = location.decode('utf-8')
		result = sess.query(songfromdb).filter(songfromdb.location == location).one()
		result = {'ID':result.ID, \
		'title':unicode(result.title).encode('utf-8'), \
		'album':unicode(result.album).encode('utf-8'), \
		'artist':unicode(result.artist).encode('utf-8'), \
		'year':unicode(result.year).encode('utf-8'), \
		'genre':unicode(result.genre).encode('utf-8'), \
		'location':unicode(result.location).encode('utf-8'), \
		'length':float(result.length)}
		sess.commit()
		sess.close()
		return result
	def getLocationByID(self, songID):
		sess = self.sessionMaker()
		result = sess.query(songfromdb).filter(songfromdb.ID == songID).one()
		returnMe =  result.location
		sess.commit()
		sess.close()
		return returnMe
	def getRandomID(self):
		sess = self.sessionMaker()
		maxID = sess.query(songfromdb).count()
		sess.commit()
		sess.close()
		ID = random.randint(1, maxID)
		return ID
	def searchForSongs(self, query):
		if not query or query == '':
			print 'Please enter search terms'
			return None
		if type(query) == str:
			query = query.decode('utf-8')
		query = query.lower()
		query = '%' + query + '%'
		sess = self.sessionMaker()
		results = sess.query(songfromdb).filter(sqlalchemy.or_(songfromdb.title.like(query), songfromdb.artist.like(query), songfromdb.album.like(query))).order_by('album').all() 
		returnMe = []
		for row in results:
			try: 
				longNess = int(row.length)
			except ValueError:
				longNess = 'Unknown'
			returnMe.append({'ID':row.ID, \
			'title':unicode(row.title).encode('utf-8'), \
			'album':unicode(row.album).encode('utf-8'), \
			'artist':unicode(row.artist).encode('utf-8'), \
			'year':unicode(row.year).encode('utf-8'), \
			'genre':unicode(row.genre).encode('utf-8'), \
			'location':unicode(row.location).encode('utf-8'), \
			'length':longNess})
		sess.commit()
		sess.close()
		return returnMe
	def pprint(self, songID):
		sess = self.sessionMaker()
		songRow = sess.query(songfromdb).filter(songfromdb.ID == songID).one()
		
		if not songRow:
			return 'Song not found.'
		else:
			returnString =  'ID: ' + str(songRow.ID).encode('utf-8') + ' | ' + \
			'Title: ' + songRow.title.encode('utf-8') + ' | ' + \
			'Album: ' + songRow.album.encode('utf-8') + ' | ' + \
			'Artist: ' + songRow.artist.encode('utf-8') + ' | ' + \
			'Length: ' + str(songRow.length).encode('utf-8')
			sess.commit()
			sess.close()
			return returnString
	def pprintByLocation(self, snglocation):
		sess = self.sessionMaker()
		if type(snglocation) == str:
			snglocation = unicode(snglocation, 'utf-8')
		songRow = sess.query(songfromdb).filter(songfromdb.location == snglocation).one()

		if not songRow:
			sess.commit()
			sess.close()
			return 'Song not found.'
		else:
			returnString =  'ID: ' + str(songRow.ID).encode('utf-8') + ' | ' + \
			'Title: ' + songRow.title.encode('utf-8') + ' | ' + \
			'Album: ' + songRow.album.encode('utf-8') + ' | ' + \
			'Artist: ' + songRow.artist.encode('utf-8') + ' | ' + \
			'Length: ' + str(songRow.length).encode('utf-8')
			sess.commit()
			sess.close()
			return returnString
	def deleteItem(self, location):
		sess = self.sessionMaker()
		result = sess.query(songfromdb).filter(songfromdb.location == location).one()
		printMe = result.title
		sess.delete(result)
		sess.commit()
		sess.close()
		return 'Deleted ' + printMe
		
	def addItemByLocation(self, location):
		sess = self.sessionMaker()
		item = scanner.song(location)
		if not item.doNotAdd:
			songID = sess.query(songfromdb).count() + 1
			insertSong = songfromdb(songID, item.meta['title'], item.meta['album'], item.meta['artist'], item.meta['date'], item.meta['genre'], item.meta['location'], item.meta['length'])
			sess.add(insertSong)
		sess.commit()
		sess.close()
		return 'Added ' + item.meta['title']
	def getListOfLocations(self):
		"""returns a list of every song location in the database. For use in database comparison"""
		sess = self.sessionMaker()
		results = sess.query(songfromdb).all()
		returnMe = []
		for item in results:
			returnMe.append(item.location)
		sess.commit()
		sess.close()
		return returnMe

class playlist(object):
	"""Internal representation of a list of songs.
	For convenience (not having to type database name for every function call), playlists are tied to a database."""
	def __init__(self, dbName, name):
		self.playlist = []
		self.db = dbName
		self.plName = name
	def pprint(self):
		"""docstring for __str__"""
		returnString = ''
		print self.plName.center(62, '=')
#		print '\n'
		for item in self.playlist:
			print self.db.pprintByLocation(item).decode('utf-8')
#			print '\n'
		
		print '=============================================================='
		return ''
	def add(self, songLoc, load=True):#CHECK IF LOCATION IS VALID - SEARCH FOR FILENAME IF NOT; OR BUST SAFELY
		if isinstance(songLoc, basestring):
			if isinstance(songLoc, unicode):
				songLoc = songLoc.encode('utf-8')
			if songLoc in self.playlist:
				print "Duplicate Entry", songLoc.split('/')[-1]
			else:
				self.playlist.append(songLoc)
				if not load:
					print 'Added ', self.db.pprintByLocation(songLoc)
					
		else:
			print "Please give me a string location!"
	def saveToDisk(self, location, directory):
		"""Saves the playlist to the chosen location in XSPF format."""
		if location.startswith('temp'):
			return "We don't save temporaries!"
		location = os.path.join(directory, location)
		xml = XmlWriter(io.open(location, 'w+b'), indentAmount='  ')

		xml.prolog()
		xml.start('playlist', { 'xmlns': 'http://xspf.org/ns/0/', 'version': '1' })
		xml.start('trackList')

		for line in self.playlist:
			if isinstance(line, unicode):
				line = line.encode('utf-8')
			url = 'file://' + urllib.pathname2url(line)
			xml.start('track')
			xml.elem('location', url)
			xml.end() # track
		xml.end() # trackList
		xml.end() # playlist
		return 'Success'
	def loadFromDisk(self, plName, pathName):
		"""loads a playlist from the harddrive"""
		location = os.path.join(pathName, plName + '.xspf')
		try:
			tree = parse(location)
		except IOError:
			return 'File not found'
		except ExpatError:
			os.remove(location)
			return 'Invalid file'
		root = tree.getroot()
		pl = self.playlist
		for item in root.getiterator('{http://xspf.org/ns/0/}location'):
			formattedPath = item.text[7:]
			formattedPath = urllib.url2pathname(formattedPath).decode('utf-8')
			self.add(formattedPath)
		return 'Load of ' + plName + ' complete'
		





class XmlWriter(object):
	def __init__(self, outStream, indentAmount='  '):
		self._out = outStream
		self._indentAmount = indentAmount
		self._stack = [ ]

	def prolog(self, encoding='UTF-8', version='1.0'):
		pi = '<?xml version="%s" encoding="%s"?>' % (version, encoding)
		self._out.write(pi + '\n')

	def start(self, name, attrs={ }):
		indent = self._getIndention()
		self._stack.append(name)
		self._out.write(indent + self._makeTag(name, attrs) + '\n')

	def end(self):
		name = self._stack.pop()
		indent = self._getIndention()
		self._out.write('%s</%s>\n' % (indent, name))

	def elem(self, name, value, attrs={ }):
		# delete attributes with an unset value
		for (k, v) in attrs.items():
			if v is None or v == '':
				del attrs[k]

		if value is None or value == '':
			if len(attrs) == 0:
				return
			self._out.write(self._getIndention())
			self._out.write(self._makeTag(name, attrs, True) + '\n')
		else:
			escValue = saxutils.escape(value or '')
			self._out.write(self._getIndention())
			self._out.write(self._makeTag(name, attrs))
			self._out.write(escValue)
			self._out.write('</%s>\n' % name)

	def _getIndention(self):
		return self._indentAmount * len(self._stack)

	def _makeTag(self, name, attrs={ }, close=False):
		ret = '<' + name

		for (k, v) in attrs.iteritems():
			if v is not None:
				v = saxutils.quoteattr(str(v))
				ret += ' %s=%s' % (k, v)

		if close:
			return ret + '/>'
		else:
			return ret + '>'

if __name__ == '__main__':
	print 'Don\'t run me! I\'m just a module file, run player.py!'