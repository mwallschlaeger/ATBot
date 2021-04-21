import logging, sys, argparse, re
import xml.etree.ElementTree as ET

SCRIPT_NAME="WINDOW_DUMP_XML_PARSER"

def buitify_tweet(tweet):
	tweet=tweet.replace('\n','')
	tweet=tweet.replace('hashtag ','#')
	return tweet.strip()

def get_tweet(content_desc_line):
	usernames_and_time = content_desc_line.split(". . .")[0] 
	tweet = content_desc_line.split(". . .")[1]
	try:
		meta = content_desc_line.split(". . .")[2] 
	except:
		meta=""

	tweet = buitify_tweet(tweet)
	return usernames_and_time,tweet,meta

def get_time(usernames_and_time):
	time_arr = usernames_and_time.split(". ")
	time = time_arr[len(time_arr)-1]
	usernames = usernames_and_time[0:len(usernames_and_time)-len(time)-2] # -2 = ". " 
	return usernames, time

def get_usernames(usernames):
		user_arr = usernames.split("@")
		username = user_arr[len(user_arr)-1]
		username = "@"+username
		given_username = usernames[0:len(usernames)-len(username)]
		return given_username,username

def set_action_bounds(tweet_dict,inline_action_bounds):
	import math
	button_width = math.floor(inline_action_bounds[2] / 4) # number of buttons
	tweet_dict["reply_tweet_bounds"] = [inline_action_bounds[0], inline_action_bounds[1], button_width, inline_action_bounds[3]]

	tweet_dict["re_tweet_bounds"] = [button_width+1, inline_action_bounds[1], button_width * 2, inline_action_bounds[3]]
	tweet_dict["like_tweet_bounds"] =  [(button_width * 2) + 1, inline_action_bounds[1], button_width * 3, inline_action_bounds[3]]
	tweet_dict["share_bounds"] = [(button_width * 3) + 1, inline_action_bounds[1], inline_action_bounds[2], inline_action_bounds[3]]
	tweet_dict["inline_actions_bounds"] = inline_action_bounds

def bounds_str_to_list(bounds_str):
	R = re.compile("\\[(?P<x_start>[0-9]+),(?P<y_start>[0-9]+)\\]\\[(?P<x_end>[0-9]+),(?P<y_end>[0-9]+)\\]")
	match = R.match(bounds_str)
	if match:
		cords = match.groupdict()
	return [int(cords["x_start"]), # 4 item list
			int(cords["y_start"]),
			int(cords["x_end"]),
			int(cords["y_end"])]

def get_xml_tree(xml_filename):
	try:
		tree = ET.parse(xml_filename)
	except:
		logging.error("{}: Unable to parse XML file ...".format(SCRIPT_NAME))
		sys.exit(1)
	return tree

