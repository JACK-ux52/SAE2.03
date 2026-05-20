# 1. On utilise l'image officielle Python
FROM python:3.13

# 2. Définit le dossier de travail dans le conteneur
WORKDIR /app

# 3. Copie le fichier des dépendances (requirements.txt)
COPY /app/requirements.txt .

# 4. Installe les bibliothèques (Flask, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copie tout le reste du code source
COPY . .

# 6. Expose le port utilisé par Flask et pour PostgreSQL (souvent 5000)
EXPOSE 5000
EXPOSE 5432

# 7. Commande pour lancer l'application
# Cette commande va lister tous les fichiers du conteneur au démarrage
CMD ["sh", "-c", "python $(find /app -name app.py | head -n 1)"]