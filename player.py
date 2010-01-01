#!/usr/bin/python2.6

# encoding: utf-8
#TODO:
#Command shell with regexes
#ncurses interface
#docstrings as-you-type
"""
player.py

"""

import sys
import urllib
import scanner
import database
import pdb
import subprocess
import readline
import os
import random
import cPickle
import glob
import pygst
pygst.require("0.10")
import gst
import threading
import time
import datetime
import Growl

appName = 'PyPlayer'
lolmessage = '''So, you ignored that STERN warning on the github page, eh? Well, I\'m very flattered, but you\'re in for a bumpy ride. Ok, heres what you need to do:
	rename PyPlayer.conf.example to PyPlayer.conf. Edit it, insert paths where directed.'''
workingDir = u'/private/var/root/Working/PyPlayer2'
dbLocation = 'sqlite:///' + os.path.join(workingDir, 'songBase.sqlite')
musicDir = u'/private/var/root/Music/Local Music Lib/iTunes Media/Music'
class commandShell(object):
	def __init__(self):
		self.exit = False
		self.currentPlaylists = dict()
		self.db = db = database.database(dbLocation)
		self.plyr = player(self.db, self)
		self.dir = workingDir
		self.musicDir = musicDir
		self.scnr = scanner.scanMachine()
		print 'Scanning playlists'
		self.scanForPlaylists()
		print 'Scanning for changes to music'
		changes = self.scanForChanges()
		if changes > 0:
			print 'Changes detected in music library. Recommend rescan.'
	def scanForChanges(self):
		"""docstring for scanForChanges"""
		songList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'mp3', u'ogg', u'flac'])
		picklePath = os.path.join(self.dir, 'musicDirData.pickle')
		newSongs = []
		deletedSongs = []
		if not glob.glob(picklePath):
			cPickle.dump(songList, open(picklePath, 'w+b'), 2)
		else:#do comparison, comparison file exists
			oldSongList = cPickle.load(open(picklePath, 'r+b'))
			for item in songList:
				if item not in oldSongList:
					print 'Adding ', item
					print self.db.addItemByLocation(item)
			for item in oldSongList:
				if item not in songList:
					print 'Attempting removal of ', item
					print self.db.deleteItem(item)
			cPickle.dump(songList, open(picklePath, 'w+b'), 2)
		return len(newSongs) + len(deletedSongs)
	def scanForPlaylists(self):
		"""Scans the current working directory (ie the script directory) recursively for playlists and loads them."""
		listOfPlaylists = self.scnr.scanForFiles(startDirectory=self.dir, fileTypes=['xspf'], dontvisit=[])
		for item in listOfPlaylists:
			plName = os.path.split(item)[-1].split('.')[0]
			try:
				if self.currentPlaylists[plName]:
					print self.currentPlaylists[plName].loadFromDisk(plName, self.dir)
			except KeyError:
				self.currentPlaylists[plName] = database.playlist(self.db, plName)
				print self.currentPlaylists[plName].loadFromDisk(plName, self.dir)
	
	def createShell(self):
		while self.exit == False:
			try:
				rawInput = None
				userInput = None
				rawInput = raw_input('Type a command >').lower()
				userInput = rawInput.split(" ")
				userInput[0] = userInput[0].lower()
				if userInput[0] == "help":
					print '''Type a space-seperated list consisting of a command and then parameters. For example:
					play random
					play 143
					add <ID or search string> to APlaylist
					search <string>
					'''
					
				#=============================================================================================
				#=========== PLAY OPERATIONS
				#=============================================================================================
				elif userInput[0] == 'play':
					try:
						if not userInput[1]:
							pass
						if userInput[1].isdigit():
							songIDtoPlay = int(userInput[1])
							self.plyr.playRandom(songIDtoPlay)
						elif userInput[1] == 'random':
							self.plyr.playRandom()
						elif userInput[1] in self.currentPlaylists:
							#is it a playlist name?
							try:
								if userInput[1] in self.currentPlaylists:
									self.plyr.playAList(self.currentPlaylists[userInput[1]])
							except IndexError:
								print"Usage: play <ID, playlist or search query>"
						else:#must be a search query, let's make a temporary playlist with the results and play that
							randomName = ['temp', unicode(random.getrandbits(50))]
							randomName = ''.join(randomName)
							searchQuery = rawInput[5:]
							searchResults = self.db.searchForSongs(searchQuery)
							if not searchResults == [] or searchResults == None:
								self.currentPlaylists[randomName] = database.playlist(self.db, randomName)
								for song in searchResults:
									self.currentPlaylists[randomName].add(song['location'])
								self.plyr.playAList(self.currentPlaylists[randomName], True)

							

					except ValueError: 
						pass
					
					except IndexError:
						self.plyr.play()
				elif userInput[0] == 'pause':
					self.plyr.pause()
				elif userInput[0] == 'next':
					self.plyr.playNext()
				elif userInput[0] == 'stop':
					self.plyr.unprimePlayer()

				#=============================================================================================
				#=========== QUITTING
				#=============================================================================================

				elif userInput[0] == "exit" or userInput[0] == "quit":
					self.quitProperly()

							
				#=============================================================================================
				#=========== DIRECT SEARCHES
				#=============================================================================================
				elif userInput[0] == 'search':
					try:
						searchQuery = rawInput[7:]
						results = self.db.searchForSongs(searchQuery)
						if results == None or results == []:
							print 'No results found.'
						else:
							for row in results:
								print str(row['ID']) + ' ' + row['title']
					except IndexError:
						print 'You forgot to enter some search terms!'
				#=============================================================================================
				#=========== PLAYLIST OPERATIONS
				#=============================================================================================
				elif userInput[0] == 'add':
					try:
						end = rawInput.find('to')#Some shitty parsing here, assumes everything between the 4th character and the word "to" is the search query or ID,
						# and everything past the word "to" (end+3) is the playlist name. Hey, it works
						if end == -1:
							print"Usage: add <ID or search string> to <playlist name>"
							print"Playlist is created if not already existing."
						else:
							playlistName = rawInput[end+3:len(rawInput)]#THis grabs the playlist name in a string.
							if playlistName == '' or not playlistName:
								raise ValueError, 'No playlist name given'
							try:
								if self.currentPlaylists[playlistName]:
									pass
							except KeyError:
								self.currentPlaylists[playlistName] = database.playlist(self.db, playlistName)
								print "Created", playlistName
							if userInput[1].isdigit():
								self.currentPlaylists[playlistName].add(self.db.getLocationByID(userInput[1]), False)
								
							else:
								searchQuery = rawInput[4:end-1]
								results = self.db.searchForSongs(searchQuery)
								for item in results:
									self.currentPlaylists[playlistName].add(item['location'], False)
					except (IndexError):
						print"Usage: add <ID or search string> to <playlist name>"
						print"Playlist is created if not already existing."
				elif userInput[0] == 'del':
					try:
						if not userInput[1]:
							pass
						start = rawInput.find('from')
						if start == -1:#we're deleting a playlist
							try:
								del self.currentPlaylists[userInput[1]]
								os.remove(os.path.join(self.dir, userInput[1] +'.xspf'))
								print userInput[1].strip(), 'deleted.'
							except (IndexError, KeyError):
								print 'Playlist not found, nothing deleted.'
						elif not start == -1 and userInput[1].isdigit():#removing a songID from a playlist
							songID = rawInput[4:start].strip()
							plName = rawInput[start+5:].strip()
							for item in self.currentPlaylists[plName].playlist:
								if self.db.lookupSongByLocation(item)['ID'] == int(songID):
									print item, 'deleted'
									self.currentPlaylists[plName].playlist.remove(item)
									
						else:
							print'Usage: del <ID or playlist name> [from <playlist name>] '
							
					except IndexError:
						print'Usage: del <ID or playlist name> [from <playlist name>] '
					except OSError:#playlist wasn't saved, we don't need to handle this
						pass
					
				#=============================================================================================
				#=========== PLAYLIST PRINTING FUNCTIONS
				#=============================================================================================
				elif userInput[0] == 'currentlists' or userInput[0] == "plist":
					if not self.currentPlaylists:
						print 'No playlists loaded.'
					for item in self.currentPlaylists:
						print self.currentPlaylists[item]
				
				#=============================================================================================
				#=========== SAVE/LOAD PLAYLISTS
				#=============================================================================================
				elif userInput[0] == 'save':
					plName = rawInput[5:].strip()
					if plName == 'all':
						iterator = 0
						for item in self.currentPlaylists.keys():
							plName = self.currentPlaylists.keys()[iterator]
							item = self.currentPlaylists[plName]
							item.saveToDisk(plName + '.xspf', self.dir)
							if iterator > len(self.currentPlaylists):
								break
							else:
								iterator +=1
					else:
						try:
							self.currentPlaylists[plName].saveToDisk(plName + '.xspf', self.dir)
						except KeyError:
							print 'Playlist not found.'
				elif userInput[0] == 'load':
					plName = rawInput[5:].strip()
					if plName == 'all':
						self.scanForPlaylists()
					else:
						try:
							if self.currentPlaylists[plName]:
								print self.currentPlaylists[plName].loadFromDisk(plName, self.dir)
						except KeyError:
							self.currentPlaylists[plName] = database.playlist(self.db)
							print self.currentPlaylists[plName].loadFromDisk(plName, self.dir)
				#=============================================================================================
				#=========== 'DEBUGGING'
				#=============================================================================================
				elif userInput[0] == 'crash':
					raise 'sup bro'
			except KeyboardInterrupt:
				print
				pass
			except EOFError:
				print ''
				self.quitProperly()
	def quitProperly(self):
		"""docstring for quitProperly"""
		if not self.currentPlaylists == {}:
			save = False
			for item in self.currentPlaylists:
				if not item.startswith('temp'):
					save = True
					break
			if save:
				saveLists = raw_input('Do you want to save your playlist(s)?')
				if saveLists.lower() in ['y', 'yes', 'ok']:
					iterator = 0
					for item in self.currentPlaylists.keys():
						plName = self.currentPlaylists.keys()[iterator]
						item = self.currentPlaylists[plName]
						item.saveToDisk(plName + '.xspf', self.dir)
						if iterator > len(self.currentPlaylists):
							break
						else:
							iterator +=1
		print "Have a good day, sah!"
	#	self.db.endSession()
		quit()
				
		
					
					
