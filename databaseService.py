import cloudinary
import cloudinary.uploader
import cloudinary.api
import urllib.request
import urllib.parse
import gzip

class DatabaseService:

    def __init__(self, databaseName, cloudName, cloudinaryAPIKey, cloudinaryAPISecret):
        self.databaseName = databaseName
        self.cloudName = cloudName
        self.cloudinaryAPIKey = cloudinaryAPIKey
        self.cloudinaryAPISecret = cloudinaryAPISecret
        cloudinary.config(
            cloud_name = cloudName,
            api_key = cloudinaryAPIKey,
            api_secret = cloudinaryAPISecret
        )

    def getLinks(self):
        databaseFile = open(self.databaseName, "a+")
        databaseFile.seek(0)
        databaseLinks = databaseFile.readlines()
        formattedLinks = []
        for link in databaseLinks:
            formattedLinks.append(link.replace("\n", ""))
        return formattedLinks

    def saveToDatabase(self, links, overwrite=False):
        try:
            databaseFile = None
            if (overwrite):
                databaseFile = open(self.databaseName, "w")
            else:
                databaseFile = open(self.databaseName, "a")
            for link in links:
                databaseFile.write(link)
                databaseFile.write("\n")
            databaseFile.close()
            response = cloudinary.uploader.upload(self.databaseName, resource_type="raw", use_filename=True, unique_filename=False, overwrite=True)
            print("Cloudinary Upload Response:\n" + str(response))
        except (IOError, FileNotFoundError):
            print("Error opening database file %s" % self.databaseName)
    
    def loadCloudinaryToLocalDatabase(self):
        database = cloudinary.utils.cloudinary_url(self.databaseName)
        databaseURL = database[0].replace("image", "raw")
        req = urllib.request.Request(
                databaseURL,
                None,
                headers={
                    'User-Agent':
                    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7',
                    'Accept':
                    'text/plain',
                    'Cache-Control':
                    'no-cache'
                })
        response = urllib.request.urlopen(req)
        lines = ""
        try:
            lines = response.read().decode('utf-8')
        except UnicodeDecodeError:
            lines = gzip.decompress(response.read()).decode('utf-8')
        links = lines.split("\r\n")
        self.saveToDatabase(links, True)
