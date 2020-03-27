# coding: utf-8
import requests
import xml.etree.ElementTree as eT
import os
import json


class Utils:
    flg_debug = True
    base_path = ''

    configure = {}
    monitoring_ticket_ids = []
    notify_tickets = []

    def setFlgDebug(self, flg=False):
        self.flg_debug = flg

    def log(self, message):
        if self.flg_debug is True:
            print(message)

    def setConfigure(self, filename):
        with open(filename, 'r') as f:
            self.configure = json.loads(f.read())
            self.base_path = self.configure['monitoring_id_directory']

    def setMonitoringTicketIds(self):
        if os.path.isdir(self.base_path):
            self.monitoring_ticket_ids = os.listdir(self.base_path)

    def checkAtoms(self):
        for url in self.configure['atom_urls']:
            response = self.getAtom(url)
            self.checkAtom(response.content)

    def getAtom(self, url):
        try:
            return requests.get(url)
        except Exception as e:
            self.log(e)

    def checkAtom(self, atom):
        root = eT.fromstring(atom)
        for c in root:
            if 'entry' in c.tag:
                ticket_id = ''
                ticket_title = ''
                for e in c:
                    if 'id' in e.tag:
                        ticket_id = e.text
                    if 'title' in e.tag:
                        ticket_title = e.text
                if ticket_id != '':
                    self.checkUpdated(
                        ticket_id,
                        ticket_title
                    )

    def checkUpdated(self, ticket_id, ticket_title):
        ticket_id = ticket_id.split('/')[-1]
        filename = self.base_path + '/' + ticket_id
        if ticket_id in self.monitoring_ticket_ids:
            # check update
            updated_on = self.getUpdatedOn(ticket_id)
            last_updated = self.getLastUpdate(filename)
            if updated_on != last_updated:
                # updated
                self.log('updated')
                self.setNotify(ticket_id, ticket_title)
                self.saveEntry(filename, updated_on)
            else:
                # no update
                self.log('no update')
            self.monitoring_ticket_ids.remove(ticket_id)
        else:
            # new ticket
            self.log('new ticket')
            updated_on = self.getUpdatedOn(ticket_id)
            self.setNotify(ticket_id, ticket_title)
            self.saveEntry(filename, updated_on)

    def getLastUpdate(self, filename):
        lu = ''
        try:
            with open(filename, 'r') as f:
                lu = f.read()
        except Exception as e:
            self.log(e)
        return lu

    def getUpdatedOn(self, ticket_id):
        lu = ''
        try:
            u = self.configure['url_redmine'] + '/issues/' + ticket_id + '.json' \
                                                                         '?key=' + self.configure['redmine_api_key']
            r = requests.get(u)
            ticket_detail = json.loads(r.content)
            lu = ticket_detail['issue']['updated_on']
        except Exception as e:
            self.log(e)
        return lu

    def setNotify(self, ticket_id, ticket_title):
        self.notify_tickets.append({'id': ticket_id, 'title': ticket_title})

    def notify(self):
        if len(self.notify_tickets) > 0:
            self.doNotify()

        if len(self.monitoring_ticket_ids) > 0:
            for i in self.monitoring_ticket_ids:
                self.removeEntry(i)

    def doNotify(self):
        self.log('Notify')
        message = '{"text": "Tickets updated.'
        for m in self.notify_tickets:
            message += '\n' + m['title'] + '\n' + m['id']
        message += '"}'

        try:
            requests.post(self.configure['url_slack_webhook'], message.encode('utf-8'))
        except Exception as e:
            self.log(e)

    def saveEntry(self, filename, updated_on):
        self.log('Save: ' + filename)
        if os.path.isdir(self.base_path) is False:
            os.makedirs(self.base_path)
        with open(filename, 'w') as f:
            f.write(updated_on)

    def removeEntry(self, monitoring_ticket_id):
        filename = self.base_path + '/' + monitoring_ticket_id
        self.log('Remove: ' + filename)
        os.remove(filename)
