# Item Catalog: Phone database
This is the third project for "Full Stack Web Developer Nanodegree" on Udacity.

## Dependencies
- [Vagrant](https://www.vagrantup.com/)
- [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

## Requirements

The project has been run from a vagrant virtual machine, but basically the main requirements are the following:

- [Python 2.7]https://www.python.org/downloads/ "Download Python"
- [SQLite]https://www.sqlite.org/download.html "Download SQLite"
- [SQLAlchemy]http://www.sqlalchemy.org/download.html "Download SQLAlchemy"
- [Flask]http://flask.pocoo.org/ "Flask Website"
- Python libraries: [httplib2]https://github.com/jcgregorio/httplib2 "GitHub repository for httplib2", [oauth2client]https://github.com/google/oauth2client "GitHub repository for oauth2client" and [Requests]http://docs.python-requests.org/ "Reqests Website"

## Usage

Launch the Vagrant VM from inside the *vagrant* folder with:

`vagrant up`

Then access the shell with:

`vagrant ssh`

Then move inside the catalog folder:

`cd /vagrant/catalog`

Populate the database 

`python seeder.py`

Then run the application:

`python application.py`

After the last command you are able to browse the application at this URL:

`http://localhost:5000/`