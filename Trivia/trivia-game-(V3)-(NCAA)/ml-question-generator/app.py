from flask import Flask, render_template, request
from scripts.qa_engine import answer_question

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():

    result = None

    if request.method == "POST":

        question = request.form["question"]

        classification = answer_question(question)

        result = {
            "domain": classification.get("domain"),
            "subcontext": classification.get("subcontext"),
            "confidence": classification.get("confidence"),
            "cross_refs": classification.get("cross_refs")
        }

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)