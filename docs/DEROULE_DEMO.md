# Déroulé de la démo (environ 10 minutes)

Fil rouge : la carte Trello **« Afficher la salle de chaque exposé »** traverse les 8 phases,
du tableau Trello jusqu'à la production surveillée dans Grafana.

## Avant de commencer (5 minutes avant de passer)

- Plateforme lancée (`cd infra && docker compose up -d`) et une première exécution déjà faite
  (README, étape 6) : production en ligne en version précédente.
- Onglets ouverts dans cet ordre :
  1. Trello, tableau **M354 DevOps**
  2. VS Code sur le dépôt, terminal intégré ouvert
  3. Jenkins, job **M354 : chaîne CI/CD**
  4. http://localhost:8001 (staging)
  5. http://localhost:8000 (production)
  6. Grafana, tableau **M354 : planning des exposés**
  7. Docker Hub, page du dépôt `m354-planning` (onglet *Tags*)
- Dans un terminal à part : `./scripts/traffic.sh` (anime les courbes Grafana).
- Remplacer `AbCd1234` ci-dessous par l'identifiant court de votre carte Trello.
- Zoom navigateur à 125 % pour la salle.

## Scénario

| # | Phase | Ce qu'on fait | Ce qu'on montre | Durée |
|---|---|---|---|---|
| 1 | Plan | Trello : ouvrir la carte dans `En cours` | Les critères d'acceptation deviennent des tests | 45 s |
| 2 | Code | Branche, patch, commit, push (commandes ci-dessous) | Diff dans VS Code ; hooks pre-commit qui passent | 1 min 15 |
| 3 | Build + Test | Jenkins : **Scan Multibranch Pipeline Now** | Branche `feat/salle` : étapes vertes une par une | 1 min 30 |
| 4 | Test (bug) | Pousser la branche `demo/bug` | Étape **Test · unitaires** rouge, test en échec, Build jamais lancé | 1 min |
| 5 | Release | GitHub : Pull Request `feat/salle` vers `main`, **Merge** | Jenkins `main` : étape Release, tag `1.0.N` sur Docker Hub, `RELEASE.md` | 1 min |
| 6 | Deploy | Attendre le staging, puis cliquer **Déployer** | Staging (8001) avec la colonne Salle ; porte humaine | 1 min 30 |
| 7 | Operate | Ouvrir la production (8000), puis Trello | Badge de version ; carte déplacée dans `Terminé` avec commentaire ; job de retour arrière | 1 min 15 |
| 8 | Monitor | Grafana, puis incident simulé | Version en prod qui change ; panne détectée ; carte « Incident » créée dans Trello | 1 min 30 |

### Commandes, phase 2 (Code)

```bash
git checkout main && git pull
git checkout -b feat/salle
git apply demo/01-feat-salle.patch
git diff                                  # montrer le diff dans VS Code
git commit -am "Afficher la salle de chaque exposé [trello:AbCd1234]"
git push -u origin feat/salle
```

Phrase clé : « Le commit cite la carte Trello : le pipeline va la commenter tout seul. »

### Commandes, phase 4 (bug volontaire)

À lancer juste après le push précédent, pour que les deux pipelines tournent en parallèle :

```bash
git checkout -b demo/bug
git apply demo/02-bug.patch
git commit -am "Refactor du tableau [trello:AbCd1234]"
git push -u origin demo/bug
git checkout feat/salle
```

Phrase clé : « Une faute de frappe, `sale` au lieu de `salle`. Le test l'a vue : le bug n'a
jamais atteint la production, et la carte Trello affiche le pipeline rouge. »

### Phase 6 (Deploy)

Pendant que `main` tourne : montrer le graphe des étapes (vue **Stages** ou **Pipeline Graph**).
Quand Jenkins s'arrête sur **Deploy · approbation**, ouvrir http://localhost:8001 :
la colonne Salle est là, badge *staging*. Revenir sur Jenkins et cliquer **Déployer**.

Phrase clé : « Ici un humain valide : c'est de la livraison continue. Sans ce clic, ce serait du
déploiement continu, sans changer une ligne du pipeline. »

### Phase 7 (Operate)

1. http://localhost:8000 : badge *production* et version `1.0.N`.
2. Trello : la carte est passée dans `Terminé`, avec le commentaire « En production : v1.0.N ».
3. Retour arrière (si le temps le permet) : job **M354 : retour arrière**, **Build with Parameters**,
   `VERSION` = la version précédente. La colonne Salle disparaît de la production en quelques
   secondes. Relancer avec la nouvelle version pour revenir.

Phrase clé : « Comme chaque version est une image immuable, revenir en arrière, c'est juste
redéployer une image existante. »

### Phase 8 (Monitor) : la boucle se referme

1. Grafana : la tuile **Version en production** affiche la nouvelle version ; les courbes de
   requêtes et de latence bougent avec le trafic.
2. Simuler une panne :
   ```bash
   docker stop app-production
   ```
   Après quelques secondes, la tuile **Production** passe à **HORS LIGNE**.
3. Jenkins : lancer **M354 : sonde de production** (elle tourne aussi seule toutes les 5 min).
   Elle échoue et crée la carte **« Incident production : sonde en échec »** dans `À faire`.
4. Montrer la carte dans Trello, puis réparer :
   ```bash
   docker start app-production
   ```

Phrase clé : « Ce qu'on observe en production redevient une tâche dans le Plan : la boucle est bouclée. »

## Plan B

- Enregistrer une vidéo complète de la démo pendant une répétition (OBS Studio, gratuit).
- Si Jenkins est lent le jour J : montrer les builds de la répétition (historique conservé).
- Si le réseau tombe : Trello et Docker Hub sont optionnels, tout le reste tourne en local.

## Textes pour les slides « Dans notre démo »

| Slide | Phase | Texte proposé |
|---|---|---|
| 14 | Plan | Trello : la carte « Afficher la salle de chaque exposé » et ses critères d'acceptation. |
| 15 | Code | VS Code + Git : branche feat/salle, commit qui cite la carte Trello, hooks pre-commit (ruff, gitleaks). |
| 16 | Build | Docker : une image Python non-root construite une seule fois, étiquetée par commit. |
| 17 | Test | pytest (couverture ≥ 80 %), ruff, Bandit, pip-audit, Trivy : un échec rend le pipeline rouge. |
| 18 | Release | Docker Hub : image 1.0.N + notes de version archivées dans Jenkins. |
| 19 | Deploy | Jenkins : staging automatique, approbation humaine, puis production. |
| 20 | Operate | Smoke test, redémarrage automatique, job Jenkins de retour arrière. |
| 21 | Monitor | Prometheus + Grafana ; la sonde Jenkins ouvre une carte Trello en cas d'incident. |