class player(object):
	def playLocation(self, location, playType='random'):
		self.dbName.pprintByLocation(location)
		self.primePlayer(location, playType)
		self.play()
	def playAList(self, listname, index=0, temp=False):
		"""Plays a playlist item of the specified index. Defaults to first song."""
		if index == 0:#only print entire playlist when beginning to play it
			print listname
		self.currentList = listname
		self.playLocation(listname.playlist[index], 'playlist')

	def playRandom(self, startWith=None):
		if not startWith == None:
			self.playLocation(self.dbName.getLocationByID(startWith))
		else:
			songID = self.dbName.getRandomID()
			self.playLocation(self.dbName.getLocationByID(songID), 'random')
		
#=============================================================================================
#=========== EASY FUNCTIONS ABOVE - THAR BE DRAGONS BELOW
#=============================================================================================

	def __init__(self, dbName, cmdSh):
		self.dbName = dbName
		self.cmdSh = cmdSh
		currentlyPlaying = None
		self.player = gst.element_factory_make("playbin", "player")
		fakesink = gst.element_factory_make("fakesink", "fakesink")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)
		self.time_format = gst.Format(gst.FORMAT_TIME)
		self.growl = Growl.GrowlNotifier(applicationName=appName, notifications=['Song change'], defaultNotifications=['Song change'])
		self.growl.register()
		
	def primePlayer(self, location, playtype):
		self.unprimePlayer()
		formattedLocation = 'file://' + urllib.pathname2url(location.encode('utf-8'))
		songRow = self.dbName.lookupSongByLocation(location)
		self.dbName.pprintByLocation(location)
		self.playType = playtype
		blah = songRow['title'] + '\n'+ songRow['artist']
		self.growl.notify(noteType='Song change', title='Playing song:', description=blah, icon=Growl.Image.imageWithIconForFileType(songRow['location'].split('.')[-1]))
		self.player.set_property("uri", formattedLocation)
		self.threadName = threading.Thread(target=self.play_thread, name='theWarden')
		self.threadName.daemon = True
		self.threadName.start()
		self.currentlyPlaying = self.dbName.lookupSongByLocation(location)
		
	def unprimePlayer(self):
		
		self.currentlyPlaying = None
		self.player.set_state(gst.STATE_NULL)
		try:
			self.threadName.join()#Here, we give the helper thread time to realise nothing is playing and quit.
		except (AttributeError, RuntimeError):#No thread active?! Calling this function from within a helper thread?! Oh well, I don't care! It works!
			pass
		self.threadName = None
		return
		
	def play(self):
		self.player.set_state(gst.STATE_PLAYING)

	def pause(self):
		self.player.set_state(gst.STATE_PAUSED)

		
	def playNext(self):
		lastPlayed = self.currentlyPlaying
		self.unprimePlayer()
		if self.playType == 'playlist':
			nextSongIndex = self.currentList.playlist.index(lastPlayed['location']) + 1
			print nextSongIndex
			print len(self.currentList.playlist)
			if nextSongIndex >= len(self.currentList.playlist):
				if self.currentList.plName.startswith('temp'):#we want to play random songs afterwards, not loop.
					self.playRandom()
				else:
					self.playAList(self.currentList, index=0)
			else:
				self.playAList(self.currentList, index=nextSongIndex)
		elif self.playType == 'one':#thats all, folks~~!
			return
		else:#either random or invalid playtype. Honestly, I don't care
			self.playRandom()
	def play_thread(self):#remind me to replace simple two int comparison with a queue. then we query more often to work a long list of
	#old progress indicators rather than just two. Or just compare duration and position <3
		#while True:
			#if not self.changeTrack:
		while True:
			try:
				time.sleep(.5)
				DurationString = self.secondsToReadableTime(self.player.query_duration(self.time_format, None)[0], True)
		
			#	oldPosition = self.secondsToReadableTime(self.player.query_position(self.time_format, None)[0], True)
				break
			except gst.QueryError:
			#	print '\nUnable to query duration from gstreamer. Fuck you, gstreamer. Falling back to stored data minus 2 seconds.'
				DurationString = self.secondsToReadableTime(self.currentlyPlaying['length'] - 2, False)
				break
		while True:
			try:			
				time.sleep(1)
				if gst.STATE_PLAYING == self.player.get_state()[1]:
					pos_int = self.player.query_position(self.time_format, None)[0]
					#DurationString = self.secondsToReadableTime(songlength, False)
					PositionString = self.secondsToReadableTime(pos_int, True)
					print self.currentlyPlaying['title'], ': ', PositionString, DurationString
					if DurationString == PositionString:
						if self.currentlyPlaying == None:
							print 'Nothing playing, quitting'
						else:
							self.playNext()
							break
				else:
					break
			except TypeError:
				print 'lolwat'
				
	
	def secondsToReadableTime(self, timeInt, divide):
		if divide:
			timeInt = timeInt / 1000000000
		timeInt = round(timeInt)
		time = str(datetime.timedelta(seconds=timeInt))
		if int(time[:1]) > 0:#if there's hours, show em
			return time
		else:
			return time[2:]
	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS: #graceful exit, EOF etc. Return player to default state
			self.unprimePlayer()
		elif t == gst.MESSAGE_ERROR: #ohshit! Still, little difference to previous mode
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.unprimePlayer()
	

				


if __name__ == "__main__":
	
	shell = commandShell()

	shell.createShell()

	
	
	
	
#the graveyard
#subprocess.Popen(command, stdout=open('/dev/null'), stderr=open('/dev/null')).wait()
#help_message = '''
#Sup bro. Fuck off.
#'''
#import getopt
#class Usage(Exception):
#	def __init__(self, msg):
#		self.msg = msg
#def main(argv=None):
#	if argv is None:
#		argv = sys.argv
#	try:
#		try:
#			opts, args = getopt.getopt(argv[1:], "ho:v", ["help", "output="])
#		except getopt.error, msg:
#			raise Usage(msg)
#	
#		# option processing
#		for option, value in opts:
#			if option == "-v":
#				verbose = True
#			if option in ("-h", "--help"):
#				raise Usage(help_message)
#			if option in ("-o", "--output"):
#				output = value
#	
#	except Usage, err:
#		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
#		return 2

#elif userInput[0] == 'new':
#	if userInput[1] == 'playlist':
#		if userInput[2]:
#			if not userInput.startswith('\'') or userInput.startswith('\"'):
#				pass
#			plName = eval(userInput[2])
#			plName = database.playlist()
#			
#		else:
#			print 'Please supply a playlist name!'