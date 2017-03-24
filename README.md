# Botfly

Botfly is an interactive web app botnet that is comprised of two main components. The server, which is the net itself and the client which is to be run on victim machines, thus, rendering them as a ‘bot.’ The server, a Flask app, provides a web terminal to control each bot as well as prebuild Metasploit style payloads that can be launched with provided parameters. A ‘Finder’ allows the user to traverse the file system of each bot and download files from the victim machine.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

The Botfly server requires python 3.5 and several additional python modules. A requirements.txt file is included.

```
cd Botfly
```

```
pip3 install -r requirements.txt
```

### Installing

With the necessary requirements installed, the project should be clone and play.

Clone the repo

```
git clone https://github.com/Renmusxd/Botfly.git
```

run the server

```
python3.5 runserver.py
```

By default, the server will run locally at http://127.0.0.1:5500

![alt text][screenshot-index]

[screenshot-index]: Screenshot-index.png "Home Page"

## Testing Bot Connection

In order to test a bot connection, you can connect your localhost as a bot to the server. To do so, run client.py with python 2.7 (although python 3 should work as well)

```
cd client
```

```
python client.py
```

You can now select the newly connected bot by choosing said bot from the botlist sidebar which can be opened using the 'Bots' button in the navbar.

## Finder

Botfly provides an interactive bot folder traversal mechanism that can be accessed by clicking the ‘Finder’ button in the navbar.

![alt text][screenshot-finder]

[screenshot-finder]: Screenshot-finder.png "Home Page"

## Built With
* [Flask](http://flask.pocoo.org/) - The web framework used
* [Socket.IO](http://socket.io/) - Used for websocket communication between  server and client
* [Twitter Bootstrap](http://getbootstrap.com/) - Front end 

## Authors

* **Evan King** - *Cornell Hacking Club President*
* **Sumner Hearth** - *Cornell Hacking Club Vice President and Treasurer*


## Disclaimer


Botfly, it's authors, and Cornell Hacking Club are in no way responsible for misuse or for any damage that you may cause. Botfly was created as a proof of concept for academic purposes and should be utilized as such.

You agree that you use this software at your own risk.

## Acknowledgments

* Hat tip to anyone who's code was used from StackOverflow


