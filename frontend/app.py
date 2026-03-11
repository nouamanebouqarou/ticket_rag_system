import streamlit as st
import requests
import os

# Page configuration
st.set_page_config(
    page_title="Ticket RAG System",
    page_icon="🎫",
    layout="wide",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    .status-online {
        background-color: #d4edda;
        color: #155724;
    }
    .status-offline {
        background-color: #f8d7da;
        color: #721c24;
    }
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-online {
        background-color: #28a745;
    }
    .dot-offline {
        background-color: #dc3545;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .result-box {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 1rem;
        margin-top: 1rem;
        border-radius: 0 5px 5px 0;
    }
    .error-box {
        background-color: #ffe7e7;
        border-left: 4px solid #cc0000;
        padding: 1rem;
        margin-top: 1rem;
        border-radius: 0 5px 5px 0;
    }
    .success-box {
        background-color: #e7ffe7;
        border-left: 4px solid #00cc00;
        padding: 1rem;
        margin-top: 1rem;
        border-radius: 0 5px 5px 0;
    }
    .keyword-tag {
        display: inline-block;
        background-color: #6c757d;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.25rem;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 2rem;
        border-top: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = os.getenv('API_URL', 'http://localhost:8000')

def api_get(endpoint):
    """Make GET request to API"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def api_post(endpoint, data):
    """Make POST request to API"""
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Initialize session state
if 'stats' not in st.session_state:
    st.session_state.stats = None
if 'domains' not in st.session_state:
    st.session_state.domains = []
if 'status' not in st.session_state:
    st.session_state.status = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "dashboard"

# Load initial data
@st.cache_data(ttl=60)
def load_stats():
    return api_get("stats")

@st.cache_data(ttl=60)
def load_domains():
    return api_get("domains")

@st.cache_data(ttl=60)
def load_status():
    return api_get("status")

# Header
st.markdown('<div class="main-header">🎫 Ticket RAG System</div>', unsafe_allow_html=True)

# Status badge
status = load_status()
if status:
    st.markdown(f'''
        <span class="status-badge status-online">
            <span class="status-dot dot-online"></span>
            {status.get("api_type", "Unknown")} | {status.get("models", {}).get("llm", "Unknown")}
        </span>
    ''', unsafe_allow_html=True)
else:
    st.markdown('''
        <span class="status-badge status-offline">
            <span class="status-dot dot-offline"></span>
            Disconnected
        </span>
    ''', unsafe_allow_html=True)

st.markdown("---")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Analyze Ticket", "Search Similar", "Suggest Resolution"]
)

# Cache data
stats = load_stats()
domains = load_domains() or []

# ==================== DASHBOARD PAGE ====================
if page == "Dashboard":
    st.header("Dashboard")

    if stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{stats.get("total_tickets", 0):,}</div>
                    <div class="metric-label">Total Tickets</div>
                </div>
            ''', unsafe_allow_html=True)

        with col2:
            resolved = stats.get("resolved_tickets", 0)
            st.markdown(f'''
                <div class="metric-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                    <div class="metric-value">{resolved:,}</div>
                    <div class="metric-label">Resolved</div>
                </div>
            ''', unsafe_allow_html=True)

        with col3:
            unresolved = stats.get("unresolved_tickets", 0)
            st.markdown(f'''
                <div class="metric-card" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">
                    <div class="metric-value">{unresolved:,}</div>
                    <div class="metric-label">Unresolved</div>
                </div>
            ''', unsafe_allow_html=True)

        with col4:
            domains_count = len(stats.get("domains", []))
            st.markdown(f'''
                <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <div class="metric-value">{domains_count}</div>
                    <div class="metric-label">Domains</div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")

        # Domains section
        if domains:
            st.subheader("Available Domains")
            cols = st.columns(min(len(domains), 4))
            for i, domain in enumerate(domains):
                with cols[i % 4]:
                    st.markdown(f'''
                        <div style="
                            background-color: #f0f0f0;
                            padding: 0.75rem;
                            border-radius: 8px;
                            text-align: center;
                            margin-bottom: 0.5rem;
                        ">
                            <span style="font-weight: 500;">{domain}</span>
                        </div>
                    ''', unsafe_allow_html=True)
    else:
        st.warning("Unable to load statistics. Make sure the backend is running.")

# ==================== ANALYZE TICKET PAGE ====================
elif page == "Analyze Ticket":
    st.header("Analyze Ticket")

    with st.form("analyze_form"):
        ticket_number = st.text_input("Ticket Number", placeholder="e.g., TI0000001")

        domain_options = [""] + domains if domains else [""]
        domain = st.selectbox("Domain (Optional)", domain_options, format_func=lambda x: "Select a domain..." if x == "" else x)

        context = st.text_area(
            "Ticket Context / Description",
            placeholder="Paste the ticket description, activity report, or problem details here...",
            height=150
        )

        submitted = st.form_submit_button("Analyze Ticket", type="primary", use_container_width=True)

    if submitted:
        if not ticket_number.strip() or not context.strip():
            st.error("Please fill in ticket number and context")
        else:
            with st.spinner("Analyzing ticket..."):
                result = api_post("analyze", {
                    "ticket_number": ticket_number.strip(),
                    "context": context.strip(),
                    "domain": domain if domain else None
                })

            if result:
                # Display result
                is_resolved = result.get("is_resolved")

                if is_resolved is True:
                    st.markdown(f'''
                        <div class="success-box">
                            <h4>✅ Status: Resolved</h4>
                            <p><strong>Ticket:</strong> {result.get("ticket_number", "N/A")}</p>
                            {f'<p><strong>Domain:</strong> {result.get("domain")}</p>' if result.get("domain") else ""}
                        </div>
                    ''', unsafe_allow_html=True)

                    if result.get("cause_summary"):
                        st.markdown("**Root Cause:**")
                        st.info(result["cause_summary"])

                    if result.get("keywords"):
                        st.markdown("**Keywords:**")
                        for keyword in result["keywords"]:
                            st.markdown(f'<span class="keyword-tag">{keyword}</span>', unsafe_allow_html=True)

                    if result.get("resolution_summary"):
                        st.markdown("**Resolution Summary:**")
                        st.info(result["resolution_summary"])

                    if result.get("resolution_steps"):
                        st.markdown("**Resolution Steps:**")
                        for i, step in enumerate(result["resolution_steps"], 1):
                            st.markdown(f"{i}. {step}")

                    # Metadata
                    cols = st.columns(2)
                    with cols[0]:
                        if result.get("embedding_generated"):
                            st.success("✓ Embedding Generated")
                        else:
                            st.warning("⚠ Embedding Not Generated")
                    with cols[1]:
                        if result.get("saved_to_db"):
                            st.success("✓ Saved to Database")
                        else:
                            st.warning("⚠ Not Saved to Database")

                elif is_resolved is False:
                    st.markdown(f'''
                        <div class="error-box">
                            <h4>❌ Status: Unresolved</h4>
                            <p><strong>Ticket:</strong> {result.get("ticket_number", "N/A")}</p>
                            {f'<p><strong>Domain:</strong> {result.get("domain")}</p>' if result.get("domain") else ""}
                        </div>
                    ''', unsafe_allow_html=True)

                    if result.get("analysis"):
                        st.markdown("**Analysis:**")
                        st.write(result["analysis"])
                else:
                    st.markdown(f'''
                        <div class="result-box">
                            <h4>❓ Status: Uncertain</h4>
                            <p><strong>Ticket:</strong> {result.get("ticket_number", "N/A")}</p>
                        </div>
                    ''', unsafe_allow_html=True)

                if result.get("error"):
                    st.error(f"Error: {result['error']}")

# ==================== SEARCH SIMILAR PAGE ====================
elif page == "Search Similar":
    st.header("Search Similar Tickets")

    with st.form("search_form"):
        query = st.text_area(
            "Search Query",
            placeholder="Enter a ticket description or problem statement to find similar tickets...",
            height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            domain_options = [""] + domains if domains else [""]
            domain = st.selectbox("Domain (Optional)", domain_options, format_func=lambda x: "Any domain" if x == "" else x)
        with col2:
            top_k = st.slider("Number of Results", min_value=1, max_value=20, value=5)

        similarity_threshold = st.slider("Similarity Threshold", min_value=0.0, max_value=1.0, value=0.7, step=0.05)

        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

    if submitted:
        if not query.strip():
            st.error("Please enter a search query")
        else:
            with st.spinner("Searching for similar tickets..."):
                results = api_post("search", {
                    "query": query.strip(),
                    "domain": domain if domain else None,
                    "top_k": top_k,
                    "similarity_threshold": similarity_threshold
                })

            if results and results.get("results"):
                st.success(f"Found {len(results['results'])} similar tickets")

                for i, ticket in enumerate(results["results"], 1):
                    similarity = ticket.get("similarity", 0)
                    similarity_pct = round(similarity * 100, 1)

                    with st.expander(f"#{i} - {ticket.get('ticket_number', 'Unknown')} (Similarity: {similarity_pct}%)"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Ticket Number:** {ticket.get('ticket_number', 'N/A')}")
                            st.markdown(f"**Domain:** {ticket.get('domain', 'N/A')}")
                            st.markdown(f"**Similarity:** {similarity_pct}%")
                        with col2:
                            status_color = "green" if ticket.get("is_resolved") else "red"
                            status_text = "Resolved" if ticket.get("is_resolved") else "Unresolved"
                            st.markdown(f"**Status:** :{status_color}[{status_text}]")

                        if ticket.get("cause_summary"):
                            st.markdown("**Root Cause:**")
                            st.write(ticket["cause_summary"])

                        if ticket.get("resolution_summary"):
                            st.markdown("**Resolution:**")
                            st.write(ticket["resolution_summary"])
            else:
                st.info("No similar tickets found")

# ==================== SUGGEST RESOLUTION PAGE ====================
elif page == "Suggest Resolution":
    st.header("Suggest Resolution")

    with st.form("suggest_form"):
        problem_description = st.text_area(
            "Problem Description",
            placeholder="Describe the problem you need to resolve...",
            height=150
        )

        col1, col2 = st.columns(2)
        with col1:
            domain_options = [""] + domains if domains else [""]
            domain = st.selectbox("Domain (Optional)", domain_options, format_func=lambda x: "Any domain" if x == "" else x)
        with col2:
            top_k = st.slider("Number of References", min_value=1, max_value=10, value=5)

        submitted = st.form_submit_button("Get Suggestions", type="primary", use_container_width=True)

    if submitted:
        if not problem_description.strip():
            st.error("Please enter a problem description")
        else:
            with st.spinner("Generating resolution suggestions..."):
                result = api_post("suggest-resolution", {
                    "problem_description": problem_description.strip(),
                    "domain": domain if domain else None,
                    "top_k": top_k
                })

            if result:
                st.markdown("### Suggested Resolution")
                st.markdown(result.get("suggestion", "No suggestion generated"))

                if result.get("references"):
                    st.markdown("---")
                    st.markdown("### Reference Tickets")

                    for ref in result["references"]:
                        with st.expander(f"{ref.get('ticket_number', 'Unknown')} (Similarity: {round(ref.get('similarity', 0) * 100, 1)}%)"):
                            if ref.get("cause_summary"):
                                st.markdown(f"**Cause:** {ref['cause_summary']}")
                            if ref.get("resolution_summary"):
                                st.markdown(f"**Resolution:** {ref['resolution_summary']}")

# Footer
st.markdown('<div class="footer">Ticket RAG System v3.0 | Powered by RAG & LLM</div>', unsafe_allow_html=True)
