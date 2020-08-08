![Chime Banner](https://raw.githubusercontent.com/realmayus/chime/master/assets/chime_banner.png?token=AJC6B5VTHEZ5UHNY7QNDCU263LCCK)
<p align="center"><strong>A scalable, intuitive and easy-to-use music bot with custom playlists for Discord.</strong></p>

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/0154ebd7b9284606951bfc6429701324)](https://app.codacy.com/manual/realmayus/chime?utm_source=github.com&utm_medium=referral&utm_content=realmayus/chime&utm_campaign=Badge_Grade_Dashboard)


#### Get Started

Don't want to host it on your own? You can invite a hosted version of chime by clicking [here](https://discord.com/api/oauth2/authorize?client_id=716032601646694531&permissions=37055552&scope=bot)

**Chime's website:** https://chime.realmayus.xyz

**Related Projects**:

chime-web, the frontend of the chime website: https://github.com/realmayus/chime-web

chime-backend, the backend of the chime website: https://github.com/realmayus/chime-backend

#### Host chime on your own
_If you however_ want it to host chime on your own, choose one of the two methods to install chime:

##### 1) Automatic script

```
source <(curl -s https://gist.githubusercontent.com/realmayus/b313066aba5e7acd34711b03b6fd762e/raw/setup-chime-vm.sh)
```
This will install chime automatically in the folder `chime` in your home folder. [The script](https://gist.githubusercontent.com/realmayus/b313066aba5e7acd34711b03b6fd762e/raw/setup-chime-vm.sh) will automatically download OpenJDK 13 and install it, install required python packages, setup a virtual environment, clone the repository, create required files and install chime.
You just have to enter your firebase SDK key in `secret/firebase_creds.json` and your tokens in `secret/token.ini`.
The script was tested on Ubuntu 20.04 LTS. **Please make sure that you have Python >= 3.7 installed, otherwise, our music backend Lavalink might not work.**

To start chime, simply start Lavalink using `java -jar lavalink/Lavalink.jar` (I recommend you to do this in a `screen`) and then start chime by simply executing `chime`. To uninstall it, use `python3 -m pip uninstall chime-discord`. *Make sure that you're in the virtual environment* (`source venv/bin/activate`). 

##### 2) Manually
1. Install JDK 13. *It has to be JDK 13* 
2. Make sure that you have installed PIP and Python >= 3.7
3. Clone the chime repository.
4. Setup a virtual environment using `python3 -m virtualenv venv` and enter it using `source venv/bin/activate`
5. Create a folder called `secret` in the chime repository that you've cloned and create two files, called `firebase_creds.json` and `token.ini`. Insert your firebase SDK key in the first one and your tokens in the second one.
6. Install the discord.py library using `python3 -m pip install discord`
7. Install chime using `python3 -m pip install .`
8. Done! To uninstall chime, use `python3 -m pip uninstall chime-discord`, make sure you're in the current virtual environment.

##### `token.ini`
The token.ini file should contain at least one token:
* a discord bot token

It is recommended to add one additional token:
* a secondary discord bot token, so that you can minimize downtime while you're developing something

The file should look like this:
```ini
[token]
token = YOUR_PRIMARY_TOKEN
; token-dev = YOUR_SECONDARY_TOKEN  <-- OPTIONAL
```


You have to update the chime binary after changing anything:

##### Updating the chime binary
Every time you have changed any file, you have to update the chime binary so that your OS always loads the most recent version when you run `chime`.
To do that, enter your virtual environment using `source venv/bin/activate` and run:
`python3 -m pip install .`

##### Updating chime itself
If new commits were commited and you want to update chime, simply execute `git pull` in the root directory of chime and then update the chime binary.


#### Service file
If you want to use a process manager to start/stop chime automatically, you can use systemd with this config file:
https://gist.github.com/realmayus/cc18a29aadff5b92c776632f8632645f
Put that in /etc/systemd/system/chime.service and start the service with `service chime start` and stop it with `service chime stop`. You can see the logs using `journalctl -u chime.service`.

#### Asset Credits
Music Disc with Note: Icon made by Freepik from www.flaticon.com
