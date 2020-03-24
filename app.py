# coding: utf-8
import os
import requests
import xml.etree.ElementTree as et
import json

flg_debug = True
base_path = './entries'

configure = {}
monitoring_ticket_ids = []
notify_tickets = []


def log(s):
    if flg_debug is True:
        print(s)


def getAtom(url):
    try:
        r = requests.get(url)
        return r
    except Exception as e:
        log(e)


def checkAtom(a):
    root = et.fromstring(a)
    for c in root:
        if 'entry' in c.tag:
            ticket_id = ''
            ticket_updated = ''
            ticket_title = ''
            for e in c:
                if 'id' in e.tag:
                    ticket_id = e.text
                if 'updated' in e.tag:
                    ticket_updated = e.text
                if 'title' in e.tag:
                    ticket_title = e.text
            if ticket_id != '':
                checkUpdated(
                    ticket_id,
                    ticket_updated,
                    ticket_title
                )


def checkUpdated(ti, tu, tt):
    ticket_id = ti.split('/')[-1]
    filename = base_path + '/' + ticket_id
    if ticket_id in monitoring_ticket_ids:
        # check update
        updated_on = getUpdatedOn(ticket_id)
        last_updated = getLastUpdate(filename)
        if updated_on != last_updated:
            # updated
            log('updated')
            setNotify(ti, tt)
            saveEntry(filename, updated_on)
        else:
            # no update
            log('no update')
        monitoring_ticket_ids.remove(ticket_id)
    else:
        # new ticket
        log('new ticket')
        updated_on = getUpdatedOn(ticket_id)
        setNotify(ti, tt)
        saveEntry(filename, updated_on)


def getLastUpdate(filename):
    lu = ''
    try:
        with open(filename, 'r') as f:
            lu = f.read()
    except Exception as e:
        log(e)
    return lu


def getUpdatedOn(ticket_id):
    lu = ''
    try:
        u = configure['url_redmine'] + '/issues/' + ticket_id + '.json' \
                                                  '?key=' + configure['redmine_api_key']
        r = requests.get(u)
        ticket_detail = json.loads(r.content)
        lu = ticket_detail['issue']['updated_on']
    except Exception as e:
        log(e)
    return lu


def setNotify(ti, tt):
    notify_tickets.append({'id': ti, 'title': tt})


def doNotify():
    log('Notify')
    message = '{"text": "Tickets updated.'
    for m in notify_tickets:
        message += '\n' + m['title'] + '\n' + m['id']
    message += '"}'

    try:
        requests.post(configure['url_slack_webhook'], message.encode('utf-8'))
    except Exception as e:
        log(e)


def saveEntry(fn, tu):
    log('Save: ' + fn)
    if os.path.isdir(base_path) is False:
        os.makedirs(base_path)
    with open(fn, 'w') as f:
        f.write(tu)


def removeEntry(fn):
    filename = base_path + '/' + fn
    log('Remove: ' + filename)
    os.remove(filename)


# set configure
with open('./configure.json', 'r') as f:
    configure = json.loads(f.read())

# set monitoring ticket ids
if os.path.isdir(base_path):
    monitoring_ticket_ids = os.listdir(base_path)

for url in configure['atom_urls']:
    response = getAtom(url)
    checkAtom(response.content)

if len(notify_tickets) > 0:
    doNotify()

if len(monitoring_ticket_ids) > 0:
    for i in monitoring_ticket_ids:
        removeEntry(i)
