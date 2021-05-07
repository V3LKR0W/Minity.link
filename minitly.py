import flask, pymongo, asyncio, random, string, requests, tldextract, base64, io, pyqrcode
from pymongo import MongoClient
from flask import Flask, redirect, render_template, request, jsonify, url_for, abort, flash
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr
from Keys import *
from ipbans import *

app = Flask(__name__, static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = settings['secret_key']  
client = MongoClient(f'mongodb+srv://{settings["mongo_usr"]}:{settings["mongo_pw"]}@cluster0.aqsya.mongodb.net/{settings["mongo_db"]}?retryWrites=true&w=majority')
limiter = Limiter(
    app,
    key_func=get_ipaddr,
    default_limits=["500 per hour"]
)

# Error handlers

@app.errorhandler(404)
def not_found(err):
    return render_template('404.html')

@app.errorhandler(403)
def forbidden(err):
    return 'forbidden'

@app.errorhandler(405)
def method_not_allowed(err):
    error = {
        'error':str(err),
    }
    return jsonify(error)

@app.errorhandler(429)
def ratelimit_handler(e):
    error = {
        'error':'You are being rate-limited.'
    }
    return jsonify(error)

@app.errorhandler(406)
def ban_handler(e):
    error = {
        'You have been banned':'Your IP has been blacklisted.',
    }
    return jsonify(error)
    
# Database
def add_url(url, minity_url, ip):
    db = client['minity']
    collection = db['links']
    payload = {
        'url':str(url),
        'minity_link':str(minity_url),
        'clicks':str(0),
        'ip':str(ip),
    }
    
    collection.insert_one(payload)




# Functions
def generate(url, minited_url, ip):
    if not url.startswith('https://') or url.startswith('http://') or url.startswith('www.'):
        new_url = f'https://{url}'
        add_url(new_url, minited_url, ip)
        return redirect('/')
    else:
        add_url(url, minited_url, ip)
        return redirect('/')

def generate_api(url, minited_url, ip):
    if not url.startswith('https://') or url.startswith('http://') or url.startswith('www.'):
        new_url = f'https://{url}'
        add_url(new_url, minited_url, ip)
    else:
        add_url(url, minited_url, ip)


def random_string():
    letters = string.ascii_lowercase
    generated_string = ''.join(random.choice(letters) for i in range(10))
    return generated_string
    


# Routes
@app.route('/', methods=['GET','POST'])
@limiter.limit('100/hour', override_defaults=True)
def index():
    global click_num
    db = client['minity']
    collection = db['links']
    if request.method == 'GET':
        collection_clicks = db['clicks']
        clicks = collection_clicks.find({'find':'total_clicks'})
        numOfLinks = collection.find({}).count()
        
        for i in clicks:
            click_num = i['total_clicks']
        
        return render_template('index.html', links_shortned=numOfLinks,clicks=click_num)
        
    if request.method == 'POST':
        url = request.form['URL']
        suffix = tldextract.extract(str(url)).suffix
        domain = tldextract.extract(str(url)).domain
        client_remote_address = request.headers['X-Forwarded-For']
        ip = client_remote_address.split(',')[0]

        for bans in ip_list:
            print(ip)
            if ip == bans:
                abort(406)           
                
        if url == '' or None:
            flash('URL cannot be empty.', 'category2')
            return redirect(url_for('index'))
        elif suffix == '':
            flash('URL must have a TLD. Example: .com / .org / .net', 'category2')
            return redirect(url_for('index'))
        elif domain == 'minity':
            flash('Sorry you cannot shorten this link for security reasons.', 'category2')
            return redirect(url_for('index'))
        else:
            minited_url = random_string()
            search_minity_link = collection.find({'link': str(minited_url)})
            if search_minity_link.count() < 1:
                minited_url = random_string()
                generate(url, minited_url, ip)
                c = pyqrcode.create(f'https://minity.link/r/{minited_url}')
                s = io.BytesIO()
                c.png(s,scale=5)
                encoded = base64.b64encode(s.getvalue()).decode("ascii")    
                flash(minited_url, 'category1')
                flash(encoded, 'category3')
                return redirect(url_for('index'))
                
            if not url.startswith('https://') or url.startswith('http://') or url.startswith('www.'):
                new_url = f'https://{url}'
                add_url(new_url, minited_url, ip)
                flash(minited_url, 'category1')
                return redirect(url_for('index'))
            elif suffix == '' or None:
                flash('URL must have a TLD. Example: .com / .org / .net', 'category2')
                return redirect(url_for('index'))
            elif domain == 'minity':
                flash('Sorry you cannot shorten this link for security reasons.', 'category2')
                return redirect(url_for('index'))
            else:
                add_url(url, minited_url, ip)
                c = pyqrcode.create(f'https://minity.link/r/{minited_url}')
                s = io.BytesIO()
                c.png(s,scale=5)
                encoded = base64.b64encode(s.getvalue()).decode("ascii")   
                flash(minited_url, 'category1') 
                flash(minited_url, 'category1')
                flash(encoded, 'category3')
                return redirect(url_for('index'))


@app.route('/r/<string:url>', methods=['GET'])
def link(url):
    global redirect_url
    db = client['minity']
    collection = db['links']
    collection_clicks = db['clicks']
    search_minity_link = collection.find({'minity_link': str(url)})
    clicks = collection_clicks.find({})
    if search_minity_link.count() < 1:
        abort(404)
    else:
        for c in clicks:
            click_num = int(c['total_clicks'])+1
            collection_clicks.update_one({}, {'$set':{'total_clicks':str(click_num)}})
            
        for results in search_minity_link:
            redirect_url = results['url']
            
    return render_template('return.html', url=redirect_url)


# Static Pages
@app.route('/privacy')
@limiter.exempt
def privacy():
    return render_template('privacy.html')

@app.route('/api/docs')
@limiter.exempt
def api_docs():
    return render_template('apidocs.html')


# API

@app.route('/api/statistics', methods=['GET'])
@limiter.exempt
def statistics():
    if request.method == 'POST':
        payload = {
            'Incorrect calling method':'POST not allowed. Use GET',
        }
        return jsonify(payload)
    
    if request.method == 'GET':
        db = client['minity']
        total_links = db['links']
        total_clicks = db['clicks']
        clicks = total_clicks.find({'find':'total_clicks'})
        links = total_links.count()
        for c in clicks:
            global x
            x = c['total_clicks']
                    
        payload = {
            'total_clicks':str(x),
            'total_links':str(links),
        }
        return jsonify(payload)

@app.route('/api/create', methods=['GET','POST'])
@limiter.limit('50/hour', override_defaults=True)
def api_create():
    if request.method == 'GET':
        payload = {
            'Incorrect calling method':'GET not allowed. Use POST.'
        }
        return jsonify(payload)
    if request.method == 'POST':
        url = request.form['url']
        suffix = tldextract.extract(str(url)).suffix
        domain = tldextract.extract(str(url)).domain
        client_remote_address = request.headers['X-Forwarded-For']
        ip = client_remote_address.split(',')[0]
        
        for bans in ip_list:
            print(ip)
            if ip == bans:
                abort(406)   
         
        db = client['minity']
        collection = db['links']
        minited_url = random_string()
        search_minity_link = collection.find({'link': str(minited_url)})
        if search_minity_link.count() < 1:
            minited_url = random_string()
            if not url.startswith('https://') or url.startswith('http://'):
                payload = {
                    'error':'URL missing protcol please add https:// , http://'
                }
                return jsonify(payload)
            elif suffix == '' or None:
                payload = {
                    'error':'URL must have a TLD, ex: .com / .org / .net etc..'
                }
                return jsonify(payload)
            elif domain == 'minity':
                payload = {
                    'error':f'You are blocked from shortening a black listed domain: {url}'
                }
                return jsonify(payload)
            
            payload = {
                'minity_link':f'https://minity.link/r/{str(minited_url)}',
            }
            generate_api(url, minited_url, ip)
            return jsonify(payload)
        else:
            if not url.startswith('https://') or url.startswith('http://'):
                payload = {
                    'error':'URL missing protcol please add https:// , http://'
                }
                return jsonify(payload)
            elif suffix == '' or None:
                payload = {
                    'error':'URL must have a TLD, ex: .com / .org / .net etc..'
                }
                return jsonify(payload)
            elif domain == 'minity':
                payload = {
                    'error':f'You are blocked from shortening a black listed domain: {url}'
                }
                return jsonify(payload)
            
            payload = {
                'minity_link':f'https://minity.link/r/{str(minited_url)}',
            }
            generate_api(url, minited_url, ip)
            return jsonify(payload)


if __name__ == "__main__":
    app.run()
