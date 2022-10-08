from django.shortcuts import render
from django.http import HttpResponse
import requests
import traceback
import time
import rsa
from rsa import PublicKey, PrivateKey
import random
import hashlib
import json
from django.utils import timezone
from .models import *

# this stuff can be changed and new networks disconnected from the main network can be established
network_owner = "generationxcode."
network_host = "https://eggnft.generationxcode.repl.co/"

# more user friendly moment
initialized = False

# the original public key to compare yours to and change if needed
MAIN_PUBLIC_KEY = [
    93604489133966140839188488611575406888187157546413625479305396588460631319813235737326833153126266236314757531434477028863669619203471498228321771907170764053750210158264434226821771256415954959222865826396949984177302278878225511871990947930735753306754761742109953984586498872779225629204382546678403734419,
    65537
]

#json helpers


def from_json(json_code):
    """
  args -> json_code
  this converts json code to python
  """
    try:
        return json.loads(json_code)
    except:
        return json_code


def to_json(code):
    """
  args -> the data you want to convert to json
  converts stuff to json so we can hash it
  """
    try:
        return json.dumps(code)
    except:
        return code


# personal data helpers


def read_personal_data():
    """
  args -> None
  This reads personal data from the personal data file. returns a list 
  with username and url
  """
    personal_data = {}
    with open("personal_data.json", "r+") as outfile:
        personal_data = json.load(outfile)
    return personal_data


def write_personal_data(url_got):
    """
  args -> "url_got"
  This writes personal data to the personal data file
  """
    index = url_got.index(".") + 1
    username = url_got[index:-8]
    with open("personal_data.json", "w") as outfile:
        json.dump([url_got, username], outfile)
    return True


# database helpers


def read_block_latest_db():
    """
  args -> None
  returns the data in a block that has been last published in the form a dictionary. This will be used in checking whether the blockchain is correct and to calculate the previous hash and to build up the plots db
  """
    block = Blockchain.objects.latest('pub_date')
    return {
        'transactions': json.loads(block.transactions),
        'index': block.index,
        'timestamp': float(block.timestamp),
        'hash': block.hash,
        'nonce': block.nonce,
        'owner': block.owner
    }


def read_block_db(index):
    """
  args -> index
  returns the data in a block in the form a dictionary. This will be used in checking whether the blockchain is correct and to calculate the previous hash and to build up the plots db
  """
    block = Block_chain.objects.get(index=str(index))
    return {
        'transactions': json.loads(block.transactions),
        'index': block.index,
        'timestamp': float(block.timestamp),
        'hash': block.hash,
        'nonce': block.nonce,
        'owner': block.owner
    }


def remove_block_db():
    """
  args -> None
  this deletes all blocks from the database
  """
    Blockchain.objects.all().delete()
    return True


def write_block_db(block):
    """
  args -> {block}
  writes a block in the blockchain
  """
    try:
        if Blockchain.objects.get(index=block['index']):
            p = Blockchain.objects.get(index=str(block['index']))
            p.owner = block['owner']
            p.timestamp = str(block['timestamp'])
            p.hash = block['hash']
            p.nonce = str(block['nonce'])
            p.transactions = json.dumps(block['transactions'])
            p.pub_date = timezone.now()
            p.save()
            print("more than index :)")
        else:
            Blockchain(index=str(block['index']),
                       timestamp=str(block['timestamp']),
                       hash=block['hash'],
                       nonce=str(block['nonce']),
                       transactions=json.dumps(block['transactions']),
                       pub_date=timezone.now()).save()
            print("done")
        return True
    except:
        Blockchain(index=str(block['index']),
                   timestamp=str(block['timestamp']),
                   hash=block['hash'],
                   nonce=str(block['nonce']),
                   transactions=json.dumps(block['transactions']),
                   pub_date=timezone.now()).save()
        print("done")
        return True


