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
		<meta name="description" content="HooptySearch - A clean better way to view and search craigslist car and truck listings">
		<META NAME="ROBOTS" CONTENT="INDEX, FOLLOW">
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
		<script>
			(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
			(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
			m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
			})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

			ga('create', 'UA-43779340-1', 'hooptysearch.com');
			ga('send', 'pageview');
		</script>

		<body>
		<div class=\"Content\">

		<h1>Hoopty Search</h1>
		<h3>Sorting parameters:</h3>
		<form name=\"sorting\" id=\"sorting\">
			<table class=\"center\">
				<tr>
					<td width=\"50%%\">
						Keyword:
					</td>
					<td align=\"right\">
						<input type=\"text\" name=\"model\" value=\"%s\" /> <br/> 
					</td>
				</tr>
				<tr>
					<td>
						City:
					</td>
					<td align=\"right\">
						%s 
					</td>
				</tr>
				<tr>
					<td>
						Dealer, owners or both?
					</td>
					<td align=\"middle\">
						<select name=\"listing\">
							<option value=\"0\"%s>Owners</option>
							<option value=\"1\"%s>Dealers</option>
							<option value=\"2\"%s>Both</option>
						</select>
					</td>
				</tr>
				<tr>
					<td>
						Min price:
					</td>
					<td align=\"right\">
						<input type=\"text\" name=\"minprice\" value=\"%s\" /> <br/> 
					</td>
				</tr>
				<tr>
					<td>
						Max price:
					</td>
					<td align=\"right\">
						<input type=\"text\" name=\"maxprice\" value=\"%s\" /> <br/> 
					</td>
				</tr>
			</table>
			<input type=\"submit\" name=\"submit\" /> 
		</form>"""

	parameters = parse_qs(environ.get('QUERY_STRING', ''))

	# The only parameter that is NEEDED is 'model', error out if not found
	if 'model' in parameters and 'city' in parameters:
		# here use assign a string to be concated into the default html to save peoples
		# choice of dealer or not, also check for the selection.
		selected = ["","",""]
		listing = parameters.get('listing', [''])[0]
		if listing != "":
			if listing == "1":
				listing = "ctd"
				selected[0] =  " selected=\"selected\""
			elif listing == "2":
				selected[1] =  " selected=\"selected\""
				listing = "cta"
			else:
				listing = "cto"
				selected[2] =  " selected=\"selected\""
		
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
		default_html = default_html % (term, city_html, selected[2], selected[0], selected[1], min_price, max_price)
		
		### Craigslist RSS Search URL ###
		rss_generic_link = "http://" + city + ".craigslist.org/search/%s?query=%s&minAsk=%s&maxAsk=%s&srchType=T&format=rss"
		

		term = urllib.quote(term)
		#print rss_generic_link
		#rss_link = rss_generic_link % (listing, term, urllib.quote(min_price), urllib.quote(max_price))
		print rss_generic_link
		
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
				year = re.search("([ ]|^)[4-9][0-9]", title)
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
			# grab the mileage.
			miles = re.search("(([1-9]|[ ])[0-9]{2}(k|K|XX|XXX|,XXX|(\d|,)[0-9]XX|,000|000|thousand miles|kms| kms| km)|[0-9]{6}|[0-9]{3},[0-9]{3})", text, re.IGNORECASE)
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
				mile = ""

			# last n chars after the last '$' of title are price.
			price = title.split("$")
			if len(price) < 2:
				price = "noprice"
			else:
				price = "$" + price[-1]
			
			database.append([url, title, text, year, price, miles])
				
		output = default_html + "<br>\n<h3>Listings: </h3>\n"
		
		# build a header for the listings with labled columbs
		output += """
		<table border=\"0\" width=\"500\" class=\"center\">
		<tr>
			<td style=\"width:100px\">
				<b>Year</b>
			</td>
			<td style=\"width:100px\">
				<b>Price</b>
			</td>
			<td style=\"width:100px\">
				<b>Miles/Kilometers</b>
			</td>
			<td></td>
		</tr>
	</table>"""
		
		output += "<table border=\"1\" width=\"500\" class=\"center\">\n"
		
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
						output += "<a href=\'" + set[0].encode('ascii') + "\'>" + set[4].encode('ascii') + "</a> "
						if set[5] is not None:
							output += "</td><td width=\"100px\"> "
							output += set[5].encode('ascii')
						output += "</td></tr>"
				output += "</table>	\n</td>\n</tr>\n"
			saved_year = entry[3]
		
		# clean up and create the return request. 
		output += "\n<br>\n<text>To learn more check out <a href=\"https://github.com/mothran/hoopty\">https://github.com/mothran/hoopty</a></text></body>\n</div>\n</html>"
		status = '200 OK'
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(output)))]
		start_response(status, response_headers)
		return [output]
	elif 'model' in parameters and 'city' not in parameters:
		status = '200 OK'
		default_html = default_html % ("", city_html, "", "", "", "", "5000")
		default_html += "\n<br><br>\nPlease enter a keyword <b>and</b> city<br><text>To learn more check out <a href=\"https://github.com/mothran/hoopty\">https://github.com/mothran/hoopty</a></text>\n</body>\n</div>\n</html>"
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(default_html)))]
		start_response(status, response_headers)
		return [default_html]
	else:
		status = '200 OK'
		default_html = default_html % ("", city_html, "", "", "", "", "5000")
		default_html += "\n<br><br>\n<text>Please enter a keyword and city</text><br><text>To learn more check out <a href=\"https://github.com/mothran/hoopty\">https://github.com/mothran/hoopty</a></text>\n</body>\n</div>\n</html>"
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(default_html)))]
		start_response(status, response_headers)
		return [default_html]
