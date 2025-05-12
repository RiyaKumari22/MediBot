from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["medibot_db"]
diseases_collection = db["diseases"]
symptoms_collection = db["symptoms"]

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json.get("message", "").strip().lower()

    if "check disease" in user_input:
        return jsonify({"response": "Sure! Please enter the disease name.", "action": "search_disease"})

    elif "check symptoms" in user_input:
        return jsonify({"response": "Got it! Please enter your symptoms separated by commas.", "action": "check_symptoms"})

    else:
        return jsonify({"response": "I can help you check for diseases or symptoms. Please choose one."})

@app.route('/result', methods=['POST'])
def result():
    query = request.form.get('query', "").strip().capitalize()

    if not query:
        return redirect(url_for('disease'))  # Redirect if input is empty

    result = diseases_collection.find_one({"name": query}, {"_id": 0})

    if result:
        # Generate Wikipedia link
        wiki_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
        return render_template('result.html', disease=query, info=result, wiki_url=wiki_url)
    else:
        return render_template('disease.html', error=f"No data found for '{query}'. Please try another disease.")
@app.route('/symptoms', methods=['GET', 'POST'])
def symptoms():
    if request.method == 'POST':
        # Get the input as a string and split it into a list
        symptoms_input_raw = request.form.get('symptoms', '')
        symptoms_input = [sym.strip().lower() for sym in symptoms_input_raw.split(',') if sym.strip()]

        if not symptoms_input:
            return render_template('symptoms.html', error="Please enter at least one symptom.")

        # Find diseases that match ALL symptoms
        possible_diseases = symptoms_collection.find(
            {"symptoms": {"$all": symptoms_input}},
            {"_id": 0}
        )

        diseases_list = []
        for disease in possible_diseases:
            diseases_list.append({
                "name": disease["disease"],
                "medicines": disease.get("medicines", []),
                "specialist": disease.get("specialist", "General Physician")
            })

        if diseases_list:
            return render_template('symptoms_result.html', symptoms=symptoms_input, diseases=diseases_list)
        else:
            return render_template('symptoms.html', error="No matching diseases found for the given symptoms.")

    return render_template('symptoms.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search_term = request.args.get('query', '').capitalize()
    
    # Fetch matching disease names
    suggestions = diseases_collection.find(
        {"name": {"$regex": f"^{search_term}"}},
        {"name": 1, "_id": 0}
    )

    # Return only disease names in a list
    return jsonify([disease["name"] for disease in suggestions])

@app.route('/disease')
def disease():
    return render_template('disease.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/health')
def health():
    return render_template('health.html')
if __name__ == '__main__':
    app.run(debug=True)
