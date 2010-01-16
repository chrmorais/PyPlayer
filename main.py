#!/usr/bin/python2.6

# encoding: utf-8
"""
main.py

Created by Mitchell Ferguson on 2009-12-29.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""
import sys, os
import urwid
import player
import database




def main():
	cmdShInterface = urwid.Edit("Enter a command >")
	cmdSh = player.commandShell()
	db = cmdSh.db
	songList = db.getListOfSongs()
	songListWidgets = list()
	for item in songList:
		songListWidgets.append(urwid.Text(item["title"]))
	mainListContent = urwid.SimpleListWalker([
		urwid.AttrMap(w, None, 'reveal focus') for w in songListWidgets])
	mainList = urwid.ListBox(mainListContent)
	topFrame = urwid.Frame(mainList)
	loop = urwid.MainLoop(topFrame)
	loop.run()
if __name__ == "__main__":
	main()
