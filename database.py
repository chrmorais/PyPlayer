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
		self.title = uniMe(title)
		self.album = uniMe(album)
		self.artist = uniMe(artist)
		self.year = uniMe(year)
		self.genre = uniMe(genre)
		self.location = uniMe(location)
		self.length = uniMe(length)
	
	def __str__(self):
		returnstring = u'ID: ' + uniMe(str(self.ID)) + u' Title: ' + self.title + u' Album: ' + self.album
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
		"""inserts a list of items to the database. Pass in a list of song dataz, [[title, album, artist, year, genre, location, length], [title]]
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
		row = sess.query(songfromdb).filter(songfromdb.ID == int(songID)).one()
		returnMe = {'ID':row.ID, \
		'title':uniMe(row.title), \
		'album':uniMe(row.album), \
		'artist':uniMe(row.artist), \
		'year':uniMe(row.year), \
		'genre':uniMe(row.genre), \
		'location':uniMe(row.location), \
		'length':uniMe(row.length)}
		sess.commit()
		sess.close()
		return returnMe
	def lookupSongByLocation(self, location):
		sess = self.sessionMaker()
		if type(location) == str:
			location = location.decode('utf-8')
		row = sess.query(songfromdb).filter(songfromdb.location == location).one()
		returnMe = {'ID':row.ID, \
		'title':uniMe(row.title), \
		'album':uniMe(row.album), \
		'artist':uniMe(row.artist), \
		'year':uniMe(row.year), \
		'genre':uniMe(row.genre), \
		'location':uniMe(row.location), \
		'length':uniMe(row.length)}
		sess.commit()
		sess.close()
		return returnMe
	def getLocationByID(self, songID):
		sess = self.sessionMaker()
		result = sess.query(songfromdb).filter(songfromdb.ID == songID).one()
		returnMe =	result.location
		sess.commit()
		sess.close()
		return returnMe
	def getRandomID(self):
		sess = self.sessionMaker()
		maxID = max(sess.query(songfromdb.ID))
		sess.commit()
		sess.close()
		ID = random.randint(1, maxID[0])
		return ID
	def searchForSongs(self, query):
		if not query or query == '':
			print 'Please enter search terms'
			return None
		query = uniMe(query)
		query = query.lower()
		query = '%' + query + '%'
		sess = self.sessionMaker()
		results = sess.query(songfromdb).filter(sqlalchemy.or_(songfromdb.title.like(query), songfromdb.artist.like(query), songfromdb.album.like(query))).order_by('album').all() 
		returnMe = []
		if not results:
			return None
		for row in results:
			returnMe.append({'ID':row.ID, \
			'title':uniMe(row.title), \
			'album':uniMe(row.album), \
			'artist':uniMe(row.artist), \
			'year':uniMe(row.year), \
			'genre':uniMe(row.genre), \
			'location':uniMe(row.location), \
			'length':uniMe(row.length)})
		sess.commit()
		sess.close()
		return returnMe
	def pprint(self, songID):
		sess = self.sessionMaker()
		songRow = sess.query(songfromdb).filter(songfromdb.ID == songID).one()
		if not songRow:
			return 'Song not found.'
		else:
			returnString =	'ID: ' + str(songRow.ID).decode('utf-8') + ' | ' + \
			'Title: ' + uniMe(songRow.title) + ' | ' + \
			'Album: ' + uniMe(songRow.album) + ' | ' + \
			'Artist: ' + uniMe(songRow.artist) + ' | ' + \
			'Length: ' + uniMe(songRow.length)
			sess.commit()
			sess.close()
			return returnString
	def pprintByLocation(self, snglocation):
		sess = self.sessionMaker()
		snglocation = uniMe(snglocation)
		songRow = sess.query(songfromdb).filter(songfromdb.location == snglocation).one()
		if not songRow:
			sess.commit()
			sess.close()
			return 'Song not found.'
		else:
			returnString =	'ID: ' + uniMe(str(songRow.ID)) + ' | ' + \
			'Title: ' + uniMe(songRow.title) + ' | ' + \
			'Album: ' + uniMe(songRow.album) + ' | ' + \
			'Artist: ' + uniMe(songRow.artist) + ' | ' + \
			'Length: ' + uniMe(str(songRow.length))
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
	def getListOfSongs(self, locations=False):
		"""returns a list of every song in the database. For use in database comparison"""
		sess = self.sessionMaker()
		results = sess.query(songfromdb).all()
		returnMe = []
		for row in results:
			if locations == True:
				returnMe.append(row.location)
			else:
				returnMe.append({'ID':uniMe(str(row.ID)), \
				'title':row.title, \
				'album':row.album, \
				'artist':row.artist, \
				'year':row.year, \
				'genre':row.genre, \
				'location':row.location, \
				'length':row.length})
			#	print type(returnMe[0]['location'])
		sess.commit()
		sess.close()
		
		return returnMe
def uniMe(obj, encoding='utf-8'):
	if isinstance(obj, basestring):
		if not isinstance(obj, unicode):
			obj = unicode(obj, encoding)
	return obj

class playlist(list):
	"""Internal representation of a list of songs.
	For convenience (not having to type database name for every function call), playlists are tied to a database."""
	def __init__(self, dbName, name):
		self.db = dbName
		self.plName = name
	def __str__(self):
		returnString = ''
		print self.plName.center(62, '=')
		for item in self:
			print self.db.pprintByLocation(item)
		return '=============================================================='
		#return ''
	def __setitem__(self, index, item):
		item = uniMe(item)
		return list.__setitem__(self, index, item)
	def add(self, songLoc, load=False):#CHECK IF LOCATION IS VALID - SEARCH FOR FILENAME IF NOT; OR BUST SAFELY
		if isinstance(songLoc, basestring):
			songLoc = uniMe(songLoc)
			if songLoc in self:
				print 'Duplicate not added:', songLoc
			else:
				self.append(songLoc)
				if load == False:
					print 'Added ', self.db.pprintByLocation(songLoc)
					
		else:
			print "Please give me a string location!"
	def saveToDisk(self, location, directory):
		"""Saves the playlist to the chosen location in XSPF format."""
		if location.startswith('temp') or location == 'random':
			return "We don't save temporaries!"
		location = os.path.join(directory, location)
		xml = XmlWriter(io.open(location, 'w+b'), indentAmount='  ')

		xml.prolog()
		xml.start('playlist', { 'xmlns': 'http://xspf.org/ns/0/', 'version': '1' })
		xml.start('trackList')

		for line in self:
			line = uniMe(line)
			url = 'file://' + urllib.pathname2url(line)
			xml.start('track')
			xml.elem('location', url)
			xml.end() # track
		xml.end() # trackList
		xml.end() # playlist
		return 'Success'
	def loadFromDisk(self, plName, pathName):
		"""loads a playlist from the harddrive"""
		location = uniMe(os.path.join(pathName, plName + '.xspf'))
		try:
			tree = parse(location)
		except IOError:
			return 'File not found'
		except ExpatError:
			os.remove(location)
			return 'Invalid file'
		root = tree.getroot()
		for item in root.getiterator('{http://xspf.org/ns/0/}location'):
			formattedPath = item.text[7:]
			formattedPath = urllib.url2pathname(formattedPath).decode('utf-8')
			self.add(formattedPath, True)
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