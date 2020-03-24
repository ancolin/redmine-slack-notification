# coding: utf-8
import requests
import xml.etree.ElementTree as et
import os

flg_debug = True
url_watching = ''
url_my_ticket = ''
base_path = './entries'
url_slack_webhook = ''


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
    filename = base_path + '/' + ti.split('/')[-1]
    if os.path.isfile(filename):
        # check update
        last_updated = getLastUpdate(filename)
        if tu != last_updated:
            # updated
            log('updated')
            doNotify(ti, tt)
            saveEntry(filename, tu)
        else:
            # no update
            log('no update')
    else:
        # new ticket
        log('new ticket')
        doNotify(ti, tt)
        saveEntry(filename, tu)


def getLastUpdate(fn):
    lu = ''
    try:
        with open(fn, 'r') as f:
            lu = f.read()
    except Exception as e:
        log(e)
    return lu


def doNotify(ti, tt):
    log('Notify: ' + ti)
    message = '{"text": "Ticket updated: ' + tt + '\n' + ti + '"}'
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

