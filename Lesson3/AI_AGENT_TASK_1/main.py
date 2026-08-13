
from fastapi import FastAPI
from pydantic import BaseModel
import requests, os, json, base64, mimetypes
from typing import List, Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

KEY_VAULT_NAME = os.getenv("KeyVaultName")

BACKEND_BASE_URL = os.getenv("BackendBaseUrl", "http://localhost:5000")


def load_secret(name: str, fallback_env: str = None) -> str:
    if KEY_VAULT_NAME:
        vault_url = f"https://{KEY_VAULT_NAME}.vault.azure.net"
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        return client.get_secret(name).value
    if fallback_env:
        return os.getenv(fallback_env, "")
    return ""


ANTHROPIC_API_KEY = load_secret("AnthropicApiKey", fallback_env="ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = load_secret("AnthropicBaseUrl", fallback_env="ANTHROPIC_BASE_URL") or "https://api.anthropic.com"
ANTHROPIC_URL = f"{ANTHROPIC_BASE_URL.rstrip('/')}/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL_NAME = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Image handling (shared by both workflow and agent endpoints)
# ---------------------------------------------------------------------------

def image_url_to_base64_block(url: str) -> dict:
    """
    Returns an Anthropic base64 image content block from either:
      1. A real HTTP(S) image URL -- downloaded and base64-encoded here, or
      2. An already-encoded data URI (e.g. "data:image/jpeg;base64,...") -- parsed directly,
         no network request needed.

    NOTE: the Presidio LLM gateway proxy this service is currently pointed at does not support
    the "url" image source type ("URL sources are not supported" error) -- it requires images to
    be sent as base64 data, one way or another.
    """
    if url.startswith("data:"):
        try:
            header, encoded = url.split(",", 1)
            media_type = header.split(":", 1)[1].split(";")[0] or "image/jpeg"
        except (IndexError, ValueError):
            media_type = "image/jpeg"
            encoded = url.split(",", 1)[-1]

        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded,
            },
        }

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type")
    if not content_type or not content_type.startswith("image/"):
        guessed, _ = mimetypes.guess_type(url)
        content_type = guessed or "image/jpeg"

    encoded = base64.b64encode(resp.content).decode("utf-8")

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": content_type,
            "data": encoded,
        },
    }


# ---------------------------------------------------------------------------
# Shared request models
# (vendorId / price are optional so the workflow endpoints work fine without them,
#  while the agent endpoints can use them when present)
# ---------------------------------------------------------------------------

class ProductValidationRequest(BaseModel):
    name: str
    description: str
    category: str
    subCategory: str
    imageUrls: List[str]
    vendorId: Optional[str] = None
    price: Optional[float] = None


class VariantAttribute(BaseModel):
    attributeName: str
    attributeValue: str


class ProductVariantValidationRequest(BaseModel):
    productName: str
    description: str
    productCategoryName: str
    productSubCategoryName: str
    sku: str
    attributes: List[VariantAttribute]
    imageUrls: List[str]
    vendorId: Optional[str] = None
    price: Optional[float] = None


# ===========================================================================
# WORKFLOW implementation — fixed steps, same prompt every time
# ===========================================================================

def call_claude(content_blocks: list) -> str:
    """Calls the Anthropic Messages API (or configured gateway) and returns the reply text."""
    payload = {
        "model": MODEL_NAME,
        "max_tokens": 400,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": content_blocks}
        ],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }
    resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=60)

    if not resp.ok:
        print("ANTHROPIC ERROR BODY:", resp.text)

    resp.raise_for_status()
    data = resp.json()

    text_parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
    return "".join(text_parts)


def parse_json_response(content: str) -> dict:
    content = content.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "isValid": False,
            "confidence": 0,
            "issues": ["AI response parse error"],
            "recommendation": "REJECT",
        }


def build_workflow_prompt(p: ProductValidationRequest) -> str:
    return f"""
You are a strict e-commerce product QA reviewer.
You will be shown one or more images of the same product.
Check if the images collectively match the product data below, and if the data itself is consistent.

Product Name: {p.name}
Description: {p.description}
Category: {p.category}
Subcategory: {p.subCategory}

Rules:
1. All images must visually match the product name and description (different angles are fine).
2. If any image looks unrelated to the others or to the product data, flag it.
3. Category and Subcategory must logically fit the product.
4. Name/description must not be misleading, empty, or gibberish.

Respond ONLY in strict JSON:
{{
  "isValid": true/false,
  "confidence": 0-100,
  "issues": ["short reason 1", "short reason 2"],
  "recommendation": "ACCEPT" or "REJECT"
}}
"""


