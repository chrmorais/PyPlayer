#!/usr/bin/python2.6

# encoding: utf-8
#TODO:
#Command shell with regexes
#ncurses interface
#docstrings as-you-type
#defense against moved files referenced in saved playlists 
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
import cmd
import time
#So, you ignored that STERN warning on the github page, eh? Well, I'm very flattered, but you're in for a bumpy ride. Ok, heres what you need to do:
#edit the config file, insert paths where directed. Install packages as necessary to fufill packages required for the above imports. Also toss in sqlite3. Then run me, song db should be created automatically.
runType = 'debug' #currently does nothing much, it's a placeholder! :O
appVersion = 0.5


def getHeightAndWidth():
	"""Returns the size of the terminal in the format rows, cols, x pixels, y pixels"""
	s = struct.pack("HHHH", 0, 0, 0, 0)
	fd_stdout = sys.stdout.fileno()
	x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
	# rows, cols, x pixels, y pixels
	return struct.unpack("HHHH", x)
def uniMe(obj, encoding='utf-8'):
	if isinstance(obj, basestring):
		if not isinstance(obj, unicode):
			obj = unicode(obj, encoding)
	return obj

class commandShell(cmd.Cmd):
	def __init__(self, mainScreen, completekey='tab', stdin=None, stdout=None):
		initalTime = time.clock()
		print "".center(62, "=")
		print '=============== Beginning startup of PyPlayer ' + str(float(appVersion))
		print ''.center(62, '=')
		#load config variables from file
		sys.stdout.write('Loading config from config.yml... ' + '\r')
		sys.stdout.flush()
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
		print 'Loading config from config.yml... Done'
		#=========================================================================
		sys.stdout.write('Initalizing variables...' + '\r')
		sys.stdout.flush()
		self.exit = False
		self.currentPlaylists = dict()
		self.intro = 'Common commands: play, search, pause, next, prev. Type help for full listing, and help <command> for more help.'
		self.stdin = sys.stdin
		self.stdout = sys.stdout
		self.cmdqueue = []
		self.completekey = completekey
		self.use_rawinput = True
		self.spam = spam
		self.mainScreen = mainScreen
		#=========================================================================
		print "Initalizing variables...Done"
		sys.stdout.write('Initalizing database at ' + dbFileName + '...' + '\r')
		sys.stdout.flush()
		self.db = db = database.database(dbLocation)
		print 'Initalizing database at ' + dbFileName + '...' + 'Done'
		#=========================================================================
		self.appName = appName
		sys.stdout.write('Initalizing player... ' + '\r')
		sys.stdout.flush()
		self.plyr = player(self.db, self, self.mainScreen)
		print 'Initalizing player...Done'
		#=========================================================================
		self.dir = workingDir
		self.musicDir = musicDir
		sys.stdout.write('Initalizing scanner... ' + '\r')
		sys.stdout.flush()
		self.scnr = scanner.scanMachine(self.db)
		print 'Initalizing scanner...Done'
		#=========================================================================
		sys.stdout.write('Scanning playlists... ' + '\r')
		sys.stdout.flush()
		self.scanForPlaylists()
		print 'Scanning playlists...Done'
		#=========================================================================
		sys.stdout.write('Scanning for library changes... ' + '\r')
		sys.stdout.flush()
		self.scanForChanges()
		print 'Scanning for library changes...Done'
		finalTime = time.clock()
		difference = finalTime - initalTime
		print "Startup took " + str(difference) + " seconds. Nice!"


	def scanForChanges(self):
		"""Checks the current music folder vs. the current database. Any changes are merged in automatically."""
		songList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'.mp3', u'.ogg', u'.flac'])
		if not self.db.isDBThere():
			print 'Database not there!~\nRemaking library'
			self.db.metadata.create_all(self.db.conn)
			remakeList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'.mp3', u'.ogg', u'.flac'])
			self.scnr.addToDatabase(remakeList)
		else:#DB appears OK, let's compare and fix!
			oldSongList = self.db.getListOfSongs(locations=True)
			for item in songList:
				if item not in oldSongList:
					print self.db.addItemByLocation(item)
			for item in oldSongList:
				if item not in songList:
					print self.db.deleteItem(item)
		return 
	def scanForPlaylists(self):
		"""Scans the current working directory (ie the script directory) recursively for playlists and loads them."""
		listOfPlaylists = self.scnr.scanForFiles(startDirectory=self.dir, fileTypes=['.xspf'], dontvisit=[])
		for item in listOfPlaylists:
			plName = os.path.split(item)[-1].split('.')[0]
			if not plName == 'random':
				try:
					if self.currentPlaylists[plName]:
						print self.currentPlaylists[plName].loadFromDisk(plName, self.dir)
				except KeyError:
					self.currentPlaylists[plName] = database.playlist(self.db, plName)
					print self.currentPlaylists[plName].loadFromDisk(plName, self.dir)
			else:
				os.remove(os.path.join(self.dir, plName +'.xspf'))
	def preloop(self):
		if gst.STATE_PLAYING == self.plyr.player.get_state()[1]:
			self.prompt = ''
		else: 
			self.prompt = 'Enter a command >'
	#def createShell(self):
	#		try:
	#			self.cmdloop()
	#		except KeyboardInterrupt:
	#			
	#			pass
	#		except EOFError:
	#			print
	#			self.quitProperly()

		#=============================================================================================
		#=========== QUITTING
		#=============================================================================================
	def do_quit(self, rawInput):
		"""Quits the application, saving all non-temporary playlists."""
		self.quitProperly()

		#=============================================================================================
		#=========== PLAY OPERATIONS
		#=============================================================================================
	def do_play(self, rawInput):
		"""Play on it's own simply starts the player playing, if it is currently paused. Add some extra words to play, and it is used to get the ball rolling.
Acceptable formats:
play random
play <song ID>
play <search string>"""
		userInput = rawInput.split(' ')
		try:
			if not rawInput or rawInput == '':
				self.plyr.play()
			elif userInput[0].isdigit():
				songIDtoPlay = int(userInput[0])
				self.plyr.playRandom(songIDtoPlay)
			elif userInput[0] == 'random':
				self.plyr.playRandom(None)
			elif userInput[0] in self.currentPlaylists:
				#is it a playlist name?
				#print  self.currentPlaylists[userInput[0]]
				self.plyr.playAList(None, userInput[0])
			else:#must be a search query, let's make a temporary playlist with the results and play that
				randomName = [u'temp', unicode(random.getrandbits(50))]
				randomName = ''.join(randomName)
				searchResults = self.db.searchForSongs(rawInput)
				if searchResults:
					self.currentPlaylists[randomName] = database.playlist(self.db, randomName)
					for song in searchResults:
						self.currentPlaylists[randomName].add(song['location'], True)
					#print self.currentPlaylists[randomName]
					self.plyr.playAList(None, randomName)
				else:#no results found, obviously
					self.mainScreen.setStatus((None, 'No results found for play.'))



		except ValueError: 
			pass

	def do_pause(self, rawInput):
		"""Pauses the currently playing song. If nothing is playing, does nothing."""
		self.plyr.pause()
	def do_next(self, rawInput):
		"""Plays the next song in a playlist. 
If we are at the end of the playlist, this command will loop normak playlists and start playing shuffle after temporary playlists.
If no playlist is loaded, does nothing."""
		self.plyr.playNext()
	def do_prev(self, rawInput):
		"""Plays the song before the currently playing song in a playlist. If at the beginning of a list, plays the final song. If no playlist loaded, does nothing."""
		self.plyr.playPrevious()
