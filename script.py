import requests
from bs4 import BeautifulSoup
import os
import git
import argparse
from urllib.parse import quote

# Configuration
PERPLEXITY_API_KEY = "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"
GIT_REPO_URL = "grond.iut-fbleau.fr/djedidi/saedjedidi.git"
GIT_USERNAME = "djedidi"
GIT_PASSWORD = "Hzcat@9977ejarutUP."
ENCODED_PASSWORD = quote(GIT_PASSWORD)

PROMPT_TEMPLATE = (
    "Fais uniquement les exercices dans ce que je te copie colle, "
    "dans ce chat, code uniquement en C89, donne-moi tous les codes en texte brut "
    "directement afin que je copie-colle, et mets bien le titre de l'exo à chaque fois. "
    "Ne mets pas de commentaires. Utilise la documentation disponible dans : "
    "https://iut-fbleau.fr/sitebp/dev11bis/"
)

def fetch_page_content(url):
    """Récupère et extrait le contenu principal de la page spécifiée."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find('div', class_='container')
        if not container:
            raise ValueError("Aucun contenu trouvé dans l'élément de classe 'container'.")
        content = container.get_text(strip=True, separator='\n')
        print(f"Contenu extrait : {content[:200]}...")
        return content
    except Exception as e:
        print(f"Erreur lors de la récupération de la page : {e}")
        return None

def solve_exercise_with_perplexity(exercise_text):
    """Envoie l'exercice au modèle Perplexity pour obtenir une solution."""
    try:
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = [
            {"role": "system", "content": PROMPT_TEMPLATE},
            {"role": "user", "content": exercise_text}
        ]
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": messages,
            "max_tokens": 1500
        }
        print(f"Envoi de l'exercice à Perplexity : {exercise_text[:200]}...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", None)
    except Exception as e:
        print(f"Erreur lors de l'appel à l'API Perplexity : {e}")
        return None

def save_exercise_to_file(title, content):
    """Enregistre la solution de l'exercice dans un fichier."""
    filename = f"{title}.c"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Exercice sauvegardé dans : {filename}")
        return filename
    except IOError as e:
        print(f"Erreur lors de la sauvegarde de {filename} : {e}")
        return None

def sync_and_push_to_git():
    """Synchronise et pousse les modifications dans le dépôt Git."""
    try:
        repo = git.Repo(os.getcwd())
        remote_url = f"https://{GIT_USERNAME}:{ENCODED_PASSWORD}@{GIT_REPO_URL}"
        repo.git.stash('save', 'temporary stash')
        repo.git.pull(remote_url, 'main')
        try:
            repo.git.stash('pop')
        except git.exc.GitCommandError:
            print("Pas de stash à appliquer.")
        repo.git.add(A=True)
        repo.index.commit("Ajout des exercices")
        repo.git.push(remote_url, 'main')
        print("Les fichiers ont été poussés avec succès.")
    except Exception as e:
        print(f"Erreur lors du push Git : {e}")

def process_exercises(url):
    """Processus principal pour traiter les exercices d'une URL donnée."""
    print("Récupération du contenu de la page...")
    page_content = fetch_page_content(url)
    if not page_content:
        return
    print("Extraction des exercices...")
    exercises = [ex.strip() for ex in page_content.split("Exercice") if ex.strip()]
    successful_exercises = 0
    for i, exercise in enumerate(exercises, start=1):
        title = f"exo{i}"
        print(f"\nRésolution de {title}...")
        solution = solve_exercise_with_perplexity(exercise)
        if solution and save_exercise_to_file(title, solution):
            successful_exercises += 1
    if successful_exercises > 0:
        print(f"\n{successful_exercises} exercices traités avec succès. Push vers Git...")
        sync_and_push_to_git()
    else:
        print("Aucun exercice n'a été traité avec succès. Abandon du push Git.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Résout les exercices d'une URL donnée")
    parser.add_argument("--url", required=True, help="URL de la page contenant les exercices")
    args = parser.parse_args()
    process_exercises(args.url)
