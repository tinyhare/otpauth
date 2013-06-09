# -*- coding: utf-8 -*-
"""
    otpauth
    ~~~~~~~

    Implements two-step verification of HOTP/TOTP.

    :copyright: (c) 2013 by Hsiaoming Yang.
    :license: BSD, see LICENSE for more details.
"""

import sys

if sys.version_info[0] == 3:
    python_version = 3
    string_type = str
else:
    python_version = 2
    string_type = unicode

import base64
import hashlib
import hmac
import struct
import time


__all__ = ['OtpAuth']


class OtpAuth(object):
    """One Time Password Authentication.

    :param secret: A secret token for the authentication.
    """

    def __init__(self, secret):
        self.secret = secret

    def hotp(self, counter=4):
        # https://tools.ietf.org/html/rfc4226
        msg = struct.pack('>Q', counter)
        digest = hmac.new(self.secret, msg, hashlib.sha1).digest()

        ob = digest[19]
        if python_version == 2:
            ob = ord(ob)

        pos = ob & 15
        base = struct.unpack('>I', digest[pos:pos + 4])[0] & 0x7fffffff
        token = base % 1000000
        return token

    def totp(self, period=30):
        """Generate a TOTP code.

        A TOTP code is an extension of HOTP algorithm.

        :param period: A period that a TOTP code is valid in seconds
        """
        # https://tools.ietf.org/html/rfc6238
        counter = int(time.time()) // period
        return self.hotp(counter)

    def valid_hotp(self, code, last=0, trials=100):
        if not valid_code(code):
            return False

        code = int(code)
        for i in xrange(last + 1, last + trials + 1):
            if self.hotp(counter=i) == code:
                return i
        return False

    def valid_totp(self, code, period=30):
        """Valid a TOTP code.

        :param code: A number than is less than 6 characters.
        :param period: A period that a TOTP code is valid in seconds
        """
        return valid_code(code) and self.totp(period) == int(code)

    def to_google(self, type, label, issuer, counter=None):
        type = type.lower()

        if type not in ('hotp', 'totp'):
            raise TypeError

        secret = encode32(self.secret)

        # https://code.google.com/p/google-authenticator/wiki/KeyUriFormat
        url = ('otpauth://%(type)s/%(label)s?secret=%(secret)s'
               '&issuer=%(issuer)s')
        if type == 'hotp' and not counter:
            raise ValueError('HOTP type authentication need counter')
        dct = dict(
            type=type, label=label, issuer=issuer,
            secret=secret, counter=counter
        )
        ret = url % dct
        if type == 'hotp':
            ret = '%s&counter=%s' % (ret, counter)
        return ret


def encode32(text):
    if isinstance(text, string_type):
        # Python3 str -> bytes
        # Python2 unicode -> str
        text = text.encode('utf-8')
    return base64.b32encode(text)


def valid_code(code):
    code = string_type(code)
    code = code.decode('utf-8')
    return code.isdigit() and len(code) <= 6