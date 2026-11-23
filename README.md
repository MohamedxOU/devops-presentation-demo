# Démo M354 : Culture DevOps et chaîne CI/CD

Une petite application web Python (Flask) qui affiche le planning des exposés du module,
et une chaîne DevOps complète avec un outil gratuit et spécialisé par phase.

| Phase | Outil | Rôle dans la démo |
|---|---|---|
| 1. Plan | **Trello** | Carte « Afficher la salle de chaque exposé », déplacée et commentée automatiquement |
| 2. Code | **Git + GitHub + VS Code + pre-commit** | Branche, commit qui cite la carte Trello, hooks ruff et gitleaks |
| 3. Build | **Docker** | Une image construite une seule fois, non-root, étiquetée par commit |
| 4. Test | **pytest, ruff, Bandit, pip-audit, Trivy** | Tests et couverture, lint, SAST, dépendances, scan de l'image |
| 5. Release | **Docker Hub** | Image versionnée `1.0.N` + `RELEASE.md` archivé dans Jenkins |
| 6. Deploy | **Jenkins** | Staging automatique, approbation humaine, puis production |
| 7. Operate | **Jenkins + Docker** | Smoke test, redémarrage automatique, job de retour arrière |
| 8. Monitor | **Prometheus + Grafana** | Tableau de bord en direct ; une sonde Jenkins ouvre une carte Trello en cas d'incident |

Tout tourne en local sur un seul poste avec Docker. Seuls Trello, GitHub et Docker Hub
sont en ligne (comptes gratuits).

```
GitHub ──(scan 1 min)──> Jenkins ──> tests ──> image ──> Docker Hub
                            │                              │
                            ├──> app-staging  :8001 <──────┤
                            ├──(approbation)               │
                            └──> app-production :8000 <────┘
                                       │
                         Prometheus :9090 ──> Grafana :3000
```

---

## 1. Prérequis (une seule fois)

- **Docker** avec Docker Compose v2 (Linux, ou Docker Desktop sur macOS/Windows ;
  sous Windows, lancer toutes les commandes depuis WSL2).
- **Git** et **VS Code**.
- 4 Go de RAM libres et environ 5 Go de disque.
- Comptes gratuits : **GitHub**, **Trello**, **Docker Hub**.

## 2. Dépôt GitHub

1. Créer un dépôt **public** `m354-devops-demo` sur GitHub (public = Jenkins le lit sans identifiants).
2. Pousser ce dossier :
   ```bash
   git init -b main
   git add .
   git commit -m "Base de la démo"
   git remote add origin https://github.com/VOTRE_COMPTE/m354-devops-demo.git
   git push -u origin main
   ```
3. Optionnel mais conseillé, installer les hooks locaux :
   ```bash
   python3 -m venv .venv && . .venv/bin/activate
   pip install -r requirements-dev.txt pre-commit
   pre-commit install
   ```

## 3. Trello (phase Plan)

1. Créer un tableau **M354 DevOps** avec 4 listes : `Backlog`, `À faire`, `En cours`, `Terminé`.
2. Créer la carte **« Afficher la salle de chaque exposé »** dans `En cours`, avec ses critères
   d'acceptation en description :
   - la page d'accueil affiche une colonne Salle ;
   - chaque exposé a une salle ;
   - un test automatique le vérifie.
3. Noter l'identifiant court de la carte : c'est le code dans son URL,
   `https://trello.com/c/AbCd1234/...` donne `AbCd1234`.
4. Obtenir une clé et un token API : sur https://trello.com/power-ups/admin, créer un
   Power-Up (nom libre), ouvrir l'onglet **API key**, générer la clé, puis cliquer sur le
   lien **Token** pour autoriser votre compte.
5. Récupérer les identifiants des listes (l'identifiant du tableau est dans son URL,
   `https://trello.com/b/XyZ98765/...`) :
   ```bash
   TRELLO_KEY=... TRELLO_TOKEN=... python3 scripts/trello.py lists XyZ98765
   ```
   Garder l'id de `À faire` (TRELLO_LIST_TODO) et celui de `Terminé` (TRELLO_LIST_DONE).

Sans Trello, la démo fonctionne quand même : les étapes Trello affichent « non configuré ».

## 4. Docker Hub (phase Release)

1. Sur Docker Hub : **Account settings > Personal access tokens > Generate**, droits *Read & Write*.
2. Garder le nom d'utilisateur et le token.

