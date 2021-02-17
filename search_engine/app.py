import os, sys, json
import flask
from flask import request, jsonify
from werkzeug.exceptions import HTTPException
from search import Serving

app = flask.Flask(__name__)
app.config["DEBUG"] = True
ConfigPath = "./config/search.conf"
SERVING = Serving(ConfigPath)
options = {"type": False,
           "domain": False,
           "quality": False,
           "ycc": False,
           "website_source": False,
           "file_source": False,
           }


@app.route('/', methods=['GET'])
def home():
    return "<h1>Welcome to Alexa Search Engine</h1>"


# @app.errorhandler(HTTPException)
# def handle_exception(e):
#     """Return JSON instead of HTML for HTTP errors."""
#     # start with the correct headers and status code from the error
#     response = e.get_response()
#     # replace the body with JSON
#     response.data = json.dumps({
#         "code": e.code,
#         "name": e.name,
#         "description": e.description,
#     })
#     response.content_type = "application/json"
#     return response


@app.route('/search', methods=['GET'])
def search():

    assert "src_text" in request.args, "No source text provided."
    source_text = request.args['src_text']
    n_best = int(request.args['n_best'])

    print("Search {} best matches for text: {}".format(n_best, source_text, flush=True))

    results = SERVING.search(source_text, n_best)

    return jsonify(results)


@app.route('/advanced_search', methods=['GET'])
def advanced_search():

    assert "src_text" in request.args, "No source text provided."
    assert "src_lang" in request.args, "No source language provided."

    source_text = request.args['src_text']
    n_best = int(request.args['n_best'])
    # src_lang = request.args['src_lang']
    # tgt_lang = request.args['tgt_lang']

    options = ['src_text', 'n_best', 'src_lang', 'tgt_lang']
    # quality, type, website_id, file_id, note, uri,owner,size,last_update,ycc_id,note,ycc,ycc_gloss,domain,note
    if bool(request.args.get('type', False)):
        options.append('type')
    if bool(request.args.get('domain', False)):
        options.append('domain')
    if bool(request.args.get('quality', False)):
        options.append('domain')
    if bool(request.args.get('ycc', False)):
        options.append('ycc')
    # options['website_id'] = bool(request.args.get('website_id', False))
    # options['file_id'] = bool(request.args.get('file_id', False))

    results = SERVING.search(source_text, n_best, advanced=True)
    adv_results = []
    for result in results:
        new_result = {}
        for op in options:
            if op in result:
                new_result[op] = result[op]
        adv_results.append(new_result)

    return jsonify(results)


if __name__ == '__main__':
    host = os.getenv("IP", "0.0.0.0")
    port = int(os.getenv("PORT", 5555))
    app.run(host=host, port=port)

