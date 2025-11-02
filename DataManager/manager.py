import json
import boto3
from botocore.exceptions import ClientError

class S3Storage:
    def __init__(self, bucket_name, region_name="us-east-1"):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3 = boto3.client("s3", region_name=self.region_name)
        self.ensure_bucket_exists()

    def ensure_bucket_exists(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3.create_bucket(Bucket=self.bucket_name)
            print(f"Bucket {self.bucket_name} created")

    def save_json(self, key, data):
        json_data = json.dumps(data)
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=json_data, ContentType="application/json")
        print(f"Saved to {self.bucket_name}/{key}")

    def load_json(self, key):
        response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)

    def delete_json(self, key):
        self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        print(f"Deleted {self.bucket_name}/{key}")


