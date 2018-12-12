# prend

**P**ython **R**ule **En**gine **D**aemon - an external rule engine for [OpenHAB](https://www.openhab.org/)

Write your own [OpenHAB](https://www.openhab.org/) rules with Python 3. Use your favorite editor, debug your code and write unittests!


## Features

- external rule engine for OpenHAB. Reads and caches states of items, groups and things.
- connects to OpenHAB via REST API (see [REST demo](http://demo.openhab.org:8080/doc/index.html))
- gets updated by change notifications about state changes
- runs as deamon
- write you own rules and subscribe for state changes and cron events
- change OpenHAB states via COMMANDs and UPDATEs
- programming language: Python 3 (use your favorite tools incl. debugger, unittests, code inspection)


## Disclaimer

- Tested only under Linux and I have no intentions to support other operating systems.
- At moment the code is provided only as sample project, not as python package.
- This is a very early version, so I expect some API changes...
- There are lots of different devices available for OpenHAB. Each of them could provide different values and types which could lead to unexpected behavior.


## Motivation

During an OpenHAB update from 2.1 to 2.3 I run into problems with the OpenHAB rule engine.

There were some issues about
- Lambda functions couldn't be used without locks anymore. (https://github.com/eclipse/smarthome/issues/6234)
- (But) try-finally constructs got unreliable too. There were situations were the "finally"-branch was not called and let the system in a locked state. (A related issue: https://github.com/eclipse/smarthome/issues/6218)


Issues were filed as bug, but the immediate solution was to change my code, even if it took some time. I had difficulties to find the problems without proper tooling (debugger, unittests). Some of the strange situations occured only during startup of OpenHAB.

The alternative [JSR 223](https://www.openhab.org/docs/configuration/jsr223-js.html) supports only Python 2.7 and that Javascript was also quite of cumbersome (no ES6). Both implementations base on a the (Java) Oracle Nashorn engine which is announced as deprecated.

So the question was, how to make my code future proof and easy to handle...


## Startup

```bash
# get the code
$ git clone --depth=1
$ cd prend

# create virtual environment (make sure, that python3 and virtualenv are installed)
$ virtualenv -p $(type -p python3) venv
# activate venv
$ source ./venv/bin/activate
# check python version => 3.6 and above
$ python --version

# install required packages
pip install -r requirements.txt
```

Configure the OpenHAB items used in ./app/test_rule.py ($OPENHAB_CONF_DIR/items/*.items):
```
Switch dummy_switch 		"dummy_switch"
String dummy_string 		"dummy_string [%s]"
Number dummy_number 		"dummy_number [%d]"
Number dummy_number_2 		"dummy_number_2 [%d]"
```

Configure app via config file ($PROJECT_DIR/prend.conf):
```
[openhab]
rest_base_url=http://127.0.0.1:8080/rest
username=
password=

[system]
work_dir=./__test__
pid_file=./__test__/prend.pid

[logging]
loglevel=debug
logfile=./__test__/prend.log
```

Run:
```bash
# start via bash script (activates venv)
$ $PROJECT_DIR/prend.sh --help
$ $PROJECT_DIR/prend.sh --status

# or do the venv activation manually
$ cd $PROJECT_DIR
$ ./venv/bin/activate

# show command line options
$ python prend.py --help

$ python prend.py --status         # check settings
$ python prend.py --foreground     # for debugging
$ python prend.py --start          # start daemon
$ python prend.py --stop           # stop daemon
```

## Provide your own rules

provide a rule class:
- see the sample rule $PROJECT_DIR/app/test_rule.py
- inherit from pred.Rule
- implement "register_actions" to subscribe to changes or cron actions
- implement "notify_action" and put your code here
- access states via super class functions

register your rule class in $PROJECT_DIR/prend.py:
```python
def main():
    process = Process()
    ...

    # todo - register your rule classes
    process.register_rule(TestRule())

    # run endless loop
    return process.run()
    ...
```

## Package dependencies

(in addition to requirements.txt)

- multiprocessing_logging
    - https://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python
    - https://github.com/jruere/multiprocessing-logging
- aiosseclient
    - for OpenHAB notifications
    - Asynchronous Server Side Events (SSE) Client
    - https://github.com/ebraminio/aiosseclient
    - pip install git+https://github.com/ebraminio/aiosseclient
- cannibalised projects
    - for deamon: https://github.com/serverdensity/python-daemon
    - python-openhab: https://github.com/sim0nx/python-openhab

