#! /usr/bin/env python
# -*- coding: latin-1 -*-

import sys
from math import pow, sqrt, trunc
from random import randint, randrange
from xml.etree import ElementTree
 
class SectorInits:
	"""Contains the basic data for creating a sector"""
	type = ''
	mins = {}
	maxs = {}
	nebula_rad = 0

# Constants
# The numbers below need to be balanced against each other -- especially 
# min_system_dist must not be too high or the program will endlessly loop
# trying to find a location that is far enough from all surrounding systems.
# Map distance units
map_width = 60
map_height = 45
start_exit_height_range = 20
min_system_dist = 6  
neighbour_notice = 14
nebula_rad_friendly = 10
nebula_rad_neutral  = 16
nebula_rad_hostile  = 13
# Numbers of systems in sector
min_friendly = {'station': 2, 'distress': 2, 'enemy':  4, 'neutral':  8, 'empty': 4}
max_friendly = {'station': 4, 'distress': 4, 'enemy':  8, 'neutral': 12, 'empty': 7}
min_neutral  = {'station': 2, 'distress': 3, 'enemy':  5, 'neutral':  7, 'empty': 3}
max_neutral  = {'station': 3, 'distress': 5, 'enemy':  9, 'neutral': 12, 'empty': 6}
min_hostile  = {'station': 1, 'distress': 2, 'enemy':  6, 'neutral':  6, 'empty': 5}
max_hostile  = {'station': 3, 'distress': 3, 'enemy': 10, 'neutral': 10, 'empty': 9}
danger_chances  = {'start':  0, 'exit':  0, 'dummy':  0, 'station':  0, 'distress':  20, 'enemy': 10, 'neutral': 10, 'empty': 30}
# Percentages
nebula_chance_home  = 40 
nebula_chance_other = 60
nebula_chance_add_neutral = 10
asteroid_chance = 60 # Other possibility is solar flare

# Display stuff
syst_colors_rgb = {'start': "#00FF00", 'exit': "#00FF00", 'dummy': "#000000", 'station': "#0000FF", 'distress': "#FF7F00", 'enemy': "#FF0000", 'neutral': "#00FFFF", 'empty': "#9F9F9F", 'unknown': "#7F7F7F"}
other_colors_rgb = {'nebula': "#3F003F", 'solar_flare': "#FFFF00", 'asteroid_field': "#BF7F3F", 'plasma_storm': "#7FFFFF", 'nebula_center': "#FF7FFF"}
nebula_opacity = 1
danger_opacity = 0.5

# The two svg trees for the referee map and the team map
referoot = ElementTree.Element('svg', xmlns='http://www.w3.org/2000/svg') 
teamroot = ElementTree.Element('svg', xmlns='http://www.w3.org/2000/svg') 

# Format of items in systemlist: [x, y, system_type, [list_of_notes] ]
# system_type has one of: ['start', 'exit', \
#	'station', 'distress', 'enemy', 'neutral', 'empty', \
#	'dummy'] 
# list_of_notes may have some of: ['station_near_x_y', 'distress_near_x_y', \
#	'danger', 'plasma_storm', 'asteroid_field', 'solar_flare', \
#	'in_nebula', 
#	'nebula_center']
# dummy is for nebula_center and other "systems" that don't really exist
systemlist = []

# Must have one of 'friendly', 'neutral', or 'hostile'
# May have anything, following have effect:
#  'home'
sector_keywords = ['neutral'] 
sector_init_data = SectorInits()


def do_setup():
	if 'friendly' in sector_keywords:
		sector_init_data.type = 'friendly' # Yeah, dumb
		sector_init_data.mins = min_friendly
		sector_init_data.maxs = max_friendly
		sector_init_data.nebula_rad = nebula_rad_friendly
	elif 'neutral' in sector_keywords:
		sector_init_data.type = 'neutral'
		sector_init_data.mins = min_neutral
		sector_init_data.maxs = max_neutral
		sector_init_data.nebula_rad = nebula_rad_neutral
	elif 'hostile' in sector_keywords:
		sector_init_data.type = 'hostile'
		sector_init_data.mins = min_hostile
		sector_init_data.maxs = max_hostile
		sector_init_data.nebula_rad = nebula_rad_hostile

def distance(x1,y1,x2,y2):
	return sqrt(pow(x1-x2,2)+pow(y1-y2,2))


