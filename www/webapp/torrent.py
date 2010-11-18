#!/usr/bin/python

import time

import tornado.database


def decode_hex(s):
	ret = []
	for c in s:
		for i in range(256):
			if not c == chr(i):
				continue

			ret.append("%0x" % i)

	return "".join(ret)

class Tracker(object):
	id = "The%20IPFire%20Torrent%20Tracker"

	# Intervals
	interval = 60*60
	min_interval = 30*60

	numwant = 50

	def __init__(self):
		self.db = tornado.database.Connection(
			host="mysql.ipfire.org",
			database="tracker",
			user="webapp",
		)

	def _fetch(self, hash, limit=None, random=False, completed=False, no_peer_id=False):
		query = "SELECT * FROM peers WHERE last_update >= %d" % self.since

		if hash:
			query += " AND hash = '%s'" % hash

		if completed:
			query += " AND left_data = 0"
		else:
			query += " AND left_data != 0"

		if random:
			query += " ORDER BY RAND()"

		if limit:
			query += " LIMIT %s" % limit

		peers = []
		for peer in self.db.query(query):
			if not peer.ip or not peer.port:
				continue

			peer_dict = {
				"ip" : str(peer.ip),
				"port" : int(peer.port),
			}

			if not no_peer_id:
				peer_dict["peer id"] = str(peer.id),

			peers.append(peer_dict)

		return peers

	def get_peers(self, hash, **kwargs):
		return self._fetch(hash, **kwargs)

	def get_seeds(self, hash, **kwargs):
		kwargs.update({"completed" : True})
		return self._fetch(hash, **kwargs)

	def complete(self, hash):
		return len(self.get_seeds(hash))

	def incomplete(self, hash):
		return len(self.get_peers(hash))

	def event_started(self, hash, peer_id):
		# Damn, mysql does not support INSERT IF NOT EXISTS...
		if not self.db.query("SELECT id FROM peers WHERE hash = '%s' AND peer_id = '%s'" % (hash, peer_id)):
			self.db.execute("INSERT INTO peers(hash, peer_id) VALUES('%s', '%s')" % (hash, peer_id))

		if not hash in [h["hash"] for h in self.hashes]:
			self.db.execute("INSERT INTO hashes(hash) VALUES('%s')" % hash)

	def event_stopped(self, hash, peer_id):
		self.db.execute("DELETE FROM peers WHERE hash = '%s' AND peer_id = '%s'" % (hash, peer_id))

	def event_completed(self, hash, peer_id):
		self.db.execute("UPDATE hashes SET completed=completed+1 WHERE hash = '%s'" % hash)

	def scrape(self, hashes=[]):
		ret = {}
		for hash in self.db.query("SELECT hash, completed FROM hashes"):
			hash, completed = hash.hash, hash.completed

			if hashes and hash not in hashes:
				continue

			ret[hash] = {
				"complete" : self.complete(hash),
				"downloaded" : completed or 0,
				"incomplete" : self.incomplete(hash),
			}

		return ret

	def update(self, hash, id, ip=None, port=None, downloaded=None, uploaded=None, left=None):
		args = [ "last_update = '%s'" % self.now ]

		if ip:
			if ip.startswith("172.28.1."):
				ip = "178.63.73.246"

			args.append("ip='%s'" % ip)

		if port:
			args.append("port='%s'" % port)

		if downloaded:
			args.append("downloaded='%s'" % downloaded)

		if uploaded:
			args.append("uploaded='%s'" % uploaded)

		if left:
			args.append("left_data='%s'" % left)

		if not args:
			return

		query = "UPDATE peers SET " + ", ".join(args) + \
			" WHERE hash = '%s' AND peer_id = '%s'" % (hash, id)

		self.db.execute(query)

	@property
	def hashes(self):
		return self.db.query("SELECT * FROM hashes");

	@property
	def now(self):
		return int(time.time())

	@property
	def since(self):
		return int(time.time() - self.interval)


tracker = Tracker()


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
