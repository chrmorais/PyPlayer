#!/usr/bin/python2.6

# encoding: utf-8
"""
main.py

"""
import sys, os
import urwid
import player
import database

class songWidget(urwid.Button):
	button_left = urwid.widget.Text('')
	button_right = urwid.widget.Text('')
	def __init__(self, label, location):
		self.__super.__init__(label)
		self.location = location
		urwid.connect_signal(obj=self, name='click', callback=cmdSh.plyr.playLocation, user_arg=self.location)
	
def main():
	loop = urwid.MainLoop(topFrame, palette)
	loop.run()

palette = [('header', 'white', 'black'),
	('reveal focus', 'black', 'dark cyan', 'standout'),]
cmdShInterface = urwid.Edit("Enter a command >")
cmdSh = player.commandShell()
db = cmdSh.db
songList = db.getListOfSongs()
songListWidgets = list()
for item in songList:
	songListWidgets.append(songWidget(item["title"], item['location']))
mainListContent = urwid.SimpleListWalker([
	urwid.AttrMap(w, None, 'reveal focus') for w in songListWidgets])
mainList = urwid.ListBox(mainListContent)
topFrame = urwid.Frame(mainList)




if __name__ == "__main__":
	main()
