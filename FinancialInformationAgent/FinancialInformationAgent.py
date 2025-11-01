import json
import boto3
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

def analyze_company_with_claude(company_name):
    """
    Utilise Claude via Bedrock pour analyser une compagnie
    """
    
    prompt = f"""Tu es un analyste financier expert. Analyse l'entreprise {company_name} et fournis les informations suivantes au format JSON:

{{
  "overview": {{
    "region": "Région, Pays, Continent"
  }},
  "sector": {{
    "industry": "Industrie principale",
    "sector": "Secteur économique",
    "subsector": "Sous-secteur"
  }},
  "subsidiaries": ["Filiales principales si connues"],
  "suppliers": ["Fournisseurs clés si connus"],
}}

Fournis uniquement le JSON, sans texte additionnel."""

    try:
        # Appeler Claude via Bedrock
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.3,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        # Lire la réponse
        response_body = json.loads(response['body'].read())
        claude_response = response_body['content'][0]['text']
        
        # Extraire le JSON de la réponse
        start_idx = claude_response.find('{')
        end_idx = claude_response.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            analysis = json.loads(claude_response[start_idx:end_idx])
            return {
                'success': True,
                'analysis': analysis
            }
        else:
            return {
                'success': False,
                'error': 'Format de réponse invalide',
                'raw_response': claude_response
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def lambda_handler(event, context):
    """
    Handler principal de la Lambda
    """
    
    print("Event reçu:", json.dumps(event))
    
    try:
        # Extraire le nom de la compagnie
        if 'body' in event:
            body = json.loads(event['body'])
            company = body.get('company')
        else:
            company = event.get('company')
        
        if not company:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Paramètre "company" requis',
                    'example': {'company': 'Apple'}
                })
            }
        
        print(f"Analyse de la compagnie: {company}")
        
        # Analyser avec Claude
        analysis_result = analyze_company_with_claude(company)
        
        if analysis_result['success']:
            result = {
                'status': 'success',
                'company': company,
                'timestamp': datetime.now().isoformat(),
                'data': analysis_result['analysis'],
                'source': 'AWS Bedrock (Claude 3.5 Sonnet)'
            }
            status_code = 200
        else:
            result = {
                'status': 'error',
                'company': company,
                'error': analysis_result.get('error'),
                'details': analysis_result.get('raw_response')
            }
            status_code = 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e)
            })
        }
        
if __name__ == "__main__":
    print("\n🧪 Test local de l'agent Lambda\n")
    
    # Test simple
    event = {"company": "Microsoft"}
    result = lambda_handler(event, None)
    
    # Afficher le résultat
    print("="*80)
    print(result['body'])
    print("="*80)
    
    with open('result.json', 'w', encoding='utf-8') as f:
        f.write(result['body'])
    
    print("\n✅ Résultat sauvegardé dans result.json")