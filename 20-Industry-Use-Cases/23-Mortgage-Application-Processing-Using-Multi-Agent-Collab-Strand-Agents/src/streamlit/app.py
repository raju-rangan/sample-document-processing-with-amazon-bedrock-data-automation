import streamlit as st
import streamlit_antd_components as sac
from config import APP_TITLE, MAX_FILE_SIZE_MB, ALLOWED_FILE_TYPES
from aws_utils import upload_file_to_s3, get_all_applications
from data_utils import parse_dynamodb_item

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏠")
    
    sac.divider(label=APP_TITLE, icon='house', align='center', color='blue', size='lg', key='main_divider')
    
    selected = sac.menu([
        sac.MenuItem('applications', icon='list-ul', children=[
            sac.MenuItem('view-all', icon='eye'),
        ]),
        sac.MenuItem('upload', icon='cloud-upload'),
    ], format_func='title', open_all=True, key='main_menu')
    
    st.divider()
    
    if selected == 'upload':
        upload_page()
    else:
        applications_page()

def upload_page():
    sac.alert(label='Upload Mortgage Application', 
              description='Select a PDF file to upload', 
              color='info', banner=True, icon=True, key='upload_alert')
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Choose PDF file", type=ALLOWED_FILE_TYPES)
        
        if uploaded_file:
            with st.container():
                sac.result(
                    label='File Selected',
                    description=f'**{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)',
                    status='info',
                    key='file_selected_result'
                )
                
                if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    sac.alert(label='File Too Large', 
                             description=f'Maximum size is {MAX_FILE_SIZE_MB}MB', 
                             color='error',
                             key='file_too_large_alert')
                else:
                    if st.button("📤 Upload", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Uploading..."):
                                file_key = upload_file_to_s3(uploaded_file.getvalue(), uploaded_file.name)
                            
                            sac.result(
                                label='Upload Successful!',
                                description=f'File uploaded to: `{file_key}`',
                                status='success',
                                key='upload_success_result'
                            )
                            
                        except Exception as e:
                            sac.alert(label='Upload Failed', 
                                     description=str(e), 
                                     color='error',
                                     key='upload_failed_alert')
    
    with col2:
        with st.container(border=True):
            st.write("**Upload Guidelines**")
            st.write("• PDF files only")
            st.write("• Max 10MB file size") 
            st.write("• Files stored securely in S3")

def applications_page():
    try:
        applications = get_all_applications()
        total_apps = len(applications)
        pending_apps = len([app for app in applications if 'status' in app and app['status']['S'] == 'pending'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric('Total Applications', str(total_apps))
        
        with col2:
            st.metric('Pending Review', str(pending_apps))
        
        with col3:
            if applications:
                total_loan = sum([float(app['loan_amount']['N']) for app in applications if 'loan_amount' in app])
                st.metric('Total Loan Value', f'${total_loan:,.0f}')
        
        with col4:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        st.divider()
        
        if not applications:
            sac.result(
                label='No Applications Found',
                description='No mortgage applications in the database',
                status='empty',
                key='no_applications_result'
            )
            return
        
        for i, app in enumerate(applications):
            show_application_card(app, i)
            
    except Exception as e:
        sac.alert(label='Error Loading Applications', 
                 description=str(e), 
                 color='error', banner=True,
                 key='error_loading_alert')

def show_application_card(app, index):
    parsed_app = parse_dynamodb_item(app)
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"👤 {parsed_app.get('borrower_name', 'Unknown')}")
            st.caption(f"ID: {parsed_app.get('application_id', 'N/A')[:8]}...")
        
        with col2:
            status = parsed_app.get('status', 'unknown').title()
            color = 'orange' if status == 'Pending' else 'green' if status == 'Approved' else 'blue'
            sac.tags([status], color=color, size='md', key=f'status_tag_{index}')
        
        with col3:
            created = parsed_app.get('created_at', '')[:10] if parsed_app.get('created_at') else 'N/A'
            st.caption(f"📅 {created}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            loan_amount = parsed_app.get('loan_amount', 0)
            st.metric('Loan Amount', f'${loan_amount:,.0f}')
        
        with col2:
            loan_info = parsed_app.get('loan_information', {})
            property_value = 0
            if isinstance(loan_info, dict) and 'property' in loan_info:
                property_info = loan_info['property']
                if isinstance(property_info, dict):
                    property_value = property_info.get('value', 0)
            st.metric('Property Value', f'${property_value:,.0f}')
        
        with col3:
            personal_info = parsed_app.get('personal_information', {})
            dependents = personal_info.get('dependents', 0) if isinstance(personal_info, dict) else 0
            st.metric('Dependents', str(dependents))
        
        tabs = sac.tabs([
            sac.TabsItem(label='Personal', icon='person'),
            sac.TabsItem(label='Property', icon='house'),
            sac.TabsItem(label='Employment', icon='briefcase'),
            sac.TabsItem(label='Financial', icon='currency-dollar'),
        ], align='center', variant='outline', key=f'app_tabs_{index}')
        
        if tabs == 'Personal':
            show_personal_info(parsed_app, personal_info)
        elif tabs == 'Property':
            show_property_info(loan_info)
        elif tabs == 'Employment':
            show_employment_info(parsed_app.get('employment_history', []))
        elif tabs == 'Financial':
            show_financial_info(parsed_app.get('assets', {}), parsed_app.get('liabilities', []))
        
        st.divider()

def show_personal_info(parsed_app, personal_info):
    if isinstance(personal_info, dict):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information**")
            st.write(f"• SSN: {parsed_app.get('ssn', 'N/A')}")
            st.write(f"• Date of Birth: {personal_info.get('date_of_birth', 'N/A')}")
            st.write(f"• Marital Status: {personal_info.get('marital_status', 'N/A')}")
            st.write(f"• Citizenship: {personal_info.get('citizenship', 'N/A')}")
        
        with col2:
            contact = personal_info.get('contact', {})
            if isinstance(contact, dict):
                st.write("**Contact Information**")
                st.write(f"• Email: {contact.get('email', 'N/A')}")
                st.write(f"• Phone: {contact.get('cell_phone', contact.get('home_phone', 'N/A'))}")
                st.write(f"• Address: {contact.get('address', 'N/A')}")

def show_property_info(loan_info):
    if isinstance(loan_info, dict):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Loan Details**")
            st.write(f"• Purpose: {loan_info.get('purpose', 'N/A')}")
            st.write(f"• Occupancy: {loan_info.get('occupancy', 'N/A')}")
        
        with col2:
            if 'property' in loan_info and isinstance(loan_info['property'], dict):
                property_info = loan_info['property']
                st.write("**Property Details**")
                st.write(f"• Address: {property_info.get('address', 'N/A')}")
                st.write(f"• Value: ${property_info.get('value', 0):,.0f}")

def show_employment_info(employment):
    if employment:
        for i, emp in enumerate(employment):
            if isinstance(emp, dict):
                with st.expander(f"Job {i+1}: {emp.get('employer', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Position:** {emp.get('position', 'N/A')}")
                        st.write(f"**Start Date:** {emp.get('start_date', 'N/A')}")
                        if 'end_date' in emp:
                            st.write(f"**End Date:** {emp.get('end_date', 'N/A')}")
                    with col2:
                        st.write(f"**Base Income:** ${emp.get('monthly_base_income', 0):,.0f}/month")
                        if 'monthly_bonus_income' in emp:
                            st.write(f"**Bonus Income:** ${emp.get('monthly_bonus_income', 0):,.0f}/month")
    else:
        st.info("No employment history available")

def show_financial_info(assets, liabilities):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Assets**")
        if isinstance(assets, dict) and 'accounts' in assets:
            accounts = assets['accounts']
            if accounts:
                for account in accounts:
                    if isinstance(account, dict):
                        st.write(f"• {account.get('institution', 'N/A')} ({account.get('type', 'N/A')}): ${account.get('value', 0):,.0f}")
            else:
                st.info("No assets listed")
        else:
            st.info("No assets information")
    
    with col2:
        st.write("**Liabilities**")
        if liabilities:
            for liability in liabilities:
                if isinstance(liability, dict):
                    st.write(f"• {liability.get('institution', 'N/A')} ({liability.get('type', 'N/A')}): ${liability.get('balance', 0):,.0f}")
        else:
            st.info("No liabilities listed")

if __name__ == "__main__":
    main()
