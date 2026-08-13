
import streamlit as st
import requests

st.set_page_config(page_title="Product Validation: Workflow vs Agent", layout="wide")

st.title("🛒 Product Validation Demo")
st.caption("Compare the fixed-workflow validator against the dynamic agent validator.")

with st.sidebar:
    st.header("Settings")
    api_base = st.text_input("API base URL", value="http://localhost:8000")
    mode = st.radio(
        "Which endpoint(s) to call",
        ["Both (compare)", "Workflow only", "Agent only"],
        index=0,
    )

st.subheader("Product details")

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Product name", value="Wireless Bluetooth Earbuds")
    category = st.text_input("Category", value="Electronics")
    vendor_id = st.text_input("Vendor ID (agent only)", value="vendor-123")
with col2:
    sub_category = st.text_input("Subcategory", value="Audio")
    price = st.number_input("Price (agent only)", min_value=0.0, value=19.99, step=0.01)

description = st.text_area(
    "Description",
    value="Noise-cancelling earbuds with 24hr battery life and touch controls.",
    height=100,
)

image_urls_raw = st.text_area(
    "Image URLs (one per line)",
    value="https://images.unsplash.com/photo-1590658268037-6bf12165a8df",
    height=100,
)
image_urls = [u.strip() for u in image_urls_raw.splitlines() if u.strip()]

run = st.button("🚀 Validate", type="primary", use_container_width=True)


def call_endpoint(path: str, payload: dict):
    try:
        resp = requests.post(f"{api_base}{path}", json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json(), None
    except Exception as e:
        return None, str(e)


def render_result(title: str, result: dict, error: str):
    st.markdown(f"#### {title}")
    if error:
        st.error(f"Request failed: {error}")
        return

    rec = result.get("recommendation", "UNKNOWN")
    color = {"ACCEPT": "green", "REJECT": "red", "ESCALATE": "orange"}.get(rec, "gray")
    st.markdown(f"**Recommendation:** :{color}[{rec}]")
    st.progress(min(max(result.get("confidence", 0), 0), 100) / 100)
    st.caption(f"Confidence: {result.get('confidence', 'n/a')}%")

    issues = result.get("issues", [])
    if issues:
        st.markdown("**Issues flagged:**")
        for i in issues:
            st.markdown(f"- {i}")
    else:
        st.markdown("_No issues flagged._")

    tools_used = result.get("toolsUsed")
    if tools_used is not None:
        if tools_used:
            st.markdown("**Tools the agent called:**")
            for t in tools_used:
                st.markdown(f"- `{t}`")
        else:
            st.markdown("**Tools the agent called:** none — decided the listing was clear enough on its own")

    with st.expander("Raw JSON response"):
        st.json(result)


if run:
    if not image_urls:
        st.warning("Add at least one image URL before validating.")
    else:
        payload = {
            "name": name,
            "description": description,
            "category": category,
            "subCategory": sub_category,
            "imageUrls": image_urls,
            "vendorId": vendor_id,
            "price": price,
        }

        if mode == "Both (compare)":
            colA, colB = st.columns(2)
            with st.spinner("Calling both endpoints..."):
                wf_result, wf_err = call_endpoint("/validate-product", payload)
                agent_result, agent_err = call_endpoint("/validate-product-agent", payload)
            with colA:
                render_result("🧱 Fixed Workflow (`/validate-product`)", wf_result, wf_err)
            with colB:
                render_result("🤖 Dynamic Agent (`/validate-product-agent`)", agent_result, agent_err)

        elif mode == "Workflow only":
            with st.spinner("Calling workflow endpoint..."):
                wf_result, wf_err = call_endpoint("/validate-product", payload)
            render_result("🧱 Fixed Workflow (`/validate-product`)", wf_result, wf_err)

        else:
            with st.spinner("Calling agent endpoint..."):
                agent_result, agent_err = call_endpoint("/validate-product-agent", payload)
            render_result("🤖 Dynamic Agent (`/validate-product-agent`)", agent_result, agent_err)