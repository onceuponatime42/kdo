import os
from notion_client import Client
from datetime import datetime
import requests
import base64

# Récupérer les variables d'environnement
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
TOKEN = os.environ["TOKEN"]
REPO = os.environ["REPO"]
FICHIER = os.environ["FICHIER"]

notion = Client(auth=NOTION_TOKEN)

def get_pages(database_id):
    results = []
    has_more = True
    next_cursor = None

    while has_more:
        response = notion.databases.query(
            **({"database_id": database_id, "start_cursor": next_cursor} if next_cursor else {"database_id": database_id})
        )
        results.extend(response["results"])
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor", None)
    return results

def get_notion_url(page_name, page_id):
    # Notion URLs are constructed as https://www.notion.so/{page_id_without_dashes}
    page_id_no_dash = page_id.replace("-", "")
    return f"https://www.notion.so/{page_name.replace(' ', '-')}-{page_id_no_dash}"

def find_page_by_today_date(pages):
    today = datetime.today()
    for page in pages:
        properties = page["properties"]
        page_name = properties["Name"]["title"][0]["plain_text"]
        
        long_id = properties["Long ID"]["formula"]["string"]
        date_value = properties["Date"]["date"]["start"]
        date_obj = datetime.fromisoformat(date_value)
        if date_obj.day == today.day and date_obj.month == today.month:
            return get_notion_url(page_name, long_id)
    return None



def update_html(nouvelle_url):

    # RECUPERATION DU SHA DU FICHIER
    headers = {"Authorization": f"token {TOKEN}"}
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{FICHIER}", headers=headers)
    json = r.json()
    sha = json['sha']

    # PREPARATION DU NOUVEAU CONTENU
    nouveau_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; URL='{nouvelle_url}'" />
    </head>
    <body>
        Redirection automatique...
    </body>
    </html>
    """

    content_b64 = base64.b64encode(nouveau_html.encode()).decode()

    data = {
        "message": "Mise à jour url automatique",
        "content": content_b64,
        "sha": sha
    }

    # PUSH DE LA MODIFICATION
    r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{FICHIER}", headers=headers, json=data)
    if r.status_code == 200 or r.status_code == 201:
        print("Mise à jour effectuée!")
    else:
        print("Erreur!", r.text)

if __name__ == "__main__":
    pages = get_pages(DATABASE_ID)
    url = find_page_by_today_date(pages)
    if url:
        print(f"La page à consulter aujourd'hui : {url}")
        update_html(url)
    else:
        print("Aucune page ne correspond à la date d'aujourd'hui.")
