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
import glob
import pygst
pygst.require("0.10")
import gst
import threading
import time
import datetime
import Growl
import termios
import fcntl
import struct
import yaml

#lolmessage = '''So, you ignored that STERN warning on the github page, eh? Well, I\'m very flattered, but you\'re in for a bumpy ride. Ok, heres what you need to do:
#	rename PyPlayer.conf.example to PyPlayer.conf. Edit it, insert paths where directed.'''
runType = 'debug' #currently does nothing much, it's a placeholder! :O

try:
	fileObj = open(os.path.join(os.getcwdu() + '/config.yml'))
except IOError:
	print 'Config file not found. Give it back!'
	print 'Lost it? Find a copy on http://github.com/ripdog/PyPlayer/raw/master/config.yml'
	quit()
try:
	config = yaml.load(fileObj)[runType]
except:#Too many errors to catch individually. In any case, if this fails, the file is likely borked.
	print 'Config file corrupt!'
	print 'Grab a new copy from http://github.com/ripdog/PyPlayer/raw/master/config.yml'
	quit()
spam = config['spam']
appName = config['appName']
workingDir = config['workingDir']
musicDir = config['musicDir']
dbFileName = config['dbFileName']
dbLocation = 'sqlite:///' + os.path.join(workingDir, dbFileName)

def getHeightAndWidth():
	"""Returns the size of the terminal in the format rows, cols, x pixels, y pixels"""
	s = struct.pack("HHHH", 0, 0, 0, 0)
	fd_stdout = sys.stdout.fileno()
	x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
	# rows, cols, x pixels, y pixels
	return struct.unpack("HHHH", x)
