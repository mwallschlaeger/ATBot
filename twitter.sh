#!/bin/bash  

# EXECUTABLES
ADB=$(which adb)
EXEC="$ADB shell"
INPUT="$EXEC /system/bin/input"
SCREENSHOT="$EXEC /system/bin/screencap"
PULL="$ADB pull"
INSTALL="$ADB install"
UIAUTOMATOR_DUMP="$EXEC uiautomator dump"	
DOWNLOAD="wget --no-check-certificate"

# REMOTE PATH TO SAVE PICTURES
REMOTE_FILEPATH_EMULATOR="/data/twitter_sc"
REMOTE_FILEPATH_DEVICE="/sdcard/twitter_sc"


# APK DOWNLOAD URL
APK_DOWNLOAD_URL=""
APK_TMP_PATH="/tmp/twitter.apk"

# TWITTER RELATED STRINGS
TWITTER_PACKAGE="com.twitter.android"
TWITTER_ONBOARDING_ACTIVITY="com.twitter.android/com.twitter.app.onboarding"
TWITTER_LOGIN_ACTIIVITY="com.twitter.android/com.twitter.android.LoginActivity"
TWITTER_MAIN_ACTIVITY="com.twitter.android/com.twitter.app.main.MainActivity"
TWITTER_TWEET_ACTIVITY="com.twitter.android/com.twitter.composer.ComposerActivity"
TWITTER_LOGIN_CHALLENGE_ACTIVTY="com.twitter.android/com.twitter.android.LoginChallengeActivity"

# ANDROID RELATED STRING
KEYBOARD_VISABLE_STRING="mHasSurface=true"
KEYBOARD_INVISABLE_STRING="mHasSurface=false"

# KEYEVENTS 
KEY_EVENT_HIDE_KEYBOARD=111
KEY_EVENT_DEL=67
KEY_EVENT_RETURN=66
KEY_EVENT_SPACE=62
KEY_EVENT_TAB=61

function connect_tcp(){
	hostname=$1
	port=$2
	ret=$($ADB connect "$hostname:$port")
	if [[ "$ret" == *"connected"* ]] ; then
		return 0
	else
		return 1
	fi
}

function get_adb_device_description(){
	description=$($ADB devices -l | awk -F "     " '{ print $2}')
	echo "$description"
}

function is_emulator(){
	description=get_adb_device_description 
	if [[ "$description" == *"emulator"* ]] ; then
		return 0
	else
		return 1
	fi
}


# LOGGING
function err_msg_exit(){
	err_log $@
	exit 1
}

function err_log(){
	echo "ERROR: $*" > /dev/stderr 
}

function info_log(){
	echo "INFO: $*" > /dev/stderr
}

function warning_log(){
	echo "WARNING: $*" > /dev/stderr	
}

function get_mcurrent_focus_string(){
	str=$($EXEC dumpsys window windows | grep -E 'mCurrentFocus')
	echo $str
}

function get_mhassurface_focus_string(){
	str=$($EXEC dumpsys window InputMethod | grep -E 'mHasSurface')
	echo $str
}

function get_display_height(){
	str=$($EXEC dumpsys display | grep -E 'mDisplayHeight' | awk -F "=" '{ print $2 }')
	echo $str
}

function get_display_width(){
	str=$($EXEC dumpsys display | grep -E 'mDisplayWidth' | awk -F "=" '{ print $2 }')
	echo $str
}

function is_current_app_twitter(){
	mcurrent=$(get_mcurrent_focus_string)
	if [[ "$mcurrent" == *"$TWITTER_PACKAGE"* ]] ; then
		return 0
	else
		return 1
	fi
}

function is_twitter_challenge_activity(){
	mcurrent=$(get_mcurrent_focus_string)
	if [[ "$mcurrent" == *"$TWITTER_LOGIN_CHALLENGE_ACTIVTY"* ]] ; then
		return 0
	else
		return 1
	fi
}

function is_twitter_onboarding_activity(){
	mcurrent=$(get_mcurrent_focus_string)
	if [[ "$mcurrent" == *"$TWITTER_ONBOARDING_ACTIVITY"* ]] ; then
		return 0
	else
		return 1
	fi
}

function is_twitter_login_activity(){
	mcurrent=$(get_mcurrent_focus_string)
	if [[ "$mcurrent" == *"$TWITTER_LOGIN_ACTIIVITY"* ]] ; then
		return 0
	else
		return 1
	fi
}

function is_twitter_main_activity(){
	mcurrent=$(get_mcurrent_focus_string)
	if [[ "$mcurrent" == *"$TWITTER_MAIN_ACTIVITY"* ]] ; then
		return 0
	else
		return 1
	fi
}

function is_twitter_tweet_activity(){
	mcurrent=$(get_mcurrent_focus_string)
	if [[ "$mcurrent" == *"$TWITTER_TWEET_ACTIVITY"* ]] ; then
		return 0
	else
		return 1
	fi
}

function is_twitter_installed(){
	if $EXEC pm list packages | grep -q "$TWITTER_PACKAGE"; then
		return 0
	else
		return 1
	fi

}

function launch_twitter(){
	$EXEC  monkey -p "$TWITTER_PACKAGE" -c android.intent.category.LAUNCHER 1;
	sleep 7
}

function close_twitter(){
	$EXEC am force-stop "$TWITTER_PACKAGE"
}

function download_apk(){
	$DOWNLOAD -O "$APK_TMP_PATH" "$APK_DOWNLOAD_URL"
}

function install_apk(){
	if ! [ -e "$APK_TMP_PATH" ] ; then
		download_apk
	fi
	$INSTALL "$APK_TMP_PATH"
}

