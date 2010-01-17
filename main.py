#!/usr/bin/python2.6

# encoding: utf-8
"""
main.py

"""
import sys, os
import urwid
import player
import database
cmdSh = player.commandShell()
db = cmdSh.db
palette = [('header', 'white', 'black'),
	('reveal focus', 'black', 'dark cyan', 'standout'),]
class songWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label, location):
		self.__super.__init__(label)
		self.location = location
		urwid.connect_signal(obj=self, name='click', callback=cmdSh.plyr.playLocation, user_arg=self.location)
class plWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label, plName):
		self.__super.__init__(label)
		self.plName = plName
		urwid.connect_signal(obj=self, name='click', callback=cmdSh.plyr.playList, user_arg=self.plName)

class libraryWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label='Library'):
		self.__super.__init__(label)
		urwid.connect_signal(obj=self, name='click', callback=cmdSh.plyr.playRandom)
	
def main(display):
	loop = urwid.MainLoop(display, palette)
	loop.run()


class mainDisplay(object):
	def __init__(self):

		cmdShInterface = urwid.Edit("Enter a command >")

		songList = db.getListOfSongs()
		songListWidgets = list()
		songListWidgets.append(libraryWidget())
		for item in songList:
			songListWidgets.append(songWidget(item["title"], item['location']))
		playlists = cmdSh.currentPlaylists
		print playlists
		playlistWidgets = list()
		for item in playlists.keys():
			playlistWidgets.append(plWidget(item))


		mainListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in songListWidgets])
		plListContent = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in playlistWidgets])
		mainList = urwid.ListBox(mainListContent)
		plList = urwid.ListBox(plListContent)
		columns = urwid.Columns([mainList, plList])
		self.topFrame = urwid.Frame(columns)




if __name__ == "__main__":
	mainDisp = mainDisplay()
	mainFrame = mainDisp.topFrame
	main(mainFrame)