def build_workflow_variant_prompt(p: ProductVariantValidationRequest) -> str:
    attrs_text = "\n".join(
        f"- {a.attributeName}: {a.attributeValue}" for a in p.attributes
    ) or "No attributes provided"

    return f"""
You are a strict e-commerce product QA reviewer.
You will be shown one or more images of a specific product VARIANT (e.g. a particular color/size combination of a base product).
Check if the images match the variant's declared attributes, and if the data is internally consistent.

Base Product Name: {p.productName}
Description: {p.description}
Category: {p.productCategoryName}
Subcategory: {p.productSubCategoryName}
SKU: {p.sku}

Variant Attributes:
{attrs_text}

Rules:
1. Images must visually match the base product name/description (different angles are fine).
2. Images must visually match the declared variant attributes where visually verifiable — for example, if an attribute is "Color: Red", the product in the image should appear red. If an attribute cannot be visually verified (e.g. "Material: Cotton"), do not penalize for it.
3. If any image looks unrelated to the others or to the product/variant data, flag it.
4. Category and Subcategory must logically fit the product.
5. SKU, name, and description must not be misleading, empty, or gibberish.

Respond ONLY in strict JSON:
{{
  "isValid": true/false,
  "confidence": 0-100,
  "issues": ["short reason 1", "short reason 2"],
  "recommendation": "ACCEPT" or "REJECT"
}}
"""


@app.post("/validate-product")
def validate_product(p: ProductValidationRequest):
    content_blocks = [{"type": "text", "text": build_workflow_prompt(p)}]

    for url in p.imageUrls:
        content_blocks.append(image_url_to_base64_block(url))

    content = call_claude(content_blocks)
    return parse_json_response(content)


@app.post("/validate-variant")
def validate_variant(p: ProductVariantValidationRequest):
    content_blocks = [{"type": "text", "text": build_workflow_variant_prompt(p)}]

    for url in p.imageUrls:
        content_blocks.append(image_url_to_base64_block(url))

    content = call_claude(content_blocks)
    return parse_json_response(content)


# ===========================================================================
# AGENT implementation — dynamic tool use, decided per listing
# ===========================================================================

TOOLS = [
    {
        "name": "check_duplicate_product",
        "description": (
            "Check whether a very similar product (same name/category) already exists in "
            "the marketplace catalog. Use this when a listing looks generic, copy-pasted, "
            "or you suspect it might be a re-submission of a rejected/duplicate item."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "category": {"type": "string"},
            },
            "required": ["product_name", "category"],
        },
    },
    {
        "name": "check_price_anomaly",
        "description": (
            "Compare a submitted price against the average market price for its category/"
            "subcategory. Use this when the price seems suspiciously low (possible scam/"
            "counterfeit) or suspiciously high relative to what the images and description "
            "suggest."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "subcategory": {"type": "string"},
                "price": {"type": "number"},
            },
            "required": ["category", "price"],
        },
    },
    {
        "name": "get_vendor_trust_profile",
        "description": (
            "Look up a vendor's history: total submissions, past rejection rate, and any "
            "policy strikes. Use this when the listing content itself is ambiguous (not "
            "clearly good or bad) and the vendor's track record could tip the decision -- "
            "e.g. a borderline listing from a vendor with a high rejection rate deserves "
            "more scrutiny than the same listing from a trusted vendor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"vendor_id": {"type": "string"}},
            "required": ["vendor_id"],
        },
    },
]


def check_duplicate_product(product_name: str, category: str) -> dict:
    try:
        resp = requests.get(
            f"{BACKEND_BASE_URL}/api/products/check-duplicate",
            params={"name": product_name, "category": category},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"duplicate check unavailable: {e}"}


def check_price_anomaly(category: str, price: float, subcategory: Optional[str] = None) -> dict:
    try:
        resp = requests.get(
            f"{BACKEND_BASE_URL}/api/products/price-benchmark",
            params={"category": category, "subcategory": subcategory or "", "price": price},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"price benchmark unavailable: {e}"}


def get_vendor_trust_profile(vendor_id: str) -> dict:
    try:
        resp = requests.get(f"{BACKEND_BASE_URL}/api/vendors/{vendor_id}/trust-profile", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"vendor profile unavailable: {e}"}


TOOL_FUNCTIONS = {
    "check_duplicate_product": lambda i: check_duplicate_product(i["product_name"], i["category"]),
    "check_price_anomaly": lambda i: check_price_anomaly(i["category"], i["price"], i.get("subcategory")),
    "get_vendor_trust_profile": lambda i: get_vendor_trust_profile(i["vendor_id"]),
}