def write_plot_db(plot):
    """
  args -> {plot}
  this adds a new plot to the plots database, which is the only other database to the main blockchain database
  a plot will contain {coordinates, landscape, owner, owner public key, hash of last transaction}
  coordinates show the plot on a 3d graph that we will build up as a square spiral
  landscape is the distribution of blocks on a plot
  owner is the username of the owner
  owner public key is to identify the block along with the coordinates
  """
    try:
        if plots.objects.get(coords=to_json(plot['coords'])):
            p = plots.objects.get(coords=to_json(plot['coords']))
            p.owner = plot['owner']
            p.owner_public_key = to_json(plot['owner_public_key'])
            p.hash = plot['hash']
            p.landscape = json.dumps(plot['landscape'])
            p.save()
            print("more than index :)")
        else:
            plots(coords=to_json(plot['coords']),
                  owner_public_key=plot['owner_public_key'],
                  owner=plot['owner'],
                  hash=plot['hash'],
                  landscape=json.dumps(plot['landscape'])).save()
            print("done")
        return True
    except:
        plots(coords=to_json(plot['coords']),
              owner_public_key=plot['owner_public_key'],
              owner=plot['owner'],
              hash=plot['hash'],
              landscape=json.dumps(plot['landscape'])).save()
        print("done")
        return True


def remove_all_plots_db():
    """
  args -> None
  this deletes the entirety of the plots database so we can rebuild it. 
  This is done when resyncing to find some blocks are wrong
  """
    plots.objects.all().delete()
    return True


def read_plot_db(plot_coords):
    """
  args -> plot_coords
  this reads a plot from the plots database
  """
    plot = plots.objects.get(coords=to_json(plot_coords))
    return {
        'landscape': json.loads(plot.landscape),
        'coords': from_json(plot.coords),
        'owner': plot.owner,
        'hash': plot.hash,
        'owner_public_key': plot.owner_public_key
    }


# random helpers


def hash_txt(text):
    """
  args -> "text"
  converts text to a hash
  """
    m = hashlib.sha256()
    m.update(text.encode("ascii"))
    return m.hexdigest()


def generate_zero_string(num):
    """
  args -> num (integer)
  this generates a zero string to check against from a number that is the 
  number of trailing 0s
  """
    string = ""
    for i in range(num):
        string += "0"
    return string


# cryptography and signature making helpers


def jsonify_keys(keys):
    """
  args -> [keys that are pythonified]
  converts pythonified keys to jsonified keys
  """
    try:
        return [[keys[0].n, keys[0].e],
                [keys[1].n, keys[1].e, keys[1].d, keys[1].p, keys[1].q]]
    except:
        return keys


def pythonify_keys(keys):
    """
  args -> [keys that are jsonified]
  converts jsonified keys to pythonified keys
  """
    try:
        return [
            PublicKey(keys[0][0], keys[0][1]),
            PrivateKey(keys[1][0], keys[1][1], keys[1][2], keys[1][3],
                       keys[1][4])
        ]
    except:
        return keys


def get_keys():
    """
  args -> None
  this gets the keys from the json file and returns them
  """
    keys = []
    with open("keys.json", "r+") as outfile:
        keys = json.load(outfile)
    return pythonify_keys(keys)


def create_keys():
    """
  args -> None
  this creates a new set of public and private keys for a new user and 
  stores them in a json file
  """
    (public_key, private_key) = rsa.newkeys(1024)
    keys = jsonify_keys([public_key, private_key])
    with open("keys.json", "w") as outfile:
        json.dump(to_json(keys), outfile)
    return True


def signature_making(text, key):
    """
  args -> text,key
  this makes a signature out of a private key and a hash text (or any 
  other text for that matter)
  """
    data = rsa.encrypt(text.encode("utf8"), key)
    output = 0
    size = len(data)
    for index in range(size):
        output |= data[index] << (8 * (size - 1 - index))
    return str(output)
    return "signature"


#networking helpers


def get_peers():
    """
  args -> None
  This is run when started and the node contacts the main node (my node) and 
  I send back a list of all peers to the node.
  for all repls except the one referred to as the original, the repl shall contain peers that HAVE TO HAVE the original in it
  """
    ping_all_peers()
    peers = read_peers()
    url = peers[0][0]
    store_peers(from_json(requests.post(url + "/peers").text))
    return True


def ping_all_peers():
    """
  args ->  None
  This pings all peers and checks if they are alive or dead and removes the dead ones and stores the alive ones
  """
    new_peers = []
    peers = read_peers()
    for i in peers:
        if requests.post(i[0] + "/ping", timeout=1.5).text == network_owner:
            new_peers.append(i)
    store_peers(new_peers)
    return True


def store_peers(peers):
    """
  args ->  [peers]
  this converts a list of peers to json and stores it in a json file
  """
    with open("peers.json", "w") as outfile:
        json.dump(peers, outfile)
    return True


