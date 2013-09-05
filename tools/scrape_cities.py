#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    scrape_cities.py
#
#    Copyright 2013 W. Parker Thompson <w.parker.thompson@gmail.com>
#		
#    This file is part of hooptysearch.
#
#    hooptysearch is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    hooptysearch is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with hooptysearch.  If not, see <http://www.gnu.org/licenses/>.

import sys
import urllib2
from bs4 import BeautifulSoup

# grab the HTML and soup it
req = urllib2.Request("http://craigslist.org")
response = urllib2.urlopen(req)
html = response.read()
soup = BeautifulSoup(html)

# This grabs each div of a region, div[0] is USA
nations = soup.find_all('div', attrs={'class': 'colmask'})

options = "\t\t\t<option value='%s'>%s</option>\n"
output = ""

for nation in nations:
	states = nation.find_all('ul')
	raw_states = nation.find_all('h4')
	
	# remove the tags from the states names
	states_names = []
	for state in raw_states:
		states_names.append(state.string)

	# create a dict of the names and the html of each state
	states_dict = dict(zip(states_names, states))

	# loop thru and extract the links
	for name, html in states_dict.iteritems():
		output = output + options % ("", "--" + name + "--")
		#print "\n\n" + name
		links = html.find_all('li')
		for link in links:
			city = link.a.string
			#print "\t" + city + "\t\t",
			#print link.a.get('href')
			url = link.a.get('href')[7:].split(".")[0]

			output = output + options % (url, city)

output = "<select name='city' id='city' form='sorting'>\n\t\t\t<option value=''>SELECT A CITY</option>\n" + output + "</select>"
fd = open('cl_cities.html', 'w')
fd.write(output)