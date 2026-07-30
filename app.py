# -*- coding: utf-8 -*-
import streamlit as st, requests, base64, json, logging, os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_URL = os.environ.get("PULMONARY_API_URL", "https://j29v25aib3.execute-api.us-east-1.amazonaws.com/prod/predict")

st.set_page_config(page_title="AI Pulmonary Diagnostic", page_icon="🫁", layout="wide")
st.title("🫁 AI Pulmonary Diagnostic Suite (Serverless)")
st.markdown("Hệ thống chẩn đoán viêm phổi qua ảnh X-Quang sử dụng kiến trúc AWS Serverless.")

st.sidebar.header("Tải ảnh X-Quang")
uploaded_file = st.sidebar.file_uploader("Chọn ảnh X-Quang (JPEG/PNG)...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Ảnh X-Quang đã tải lên", width=400)
    if st.button("Chẩn đoán ngay (Serverless)"):
        with st.spinner("Đang gửi yêu cầu tới AWS Serverless API..."):
            try:
                base64_encoded = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps({"image_bytes": base64_encoded}), timeout=30)
                if response.status_code == 200:
                    predictions = response.json().get("raw_predictions", [])
                    if predictions:
                        prob = predictions[0] * 100
                        st.success("Chẩn đoán hoàn tất!")
                        if prob > 50:
                            st.error(f"⚠️ Phát hiện rủi ro Viêm Phổi: {prob:.2f}%")
                        else:
                            st.info(f"✅ Phổi có dấu hiệu bình thường (Rủi ro: {prob:.2f}%)")
                        st.progress(int(prob))
                    else: st.warning("API trả về thành công nhưng không có kết quả dự đoán.")
                else: st.error(f"Lỗi hệ thống Cloud (HTTP {response.status_code})")
            except Exception as e: st.error(f"Đã xảy ra lỗi: {e}")
