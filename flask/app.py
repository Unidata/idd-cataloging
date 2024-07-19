import gzip
import json
import re
from datetime import datetime as dt
from datetime import timedelta
from flask import Flask, make_response, render_template, request
from models import session, Products
from sqlalchemy import func, not_

app = Flask(__name__)


# This function will gzip a response to be sent to the client:
def gzip_response(return_stuff):
    return_zipped = gzip.compress(return_stuff.encode("utf8"), 5)
    response = make_response(return_zipped, 200)
    response.headers["Content-Type"] = "application/json"
    response.headers['Content-length'] = len(return_zipped)
    response.headers['Content-Encoding'] = 'gzip'
    return response


# Restrict to local IPs:
def ip_check(ip):
    # Whitelist IPs that should have access to the cool stuff:
    if ip.split(".")[0] == "192" and ip.split(".")[1] == "168":
        return True
    else:
        return False


# Make it a decorator:
def whitelist_ip_check(f):
    from functools import wraps
    from flask import request, abort

    @wraps(f)
    def wrapped(*args, **kwargs):

        ip = request.remote_addr
        if ip_check(ip):
            return f(*args, **kwargs)
        else:
            # If they aren't from around here, make like we don't exist:
            return abort(404)

    return wrapped


# This function converts YYYYMMDDHHMM to a dt object:
def datestr_to_dt(datestr):
    return dt.strptime(datestr, "%Y%m%d%H%M")


@app.route('/')
def index():
    return 'Hello World'


@app.route("/iddcat")
@whitelist_ip_check
def iddcat():
    return render_template("iddcat.html")


@app.route("/iddsearch")
@whitelist_ip_check
def iddsearch():
    return render_template("search.html")


@app.route("/iddresearch")
@whitelist_ip_check
def iddresearch():
    return render_template("research.html")


@app.route('/json/null')
def null():
    return []


@app.route('/json/basic')
@whitelist_ip_check
def json_basic():
    prods = session.query(Products).order_by(Products.insertion_dt.desc()).limit(25)
    prod_list = []
    for prod in prods:
        this_prod = dict(
            insertion_time=prod.insertion_dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
            product=prod.product,
            feedtype=prod.feedtype,
            datasize=prod.datasize,
        )
        prod_list.append(this_prod)

    response = gzip_response(json.dumps(prod_list, separators=(',', ':')))
    return response


@app.route('/json/search')
@whitelist_ip_check
def json_search():
    q_feedtype = request.args.get("feedtype")
    q_startdt = request.args.get("start", default=dt.now() - timedelta(hours=4), type=datestr_to_dt)
    q_enddt = request.args.get("end", default=dt.now(), type=datestr_to_dt)
    q_keyphrase = request.args.get("phrase")
    q_notphrase = request.args.get("notphrase")

    prods = session.query(Products).filter(Products.insertion_dt >= q_startdt).filter(Products.insertion_dt <= q_enddt)

    if q_feedtype:
        prods = prods.filter(Products.feedtype.ilike(q_feedtype))
    if q_keyphrase:
        prods = prods.filter(Products.product.contains(q_keyphrase))
    if q_notphrase:
        prods = prods.filter(not_(Products.product.contains(q_notphrase)))

    prods = prods.all()

    prod_list = []
    for prod in prods:
        this_prod = dict(
            insertion_time=prod.insertion_dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
            product=prod.product,
            feedtype=prod.feedtype,
            datasize=prod.datasize,
        )
        prod_list.append(this_prod)

    response = gzip_response(json.dumps(prod_list, separators=(',', ':')))
    return response


