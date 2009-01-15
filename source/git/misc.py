# -*- coding: utf-8 -*-

# Copyright © 2008 - Steve Frécinaux
# License: LGPL 2

__all__ = ['issha1']

import re

SHA1_PATTERN = re.compile('^[a-f0-9]{40}$')

def issha1(s):
    return SHA1_PATTERN.match(s) is not None