#		self.mainScreen.setStatus()
	def do_p(self, rawInput):
		"Either plays or pauses playback based on wether we are currently playing or paused."
		self.plyr.playPause()
	def do_stop(self, rawInput):
		"Stops playback and removes song from memory. Can not restart playback after this command without defining what to play."
		self.plyr.unprimePlayer()
#			print '''Type a space-seperated list consisting of a command and then parameters. For example:
#
#			add <ID or search string> to APlaylist
#			search <string>
#			next
#			play
#			pause
#			stop
#			rescan
#			'''





		#=============================================================================================
		#=========== DIRECT SEARCHES
		#=============================================================================================
	def do_search(self, rawInput):
		"""Searches for the specified terms and prints them to the command line. To do things with these results, use add or play.
Syntax: search <search terms>"""
		try:
			results = self.db.searchForSongs(rawInput)
			if results == None or results == []:
				self.mainScreen.setStatus('No results found.')
			else:
				for songRow in results:
					print u'ID: ' + uniMe(str(songRow['ID'])) + u' | ' + \
					u'Title: ' + songRow['title'] + u' | ' + \
					u'Album: ' + songRow['album'] + u' | ' + \
					u'Artist: ' + songRow['artist']
		except IndexError:
			self.mainScreen.setStatus('You forgot to enter some search terms!')
		#=============================================================================================
		#=========== PLAYLIST OPERATIONS
		#=============================================================================================
	def do_add(self, rawInput):
		"""Adds an ID or the results of a search term to a playlist.
Playlist is created if not already existing.
Syntax: add <ID or search string> to <playlist name>"""
		userInput = rawInput.split(' 8')
		try:
			end = rawInput.find('to')#Some shitty parsing here, assumes everything between the 4th character and the word "to" is the search query or ID,
			# and everything past the word "to" (end+3) is the playlist name. Hey, it works

			if end == -1: #"to" not found, it's necessary!
				self.onecmd('help add')
			elif rawInput[end+2:end+3] != ' ':
				self.onecmd('help add')
			else:
				playlistName = rawInput[end+3:]#This grabs the playlist name in a string.
				if playlistName == '' or not playlistName:
					self.onecmd('help add')
				try:
					if self.currentPlaylists[playlistName]:
						pass
				except KeyError:
					self.currentPlaylists[playlistName] = database.playlist(self.db, playlistName)
					#print "Created", playlistName
				if userInput[0].isdigit():
					self.currentPlaylists[playlistName].add(self.db.getLocationByID(userInput[1]))

				else:
					searchQuery = rawInput[4:end-1]
					results = self.db.searchForSongs(searchQuery)
					if not results == None:
						for item in results:
							self.currentPlaylists[playlistName].add(item['location'])
					else:
						self.mainScreen.setStatus((None, 'No results found.'))
		except (IndexError):
			self.onecmd('help add')
	def do_del(self, rawInput):
		"""Removes either an ID from a playlist, or deletes a playlist.
If playlist is empty after ID removal, playlist is deleted.
Syntax: del <ID or playlist name> [from <playlist name>]"""
		userInput = rawInput.split(' ')
		try:
			if not userInput[0]:
				pass
			else:
				start = rawInput.find('from')
				if start == -1:#we're deleting a playlist
					try:
						del self.currentPlaylists[userInput[0]]
						os.remove(os.path.join(self.dir, userInput[0] +'.xspf'))
						self.mainScreen.setStatus(userInput[0].strip() + 'deleted.')
					except (IndexError, KeyError):
						self.mainScreen.setStatus('Playlist not found, nothing deleted.')
				elif not start == -1 and userInput[0].isdigit():#removing a songID from a playlist
					songID = rawInput[:start].strip()
					plName = rawInput[start+1:].strip()
					for item in self.currentPlaylists[plName]:
						songObject = self.db.lookupSongByLocation(item)
						if songObject['ID'] == int(songID):
							self.mainScreen.setStatus(songObject['title'], 'removed from ', plName)
							self.currentPlaylists[plName].remove(item)
					if len(self.currentPlaylists[plName]) <= 0:
						del self.currentPlaylists[plName]
						self.mainScreen.setStatus(plName, 'is now empty, deleting.')

				else:
					self.onecmd('help del')

		except IndexError:
			self.onecmd('help del')
		except OSError:#playlist wasn't saved, we don't need to handle this
			pass

		#=============================================================================================
		#=========== PLAYLIST PRINTING FUNCTION
		#=============================================================================================
	def do_plist(self, rawInput):
		"""Prints out the names and contents of every loaded playlist."""
		if not self.currentPlaylists:
			print 'No playlists loaded.'
		for item in self.currentPlaylists:
			if not item == 'random':
				print self.currentPlaylists[item]

		#=============================================================================================
		#=========== SAVE/LOAD PLAYLISTS
		#=============================================================================================
	def do_save(self, rawInput):
		"""Saves a currently loaded playlist to disk in the workingDir specified in config.yml.
Syntax: save <playlist name>"""
		plName = rawInput.strip()
		if isinstance(plName, str):
			plName = plName.decode('utf-8')
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
				self.mainScreen.setStatus('Playlist not found.')
	def do_load(self, rawInput):
		"""Loads a playlist from the workingDir specified in config.yml.
Do not specify the .xspf.
Syntax: load <playlist file name>"""
		plName = rawInput.strip()
		if plName == 'all':
			self.scanForPlaylists()
		else:
			try:
				if self.currentPlaylists[plName]:
					self.mainScreen.setStatus(self.currentPlaylists[plName].loadFromDisk(plName, self.dir))
			except KeyError:
				self.currentPlaylists[plName] = database.playlist(self.db)
				self.mainScreen.setStatus(self.currentPlaylists[plName].loadFromDisk(plName, self.dir))
		#=============================================================================================
		#=========== 'DEBUGGING'
		#=============================================================================================
	def do_crash(self, rawInput):
		"""What do you think this does?"""
		raise 'sup bro'

		#=============================================================================================
		#=========== RESCAN LIBRARY
		#=============================================================================================
	def do_rescan(self, rawInput):
		"""Destroys and remakes the library with the contents of the musicDir specified in config.yml."""
		self.mainScreen.setStatus('Remaking library')
		songList = self.scnr.scanForFiles(startDirectory=self.musicDir, fileTypes=[u'.mp3', u'.ogg', u'.flac'])
		self.scnr.addToDatabase(songList)
		#=============================================================================================
		#=========== MISC FUNCTIONS
		#=============================================================================================
	def do_stats(self, rawInput):
		"""Prints a number of novelty statistics about your music library."""
		library = self.db.getListOfSongs()
		totalNum = len(library)
		totalLength = 0
		libraryLengths = list()
		for item in library:
			totalLength += item['length']
			libraryLengths.append(item['length'])
		maxLength = max(libraryLengths)
		avgLength = totalLength / len(library)
		minLength = min(libraryLengths)
		returnList = list()
		returnList.append("Total length of lib: " + self.plyr.secondsToReadableTime(totalLength, False) + " | ")
		returnList.append('Total number of songs: ' + str(totalNum) + " | ")
		returnList.append('Longest song: ' + self.plyr.secondsToReadableTime(maxLength, False) + " | ")
		returnList.append('Shortest song: '+ self.plyr.secondsToReadableTime(minLength, False) + " | ")
		returnList.append('Average length: ' + self.plyr.secondsToReadableTime(avgLength, False))
		returnString = ''.join(returnList)
		self.mainScreen.setStatus((None, returnString))
	def do_dups(self, rawInput):
		songList = self.db.getListOfSongs()
		for item in songList:
			songList[songList.index(item)] = item['title']
		secondList = list()
		dups = list()
		while True:
			try:
				compareMe = songList.pop()
				if compareMe in secondList:
					dups.append(compareMe)
				secondList.append(compareMe)
			except IndexError:
				break
		for item in dups:
			print item
	def quitProperly(self):
		"""Quits the application, saving all non-temporary playlists."""
		if not self.currentPlaylists == {}:
			save = False
			for item in self.currentPlaylists:
				if not item.startswith('temp') and not item == 'random':
					save = True
					break
			if save:
				#saveLists = raw_input('Do you want to save your playlist(s)?')
				#if saveLists.lower().strip() in ['y', 'yes', 'ok']:
				iterator = 0
				for item in self.currentPlaylists.keys():
					self.currentPlaylists[item].saveToDisk(item + '.xspf', self.dir)
		self.mainScreen.quitTime()
		quit()

		
					
					
