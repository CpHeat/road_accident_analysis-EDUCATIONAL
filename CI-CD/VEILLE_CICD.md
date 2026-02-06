Phase 0:

Mission 1 : Comprendre CI/CD

Question 1 - Qu'est-ce que la CI (Continuous Integration) ?
- La CI permet d'automatiser les étapes de vérification redondantes lorsqu'on pousse du code : tests, linting, check failles de sécurité/fuites de credentials etc..
- Les principes clés sont de ne pas deployer du code de mauvaise qualité, de verifier que le nouveau code ne casse pas les fonctionnalités existantes, ne pose pas de problemes de sécurité avant de passer à la phase de distribution/déploiement
- GitHub Actions, Jenkins, Semaphore

Question 2 - Qu'est-ce que le CD (Continuous Deployment/Delivery) ?
- Le continuous delivery crée des images et les distribue sur dockerhub ou ghcr par exemple, le continuous deployment va déployer en plus ces images en production
- Le bénéfice est un gain de temps énorme pour les équipes DevOps et une réactivité accrue des équipes de dev (le code est en prod qq minutes après avoir été poussé, on peut appliquer des fix presque en direct et itérer beaucoup plus fréquement selon les retours utilisateurs), le risque est de metre en production une version cassée du produit si les verifications en amont ont été mal pensées

Question 3 - Pourquoi CI/CD est important ?
- On évite de pousser du code non testé, des credentials, les erreurs d'inattention sont capturées par la pipeline et bloquées
- On évite de devoir exécuter les tests, verifier le linting, créer les images, pousser sur le container registry, déployer à la main a chaque itération du code (y compris pour des petits fixes de qq lignes)
- On évite les problèmes de communication entre les équipes de dev et les équipes de déploiement et la surcharge des équipe de déploiement. Celles-ci peuvent se concentrer sur d'autres tâches

Mission 2 : Maîtriser uv

Question 1 - Qu'est-ce que uv ?
- uv remplace pip/poetry/pipenv (et d'autres) en un seul outil
- uv est plus rapide et plus simple à utiliser. Il permet également de créer facilement des environnements virtuels, installer en une ligne différentes versions de python..

Question 2 - Comment uv fonctionne avec pyproject.toml ?
[project]
name = "backend" # Nom du projet (permet a uv de savoir où chercher)
version = "0" # Version du projet
description = "Add your description here" # Description du projet
readme = "README.md" # Adresse du readme du projet
requires-python = "==3.12.*" # Version de python attendue
dependencies = [] # Liste des dépendances globales du projet (mise a jour a chaque appel de uv add *)
[dependency-groups]
dev = ["pytest"] # Liste des dépendances spécifiques a la release dev

Un appel a uv sync crée la venv si nécessaire et installe toutes les dépendances nécessaires
uv build va créer une distribution du projet dans un dossier dist

Question 3 - Comment utiliser uv dans GitHub Actions ?

steps:
    - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          # Install a specific version of uv.
          version: "0.9.29"
          enable-cache: true

    - name: Install the project
        run: uv sync

Mission 3 - Comprendre Semantic Release

Question 1 - Qu'est-ce que le versionnage sémantique (SemVer) ?
- le premier chiffre (MAJOR) représente une version majeure, cad avec des breaking changes. l'exemple courant serait une version d'api ayant fortement changé ses endpoints, au points que les appels ne sont plus compatibles avec ceux de la version précedente
le second chiffre (MINOR) représente une version mineure, cad une/des nouvelles features mais de maniere transparente, entierement compatible avec l'ancienne version.
le troisième chiffre (PATCH) représente un simple fix

Question 2 - Qu'est-ce que Conventional Commits ?
- un commit doit contenir un titre (type: description), un corps (description claire des changements) et un pied (peut par exemple contenir la description d'un breaking change)
- il y a 2 types primordiaux: feat (nouvelle feature) et fix (réparation/modification mineure). Un breaking change peut etre indiqué par breaking change dans le pied, ou un ! avant le type de commit,..
d'autres types existent mais ne sont pas pris en compte pour le versioning
- Le versioning doit tenir compte de ces 3 types: bumper MAJOR si breaking change, bumper MINOR si feat, bumper PATCH si fix

Question 3 - Comment python-semantic-release fonctionne ?
- uv run semantic-release generate-config --pyproject >> pyproject.toml permet de générer une configuration de base à ajouter dans pyproject.toml
on pourra y définir quels mots-clés chercher dans les commits pour céfinir les versions, comment gérer le changelog, les builds...
- le changelog est généré a chaque semantic release
- les releases sont crées via --vcs-release suviant les règles build_command

Question 5 - MkDocs & GitHub Pages
- MKDocs génère la doc a partir du dossier docs et d'un fichier de configuration, et la publie en site statique
- la commande mkdocs gh-deploy génère une doc sur la branche gh_pages qui la rend accessible via github pages
- mkdocstrings génère une doc pour les classes fonctions methodes etc... sur le meme principe que MKDocs
