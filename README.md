# BubbleFlow

**[Live Demo](https://bubbleflow-v2.vercel.app)**

BubbleFlow is a full-stack inventory and production system for boba shops. I built it from my experience as a shift lead at a high-volume boba shop, where front-of-house orders and back-of-house batch prep had no real way to talk to each other. BubbleFlow links the two so staff always know what's prepared, what's being made, and when to make more.

## What it does

- Tracks prepared inventory like teas and tapioca, batch by batch
- Tracks each batch through its lifecycle: preparing, cooling, ready, or expired
- Consumes the earliest-expiring batch first (FEFO: First Expired, First Out)
- Records every inventory change as an event in an append-only ledger instead of overwriting quantities
- Automatically updates inventory when orders are placed
- Warns when prepared items are running low
- Recommends how much to prepare using time-of-day sales history, current stock, incoming batches, and configurable safety buffers

## Tech Stack

**Frontend:** React, TypeScript, Tailwind CSS, Vite

**Backend:** Python, Django, Django REST Framework

**Database:** PostgreSQL

**Deployment:** Vercel

## Key Design Decisions

### Append-only inventory ledger

Instead of storing one inventory number and constantly replacing it, every change is an event. Batch balances are derived from production, consumption, waste, correction, and expiration events, which keeps a full audit trail of where every milliliter went.

```
Batch created       +4000 ml
Order consumption    -500 ml
Waste                -100 ml
Correction           +200 ml
```

### Preventing overselling with row-level locks

Order consumption runs inside database transactions and uses PostgreSQL row-level locks, so two orders can never consume the same inventory at the same time.

In a stress test, **200 concurrent orders competed for 100 servings, and exactly 100 succeeded.** Each order consumes from the earliest-expiring batch first (FEFO).

### Demand-aware production recommendations

The recommendation engine combines time-of-day sales history, current stock, batches already being prepared, and configurable safety buffers to suggest whether more should be made and how much.

## How it works

```
React
  ↓
Django REST API
  ↓
Services
  ↓
Django ORM
  ↓
PostgreSQL
```

The React frontend talks to the Django backend through a REST API. Django handles the business logic in a services layer and uses the ORM to read and write PostgreSQL.

## Project Structure

```
backend/
  operations/
    models.py
    serializers.py
    views.py
    services/
      inventory.py
      orders.py
      forecasting.py

frontend/
  src/
    components/
    pages/
    App.tsx
    main.tsx
```

## Status

Deployed and working: inventory ledger, batch tracking, FEFO ordering, concurrency-safe order handling, and the production recommendation engine.

## Vercel Deployment

The repository deploys as one Vercel project with a Django backend service and a Vite frontend service. Keep the Vercel project Root Directory set to the repository root.

Connect a hosted PostgreSQL database and expose its connection string as `DATABASE_URL`. Vercel Marketplace database integrations normally add this automatically. The existing `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` variables remain supported. SQLite is only used when neither configuration is present, so Django can build and run locally without production secrets.

Set `DJANGO_SECRET_KEY` to a long random value in the Vercel project environment. If it's missing, Django generates a temporary key so the build can finish, but a stable value is required before adding login sessions or other signed data.

When PostgreSQL configuration is present, the Vercel backend build automatically applies migrations and runs the idempotent `seed_demo` command. Builds without PostgreSQL skip these database steps.
