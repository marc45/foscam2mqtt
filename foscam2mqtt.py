#!/usr/bin/env python

import json
import time
import argparse
import paho.mqtt.client as mqtt
from foscam.foscam import FoscamCamera, FOSCAM_SUCCESS


client = None
args = None
lastAttrValue = {}
lastTimePublish = 0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--name", help="foscam camera name")
    parser.add_argument("-H", "--host", help="foscam camera host/ip")
    parser.add_argument("-p", "--port", help="foscam camera port", type=int)
    parser.add_argument("-u", "--username", help="foscam camera username")
    parser.add_argument("-w", "--password", help="foscam camera password")
    parser.add_argument("-M", "--mqtthost", help="mqtt host")
    parser.add_argument("-P", "--mqttport", help="mqtt port", type=int)
    parser.add_argument("-U", "--mqttusername", help="mqtt camera username")
    parser.add_argument("-W", "--mqttpassword", help="mqtt camera password")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    return parser.parse_args()


def print_devinfo(params):
    global lastAttrValue, lastTimePublish

    data = {}
    changed = False
    attrs = ('motionDetectAlarm', 'soundAlarm', 'infraLedState')
    for attr in attrs:
        if attr not in lastAttrValue or params[attr] != lastAttrValue[attr]:
            changed = True
        data[attr] = lastAttrValue[attr] = params[attr]

    json_data = json.dumps(data)

    if changed or (time.time() - lastTimePublish) > 10:
        (res, _) = client.publish("ipcamera/"+args.name, json_data, qos=0)
        lastTimePublish = time.time()
        if args.verbose:
            print("Publish to mqtt: %s" % mqtt.error_string(res))


def main():
    global args, client

    args = parse_args()
    if args.verbose:
        print("Init mqtt..")
    client = mqtt.Client(client_id="", clean_session=True, userdata=None,
                         protocol=mqtt.MQTTv311)
    client.username_pw_set(args.mqttusername, args.mqttpassword)
    client.connect(args.mqtthost, args.mqttport, 60)
    client.loop_start()

    if args.verbose:
        print("Init foscam..")
    mycam = FoscamCamera(args.host, args.port, args.username, args.password,
                         daemon=False, verbose=args.verbose)

    while True:
        rc, params = mycam.get_dev_state()
        if rc == FOSCAM_SUCCESS:
            print_devinfo(params)
        else:
            print("Failed to get camera info: %d" % rc)
            time.sleep(30)
        time.sleep(1)


if __name__ == "__main__":
    main()
