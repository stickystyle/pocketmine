#!/usr/bin/env python

import urllib2
import json
import sys
import tarfile
import os
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import yaml

CHANNEL = 'beta'
PORTS = (19132, 19133, 19134, 19135)
SERVER = 'test'
port = 19132


def get_tarfile(channel):
    r = urllib2.Request(url='http://www.pocketmine.net/api/?channel={}'.format(CHANNEL))
    response = urllib2.urlopen(r)
    if response.getcode() != 200:
        sys.exit()
    json_body = json.loads(response.read())
    tag = json_body['details_url'].split('/')[-1]
    print tag

    r = urllib2.Request(url='https://api.github.com/repos/PocketMine/PocketMine-MP/releases/tags/{}'.format(tag))
    response = urllib2.urlopen(r)
    if response.getcode() != 200:
        sys.exit()
    json_body = json.loads(response.read())
    print json_body['tarball_url']

    r = urllib2.Request(url=json_body['tarball_url'])
    response = urllib2.urlopen(r)
    if response.getcode() != 200:
        sys.exit()

    pm_tar = tarfile.open(fileobj=StringIO(response.read()))
    return pm_tar

def get_pocketmineyaml(pm_tar, channel):
    for tar_member in pm_tar.getnames():
        if tar_member.split('/')[-1] == "pocketmine.yml":
            print tar_member
            break
    pocketmine_yml = pm_tar.extractfile(tar_member).read()
    pocketmine_yml = yaml.load(pocketmine_yml)
    pocketmine_yml['auto-updater']['preferred-channel'] = channel
    pocketmine_yml['auto-updater']['enabled'] = False
    return pocketmine_yml

def get_container(server, channel, port):
    cwd = os.getcwd()
    container = {server:{'image':'stickystyle/pocketmine:{}'.format(channel),
                     'volumes':['{}/pm-{}/worlds:/pocketmine/worlds'.format(cwd, server),
                                '{}/pm-{}/plugins:/pocketmine/plugins'.format(cwd, server),
                                '{}/pm-{}/configs:/pocketmine/configs'.format(cwd, server),
                                '{}/pm-{}/players:/pocketmine/players'.format(cwd, server)
                               ],
                     'ports':['{}:19132/udp'.format(port)],
                     'restart': 'always'
                     }
            }
    return container

pm_tar = get_tarfile(CHANNEL)
pocketmine_yml = get_pocketmineyaml(pm_tar, CHANNEL)
container = get_container(SERVER, CHANNEL, port)

with open('docker-compose.yml', 'w') as fh:
    fh.write(yaml.dump(container))

cwd = os.getcwd()
os.mkdir('{}/pm-{}'.format(cwd, SERVER))
for pm_dir in container[SERVER]['volumes']:
    os.mkdir(pm_dir.split(':')[0])

with open('{}/pm-{}/configs/pocketmine.yml'.format(cwd, SERVER), 'w') as fh:
    fh.write(yaml.dump(pocketmine_yml))
