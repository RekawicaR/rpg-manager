# RPG Campaign Manager API

A Django REST API for managing tabletop RPG campaigns, campaign membership, invites, source restrictions, and a spell compendium.

## Features

- JWT authentication with register, login, and refresh endpoints
- Campaign CRUD with DM and Player roles
- Invite-based campaign joining with expiring links
- Campaign source allow-list management
- Campaign item rules for compendium entries
- Public spell read endpoints with moderator-only write access
- PostgreSQL-backed Django project
- API tests for campaigns and spells

## Run locally

1. Clone the repository:
   ```bash
   git clone https://github.com/RekawicaR/rpg-manager.git
   cd rpg-manager
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set up environment variables in .env file (example):
   ```
   SECRET_KEY=dev-secret-key
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   POSTGRES_DB=rpg_campaign_manager
   POSTGRES_USER=rpg_user
   POSTGRES_PASSWORD=rpg_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```
4. Run migrations: (this assumes the postgres database is already configured)
   ```
   python manage.py migrate
   ```
5. Run the server:
   ```
   python manage.py runserver
   ```

---

## API Endpoints

### Core

| Method | Endpoint     | Description        |
| ------ | ------------ | ------------------ |
| GET    | /api/health/ | Returns API status |


### Auth

| Method | Endpoint            | Description                          |
| ------ | ------------------- | ------------------------------------ |
| POST   | /api/auth/register/ | Register a new user                  |
| POST   | /api/auth/login/    | Login, receive JWT tokens            |
| POST   | /api/auth/refresh/  | Refresh access token                 |

### Campaigns

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/campaigns/` | List campaigns the current user belongs to |
| POST | `/api/campaigns/` | Create a campaign and become its DM |
| GET | `/api/campaigns/{id}/` | Retrieve campaign details |
| PATCH | `/api/campaigns/{id}/` | Update a campaign, DM only |
| DELETE | `/api/campaigns/{id}/` | Delete a campaign, DM only |
| POST | `/api/campaigns/{campaign_id}/invite/` | Create an invite link, DM only |
| POST | `/api/campaigns/invites/{token}/accept/` | Accept an invite |
| GET | `/api/campaigns/{campaign_id}/sources/` | List enabled sources for a campaign |
| PUT | `/api/campaigns/{campaign_id}/sources/` | Replace enabled sources, DM only |
| GET | `/api/campaigns/{campaign_id}/rules/` | List campaign item rules |
| POST | `/api/campaigns/{campaign_id}/rules/` | Create or update a rule, DM only |
| DELETE | `/api/campaigns/{campaign_id}/rules/{rule_id}/` | Delete a rule, DM only |

### Spells

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/spells/` | Public spell list |
| GET | `/api/spells/{id}/` | Public spell detail |
| POST | `/api/spells/` | Create a spell, moderator only |
| PATCH | `/api/spells/{id}/` | Update a spell, moderator only |
| DELETE | `/api/spells/{id}/` | Delete a spell, moderator only |

## Domain rules

### Campaign membership

- The campaign creator becomes the `DM`
- Other users join as `PLAYER`
- Membership is stored in `CampaignMembership`
- A user can belong to many campaigns, but only once per campaign

### Campaign invites

- Invites are created by a DM
- Each invite uses a UUID token
- Invites expire after 7 days
- Invite acceptance is idempotent:
  First use returns `201` with `joined=true`
  Repeated use by the same user returns `200` with `joined=false`

### Campaign sources

- Each campaign can enable a subset of compendium sources
- Members can read enabled sources
- Only the DM can replace the source list
- Sending an empty list clears all enabled sources

### Spell validation

- Spell validation rules are shared between the model and serializer
- API validation covers casting, duration, range, area, and concentration consistency
- Spell list and detail are public
- Spell write operations are restricted to moderators

## Tests

Run tests with:
```bash
python manage.py test apps/
```
Tests currently cover:
- Health check endpoint
- User authentication (register, login, refresh)
- Campaign creation
- DM role assignment
- Invite creation
- Joining campaign via invite
- Idempotent invite usage
- Expired invite
- Campaign GET, PATCH, DELETE with DM permissions
- CampaignSource GET and PUT (DM update, member view, non-member forbidden)
- Spell CRUD and permissions

---

## Tech Stack
- Django
- Django REST Framework
- PostgreSQL
- JWT (SimpleJWT)
