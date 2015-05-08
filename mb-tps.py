#!/usr/bin/env python

import argparse
import datetime
import sys
import os
from trolly.client import Client
from trolly.board import Board
from trolly.member import Member
import json
import smtplib
from email.mime.text import MIMEText

__version__ = '0.1'

# TODO: gmail doesn't display markdown :(
# TODO: deal with labels and dropped
# TODO: figure out when and where we need the client object

# ASSUMPTION: We are using fastbugz style URLs and the 5th possition is the case number
# ASSUMPTION: The board in question has unique list names
# ASSUMPTION: The script runs on a day of the week in question. (so the email title looks good)

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
    parser.add_argument('--noarchive', help='Do not archive the done items', default=False, action='store_true')
    parser.add_argument('--nextList', help='The list that holds the next up items')
    parser.add_argument('--todoList', help='The list that holds the next up items')
    parser.add_argument('--nomove', help='Do not move cards around', default=False, action='store_true')

    return parser

def load_config_file(**kwargs):
    file_name = kwargs['file']

    fp = open(file_name,'rb')
    return json.load(fp)

def gen_run_config():

    # an empty dict that we will fill
    config = {}
    # What is the year and weeknumber?
    now = datetime.datetime.now()
    config['week'] = "%s-W%s" %(now.year, now.isocalendar()[1])
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
    args = ["debug", "verbose", "board", "list", "email", "noarchive", "nextList", "todoList", "nomove"] 
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

def archive_done_cards(**kwargs):
    debug = kwargs['debug']
    verbose = kwargs['verbose']
    listObj = kwargs['list']

    for cardObj in listObj.getCards():
        if (verbose):
            print "Archiving card: %s" % cardObj.id
        result = cardObj.updateCard({ "closed": "true" })

def move_all_list_cards(**kwargs):
    debug = kwargs['debug']
    verbose = kwargs['verbose']
    fromListObj = kwargs['fromListObj']
    toListID = kwargs['toListID']

    for cardObj in fromListObj.getCards():
        if (verbose):
            print "Moving card %s from list %s to list %s" % (cardObj.id, fromListObj.id, toListID)
        result = cardObj.updateCard( {"idList" : toListID})


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
    thisweek = kwargs['thisweek']

    msg_text = "This is what we did this week %s\n" % thisweek
    msg_text += "=============================\n"

    for card in cardsList:
        if(verbose):
            print "Done Card: %s" % card['name']
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
    email_msg = gen_markdown_email(debug=runConfig['debug'], verbose=runConfig['verbose'],  cards=doneCardsList, thisweek=runConfig['week'])

    # Archive all the cards in the done list
    if ( not runConfig['noarchive'] ):
        archive_done_cards(debug=runConfig['debug'], verbose=runConfig['verbose'],  list=doneListObj)

    # Move the up next cards to this week 
    if ( runConfig['nextList'] and runConfig['todoList'] and not runConfig['nomove']):
        # Get the list object for nextlist
        nextListObj = get_list_obj(debug=runConfig['debug'], verbose=runConfig['verbose'], trelloConn=trello_conn, boardID=runConfig['board'], listName=runConfig['nextList'] )
        # Get the list object for todolist
        todoListObj = get_list_obj(debug=runConfig['debug'], verbose=runConfig['verbose'], trelloConn=trello_conn, boardID=runConfig['board'], listName=runConfig['todoList'] )
        # Move the cards
        result = move_all_list_cards(debug=runConfig['debug'], verbose=runConfig['verbose'], fromListObj=nextListObj, toListID=todoListObj.id)

    # send the email!
    if (runConfig['email']):
        msg = MIMEText(email_msg)
        msg['Subject'] = runConfig['msgSubject'] + runConfig['week']
        msg['From'] = runConfig['msgFrom']
        msg['To'] = runConfig['email']

        s = smtplib.SMTP(runConfig['msgServer'])
        s.sendmail(runConfig['msgFrom'], [runConfig['email']], msg.as_string())
        s.quit()

if __name__ == '__main__':
    main()
