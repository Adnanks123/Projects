import json
import random
from difflib import get_close_matches
from flask import Flask, request, jsonify, send_from_directory
from nltk.corpus import wordnet
import spacy

# Load the English language model
nlp = spacy.load('en_core_web_sm')

# Example function to demonstrate NLP techniques
def process_text(text):
    doc = nlp(text)

    # Named Entity Recognition (NER)
    entities = [(entity.text, entity.label_) for entity in doc.ents]

    # Part-of-Speech Tagging (POS)
    pos_tags = [(token.text, token.pos_) for token in doc]

    # Dependency Parsing
    dependencies = [(token.text, token.dep_, token.head.text) for token in doc]

    return entities, pos_tags, dependencies

# Example usage
text = "Apple is looking at buying U.K. startup for $1 billion"
entities, pos_tags, dependencies = process_text(text)
print("Entities:", entities)
print("POS Tags:", pos_tags)
print("Dependencies:", dependencies)


app = Flask(__name__, static_folder='static', static_url_path='')


# Load the knowledge base from a file
def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data


# Save the knowledge base to a file
def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


# Find the best match for a user's question
def find_best_match(user_question: str, questions: list[str]) -> str | None:
    matches = get_close_matches(user_question, questions, n=3, cutoff=0.6)
    if not matches:
        return None

    # Rank matches by similarity using NLP
    user_doc = nlp(user_question)
    ranked_matches = sorted(matches, key=lambda q: user_doc.similarity(nlp(q)), reverse=True)
    return ranked_matches[0]


# Get an answer for a given question
def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["questions"] == question:
            answers = q.get("answers")
            return random.choice(answers) if answers else None


# Add fun responses
def add_fun_responses() -> dict:
    fun_responses = {
        "fun_facts": [
            "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3000 years old and still perfectly edible. 🍯",
            "Fun fact: A day on Venus is longer than a year on Venus! 🌌",
            "Did you know? Octopuses have three hearts. 🐙"
        ],
        "jokes": [
            "Why don't scientists trust atoms? Because they make up everything! 😂",
            "I'm reading a book on anti-gravity. It's impossible to put down! 📚"
        ],
        "quotes": [
            "Believe you can and you're halfway there. -Theodore Roosevelt 💪",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. -Winston Churchill 🌟"
        ]
    }
    return fun_responses


# Get a random fun response
def get_fun_response(response_type: str) -> str:
    fun_responses = add_fun_responses()
    return random.choice(fun_responses[response_type])


# Load knowledge base
knowledge_base = load_knowledge_base('knowledge_base.json')


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    user_input = user_input.strip().lower()

    if user_input in ['hi', 'hello', 'hey']:
        greetings = ["Hello! How can I assist you today? 😊", "Hi there! What can I do for you? 👋",
                     "Hey! Need any help? 🤗"]
        return jsonify({"response": random.choice(greetings)})

    if user_input in ['bye', 'goodbye', 'see you']:
        farewells = ["Goodbye! Have a great day! 👋", "See you soon! Take care! 😊",
                     "Bye! Don't hesitate to come back if you need anything else! 🙌"]
        return jsonify({"response": random.choice(farewells)})

    if user_input == 'fun fact':
        return jsonify({"response": get_fun_response('fun_facts')})

    if user_input == 'tell me a joke':
        return jsonify({"response": get_fun_response('jokes')})

    if user_input == 'inspire me':
        return jsonify({"response": get_fun_response('quotes')})

    best_match = find_best_match(user_input, [q["questions"] for q in knowledge_base["questions"]])

    if best_match:
        answer = get_answer_for_question(best_match, knowledge_base)
        return jsonify({"response": answer + ' 😊'})

    else:
        return jsonify({"response": "I don't know the answer to that. Can you teach me? 🧐"})


@app.route('/learn', methods=['POST'])
def learn():
    user_input = request.json.get('question')
    new_answer = request.json.get('answer')

    for q in knowledge_base["questions"]:
        if q["questions"] == user_input:
            q["answers"].append(new_answer)
            save_knowledge_base('knowledge_base.json', knowledge_base)
            return jsonify({"response": "Thank you! I learned new responses! 🙌"})

    knowledge_base["questions"].append({"questions": user_input, "answers": [new_answer]})
    save_knowledge_base('knowledge_base.json', knowledge_base)
    return jsonify({"response": "Thank you! I learned new responses! 🙌"})


if __name__ == '__main__':
    app.run(debug=True)
