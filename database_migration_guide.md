# Database Migration Guide: PostgreSQL (Render) to TiDB (MySQL)

If Render's free PostgreSQL tier is exhausted and you need to switch to TiDB without losing any of your IDS data, telemetry, or user accounts, follow this step-by-step guide.

## Prerequisites

1. **Create a TiDB Serverless Cluster:**
   - Go to [TiDB Cloud](https://tidbcloud.com/) and create a free Serverless cluster.
   - Note down your connection details (Host, Port, User, Password).

2. **Ensure Dependencies are Installed:**
   `PyMySQL` is already added to `backend/requirements.txt` to support TiDB.

## Migration Steps

Since PostgreSQL and TiDB use slightly different SQL dialects, the safest and cleanest way to migrate data in Django is using its built-in JSON serialization (`dumpdata` and `loaddata`).

### Step 1: Export Data from Render (PostgreSQL)

While your application is still connected to the **Render PostgreSQL database**, dump all your data into a JSON file.

Run this command in your production environment (or locally while connected to the Render DB via environment variables):

```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 4 > datadump.json
```
*(Note: We exclude `contenttypes` and `auth.Permission` as they are recreated automatically and can cause conflicts during import.)*

### Step 2: Switch the Database Engine to TiDB

In your Render environment (or local `.env`), update the environment variables to point to your new TiDB database:

```env
DB_ENGINE=mysql
DB_NAME=your_tidb_db_name
DB_USER=your_tidb_user
DB_PASSWORD=your_tidb_password
DB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
DB_PORT=4000
```

Because of our dynamic `settings.py` configuration, setting `DB_ENGINE=mysql` will automatically load `pymysql` and configure Django to use the MySQL backend for TiDB.

### Step 3: Run Migrations on TiDB

Before importing the data, you need to create the database schema in TiDB.

```bash
python manage.py migrate
```

### Step 4: Import the Data

Load the JSON data into your new TiDB database:

```bash
python manage.py loaddata datadump.json
```

### Step 5: Verify

Start your Django server and verify that all users, telemetry, and forensic data are fully intact. 

```bash
python manage.py runserver
```

You are now successfully running on TiDB for free, forever!
