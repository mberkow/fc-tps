
MB TPS Generator
================
To be clear I don't have to submit weekly TPS reports. We do have weekly kiwis, GTD advocates a weekly review, and I have found that having a summary of what I've completed lends itself to a sense of accomplishment. I recently started using a very simple [Trello](http://trello.com) [board](https://trello.com/b/djxM0V04/tps-example-board) to capture and track what I'm working on. I decided to automate the weekly review. Why?

+ Start using technologies that I should be more familiar with (Trello API, Python, Github, Markdown)
+ Help keep a log of what I've been working on.
+ At a glance see how many cards have cases (they should all have cases)
+ I never have to answer the question what should/could/might I work on _NOW_

So I wrote this script. I ended up using the [Trolly](https://github.com/plish/Trolly) library since I didn't feel like re-writing an interface to the API. I did find that it is inefficent to get boards/lists by name. The script isn't perfect and assumes a very specific workflow, but it was fun to write.

Assumptions
===========
+ We are using fastbugz style URLs and the 5th position is the case number
+ The board in question has unique list names
+ The script runs on a day of the week in question. (so the email title looks good)  

TODO
====
+ gmail doesn't display markdown :(
+ deal with labels and dropped
+ figure out when and where we need the client object

Usage
=====
    mb-tps.py [-h] [-v] [--apikey APIKEY] [--token TOKEN] [--verbose]
                    [--debug DEBUG] [--board BOARD] [--list LIST] [--email EMAIL]
                    [--config CONFIG] [--noarchive] [--nextList NEXTLIST]
                    [--todoList TODOLIST] [--nomove]

    Some testing with the trello API.

    optional arguments:
        -h, --help           Show this help message and exit
        -v, --version        Show program's version number and exit
        --apikey APIKEY      The Trello API Key.
        --token TOKEN        The Trello auth token
        --verbose            The script will tell you what it is doing
        --debug DEBUG        Set the debugging level
        --board BOARD        The ID of the board to use
        --list LIST          The name of the list to use
        --email EMAIL        The email address to send the report to
        --config CONFIG      The location of a configfile
        --noarchive          Do not archive the done items
        --nextList NEXTLIST  The list that holds the next up items
        --todoList TODOLIST  The list that holds the next up items
        --nomove             Do not move cards around
