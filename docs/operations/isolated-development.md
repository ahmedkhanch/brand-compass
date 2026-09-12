# Développement isolé sur Hetzner 8 Go

Le serveur sélectionné après audit est `178.105.228.170`. Le code est dans `/srv/radaros/source` et la base de validation dans `/srv/radaros/state`. Aucune base de comptes historique ni clé de fournisseur payant n’est copiée.

## Backend

Le service `radaros-api` utilise l’utilisateur système `radaros`, un environnement Python dédié et écoute uniquement sur `127.0.0.1:14399`. Son démarrage exécute Alembic avant Uvicorn. Les deux modes de démonstration sont désactivés. Les lectures privées doivent donc refuser un token de démonstration même si le frontend historique possède une interface de démo.

Le fichier de service versionné est `ops/radaros-api.service`. Le fichier `/srv/radaros/backend.env`, absent du dépôt, contient la configuration locale. Une installation existante doit conserver sa configuration et sa base ; ne pas les remplacer par un exemple.

```ini
DATABASE_URL=sqlite+aiosqlite:////srv/radaros/state/radaros.db
DEMO_MODE=false
ALLOW_DEMO_AUTH=false
DEBUG=false
```

Les validations de sécurité utilisent leur propre base temporaire et ne passent pas par la base du service. `/docs` et `/openapi.json` appartiennent à ce backend ; les fixtures HTTP des tests n’y sont jamais enregistrées.

## Contrôles et retour arrière

Après démarrage, contrôler le statut systemd, la santé HTTP, Swagger, le refus 401 d’une lecture sans identité et le refus 401 d’un token démo. Le mode d’identité doit annoncer `unconfigured` tant que Clerk n’a pas été configuré.

Conserver le commit et l’artefact précédents avant mise à jour. Pour ce lot sans migration nouvelle, revenir au code de la livraison précédente puis redémarrer le service suffit. Ne jamais revenir à l’API historique non sécurisée en exposition publique. Les futures migrations imposeront leur procédure de retour arrière propre, testée sur copie jetable.

Le site public de suivi reste protégé par son proxy ; le backend isolé n’ajoute aucun port public. La réactivation du produit, des jobs et des fournisseurs est suivie dans F03–F05.