function is_android_keyboard_visable(){
	str=$(get_mhassurface_focus_string)
	if [[ $str == *"$KEYBOARD_VISABLE_STRING"* ]] ; then
		return 0
	elif [[ $str == *"$KEYBOARD_INVISABLE_STRING"* ]] ; then
		return 1
	else 
		err_msg_exit "Could not obtain Keyboard visibility ..."
	fi
}

# not working
#function hide_android_software_keyboard(){
#	$INPUT keyevent "$KEY_EVENT_HIDE_KEYBOARD"
#}

function screenshot(){
	local_filepath="$1"
	remote_filename=$(pwgen -1)
	REMOTE_FILEPATH="$(get_remote_path)"
	$SCREENSHOT -p "$REMOTE_FILEPATH/$remote_filename.png"
	ret=$($PULL $REMOTE_FILEPATH/$remote_filename.png $local_filepath)
	return 0
}

function get_remote_path(){
	if is_emulator ; then
		echo "$REMOTE_FILEPATH_EMULATOR"
	else
		echo "$REMOTE_FILEPATH_DEVICE"
	fi
}

function get_uiautomator_dump_file(){
	local_filepath="$1"
	remote_filename=$(pwgen -1)
	REMOTE_FILEPATH="$(get_remote_path)"
	$EXEC mkdir -p "$REMOTE_FILEPATH"

	$UIAUTOMATOR_DUMP  "$REMOTE_FILEPATH/$remote_filename.xml"
	ret=$($PULL $REMOTE_FILEPATH/$remote_filename.xml $local_filepath)
	return 0
}


function diversify_screen_position(){
	position=$1
	vary=$2
	applied_vary=$RANDOM
	let "applied_vary %= $vary"
	number2=$RANDOM
	let "number2 %= 2"
	if [ $number2 -eq 0 ] ; then
		let "position = position - applied_vary"
	else
		let "position = position + applied_vary"
	fi
	echo $position	
}


function get_random_center_x(){ 
	width=$(get_display_width)
	let "with_touch_leftest = (width / 10) * 3"
	with_random=$RANDOM
	let "with_random %= (width / 2)"
	let "x = with_touch_leftest + with_random"
	echo $x
}

function get_radom_bottom_y(){
	height=$(get_display_height)

	let "hight_one_tenth = (height / 10) * 1"
	height_random=$RANDOM
	let "height_random %= (width / 5)"
	let "y = hight_one_tenth + height_random"
	echo $y
}

function get_radom_top_y(){
	height=$(get_display_height)

	let "hight_nine_tenth = (height / 10) * 9"
	height_random=$RANDOM
	let "height_random %= (width / 5)"
	let "y = hight_nine_tenth - height_random"
	echo $y
}

function get_random_swipe_delay(){
	min_swipe=400
	time_vary_range=220
	time_random=$RANDOM
	let "time_random %= time_vary_range"
	let "time = min_swipe + time_random"
	echo $time
}

function get_screen_swipe_values(){
	direction=$1


	if [ "$direction" == "up" ] ; then
		x_start=$(get_random_center_x)
		y_start=$(get_random_bottom_y)
		x_end=$(get_random_center_x)
		y_end=$(get_random_top_y)
		time=$(get_random_swipe_delay)
	elif [ "$direction" == "down" ] ; then
		x_start=$(get_random_center_x)
		y_start=$(get_random_top_y)
		x_end=$(get_random_center_x)
		y_end=$(get_random_bottom_y)
		time=$(get_random_swipe_delay)
	else
		warning_log "Wrong parameters for get_screen_swipe_values, requires 'up' or 'down' ..." 
		return -1
	fi
	echo $x_start $y_start $x_end $y_end $time
}
#######################
# SCREEN INTERACTIONS #
#######################

# TOUCH
function touch_on_screen_in_bounds(){
	x_start=$1
	y_start=$2
	x_end=$3
	y_end=$4

	x_off=$RANDOM
	y_off=$RANDOM
	let "x_off %= (x_end - x_start)"	
	let "y_off %= (y_end - y_start)"	

	x=0
	y=0
	let "x = x_start + x_off"	
	let "y = y_start + y_off"	
	info_log $x $y
	$INPUT tap $x $y
}

function touch_on_screen(){
	x=$1
	y=$2
	$INPUT tap $x $y
}

# SWIPE
function swipe_screen_down(){
	$INPUT swipe $(get_screen_swipe_values "down")
}

function swipe_screen_up(){
	$INPUT swipe $(get_screen_swipe_values "up")
}


# KEYBOARD

# maybe requires more special character handling ...
function type_on_screen(){
	text=$1
	min_delay=$2
	max_delay=$3

	for i in $(seq 1 ${#text})  ; do
		delay=$RANDOM
		let "delay %= (max_delay - min_delay)"
		let "delay = delay + min_delay"

		char="${text:i-1:1}"
		if [[ "$char" == " " ]] ; then
			$INPUT keyevent "$KEY_EVENT_SPACE"
		else
			$INPUT text "$char" 
		fi

		if [ "$delay" -lt 100 ] ; then
			sleep "0.0$delay"
		elif [ "$delay" -lt 1000 ] ; then
			sleep "0.$delay"
		else
			# broke needs float operation
			delay="$(($delay / 1000.0))"
			info_log $delay
			sleep "$delay"
		fi
	done
}

function type_slow(){
	text=$1
	min_delay=350 # ms
	max_delay=800 # ms

	type_on_screen "$text" "$min_delay" "$max_delay"

}

function type_average(){
	text=$1
	min_delay=200 # ms
	max_delay=600 # ms

	type_on_screen "$text" "$min_delay" "$max_delay"
}

function type_fast(){
	text=$1
	min_delay=80 # ms
	max_delay=250 # ms

	type_on_screen "$text" "$min_delay" "$max_delay"
}