#	Output functions
# Note: Python does not allow hyphens as keywords (like "stroke-width")
# so we use underscores and replace them once the svg is a string. 
def create_svg_maps():
	ssm = 20 # svg size multiplier
	eed = 25 # extra edge distance
	scr = 5 # system circle radius
	scsw = 2 # system circle stroke width
	dssl = 20 # danger square side length
	cas = 4 # coordinate arrow size
	smaw = map_width * ssm # svg map area width
	smah = map_height * ssm # svg map area height
	# Fill out the attributes of the root elements
	# viewBox is x y width height
	temp_str = str(-eed) + ' ' + str(-eed) + ' ' + \
		 str(smaw + 2*eed) + ' ' + str(smah + 2*eed)
	referoot.set('width',str(smaw + 2*eed))
	referoot.set('height',str(smah + 2*eed))
	referoot.set('viewBox',temp_str)
	teamroot.set('width',str(smaw + 2*eed))
	teamroot.set('height',str(smah + 2*eed))
	teamroot.set('viewBox',temp_str)
	# Black background for referee map
	ElementTree.SubElement(referoot, 'rect', x=str(-2*eed), y=str(-2*eed), 
		width=str(smaw + 4*eed), height=str(smah + 4*eed), 
		fill='black', stroke='black', 
		stroke_width='1')
	# White background for player team map
	ElementTree.SubElement(teamroot, 'rect', x=str(-2*eed), y=str(-2*eed), 
		width=str(smaw + 4*eed), height=str(smah + 4*eed), 
		fill='white', stroke='white', 
		stroke_width='1')
	for syst in systemlist:
		# A circle for showing the nebula area
		if 'nebula_center' in syst[3]:
			ElementTree.SubElement(referoot, 'circle', 
				r=str(sector_init_data.nebula_rad * ssm), 
				cx=str(syst[0] * ssm), cy=str(syst[1] * ssm),
				stroke=str(other_colors_rgb['nebula']), 
				stroke_width='1', fill_opacity='0')
			continue
		# A circle for showing what neighbouring systems 
		# might know about stations or distress signals
		if syst[2] == 'station' or syst[2] == 'distress':
			ElementTree.SubElement(referoot, 'circle', 
				r=str(neighbour_notice * ssm), 
				cx=str(syst[0] * ssm), cy=str(syst[1] * ssm),
				stroke=str(syst_colors_rgb[syst[2]]),
				stroke_width='1', fill_opacity='0')
		# Add circles showing systems in nebula area
		if 'in_nebula' in syst[3]:
			ElementTree.SubElement(referoot, 'circle', 
				r=str(min_system_dist / 2 * ssm),
				cx=str(syst[0] * ssm), cy=str(syst[1] * ssm),
				stroke=str(other_colors_rgb['nebula']),
				stroke_width='0',
				fill=str(other_colors_rgb['nebula']),
				fill_opacity=str(nebula_opacity) )
		# Add Danger rectangles
		if 'danger' in syst[3]:
			danger_type = ''
			for dt in syst[3]:
				 if dt in other_colors_rgb:
					danger_type = dt
			ElementTree.SubElement(referoot, 'rect', 
				x=str(syst[0]*ssm - dssl), y=str(syst[1]*ssm - dssl),
				width=str(dssl * 2), height=str(dssl * 2), 
				fill_opacity=str(danger_opacity),
				fill=str(other_colors_rgb[danger_type]),
				stroke=str(other_colors_rgb[danger_type]),
				stroke_width=str(scsw) )
		# Each system gets a small circle for itself, color-coded
		ElementTree.SubElement(referoot, 'circle', 
			r=str(scr), 
			cx=str(syst[0] * ssm), cy=str(syst[1] * ssm),
			stroke=str(syst_colors_rgb[syst[2]]), 
			stroke_width=str(scsw), 
			fill=str(syst_colors_rgb[syst[2]]) )
		# Each system gets a identical small circle for itself
		if syst[2] == 'start' or syst[2] == 'exit':
			ElementTree.SubElement(teamroot, 'circle', 
				r=str(scr), 
				cx=str(syst[0] * ssm), cy=str(syst[1] * ssm),
				stroke=str(syst_colors_rgb[syst[2]]), 
				stroke_width='1', fill_opacity='0')
		else:
			ElementTree.SubElement(teamroot, 'circle', 
				r=str(scr), 
				cx=str(syst[0] * ssm), cy=str(syst[1] * ssm),
				stroke=str(syst_colors_rgb['unknown']), 
				stroke_width=str(scsw), 
				fill=str(syst_colors_rgb['unknown']) )
	# Distance markers for player map
	for x in range(map_width+1):
		top_str = ''
		bottom_str = ''
		if x % 5 == 0:
			top_str = str(x*ssm) + ',0 ' 
			top_str += str(x*ssm - cas) + ',' + str(-cas*2) + ' ' 
			top_str += str(x*ssm + cas) + ',' + str(-cas*2) 
			bottom_str = str(x*ssm) + ',' + str(smah) + ' ' 
			bottom_str += str(x*ssm - cas) + ',' + str(smah+cas*2) + ' ' 
			bottom_str += str(x*ssm + cas) + ',' + str(smah+cas*2) 
		else:
			top_str = str(x*ssm) + ',0 '
			top_str += str(x*ssm - cas/2) + ',' + str(-cas) + ' ' 
			top_str += str(x*ssm + cas/2) + ',' + str(-cas) 
			bottom_str = str(x*ssm) + ',' + str(smah) + ' ' 
			bottom_str += str(x*ssm - cas/2) + ',' + str(smah+cas) + ' ' 
			bottom_str += str(x*ssm + cas/2) + ',' + str(smah+cas) 
		ElementTree.SubElement(teamroot, 'polygon', 
			points=top_str,
			fill='black', stroke='black', 
			stroke_width='1')
		ElementTree.SubElement(teamroot, 'polygon', 
			points=bottom_str,
			fill='black', stroke='black', 
			stroke_width='1')
	# Left & right edges need a bit of extra space to fit start and exit
	for y in range(map_height+1):
		left_str = ''
		right_str = ''
		if y % 5 == 0:
			left_str = str(-scr) + ',' + str(y*ssm) + ' ' 
			left_str += str(-cas*2-scr) + ',' + str(y*ssm - cas) + ' ' 
			left_str += str(-cas*2-scr) + ',' + str(y*ssm + cas) 
			right_str = str(smaw+scr) + ',' + str(y*ssm) + ' ' 
			right_str += str(smaw+cas*2+scr) + ',' + str(y*ssm - cas) + ' ' 
			right_str += str(smaw+cas*2+scr) + ',' + str(y*ssm + cas) 
		else:
			left_str = str(-scr) + ',' + str(y*ssm) + ' ' 
			left_str += str(-cas-scr) + ',' + str(y*ssm - cas/2) + ' ' 
			left_str += str(-cas-scr) + ',' + str(y*ssm + cas/2) 
			right_str = str(smaw+scr) + ',' + str(y*ssm) + ' ' 
			right_str += str(smaw+cas+scr) + ',' + str(y*ssm - cas/2) + ' ' 
			right_str += str(smaw+cas+scr) + ',' + str(y*ssm + cas/2) 
		ElementTree.SubElement(teamroot, 'polygon', 
			points=left_str,
			fill='black', stroke='black', 
			stroke_width='1')
		ElementTree.SubElement(teamroot, 'polygon', 
			points=right_str,
			fill='black', stroke='black', 
			stroke_width='1')


