import getopt, sys, os, urllib, urllib2, re, urlparse, os, threading, signal
from optparse import OptionParser, OptionGroup

class Service(threading.Thread):
    def __init__(self, type, url, regex, exit_on_match, hash):
        threading.Thread.__init__(self)
        self.type = type
        self.url = url
        self.hash = hash if hash != None else ""
        self.regex = regex.replace('{HASH}', self.hash)
        self.args = {}
        self.name = urlparse.urlparse(url)[1]
        self.exit_on_match = exit_on_match

        if self.type == 'POST':
            self.args = self.__parseArgs()

    def run(self):
        global cracked
        cleartext = self.__crack(self.hash)
        if cleartext != None:
            print("!!!\t The plaintext of %s is '%s' (found on %s)" % (self.hash, cleartext, self.name))
            if self.exit_on_match == True:
                os.kill(os.getpid(), signal.SIGTERM)

    def __crack(self, hash):
        data = ''
        try:
            if self.type == 'GET':
                url = self.url.replace('{HASH}', hash)
                data = self.__exec_get(url)
            else:
                url = self.url.replace('{HASH}', hash)
                args = self.args
                for name, value in args.interitems():
                    args[name] = value.replace('{HASH}', hash)
                data = self.__exec_post(url, args)
        except:
            pass
        return self.__xtract_data(data)

    def __xtract_data(self, data):
        m = re.search(self.regex, data)
        return m.group(1) if m is not None else None

    def __exec_get(self, url):
        return urllib2.urlopen(urllib2.Request(url)).read()
    def __exec_post(self, url):
        return urllib2.urlopen(urllib2.Request(url, urllib.urlencode(data))).read()
    def __parseArgs(self):
        m = re.search("([^\[]+)\[([^\]]+)\]", self.url)
        self.url = m.group(1)
        params = m.group(2)
        params = params.split(',')
        args = {}

        for param in params:
            (k,v) = param.split(':')
            args[k] = v
        return args
try:
    parser = OptionParser(usage="usage: %prog [option] [--hash <hash>]\n\n" + "EXAMPLE:\n" + " %prog --hash 7815696ecbf1c96e6894b779456d330e\n" + "%prog --thread 10 --exit-first --hash 7815696ecbf1c96e6894b779456d330e\n" + "%prog --input hashlist.txt\n" + "%prog --list")

    parser.add_option("-H", "--hash", action="store", dest="hash", default=None, help="The hash to crack, mandatory.")
    parser.add_option("-t", "--thread", action="store", dest="thread", default=10, help="Specify how many threads to use, default 10")
    parser.add_option("-e", "--exit-first", action="store", dest="exit_on_first", default=False, help="Stop execution upon first positive match")
    parser.add_option("-i", "--input", action="store", dest="input", default=None, help="Read a list of hashes from the given file")
    (o, args) = parser.parse_args()
    conf = open("md5.conf", "rt")
    services = []
    hashes = []

    if o.input != None:
        o.exit_on_first = False
        hashlist = open(o.input, "rt")
        for line in hashlist:
            md5 = line.rstrip()
            if md5 != '':
                hashes.append(md5)
    elif o.hash != None:
        hashes.append(o.hash)
    else:
        parser.error("No hash specified!")
    for line in conf:
        (type , url, regex) = line.rstrip().split('|')
        for md5_hash in hashes:
            services.append(Service(type, url, regex, o.exit_on_first, md5_hash))
    conf.close()

    i = 0
    for si,service in enumerate(services):
        print("Searching for '%s' on %s..."%(service.hash, service.name))
        service.start()
        i += 1
        if i > o.thread or si >= len(services):
            service.join()
            i = 0
except IOError as e:
    print e
except:
    raise
