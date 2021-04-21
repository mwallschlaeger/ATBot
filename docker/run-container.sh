#/bin/bash

ADB_PORT=$1
container_name="mwall2bitflow/android-emulator-23"

docker -v

if [ $? -eq 1 ] ; then
	apt-get install docker
fi

docker run --rm --privileged -p 5900:5900 -p $ADB_PORT:5555 -e ANDROID_ARCH="x86" -v /dev/kvm:/dev/kvm $container_name


