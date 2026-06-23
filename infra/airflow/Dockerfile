FROM apache/airflow:3.1.1-python3.10

# Install Airflow providers from requirements.txt. Adding more providers
# later (S3, HTTP, etc.) means editing requirements.txt and rebuilding —
# no changes needed here.
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
