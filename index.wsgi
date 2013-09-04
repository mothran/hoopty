#!/usr/local/bin/python

import feedparser
import urllib
import re
import operator
from lxml.html.clean import Cleaner
from cgi import parse_qs, escape


def application(environ, start_response):

	default_html = """<html>
		<head>
		<title>Hoopty Search</title>
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
		<div class=\"Content\">

		<h1>Hoopty Search</h1>
		<h3>Sorting parameters:</h3>
		<form name=\"sorting\">
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
						<input type=\"text\" name=\"city\" value=\"%s\" /> <br/> 
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
		
		# sanitize for XSS and '%'
		# I need to look over this again.
		term = escape(search_terms[0], True).strip("%")
		city = escape(city, True).strip("%")
		min_price = escape(min_price, True).strip("%")
		max_price = escape(max_price, True).strip("%")
		
		# here we input the users values back into the form, the selected[]'s are 
		# unordered because of the if else block requires that 'owners' be default.
		default_html = default_html % (term, city, selected[2], selected[0], selected[1], min_price, max_price)
		
		### Craigslist RSS Search URL ###
		rss_generic_link = "http://" + urllib.quote(city) + ".craigslist.org/search/%s?query=%s&minAsk=%s&maxAsk=%s&srchType=T&format=rss"
		

		term = urllib.quote(term)
		#print rss_generic_link
		#rss_link = rss_generic_link % (listing, term, urllib.quote(min_price), urllib.quote(max_price))
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
				year = re.search("([ ]|^)[2-9][0-9]", title)
				if year is not None:
					year = year.group(0)
					if len(year) > 2:
						year = "19" + year[1:]
					else:
						year = "19" + year
				else:
					year = "?"
			# grab the mileage.
			miles = re.search("(([1-9]|[ ])[0-9][0-9](k|K|xx|xxx|XXX|,XXX|(\d|,)[0-9]xx|(\d|,)[0-9]XX|,000|000|thousand miles)|[0-9]{6})", text)
			if miles is not None:
				miles = miles.group(0)
				# make the output huamn readable.
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
		output += "\n</body>\n</div>\n</html>"
		status = '200 OK'
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(output)))]
		start_response(status, response_headers)
		return [output]
	elif 'model' in parameters and 'city' not in parameters:
		status = '200 OK'
		default_html = default_html % ("", "", "", "", "", "", "5000")
		default_html += "\n<br><br>\nPlease enter a keyword <b>and</b> city<br>\n</body>\n</div>\n</html>"
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(default_html)))]
		start_response(status, response_headers)
		return [default_html]
	else:
		status = '200 OK'
		default_html = default_html % ("", "", "", "", "", "", "5000")
		default_html += "\n<br><br>\n<text>Please enter a keyword and city</text><br>\n</body>\n</div>\n</html>"
		response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(default_html)))]
		start_response(status, response_headers)
		return [default_html]