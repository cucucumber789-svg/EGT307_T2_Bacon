from flask import Blueprint, jsonify
from app.services.data_ingestion import parse_csv, save_local, forward_to_backend

ingestion_bp = Blueprint("ingestion", __name__)


@ingestion_bp.route("/ingest/file", methods=["POST"])
def ingest_raw_file():
    df = parse_csv()
    save_local(df)
    result = forward_to_backend(df)
    return jsonify({"rows": len(df), **result}), 201
