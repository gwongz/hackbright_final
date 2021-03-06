import os 
import re 
from PIL import Image
import model 

"""Loads templates for ocr alphabet and font letters into database"""


def make_dictionary(directory):

	templates_dict = {}
	# looks for .png sample files in fonts directory and appends to dict by letter 
	for dirpath, dirnames, fnames in os.walk(directory):
	    for f in fnames:
	        if f.endswith('.png'):
	        	location = os.path.join(dirpath, f)
	        	letter = f.split('.')[0]
	        	templates_dict.setdefault(location, letter)

	return templates_dict


def get_image_info(templates_dict):
	# updates dictionary with more info for loading to db

	for key in templates_dict.iterkeys():
		img = Image.open(key)
		img = img.convert('1') 

		width = img.size[0]
		height = img.size[1]
		pixels = img.load()
		all_pixels = []
		for x in range(width):	
			for y in range(height):
				cpixel = pixels[x,y]
				all_pixels.append(cpixel)
		black_pixels = all_pixels.count(0)
		aspect_ratio = float(width)/float(height)

		current_value = templates_dict[key]
		# resets dictionary values to include black_pixels, width, height
		new_array = [current_value, black_pixels, width, height, aspect_ratio]	 
		templates_dict[key] = new_array

	return templates_dict


def load_letters(session, image_info): #image_info is a dictionary

	for key in image_info.iterkeys():
		file_url = key
		font_name = key.split('/')[1]
		letter_of_alphabet = image_info[key][0]
		value = ord(letter_of_alphabet)
		black_pixels = image_info[key][1]
		width = image_info[key][2]
		height = image_info[key][3]
		aspect_ratio = image_info[key][4]

		letter = model.Letter(value = value,
								file_url = file_url,
								font_name = font_name,
								black_pixels = black_pixels,
								width = width,
								height = height,
								aspect_ratio = aspect_ratio)

		session.add(letter)
	session.commit()


def load_ocr_letters(session, image_info):

	for key in image_info.iterkeys():
		file_url = key
		letter_of_alphabet = image_info[key][0]
		value = ord(letter_of_alphabet)
		black_pixels = image_info[key][1]
		width = image_info[key][2]
		height = image_info[key][3]
		aspect_ratio = image_info[key][4]

		ocr_letter = model.OCR_Letter(value = value,
								file_url = file_url,
								black_pixels = black_pixels,
								width = width,
								height=height,
								aspect_ratio = aspect_ratio)

		session.add(ocr_letter)
	session.commit()

def load_fonts(session, directory):

	font_files = os.listdir(directory)
	for f in font_files:
		if f.endswith('.ttf') or f.endswith('.ttc') or f.endswith('dfont'):
			fullname = f.split('.')[0]
			name = re.sub('-webfont', '', fullname)
			font = model.Font(name = name)

			session.add(font)
			session.commit()

# user fcns used in ranked_match.py  
def load_user_image(session, img_location, file_url):
	img = Image.open(img_location)
	img = img.convert('1') # converts to black and white

	width = img.size[0]
	height = img.size[1]
	aspect_ratio = float(width)/float(height)
	pixels = img.load()
	all_pixels = []
	for x in range(width):	
		for y in range(height):
			cpixel = pixels[x,y]
			all_pixels.append(cpixel)
	black_pixels = all_pixels.count(0)

	user_image = model.User_Image(file_url = file_url,
								black_pixels = black_pixels,
								width = width,
								height = height,
								aspect_ratio = aspect_ratio)

	session.add(user_image)
	session.commit()

def clear_user(session):
	user_img = model.session.query(model.User_Image).all()

	for imgfile in user_img:
		session.delete(imgfile)
		session.commit()



def main(session):
	ocr_alphabet = make_dictionary(directory='ocr_alphabet')
	ocr_info = get_image_info(ocr_alphabet)
	load_ocr_letters(session, ocr_info)

	fonts = make_dictionary(directory='font_letters')
	font_info = get_image_info(fonts)
	load_letters(session, font_info)

	load_fonts(session, directory='font_files')


if __name__ == "__main__":

	main(model.session)
	        	 


