import json
import boto3
import re
from datetime import datetime
from urllib.parse import unquote_plus
from decimal import Decimal

# Initialize AWS clients
s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

# Tables
table_name = 'TextractProductImages'
table = dynamodb.Table(table_name)
summary_table = dynamodb.Table('ProductComplianceSummary')

def extract_product_id_from_key(s3_key):
    try:
        match = re.match(r'product-images/(\d+)/image_(\d+)\.jpg', s3_key)
        if match:
            return match.group(1), int(match.group(2))
        return None, None
    except Exception as e:
        print(f"Error extracting product ID from key {s3_key}: {e}")
        return None, None

def check_product_flags(product_id):
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('ProductID').eq(str(product_id))
    )
    items = response.get('Items', [])
    
    combined_text = " ".join([i.get("ExtractedText", "") for i in items]).lower()
    
    flags = {
        "HasNutritionalInfo": False,
        "HasFSSAI": False,
        "FSSAICodes": [],
        "HasManufacturerDetails": False,
        "IsCompliant": False,
        "HasConsumerCareDetails": False
    }

    # Nutritional info
    if any(keyword in combined_text for keyword in [
        "nutritional information", "serving size", "energy", "kcal", "protein"
    ]):
        flags["HasNutritionalInfo"] = True

    # FSSAI detection: allow line breaks, "Lic No", multiple codes
    fssai_matches = re.findall(
        r"(?:fssai[\s:\-]*|lic\.?\s*no\.?\s*)(\d{10,16})",
        combined_text,
        re.IGNORECASE | re.DOTALL
    )
    if fssai_matches:
        flags["HasFSSAI"] = True
        flags["FSSAICodes"] = list(set(fssai_matches))  # unique codes

    # Manufacturer details
    if any(keyword in combined_text for keyword in [
        "manufactured by", "mfg. by", "marketed by", "imported by", "address"
    ]):
        flags["HasManufacturerDetails"] = True

    # Consumer care details (phone or email)
    phone_matches = re.findall(r'\b\d{10}\b', combined_text)  # simple 10-digit phone
    email_matches = re.findall(r'[\w\.-]+@[\w\.-]+', combined_text)
    if phone_matches or email_matches or "consumer care" in combined_text or "contact" in combined_text:
        flags["HasConsumerCareDetails"] = True

    # Overall compliance: FSSAI, nutrition, manufacturer, consumer care
    if all([flags["HasNutritionalInfo"], flags["HasFSSAI"], flags["HasManufacturerDetails"], flags["HasConsumerCareDetails"]]):
        flags["IsCompliant"] = True

    # Save compliance summary
    summary_table.put_item(
        Item={
            "ProductID": str(product_id),
            "Flags": flags,
            "LastChecked": datetime.utcnow().isoformat()
        }
    )

    print(f"📊 Compliance flags for Product {product_id}: {flags}")
    return flags

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = unquote_plus(record['s3']['object']['key'])
            
            print(f"Processing file: {object_key} from bucket: {bucket_name}")
            
            product_id, image_index = extract_product_id_from_key(object_key)
            if not product_id or not image_index:
                print(f"Skipping file {object_key} - doesn't match expected pattern")
                continue
            
            # Check if image already processed
            try:
                response = table.get_item(
                    Key={'ProductID': product_id, 'ImageIndex': str(image_index)}
                )
                if 'Item' in response:
                    print(f"Image already processed: {product_id}/image_{image_index}")
                    continue
            except Exception as e:
                print(f"Error checking existing record: {e}")
            
            # Textract call
            response = textract.detect_document_text(
                Document={'S3Object': {'Bucket': bucket_name, 'Name': object_key}}
            )
            
            extracted_text = ""
            confidence_scores = []
            for item in response['Blocks']:
                if item['BlockType'] == 'LINE':
                    extracted_text += item['Text'] + '\n'
                    if 'Confidence' in item:
                        confidence_scores.append(item['Confidence'])
            
            avg_confidence = (
                Decimal(str(sum(confidence_scores) / len(confidence_scores)))
                if confidence_scores else Decimal("0")
            )
            
            db_item = {
                'ProductID': str(product_id),
                'ImageIndex': str(image_index),
                'S3Bucket': bucket_name,
                'S3Key': object_key,
                'ExtractedText': extracted_text.strip(),
                'AverageConfidence': avg_confidence,
                'ProcessedTimestamp': datetime.utcnow().isoformat(),
                'TextractJobId': response.get('JobId', 'SYNC_PROCESSING'),
                'TotalLines': Decimal(str(len([b for b in response['Blocks'] if b['BlockType'] == 'LINE']))),
                'TotalWords': Decimal(str(len([b for b in response['Blocks'] if b['BlockType'] == 'WORD'])))
            }
            
            table.put_item(Item=db_item)
            print(f"✅ Stored product {product_id}, image {image_index} in DynamoDB")
            
            check_product_flags(product_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Text extraction + compliance check completed successfully',
                'processedRecords': len(event['Records'])
            })
        }
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing document: {str(e)}')
        }
