import json
import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*"])

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.json')


def load_db():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_db(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/api/ping')
def ping():
    return jsonify({"status": "ok"})


@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(load_db())


@app.route('/api/products', methods=['POST'])
def add_product():
    item = request.get_json()
    if not item:
        return jsonify({"error": "empty body"}), 400
    db = load_db()
    # assign new id
    existing_ids = {p.get('id') for p in db}
    new_id = max((p.get('id', 0) for p in db), default=0) + 1
    while new_id in existing_ids:
        new_id += 1
    item['id'] = new_id
    db.append(item)
    save_db(db)
    return jsonify(item), 201


@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    db = load_db()
    new_db = [p for p in db if p.get('id') != pid]
    if len(new_db) == len(db):
        return jsonify({"error": "not found"}), 404
    save_db(new_db)
    return jsonify({"deleted": pid})


@app.route('/api/products/import', methods=['POST'])
def import_products():
    body = request.get_json()
    if not body:
        return jsonify({"error": "empty body"}), 400
    mode = body.get('mode', 'append')
    items = body.get('items', [])
    if not isinstance(items, list):
        return jsonify({"error": "items must be array"}), 400

    if mode == 'replace':
        db = []
    else:
        db = load_db()

    existing_ids = {p.get('id') for p in db}
    max_id = max((p.get('id', 0) for p in db), default=0)

    for item in items:
        max_id += 1
        while max_id in existing_ids:
            max_id += 1
        item['id'] = max_id
        existing_ids.add(max_id)
        db.append(item)

    save_db(db)
    return jsonify({"imported": len(items), "total": len(db)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5678, debug=True)
