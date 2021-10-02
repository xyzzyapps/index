# Welcome to Index!

This is a project built during the reinvention jam of handmade network!
Index is a browser with some twists.

# Current Status

The project is usable for local setups. It is highly insecure as it supports arbitrary code execution. Browsers work well because code is executed in a secure sandbox.

The current project functions like Gopher/Gemini with markdown support.

- Note management
- Supports embedding youtube videos
- Generated embeds via python code
- Supports embedded note sections in other notes via Xanadu Style transclusions
- Code snippet management, with basic literate programming
- Task list
- Embed any website or html page for js visualisations
- A simple email integration is implemented where the remote page can provide a "button"
which onclick sends an email via the users smtp

# Setup

```
git clone https://github.com/xyzzyapps/index.git
virtualenv env
source env/bin/activate

vim user_metadata.yaml # This file has details with which you send mails

cd server
python -m http.server 8083 # start the http server in any folder for testing

In another tab start the browser with,

python index.py "http://127.0.0.1:8083"
```


