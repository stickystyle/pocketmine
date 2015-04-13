#!/usr/bin/env python

import urllib2
import json
import sys
import tarfile
import os
import os.path
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import yaml

PORTS = (19132, 19133, 19134, 19135)


def get_tarfile(channel):
    r = urllib2.Request(url='http://www.pocketmine.net/api/?channel={}'.format(channel)) # noqa
    response = urllib2.urlopen(r)
    if response.getcode() != 200:
        sys.exit()
    json_body = json.loads(response.read())
    tag = json_body['details_url'].split('/')[-1]
    print tag

    r = urllib2.Request(url='https://api.github.com/repos/PocketMine/PocketMine-MP/releases/tags/{}'.format(tag)) # noqa
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
    container = {'image': 'stickystyle/pocketmine:{}'.format(channel),
                     'volumes': ['{}/pm-{}/worlds:/pocketmine/worlds'.format(cwd, server), # noqa
                                '{}/pm-{}/plugins:/pocketmine/plugins'.format(cwd, server), # noqa
                                '{}/pm-{}/configs:/pocketmine/configs'.format(cwd, server), # noqa
                                '{}/pm-{}/players:/pocketmine/players'.format(cwd, server) # noqa
                                ],
                     'ports': ['{}:19132/udp'.format(port)],
                     'restart': 'always'
                 }
    return container


def main(server_name, channel):
    pm_tar = get_tarfile(channel)
    pocketmine_yml = get_pocketmineyaml(pm_tar, channel)

    try:
        with open('docker-compose.yml', 'r') as fh:
            docker_yml = yaml.load(fh.read())
    except IOError:
            docker_yml = {}

    avail_ports = list(PORTS)
    for container_key in docker_yml:
        container_port = int(docker_yml[container_key]['ports'][0].split(':')[0]) # noqa
        if container_port in avail_ports:
            avail_ports.remove(container_port)
    if len(avail_ports) == 0:
        print 'no more ports!'
        sys.exit()
    port = avail_ports.pop()
    container = get_container(server_name, channel, port)

    docker_yml[server_name] = container
    with open('docker-compose.yml', 'w') as fh:
        fh.write(yaml.dump(docker_yml))

    os.mkdir('{}/pm-{}'.format(os.getcwd(), server_name))
    for pm_dir in container['volumes']:
        os.mkdir(pm_dir.split(':')[0])

    with open('{}/pm-{}/configs/pocketmine.yml'.format(os.getcwd(), server_name), 'w') as fh: # noqa
        fh.write(yaml.dump(pocketmine_yml))

if __name__ == '__main__':
    channel = 'beta'
    server_name = sys.argv[1]
    main(server_name, channel)
