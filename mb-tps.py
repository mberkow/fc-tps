#!/usr/bin/python

import argparse
import sys
import os
from trolly.client import Client
from trolly.board import Board
from trolly.member import Member
import json
import smtplib
from email.mime.text import MIMEText

__version__ = '0.1'


# TODO: Put the week as YYYY-WW in the subject
# TODO: gmail doesn't display markdown :(
# TODO: we need to archive the items

def make_parser():
    """ Creates an ArgumentParser to parse the command line options. """
    parser = argparse.ArgumentParser(description='Some testing with the trello API.')

    parser.add_argument('-v', '--version', action='version', version='%(prog)s '+__version__)

    parser.add_argument('--apikey', help='The Trello API Key.')
    parser.add_argument('--token', help='The Trello auth token')
    parser.add_argument('--verbose', help='The script will tell you what it is doing', default=False, action='store_true')
    parser.add_argument('--debug', help='Set the debugging level', default=0, type=int)
    parser.add_argument('--board', help='The ID of the board to use')
    parser.add_argument('--list', help='The name of the list to use', default='Done')
    parser.add_argument('--email', help='The email address to send the report to')
    parser.add_argument('--config', help='The location of a configfile', default='config.json')

    return parser

def load_config_file(**kwargs):
    file_name = kwargs['file']

    fp = open(file_name,'rb')
    return json.load(fp)

def gen_run_config():

    # an empty dict that we will fill
    config = {}
    # what it says
    required_configs = ['token', 'apikey', 'board', 'msgServer', 'msgSubject', 'msgFrom']

    # Get the command line arguments
    parser = make_parser()
    arguments = parser.parse_args()

    # If we have a config file lets get it
    if (arguments.config):
        file_config = load_config_file(file="config.json")

    # Load the stuff we know needs to be in the config file
    config['msgFrom']  = file_config['emailFrom']
    config['msgServer'] = file_config['emailServer']
    config['msgSubject'] = file_config['emailSubject']

    # what is our api key
    if arguments.apikey:
        if os.access(arguments.apikey, os.R_OK):
            config['apikey'] = [l.strip() for l in open(arguments.apikey, 'r') if l.strip()][0]
        else:
            config['apikey'] = arguments.apikey
    else:
        config['apikey'] = file_config['apikey']

    # what is our token
    if arguments.token:
        if os.access(arguments.token, os.R_OK):
            config['token'] = [l.strip() for l in open(arguments.token, 'r') if l.strip()][0]
        else:
            config['token'] = arguments.token
    else:
        config['token'] = file_config['token']

    # For the rest Let's just itterate over 
    args = ["debug", "verbose", "board", "list", "email"] 
    for argName in args:
        if getattr(arguments, argName):
            config[argName] = getattr(arguments, argName)
        else:
            config[argName] = file_config[argName]

    # let's make sure we have everything we know we need
    for argName in required_configs:
        if config[argName] == "":
            print >> sys.stderr, 'Invalid arguments: You must specify a value for %s' % argName
            parser.print_help()
            exit(1)

    # some helpful debugging
    if config['debug']:
        print "Using API Key: %s" % config['apikey'] 
        print "Using Token: %s" % config['token']

    if (config['debug'] >= 2):
        print config

    return config

def get_list_obj(**kwargs):
    debug = kwargs['debug']
    verbose = kwargs['verbose']
    conn = kwargs['trelloConn']
    board_id = kwargs['boardID']
    list_name = kwargs['listName']

    # Get the board
    boardObj = Board(conn, board_id)

    # Find the Done list ID
    for boardListObj in boardObj.getLists():
        listDict = boardListObj.getListInformation()
        if (listDict['name'] == list_name):
            if (debug >= 1):
                print "Found %s as ID for list %s" % (listDict['id'], list_name)
            returnObj = boardListObj
        if (debug >= 2):
            print "%s : %s" % (listDict['id'], listDict['name'])

    return returnObj

def get_list_cards(**kwargs):
    debug = kwargs['debug']
    verbose = kwargs['verbose']
    listObj = kwargs['list']
    
    returnList  = []

    for cardObj in listObj.getCards():
        cardDict = cardObj.getCardInformation()
        if (debug >= 1):
            print cardDict
        if (debug >= 1):
            print "%s : %s : %s " % ( cardDict['name'], cardDict['badges']['fogbugz'], cardDict['url']) 
        returnList.append( {'id': cardDict['id'], 'idShort': cardDict['idShort'], 'name': cardDict['name'], 'url': cardDict['url'], 'case': cardDict['badges']['fogbugz'] })

    return returnList

def gen_markdown_email(**kwargs):
    debug = kwargs['debug']
    verbose = kwargs['verbose']
    cardsList = kwargs['cards']

    msg_text = "This is what we did this week\n"
    msg_text += "=============================\n"

    for card in cardsList:
        msg_text += "+ \("
        msg_text += "[%s](%s)" % (card['idShort'], card['url'])
        if card['case']:
            msg_text += "|"
            msg_text += "[%s](%s)" % (card['case'].rsplit('/')[5], card['case'])
        msg_text += "\)"
        msg_text += " %s \n" % card['name'] 

    if (debug >= 1):
        print msg_text

    return msg_text

def main():

    # What are our configs
    runConfig = gen_run_config()

    # connect to trello!
    trello_conn = Client(runConfig['apikey'], runConfig['token'])

    # get the done list object    
    doneListObj = get_list_obj(debug=runConfig['debug'], verbose=runConfig['verbose'], trelloConn=trello_conn, boardID=runConfig['board'], listName=runConfig['list'] )

    # the the information we care about from the cards in the done list
    doneCardsList = get_list_cards(debug=runConfig['debug'], verbose=runConfig['verbose'],  list=doneListObj)

    # Generate the email text
    email_msg = gen_markdown_email(debug=runConfig['debug'], verbose=runConfig['verbose'],  cards=doneCardsList)

    if runConfig['verbose']:
        print email_msg

    # send the email!
    if (runConfig['email']):
        msg = MIMEText(email_msg)
        msg['Subject'] = runConfig['msgSubject']
        msg['From'] = runConfig['msgFrom']
        msg['To'] = runConfig['email']

        s = smtplib.SMTP(runConfig['msgServer'])
        s.sendmail(runConfig['msgFrom'], [runConfig['email']], msg.as_string())
        s.quit()







if __name__ == '__main__':
    main()