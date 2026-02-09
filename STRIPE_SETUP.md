# Stripe Setup Guide for ShortCut App

Ce guide vous explique comment configurer Stripe pour l'intégration des abonnements de l'application ShortCut selon le PRD F7.

## Configuration requise

Vous devez créer 4 produits dans Stripe Dashboard pour correspondre aux plans définis dans le PRD F7.

## Étapes de configuration

### 1. Accéder au Stripe Dashboard

1. Connectez-vous à [Stripe Dashboard](https://dashboard.stripe.com)
2. Sélectionnez votre projet ou créez-en un nouveau
3. Allez dans **Produits** > **Catalogue des produits**

### 2. Créer les produits et prix

#### Produit 1: Free Plan
- **Nom**: Free Plan
- **Description**: Plan gratuit avec fonctionnalités de base
- **Type**: Recurring (récurrent)
- **Prix**: 0,00 €
- **Fréquence**: Monthly (mensuel)
- **ID de prix à noter**: `price_free` (utilisé dans le code)

**Limites du plan Free**:
- 30 minutes d'upload par mois
- 5 clips par mois
- Durée max source: 10 minutes
- Plateforme: TikTok uniquement
- Styles sous-titres: clean, minimal
- Watermark: Oui
- Programmation: Non

#### Produit 2: Starter Plan
- **Nom**: Starter Plan
- **Description**: Plan débutant pour créateurs occasionnels
- **Type**: Recurring (récurrent)
- **Prix**: 9,99 €
- **Fréquence**: Monthly (mensuel)
- **ID de prix à noter**: `price_starter` (utilisé dans le code)

**Limites du plan Starter**:
- 120 minutes d'upload par mois (2 heures)
- 30 clips par mois
- Durée max source: 1 heure
- Plateformes: TikTok, YouTube
- Styles sous-titres: clean, minimal, hormozi, neon, karaoke
- Watermark: Non
- Programmation: Oui (max 5 posts/semaine)

#### Produit 3: Pro Plan
- **Nom**: Pro Plan
- **Description**: Plan professionnel pour créateurs actifs
- **Type**: Recurring (récurrent)
- **Prix**: 29,99 €
- **Fréquence**: Monthly (mensuel)
- **ID de prix à noter**: `price_pro` (utilisé dans le code)

**Limites du plan Pro**:
- 600 minutes d'upload par mois (10 heures)
- 150 clips par mois
- Durée max source: 4 heures
- Plateformes: TikTok, YouTube, Instagram
- Styles sous-titres: Tous disponibles
- Watermark: Non
- Programmation: Illimitée

#### Produit 4: Enterprise Plan
- **Nom**: Enterprise Plan
- **Description**: Plan entreprise avec toutes les fonctionnalités
- **Type**: Recurring (récurrent)
- **Prix**: 79,99 €
- **Fréquence**: Monthly (mensuel)
- **ID de prix à noter**: `price_enterprise` (utilisé dans le code)

**Limites du plan Enterprise**:
- Minutes d'upload: Illimitées
- Clips: Illimités
- Durée max source: Illimitée
- Plateformes: Toutes
- Styles sous-titres: Tous
- Watermark: Non
- Programmation: Illimitée

### 3. Configuration des Webhooks

1. Allez dans **Développeurs** > **Webhooks**
2. Cliquez sur **+ Ajouter un endpoint**
3. URL de l'endpoint: `https://your-domain.com/api/webhooks/stripe`
4. Sélectionnez les événements suivants:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

### 4. Variables d'environnement

Après avoir créé les produits, ajoutez ces variables dans votre fichier `.env`:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Product Price IDs
STRIPE_PRICE_FREE=price_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### 5. Mode Test vs Production

#### Mode Test
- Utilisez les clés qui commencent par `pk_test_` et `sk_test_`
- Les paiements ne sont pas réels
- Utilisez les [cartes de test Stripe](https://stripe.com/docs/testing#cards)

#### Mode Production
- Utilisez les clés qui commencent par `pk_live_` et `sk_live_`
- Vérifiez que tous les webhooks fonctionnent correctement
- Testez le flow complet de souscription

### 6. Validation

Pour valider votre configuration:

1. **Testez la création d'abonnement** pour chaque plan
2. **Vérifiez les webhooks** avec l'outil de test Stripe
3. **Testez les échecs de paiement** et la gestion de la grace period
4. **Validez les limites** de chaque plan dans l'application

### 7. Gestion des erreurs

L'application gère automatiquement:
- Les échecs de paiement avec grace period de 7 jours
- Les rétrogradations automatiques vers le plan Free
- Les webhooks en double (idempotence)
- Les tentatives de paiement multiples

### Support

En cas de problème:
1. Vérifiez les logs Stripe Dashboard
2. Consultez les webhooks dans Stripe
3. Vérifiez que les Price IDs correspondent dans l'application
4. Testez avec des cartes de test valides

## Maintenance

- Surveillez les métriques Stripe mensuellement
- Mettez à jour les prix si nécessaire via Stripe Dashboard
- Sauvegardez les Price IDs avant tout changement
- Testez les nouveaux webhooks en mode test avant production