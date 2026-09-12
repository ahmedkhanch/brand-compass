# F01/F02 — Identité et accès aux rapports

## Problème et comportement livré

Le socle historique acceptait des identités de démonstration hors démo, exposait le flux de rapports étrangers et laissait le navigateur attribuer un abonnement. Cette livraison exige une identité vérifiée, applique la propriété à chaque lecture/suppression/suivi et filtre les données Ads selon les droits persistés au moment de la requête. Un changement d’URL après paiement ne change aucun droit.

## Responsabilités et contrats

Les routes HTTP délèguent aux services d’identité, d’accès aux rapports et d’abonnement. Les repositories portent les expressions SQLAlchemy ; l’adaptateur JWT vérifie les signatures et les claims sans accès aux données. Le service de suivi ouvre une courte transaction de lecture par actualisation et termine le flux si le rapport disparaît.

Le rapport public utilise une liste explicite de champs autorisés. Les coûts internes ne font pas partie de ce contrat ; les Ads nécessitent le niveau Radar. Un rapport absent ou étranger renvoie toujours 404. Toutes les réponses API/SSE interdisent le stockage en cache. Le client applique également `cache: no-store`.

Le catalogue des opérations, schémas et erreurs est exclusivement **Swagger `/docs`**, généré par FastAPI depuis `/openapi.json`. Aucune seconde liste manuelle de routes n’est maintenue ici.

## Configuration

- `DEMO_MODE=false` et `ALLOW_DEMO_AUTH=false` par défaut. Il faut activer les deux pour accepter les identités de fixtures `dev-user-*`. Réserver ce mode à une base isolée.
- `CLERK_JWT_ISSUER` doit être une URL HTTPS ; `CLERK_AUTHORIZED_PARTIES` doit contenir les origines autorisées, séparées par des virgules. Sans ces paramètres, l’identité réelle échoue avec 503.
- `CLERK_JWT_AUDIENCE` permet d’exiger l’audience d’un template JWT configuré pour cette application. La validation RS256, de l’émetteur, de `exp`, `iat`, `sub` et de `azp` reste obligatoire.
- Les clés publiques sont obtenues par JWKS avec un délai limité. Une indisponibilité produit un 503 générique, jamais un compte anonyme.

## Schéma et exploitation

Aucun changement de schéma dans ce lot. Le démarrage ne lance plus `create_all` ni de PRAGMA SQL. Exécuter `python -m alembic upgrade head` avant le service ; les migrations historiques appliquées restent intactes. Voir [le déploiement isolé](../operations/isolated-development.md).

## Validation

Les tests `backend/tests/security` exercent la frontière HTTP avec une base temporaire créée par Alembic. La fixture de données est une route ajoutée **uniquement par les tests**, absente de l’application démarrée normalement. Les appels suivent aussi une fonction de service utilisant SQLAlchemy.

```sh
cd backend
python -m pytest tests/security -q
```

41 tests passent sur la machine de développement : identité, signatures RSA réelles, claims, sélection JWKS, droits, isolation, suppression pendant SSE, cache privé, pagination, panne Ads et création concurrente d’un compte. La source de vérité de la validation fonctionnelle affichée est `frontend/src/data/radar-security-validation.json`, rendue dans `/tests#security`.

La suite backend complète donne **45 réussites et un échec** : `test_demo_mode.py::test_meta_ads_present`. Le même échec (Ads de démonstration vides) est reproduit sur le commit de départ `b559f58` avec 4 réussites et un échec. Cette dette de fixtures est suivie dans F03 ; la suite complète n’est pas annoncée verte.

La baseline initiale a échoué sur 11 des 12 premières régressions. Les nouvelles assertions étendent la couverture ; ce n’est pas une comparaison de temps de performance.

## Revue indépendante

AskClaude Opus 4.7, effort high : configuration `azp` désormais obligatoire ; tests de clé inconnue, fournisseur Ads indisponible et concurrence ajoutés. Les affectations de paramètres de test ont été normalisées. Le test webhook est explicitement nommé comme test du **stub historique** et vérifie son reçu `mode=stub` ; il ne prouve pas la vérification Stripe. Le retour checkout n’annonce une confirmation que si le niveau persisté correspond au niveau demandé.

Nous ne retenons pas les points purement cosmétiques comme failles bloquantes : la propriété est vérifiée avant le filtrage, et les transactions SSE sont volontairement courtes. Le plafond de connexions SSE et le message d’attente de paiement restent à traiter dans F05/R03.

La seconde revue AskClaude conclut ACCEPT après contrôle des correctifs, sans défaut bloquant dans ce périmètre. Les remarques restantes sont suivies comme dettes distinctes ; cet avis ne remplace pas les tests exécutés.

## Limites et tickets restants

- Clerk réel n’est pas configuré dans l’instance isolée ; le téléchargement réseau JWKS est simulé dans les tests, pas la cryptographie.
- Le cycle Stripe signé, l’idempotence et les renouvellements restent dans F02/R03. Aucun paiement réel ni remboursement n’est prouvé ici.
- Les tests de concurrence concernent SQLite. Un passage PostgreSQL demande sa propre validation.
- La collecte réelle et la vérité des scores relèvent de F03. L’API publique historique n’est pas réactivée par cette livraison.
