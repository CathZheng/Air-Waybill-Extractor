import streamlit as st
import json
from pdf2image import convert_from_bytes
import io
from google import genai
from google.genai import types
import os 
import time # To add a timer and timestamps
import re 
# --- Backend Function ---
# This function encapsulates your original logic.
def extract_awb_data(pdf_bytes, api_key):
    """
    Takes PDF bytes and an API key, converts the first page to an image,
    and calls the Gemini API to extract information as a JSON string.
    """
    print(f"\n[LOG] {time.ctime()}: Backend function 'extract_awb_data' started.")
    try:
        # 1. Convert PDF to image
        print("[LOG] Step 1: Converting PDF bytes to image...")
        images = convert_from_bytes(pdf_bytes)
        if not images:
            print("[ERROR] PDF conversion failed. No images were created.")
            raise ValueError("Could not convert PDF to image. The file might be corrupted or empty.")
        
        print("✅ [LOG] PDF page converted to image successfully.")
        page = images[0]
        buffer = io.BytesIO()
        page.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        print("[LOG] Image saved to in-memory buffer.")

        # 2. Configure and call the Generative AI model
        print("[LOG] Step 2: Configuring Google AI client...")
        client = genai.Client(api_key=api_key)
        
        prompt = """
        This is an Air Waybill, extract all information in it with the headers then export it in json format. Do not make up any header. Do not make up any information. Do not include ```json ... ``` in the output.
            {{"Air Waybill Number": " ",
             "Shipper's Name and Address": " ",
             "Shipper's Account Number": " ",
             "Consignee's Name and Address": " ",
             "Issuing Carrier's Agent Name and City": "",
             "Issued by": " ",
             "Agent's IATA Code": "",
             "Account No": "",
             "Airport of Departure (Addr. of First Carrier) and Requested Routing": "",
             "Routing and Destination": [{{"to": " ", "by": " "}}],
             "Airport of Destination": " ",
             "Flight/Date": " ",
             "Handling Information": " ",
             "Accounting Information": " ",
             "Currency Code": " ",
             "CHGS": [{{"CHGS Code":" ", "WT/VAL": [{{"PPD": " ", "COLL":" "}}], "Other": [{{"PPD": " ", "COLL":" "}}]}}],
             "Declared Value for Carriage": " ",
             "Declared Value for Customs": " ",
             "Amount of Insurance": "",
             "Goods Description Table Rows": [
                {{
                "No. of Pieces RCP": "",
                "Gross Weight": "",
                "kg/lb": "",
                "Rate Class / Commodity Item No.": "",
                "Chargeable Weight": "",
                "Rate": "",
                "Charge": "",
                "Total": "",
                "Nature and Quantity of Goods (incl. Dimensions or Volume)": ""
                }}],
             "Charges Details": [
                {{
                "Weight Charge": {{"Prepaid": "", "Collect": ""}},
                "Valuation Charge": {{"Prepaid": "", "Collect": ""}},
                "Tax": {{"Prepaid": "", "Collect": ""}},
                "Total Other Charges Due Agent": {{"Prepaid": "", "Collect": ""}},
                "Total Other Charges Due Carrie": {{"Prepaid": "", "Collect": ""}},
                "Total Prepaid": "",
                "Total Collect": "",
                "Currency Conversion Rates": "",
                "CC Charges at Dest Currency":""
                }}],
             "Signature of Shipper of his Agent": "",
             "Executed on (date)": "",
             "at (place)": "",
             "Signature of Issuing Carrier or its Agent": ""
            }}
        """
        
        print("[LOG] Calling the Gemini API...")
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=img_bytes,
                    mime_type='image/png',
                ),
                prompt,
            ]
        )
        print("✅ [LOG] Received response from Gemini API.")
        
        return response.text

    except Exception as e:
        print(f"❌ [ERROR] An exception occurred in the backend: {str(e)}")
        return f"An error occurred: {str(e)}"

