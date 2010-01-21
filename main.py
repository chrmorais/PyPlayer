#!/usr/bin/python2.6
# coding:UTF-8

"""
main.py

"""
import sys, os
import urwid
import player
import database
import cmd
import time
import yaml
import scanner
import urwid.curses_display
import pprint

class myPile(urwid.Pile):
	pass

class songWidget(urwid.Button):
	button_left = urwid.widget.Text('')# CHANGE ME to indicate playing song. Scroll to focus will be hard tho :(
	button_right = urwid.widget.Text('')
	def __init__(self, label, location):
		self.__super.__init__(label)
		self.location = location
		urwid.connect_signal(obj=self, name='click', callback=commandSh.plyr.playAList, user_arg=[commandSh.plyr.currentList, 0, self.location])
class plWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label):
		self.__super.__init__(label)
		urwid.connect_signal(obj=self, name='click', callback=commandSh.plyr.playAList, user_arg=label)

class libraryWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label='Library'):
		self.__super.__init__(label)
		urwid.connect_signal(obj=self, name='click', callback=commandSh.plyr.playAList)
def docstringDisplayer(text):
	if hasattr(commandSh, 'do_' + text):
		mainDisp.setStatus((None, getattr(commandSh, 'do_' + text.strip()).__doc__))
	else:
		pass
	#mainDisp.setStatus(text)

class cmdSh(urwid.Edit):
	def __init__(self, prompt):
			self.__super.__init__(prompt)
	def keypress(self, size, key):
		#docstringDisplayer(self.get_edit_text())
		if key == "enter":
			commandSh.onecmd(self.get_edit_text())
			self.set_edit_text('')
			return
		if key == 'tab':
			mainDisp.pile.set_focus(0)
		self.__super.keypress(size, key)


#def playSong(songLoc, inList='random'):
#	while True:
#		if commandSh.plyr.currentList == inList:#we want to play an item in the current playlist
#
#			comma
#		else:
#			if inList in commandSh.currentPlaylists.keys():
#				commandSh.plyr.currentList = inList
#			else:
#				raise KeyError, "Non-existant playlist! Careful!"
		

class mainDisplay(object):
	def __init__(self):
		self.showPlayback = [True, 0]#Set this to false to display non-playback related info on the second display line. WHen set to false, you must set the second value to the current CPU time
		self.currentFocus = 5
		self.currentSongWidgets = list()
		self.currentPLWidgets = list()
	def renderList(self):
#		if not commandSh.plyr.currentlyPlaying == None:
#			print commandSh.plyr.currentlyPlaying
#			self.quitTime()
		try:
			for item in self.mainList.body:
				if item._original_widget.location == commandSh.plyr.currentlyPlaying['location']:
					item.button_left = urwid.widget.Text('▶')
		except KeyError:
			
			for item in self.mainList.body:
				if item._original_widget.location == commandSh.plyr.currentlyPlaying['location']:
					item.button_left = urwid.widget.Text('▶')
		except AttributeError:
			pass
		
		songList = db.getListOfSongs()
		songDictList = [item for item in songList if item['location'] in commandSh.currentPlaylists[commandSh.plyr.currentList]]
		self.currentSongWidgets = self.createList(songDictList)
		self.mainListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in self.currentSongWidgets])
		if not commandSh.plyr.currentList == 'random':
			print self.mainList.body
			os.system('clear')
		#	raise urwid.ExitMainLoop
		self.mainList = urwid.ListBox(self.mainListContent)
		self.columns = urwid.Columns([self.mainList, self.secondaryList])
		self.pile = urwid.Pile([self.columns, ("fixed", 1, self.statusDisplayOne), ("fixed", 1, self.statusDisplayTwo), ("fixed", 1, self.cmdShInterface)], 3)
		self.topFrame = urwid.Frame(self.pile)
		#loop.draw_screen()
	def createList(self, songs):
		"""Pass me a list of song dicts (as returned by getListOfSongs() and the song lookup functions) and I will create a list of songWidgets to stick in a listwalker. """
		return [songWidget(item["title"], item['location']) for item in songs]
	def scanPlaylists(self):
		"""Returns a list of plWidgets based on currently loaded playlists."""
		playlists = commandSh.currentPlaylists
		playlistWidgets = list()
		playlistWidgets.append(libraryWidget())
		for item in playlists.keys():
			playlistWidgets.append(plWidget(item))
		self.currentPLWidgets = playlistWidgets
		self.secondaryListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in self.currentPLWidgets])
		self.secondaryList = urwid.ListBox(self.secondaryListContent)
	def setStatus(self, message, songInfo=False):
		"""Pass in a two-tuple of lines to change. None does not change a line."""
		if message == "reset":
			self.showPlayback = [True, 0]
			return
		if not isinstance(message, tuple):
			raise TypeError, "setStatus only takes tuples!"
		if not message[0] == None:
			self.statusDisplayOne.original_widget.set_text(message[0])
		if not message[1] == None:
			if songInfo and self.showPlayback[0]:
				self.statusDisplayTwo.original_widget.set_text(message[1])
			elif songInfo and not self.showPlayback[0]:#This triggers when we are trying to display song info, but other info is being displayed atm.
				difference = time.clock() - self.showPlayback[1]#So we check how long this info has been there for
			#	self.statusDisplayTwo.original_widget.set_text(str(difference))
				if difference > 0.4:
					self.showPlayback = [True, 0]#if it's hung around for longer than 10 secs, put the playback info back.
					self.statusDisplayTwo.original_widget.set_text(message[1])
			else:#it isn't song info
				if not self.showPlayback[0]:
					self.statusDisplayTwo.original_widget.set_text(message[1])
				else:
					self.showPlayback = [False, time.clock()]
					self.statusDisplayTwo.original_widget.set_text(message[1])
		loop.draw_screen()
	def setTopStatus(self, message):
		pass
	def initFace(self):
		self.cmdShInterface = urwid.Filler(cmdSh("Enter a command >"))
		self.statusDisplayOne = urwid.Filler(urwid.Text("Welcome to PyPlayer!"))
		self.statusDisplayTwo = urwid.Filler(urwid.Text("Common commands: play, search, pause, next, prev. Type help for full listing, and help <command> for more help."))
		#===================================================================================================================================
	#	songList = db.getListOfSongs()
		commandSh.plyr.createRandomList()
		self.scanPlaylists()
		self.renderList()
		

		
		
	#	quit()
		

		#

	def quitTime(self):
		raise urwid.ExitMainLoop

#def moveFocus():



mainDisp = mainDisplay()
commandSh = player.commandShell(mainDisp)
db = commandSh.db
mainDisp.initFace()
mainFrame = mainDisp.topFrame
palette = [('header', 'white', 'black'), ('reveal focus', 'black', 'dark cyan', 'standout'),]
loop = urwid.MainLoop(mainFrame, palette)#, unhandled_input=moveFocus)
loop.run()