def read_peers():
    """
  args -> None
  this reads the peers from the file and returns them as unjsonified
  """
    peers = []
    me = read_personal_data()
    with open("peers.json", "r+") as outfile:
        peers = json.load(outfile)
    if [network_host, network_owner] in peers:
        peers_proper = []
        for i in peers:
            if i != me:
                peers_proper.append(i)
        return peers_proper
    else:
        peers.append([network_host, network_owner])
        print(peers)
        peers_proper = []
        for i in peers:
            if i != me:
                peers_proper.append(i)
        return peers_proper


def broadcast_transaction_single(peer, transaction):
    """
  args -> "peer url", {transaction}
  This broadcasts a transaction to a singular peer
  """
    requests.post(peer + "/new_transacton", {'transaction': transaction})
    return True


def broadcast_transaction_all(transaction):
    """
  args -> {transaction}
  broadcasts a transaction to all peers 
  """
    peers = read_peers()
    for i in peers:
        broadcast_transaction_single(i, transaction)
    return True


def broadcast_block_single(peer, block):
    """
  args -> "peer url", {block}
  This broadcasts a block to a singular peer
  """
    requests.post(peer + "/new_block", {'block': block})
    return True


def broadcast_block_all(block):
    """
  args -> {block}
  broadcasts a block to all peers 
  """
    peers = read_peers()
    for i in peers:
        broadcast_block_single(i, block)
    return True


def write_network():
  """
  args->none
  This stores the network url and owner in the json file. returns True
  """
  with open("network.json",'w') as outfile:
    json.dump([network_owner,network_host],outfile)
  return True


def read_network():
  """
  args->none
  Returns True, assigns the network vars with data from file
  """
  with open("network.json",'r') as outfile:
    arr = json.load(outfile)
    network_host=arr[1]
    network_owner=arr[0]
  return True

    
# getting started with the plots class finally


