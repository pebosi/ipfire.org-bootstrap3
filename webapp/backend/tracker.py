#!/usr/bin/python

from __future__ import division

import random

from misc import Object

def decode_hex(s):
	ret = []
	for c in s:
		for i in range(256):
			if not c == chr(i):
				continue

			ret.append("%02x" % i)

	return "".join(ret)

class Tracker(Object):
	@property
	def tracker_id(self):
		return self.settings.get("tracker_id", "TheIPFireTorrentTracker")

	def _fuzzy_interval(self, interval, fuzz=60):
		return interval + random.randint(-fuzz, fuzz)

	@property
	def interval(self):
		return self.settings.get_int("tracker_interval", 3600)

	@property
	def min_interval(self):
		interval = self.settings.get_int("tracker_min_interval", self.interval // 2)

		return self._fuzzy_interval(interval)

	@property
	def numwant(self):
		return self.settings.get_int("tracker_numwant", 50)

	def get_peers(self, info_hash, limit=None, random=True, no_peer_id=False, ipfamily=None):
		query = "SELECT * FROM tracker WHERE last_update >= NOW() - INTERVAL '%ss'"
		args = [self.interval,]

		if info_hash:
			query += " AND hash = %s"
			args.append(info_hash)

		if random:
			query += " ORDER BY RANDOM()"

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		peers = []
		for row in self.db.query(query, *args):
			peer6 = None
			peer4 = None

			if row.address6 and row.port6:
				peer6 = {
					"ip" : row.address6,
					"port" : row.port6,
				}

			if row.address4 and row.port4:
				peer4 = {
					"ip" : row.address4,
					"port" : row.port4,
				}

			if not no_peer_id:
				if peer6:
					peer6["peer id"] = row.id

				if peer4:
					peer4["peer id"] = row.id

			if peer6:
				peers.append(peer6)

			if peer4:
				peers.append(peer4)

		return peers

	def cleanup_peers(self):
		"""
			Remove all peers that have timed out.
		"""
		self.db.execute("DELETE FROM tracker \
			WHERE last_update < NOW() - INTERVAL '%ss'", self.interval + 600)

	def update_peer(self, peer_id, info_hash, address6=None, port6=None,
			address4=None, port4=None, downloaded=None, uploaded=None, left_data=None):
		if address4 and address4.startswith("172.28.1."):
			address = "178.63.73.246"

		query = "UPDATE tracker SET last_update = NOW()"
		args = []

		if address6:
			query += ", address6 = %s"
			args.append(address6)

		if port6:
			query += ", port6 = %s"
			args.append(port6)

		if address4:
			query += ", address4 = %s"
			args.append(address4)

		if port4:
			query += ", port4 = %s"
			args.append(port4)

		if downloaded:
			query += ", downloaded = %s"
			args.append(downloaded)

		if uploaded:
			query += ", uploaded = %s"
			args.append(uploaded)

		if left_data:
			query += ", left_data = %s"
			args.append(left_data)

		query += " WHERE id = %s AND hash = %s"
		args += [peer_id, info_hash]

		self.db.execute(query, *args)

	def complete(self, info_hash):
		ret = self.db.get("SELECT COUNT(*) AS c FROM tracker \
			WHERE hash = %s AND left_data = 0", info_hash)

		if ret:
			return ret.c

	def incomplete(self, info_hash):
		ret = self.db.get("SELECT COUNT(*) AS c FROM tracker \
			WHERE hash = %s AND left_data > 0", info_hash)

		if ret:
			return ret.c

	def handle_event(self, event, peer_id, info_hash, **kwargs):
		# started
		if event == "started":
			self.insert_peer(peer_id, info_hash, **kwargs)

		# stopped
		elif event == "stopped":
			self.remove_peer(peer_id, info_hash)

	def peer_exists(self, peer_id, info_hash):
		ret = self.db.get("SELECT COUNT(*) AS c FROM tracker \
			WHERE id = %s AND hash = %s", peer_id, info_hash)

		if ret and ret.c > 0:
			return True

		return False

	def insert_peer(self, peer_id, info_hash, address6=None, port6=None, address4=None, port4=None):
		exists = self.peer_exists(peer_id, info_hash)
		if exists:
			return

		self.db.execute("INSERT INTO tracker(id, hash, address6, port6, address4, port4) \
			VALUES(%s, %s, %s, %s, %s, %s)", peer_id, info_hash, address6, port6, address4, port4)

	def remove_peer(self, peer_id, info_hash):
		self.db.execute("DELETE FROM tracker \
			WHERE id = %s AND hash = %s", peer_id, info_hash)

	def scrape(self, info_hashes):
		ret = {
			"files" : {},
			"flags" : {
				"min_request_interval" : self.interval,
			}
		}

		if info_hashes:
			for info_hash in info_hashes:
				ret["files"][info_hash] = {
					"complete"   : self.complete(info_hash),
					"incomplete" : self.incomplete(info_hash),
					"downloaded" : 0,
				}

		return ret


##### This is borrowed from the bittorrent client libary #####

def decode_int(x, f):
    f += 1
    newf = x.index('e', f)
    n = int(x[f:newf])
    if x[f] == '-':
        if x[f + 1] == '0':
            raise ValueError
    elif x[f] == '0' and newf != f+1:
        raise ValueError
    return (n, newf+1)

def decode_string(x, f):
    colon = x.index(':', f)
    n = int(x[f:colon])
    if x[f] == '0' and colon != f+1:
        raise ValueError
    colon += 1
    return (x[colon:colon+n], colon+n)

def decode_list(x, f):
    r, f = [], f+1
    while x[f] != 'e':
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return (r, f + 1)

def decode_dict(x, f):
    r, f = {}, f+1
    while x[f] != 'e':
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return (r, f + 1)

decode_func = {}
decode_func['l'] = decode_list
decode_func['d'] = decode_dict
decode_func['i'] = decode_int
decode_func['0'] = decode_string
decode_func['1'] = decode_string
decode_func['2'] = decode_string
decode_func['3'] = decode_string
decode_func['4'] = decode_string
decode_func['5'] = decode_string
decode_func['6'] = decode_string
decode_func['7'] = decode_string
decode_func['8'] = decode_string
decode_func['9'] = decode_string

def bdecode(x):
    try:
        r, l = decode_func[x[0]](x, 0)
    except (IndexError, KeyError, ValueError):
        raise Exception("not a valid bencoded string")
    if l != len(x):
        raise Exception("invalid bencoded value (data after valid prefix)")
    return r

from types import StringType, IntType, LongType, DictType, ListType, TupleType


class Bencached(object):

    __slots__ = ['bencoded']

    def __init__(self, s):
        self.bencoded = s

def encode_bencached(x,r):
    r.append(x.bencoded)

def encode_int(x, r):
    r.extend(('i', str(x), 'e'))

def encode_bool(x, r):
    if x:
        encode_int(1, r)
    else:
        encode_int(0, r)

def encode_string(x, r):
    r.extend((str(len(x)), ':', x))

def encode_list(x, r):
    r.append('l')
    for i in x:
        encode_func[type(i)](i, r)
    r.append('e')

def encode_dict(x,r):
    r.append('d')
    ilist = x.items()
    ilist.sort()
    for k, v in ilist:
        r.extend((str(len(k)), ':', k))
        encode_func[type(v)](v, r)
    r.append('e')

encode_func = {}
encode_func[Bencached] = encode_bencached
encode_func[IntType] = encode_int
encode_func[LongType] = encode_int
encode_func[StringType] = encode_string
encode_func[ListType] = encode_list
encode_func[TupleType] = encode_list
encode_func[DictType] = encode_dict

try:
    from types import BooleanType
    encode_func[BooleanType] = encode_bool
except ImportError:
    pass

def bencode(x):
    r = []
    encode_func[type(x)](x, r)
    return ''.join(r)
