# prend

**P**ython **R**ule **En**gine **D**aemon - an external rule engine for [OpenHAB]

Write your own [OpenHAB] rules with Python 3. Use your favorite editor, debug your code and write unittests!


## Features

- external rule engine for OpenHAB. Reads and caches states of items, groups and things.
- connects to OpenHAB via REST API (see [REST demo](http://demo.openhab.org:8080/doc/index.html))
- gets updated by change notifications about state changes
- runs as deamon
- write your own rules and subscribe for state changes and cron events
- change OpenHAB states via COMMANDs and UPDATEs
- programming language: Python 3 (use your favorite tools incl. debugger, unittests, code inspection)


## Disclaimer

- Tested only under Linux and I have no intentions to support other operating systems.
- At moment the code is provided only as sample project, not as python package.
- No service script is provided so far to run it as system daemon.
- Python programming skills required.
- HTTP authenification (username/password) is not tested.
- Tested with OpenHAB 2.3 Release (only)


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

Configure the OpenHAB items used in [sample_rule.py]($OPENHAB_CONF_DIR/items/*.items):
```
Switch dummy_switch 		"dummy_switch"
String dummy_string 		"dummy_string [%s]"
Number dummy_number 		"dummy_number [%d]"
Number dummy_number_2 		"dummy_number_2 [%d]"
```

Put the items into your OpenHAB \*.sitemap:
```
sitemap default label="Smarthome" {
    Frame label="Test" {
        Default item=dummy_switch
        Default item=dummy_string
        Setpoint item=dummy_number minValue=-100 maxValue=100 step=1
        Default item=dummy_number_2
    }
}
```


Configure app via config file ($PROJECT_DIR/prend.conf):
```
[openhab]
rest_base_url=http://127.0.0.1:8080/rest
username=
password=
simulate_sending=False

[system]
work_dir=./__work__
pid_file=./__work__/prend.pid

[logging]
loglevel=debug
logfile=./__work__/prod.log
log_config_file=
```

Via *log_config_file* you can configure a Python logging ini file - [see the Hitchhiker's guide](https://docs.python-guide.org/writing/logging/#example-configuration-via-an-ini-file).
The *logfile* is taken over by using the key *default_logfile*. But be carefully, the app won't start with a wrong configuration.


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
$ python prend.py --ensure         # ensure that the daemon is running (e.g. call from cron)
$ python prend.py --stop           # stop daemon
```


## Provide your own rules

See [$PROJECT_DIR/app/sample_rule.py][sample_rule.py] and all functions provided by the base class.

Create a new rule class:
- inherit from prend.Rule
- implement "register_actions" to subscribe to changes or cron actions
- implement "notify_action" and put your code here
- access states via super class functions
- read entries from configuration via super class functions

register your rule class in [/$PROJECT_DIR/prend.py](https://github.com/rosenloecher-it/prend/blob/master/prend.py):
```python
def main():
    process = Process()
    ...

    # todo - register your rule classes
    process.register_rule(SampleRule())

    # run endless loop
    return process.run()
```


## Maintainer & License

GPLv3 © [Raul Rosenlöcher](https://github.com/rosenloecher-it)

The code is available at [GitHub][home].


[home]: https://github.com/rosenloecher-it/prend
[OpenHAB]: https://www.openhab.org/
[sample_rule.py]: https://github.com/rosenloecher-it/prend/blob/master/app/sample_rule.py

