# RPG Campaign Manager API

A Django REST API project for managing Dungeons & Dragons campaigns.  
This is the initial setup including project structure, a health check endpoint, PostgreSQL database configuration,
and JWT authentication.


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


## Tests

Run tests with:
```bash
python manage.py test apps/
```
Tests currently cover:
- Health check endpoint
- User registration
- JWT login and token refresh