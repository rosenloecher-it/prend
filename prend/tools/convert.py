from typing import Optional


class Convert:

    @staticmethod
    def convert_to_bool(text_in: str, fallback:Optional[bool]=None) -> bool:
        if not text_in:
            return fallback
        text_in = text_in.strip().lower()
        if text_in == 'false' or text_in == '0' or text_in == 'no' or text_in == 'off':
            return False
        if text_in == 'true' or text_in == '1' or text_in == 'yes' or text_in == 'on':
            return True
        return fallback

    @staticmethod
    def convert_to_int(text_in: str, fallback:Optional[int]=None) -> int:
        if text_in is None:
            return fallback
        try:
            return int(text_in)
        except ValueError:
            return fallback


    @staticmethod
    def convert_to_float(text_in: str, fallback: Optional[float] = None) -> float:
        if text_in is None:
            return fallback
        try:
            return float(text_in)
        except ValueError:
            return fallback
