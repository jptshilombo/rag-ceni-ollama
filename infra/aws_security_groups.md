# Groupes de securite AWS

## Regles entrantes recommandees

- `22/tcp` : uniquement depuis l'IP d'administration ou le VPN.
- `8000/tcp` : uniquement depuis des IPs specifiques pour un POC. Ne pas exposer largement sur Internet.
- `80/tcp` et `443/tcp` : ouverts uniquement si l'API est placee derriere un reverse proxy ou un ALB.
- `6333/tcp` : ne pas ouvrir publiquement. Qdrant doit rester accessible uniquement en localhost, reseau Docker ou sous-reseau prive.

## Qdrant

En production, ne publiez pas le port `6333` dans Docker Compose. L'API FastAPI communique avec Qdrant via le reseau Docker interne avec `QDRANT_URL=http://qdrant:6333`.

Si une exposition temporaire est necessaire pour une operation d'administration, limitez la regle a une seule IP de confiance et retirez-la apres usage.

## Evolution recommandee

Pour un usage durable :

- Placer l'API derriere un Application Load Balancer.
- Utiliser ACM pour TLS/HTTPS.
- Ajouter une authentification applicative.
- Journaliser les acces API.
- Deplacer les instances dans des subnets prives des que l'architecture depasse le POC.
