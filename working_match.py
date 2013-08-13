import os
import re
import numpy as np 
from PIL import Image, ImageOps
import SimpleCV as cv

import model 
from seed import load_user_image, clear_user
from process_images import crop_at_bounds, make_constrained



"""Runs xor on each letter of alphabet. Takes the longest and then matches to font"""

def process_user_image(directory):

	crop_at_bounds(directory)
	make_constrained(directory)

	segments = os.listdir(directory)
	if '.DS_Store' in segments:
		segments.remove('.DS_Store')

	session = model.session
	clear_user(session)
	
	for imgfile in segments:
		location = os.path.abspath(os.path.join(directory, imgfile))
		file_url = os.path.join(directory, imgfile)
		name = str(file_url)
		load_user_image(session, location, file_url)


def get_letter(user_dir, ocr_dir):

	ocr_dict = {}
	segments = os.listdir(user_dir)
	if '.DS_Store' in segments:
		segments.remove('.DS_Store')
		segments = sorted_nicely(segments)

	ocr_alphabet = []
	for dirpath, dirnames, fnames in os.walk(ocr_dir):
	    	for f in fnames:
	       		if f.endswith('.png'):
	       			ocr_alphabet.append(f)

	print "These are the user segments. They should be in alphanumeric order: ", segments
	print "These are the templates. They should be in alphabetic order: ", ocr_alphabet


	for imgfile in segments:

		img_url = os.path.abspath(os.path.join(user_dir, imgfile))	
		user_img = img_url # 
		# deterine whether to check upper or lower[?]

		count = 0 
		for letter in ocr_alphabet:

			if count > 26:
				letter_url = os.path.abspath(os.path.join(ocr_dir+'/upper', letter))

			else:
				letter_url = os.path.abspath(os.path.join(ocr_dir+'/lower', letter))
			
			print "OCR template url: ", letter_url
			print "OCR template letter", letter 

			letter = letter_url
			# print "This is the template size: ", letter.size

			xor_of_images = difference_of_images(user_img, letter)
			# print "User img mode", user_img.mode
			# print "Letter img mode", letter.mode
			print "This is xor_of_images", xor_of_images

			if img_url not in ocr_dict.keys():
				ocr_dict.setdefault(img_url, [xor_of_images])
			
			else:
				ocr_dict[img_url].append(xor_of_images)				


			count +=1
		# only continue if there is a bad match result?
	return ocr_dict # a dictionary with imgname as key and 52 percentages 

# only works when images are identically sized 
def difference_of_images(user_img, template_img): # passed in as SimpleCV images

	user = cv.Image(user_img).binarize()
	user_matrix = user.getNumpy().flatten()

	template = cv.Image(template_img).binarize()
	template_matrix = template.getNumpy().flatten()

	# print "User matrix", user_matrix
	# print 'Template matrix', template_matrix

	# performs xor match 
	difference = [i^j for i,j in zip(user_matrix, template_matrix)]	
	difference2 = [i^j for i,j in zip(template_matrix, user_matrix)]
	# print "xor of difference1", difference
	# print "xor of difference2", difference2

	# # however many times 0 appears in the list
	diff = difference.count(255)
	# print "Count of difference in pixel", diff

	diff2 = difference2.count(255)
	# print "Count of difference in pixel", diff2

	total_diff = diff + diff2
	xor_value = total_diff/float(len(user_matrix)+len(template_matrix))

	print "Percentage of difference between the two images:", xor_value*100
	return xor_value
	# 1 means complete difference; 0 means complete same


def identify_letter(ocr_data):

	ocr_match_dict = {}

	for key in ocr_data.iterkeys():
		min_value = min(ocr_data[key]) # finds lowest % diff from list, 0 is a perfect match 
		idx_pos = ocr_data[key].index(min_value)
		print min_value, idx_pos
		if idx_pos < 26:
			letter = chr(idx_pos + 97) # if lower 
		else:
			letter = chr(idx_pos + 39) # if upper 
		ocr_match_dict.setdefault(key, [min_value, idx_pos, letter])

	return ocr_match_dict

