import json
import time
import requests

# Konfiguracja API Ollama
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODELS_URL = "http://localhost:11434/api/tags"
ALL_MODELS = 1
MAX_SIZE = 17165189120

# Wczytanie testów z pliku JSON
def load_json(filename):
    print("Load", filename)
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

# Pobranie listy dostępnych modeli
def get_available_models():
    print("Get available models.")
    try:
        response = requests.get(OLLAMA_MODELS_URL, timeout=10)
        response.raise_for_status()
        models = response.json().get("models", [])

        print("Ollama models:", len(models))
        print("")

        available_models = []
        for model in models:
            model_name = model["name"]
            model_size = model["size"]
            available_models.append({"name": model_name, "size": model_size})
        return available_models    
        #return [model["name"] for model in models]
    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas pobierania listy modeli: {e}")
        return []

# Wysłanie zapytania do modelu
def query_ollama(model, prompt, context=""):
    payload = {"model": model, "prompt": prompt, "stream": False}
    print("Query ollama:", payload["prompt"])

    if context:
        payload["context"] = context
    headers = {"Content-Type": "application/json"}
    start_time = time.time()
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=3000)
        duration = time.time() - start_time
        response.raise_for_status()
        result = response.json()
        
        print("response:", result.get("response", "Brak odpowiedzi"))
        print(90*"#")
        print("")

        return {
            "response": result.get("response", "Brak odpowiedzi"),
            "total_duration": result.get("total_duration", 0),
            "load_duration": result.get("load_duration", 0),
            "prompt_eval_count": result.get("prompt_eval_count", 0),
            "prompt_eval_duration": result.get("prompt_eval_duration", 0),
            "eval_count": result.get("eval_count", 0),
            "eval_duration": result.get("eval_duration", 0)
        }
    except requests.exceptions.RequestException as e:
        print(f"Błąd zapytania do modelu {model}: {e}")
        return {"response": f"Błąd: {str(e)}", "total_duration": duration, "load_duration": 0, "prompt_eval_count": 0, "prompt_eval_duration": 0, "eval_count": 0, "eval_duration": 0}

# Wykonanie testów na wielu modelach
def run_tests(models, tests, output_file):
    print("Run tests.")
    available_models = get_available_models()
    results = {}

    if ALL_MODELS == 1:
        models = available_models #wszystkie modele
        
    for model in models:
        if model not in available_models:
            print(f"Model {model["name"]} nie jest dostępny na serwerze Ollama. Pomijam testy.")
            print("")
            continue
        if model["size"] > MAX_SIZE:
            print(f"Model {model["name"]} zbyt wielki! Pomijam testy.")
            print("")
            continue

        model_results = []

        print("Model", model["name"])
        print((len(model["name"])+6)*"=")
        print(round(model["size"] / 1024 / 1024 / 1024, 1), "GB")
        print("")
        #a = input("Czekam na ENTER...")
        
        for test in tests:
            question, context = test["query"], test.get("context", "")
            result = query_ollama(model["name"], question, context)
            model_results.append({
                "query": question,
                "expected": test["answer"],
                "response": result["response"],
                "duration": result["total_duration"] / 1e9,  # Konwersja nanosekund na sekundy
                "score": 0,  # TODO: dodać ocenianie odpowiedzi
                "stats": {
                    "load_duration": result.get("load_duration", 0) / 1e9,
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "prompt_eval_duration": result.get("prompt_eval_duration", 0) / 1e9,
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0) / 1e9
                }
            })
        results[model["name"]] = model_results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    return results

# Generowanie Markdown
def generate_markdown(results):
    md = "| Model | Pytanie | Odpowiedź modelu | Czas odpowiedzi (s) | Tokeny promptu | Tokeny wygenerowane |\n|---|---|---|---|---|---|\n" + "".join(
        f"| {model} | {res['query']} | {res['response']} | {res['duration']:.2f} | {res['stats']['prompt_eval_count']} | {res['stats']['eval_count']} |\n"
        for model, model_results in results.items() for res in model_results
    )
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

    print("")
    print(90*"#")
    print("")
    print("Testy zakończone. Wyniki zapisane do results.json i results.md")
