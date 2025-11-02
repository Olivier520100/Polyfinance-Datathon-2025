import json
import boto3
from datetime import datetime
import pandas as pd
from collections import Counter
import time

bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

# Les 11 secteurs GICS du marché boursier
GICS_SECTORS = {
    "Information Technology": {
        "weight": 30.0,
        "description": "Entreprises développant des logiciels, matériels, semi-conducteurs, etc."
    },
    "Health Care": {
        "weight": 12.5,
        "description": "Sociétés pharmaceutiques, biotechnologies, équipements médicaux, hôpitaux, etc."
    },
    "Financials": {
        "weight": 13.0,
        "description": "Banques, compagnies d’assurance, sociétés de gestion d’actifs, etc."
    },
    "Consumer Discretionary": {
        "weight": 10.6,
        "description": "Biens et services non essentiels : automobile, luxe, commerce, divertissement..."
    },
    "Communication Services": {
        "weight": 9.0,
        "description": "Télécommunications, médias, plateformes en ligne, réseaux sociaux..."
    },
    "Industrials": {
        "weight": 8.0,
        "description": "Manufacture, transport, ingénierie, aérospatial, logistique..."
    },
    "Consumer Staples": {
        "weight": 6.0,
        "description": "Produits de base : alimentation, boissons, produits ménagers, etc."
    },
    "Energy": {
        "weight": 4.0,
        "description": "Extraction, raffinage, distribution et services liés au pétrole et au gaz."
    },
    "Utilities": {
        "weight": 2.5,
        "description": "Fournisseurs d’électricité, eau, gaz, énergie renouvelable."
    },
    "Real Estate": {
        "weight": 2.5,
        "description": "Fonds immobiliers (REITs), gestion de propriétés, promoteurs."
    },
    "Materials": {
        "weight": 2.0,
        "description": "Extraction et transformation de ressources naturelles, chimie, métaux..."
    }
}

