import sys
from prend.process import Process
from app.fronstor.fronstor_rule import FronstorRule


def main():
    process = Process()

    exit_code = process.init()
    if exit_code is not None:
        sys.exit(exit_code)

    process.register_rule(FronstorRule())

    # run endless loop
    return process.run()


if __name__ == '__main__':
    sys.exit(main())