class Plots():

  
    def __init__(self):
        """
    functions to be carried out when initializing the server
    """
        self.initialized = False
        self.current_transactions = []
        self.difficulty = 4

  
    def initialize(self, personal_url):
        """
    initializing the blockchain
    """
        read_network()
        write_personal_data(personal_url)
        keys = get_keys()
        personal_data = read_personal_data()
        """if not (self.blockchain_checking(personal_data[0])):
            remove_block_db()
        """
        if personal_data[0] != "https://eggnft.generationxcode.repl.co/":
            if jsonify_keys(keys)[0] == MAIN_PUBLIC_KEY:
                create_keys()
        peers = read_peers()
        length = 0
        try:
            length = read_block_latest_db()['index']
        except:
            length = 0
        print(length)
        got = False
        peers_known = read_peers()
        for i in peers:
            look_peers = from_json(requests.post(i[0] + "/peers").text)
            for v in look_peers:
                found = False
                for m in peers_known:
                    if m == v:
                        found = True
                if found != True:
                    peers_known.append(v)
        store_peers(peers_known)

        for i in peers:
            foreign_len = int(requests.post(i[0] + "/chain_length").text)
            if foreign_len > length:
                if self.check_blockchain(i[0]) == True:
                    remove_block_db()
                    running = True
                    v = 0
                    while running == True:
                        server_response = requests.post(
                            i[0] + "/block_num", {
                                "index": str(v)
                            }).text
                        if server_response == "Done":
                            running = False
                            break
                        write_block_db(from_json(server_response))

                    got = True
                    length = foreign_len
        if (got == False) and (length == 0):
            write_block_db({
                "index": 0,
                'timestamp': time.time(),
                'owner': network_owner,
                'hash': hash_txt("epic"),
                'nonce': 'none',
                'transactions': []
            })
            self.first_transaction_in_block()
        elif got == True:
            self.log_transactions_all()
            for i in peers:
                requests.post(i[0] + "/new_peer", {"peer": personal_data[0]})
        self.initialized = True
        return True

  
    def mine(self):
        """
    mining a block let people crash everything at this point idc.
    """
        counter = 0
        block = read_block_latest_db()
        hash = block['hash']
        zero_string = generate_zero_string(self.difficulty)
        mined = False
        print("MINING RN. Dont try and mine again or else problems shall occur... mostly the repl maxing out maybe")
        while mined == False:
            if hash_txt(hash + str(counter))[:self.difficulty] == zero_string:
                mined = True
            counter+=1
        self.new_block_mined(counter, block['index'])
        return True

  
    def new_block_mined(self, nonce, index):
        """
    steps after mining is completed successfully, such as looking at whether the block is outdated or not
    """
        if read_block_latest_db()['index'] == index:
            block = read_block_latest_db()
            block['transactions'] = self.current_transactions
            block['nonce'] = nonce
            write_block_db(block)
            self.current_transactions = []
            broadcast_block_all(block)
            self.log_transactions(block)
            write_block_db({
                "index": block['index'] + 1,
                'timestamp': time.time(),
                'owner': network_owner,
                'hash': hash_txt(to_json(block)),
                'nonce': 'none',
                'transactions': []
            })
            self.first_transaction_in_block()
        return True

  
    def new_block_recieved(self, block):
        """
    {block}
    processes to be done when someone else broadcasts a block
    """
        if self.check_block(block):
            for i in block['transactions']:
                removed = "e"
                for m, v in enumerate(self.current_transactions):
                    if i == v:
                        removed = i
                if removed != "e":
                    self.current_transactions.pop(removed)
            write_block_db(block)
            write_block_db({
                "index": block['index'] + 1,
                'timestamp': time.time(),
                'owner': network_owner,
                'hash': hash_txt(to_json(block)),
                'nonce': 'none',
                'transactions': []
            })
        return True


    def add_recieved_transaction(self, transaction):
        """
    {transaction}
    processes to be done when a new transaction is to be added through an external broadcast
    """
        if self.check_transaction(transaction):
            self.current_transactions.append(transaction)
        return True


    # a transact transaction shall contain the type (edit or *transact*), plot, previous hash, owner public key, receiver public key, signature of the previous hash by the owner

      
    # an edit transaction shall contain the type (*edit* or transact) public key of the owner, plot, signature of the hashed( edit hashed and the previous hash) concatenated, edit array in json

      
    def new_transaction(self, plot, type, data):
        """
    plot,"type",{data}
    This creates a new transaction that you want to create not someone else data is public key for transact type and for edit type its the landscape array
    """
        me = read_personal_data()[1]
        if type == "transact":
            plot_e = read_plot_db(plot)
            transaction = {
                "plot": plot,
                'type': type,
                'prev_public_key': jsonify_keys(get_keys()),
                'hash': plot_e['hash'],
                'owner_public_key': data,
                'signature': signature_making(plot_e['hash'],get_keys()[1]),
                "owner": me
            }
            self.current_transactions.append(transaction)
            broadcast_transaction_all(transaction)
        else:
            plot_e = read_plot_db(plot)
            transaction = {
                "plot":
                plot,
                'owner':
                me,
                'type':
                type,
                'owner_public_key':
                jsonify_keys(get_keys()),
                'hash':
                plot_e['hash'],
                'landscape':
                data,
                'signature':
                signature_making(
                    hash_txt(plot_e['hash'] + hash_txt(to_json(data))),get_keys()[1])
            }
            self.current_transactions.append(transaction)
            broadcast_transaction_all(transaction)
        return True

  
    def check_transaction(self, transaction):
        """
    {transaction}
    This checks if the transaction is legal or illegal
    """
        if transaction["owner_public_key"] == "egg":
            return True

        for i in self.current_transactions:
            if (i['plot'] == transaction['plot']):
                return False

        if transaction["type"] == 'transact':
            plot_db_entry = read_plot_db(transaction['plot'])
            if plot_db_entry['owner_public_key'] != transaction[
                    'prev_public_key']:
                return False

        if transaction["type"] == "edit":
            plot_db_entry = read_plot_db(transaction['plot'])
            if plot_db_entry['owner_public_key'] != transaction[
                    'owner_public_key']:
                return False

        return True

  
    def first_transaction_in_block(self):
        """
    processes that award the miner a plot of land
    """
        latest_index = int(read_block_latest_db()['index'])
        # right up left down. start from origin and keep increaing the number of steps in each direction by one
        steps = 0
        place = [0, 0]
        direction = "d"
        count = 0
        me = read_personal_data()[1]
        while count <= (latest_index + 1):
            if direction == "r":
                place[0] += steps
                count += steps
                steps += 1
                direction = "u"
            elif direction == "u":
                place[1] += steps
                count += steps
                steps += 1
                direction = "l"
            elif direction == "l":
                place[0] -= steps
                count += steps
                steps += 1
                direction = "d"
            elif direction == "d":
                place[1] -= steps
                count += steps
                steps += 1
                direction = "r"
        if count > (latest_index + 1):
            correction = count - latest_index + 1
            if direction == "r":
                place[1] += correction
            elif direction == "u":
                place[0] -= correction
            elif direction == "l":
                place[1] -= correction
            elif direction == "d":
                place[0] += correction
        key = jsonify_keys(get_keys())[0]
        transaction = {
            "plot": place,
            'type': "transact",
            'prev_public_key': "egg",
            'hash': hash_txt("epic"),
            'owner_public_key': key,
            'signature': signature_making(hash_txt("epic"),get_keys()[1]),
            "owner": me
        }
        self.current_transactions.append(transaction)
        broadcast_transaction_all(transaction)
        return True

  
    def check_block(self, block):
        """
    {block}
    checks a single block
    """
        if hash_txt(block['hash'] + str(block['nonce'])
                    )[:self.difficulty] != generate_zero_string(
                        self.difficulty):
            return False

        for i in block['transactions']:
            if not (self.check_transaction(i)):
                return False
        return True

  
    def check_blockchain(self, peer):
        """
    look at one peer request its blockchain and it it checks out, let us have it
    """
        length = int(requests.post(peer + "/chain_length").text)
        prev_hash
        for i in range(length):
            if i > 0:
                block = from_json(
                    requests.post(peer + "/block_num", {'index': str(i)}))
                if block['hash'] != prev_hash:
                    return False
                if hash_txt(block['hash'] + str(block["nonce"])
                            )[:self.difficulty] != generate_zero_string(
                                self.difficulty):
                    return False
                prev_hash = block['hash']
        return True

  
    def log_transactions(self, block):
        """
    {block}
    logs the transactions from a block
    """
        for i in block['transactions']:
            if i['type'] == 'transact':
                if i['prev_public_key'] == "egg":
                    write_plot_db({
                        "coords":
                        i['plot'],
                        "hash":
                        hash_txt(to_json(i)),
                        "owner":
                        i['owner'],
                        "owner_public_key":
                        i['owner_public_key'], 'landscape':[]
                    })
                else:
                    p = plots.objects.get(coords=to_json(i['plot']))
                    p.hash = hash_txt(to_json(i))
                    p.owner = i['owner']
                    p.owner_public_key = to_json(i['owner_public_key'])
                    p.save()
            elif i['type'] == 'edit':
                p = plots.objects.get(coords=to_json(i['plot']))
                p.landscape = to_json(i['landscape'])
                p.save()
        return True

  
    def log_transactions_all(self):
        """
    goes through the blockchain database and logs all the transactions from every block in the database
    """
        remove_all_plots_db()
        index_latest = int(read_block_latest_db()['index'])
        for i in range(index_latest):
            self.log_transactions(read_block_db(i))
        return True


