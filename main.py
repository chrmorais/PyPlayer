#!/usr/bin/python2.6

# encoding: utf-8
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

class myPile(urwid.Pile):
	pass

class songWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label, location):
		self.__super.__init__(label)
		self.location = location
		urwid.connect_signal(obj=self, name='click', callback=commandSh.plyr.playLocation, user_arg=self.location)
class plWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label):
		self.__super.__init__(label)
		urwid.connect_signal(obj=self, name='click', callback=commandSh.plyr.playAList, user_arg=self.label)

class libraryWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label='Library'):
		self.__super.__init__(label)
		urwid.connect_signal(obj=self, name='click', callback=commandSh.plyr.playRandom)
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
			try:
				mainDisp.pile.set_focus(mainDisp.currentFocus + 1)
				mainDisp.currentFocus +=1
			except AssertionError:
				mainDisp.pile.set_focus(0)
		self.__super.keypress(size, key)

	

class mainDisplay(object):
	def __init__(self):
		self.showPlayback = [True, 0]#Set this to false to display non-playback related info on the second display line. WHen set to false, you must set the second value to the current CPU time
		self.currentFocus = 5
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
		songList = db.getListOfSongs()
		songListWidgets = list()
		for item in songList:
			songListWidgets.append(songWidget(item["title"], item['location']))
		#
		playlists = commandSh.currentPlaylists
		playlistWidgets = list()
		playlistWidgets.append(libraryWidget())
		#
		self.cmdShInterface = urwid.Filler(cmdSh("Enter a command >"))
		self.statusDisplayOne = urwid.Filler(urwid.Text("Welcome to PyPlayer!"))
		self.statusDisplayTwo = urwid.Filler(urwid.Text("Common commands: play, search, pause, next, prev. Type help for full listing, and help <command> for more help."))
		for item in playlists.keys():
			playlistWidgets.append(plWidget(item))
		
		self.mainListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in songListWidgets])
		self.plListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in playlistWidgets])
		self.mainList = urwid.ListBox(self.mainListContent)
		self.plList = urwid.ListBox(self.plListContent)
		self.columns = urwid.Columns([self.mainList, self.plList])
		#
		self.pile = urwid.Pile([self.columns, ("fixed", 1, self.statusDisplayOne), ("fixed", 1, self.statusDisplayTwo), ("fixed", 1, self.cmdShInterface)], 3)
		self.topFrame = urwid.Frame(self.pile)
	def quitTime(self):
		raise urwid.ExitMainLoop





mainDisp = mainDisplay()
commandSh = player.commandShell(mainDisp)
db = commandSh.db
mainDisp.initFace()
mainFrame = mainDisp.topFrame
palette = [('header', 'white', 'black'), ('reveal focus', 'black', 'dark cyan', 'standout'),]
loop = urwid.MainLoop(mainFrame, palette)
loop.run()

