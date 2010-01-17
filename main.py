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
def docstringDisplayer(text,):
	mainDisp.setStatus(text)
class cmdSh(urwid.Edit):
#	def __init__(self, caption="", edit_text="", multiline=False,
 #           align=LEFT, wrap=SPACE, allow_tab=False,
  #          edit_pos=None, layout=None):
			
	def keypress(self, size, key):
		docstringDisplayer(self.get_edit_text())
		if key == "enter":
			commandSh.onecmd(self.get_edit_text())
			self.set_edit_text('')
			return
		self.__super.keypress(size, key)
		loop.draw_screen()
	
		
	


class mainDisplay(object):
	def __init__(self):
		pass
	def setStatus(self, message):
		""""""
		self.statusDisplay.original_widget.set_text(message)
		loop.draw_screen()
		
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
		self.statusDisplay = urwid.Filler(urwid.Text("Welcome to PyPlayer\nCommon commands: play, search, pause, next, prev. Type help for full listing, and help <command> for more help."))
		for item in playlists.keys():
			playlistWidgets.append(plWidget(item))
		
		self.mainListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in songListWidgets])
		self.plListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in playlistWidgets])
		self.mainList = urwid.ListBox(self.mainListContent)
		self.plList = urwid.ListBox(self.plListContent)
		self.columns = urwid.Columns([self.mainList, self.plList])
		#
		self.pile = urwid.Pile([self.columns, ("fixed", 2, self.statusDisplay), ("fixed", 1, self.cmdShInterface)])
		self.topFrame = urwid.Frame(self.pile)
	def quitTime(self):
		raise urwid.ExitMainLoop





mainDisp = mainDisplay()
commandSh = player.commandShell(mainDisp)
db = commandSh.db
mainDisp.initFace()
mainFrame = mainDisp.topFrame

palette = [('header', 'white', 'black'), ('reveal focus', 'black', 'dark cyan', 'standout'),]
def main(display):
	global loop
	loop = urwid.MainLoop(display, palette)
	loop.run()


if __name__ == "__main__":
	main(mainFrame)
