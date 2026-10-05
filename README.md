# BubbleFlow

BubbleFlow is a full-stack inventory and production system for boba shops. I built it based on problems I noticed while working at a high-volume boba shop, especially the lack of communication between front-of-house orders and back-of-house production.

The main goal is to keep track of prepared ingredients, know what is currently being made, and help staff figure out when they need to make more.

## What it does

- Tracks prepared inventory like teas and tapioca
- Tracks batches as they are preparing, cooling, ready, or expired
- Uses FEFO (First Expired, First Out) so older batches are consumed first
- Records inventory changes through an event ledger instead of directly overwriting quantities
- Automatically updates inventory when orders are placed
- Warns when prepared items are running low
- Uses recent consumption to estimate future demand and recommend how much should be prepared
- Uses database transactions and row locking to prevent conflicting inventory updates

## Tech Stack

**Frontend:** React, TypeScript, Tailwind CSS, Vite

**Backend:** Django, Django REST Framework, PostgreSQL

## How it works

The React frontend communicates with the Django backend through a REST API. Django handles the business logic and uses the ORM to read and write data in PostgreSQL.

```text
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

One of the main parts of BubbleFlow is the inventory event system. Instead of storing a single inventory value and constantly replacing it, changes are recorded as events.

For example:

```text
Batch created       +4000 ml
Order consumption    -500 ml
Waste                -100 ml
Correction           +200 ml
```

The current inventory is calculated from those events.

When an order is placed, BubbleFlow figures out how much of each prepared item the order needs and consumes from batches using FEFO. Batches that expire sooner are used first. Inventory operations are wrapped in database transactions and use row locking so two operations cannot consume the same inventory at the same time.

## Production Forecasting

BubbleFlow also uses recent order consumption to estimate how quickly an item is being used. It uses that rate along with current inventory, batches already being prepared, and an inventory buffer to recommend whether more should be made.

## Project Structure

```text
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

The core inventory, batch, ordering, and forecasting systems are working. I'm currently working on testing, deployment, and general cleanup.

## Vercel Deployment

The repository deploys as one Vercel project with a Django backend service and a Vite frontend service. Keep the Vercel project Root Directory set to the repository root.

Connect a hosted PostgreSQL database to the project and expose its connection string as `DATABASE_URL`. Vercel Marketplace database integrations normally add this variable automatically. `DATABASE_URL` is used in production; the existing `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` variables remain supported. SQLite is used only when neither configuration is present so Django can build and run locally without production secrets.

Set `DJANGO_SECRET_KEY` to a long random value in the Vercel project environment. If it is absent, Django generates a temporary key so the build can complete, but a stable value is required before adding login sessions or other signed data.

When PostgreSQL configuration is present, the Vercel backend build automatically applies migrations and runs the idempotent `seed_demo` command. Builds without PostgreSQL skip these database steps.