def display_awb_data(data):
    """
    Display the Air Waybill data in a beautiful, organized format
    """
    st.markdown("---")
    
    # Document Header
    st.markdown("## 📋 Air Waybill Information")
    
    # Basic Information Section
    with st.container():
        st.markdown("### 📄 Document Details")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Air Waybill Number:** `{data.get('Air Waybill Number', 'N/A')}`")
            st.markdown(f"**Flight/Date:** {data.get('Flight/Date', 'N/A')}")
            st.markdown(f"**Currency Code:** {data.get('Currency Code', 'N/A')}")
        
        with col2:
            st.markdown(f"**Airport of Departure:** {data.get('Airport of Departure (Addr. of First Carrier) and Requested Routing', 'N/A')}")
            st.markdown(f"**Airport of Destination:** {data.get('Airport of Destination', 'N/A')}")
            st.markdown(f"**Agent's IATA Code:** {data.get('Agent\'s IATA Code', 'N/A')}")
    
    st.markdown("---")
    
    # Parties Information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📤 Shipper Information")
        st.text_area("Shipper's Name and Address", 
                    data.get("Shipper's Name and Address", "N/A"), 
                    height=100, disabled=False)
        st.markdown(f"**Account Number:** {data.get('Shipper\'s Account Number', 'N/A')}")
    
    with col2:
        st.markdown("### 📥 Consignee Information")
        st.text_area("Consignee's Name and Address", 
                    data.get("Consignee's Name and Address", "N/A"), 
                    height=100, disabled=False)
    
    st.markdown("---")
    
    # Agent and Routing Information
    st.markdown("### 🏢 Agent & Routing Details")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Issuing Carrier's Agent:** {data.get('Issuing Carrier\'s Agent Name and City', 'N/A')}")
        st.markdown(f"**Issued by:** {data.get('Issued by', 'N/A')}")
        st.markdown(f"**Account No:** {data.get('Account No', 'N/A')}")
    
    with col2:
        # Display routing information
        routing_data = data.get('Routing and Destination', [])
        if routing_data and isinstance(routing_data, list):
            st.markdown("**Routing Information:**")
            for i, route in enumerate(routing_data):
                if isinstance(route, dict):
                    st.markdown(f"• To: {route.get('to', 'N/A')} | By: {route.get('by', 'N/A')}")
        else:
            st.markdown("**Routing Information:** N/A")
    
    st.markdown("---")
    
    # Goods Description
    st.markdown("### 📦 Goods Description")
    goods_data = data.get('Goods Description Table Rows', [])
    
    if goods_data and isinstance(goods_data,list):
        for i, item in enumerate(goods_data):
            if isinstance(item, dict):
                with st.expander(f"Item {i+1}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**Pieces:** {item.get('No. of Pieces RCP', 'N/A')}")
                        st.markdown(f"**Gross Weight:** {item.get('Gross Weight', 'N/A')} {item.get('kg/lb', '')}")
                    
                    with col2:
                        st.markdown(f"**Chargeable Weight:** {item.get('Chargeable Weight', 'N/A')}")
                        st.markdown(f"**Rate:** {item.get('Rate', 'N/A')}")
                    
                    with col3:
                        st.markdown(f"**Charge:** {item.get('Charge', 'N/A')}")
                        st.markdown(f"**Total:** {item.get('Total', 'N/A')}")
                    
                    st.markdown(f"**Rate Class/Commodity:** {item.get('Rate Class / Commodity Item No.', 'N/A')}")
                    st.text_area(f"Nature and Quantity of Goods {i+1}", 
                               item.get('Nature and Quantity of Goods (incl. Dimensions or Volume)', 'N/A'),
                               height=100, disabled=False, key=f"goods_{i}")
    else:
        st.info("No goods description data available")
    
    st.markdown("---")
    
    # Charges Details
    st.markdown("### 💰 Charges Details")
    charges_data = data.get('Charges Details', [])
    
    if charges_data and isinstance(charges_data, list):
        for charge_detail in charges_data:
            if isinstance(charge_detail, dict):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Prepaid Charges:**")
                    weight_charge = charge_detail.get('Weight Charge', {})
                    if isinstance(weight_charge, dict):
                        st.markdown(f"• Weight Charge: {weight_charge.get('Prepaid', 'N/A')}")
                    
                    val_charge = charge_detail.get('Valuation Charge', {})
                    if isinstance(val_charge, dict):
                        st.markdown(f"• Valuation Charge: {val_charge.get('Prepaid', 'N/A')}")
                    
                    tax_charge = charge_detail.get('Tax', {})
                    if isinstance(tax_charge, dict):
                        st.markdown(f"• Tax: {tax_charge.get('Prepaid', 'N/A')}")
                    
                    st.markdown(f"**Total Prepaid:** {charge_detail.get('Total Prepaid', 'N/A')}")
                
                with col2:
                    st.markdown("**Collect Charges:**")
                    if isinstance(weight_charge, dict):
                        st.markdown(f"• Weight Charge: {weight_charge.get('Collect', 'N/A')}")
                    
                    if isinstance(val_charge, dict):
                        st.markdown(f"• Valuation Charge: {val_charge.get('Collect', 'N/A')}")
                    
                    if isinstance(tax_charge, dict):
                        st.markdown(f"• Tax: {tax_charge.get('Collect', 'N/A')}")
                    
                    st.markdown(f"**Total Collect:** {charge_detail.get('Total Collect', 'N/A')}")
    else:
        st.info("No charges details available")
    
    st.markdown("---")
    
    # Declaration and Insurance
    st.markdown("### 📋 Declarations & Insurance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Declared Value for Carriage:** {data.get('Declared Value for Carriage', 'N/A')}")
    
    with col2:
        st.markdown(f"**Declared Value for Customs:** {data.get('Declared Value for Customs', 'N/A')}")
    
    with col3:
        st.markdown(f"**Amount of Insurance:** {data.get('Amount of Insurance', 'N/A')}")
    
    st.markdown("---")
    
    # Additional Information
    st.markdown("### ℹ️ Additional Information")
    
    if data.get('Handling Information') and data.get('Handling Information').strip():
        st.text_area("Handling Information", 
                    data.get('Handling Information', 'N/A'), 
                    height=60, disabled=True)
    
    if data.get('Accounting Information') and data.get('Accounting Information').strip():
        st.text_area("Accounting Information", 
                    data.get('Accounting Information', 'N/A'), 
                    height=60, disabled=True)
    
    # Signatures and Execution
    st.markdown("### ✍️ Signatures & Execution")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Executed on:** {data.get('Executed on (date)', 'N/A')}")
        st.markdown(f"**At (place):** {data.get('at (place)', 'N/A')}")
    
    with col2:
        st.markdown(f"**Shipper/Agent Signature:** {data.get('Signature of Shipper of his Agent', 'N/A')}")
        st.markdown(f"**Carrier/Agent Signature:** {data.get('Signature of Issuing Carrier or its Agent', 'N/A')}")