# Prints out a reasonable good-looking csv file with a ';' as separator
# (Using the csv module might be smart if this gets more complicated.)
def print_system_info():
	system_string = "# Number of systems: " + str(len(systemlist)) + "\n"
	main_separator = "; "
	secondary_separator = ", "
	systemlist.sort()
	for syst in systemlist:
		if syst[2] == 'dummy':
			continue
		system_string += str(syst[0]) + main_separator
		system_string += str(syst[1]) + main_separator
		system_string += str(syst[2]) + main_separator
		if syst[3] != []:
			item_string = ''
			for item in syst[3]:
				item_string += str(item) + secondary_separator
			# Remove last separator
			system_string += item_string[:-2] + " "
		system_string += "\n"
	print system_string

def print_svg():
	# Header is not included in tree.
	foostring = '<?xml version="1.0"?>\n' + \
		'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n' + \
		'  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
	refestring = foostring
	teamstring = foostring
	# Create referee svg map from the xml object
	foostring = ElementTree.tostring(referoot)
	# Add some line breaks
	barstring = foostring.replace('>','>\n\n')
	# Fix hyphens
	refestring += barstring.replace('_','-')
	# Create team svg map from the xml object in the same way
	foostring = ElementTree.tostring(teamroot)
	barstring = foostring.replace('>','>\n\n')
	teamstring += barstring.replace('_','-')
	# Actually print out the stuff (later into separate outputs)
	print refestring
	print "<!--"
	print teamstring
	print_system_info()
	print "-->"


#	Map generation functions
# On x-axis, only start and exit can have 0 and map_width, respectively;
# everything else is in between.  
# On y-axis, everything is in between 0 and map_height.
def create_system_types_min_list():
	types_list = []
	system_dict = sector_init_data.mins
	for key in system_dict:
		for x in range(system_dict[key]):
			types_list.append(key)
	return types_list

