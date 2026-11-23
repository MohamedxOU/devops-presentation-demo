#!/usr/bin/env python3
"""Petit client Trello pour la chaîne CI/CD (API REST, clé + token).

Usage :
  trello.py lists <board_id>            affiche les listes d'un tableau (préparation)
  trello.py card-from-commit            extrait la carte citée dans le dernier commit
  trello.py comment <card> <texte>      commente une carte
  trello.py move <card> <list_id>       déplace une carte vers une liste
  trello.py create <list_id> <titre> [description]
                                        crée une carte (sauf si une carte ouverte
                                        porte déjà ce titre dans la liste)

Sans TRELLO_KEY / TRELLO_TOKEN, chaque commande affiche un message et sort
avec le code 0 : la démo fonctionne aussi sans Trello.
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

API = "https://api.trello.com/1"
CARD_PATTERN = re.compile(r"(?:trello\.com/c/|\[trello:)([A-Za-z0-9]{8,24})")


def _call(method: str, path: str, **params):
    params.update(key=os.environ["TRELLO_KEY"], token=os.environ["TRELLO_TOKEN"])
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method=method, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
        return json.loads(resp.read() or b"null")


def card_from_commit() -> str:
    message = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True, check=True
    ).stdout
    match = CARD_PATTERN.search(message)
    return match.group(1) if match else ""


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    command, args = argv[0], argv[1:]

    if command == "card-from-commit":
        print(card_from_commit())
        return 0

    if not os.environ.get("TRELLO_KEY") or not os.environ.get("TRELLO_TOKEN"):
        print("Trello non configuré : étape ignorée.")
        return 0

    if command == "lists":
        for lst in _call("GET", f"/boards/{args[0]}/lists", fields="name"):
            print(f"{lst['id']}  {lst['name']}")
    elif command == "comment":
        _call("POST", f"/cards/{args[0]}/actions/comments", text=args[1])
        print(f"Commentaire ajouté sur la carte {args[0]}")
    elif command == "move":
        if not args[1]:
            print("Liste cible non configurée : déplacement ignoré.")
            return 0
        _call("PUT", f"/cards/{args[0]}", idList=args[1])
        print(f"Carte {args[0]} déplacée")
    elif command == "create":
        list_id, title = args[0], args[1]
        if not list_id:
            print("Liste cible non configurée : création ignorée.")
            return 0
        existing = _call("GET", f"/lists/{list_id}/cards", fields="name")
        if any(card["name"] == title for card in existing):
            print(f"Carte déjà ouverte : {title}")
            return 0
        card = _call("POST", "/cards", idList=list_id, name=title, desc=" ".join(args[2:]))
        print(f"Carte créée : {card['shortUrl']}")
    else:
        print(f"Commande inconnue : {command}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
