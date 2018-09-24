import re
import urllib.request
import urllib.parse
import json
import time
import smtplib
from email.message import EmailMessage


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
    try:
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
    except urllib.error.HTTPError as httpError:
        print(httpError.headers)
        print(httpError)
        raise httpError


def findAllMegaLinks(posts, responseType):
    # posts - a list of the posts as a json object returned from the 4chan API
    regex = re.compile(r"(https://mega\.nz/#.?![\w!_-]+)( |<|$)")
    megaLinks = []
    matches = []
    print("Finding all mega links in thread...")
    for post in posts:
        if responseType == "json":
            comment = post["com"]
            matches = regex.findall(comment)
        elif responseType == "html":
            matches = regex.findall(post)
        for matchedLink, _extras in matches:
            if not matchedLink in megaLinks:
                megaLinks.append(matchedLink)
    return megaLinks


def getNewLinks(megaLinks, databaseFilename):
    try:
        databaseFile = open(databaseFilename, "r")
        databaseLinks = databaseFile.readlines()
        links = []
        newLinks = []
        for link in databaseLinks:
            links.append(link.replace("\n", ""))
        for link in megaLinks:
            if not link in links:
                newLinks.append(link)
        return newLinks
    except (IOError, FileNotFoundError):
        return []


def saveLinksToFile(links, databaseFilename):
    try:
        databaseFile = open(databaseFilename, "a")
        for link in links:
            databaseFile.write(link)
            databaseFile.write("\n")
        databaseFile.close()
    except (IOError, FileNotFoundError):
        print("Error opening database file %s" % databaseFilename)


def loadConfigSettings(configFilename):
    global linkFilename
    global databaseFilename
    global toAddress
    global interval
    global fromAddress
    global emailPass
    try:
        configFile = open(configFilename, "r")
        configContents = configFile.read()
        configJSON = json.loads(configContents)
        linkFilename = configJSON["urlFile"]
        databaseFilename = configJSON["databaseFile"]
        toAddress = configJSON["email"]["toAddress"]
        fromAddress = configJSON["email"]["fromAddress"]
        emailPass = configJSON["email"]["pass"]
        interval = configJSON["interval"]
    except (IOError, FileNotFoundError):
        print("Error opening config file %s" % configFilename)


def sendEmail(server, fromAddress, toAddress, megaLinks, url):
    msg = EmailMessage()
    msg.set_content(str(megaLinks))
    msg["Subject"] = "New megalinks found"
    msg["From"] = fromAddress
    msg["To"] = toAddress
    server.send_message(msg)


def setupSMTPServer(loginDetails):
    # Make sure you have set your gmail account settings to
    # accept less secure apps
    # https://myaccount.google.com/lesssecureapps
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(True)
    server.ehlo()
    server.starttls()
    server.ehlo()
    username, password = loginDetails
    server.login(username, password)
    return server


# Config init
configFilename = "config.json"
linkFilename = ""
databaseFilename = ""
interval = 0
toAddress = ""
fromAddress = ""
emailPass = ""

# Main Function
if __name__ == "__main__":
    # Load config
    loadConfigSettings(configFilename)
    smtpServer = setupSMTPServer((fromAddress, emailPass))
    # Main program execution
    print("This is an application for watching Mega.nz links on 4chan threads")
    print(
        "By default, this application will look for a %s file to obtain the link of the thread to watch"
        % linkFilename)
    print("Now looking for %s file..." % linkFilename)
    link = readLinkFromFile(linkFilename)
    if link is None:
        print("Could not find %s file. Please input the URL manually:" %
              linkFilename)
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
            newLinks = getNewLinks(megaLinks, databaseFilename)
            print(newLinks)
            if (len(newLinks) > 0):
                print("Sending email to %s" % toAddress)
                sendEmail(smtpServer, fromAddress, toAddress, megaLinks, link)
                saveLinksToFile(newLinks, databaseFilename)
        except urllib.error.HTTPError:
            pass
        time.sleep(interval)
