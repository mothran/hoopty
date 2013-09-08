#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    index.wsgi
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
import feedparser
import urllib
import re
import operator
from lxml.html.clean import Cleaner
from cgi import parse_qs, escape
from os.path import abspath, dirname

# Thanks to: https://wiki.python.org/moin/EscapingHtml
html_escape_table = {
	"&": "&amp;",
	'"': "&quot;",
	"'": "&apos;",
	">": "&gt;",
	"<": "&lt;",
	"%": "",
}
def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

def application(environ, start_response):
	here = abspath(dirname(__file__))
	city_fd = open(here + '/tools/cl_cities.html', 'r')
	city_html = city_fd.read()

	default_html = """<html>
		<head>
		<title>Hoopty Search</title>
		<meta http-equiv="content-type" content="text/html;charset=UTF-8">
		</head>
		<style>
		body {
			margin:50px 0px; padding:0px;
			text-align:center;
			}
		
		table.center {
			margin-left:auto; 
			margin-right:auto;
		}
			
		Content {
			width:500px;
			margin:0px auto;
			text-align:left;
			padding:15px;
			border:1px dashed #333;
			background-color:#eee;
			}
		</style>

		<body>
		<div class="Content">

		<h1>Hoopty Search</h1>
		<h3>Sorting parameters:</h3>
		<form name="sorting" id="sorting">
			<table class="center">
				<tr>
					<td width="50%%">
						Type of item (New bikes and cycles!):
					</td>
					<td align="right">
						<select name="item_type">
							<option value="cartruck" %s>Cars and Trucks</option>
							<option value="bike" %s>Bicycles</option>
							<option value="cycle" %s>Motorcycles</option>
						</select>
					</td>
				</tr>
				<tr>
					<td width="50%%">
						Keyword (car make or model):
					</td>
					<td align="right">
						<input type="text" name="model" value="%s" /> <br/> 
					</td>
				</tr>
				<tr>
					<td>
						City:
					</td>
					<td align="right">
						%s 
					</td>
				</tr>
				<tr>
					<td>
						Dealer, owners or both?
					</td>
					<td align="middle">
						<select name="listing">
							<option value="0" %s>Owners</option>
							<option value="1" %s>Dealers</option>
							<option value="2" %s>Both</option>
						</select>
					</td>
				</tr>
				<tr>
					<td>
						Min price:
					</td>
					<td align="right">
						<input type="text" name="minprice" value="%s" /> <br/> 
					</td>
				</tr>
				<tr>
					<td>
						Max price:
					</td>
					<td align="right">
						<input type="text" name="maxprice" value="%s" /> <br/> 
					</td>
				</tr>
			</table>
			<input type="submit" name="submit" /> 
		</form>
	"""

	end_html = """
	<br>
		Please enter a keyword <b>and</b> city
	<br>
	</div>
	</body
	</html>"""

	parameters = parse_qs(environ.get('QUERY_STRING', ''))
	cars = bikes = cycles = False

	# The only parameter that is NEEDED is 'model', error out if not found
	if 'model' in parameters and 'city' in parameters and 'item_type' in parameters:
		# here use assign a string to be concated into the default html to save peoples
		# choice of dealer or not, also check for the selection.
		selected = ["","",""]
		items = ["","",""]
		listing = parameters.get('listing', [''])[0]

		item_type = parameters.get("item_type")[0]

		if item_type == "cartruck":
			items = ["selected", "", ""]
			cars = True
			if listing != "":
				if listing == "1":
					listing = "ctd"
					selected[0] =  "selected="
				elif listing == "2":
					selected[1] =  "selected"
					listing = "cta"
				else:
					listing = "cto"
					selected[2] =  "selected"
		elif item_type == "bike":
			bikes = True
			items = ["", "selected", ""]
			if listing == "1":
				listing = "bid"
				selected[0] =  " selected"
			elif listing == "2":
				selected[1] =  " selected"
				listing = "bia"
			else:
				listing = "bik"
				selected[2] =  " selected"
		elif item_type == "cycle":
			cycles = True
			items = ["", "", "selected"]
			if listing == "1":
				listing = "mcd"
				selected[0] =  " selected"
			elif listing == "2":
				selected[1] =  " selected"
				listing = "mca"
			else:
				listing = "mcy"
				selected[2] =  " selected"

		# I am grabbing the first arguement because currently none of these fields support
		# multiple params
		search_terms = parameters.get('model', [''])
		city = parameters.get('city', [''])[0]
		
		min_price = parameters.get('minprice', [''])[0]
		max_price = parameters.get('maxprice', [''])[0]
		
		# sanitize for XSS
		# I need to look over this again.
		term = html_escape(search_terms[0])
		city = html_escape(city)
		min_price = html_escape(min_price)
		max_price = html_escape(max_price)
		
		# find and replace the the city with some 'selected' html
		#	This is a dirty hack.
		city_html = city_html.replace(city+"'", city + "' selected")

		# here we input the users values back into the form, the selected[]'s are 
		# unordered because of the if else block requires that 'owners' be default.
		default_html = default_html % (items[0], items[1], items[2], term, city_html, selected[2], selected[0], selected[1], min_price, max_price)
		
		### Craigslist RSS Search URL ###
		rss_generic_link = "http://" + city + ".craigslist.org/search/%s?query=%s&minAsk=%s&maxAsk=%s&srchType=T&format=rss"
		

		term = urllib.quote(term)
		#print rss_generic_link
		#rss_link = rss_generic_link % (listing, term, urllib.quote(min_price), urllib.quote(max_price))
		
		# we might want to check the .boozo bit and if the RSS url is wrong.
		rss_link = rss_generic_link % (listing, term, min_price, max_price)

		# sanitize the html tags besides the listed ones:
		cleaner = Cleaner(remove_unknown_tags=False, allow_tags=['img', 'p', 'a', 'b', 'em', 'div']);
		
		database = []
		listings = feedparser.parse(rss_link)
		
		# loop through the listings and grab the critical data
		for listing in listings.entries:
			title = listing["title"]
			url = listing["link"]
			text = cleaner.clean_html(listing["description"])

			# search the listings for years
			year = re.search("(19|20)\d\d.", title)
			if year is not None:
				year = year.group(0)
			else:
				#check for 2 digit years
				year = re.search("([ ]|^|')[4-9][0-9](?!\d)", title)
				if year is not None:
					year = year.group(0)
					if len(year) > 2:
						year = "19" + year[1:]
					else:
						year = "19" + year
				else:
					# finally try checking the body
					year = re.search("(19[0-9]{2}|20[0-9]{2})", text)
					if year is not None:
						year = year.group(0)
					else:
						year = "?"

			# ITEMDEPENDENT
			if bikes:
				regex_str = "(?<!\d)\d\d( cm|cm|\")"
				height = re.search(regex_str, text, re.IGNORECASE)
				if height is not None:
					height = height.group(0)
				else:
					# check the title for height
					height = re.search(regex_str, title, re.IGNORECASE)
					if height is not None:
						height = height.group(0)
					else:
						height = ""
				# convert and standardize the output.
				if height is not "":
					height = height.lstrip()
					if height[-1:] == "\"":
						height = height[:2] + "\""
						# Removed the conversion because mountain bikes are in inches,
						# I just let the users see what the posters put up.
						# height = str(int(height[:2]) * 2.54) + " cm"
					else:
						height = height[:2] + " cm"
				miles = height
			else:
				# grab the mileage.
				miles = re.search("(([1-9]|[ ]|[\n])[0-9]{2}(k|K|XX|XXX|,XXX|(\d|,)[0-9]XX|,000|.000|000|thousand miles|kms| kms| km)|[0-9]{3},[0-9]{3})", text, re.IGNORECASE)
				if miles is not None:
					miles = miles.group(0)
					# your welcome canada and the rest of the world
					# do not include 'k' here because it will people saying 100k miles
					kilo = re.search('(km|kms)', miles, re.IGNORECASE)
					if kilo is not None:
						miles = miles[:3] + ",000 km" 
					# Make the output standardized.
					else:
						miles = miles[:3] + ",000"
				else:
					miles = ""

			# last n chars after the last '$' of title are price.
			price = title.split("$")
			if len(price) < 2:
				price = "noprice"
			else:
				try:
					price = int(price[-1])
				except ValueError:
					print "hoopty ERROR: ",
					print price + environ.get('QUERY_STRING', '')
			
			database.append([url, title, text, year, price, miles])
				
		tmp_html = """<br>
		<h3>Listings: </h3>
		<table border="0" width="500" class="center">
			<tr>
				<td style="width:100px">
					<b>Year</b>
				</td>
				<td style="width:100px">
					<b>Price</b>
				</td>
				<td style="width:100px">
					<b>%s</b>
				</td>
				<td></td>
			</tr>
		</table>
		<table border="1" width="500" class="center">\n"""

		# ITEMDEPENDENT
		if bikes:
			tmp_html = tmp_html % ("Frame height")
		else:
			tmp_html = tmp_html % ("Miles/Kilometers")

		output = "%s%s" % (default_html, tmp_html)

		# create two differently sorted databases
		database = sorted(database, key=operator.itemgetter(3, 4))
		
		# this is ugly and nested but it performs the same actions as two selects.
		# then appends the data to 'output' in table form.
		#	0	  1		2	  3		4		5
		# [url, title, text, year, price, miles]
		saved_year = ""
		for entry in database:
			if saved_year != entry[3]:
				output += "<tr>\n<td style=\"width:100px\">\n" + entry[3].encode('ascii') + "</td>\n<td>\n"
				output += "<table border=\"0\">"
				for set in database:
					# if the years are the same.
					if set[3] == entry[3]:
						output += "<tr><td width=\"100px\">"
						out_price = str(set[4])
						if out_price == "noprice":
							output += "<a href=\'" + set[0].encode('ascii') + "\'>" + str(set[4]) + "</a> "
						else:
							output += "<a href=\'" + set[0].encode('ascii') + "\'>$" + str(set[4]) + "</a> "
						if set[5] is not None:
							output += "</td><td width=\"100px\"> "
							output += set[5].encode('ascii')
						output += "</td></tr>"
				output += "</table>	\n</td>\n</tr>\n"
			saved_year = entry[3]
		
		# clean up and create the return request. 
		output += "\n<br>\n</div>\n</body>\n</html>"
		status = '200 OK'
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(output)))]
		start_response(status, response_headers)
		return [output]
	elif 'model' in parameters and 'city' not in parameters:
		status = '200 OK'
		default_html = default_html % ("", "", "", "", city_html, "", "", "", "", "5000")

		default_html += end_html
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(default_html)))]
		start_response(status, response_headers)
		return [default_html]
	else:
		status = '200 OK'
		default_html = default_html % ("", "", "", "", city_html, "", "", "", "", "5000")
		default_html += end_html
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(default_html)))]
		start_response(status, response_headers)
		return [default_html]