# Create your views here.
# a block shall contain the timestamp, username of miner, prev hash, nonce, transactions in json and index
# a transact transaction shall contain the type (edit or *transact*), plot, previous hash, owner public key, receiver public key, signature of the previous hash by the owner
# an edit transaction shall contain the type (*edit* or transact) public key of the owner, plot, signature of the hashed( edit hashed and the previous hash) concatenated, edit array in json
# blockchains shall go over the blockchains of other peers by looking at the lengths of each of the peers' chains and if they are larger than their own, delete their database of the blockchain and sync the chain from the start, if the chain is incorrect at any point, it shall repeat the process with the next largest blockchain and sync that. If none of them are correct, it shall start from the beginning by itself.
"""

urlpatterns = [
    path('', views.index, name='index'),
    path('new_peer',views.new_peer,name="new_peer"),
    path('peer',views.peers,name="peers"),
    path('ping',views.ping,name="ping"),
    path('new_transaction',views.new_transaction,name="new_transaction"),
    path('make_edit',views.make_edit,name="make_edit"),
    path('make_edit_view',views.make_edit,name="make_edit_view"),
    path('new_block',views.new_block,name="new_block"),
    path('mine',views.mine,name="mine"),
    path('make_transaction',views.make_transaction,name="make_transaction"),


    
    path('transaction_form',views.transaction_form,name="transaction_form"),
    path('plots',views.balance,name="plots"),
    path('public_key',views.public_key,name="public_key"),
    path('chain_length',views.chain_length,name="chain_length"),
    path('block_num',views.get_block,name="block_num"),
    path('latest_block_info',views.get_block,name="latest_block_info"),
    path('initialize',views.initialize,name="initialize"),
    path('initialize_view',views.initialize_view,name="initialize_view"),
  
]


"""


