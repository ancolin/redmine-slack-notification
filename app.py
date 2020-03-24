# coding: utf-8
import os
import requests
import xml.etree.ElementTree as et

flg_debug = True
url_watching = ''
url_my_ticket = ''
base_path = './entries'
url_slack_webhook = ''

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
        last_updated = getLastUpdate(filename)
        if tu != last_updated:
            # updated
            log('updated')
            setNotify(ti, tt)
            saveEntry(filename, tu)
        else:
            # no update
            log('no update')
        monitoring_ticket_ids.remove(ticket_id)
    else:
        # new ticket
        log('new ticket')
        setNotify(ti, tt)
        saveEntry(filename, tu)


def getLastUpdate(fn):
    lu = ''
    try:
        with open(fn, 'r') as f:
            lu = f.read()
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
        requests.post(url_slack_webhook, message.encode('utf-8'))
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


# set monitoring ticket ids
if os.path.isdir(base_path):
    monitoring_ticket_ids = os.listdir(base_path)

# watching ticket
if url_watching != '':
    log('checking watching ticket')
    response = getAtom(url_watching)
    checkAtom(response.content)

# my ticket
if url_my_ticket != '':
    log('checking my ticket')
    response = getAtom(url_my_ticket)
    checkAtom(response.content)

if len(notify_tickets) > 0:
    doNotify()

if len(monitoring_ticket_ids) > 0:
    # closed ticket
    for i in monitoring_ticket_ids:
        removeEntry(i)