class player(object):
	def playLocation(self, nothing, location):
		self.dbName.pprintByLocation(location)
		self.primePlayer(location)
		self.play()
	def playAList(self, nothing, listname, index=0):
		"""Plays a playlist item of the specified index. Defaults to first song."""

		self.currentList = listname
		playMe = self.cmdSh.currentPlaylists[listname][index]
		self.playLocation(None, playMe)

	def playRandom(self, nothing, startWith=None):
		if 'random' in self.cmdSh.currentPlaylists.keys():
			if not startWith == None:
				self.playLocation(None, self.dbName.getLocationByID(startWith))
			random.shuffle(self.cmdSh.currentPlaylists['random'])
			self.playAList(None, 'random', 0)
		else:
			self.cmdSh.currentPlaylists['random'] = database.playlist(self.dbName, 'random')
			songList = self.dbName.getListOfSongs()
			for item in songList:
				self.cmdSh.currentPlaylists['random'].append(item['location'])
		#	self.cmdSh.currentPlaylists['random'].randomize()
			random.shuffle(self.cmdSh.currentPlaylists['random'])
			if not startWith == None:
				self.playLocation(None, self.dbName.getLocationByID(startWith))
			else:
				self.playAList(None, 'random')


#=============================================================================================
#=========== EASY FUNCTIONS ABOVE - THAR BE DRAGONS BELOW
#=============================================================================================

	def __init__(self, dbName, cmdSh, mainScreen):
		self.mainScreen = mainScreen
		self.dbName = dbName
		self.cmdSh = cmdSh
		self.currentList = None
		self.currentlyPlaying = None
		self.player = gst.element_factory_make("playbin", "player")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)
		self.time_format = gst.Format(gst.FORMAT_TIME)
		self.growl = Growl.GrowlNotifier(applicationName=self.cmdSh.appName, notifications=['Song change'], defaultNotifications=['Song change'])
		self.growl.register()
		
	def primePlayer(self, location):
		"""Feed me a location to get the player rolling. After this, call self.play()"""
		self.unprimePlayer()
		if isinstance(location, unicode):
			location = location.encode('utf-8')
		formattedLocation = 'file://' + urllib.pathname2url(location)
		songRow = self.dbName.lookupSongByLocation(location)

		self.growl.notify(noteType='Song change', title=songRow['title'], description=songRow['album'], icon=Growl.Image.imageWithIconForFileType(songRow['location'].split('.')[-1]))
		self.currentlyPlaying = self.dbName.lookupSongByLocation(location)
	#	if isinstance(self.currentlyPlaying['location'], unicode):
	#		self.currentlyPlaying['location'] = self.currentlyPlaying['location']
		self.player.set_property("uri", formattedLocation)
		self.threadName = threading.Thread(target=self.play_thread, name='theWarden')
		self.threadName.daemon = True
		self.threadName.start()

		
	def unprimePlayer(self):
		self.currentlyPlaying = None
		self.player.set_state(gst.STATE_NULL)
	#	try:
	#		if not self.playType == 'playlist':
	#			self.currentList == None
	#	except AttributeError:
	#		pass
		try:
			self.threadName.join()#Here, we give the helper thread time to realise nothing is playing and quit.
		except (AttributeError, RuntimeError):#No thread active?! Calling this function from within a helper thread?! Oh well, I don't care! It works!
			pass
		self.threadName = None
		return
	#=============================================================================================
	#=========== PLAY CONTROL FUNCTIONS
	#=============================================================================================
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
		if self.currentList == None or self.currentList =='':
			self.playRandom(None)
			return
		nextSongIndex = self.cmdSh.currentPlaylists[self.currentList].index(lastPlayed['location']) + 1
		if nextSongIndex >= len(self.cmdSh.currentPlaylists[self.currentList]):#are we at the end of the playlist?
			if self.currentList.startswith('temp'):#we want to play random songs afterwards, not loop.
				self.playRandom(None)
			else:
				self.playAList(None, self.currentList, index=0) #loop the playlist
		else:
			self.playAList(None, self.currentList, index=nextSongIndex)

	def playPrevious(self):
		lastPlayed = self.currentlyPlaying
		self.unprimePlayer()
		if self.currentList == None or self.currentList =='':
			self.playRandom(None)
			return
		prevSongIndex = self.cmdSh.currentPlaylists[self.currentList].index(lastPlayed['location']) - 1
		if prevSongIndex < 0:
			self.playAList(None, self.currentList, index=-1) #play the last song
		else:
			self.playAList(None, self.currentList, index=prevSongIndex)
	#=============================================================================================
	#=========== PLAY THREAD FUNCTION
	#=============================================================================================
	def play_thread(self):#remind me to replace simple two int comparison with a queue. then we query more often to work a long list of
	#old progress indicators rather than just two. Or just compare duration and position <3
		while not gst.STATE_PLAYING == self.player.get_state()[1]:
			time.sleep(.1)
		self.mainScreen.setStatus("reset")
		while True:
			try:
				DurationString = self.secondsToReadableTime(self.player.query_duration(self.time_format, None)[0], True)
				break
			except gst.QueryError:
			#Unable to query duration from gstreamer. Fuck you, gstreamer. Falling back to stored data minus 1 second.
				#self.mainScreen.setStatus((None, "I like monkeys"))
				try:
					DurationString = self.secondsToReadableTime(self.currentlyPlaying['length'] - 1, False)
				except TypeError:
					DurationString = None
				break
		songInfo = self.dbName.pprintByLocation(self.currentlyPlaying['location'])
		while True:
			#try:			
			if gst.STATE_PLAYING == self.player.get_state()[1]:
				pos_int = self.player.query_position(self.time_format, None)[0]
				PositionString = self.secondsToReadableTime(pos_int, True)
				stringToWrite = (('Playing: ' + PositionString + " of " + DurationString),  songInfo)
				self.mainScreen.setStatus(stringToWrite, True)
				if DurationString == PositionString:
					if self.currentlyPlaying == None:
						pass
					else:
						self.playNext()
						break
			elif gst.STATE_PAUSED == self.player.get_state()[1]: 
				pos_int = self.player.query_position(self.time_format, None)[0]
				PositionString = self.secondsToReadableTime(pos_int, True)
				stringToWrite = (('Paused: ' + PositionString + " of " + DurationString),  songInfo)
				self.mainScreen.setStatus(stringToWrite, True)
			elif gst.STATE_NULL == self.player.get_state()[1]:#die otherwise!
				self.mainScreen.setStatus(('Nothing playing.', ""))
				break
			time.sleep(1)
			#except OSError, e:
			#	self.mainScreen.setStatus('Error detected: ' + e)
				
	#=============================================================================================
	#=========== MISC FUNCTIONS
	#=============================================================================================
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
			self.mainScreen.setStatus((None, "Error: %s" % err, debug))
			self.unprimePlayer()
	

				


if __name__ == "__main__":
	shell = commandShell()
	shell.createShell()

	
	
	
	
#the graveyard
#	elif userInput[0] == 'check':#this command checks for lengths of "Unknown"
#		results = self.db.getListOfSongs()
#		for item in results:
#			if item['length'] == 'Unknown':
#				print 'unknown found! ', item
#termSize = getHeightAndWidth()
#						oldString = stringToWrite
#if isinstance(stringToWrite, unicode):
#	stringToWrite = stringToWrite.encode('utf-8')
#	self.mainScreen.setStatus(((' ' * termSize[1]) + '\r')#what we do here is clear the entire line. 
#	sys.stdout.flush()
#	if type(listname) == basestring:
#		listname = self.cmdSh.currentPlaylists[listname]
#	if index == 0 and not listname == 'random':#only print entire playlist when beginning to play it
#		print  self.cmdSh.currentPlaylists[listname]
#	if DurationString == None:
#		print 'Unable to calculate duration of song. Stopping playback.'
#		print self.currentlyPlaying
#		self.unprimePlayer()
#		break
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