the_plots = Plots()


# work on this


def index(request):
    # information should be if the blockchain is initialized or not the_plots.initialized (bool)
    # has to have the option to initialize blockchain
    # has the option to go to the page with all your plots
    # has the option to go to the page with everyone's plots
    # has the option to mine a new plot
    # has the option to make a transaction
    # has the option to change the network
    return render(
        request, "index.html", {
            "network_owner": network_owner,
            "network_url": network_host,
            "initialized": the_plots.initialized
        })


def new_peer(request):
    new_peer_name = request.POST['peer']
    peers_known = read_peers()
    peers_known.append(new_peer_name)
    store_peers(peers_known)
    # registers peer
    return HttpResponse("epic")


def peers(request):
    peers_known = read_peers()
    # sends json list of peers
    return HttpResponse(to_json(peers_known))


def ping(request):
    # returns if alive or not
    return HttpResponse(network_owner)


def new_transaction(request):
    #logs a new transaction
    transaction = from_json(request.POST['transaction'])
    the_plots.add_recieved_transaction(transaction)
    return HttpResponse("epic")


def make_edit(request):
    # logs the edit as a transaction and mines
    plot_received = from_json(request.POST['plot'])
    landscape = from_json(request.POST['landscape'])
    the_plots.new_transaction(plot_received, "edit", landscape)
    the_plots.mine()
    return HttpResponse("epic")


# work on this
def make_edit_view(request):
    # provides page for people to make their edits
    return HttpResponse("epic")


def new_block(request):
    # recieves a block mined by someone else
    block = from_json(request.POST['block'])
    the_plots.new_block_recieved(block)
    return HttpResponse("epic")


def mine(request):
    # mines a new block
    the_plots.mine()
    return HttpResponse("epic")


def make_transaction(request):
    # makes the transaction
    plot_transacted = from_json(request.body.decode('utf-8'))['plot']
    data1 = int(from_json(request.body.decode('utf-8'))['key1'])
    data2 = int(from_json(request.body.decode('utf-8'))['key2'])
    keys = [data1, data2]
    the_plots.new_transaction(plot_transacted, "transact", keys)
    return HttpResponse("epic")


# work on this
def transaction_form(request):
    # allows user to send plots data to people if they provide their pk
    return render(request,"transaction.html",{})


# work on this
def plots_view(request):
    # returns page with 3d view of all the plots
    return HttpResponse("epic")


def public_key(request):
    # allows user to see their public key
    key = jsonify_keys(get_keys())[0]
    return HttpResponse("part 1: " + str(key[0]) + " part 2: " + str(key[1]))


def chain_length(request):
    # returns the chain length
    return HttpResponse(str(read_block_latest_db()['index']))


def initialize(request):
    # gets the info about the repl name and initializes (done from index page)
    repl_name = from_json(request.body.decode('utf-8'))['url']
    the_plots.initialize(repl_name)
    return HttpResponse("epic")


def get_block(request):
    # gives back json code of a block requested
    return HttpResponse(to_json(read_block_db(index)))


def get_owned_plots(request):
    #returns the owned plots for use in the owned plots page
    owner = read_personal_data()[1]
    plots_mine = plots.objects.filter(owner=owner)
    list_mine = []
    for i in plots_mine.iterator():
        list_mine.append(i.coords)
    return HttpResponse(to_json(list_mine))


def change_network(request):
    #changes network and saves
    print(str(request.body.decode('utf-8')))
    network_owner = from_json(request.body.decode('utf-8'))['owner']
    network_host = from_json(request.body.decode('utf-8'))['host_url']
    ping_all_peers()
    remove_block_db()
    the_plots.initialized=False
    write_network()
    return HttpResponse("epic")


def get_plot_landscape(request):
    #returns the landscape for a single plot (used in edit and view)
    plot = request.POST['plot']
    if plots.objects.filter(coords=plot).exists():
        return HttpResponse(plots.objects.get(coords=plot).landscape)
    else:
        return HttpResponse("[]")


def assets(request):
  me = read_personal_data()[1]
  my_plots = plots.objects.filter(owner=me)
  return render(request,"assets.html",{'plots':my_plots})
