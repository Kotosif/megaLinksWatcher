import re
import urllib.request
import urllib.parse
import json
import time
from os import environ
from emailService import EmailService
from databaseService import DatabaseService
import sys

def readLinkFromFile(filename):
    # Assumes the link is the first line of the file
    try:
        linkFile = open(filename, "r")
        link = linkFile.readline()
        linkFile.close()
        if link == "":
            return None
        else:
            return link
    except (IOError, FileExistsError, FileNotFoundError):
        return None


def extractURLDetails(link):
    regex = re.compile("/(.)/thread/(.*)$")
    match = regex.search(link)
    if match is None:
        raise LookupError(
            "Could not extract the board and thread number. Is the URL you gave formatted correctly?"
        )
    board = match.group(1)
    threadNumber = match.group(2)
    return (board, threadNumber)


def getThreadPostsInJSONFormat(link):
    board, threadNumber = extractURLDetails(link)
    if "archived.moe" in link:
        print("Archive link given")
        print("Sending HTTP request to get thread in HTML format...")
        req = urllib.request.Request(
            link,
            None,
            headers={
                'User-Agent':
                'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7',
                'Accept':
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })
        response = urllib.request.urlopen(req)
        return [response.read().decode('utf-8')]
    else:
        apiurl = "http://a.4cdn.org/%s/thread/%s.json" % (board,
                                                            threadNumber)
        print("Sending HTTP request to get thread in JSON format...")
        response = urllib.request.urlopen(apiurl)
        jsonResponse = json.loads(response.read().decode('utf-8'))
        posts = jsonResponse["posts"]
        return posts


def findAllMegaLinks(posts, responseType):
    # posts - a list of the posts as a json object returned from the 4chan API
    regex = re.compile(r"(https://mega\.nz/((folder\/)|(#.?!))([\w!_#-]+(<wbr>)?)+)( |<|$)")
    megaLinks = []
    matches = []
    print("Finding all mega links in thread...")
    for post in posts:
        if responseType == "json":
            try:
                comment = post["com"]
                matches = regex.findall(comment)
                for match in matches:
                    fullMatch = match[0]
                    fullMatch = fullMatch.replace("<wbr>", "")
                    fullMatch = fullMatch.replace("<", "")
                    fullMatch = fullMatch.strip()
                    megaLinks.append(fullMatch)
            except (KeyError):
                continue
        elif responseType == "html":
            matches = regex.findall(post)
            for matchedLink, _extras in matches:
                if not matchedLink in megaLinks:
                    megaLinks.append(matchedLink)
    return megaLinks


def getNewLinks(megaLinks, databaseService):
    try:
        databaseLinks = databaseService.getLinks()
        newLinks = []
        for link in megaLinks:
            if not link in databaseLinks:
                newLinks.append(link)
        return newLinks
    except (IOError, FileNotFoundError):
        print("Error opening database file %s" % databaseFilename)
        return []

def loadConfigSettings(configFilename):
    global linkFilename
    global databaseFilename
    global toAddress
    global interval
    global fromAddress
    global emailUsername
    global emailPass
    try:
        configFile = open(configFilename, "r")
        configContents = configFile.read()
        configJSON = json.loads(configContents)
        linkFilename = configJSON["urlFile"]
        databaseFilename = configJSON["databaseFile"]
        toAddress = environ["toAddress"]
        fromAddress = environ["fromAddress"]
        emailUsername = environ["emailUsername"]
        emailPass = environ["emailpass"]
        interval = configJSON["interval"]
    except (IOError, FileNotFoundError):
        print("Error opening config file %s" % configFilename)

def getURLLinkFromConfigVar():
    try:
        url = environ["url"]
        return (url, None)
    except KeyError as e:
        return ("", e)

# Config init
configFilename = "config.json"
linkFilename = ""
databaseFilename = ""
interval = 0
toAddress = ""
fromAddress = ""
emailUsername = ""
emailPass = ""
skipInitalCloudinaryLoad = False

# Main Function
if __name__ == "__main__":
    # Load config
    loadConfigSettings(configFilename)

    # Check input arguments
    if (len(sys.argv) - 1 > 0):
        if (sys.argv[1] == "--sicl"):
            skipInitalCloudinaryLoad = True
    
    # Load database
    databaseService = DatabaseService(databaseFilename, environ["cloudName"], environ["cloudinaryAPIKey"], environ["cloudinaryAPISecret"])
    if (not skipInitalCloudinaryLoad):
        databaseService.loadCloudinaryToLocalDatabase()

    # Setup SMTP Server
    smtpServer = EmailService(emailUsername, emailPass)
    smtpServer.setupSMTPServer()
    smtpServer.login()

    # Main program execution
    print("This is an application for watching Mega.nz links on 4chan threads")
    print(
        "By default, this application will look for a %s file to obtain the link of the thread to watch"
        % linkFilename)
    print("Now looking for %s file..." % linkFilename)
    link = readLinkFromFile(linkFilename)
    if link is None:
        print("Could not find %s file. Checking config variables instead." %
              linkFilename)
        link, error = getURLLinkFromConfigVar()
        if (not error is None):
            print(
                "Could not find url from config either. Please input the URL manually:"
                % linkFilename)
            while (link is None or link == ""):
                link = input()
                if (link is None or link == ""):
                    print("Please enter a URL")
    responseType = ""
    if "archived.moe" in link:
        responseType = "html"
    else:
        responseType = "json"
    while (True):
        try:
            posts = getThreadPostsInJSONFormat(link)
            megaLinks = findAllMegaLinks(posts, responseType)
            print("Megalinks found:" + megaLinks.__str__())
            newLinks = getNewLinks(megaLinks, databaseService)
            print("New links found:" + newLinks.__str__())
            if (len(newLinks) > 0):
                print("Sending email to %s" % toAddress)
                smtpServer.sendEmail(fromAddress, toAddress, "New megalinks found", "\n\n".join(newLinks))
                databaseService.saveToDatabase(newLinks)
        except urllib.error.HTTPError as httpError:
            if httpError.code == 404:
                smtpServer.sendEmail(fromAddress, toAddress, "Megalinks - Thread is closed", "The 4chan thread you were monitoring has been archived. Please update link or stop process")
            print (httpError)
            pass
        time.sleep(interval)