class commandShell(object):
	def __init__(self):
		self.exit = False
		self.currentPlaylists = dict()
		self.db = db = database.database(dbLocation)

		self.plyr = player(self.db, self)
		self.dir = workingDir
		self.musicDir = musicDir
		self.scnr = scanner.scanMachine(self.db)
		print 'Scanning playlists'
		self.scanForPlaylists()
		print 'Scanning for changes to music'
		self.scanForChanges()
			
	def scanForChanges(self):
		"""Checks the current music folder vs. the current database. Any changes are merged in automatically."""
		songList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'mp3', u'ogg', u'flac'])
		if not self.db.isDBThere():
			print 'Database not there!~\nRemaking library'
			self.db.metadata.create_all(self.db.conn)
			remakeList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'mp3', u'ogg', u'flac'])
			self.scnr.addToDatabase(remakeList)
		else:#DB appears OK, let's compare and fix!
			oldSongList = self.db.getListOfSongs(locations=True)
			for item in songList:
				if item not in oldSongList:
					print self.db.addItemByLocation(item)
			for item in oldSongList:
				if item not in songList:
					print self.db.deleteItem(item['location'])
		return 
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
		while True:
			try:
				rawInput = None
				userInput = None
				if gst.STATE_PLAYING == self.plyr.player.get_state()[1]:
					rawInput = raw_input('').lower()
				else: 
					rawInput = raw_input('Enter command >').lower()
				self.interpretCommand(rawInput)
				
			except KeyboardInterrupt:
				print
				pass
			except EOFError:
				print ''
				self.quitProperly()
	def interpretCommand(self, rawInput):
		userInput = rawInput.split(" ")
		userInput[0] = userInput[0].lower()
		if userInput[0] == "help":
			print '''Type a space-seperated list consisting of a command and then parameters. For example:
			play random
			play 143
			play <search string>
			add <ID or search string> to APlaylist
			search <string>
			next
			play
			pause
			stop
			rescan
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
					self.plyr.playAList(self.currentPlaylists[userInput[1]])
				else:#must be a search query, let's make a temporary playlist with the results and play that
					#pdb.set_trace()
					randomName = ['temp', unicode(random.getrandbits(50))]
					randomName = ''.join(randomName)
					searchQuery = rawInput[5:]
					searchResults = self.db.searchForSongs(searchQuery)
					if not searchResults == [] and not searchResults == None:
						self.currentPlaylists[randomName] = database.playlist(self.db, randomName)
						for song in searchResults:
							self.currentPlaylists[randomName].add(song['location'])
						self.plyr.playAList(self.currentPlaylists[randomName])
					else:#no results found, obviously
						print 'No results found, try harder.'

					

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
		elif userInput[0] == 'p':
			print self.plyr.player.get_state()[1]
			self.plyr.playPause()

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
					for songRow in results:
						print 'ID: ' + str(songRow['ID']) + ' | ' + \
						'Title: ' + songRow['title'] + ' | ' + \
						'Album: ' + songRow['album'] + ' | ' + \
						'Artist: ' + songRow['artist']
			except IndexError:
				print 'You forgot to enter some search terms!'
		#=============================================================================================
		#=========== PLAYLIST OPERATIONS
		#=============================================================================================
		elif userInput[0] == 'add':
			try:
				end = rawInput.find('to')#Some shitty parsing here, assumes everything between the 4th character and the word "to" is the search query or ID,
				# and everything past the word "to" (end+3) is the playlist name. Hey, it works

				if end == -1: #"to" not found, it's necessary!
					print"Usage: add <ID or search string> to <playlist name>"
					print"Playlist is created if not already existing."
				elif rawInput[end+2:end+3] != ' ':
					print "Remember to add a space beside \"to\""
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
						self.currentPlaylists[playlistName].add(self.db.getLocationByID(userInput[1]))
						
					else:
						searchQuery = rawInput[4:end-1]
						results = self.db.searchForSongs(searchQuery)
						for item in results:
							self.currentPlaylists[playlistName].add(item['location'], load=False)
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
						songObject = self.db.lookupSongByLocation(item)
						if songObject['ID'] == int(songID):
							print songObject['title'], 'removed from ', plName
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
				self.currentPlaylists[item].pprint()#.encode('utf-8')
		
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
		elif userInput[0] == 'check':#this command checks for lengths of "Unknown"
			results = getListOfSongs()
			for item in results:
				if item['length'] == 'Unknown':
					print 'unknown found! ', item
		#=============================================================================================
		#=========== RESCAN LIBRARY
		#=============================================================================================
		elif userInput[0] == 'rescan':
			print 'Remaking library'
			songList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'mp3', u'ogg', u'flac'])
			self.scnr.addToDatabase(songList)
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
				if saveLists.lower().strip() in ['y', 'yes', 'ok']:
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
	def playAList(self, listname, index=0):
		"""Plays a playlist item of the specified index. Defaults to first song."""
		if index == 0:#only print entire playlist when beginning to play it
			listname.pprint()
		self.currentList = listname
		self.playLocation(listname.playlist[index], 'playlist')

	def playRandom(self, startWith=None):
		self.playType = 'random'
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
		self.currentList = None
		self.currentlyPlaying = None
		self.player = gst.element_factory_make("playbin", "player")
		fakesink = gst.element_factory_make("fakesink", "fakesink")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)
		self.time_format = gst.Format(gst.FORMAT_TIME)
		self.growl = Growl.GrowlNotifier(applicationName=appName, notifications=['Song change'], defaultNotifications=['Song change'])
		self.growl.register()
		
	def primePlayer(self, location, playtype):
		"""Feed me a location to get the player rolling. After this, call play()
		Playtype can be 'random', 'playlist' or 'one'.
		When playtype is playlist, self.currentList must be set to the name of the current playlist."""
		self.unprimePlayer()
		if isinstance(location, unicode):
			location = location.encode('utf-8')
		formattedLocation = 'file://' + urllib.pathname2url(location)
		songRow = self.dbName.lookupSongByLocation(location)

		self.playType = playtype
		self.growl.notify(noteType='Song change', title=songRow['title'], description=songRow['album'], icon=Growl.Image.imageWithIconForFileType(songRow['location'].split('.')[-1]))
		self.currentlyPlaying = self.dbName.lookupSongByLocation(location)
		self.player.set_property("uri", formattedLocation)
		self.threadName = threading.Thread(target=self.play_thread, name='theWarden')
		self.threadName.daemon = True
		self.threadName.start()

		
	def unprimePlayer(self):
		self.currentlyPlaying = None
		self.player.set_state(gst.STATE_NULL)
		try:
			if not self.playType == 'playlist':
				self.currentList == None
		except AttributeError:
			pass
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

	def playPause(self):
		if gst.STATE_PLAYING == self.player.get_state()[1]:#we're playing!
			self.player.set_state(gst.STATE_PAUSED)
		else:
			self.player.set_state(gst.STATE_PLAYING)
		
	def playNext(self):
		lastPlayed = self.currentlyPlaying
		self.unprimePlayer()
		if self.playType == 'playlist':
			nextSongIndex = self.currentList.playlist.index(lastPlayed['location']) + 1
			if nextSongIndex => len(self.currentList.playlist):#are we at the end of the playlist?
				if self.currentList.plName.startswith('temp'):#we want to play random songs afterwards, not loop.
					self.playRandom()
				else:
					self.playAList(self.currentList, index=0) #loop the playlist
			else:
				self.playAList(self.currentList, index=nextSongIndex)
		elif self.playType == 'one':#thats all, folks~~!
			return
		else:#either random or invalid playtype. Honestly, I don't care
			self.playRandom()
	def play_thread(self):#remind me to replace simple two int comparison with a queue. then we query more often to work a long list of
	#old progress indicators rather than just two. Or just compare duration and position <3
		while not gst.STATE_PLAYING == self.player.get_state()[1]:
			time.sleep(.1)
		while True:
			try:
				DurationString = self.secondsToReadableTime(self.player.query_duration(self.time_format, None)[0], True)
				break
			except gst.QueryError:
			#Unable to query duration from gstreamer. Fuck you, gstreamer. Falling back to stored data minus 1 second.
				try:
					DurationString = self.secondsToReadableTime(self.currentlyPlaying['length'] - 1, False)
				except TypeError:
					DurationString = None
				break
		print '\nPlaying: ', self.dbName.pprintByLocation(self.currentlyPlaying['location'])
		while True:
			try:			
			#	if DurationString == None:
			#		print 'Unable to calculate duration of song. Stopping playback.'
			#		print self.currentlyPlaying
			#		self.unprimePlayer()
			#		break
				
				if gst.STATE_PLAYING == self.player.get_state()[1]:
					pos_int = self.player.query_position(self.time_format, None)[0]
					PositionString = self.secondsToReadableTime(pos_int, True)
					if spam:
						stringToWrite = self.currentlyPlaying['title'] + ': ' + PositionString + " of " + DurationString + '\r'
						termSize = getHeightAndWidth()
						sys.stdout.write((' ' * termSize[1]) + '\r')#what we do here is clear the entire line. 
						sys.stdout.flush()
						sys.stdout.write(stringToWrite)
						sys.stdout.flush()
						oldString = stringToWrite
					if DurationString == PositionString:
						if self.currentlyPlaying == None:
							print 'Nothing playing, quitting'
						else:
							self.playNext()
							break
				elif gst.STATE_PAUSED == self.player.get_state()[1]: 
					pass#Don't die during pause
				elif gst.STATE_NULL == self.player.get_state()[1]:#die otherwise!
					break
				else:#print state if not caught!
					print self.player.get_state()[1]
				time.sleep(1)
			except OSError:
				print 'Error detected: '
				
	
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