# --- Streamlit Frontend Design ---
st.set_page_config(page_title="Air Waybill Extractor", page_icon="📄", layout="wide")

st.title("📄 Air Waybill Information Extractor")
st.write("Upload an Air Waybill in PDF format to extract its contents into a structured, readable format.")

with st.sidebar:
    # st.header("Configuration")
    # api_key = st.text_input("Enter your Google AI API Key", type="password")
    # st.info("💡 Your API key is not stored. It is only used for the current session.")
    
    # Add display options
    st.header("Display Options")
    show_raw_json = st.checkbox("Show Raw JSON", value=False)
    download_json = st.checkbox("Enable JSON Download", value=True)

uploaded_file = st.file_uploader("Choose an Air Waybill PDF file", type="pdf")
api_key = st.secrets["GOOGLE_API_KEY"]
if st.button("✨ Extract Information"):
    print(f"\n[LOG] {time.ctime()}: 'Extract Information' button clicked.")
    if uploaded_file is not None and api_key:
        print("[LOG] PDF file and API key are present.")
        pdf_bytes = uploaded_file.getvalue()
        
        with st.spinner("Processing PDF and extracting data... This may take a moment. ⏳"):
            # --- TIMER START ---
            start_time = time.perf_counter()
            
            # Call the backend function
            response_text = extract_awb_data(pdf_bytes, api_key)
            
            # --- TIMER END ---
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"✅ [LOG] Total processing time: {elapsed_time:.2f} seconds.")
            
            print("[LOG] Attempting to parse API response as JSON...")
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                
                    print("✅ [LOG] JSON parsing successful. Displaying results.")
                    st.success("✅ Extraction Complete!")
                    st.info(f"⏱️ **Processing Time:** {elapsed_time:.2f} seconds")
                    if download_json:
                        st.markdown("---")
                        json_str_for_download = json.dumps(data, indent=2)
                        st.download_button(
                            label="📥 Download JSON Data",
                            data=json_str_for_download,
                            file_name=f"awb_data_{data.get('Air Waybill Number', 'unknown')}.json",
                            mime="application/json"
                        )
                    # --- All code that uses 'data' is now inside this 'if' block ---
                    display_awb_data(data)
                    
                    if show_raw_json:
                        st.markdown("---")
                        st.markdown("### 🔍 Raw JSON Data")
                        with st.expander("Click to view raw JSON"):
                            st.json(data)
                    
                else:
                    # Handle the case where the regex found no JSON
                    print("❌ [ERROR] No JSON object found in the response.")
                    st.error("Failed to parse the response as JSON. The model did not return a valid JSON object.")
                    st.info(f"⏱️ **Attempted in:** {elapsed_time:.2f} seconds")
                    st.text_area("Raw Model Response", response_text, height=200)
            except Exception as e:
                 print(f"❌ [ERROR] An unexpected error occurred on the frontend: {e}")
                 st.error(f"An unexpected error occurred: {e}")
                 st.text_area("Raw Model Response", response_text, height=200)

    elif not api_key:
        print("[WARNING] API key is missing.")
        st.warning("Please enter your Google AI API Key in the sidebar.")
    else:
        print("[WARNING] PDF file is missing.")
        st.warning("Please upload a PDF file.")
