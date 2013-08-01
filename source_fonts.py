import urllib
import os.path
import re
import csv
import re

def source_data(path):
	"""Returns list of string urls from scraper csv file"""

	
	with open (path) as csvfile:
		fonts = csv.reader(csvfile, delimiter=',', quotechar=',')
		font_urls = []
		# match = re.search(r'\Ahttp', fonts)
		for row in fonts:
			row = " ".join(row).strip(',')
			if 'http' not in row:
				continue
			else:
				font_urls.append(row)
		return font_urls # list of strings

# test
fonts = source_data("/Users/gwongz/src/hackbright/project/font/font/file")	

for font in fonts:
	print font, "\n"

def download_fonts(font_urls):
	"""Downloads ttf files and stores in local directory"""
	
	root = "/Users/gwongz/src/hackbright/project/font_files/"
	for url in font_urls:
		# renames downloaded file
		name = url.split("=")[-1] 
		pattern = re.search(".[\w]+", name)
		name = pattern.group()

		# print url, name, root
		# retrieves url and stores in specified directory as name
		urllib.urlretrieve(url, os.path.join(root, name))

download_fonts(fonts)



 

# use urlretrieve to download vs. urllopen to read
# source = urllib.urlopen("http://www.dafont.com/img/dafont.png")
# output = open("file01.png","wb")
# output.write(source.read())
# output.close()
# root = "/Users/gwongz/src/hackbright/project/font_files"
# name = "cellos.ttf"
# url = "http://img.dafont.com/dl/?f=cellos_script"

