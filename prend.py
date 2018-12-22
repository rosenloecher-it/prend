import sys
from prend.process import Process
from app.fronstor.fronstor_rule import FronstorRule
from app.tehu_form_rule import TehuFormRule
from app.led_status_rule import LedStatusRule


def main():
    process = Process()

    exit_code = process.init()
    if exit_code is not None:
        sys.exit(exit_code)

    # process.register_rule(FronstorRule())
    # process.register_rule(TehuFormRule())
    process.register_rule(LedStatusRule())

    # run endless loop
    return process.run()


if __name__ == '__main__':
    sys.exit(main())
