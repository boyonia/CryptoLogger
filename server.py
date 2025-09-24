from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

BASE_LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')

@app.route('/api/files', methods=['GET'])
def list_all_csvs():
    """
    List all CSV files under logs/, grouped by folder.
    """
    try:
        structure = {}
        for folder in os.listdir(BASE_LOGS_DIR):
            full_folder_path = os.path.join(BASE_LOGS_DIR, folder)
            if os.path.isdir(full_folder_path):
                csvs = [f for f in os.listdir(full_folder_path) if f.endswith('.csv')]
                structure[folder] = csvs
        return jsonify(structure)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<folder>/<filename>', methods=['GET'])
def get_csv_file(folder, filename):
    """
    Return contents of a specific CSV file from a folder.
    """
    try:
        if not filename.endswith('.csv'):
            return jsonify({'error': 'Only .csv files are allowed'}), 400

        file_path = os.path.join(BASE_LOGS_DIR, folder, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': f"{folder}/{filename} not found"}), 404

        df = pd.read_csv(file_path)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/live', methods=['GET'])
def get_live_data():
    """
    Return contents of live_data/live_data.csv.
    """
    try:
        file_path = os.path.join(BASE_LOGS_DIR, 'live_data', 'live_data.csv')
        if not os.path.exists(file_path):
            return jsonify({'error': 'live_data.csv not found'}), 404

        df = pd.read_csv(file_path)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/live_sentiment', methods=['GET'])
def get_live_sentiment():
    """
    Return contents of live_data/live_sentiment.csv.
    """
    try:
        file_path = os.path.join(BASE_LOGS_DIR, 'live_data', 'live_sentiment.csv')
        if not os.path.exists(file_path):
            return jsonify({'error': 'live_sentiment.csv not found'}), 404

        df = pd.read_csv(file_path)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
