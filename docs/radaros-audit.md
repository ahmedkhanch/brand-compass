# Reprise RadarOS V2 — 12 septembre 2026

Le brief `Brief RadarOS.docx` (texte et visuel embarqué) est comparé au code Brand Compass `develop` au commit `324c554`. La matrice distingue le socle réutilisable, les besoins manquants, les critères d’acceptation et les preuves dans le code. Aucun chapitre V2 n’est déclaré validé de bout en bout.

- [Page de suivi](https://brandcompass-develop.oratelecom.net/wip)
- [Validation fonctionnelle](https://brandcompass-develop.oratelecom.net/tests)
- [Board privé Forgejo](https://git.oratelecom.net/ora/brandcompass-roadmap/projects/1) : 30 besoins et 5 fondations, dont 10 P0.
- [Code canonique GitHub](https://github.com/ahmedkhanch/brand-compass)

## Sources de vérité

`frontend/src/data/radar-audit.json` porte le constat daté, les 30 exigences, les cinq fondations, leurs tickets et la synthèse critique des deux relectures AskClaude en effort high. La page et son export Markdown consomment cette même matrice. Les tickets sont la source de vérité de l’avancement après l’audit : déplacer une carte ne transforme pas automatiquement le constat historique en capacité validée.

`frontend/src/data/radar-validation.json` porte les preuves de livraison du suivi. La route `/tests` en présente les contrôles sans créer de second catalogue API. Swagger `/docs` reste le catalogue canonique du backend, qui n’est pas réactivé par cette livraison.

Le composant `AuditShell` porte la navigation, `AuditExplorer` la consultation interactive, `radar-audit-export.ts` l’export et le CSS module la présentation. Aucune persistance ni route API n’est ajoutée. Aucun secret n’est publié dans la matrice, les tickets ou les pages.

## Déploiement de développement

Les anciens services API et frontend étaient arrêtés au début de l’audit. La livraison relance uniquement le frontend de suivi. Le backend historique accepte des identités de démo hors démo, possède un upgrade direct et n’applique pas le filtre propriétaire au SSE ; sa remise en service dépend de F01/F02. Les quatre clés fournisseurs présentes n’ont pas été exercées et ne sont pas une preuve de disponibilité des collecteurs.

Depuis le checkout de livraison sur Ora :

```sh
docker compose -f docker-compose.audit.yml build frontend
docker compose -f docker-compose.audit.yml up -d frontend
```

Caddy conserve la protection Basic Auth existante. Le port 4300 écoute seulement sur la passerelle Docker `172.17.0.1` utilisée par `host.docker.internal` dans Caddy, pas sur l’interface publique. L’image n’inclut ni `.env` ni accès fournisseurs. Le build utilise le shim frontend de développement pour afficher les pages de suivi ; cela ne constitue pas une authentification SaaS.

Retour arrière : arrêter le service de ce compose ou reconstruire le frontend depuis le commit précédent. L’état précédent du chantier était arrêté ; ne pas redémarrer le backend avec le compose de démonstration pour annuler une modification de page. Les données backend existantes ne sont pas modifiées.

## Vérification

Dans `frontend`, lancer `npm ci`, puis `NEXT_PUBLIC_DEMO_MODE=1 npm run build` et ESLint sur les fichiers touchés. Le build peut signaler la convention historique `middleware.ts` dépréciée ; ce chantier ne la migre pas.

Le script `tests/e2e/audit.mjs` teste la couverture, la recherche, les filtres combinés, la remise à zéro, les détails au clavier, l’export complet et l’absence de débordement en desktop/mobile. Utiliser une installation Playwright disponible via `PLAYWRIGHT_MODULE`, ou installer Playwright dans l’environnement de validation. `BROWSER_EXECUTABLE` permet d’employer un navigateur local.

```sh
AUDIT_BASE_URL=http://127.0.0.1:4350 node tests/e2e/audit.mjs
```

Pour le site protégé, transmettre `AUDIT_USER` et `AUDIT_PASSWORD` depuis un environnement privé, jamais dans une commande versionnée. `AUDIT_ARTIFACTS` définit le dossier de preuves (par défaut `/tmp/radaros-audit-checks`). Les tests du suivi ne valident pas les anciennes analyses de démonstration, le paiement ou les futurs collecteurs V2.
