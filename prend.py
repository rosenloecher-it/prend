import sys
from prend.process import Process
from prend_app.test_rule import TestRule


def main():
    process = Process()

    exit_code = process.init()
    if exit_code is not None:
        sys.exit(exit_code)

    # todo - register your rule classes
    process.register_rule(TestRule())

    # run endless loop
    return process.run()


if __name__ == '__main__':
    sys.exit(main())
