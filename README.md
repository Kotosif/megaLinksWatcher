# megaLinksWatcher

This is a command line application that monitors 4chan threads for Mega.nz links.

When new links is found it then sends an email alert containing the new found links.

This application can be hosted on Heroku, and if you wish to do this then Cloudinary is required.


The application has several ways to find the URL. If all of them fail, then it will ask
the user to input the URL manually in the command line.

Install requirements by doing:
`pip install -r requirements.txt`

## Setup

**Step 1.**

Clone the repo and edit the config.json file as desired.

`interval` determines how often to check the thread in seconds.

`urlFile` is the file it looks for to find the URL of the thread to monitor.

`databaseFile` is the file where it stores the seen links.

**Step 2**

Then add the following to your environment variables.

`fromAddress` is the email address to send from. This application uses the Google's SMTP server, hence a Gmail account is required here.

`toAddress` is the email address to send to. Can be the same as `fromAddress`

`emailPass` is the password for the `fromAddress`.

`url` is an **optional** variable. By default it will look for a file to obtain the link of the thread to monitor. Failing that it will try to look for this.

**Step 3**

This application uses Cloudinary to fetch the database of seen links. This is because Heroku has a ephemeral filesystem so I needed a free way to host the text file that contained the seen links.  Currently there is no way to switch this off right now (planned feature). 

As a result, you should create a Cloudinary account and add these values to the environment variables:

`cloudName` is the cloud name of the Cloudinary repository.

`cloudinaryAPIKey` is the API key of the Cloudinary repository.

`cloudinaryAPISecret` is the API secret of the Cloudinary repository.

## Usage

Run the application on the command line with `python megalinkswatcher.py`

Optional parameters:

`--sicl` - Skips initial Cloudinary load