def analyze_company_with_claude(company_name):
    """
    Utilise Claude via Bedrock pour analyser une compagnie et identifier son secteur GICS
    """
    
    sectors_list = "\n".join([f"- {sector}" for sector in GICS_SECTORS])
    
    prompt = f"""Tu es un analyste financier expert. Analyse l'entreprise {company_name} et fournis les informations suivantes au format JSON.

IMPORTANT: Le secteur doit être UN SEUL des 11 secteurs GICS suivants (choisis le plus approprié):
{sectors_list}

Format de réponse (JSON uniquement):
{{
  "company_name": "{company_name}",
  "gics_sector": "Le secteur GICS principal parmi les 11 ci-dessus",
  "industry": "Industrie spécifique",
  "description": "Brève description de l'activité principale",
  "subsidiaries": ["Filiales principales si connues"],
  "suppliers": ["Fournisseurs clés si connus"],
  "marketCap": "Capitalisation Boursière du titre en date du 15 aout 2025 en format décimal base 10" 
}}

Fournis uniquement le JSON, sans texte additionnel. Le champ gics_sector doit être EXACTEMENT un des 11 secteurs listés ci-dessus."""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        claude_response = response_body['content'][0]['text']
        
        start_idx = claude_response.find('{')
        end_idx = claude_response.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            analysis = json.loads(claude_response[start_idx:end_idx])
            
            # Normaliser le secteur pour matcher les 11 secteurs GICS
            sector = analysis.get('gics_sector', 'Unknown')
            
            # Vérifier si le secteur est valide
            if sector not in GICS_SECTORS:
                for gics_sector in GICS_SECTORS:
                    if gics_sector.lower() in sector.lower() or sector.lower() in gics_sector.lower():
                        sector = gics_sector
                        break
                else:
                    sector = 'Unclassified'
            
            analysis['gics_sector'] = sector

            market_cap = analysis.get('marketCap', 'N/A')
            if isinstance(market_cap, str):
                market_cap = market_cap.replace('$', '').replace(',', '').strip()
                analysis['marketCap'] = market_cap

            subsidiaries = analysis.get('subsidiaries', [])
            suppliers = analysis.get('suppliers', [])

            if isinstance(subsidiaries, str):
                subsidiaries = [s.strip() for s in subsidiaries.split(',') if s.strip()]

            if isinstance(suppliers, str):
                suppliers = [s.strip() for s in suppliers.split(',') if s.strip()]

            analysis['subsidiaries'] = subsidiaries
            analysis['suppliers'] = suppliers
            
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
        
        analysis_result = analyze_company_with_claude(company)
        
        if analysis_result['success']:
            result = {
                'status': 'success',
                'company': company,
                'timestamp': datetime.now().isoformat(),
                'data': analysis_result['analysis'],
                'source': 'AWS Bedrock (Claude 3 Haiku)'
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


# ============================================================================
# FONCTION 1 : ANALYSE DÉTAILLÉE (votre ancien code amélioré)
# ============================================================================

def analyze_sp500_detailed(excel_file, company_column='Company', max_companies=None):
    """
    Analyse complète et détaillée de toutes les compagnies du S&P 500
    Génère des fichiers JSON et Excel avec toutes les informations
    
    Args:
        excel_file: Chemin vers le fichier Excel
        company_column: Nom de la colonne contenant les noms de compagnies
        max_companies: Nombre maximum de compagnies à analyser (None = toutes)
    
    Returns:
        dict: Dictionnaire complet avec toutes les analyses
    """
    
    print("\n" + "="*80)
    print("📊 FONCTION 1: ANALYSE DÉTAILLÉE DU S&P 500")
    print("="*80 + "\n")
    
    # Lire le fichier CSV
    try:
        df = pd.read_csv(excel_file)
        print(f"✅ Fichier CSV chargé: {len(df)} compagnies trouvées\n")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return None
    
    # Vérifier que la colonne existe
    if company_column not in df.columns:
        print(f"❌ Colonne '{company_column}' non trouvée. Colonnes: {df.columns.tolist()}")
        return None
    
    # Limiter le nombre de compagnies si spécifié
    if max_companies:
        df = df.head(max_companies)
        print(f"📊 Analyse limitée aux {max_companies} premières compagnies\n")
    
    companies = df[company_column].tolist()
    total_companies = len(companies)
    
    results = []
    sector_counts = Counter()
    errors = []
    
    print(f"🚀 Début de l'analyse de {total_companies} compagnies...\n")
    print("-"*80)
    
    for idx, company in enumerate(companies, 1):
        company = str(company).strip()
        
        print(f"[{idx}/{total_companies}] Analyse de: {company}...", end=" ")
        
        try:
            event = {"company": company}
            result = lambda_handler(event, None)
            result_body = json.loads(result['body'])
            
            if result_body['status'] == 'success':
                sector = result_body['data']['gics_sector']
                industry = result_body['data'].get('industry', 'N/A')
                description = result_body['data'].get('description', 'N/A')
                market_cap = result_body['data'].get('marketCap', 'N/A')
                subsidiaries = result_body['data'].get('subsidiaries', [])
                suppliers = result_body['data'].get('suppliers', [])

                
                results.append({
                    'company': company,
                    'gics_sector': sector,
                    'industry': industry,
                    'marketCap': market_cap,  
                    'description': description,
                    'subsidiaries' : subsidiaries,
                    'suppliers' : suppliers
                })
                
                sector_counts[sector] += 1
                print(f"✅ {sector}")
                
            else:
                error_msg = result_body.get('error', 'Erreur inconnue')
                errors.append({'company': company, 'error': error_msg})
                print(f"❌ Erreur: {error_msg}")
            
            if idx < total_companies:
                time.sleep(0.5)
                
        except Exception as e:
            errors.append({'company': company, 'error': str(e)})
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "="*80)
    print("📊 RÉSULTATS DE L'ANALYSE DÉTAILLÉE")
    print("="*80 + "\n")
    
    total_analyzed = len(results)
    
    print(f"Total de compagnies analysées: {total_analyzed}/{total_companies}")
    print(f"Erreurs: {len(errors)}\n")
    
    if total_analyzed > 0:
        print("-"*80)
        print("PONDÉRATION DES SECTEURS GICS")
        print("-"*80)
        
        sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Préparer la sortie complète
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_companies': total_companies,
                'analyzed': total_analyzed,
                'errors': len(errors)
            },
            'company_details': results,
            'errors': errors
        }
        
        # Sauvegarder en JSON
        with open('sp500_detailed_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Analyse détaillée sauvegardée dans: sp500_detailed_analysis.json")
        
        return output
    
    else:
        print("❌ Aucune compagnie n'a pu être analysée")
        return None

# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              ANALYSE SECTORIELLE DU S&P 500 - 2 FONCTIONS                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    EXCEL_FILE = "2025-08-15_composition_sp500.csv"  # Changez avec le nom exact de votre fichier CSV
    COMPANY_COLUMN = "Company"  # Changez avec le nom exact de votre colonne
    MAX_COMPANIES = 500  # Testez avec 10, puis None pour tout
    
    print("\CLiquez sur 1 pour lancer l'analyse\n")
    
    choice = input("Votre choix (1): ").strip()
    
    if choice == "1":
        print("\n🔍 Lancement de l'analyse détaillée...")
        detailed_results = analyze_sp500_detailed(
            excel_file=EXCEL_FILE,
            company_column=COMPANY_COLUMN,
            max_companies=MAX_COMPANIES
        )
    else:
        print("\n❌ Choix invalide")
    
    print("\n✨ Terminé!\n")