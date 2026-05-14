# jeune-cadre-dynamique-dns

Client DynDNS pour mettre à jour un nom de domaine Infomaniak et envoyer une notification par email lorsque l'IP change.

## Installation

1. Créer un environnement virtuel Python :

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Installer les dépendances :

   ```bash
   pip install -r requirements.txt
   ```
3. Copier `.env.example` en `.env`.
4. Remplir les variables d'environnement avec les identifiants Infomaniak et la configuration SMTP.
5. Rendre le script exécutable :

   ```bash
   chmod +x dyn_dns_updater.py
   ```

## Usage

Lancer manuellement :

```bash
python ./dyn_dns_updater.py
```

## Cron

Ajouter une tâche cron sur le Raspberry Pi pour exécuter le script régulièrement, par exemple toutes les 15 minutes :

```cron
*/15 * * * * cd /path/to/jeune-cadre-dynamique-dns && ./venv/bin/python dyn_dns_updater.py >> logs.log 2>&1
```

## Fichier d'environnement

- `INFOMANIAK_USERNAME` et `INFOMANIAK_PASSWORD` pour l'authentification DynDNS.
- `INFOMANIAK_HOSTNAME` = `neuve.3sdl.ch`.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` pour l'envoi d'email.
- `EMAIL_TO` pour la notification.
- `SMTP_USE_TLS` ou `SMTP_USE_SSL` pour la connexion SMTP.
- `SMTP_FROM` pour l'adresse de l'expéditeur.
