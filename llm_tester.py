import json
import time
import requests

# Konfiguracja API Ollama
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Wczytanie testów z pliku JSON
def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

# Wysłanie zapytania do modelu
def query_ollama(model, prompt, context=""):
    payload = {"model": model, "prompt": prompt, "context": context}
    start_time = time.time()
    response = requests.post(OLLAMA_API_URL, json=payload)
    duration = time.time() - start_time
    if response.status_code == 200:
        result = response.json()
        return result.get("response", ""), duration
    else:
        return "ERROR", duration

# Wykonanie testów na wielu modelach
def run_tests(models, tests, output_file):
    results = {}
    for model in models:
        model_results = []
        for test in tests:
            question, context = test["query"], test.get("context", "")
            answer, duration = query_ollama(model, question, context)
            model_results.append({
                "query": question,
                "expected": test["answer"],
                "response": answer,
                "duration": duration,
                "score": 0  # TODO: dodać ocenianie odpowiedzi
            })
        results[model] = model_results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    return results

# Generowanie Markdown
def generate_markdown(results):
    md = "| Model | Pytanie | Odpowiedź modelu | Czas odpowiedzi (s) |\n|---|---|---|---|\n"
    for model, model_results in results.items():
        for res in model_results:
            md += f"| {model} | {res['query']} | {res['response']} | {res['duration']:.2f} |\n"
    return md

if __name__ == "__main__":
    test_file = "tests.json"
    models_file = "models.json"
    output_file = "results.json"
    markdown_file = "results.md"
    
    tests = load_json(test_file)
    models = load_json(models_file)
    results = run_tests(models, tests, output_file)
    
    md_output = generate_markdown(results)
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(md_output)
    
    print("Testy zakończone. Wyniki zapisane do results.json i results.md")
