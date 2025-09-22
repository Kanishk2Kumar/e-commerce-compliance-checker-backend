import boto3
import json

REGION = "ap-south-1"
TABLE = "TextractProductImages"

client = boto3.client("dynamodb", region_name=REGION)
resp = client.describe_table(TableName=TABLE)
print(json.dumps({
    "TableName": resp["Table"]["TableName"],
    "KeySchema": resp["Table"]["KeySchema"],
    "AttributeDefinitions": resp["Table"]["AttributeDefinitions"],
    "TableStatus": resp["Table"]["TableStatus"],
    "Region": REGION
}, indent=2))