@app.route('/json/research')
@whitelist_ip_check
def json_research():
    q_feedtype = request.args.get("feedtype")
    q_startdt = request.args.get("start", default=dt.now() - timedelta(hours=4), type=datestr_to_dt)
    q_enddt = request.args.get("end", default=dt.now(), type=datestr_to_dt)
    q_keyphrase = request.args.get("phrase")

    prods = session.query(Products).filter(Products.insertion_dt >= q_startdt).filter(Products.insertion_dt <= q_enddt)

    if q_feedtype:
        prods = prods.filter(Products.feedtype.ilike(q_feedtype))

    prods = prods.filter(Products.product.op("~")(q_keyphrase)).all()

    prod_list = []
    for prod in prods:
        this_prod = dict(
            insertion_time=prod.insertion_dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
            product=prod.product,
            feedtype=prod.feedtype,
            datasize=prod.datasize,
        )
        prod_list.append(this_prod)

    response = gzip_response(json.dumps(prod_list, separators=(',', ':')))
    return response


@app.route('/json/feedtypes')
@whitelist_ip_check
def json_feedtypes():
    results = session.query(Products.feedtype).distinct()
    feedtype_list = [r.feedtype for r in results]
    feedtype_list.sort()

    response = gzip_response(json.dumps(feedtype_list, separators=(',', ':')))
    return response


@app.route('/json/models')
@whitelist_ip_check
def json_models():
    feeds = ["NGRID", "HDS", "CONDUIT"]
    feeds = ["NGRID"]
    feeds = ["CONDUIT"]
    yesterday = dt.now() - timedelta(hours=24)
    prods = session.query(Products).filter(Products.insertion_dt >= yesterday).filter(Products.feedtype.in_(feeds)).filter(Products.product.op('~')(r'\d{12}F\d{2,3}')).all()

    model_set = set()
    for prod in prods:
        model_set.add(prod.product.split("!grib2")[1].split("/")[2])
    model_list = sorted(model_set)

    # response = make_response(model_list, 200)
    # response.headers["Content-Type"] = "application/json"
    return "<br>\n".join(model_list)
    # response = gzip_response(json.dumps(model_list, separators=(',', ':')))
    # return response


@app.route('/json/groupdate')
@whitelist_ip_check
def json_groupdate():
    q_feedtype = request.args.get("feedtype")
    q_startdt = request.args.get("start", default=dt.now() - timedelta(hours=6), type=datestr_to_dt)
    q_enddt = request.args.get("end", default=dt.now(), type=datestr_to_dt)
    q_keyphrase = request.args.get("phrase")

    results = session.query(Products).filter(Products.feedtype.ilike(q_feedtype)).filter(Products.insertion_dt >= q_startdt).filter(Products.insertion_dt <= q_enddt).filter(Products.product.op('~')(q_keyphrase)).all()

    # with open("/opt/flask-app/junkdrawer/groupdate.log", "w") as file:
    #     file.write(str(len(results)))

    result_set = {re.sub(q_keyphrase, "DATESTR", r.product) for r in results}
    result_list = sorted(result_set)
    # result_list = ["".join(s.split("DATESTR")[0]) + "DATESTR" for s in result_list]
    result_list.insert(0, "DATESTR Format: " + q_keyphrase.replace('\\', '') + "<br>\n")

    # response = make_response(result_list, 200)
    # response.headers["Content-Type"] = "application/json"
    return "<br>\n".join(result_list)
    # response = gzip_response(json.dumps(result_list, separators=(',', ':')))
    # return response


@app.route('/json/origins')
@whitelist_ip_check
def json_origins():
    # results = session.query(Products.origin).distinct()
    # origin_list = [r.origin for r in results]
    # origin_list.sort()

    distinct_origins = session.query(Products.origin, func.count(Products.origin)).group_by(Products.origin).all()
    distinct_origins = {k: v for k, v in sorted(distinct_origins, key=lambda item: item[1], reverse=True)}

    # print the results
    origin_list = [f"{origin}: {count}" for origin, count in distinct_origins.items()]
    # origin_list.sort()

    # response = make_response(origin_list, 200)
    # response.headers["Content-Type"] = "application/json"
    # # response = gzip_response(json.dumps(prod_list, separators=(',', ':')))
    # return response
    return "<br>\n".join(origin_list)
