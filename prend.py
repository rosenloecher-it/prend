import sys
from prend.process import Process


def main():
    process = Process()

    exit_code = process.init()
    if exit_code is not None:
        sys.exit(exit_code)

    process.register_rules_from_config()

    # run endless loop
    return process.run()


if __name__ == '__main__':
    sys.exit(main())
