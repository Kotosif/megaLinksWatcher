# megaLinksWatcher

This is a command line application that monitors 4chan threads for Mega.nz links.

When new links is found it then sends an email alert containing the new found links.


The application has several ways to find the URL. If all of them fail, then it will ask
the user to input the URL manually in the command line.

## Usage

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