def get_letters_to_process(user_dir, ocr_match_dict):

	segments = os.listdir(user_dir)
	if '.DS_Store' in segments:
		segments.remove('.DS_Store')

	segments = sorted_nicely(segments)
	letters_to_process = []

	# output = ""
	for imgfile in segments:

		letter_tuple = []
		img_url = os.path.abspath(os.path.join(user_dir, imgfile))	
		letter = ocr_match_dict[img_url][2]

		letter_tuple.append(img_url)
		letter_tuple.append(letter)


		letters_to_process.append(letter_tuple)

		# letters_to_process.append(img_url)
		# letters_to_process.append(letter)
		# output += letter

	# print "It looks like your image says: %s" % (output) 
	return letters_to_process


def match_font(process_letter_list):

	letters = []
	user_urls = []

	for item in process_letter_list:
		user_urls.append(item[0])
		letters.append(item[1])

	font_table = {}
	n=0
	while n < len(letters):
		# print "This is n at the top: ", n 
		user_img = user_urls[n]
		

		relative = user_img.split('/')[-2:]
		relative_url = os.path.join(relative[0], relative[1])
		print "This is relative_url", relative_url

		letter = letters[n] # gets you one letter
		value = ord(letter)



		user_black_pixels_tuple = model.session.query(model.User_Image.black_pixels).filter(model.User_Image.file_url==relative_url)
		
		print "This is userblack pixels tuple", user_black_pixels_tuple 
		user_black_pixels = user_black_pixels_tuple[0][0]
		print "This is the number of black pixels in user image:", user_black_pixels

		fonts = model.session.query(model.Letter.file_url).filter(model.Letter.value == value).all()

		for i in range (len(fonts)):
			font_location = str(fonts[i][0])
			
			font_black_pixels_tuple = model.session.query(model.Letter.black_pixels).filter(model.Letter.file_url == font_location)
			font_black_pixels = font_black_pixels_tuple[0][0]

			black_pixels_min = user_black_pixels - 22.5 # range of 5% 
			black_pixels_max = user_black_pixels + 22.5 

			if font_black_pixels > black_pixels_min and font_black_pixels < black_pixels_max:
			# only xor if value of black pixels within range 
				font_img = font_location
				font_xor = difference_of_images(user_img, font_img)

				if font_xor <= 0.05:
					font_name = model.session.query(model.Letter.font_name).filter(model.Letter.file_url==font_location).one()
				# print "This is the fontname: ", font_name

					if font_name not in font_table.keys():
						font_table.setdefault(font_name, [font_xor])

					else:
						font_table[font_name].append(font_xor)

		# if any of the items in font table has a value that exceeds 5: break 

		n+=1
		# print 'This is n at the bottom: ', n 
	return font_table


def rank_fonts(font_table):
	for key, value in font_table.items():
		print "Ranking fonts...\n"
		print "Font, rate of difference:", key, value, '\n\n\n'  

	least_difference = min(font_table.iteritems(), key=lambda (k,v): np.mean(v))
	# print "This is the font with the least_difference with iteritems: ", least_difference
	font = least_difference[0][0]

	return "It looks like this is the font you're looking for: %s" % (font) 



	


def sorted_nicely(list):
    """ Sorts the given iterable in the way that is expected"""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(list, key = alphanum_key)


def main():
	# process_user_image('user_image') # commits user images to database, run 
	user_dir = 'user_image'
	ocr_dir = 'ocr_alphabet/Arial'

	ocr_data = get_letter(user_dir, ocr_dir)
	# # returns dictionary that has as values: list of ALL xor matches per segment for lowercase
	print "This is the ocr_data", ocr_data.items()
	# can cut run time by breaking after five keys have been appended to dictionary

	ocr_match_dict = identify_letter(ocr_data)

	print "This is the ocr_match_dict", ocr_match_dict.items()
	# # returns dictionary that has as values: list of smallest xor difference 
	# # value, idx position in img_data list, letter_of_alphabet (idx + 97 or idx + 65) 

	
	letters_to_process = get_letters_to_process(user_dir, ocr_match_dict)
	# can cut run time by only appending good matches to letter to process list
	print letters_to_process


	font_table = match_font(letters_to_process)
	print font_table.items()
	
	result = rank_fonts(font_table)
	print result 

	# return result 




if __name__ == "__main__":
	main()

	
	