AGENT_SYSTEM_PROMPT = """You are an autonomous e-commerce listing reviewer.

You are shown a product's declared data and one or more images. You also have
tools available: check_duplicate_product, check_price_anomaly, and
get_vendor_trust_profile. You decide, based on this specific listing, whether
you need any of them -- do not call a tool just because it exists. For
example: if the images and description are clearly consistent and coherent,
you likely don't need any tool. If pricing looks off, or the listing is
generic/ambiguous, or a vendor's reliability could reasonably affect the call,
call the relevant tool(s) before deciding.

When you are done reasoning and (optionally) using tools, respond with ONLY
raw JSON, no markdown fences, no preamble, in exactly this shape:
{
  "isValid": true/false,
  "confidence": 0-100,
  "issues": ["short reason 1", "short reason 2"],
  "recommendation": "ACCEPT" or "REJECT" or "ESCALATE",
  "toolsUsed": ["<names of any tools you called, empty list if none>"]
}
"ESCALATE" means the case is borderline enough that a human Admin should make
the final call.
"""


def extract_json_object(text: str) -> Optional[dict]:
    """
    Pulls the first well-formed {...} JSON object out of a string, even if
    Claude wrapped it in markdown fences or added a stray sentence before/after.
    Returns None if nothing parseable is found.
    """
    text = text.strip()
    # Strip common markdown fences first
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    start = text.find("{")
    if start == -1:
        return None

    # Walk forward tracking brace depth to find the matching closing brace,
    # so trailing text after the JSON doesn't break parsing.
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None
    return None


def run_agent(content_blocks: list, vendor_id: Optional[str] = None, max_turns: int = 5) -> dict:
    messages = [{"role": "user", "content": content_blocks}]
    tools_used = []

    for _ in range(max_turns):
        payload = {
            "model": MODEL_NAME,
            "max_tokens": 1500,
            "temperature": 0.2,
            "system": AGENT_SYSTEM_PROMPT,
            "tools": TOOLS,
            "messages": messages,
        }
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=60)
        if not resp.ok:
            print("ANTHROPIC ERROR BODY:", resp.text)
        resp.raise_for_status()
        data = resp.json()

        messages.append({"role": "assistant", "content": data["content"]})

        if data.get("stop_reason") == "tool_use":
            tool_results = []
            for block in data["content"]:
                if block.get("type") != "tool_use":
                    continue
                tool_name = block["name"]
                tool_input = block["input"]
                tools_used.append(tool_name)

                fn = TOOL_FUNCTIONS.get(tool_name)
                result = fn(tool_input) if fn else {"error": f"unknown tool {tool_name}"}

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": json.dumps(result),
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            continue  # let the agent see the tool results and decide what's next

        # No more tool calls -- this is the final answer
        text_parts = [b["text"] for b in data["content"] if b.get("type") == "text"]
        final_text = "".join(text_parts).strip()

        result = extract_json_object(final_text)
        if result is None:
            print("AGENT FINAL TEXT (unparsed):", final_text)
            result = {
                "isValid": False,
                "confidence": 0,
                "issues": [f"AI response parse error -- raw text: {final_text[:200]}"],
                "recommendation": "ESCALATE",
                "toolsUsed": tools_used,
            }
        result.setdefault("toolsUsed", tools_used)
        return result

    return {
        "isValid": False,
        "confidence": 0,
        "issues": ["Agent exceeded max tool-use turns"],
        "recommendation": "ESCALATE",
        "toolsUsed": tools_used,
    }


def build_agent_prompt(p: ProductValidationRequest) -> str:
    return f"""
Product Name: {p.name}
Description: {p.description}
Category: {p.category}
Subcategory: {p.subCategory}
Vendor ID: {p.vendorId or "unknown"}
Price: {p.price if p.price is not None else "not provided"}

Review the images against this data and decide whether the listing should be
accepted, rejected, or escalated to a human admin.
"""


def build_agent_variant_prompt(p: ProductVariantValidationRequest) -> str:
    attrs_text = "\n".join(f"- {a.attributeName}: {a.attributeValue}" for a in p.attributes) or "No attributes provided"
    return f"""
Base Product Name: {p.productName}
Description: {p.description}
Category: {p.productCategoryName}
Subcategory: {p.productSubCategoryName}
SKU: {p.sku}
Vendor ID: {p.vendorId or "unknown"}
Price: {p.price if p.price is not None else "not provided"}

Variant Attributes:
{attrs_text}

Review the images against this variant's data and decide whether it should be
accepted, rejected, or escalated to a human admin.
"""


@app.post("/validate-product-agent")
def validate_product_agent(p: ProductValidationRequest):
    content_blocks = [{"type": "text", "text": build_agent_prompt(p)}]
    for url in p.imageUrls:
        content_blocks.append(image_url_to_base64_block(url))
    return run_agent(content_blocks, vendor_id=p.vendorId)


@app.post("/validate-variant-agent")
def validate_variant_agent(p: ProductVariantValidationRequest):
    content_blocks = [{"type": "text", "text": build_agent_variant_prompt(p)}]
    for url in p.imageUrls:
        content_blocks.append(image_url_to_base64_block(url))
    return run_agent(content_blocks, vendor_id=p.vendorId)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)