Sans Docker Hub, laisser les champs vides : l'image reste dans le Docker local et la démo continue.

## 5. Lancer la plateforme

```bash
cd infra
cp .env.example .env      # puis remplir .env avec les valeurs ci-dessus
docker compose up -d --build
```

Le premier lancement prend plusieurs minutes (image Jenkins et plugins). Ensuite :

| Service | URL | Identifiants |
|---|---|---|
| Jenkins | http://localhost:8080 | `admin` / `JENKINS_ADMIN_PASSWORD` |
| Grafana | http://localhost:3000 | lecture sans compte, `admin` / `GRAFANA_ADMIN_PASSWORD` |
| Prometheus | http://localhost:9090 | aucun |
| App staging | http://localhost:8001 | après le premier déploiement |
| App production | http://localhost:8000 | après le premier déploiement |

Jenkins est configuré entièrement par fichier (`infra/jenkins/casc.yaml`) : utilisateur,
identifiants et 3 jobs sont créés automatiquement.

- **M354 : chaîne CI/CD** (multibranche) : chaque branche passe la CI, `main` va jusqu'en prod.
- **M354 : retour arrière (Operate)** : remet une version précédente en production.
- **M354 : sonde de production (Monitor)** : toutes les 5 minutes.

## 6. Première exécution (avant le jour J)

1. Dans Jenkins, ouvrir **M354 : chaîne CI/CD** puis **Scan Multibranch Pipeline Now**.
2. La branche `main` démarre. À l'étape **Deploy · approbation**, cliquer sur **Déployer**.
3. Vérifier http://localhost:8001 (staging) puis http://localhost:8000 (production).
4. Lancer une fois **M354 : sonde de production** à la main (cela active son déclencheur).
5. Ouvrir Grafana : le tableau de bord **M354 : planning des exposés** s'affiche.

Cette première exécution télécharge aussi les images Python et Trivy et la base de
vulnérabilités : le jour J, le pipeline sera beaucoup plus rapide.

## 7. Répéter la démo

Le scénario complet, minute par minute, est dans [`docs/DEROULE_DEMO.md`](docs/DEROULE_DEMO.md).
Les deux modifications de code jouées en direct sont prêtes dans `demo/` :

- `demo/01-feat-salle.patch` : la fonctionnalité (colonne Salle + test) ;
- `demo/02-bug.patch` : un bug volontaire, arrêté par les tests.

Pour revenir à l'état initial après une répétition :

```bash
git checkout main && git pull
git revert -m 1 --no-edit HEAD   # annule le merge de la fonctionnalité
git push
# Trello : remettre la carte dans « En cours » ; supprimer les cartes « Incident »
```

## 8. Arrêter

```bash
docker rm -f app-staging app-production
cd infra && docker compose down          # garde les données Jenkins
cd infra && docker compose down -v       # efface aussi l'historique Jenkins
```

## Dépannage

| Symptôme | Solution |
|---|---|
| Jenkins ne démarre pas | `docker logs jenkins` ; vérifier que `.env` existe dans `infra/` |
| `permission denied` sur `/var/run/docker.sock` | Jenkins doit tourner en root (déjà le cas dans `infra/jenkins/Dockerfile`) |
| Le pipeline ne voit pas un nouveau commit | Bouton **Scan Multibranch Pipeline Now** (le scan auto passe chaque minute) |
| `docker push` refusé | `DOCKER_IMAGE` doit commencer par votre nom Docker Hub ; token en *Read & Write* |
| Trivy lent la première fois | Normal : téléchargement de la base, mise en cache ensuite |
| Grafana vide | Attendre 10 s après le premier déploiement ; lancer `./scripts/traffic.sh` |

## Structure

```
app/                  application Flask (pages, API, /health, /version, /metrics)
tests/                tests pytest
Dockerfile            image de production (non-root, healthcheck)
Jenkinsfile           pipeline principal (CI sur toutes les branches, CD sur main)
jenkins/              pipelines de retour arrière et de sonde
scripts/              déploiement, smoke test, sonde, client Trello, trafic
infra/                Jenkins, Prometheus, Grafana (docker compose)
demo/                 modifications jouées pendant la démo
docs/DEROULE_DEMO.md  scénario de la démo
```

> Note de sécurité : pour rester simple, Jenkins utilise le socket Docker du poste et
> tourne en root. C'est acceptable pour une démo locale, jamais en production.
