import streamlit as st

# Page config
st.set_page_config(page_title="Support - MedDor", page_icon="💬", layout="centered")

# Header
st.title("Support & Feedback")

# About Project Section
st.markdown("""
### About MedDor Notes
MedDor Notes is a hobby project aimed at providing doctors with a cost-effective solution for their daily practice. 
Our goal is simple: create an easy-to-use interface that connects directly with various AI services, eliminating 
the hassle of managing multiple API credits and integrations.

### Why MedDor?
- 🎯 Simplified AI access for medical professionals
- 💰 Cost-effective solution
- 🔄 Direct integration with various AI services
- 🎨 Clean, simple user interface

### Support & Suggestions
Visit our feedback portal at [meddornotes.featurebase.app](https://meddornotes.featurebase.app/) to:
- Report issues
- Submit feature requests
- Share your suggestions
- Ask questions

### Project Vision
We're constantly looking for ways to improve while maintaining simplicity. If you have ideas for small improvements 
that align with our goal of keeping things simple and effective, we'd love to hear them!
""")

# Footer
st.markdown("---")
st.markdown("Thank you for being part of the MedDor community! 🌟")
