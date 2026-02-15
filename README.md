On déploie le projet avec la commande docker compose up -d

Décomposition des dockerfiles :
- Utilisation d'une image de base (ici python 3.12 avec UV préinstallé)
- définition du répertoire de travail (les commande seront relatives a ce dossier)
- définition du répertoire de cache UV (évite les problèmes de permissions)
- installation des dépendances hors UV
- Copie du fichier pyproject.toml contenant les dépendances
- Définition des droits owner sur le dossier de travail pour le user 1001
- définition du user sur un user non-root par sécurité (1001)
- installation des dépendances UV
- copie des fichiers du projet
- définition de la commande effectuée au lancement

Décomposition du docker-compose.yml :
- définition du network pour permettre aux containers de communiquer entre eux (avec bridge)
- pour chaque container :
  - construction de l'image (via Dockerfile) + nom et tag du build
  - nom du container
  - définition du network a utiliser
  - définition des ports a mapper entre host et container
  - définition des variables d'environnement
  - volume(s) a utiliser par le container pour persistance des données créées au runtime
  - pour backend et postgres: healthcheck (commande a executer pendant le runtime pour vérifier que le container est up et fonctionnel)
  - pour front: depends_on définit la necessité d'atendre que le backend soit up avant de lancer le front
  - les variables d'environnement définissent l'adresse de l'API depuis le cotneneur (on utilise le nom du conteneur et son port interne pour y accéder a traver le network docker)
  - définition des volumes docker

Les images sont taggées directement dans docker compose
pour push l'image du backend sur dockerhub j'utilise par exemple docker push cpheat/accident-ml-backend:1.0.3 (si la version que j'ai build via docker compose est la 1.0.3)


