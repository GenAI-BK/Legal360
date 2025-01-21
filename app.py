import streamlit as st
from backend import create_case, list_cases, bot,summarization

def main():
    st.sidebar.title("Navigation")
    choice = st.sidebar.selectbox("Choose a page", ["Home", "Create Case", "Chatbot","Summarize"])

    if choice == "Home":
        st.title("Welcome to the Legal Case Management App")
        st.write("Select an option from the sidebar to get started.")
    
    elif choice == "Create Case":
        create_case_page()

    elif choice == "Chatbot":
        chatbot_page()
    elif choice=="Summarize":
        summarize()
        
def create_case_page():

    st.title("Create Case")

    case_name = st.text_input("Case Name")
    uploaded_files = st.file_uploader("Upload Case Files", accept_multiple_files=True, type=['pdf'])

    files_with_tags = []

    if uploaded_files:
        for file in uploaded_files:
            # Use a unique key for each select box based on the file name
            tag = st.selectbox(f"Tag for {file.name}", ["Discovery", "Financial_Statements", "Interogation_Documents","Request_for_admission","Witness_list"], key=file.name)
            # Append a tuple of the file along with its selected tag to the list
            files_with_tags.append((file, tag))

        if st.button("Submit"):
            # Process each file and its tag
            try:
                results = []
                for file, tag in files_with_tags:
                    content = file.getvalue()
                    filename = file.name
                    result = create_case(case_name, filename, content, tag)
                    results.append(result)
                st.success(f"Files processed successfully: {results}")
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
    else:
        st.write("Please upload some PDF files.")

def chatbot_page():
    st.title("Chatbot for Legal Cases")

    if 'selected_case' not in st.session_state:
        st.session_state['selected_case'] = None

    case_list = list_cases()
    selected_case = st.selectbox("Select a Case", case_list)

    # Reset conversation if the case has changed
    if selected_case != st.session_state['selected_case']:
        st.session_state['selected_case'] = selected_case
        st.session_state['conversation_history'] = []

    if 'conversation_history' not in st.session_state:
        st.session_state['conversation_history'] = []

    # with st.form("chat_form"):
    user_input = st.chat_input("Ask a question:")
    # submit_button = st.form_submit_button("Send")

    if  user_input:
        # Here, integrate your chat logic to get a response
        response = bot(user_input,selected_case)  # Placeholder function
        st.session_state['conversation_history'].append((user_input, response))

    if st.session_state['conversation_history']:
        for question, answer in st.session_state['conversation_history']:
            st.write(f"Q: {question}")
            st.write(f"A: {answer}")
            st.markdown("---")  # Separator for readability
def summarize():
    st.title("Summarize Case files")
    case_list = list_cases()
    selected_case = st.selectbox("Select a Case", case_list)
    if st.button("Submit"):
        report=summarization(selected_case)
        st.write(report)
if __name__ == "__main__":
    main()