def parse_main_activity_dump(xml_filename):
	main_activity = {}
	main_activity["home_menu"] = {}
	tree = get_xml_tree(xml_filename)

	child = tree.getroot()
	tweet_items = []
	tmp_child = []
	while child is not None:
		for c in child:
			if(c.attrib["content-desc"] is not ""):
				# parse tweet button
				if (c.attrib["resource-id"] == "com.twitter.android:id/row"):
					tweet_items.append(c)

				# parse tweets
				if c.attrib["content-desc"] == "New Tweet":
					main_activity["new_tweet_bounds"] = bounds_str_to_list(c.attrib["bounds"])

			# parse bottom bar
			if c.attrib["class"] == "android.support.v7.app.ActionBar$Tab":
				if c.attrib["content-desc"] == "Home":
					main_activity["home_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				elif c.attrib["content-desc"] == "Search and Explore Tab":
					main_activity["search_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				elif c.attrib["content-desc"] == "Notifications":
					main_activity["notification_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				elif c.attrib["content-desc"] == "Messages":
					main_activity["message_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])

			# parse top home button
			if c.attrib["class"] == "android.widget.ImageButton":
				if c.attrib["content-desc"] == "Show navigation drawer":
					
					main_activity["home_menu"]["home_button_bounds"] = bounds_str_to_list(c.attrib["bounds"]) 

			# if home button was pressed
			if (c.attrib["resource-id"] == "com.twitter.android:id/name"):
				main_activity["home_menu"]["unfolded"] = True
				main_activity["home_menu"]["name"] = c.attrib["text"]
			if (c.attrib["resource-id"] == "com.twitter.android:id/username"):
				main_activity["home_menu"]["username"] = c.attrib["text"]
			if (c.attrib["resource-id"] == "com.twitter.android:id/title"):
				if c.attrib["text"] == "Profile":
					main_activity["home_menu"]["profile_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
					# UNTESTED - requires total screen size
					main_activity["home_menu"]["return_bounds"] = [
																	main_activity["home_menu"]["profile_button_bounds"][2]+2,
																	main_activity["home_menu"]["profile_button_bounds"][1],
																	main_activity["home_menu"]["profile_button_bounds"][2]+100,
																	(main_activity["home_menu"]["profile_button_bounds"][3]-main_activity["home_menu"]["profile_button_bounds"][1]) * 4,
																	]

				if c.attrib["text"] == "Lists":
					main_activity["home_menu"]["lists_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				if c.attrib["text"] == "Bookmarks":
					main_activity["home_menu"]["bookmarks_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				if c.attrib["text"] == "Moments":
					main_activity["home_menu"]["moments_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				if c.attrib["text"] == "Settings and privacy":
					main_activity["home_menu"]["settings_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])
				if c.attrib["text"] == "Help Center":
					main_activity["home_menu"]["help_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])

			tmp_child.append(c)
		try:
			child=tmp_child.pop(0)
		except:
			child=None
	main_activity["tweets"] = []
	# example: content-desc='Coldamber @Coldamber. 15 hours ago. . . Ich habe heute im Seminar 
	# "Sprache und Geschlecht" die Studierenden gefragt: "Angenommen, es muesste dein Musikgeschmack
	# im Pass stehen: Waere es bei dir Pop oder Metal?" Und meine Guete war die Empoerung gross.. . . Sascha Bors liked. .'
	for tweet_obj in tweet_items:
		tweet_dict = {}
		cd_line = tweet_obj.attrib["content-desc"]
		usernames_and_time, tweet, meta = get_tweet(cd_line)
		usernames , time = get_time(usernames_and_time) 		
		given_username, username = get_usernames(usernames)

		tweet_dict["username"] = username
		tweet_dict["given_username"] = given_username
		tweet_dict["tweet"] = tweet
		tweet_dict["time"] = time
		tweet_dict["bounds"] = bounds_str_to_list(tweet_obj.attrib["bounds"])
		for c in tweet_obj:
			if c.attrib["resource-id"] == "com.twitter.android:id/tweet_inline_actions":
				set_action_bounds(	tweet_dict=tweet_dict,
									inline_action_bounds=bounds_str_to_list(c.attrib["bounds"]))
		main_activity["tweets"].append(tweet_dict)
	return main_activity

def parse_challenge_activity_dump(xml_filename):

	tree = get_xml_tree(xml_filename)
	child = tree.getroot()

	tmp_child = []
	challenge_dicts = {}

	text_box_bounds = None
	submit_button_bounds = None

	while child is not None:
			for c in child:
				if c.attrib["class"] == "android.widget.EditText":
					if c.attrib["content-desc"] == "Phone number":
						challenge_dicts["phone_number_text_box"] = bounds_str_to_list(c.attrib["bounds"])
				if c.attrib["class"] == "android.widget.Button":
					if c.attrib["content-desc"] == "Submit":
						challenge_dicts["submit_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])

				tmp_child.append(c)
			try:
				child=tmp_child.pop(0)
			except: 
				child=None

	return challenge_dicts

def parse_onboarding_activity_dump(xml_filename):

	tree = get_xml_tree(xml_filename)
	child = tree.getroot()

	tmp_child = []
	login_button_bounds = None
	
	while child is not None:
		for c in child:
			if c.attrib["text"] == "Have an account already? Log in":
				login_button_bounds = bounds_str_to_list(c.attrib["bounds"])
			tmp_child.append(c)
		try:
			child=tmp_child.pop(0)
		except:
			child=None

	if login_button_bounds is None:
		raise ValueError

	import math
	login_button_wdith = math.floor((login_button_bounds[2]-login_button_bounds[0]) / 6) 
	login_button_bounds[0] = login_button_bounds[2] - login_button_wdith # original bounds include non clickable text first
	return login_button_bounds

def parse_login_activity_dump(xml_filename):
	login_activity = {}

	tree = get_xml_tree(xml_filename)
	child = tree.getroot()

	tmp_child = []

	while child is not None:
		for c in child:
			if c.attrib["resource-id"] == "com.twitter.android:id/login_password":
				login_activity["login_password_bounds"] = bounds_str_to_list(c.attrib["bounds"])
			if c.attrib["resource-id"] == "com.twitter.android:id/login_identifier":
				login_activity["login_identifier_bounds"] = bounds_str_to_list(c.attrib["bounds"])
			if c.attrib["resource-id"] == "com.twitter.android:id/login_login":
				login_activity["login_button_bounds"] = bounds_str_to_list(c.attrib["bounds"])

			tmp_child.append(c)
		try:
			child=tmp_child.pop(0)
		except:
			child=None

	return login_activity

def main():
	logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

	parser = argparse.ArgumentParser()
	parser.add_argument("-xmlfile",type=str,help="provide window_dump.xml")
	parser.add_argument("-activity",type=str,help="activity the dump is from (onboarding,login,main")
	args = parser.parse_args()
	if args.activity == "challenge":
		print(parse_challenge_activity_dump(args.xmlfile))
	elif args.activity == "onboarding":
		print(parse_onboarding_activity_dump(args.xmlfile))
	elif args.activity == "main":
		main_activity=parse_main_activity_dump(args.xmlfile)
		import pprint
		pp = pprint.PrettyPrinter(indent=4)
		pp.pprint(main_activity)
	elif args.activity == "login":
		print(parse_login_activity_dump(args.xmlfile))
	else:
		logging.error("Not support parameter {} ...".format(args.activity))
	exit(0)

if __name__ == '__main__':
	main()