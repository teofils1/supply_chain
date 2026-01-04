"""
Custom storage backend for MinIO with public URL rewriting.

This storage backend extends S3Boto3Storage to rewrite internal MinIO URLs
to use a public endpoint accessible from outside the Docker network.
"""

import os
from storages.backends.s3boto3 import S3Boto3Storage


class MinIOStorage(S3Boto3Storage):
    """
    Custom S3 storage backend for MinIO that rewrites URLs.
    
    Uses MINIO_ENDPOINT for internal file operations (upload/download within Docker)
    but rewrites generated URLs to use MINIO_PUBLIC_ENDPOINT for external access.
    """
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Override URL generation to replace internal endpoint with public endpoint.
        """
        # Get the original URL from the parent class
        url = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        
        # Get the public endpoint from environment
        internal_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", internal_endpoint)
        
        # Replace internal endpoint with public endpoint in the URL
        if internal_endpoint != public_endpoint and internal_endpoint in url:
            url = url.replace(internal_endpoint, public_endpoint)
        
        return url
