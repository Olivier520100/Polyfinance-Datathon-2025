import os
import json
import pandas as pd
import openai
from tavily import TavilyClient
from sec_downloader import Downloader
from markitdown import MarkItDown
from bs4 import BeautifulSoup
import copy
from pathlib import Path
from dotenv import load_dotenv
import statistics
import time
import traceback
import re

load_dotenv()

# ===== CONFIGURATION =====

client = openai.OpenAI(api_key=BEDROCK_API_KEY, base_url=BEDROCK_ENDPOINT)
tavily_client = TavilyClient(TAVILY_API_KEY)
md = MarkItDown(enable_plugins=False)


# ===== STEP 1: SEC FILING ANALYSIS =====


def analyze_sec_filing(ticker):
    """Extract risk metrics from SEC 10-K with EXACT citations - AI ONLY for extraction"""
    print(f"\n{'=' * 70}")
    print(f"[STEP 1] 📄 SEC FILING ANALYSIS: {ticker}")
    print(f"{'=' * 70}")

    try:
        dl = Downloader("Company", "email@example.com")
        html = dl.get_filing_html(ticker=ticker, form="10-K")

        soup = BeautifulSoup(html, "html.parser")

        # Extract tables
        table_list = []
        i = 1
        for table in soup.find_all("table"):
            table_list.append({"index": i, "html": str(copy.deepcopy(table))})
            table.replace_with(f"TABLE_PLACEHOLDER_{i}")
            i += 1

        # Remove hidden
        for div in soup.find_all("div", {"style": "display:none"}):
            div.decompose()

        # Convert to markdown
        with open("temp_filing.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())

        result = md.convert("temp_filing.html")

        with open("temp_filing.md", "w", encoding="utf-8") as f:
            f.write(result.text_content)

        with open("temp_filing.md", "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f]

        verified_metrics = []
        chunk_size = 100

        # AI ONLY extracts - we verify
        for idx in range(0, len(lines), chunk_size):
            chunk = lines[idx : idx + chunk_size]
            chunk_text = "\n".join(chunk)

            if not chunk_text.strip():
                continue

            try:
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": """Extract QUANTITATIVE metrics with EXACT quotes ONLY.
                            Output: {
                                "metrics": [{
                                    "type": "supplier_concentration/geographic/customer/financial",
                                    "value": number,
                                    "unit": "percent/million/etc",
                                    "exact_quote": "COPY VERBATIM from text"
                                }]
                            }""",
                        },
                        {"role": "user", "content": chunk_text},
                    ],
                    temperature=0.05,
                    max_tokens=600,
                )

                result = json.loads(response.choices[0].message.content)
                for metric in result.get("metrics", []):
                    exact_quote = metric.get("exact_quote", "")
                    # VERIFY quote exists
                    if exact_quote and exact_quote in chunk_text:
                        verified_metrics.append(metric)
                        print(
                            f"✅ {metric.get('type')}: {metric.get('value')} {metric.get('unit', '')}"
                        )

            except Exception as e:
                continue

        # Cleanup
        for temp_file in ["temp_filing.html", "temp_filing.md"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print(f"\n✅ SEC: {len(verified_metrics)} verified metrics")
        return verified_metrics

    except Exception as e:
        print(f"❌ SEC Error: {e}")
        return []


# ===== STEP 2: SUPPLIER ANALYSIS =====


def analyze_suppliers(company_name):
    """Get suppliers - AI ONLY for extraction"""
    print(f"\n{'=' * 70}")
    print(f"[STEP 2] 🔗 SUPPLIER ANALYSIS: {company_name}")
    print(f"{'=' * 70}")

    try:
        response = tavily_client.search(
            query=f"{company_name} suppliers manufacturers contractors partners COMPANY NAMES",
            include_answer="advanced",
        )

        info = response.get("answer", "")

        # AI ONLY extracts structured data
        llm_response = client.chat.completions.create(
            model=MODEL_ID,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """Extract suppliers ONLY if explicitly mentioned:
                    {
                        "suppliers": [{
                            "name": "Exact Company Name",
                            "country": "Country",
                            "criticality": "high/medium/low"
                        }]
                    }""",
                },
                {
                    "role": "user",
                    "content": f"Extract suppliers for {company_name}:\n\n{info}",
                },
            ],
            temperature=0.05,
        )

        result = json.loads(llm_response.choices[0].message.content)
        suppliers = result.get("suppliers", [])

        print(f"✅ Found {len(suppliers)} suppliers")
        for s in suppliers[:5]:
            print(f"   - {s.get('name')} ({s.get('country')})")

        return suppliers

    except Exception as e:
        print(f"❌ Supplier Error: {e}")
        return []


# ===== STEP 3: BILL ANALYSIS - FIXED TO AVOID VAGUE IMPACTS =====


def analyze_bills(company_name, sector, industry, suppliers, bills_folder="bills"):
    """Analyze bills with STRICT direct impact requirements"""
    print(f"\n{'=' * 70}")
    print(f"[STEP 3] 📜 BILL ANALYSIS: {company_name}")
    print(f"{'=' * 70}")

    bills_path = Path(bills_folder)
    if not bills_path.exists():
        print("❌ No bills folder")
        return []

    # Build supplier context - COMPACT but complete
    supplier_context = []
    for s in suppliers[:20]:  # Limit to top 20 suppliers
        supplier_context.append(
            {
                "name": s.get("name", ""),
                "country": s.get("country", ""),
                "criticality": s.get("criticality", "medium"),
            }
        )

    print(f"📊 Analyzing with {len(supplier_context)} supplier locations")
    for s in supplier_context[:5]:
        print(f"   - {s.get('name')} in {s.get('country')}")

    all_verified_impacts = []

    # Process ALL files
    for file_path in bills_path.glob("*"):
        if not file_path.is_file():
            continue

        print(f"\n📄 {file_path.name}")

        try:
            result = md.convert(str(file_path))
            bill_text = result.text_content

            # Check for extremely long lines in the original text
            bill_lines = bill_text.split("\n")
            max_line_length = max(len(line) for line in bill_lines) if bill_lines else 0
            if max_line_length > 10000:
                print(
                    f"   ⚠️  WARNING: Found extremely long line ({max_line_length} chars) - using character chunking"
                )

            # Chunk by characters to avoid extremely long lines breaking context
            char_chunk_size = 5000  # ~5k chars per chunk
            overlap = 200  # 200 char overlap to avoid splitting mid-sentence

            total_chunks = (len(bill_text) + char_chunk_size - overlap - 1) // (
                char_chunk_size - overlap
            )
            print(
                f"   📊 Total chunks: {total_chunks} (bill size: {len(bill_text):,} chars)"
            )

            chunk_num = 0

            for idx in range(0, len(bill_text), char_chunk_size - overlap):
                chunk_num += 1
                # Get chunk with overlap
                chunk_text = bill_text[idx : idx + char_chunk_size]
                chunk_length = len(chunk_text)

                if not chunk_text.strip():
                    continue

                # Skip chunks that are obviously navigation or boilerplate
                if (
                    "table of contents" in chunk_text.lower()
                    or re.search(r"page \d+", chunk_text.lower())
                    or re.search(r"section \d+", chunk_text.lower())
                ):
                    continue

                try:
                    # STRICT system message to avoid vague impacts
                    system_message = """Extract ONLY DIRECT and SPECIFIC impacts on the company or its named suppliers.
                    REJECT vague, general, or speculative impacts.

                    CRITERIA FOR EXTRACTION:
                    - MUST directly mention company, suppliers, or specific industries/products
                    - MUST have clear quantitative impact (tariff rates, tax amounts, subsidy values)
                    - MUST be specific legislation with clear consequences
                    - REJECT general policy statements without specific impacts

                    Output: {
                        "impacts": [{
                            "target": "company/specific_supplier_name",
                            "supplier_country": "country if supplier",
                            "impact_type": "tariff/regulation/tax/ban/subsidy",
                            "affected_geography": "country/region mentioned in bill",
                            "quantitative_value": number (REQUIRED for tariffs/taxes/subsidies),
                            "unit": "percent/dollars/etc",
                            "severity": float 0.0-1.0,
                            "exact_quote": "VERBATIM text from bill showing the specific impact",
                            "timeframe": "immediate/short-term/long-term",
                            "reasoning": "specific explanation of HOW this directly affects the target"
                        }]
                    }

                    REJECT impacts that are:
                    - General industry trends
                    - Vague policy statements
                    - Speculative future effects
                    - Without specific quantitative values for tariffs/taxes/subsidies"""

                    response = client.chat.completions.create(
                        model=MODEL_ID,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_message},
                            {
                                "role": "user",
                                "content": f"""Bill Text:
{chunk_text}

Company: {company_name}
Sector: {sector}
Industry: {industry}

Known Suppliers (for reference):
{json.dumps(supplier_context, indent=2)}

Analyze for DIRECT, SPECIFIC impacts only. Reject vague statements.""",
                            },
                        ],
                        temperature=0.05,
                        max_tokens=1500,  # Increased for complete reasoning
                    )

                    result = json.loads(response.choices[0].message.content)

                    for impact in result.get("impacts", []):
                        exact_quote = impact.get("exact_quote", "").strip()

                        # STRICT VERIFICATION: Quote must exist AND be meaningful
                        if (
                            exact_quote
                            and exact_quote in chunk_text
                            and len(exact_quote) > 20  # Must be substantial quote
                            and not exact_quote.lower().startswith(
                                ("section", "chapter", "article", "subsection")
                            )
                        ):
                            # Additional quality checks
                            impact_type = impact.get("impact_type", "").lower()
                            quantitative_value = impact.get("quantitative_value")

                            # Require quantitative values for financial impacts
                            if (
                                impact_type in ["tariff", "tax", "subsidy"]
                                and quantitative_value is None
                            ):
                                print(
                                    f"   ❌ REJECTED: {impact_type} without quantitative value"
                                )
                                continue

                            # Check for vague targets
                            target = impact.get("target", "").lower()
                            if target in [
                                "company",
                                "supplier",
                                "company/supplier_name",
                                "various",
                                "multiple",
                            ]:
                                print(f"   ❌ REJECTED: Vague target '{target}'")
                                continue

                            impact["bill_name"] = file_path.name
                            all_verified_impacts.append(impact)

                            print(
                                f"   ✅ {impact.get('target')}: {impact.get('impact_type')} ({impact.get('quantitative_value')}{impact.get('unit', '')})"
                            )
                        else:
                            print(f"   ❌ REJECTED: Invalid or truncated quote")

                except openai.BadRequestError as e:
                    if "maximum context length" in str(e):
                        print(
                            f"   ⚠️ CHUNK TOO LONG ERROR [chunk {chunk_num}/{total_chunks}]: chunk length={chunk_length} chars, position={idx:,}"
                        )
                        continue
                    else:
                        print(f"   ⚠️ API error [chunk {chunk_num}/{total_chunks}]: {e}")
                        continue
                except Exception as e:
                    print(
                        f"   ⚠️ Processing error [chunk {chunk_num}/{total_chunks}]: {e}"
                    )
                    continue

        except Exception as e:
            print(f"   ❌ File error: {e}")
            continue

    # Filter out low-quality impacts
    high_quality_impacts = []
    for impact in all_verified_impacts:
        # Ensure all required fields are present and meaningful
        if (
            impact.get("exact_quote")
            and impact.get("target")
            and impact.get("impact_type")
            and len(impact.get("exact_quote", "")) > 20
        ):
            high_quality_impacts.append(impact)

    bills_processed = list(set([i.get("bill_name", "") for i in high_quality_impacts]))

    print(
        f"\n✅ Bills: {len(high_quality_impacts)} high-quality impacts from {len(bills_processed)} laws"
    )
    return high_quality_impacts


# ===== STEP 4: PURE PYTHON SYNTHESIS (NO AI) =====


def synthesize_analysis(ticker, company_name, sec_metrics, suppliers, bill_impacts):
    """PURE PYTHON - NO AI HALLUCINATIONS - NO TRUNCATION"""
    print(f"\n{'=' * 70}")
    print(f"[STEP 4] 🎯 SYNTHESIS (Pure Python): {ticker}")
    print(f"{'=' * 70}")

    # Separate direct vs indirect with better filtering
    direct_impacts = [
        i
        for i in bill_impacts
        if (
            i.get("target", "").lower() == "company"
            or company_name.lower() in i.get("target", "").lower()
            or any(
                keyword in i.get("target", "").lower()
                for keyword in ["direct", "primary", "specific"]
            )
        )
    ]

    indirect_impacts = [
        i
        for i in bill_impacts
        if i not in direct_impacts
        and i.get("target")
        and i.get("target") != "company/supplier_name"
    ]

    # Get unique bills
    bills_with_direct = list(set([i.get("bill_name", "") for i in direct_impacts]))
    bills_with_indirect = list(set([i.get("bill_name", "") for i in indirect_impacts]))
    all_bills = list(set([i.get("bill_name", "") for i in bill_impacts]))

    # CALCULATE DirectRiskFactor (pure math)
    if direct_impacts:
        direct_severities = [i.get("severity", 0) for i in direct_impacts]
        avg_severity = statistics.mean(direct_severities)

        # Weight by quantitative value if available
        weighted_severities = []
        for impact in direct_impacts:
            base_severity = impact.get("severity", 0)
            quant_value = impact.get("quantitative_value")
            if quant_value and impact.get("unit") == "percent":
                # Higher percentages = higher severity adjustment
                severity_multiplier = min(2.0, 1.0 + (quant_value / 100))
                weighted_severities.append(base_severity * severity_multiplier)
            else:
                weighted_severities.append(base_severity)

        avg_severity = (
            statistics.mean(weighted_severities)
            if weighted_severities
            else avg_severity
        )

        # Check if impacts are positive or negative
        positive_keywords = ["subsidy", "tax credit", "incentive", "support", "grant"]
        negative_keywords = ["tariff", "tax", "ban", "restriction", "penalty", "fee"]

        positive_count = sum(
            1
            for i in direct_impacts
            if any(kw in i.get("impact_type", "").lower() for kw in positive_keywords)
        )
        negative_count = sum(
            1
            for i in direct_impacts
            if any(kw in i.get("impact_type", "").lower() for kw in negative_keywords)
        )

        if negative_count > positive_count:
            direct_risk = -avg_severity
        elif positive_count > negative_count:
            direct_risk = avg_severity
        else:
            direct_risk = 0
    else:
        direct_risk = 0

    # CALCULATE IndirectRiskFactor (pure math)
    if indirect_impacts:
        indirect_severities = [i.get("severity", 0) for i in indirect_impacts]
        avg_severity = statistics.mean(indirect_severities)

        positive_count = sum(
            1
            for i in indirect_impacts
            if any(
                kw in i.get("impact_type", "").lower()
                for kw in ["subsidy", "tax credit", "incentive"]
            )
        )
        negative_count = sum(
            1
            for i in indirect_impacts
            if any(
                kw in i.get("impact_type", "").lower()
                for kw in ["tariff", "tax", "ban", "restriction"]
            )
        )

        if negative_count > positive_count:
            indirect_risk = -avg_severity
        elif positive_count > negative_count:
            indirect_risk = avg_severity
        else:
            indirect_risk = 0
    else:
        indirect_risk = 0

    # CALCULATE TimeFactor (pure logic)
    immediate_count = sum(
        1 for i in bill_impacts if i.get("timeframe", "").lower() == "immediate"
    )
    short_term_count = sum(
        1 for i in bill_impacts if i.get("timeframe", "").lower() == "short-term"
    )
    long_term_count = sum(
        1 for i in bill_impacts if i.get("timeframe", "").lower() == "long-term"
    )

    if immediate_count > 0:
        time_factor = 1.0
    elif short_term_count > long_term_count:
        time_factor = 0.9
    elif short_term_count > 0:
        time_factor = 0.85
    else:
        time_factor = 0.75

    # BUILD Summary (minimal AI)
    summary_points = []
    for impact in (direct_impacts + indirect_impacts)[:3]:
        val = impact.get("quantitative_value")
        unit = impact.get("unit", "")
        if val:
            summary_points.append(
                f"{val}{unit} {impact.get('impact_type', '')} on {impact.get('target', '')}"
            )
        else:
            summary_points.append(
                f"{impact.get('impact_type', '')} on {impact.get('target', '')}"
            )

    if summary_points:
        summary = f"{len(all_bills)} laws analyzed. " + "; ".join(summary_points[:2])
    else:
        summary = (
            f"{len(all_bills)} laws analyzed with no significant impact identified"
        )

    # BUILD Keypoints (pure data)
    keypoints = []
    for impact in direct_impacts[:3]:
        val = impact.get("quantitative_value")
        unit = impact.get("unit", "")
        if val:
            keypoints.append(
                f"{val}{unit} {impact.get('impact_type', '')} - {impact.get('bill_name', '')}"
            )
        else:
            keypoints.append(
                f"{impact.get('impact_type', '')} identified in {impact.get('bill_name', '')}"
            )

    for impact in indirect_impacts[:2]:
        keypoints.append(
            f"Supplier {impact.get('target', '')} affected by {impact.get('impact_type', '')}"
        )

    if not keypoints:
        keypoints = ["No significant law impacts identified"]

    # FINAL RESULT (all pure Python, no AI hallucination) - NO TRUNCATION
    result = {
        "Ticker": ticker,
        "Summary": summary[:200],  # Reasonable limit for summary
        "SummaryKeypoints": keypoints[:5],
        "DirectRiskFactor": round(direct_risk, 3),
        "IndirectRiskFactor": round(indirect_risk, 3),
        "TimeFactor": round(time_factor, 2),
        "Overview": {
            "total_laws_analyzed": len(all_bills),
            "laws_with_direct_impact": bills_with_direct,
            "laws_with_indirect_impact": bills_with_indirect,
            "sec_citations": [
                {
                    "metric": m.get("type", ""),
                    "exact_quote": m.get("exact_quote", ""),  # NO TRUNCATION
                    "value": m.get("value"),
                }
                for m in sec_metrics[:15]
            ],
            "direct_bill_impacts": [
                {
                    "bill": i.get("bill_name", ""),
                    "type": i.get("impact_type", ""),
                    "affected_geography": i.get("affected_geography", ""),
                    "exact_quote": i.get("exact_quote", ""),  # NO TRUNCATION
                    "severity": i.get("severity", 0),
                    "timeframe": i.get("timeframe", ""),
                    "quantitative_value": i.get("quantitative_value"),
                    "reasoning": i.get("reasoning", ""),  # NO TRUNCATION
                }
                for i in direct_impacts
            ],
            "indirect_bill_impacts": [
                {
                    "supplier": i.get("target", ""),
                    "supplier_country": i.get("supplier_country", ""),
                    "bill": i.get("bill_name", ""),
                    "type": i.get("impact_type", ""),
                    "affected_geography": i.get("affected_geography", ""),
                    "exact_quote": i.get("exact_quote", ""),  # NO TRUNCATION
                    "severity": i.get("severity", 0),
                    "timeframe": i.get("timeframe", ""),
                    "reasoning": i.get("reasoning", ""),  # NO TRUNCATION
                }
                for i in indirect_impacts
            ],
            "suppliers_identified": [s.get("name", "") for s in suppliers],
        },
    }

    print(f"\n✅ SYNTHESIS COMPLETE (Pure Python):")
    print(f"   DirectRiskFactor: {result['DirectRiskFactor']}")
    print(f"   IndirectRiskFactor: {result['IndirectRiskFactor']}")
    print(f"   TimeFactor: {result['TimeFactor']}")
    print(f"   Direct impacts: {len(direct_impacts)}")
    print(f"   Indirect impacts: {len(indirect_impacts)}")

    return result


# ===== MAIN PIPELINE =====


def analyze_stock(
    ticker,
    company_name,
    sector,
    industry,
    save_individual=True,
    output_folder="company_analyses",
):
    """Complete analysis - minimal AI usage"""
    print(f"\n{'#' * 70}")
    print(f"# ANALYZING: {company_name} ({ticker})")
    print(f"{'#' * 70}")

    # AI only for extraction
    sec_metrics = analyze_sec_filing(ticker)
    suppliers = analyze_suppliers(company_name)
    bill_impacts = analyze_bills(company_name, sector, industry, suppliers)

    # Pure Python for synthesis (no hallucination)
    final_result = synthesize_analysis(
        ticker, company_name, sec_metrics, suppliers, bill_impacts
    )

    # Save individual file
    if save_individual:
        Path(output_folder).mkdir(exist_ok=True)
        company_filename = f"{ticker}.json"
        company_filepath = os.path.join(output_folder, company_filename)

        with open(company_filepath, "w") as f:
            json.dump(final_result, f, indent=2)

        print(f"\n💾 Saved to: {company_filepath}")

    return final_result


def batch_analyze_sp500(
    csv_path="constituents.csv",
    limit=None,
    output_path="sp500_bill_analysis.json",
    output_folder="company_analyses",
):
    """Batch process - saves to both aggregated JSON and individual files"""
    df = pd.read_csv(csv_path)

    if limit:
        df = df.head(limit)

    # Create output folder for individual files
    Path(output_folder).mkdir(exist_ok=True)

    results = []

    for idx, row in df.iterrows():
        try:
            result = analyze_stock(
                ticker=row["Symbol"],
                company_name=row["Security"],
                sector=row["GICS Sector"],
                industry=row["GICS Sub-Industry"],
            )

            results.append(result)

            # Save individual company file
            ticker = row["Symbol"]
            company_filename = f"{ticker}.json"
            company_filepath = os.path.join(output_folder, company_filename)

            with open(company_filepath, "w") as f:
                json.dump(result, f, indent=2)

            print(f"💾 Saved to: {company_filepath}")

            # Save aggregated file incrementally
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

            print(f"✅ {idx + 1}/{len(df)} completed\n")

        except Exception as e:
            print(f"❌ {row['Security']}: {e}")
            continue

    print(f"\n{'=' * 70}")
    print(f"COMPLETE!")
    print(f"{'=' * 70}")
    print(f"Aggregated file: {output_path}")
    print(f"Individual files: {output_folder}/")

    # Show most at risk
    sorted_by_direct = sorted(results, key=lambda x: x.get("DirectRiskFactor", 0))
    print(f"\nMost at Direct Risk:")
    for r in sorted_by_direct[:5]:
        print(f"  {r['Ticker']:5s} {r.get('DirectRiskFactor', 0):+.3f}")

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("S&P 500 BILL IMPACT ANALYSIS")
    print("Minimal AI | Pure Python Calculations | All File Types")
    print("=" * 70)

    # Run full batch analysis on ALL 500 companies
    print("\n🚀 Starting batch analysis of ALL S&P 500 companies...")
    print("This will take a while - results saved incrementally\n")

    batch_analyze_sp500()

    # Or run with limit for testing
    # batch_analyze_sp500(limit=10)