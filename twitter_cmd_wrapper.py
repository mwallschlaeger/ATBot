
import logging, subprocess, argparse, time
import parse_window_dump


DUMP_FILE_PATH="/tmp/dumpfile.xml"

def bash_execute_from_twitter_sh(command):
	global twitter_sh
	a = subprocess.run(['bash', '-c', '. {} ; {}'.format(twitter_sh,command)])
	import pprint
	pp = pprint.PrettyPrinter(indent=4)
	pp.pprint(a)
	if a.returncode == 0:
		return True
	else:
		return False

# INSTALL aND LAUNCH TWITTER
def launch_twitter():
	logging.info("launching twitter ...")
	return bash_execute_from_twitter_sh("launch_twitter")

def is_twitter_installed():
	return bash_execute_from_twitter_sh("is_twitter_installed")

def install_twitter():
	logging.info("download twitter apk...")
	if not bash_execute_from_twitter_sh("download_apk"):
		logging.error("Could not download apk ...")
		return False

	logging.info("installing twitter apk...")
	if not bash_execute_from_twitter_sh("install_apk"):
		logging.error("Could not install apk ...")
		return False
	return True

def is_current_app_twitter():
	return bash_execute_from_twitter_sh("is_current_app_twitter")

# INSIDE APP

def execute_within_twitter(command):
	is_twitter = False
	i = 3
	while not is_twitter:
		is_twitter =  is_current_app_twitter()
		if not is_twitter:
			launch_twitter() 
		i=-1
		if i == 0:
			logging.error("unable to launch twitter, bye bye ...")
			exit(1)

	return bash_execute_from_twitter_sh(command)

def is_twitter_activity():
	return execute_within_twitter("is_twitter_login_activity")

def is_onboarding_activity():
	return execute_within_twitter("is_twitter_onboarding_activity")

def parse_onboarding_activity_dump(xml_filename):
	return execute_within_twitter("parse_onboarding_activity_dump {}".format(xml_filename))

def already_logged_in():
	if is_onboarding_activity():
		return False
	if is_login_activity():
		return False
	return True 

def login():
	global DUMP_FILE_PATH
	if is_onboarding_activity():
		if execute_within_twitter("get_uiautomator_dump_file {}".format(DUMP_FILE_PATH)):
			onboarding = parse_window_dump.parse_onboarding_activity_dump(xml_filename=DUMP_FILE_PATH)
			print(onboarding)
		else: 
			logging.error("could not get ui dumpfile, bye bye ...")
			exit(1)

def login_to_main_screen(username: str, password: str):
	# is twitter installed
	if not is_twitter_installed():
		install_twitter()

	# start application
	print("twitter app is installed ...")

	if not already_logged_in():
		print("login")
		login()
	else:
		navigate_to_main_activity()

	print("{} is logged in and rdy to tweet ...".format(username))



def main():
	global twitter_sh
	logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

	parser = argparse.ArgumentParser()
	parser.add_argument("-twittersh",required=True,type=str,help="provide twitter.sh driver")
	parser.add_argument("-username", required=True,type=str,help="twitter username")
	parser.add_argument("-password", required=True,type=str,help="twitter password")
	parser.add_argument("-phone", required=True, type=str,help="varifiy phone number	")
	#parser.add_argument("-activity",type=str,help="activity the dump is from (onboarding,login,main")
	args = parser.parse_args()

	twitter_sh = args.twittersh
	login_to_main_screen(args.username,args.password)

if __name__ == '__main__':
	main()