# For each system between min and max, binary chance of appearing
def create_additional_systems_list():
	types_list = []
	system_mins = sector_init_data.mins
	system_maxs = sector_init_data.maxs
	for key in system_mins:
		max_add = system_maxs[key] - system_mins[key]
		for x in range(max_add):
			if (randrange(2) == 0):
				types_list.append(key)
	return types_list

def place_start_exit():
	ym = round(map_height / 2) # Y-axis middlepoint
	yr = round(start_exit_height_range / 2) # Y-axis range
	systemlist.append([0,randint(ym - yr, ym + yr),'start',[]])
	systemlist.append([map_width,randint(ym - yr, ym + yr),'exit',[]])

def find_location_for_system():
	too_close = True
	xloc = randint(1, map_width-1)
	# Decrease likelyhood of top/bottom edge positions
	horiz_edge = trunc(round(map_height/10))
	yloc = randint(1, map_height-horiz_edge) + randint(0, horiz_edge-1)
	while (too_close):
		too_close = False
		for syst in systemlist:
			if syst[2] == 'dummy':
				continue
			if (distance(xloc,yloc,syst[0],syst[1]) < min_system_dist):
				too_close = True
				xloc = randint(1, map_width-1)
				yloc = randint(1, map_height-horiz_edge) + randint(0, horiz_edge-1)
				break
	return [xloc,yloc]

def no_sametype_too_close(loc,type):
	too_close = True
	while (too_close):
		too_close = False
		for syst in systemlist:
			if (distance(loc[0],loc[1],syst[0],syst[1]) < neighbour_notice) and (syst[2] == type):
				too_close = True
				loc = find_location_for_system()
				break
	return loc

def create_systems(get_list):
	system_type_list = get_list()
	for type in system_type_list:
		loc = find_location_for_system()
		if type == 'station':
			loc = no_sametype_too_close(loc,'station')
		systemlist.append([loc[0],loc[1],type,[]])

def add_dangers():
	nebula_chance = 0
	danger_chance = ''
	xloc = 0
	yloc = 0
	nebula_exists = False
	if 'home' in sector_keywords:
		nebula_chance = nebula_chance_home
	else:
		nebula_chance = nebula_chance_other
	if 'neutral' in sector_keywords:
		nebula_chance = nebula_chance + nebula_chance_add_neutral 
	if randrange(100) < nebula_chance:
		nebula_from_edge = trunc(round(sector_init_data.nebula_rad/2))
		xloc = randint(nebula_from_edge, map_width-nebula_from_edge)
		yloc = randint(nebula_from_edge, map_height-nebula_from_edge)
		nebula_exists = True
		for syst in systemlist:
			if (distance(xloc,yloc,syst[0],syst[1]) <= sector_init_data.nebula_rad):
				syst[3].append('in_nebula')
		systemlist.append([xloc,yloc,'dummy',['nebula_center']])
	for syst in systemlist:	
		danger_chance = danger_chances[syst[2]]		
		if randrange(100) < danger_chance:
			syst[3].append('danger')
			if nebula_exists and distance(xloc,yloc,syst[0],syst[1]) <= sector_init_data.nebula_rad:
				syst[3].append('plasma_storm')
			else:
				if randrange(100) < asteroid_chance:
					syst[3].append('asteroid_field')
				else:
					syst[3].append('solar_flare')

def add_near_markers():
	for syst in systemlist:
		for nghb in systemlist: 
			if distance(syst[0],syst[1],nghb[0],nghb[1]) > neighbour_notice:
				continue
			if syst[0] == nghb[0] and syst[1] == nghb[1]:
				continue
			if nghb[2] == 'station':
				syst[3].append('station_near_' + str(nghb[0]) +
					'_' + str(nghb[1]))
			if nghb[2] == 'distress':
				syst[3].append('distress_near_' + str(nghb[0]) +
					'_' + str(nghb[1]))


# Main program
do_setup()


place_start_exit()
create_systems(create_system_types_min_list)
create_systems(create_additional_systems_list)
add_dangers()
add_near_markers()

create_svg_maps()
print_svg()


# debugstring = "Debug stuff: \n"
# print "<!-- \n"
# print debugstring
# print "--> \n"
#	global debugstring
#	debugstring += "Checking for " + str(type) + " closeness. \n"
#				debugstring += "ALERT! Came too close between (" + str(loc[0]) + "," + str(loc[1]) + ") and (" + str(syst[0]) + "," + str(syst[1]) + ") \n"
#			debugstring += "Checked (" + str(syst[0]) + "," + str(syst[1]) + ") [" + str(syst[2]) + "], distance was " + str(distance(loc[0],loc[1],syst[0],syst[1])) + "\n"
#		debugstring += "Created system at (" + str(loc[0]) + "," + str(loc[1]) + ") [" + str(type) + "] \n"
