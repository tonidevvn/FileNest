# FileNest Project Setup Guide

## Prerequisites

Ensure you have the following installed on your machine:

Python 3.13 or later

Git (for version control)

Virtual Environment (venv)

Docker


## Project Features


| **Status**  | **Feature Description** |
|-------------| ------- |
| ✅ Done     | File chunking mechanism for handling large files efficiently   |
| ✅ Done     | APIs for file upload, chunk distribution, and retrieval   |
| ✅ Done     | Distributed storage system integration using MinIO   |
| ✅ Done     | File replication for redundancy and data integrity   |
| ✅ Done     | Error detection mechanisms such as checksums for file verification   |
| 🔜  Ongoing | Recovery mechanisms for handling failures or corrupted chunks  |
| ✅ Done     | Retrieval logic to fetch files from the nearest or least-loaded node  |
| ✅ Done     | Caching strategies for frequently accessed files to improve performance  |
| ✅ Done     | User-friendly interface for file uploads and downloads  |
| 🔜  Ongoing | Admin panel to monitor file distribution and node statuses  |
| 🔜  Ongoing | Logging and reporting functionalities to track file access and storage operations  |
| ✅ Done     | Secure authentication and authorization using API tokens  |


## Retrieval Optimization Features

FileNest now includes sophisticated retrieval optimization capabilities:

### Intelligent File Retrieval
- **Geo-Aware Node Selection**: Files are retrieved from the nearest storage node based on the user's location
- **Load-Based Optimization**: When geographic data isn't available, the system automatically selects the least loaded node
- **Performance Tracking**: Each node's performance is continuously monitored to improve future retrieval decisions
- **Automatic Failover**: If a preferred node fails, the system seamlessly falls back to alternative nodes

### File Caching System
- **Efficient Caching**: Frequently accessed files are cached to reduce latency and server load
- **Smart Cache Management**: Files are cached based on size and access patterns
- **Cache Control**: API supports optional cache bypass with the `no_cache` parameter
- **Automatic Cache Invalidation**: Cache entries are automatically cleared when files are modified or deleted

### API Enhancements
- **Location-Aware Downloads**: Clients can provide their geographic coordinates for optimal node selection
- `/api/download/<file_id>/?lat=<latitude>&lon=<longitude>` - Downloads file from the nearest node
- `/api/download/<file_id>/?no_cache=1` - Forces a fresh download bypassing the cache

### Clone the Repository
[Repository link](https://github.com/tonidevvn/FileNest)
```
git clone [Repository link]
cd FileNest
```

## Deploying Multiple MinIO Nodes
For distributed storage testing, you can use Docker Compose to run multiple MinIO nodes:

```
docker-compose up -d
```

The included docker-compose.yml configures multiple nodes with different geographical locations.

### Start MinIO (Single Node)
```
docker run -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=admin" -e "MINIO_ROOT_PASSWORD=minioadmin" minio/minio server /data --console-address ":9001"
```

Verify MinIO is Running\
Open a browser and go to http://localhost:9001 (or your server IP if remote).\
Log in with the credentials (admin/minioadmin for the Docker example).\
You should see the MinIO web interface.


### Create and Activate Virtual Environment

```
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate    # On Windows
```

### Install Dependencies

```
pip install --upgrade pip
pip install -r requirements.txt
```

### Create a Superuser (For Admin Panel - Optional)

Follow the prompts to set up the admin account.
```
python manage.py createsuperuser
```

### Start the Development Server

Follow the prompts to access the app at: http://127.0.0.1:8000/
```
python manage.py runserver
```

