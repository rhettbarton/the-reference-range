import streamlit as st
import pandas as pd
from datetime import datetime
from data_processor import LabDataProcessor
from visualizations import LabVisualizer
import plotly.graph_objects as go

st.set_page_config(
    page_title="The Reference Range",
    page_icon="🔬",
    layout="wide"
)

# Initialize session state for tracking selected test
if 'selected_test' not in st.session_state:
    st.session_state.selected_test = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

def main():
    st.title("🔬 The Reference Range")
    st.markdown("Upload your lab results CSV to generate personalized health visualizations")
    
    # Sidebar for file upload and crosswalk
    with st.sidebar:
        st.header("📁 Data Upload")
        
        # Lab results upload
        lab_file = st.file_uploader(
            "Upload Lab Results CSV",
            type=['csv'],
            help="CSV must contain: Date, Test, Result, Units, Reference Interval, Interval Min, Interval Max, Provider, Note"
        )
        
        # Crosswalk upload
        crosswalk_file = st.file_uploader(
            "Upload Test Crosswalk CSV (Optional)",
            type=['csv'],
            help="CSV with columns: Original Test Name, Standardized Test Name, Test Category"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("This app helps you visualize and understand your lab results over time.")
    
    # Main content area
    if lab_file is not None:
        try:
            # Initialize processor
            processor = LabDataProcessor(crosswalk_file)
            
            # Load and process data
            df = processor.load_lab_data(lab_file)
            
            if df is not None and len(df) > 0:
                st.success(f"✅ Loaded {len(df)} lab results")
                
                # Display data summary
                col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.5, 1.1])
                with col1:
                    st.metric("Total Tests", len(df))
                with col2:
                    st.metric("Unique Tests", df['Standardized Test'].nunique())
                with col3:
                    st.metric("Date Range", f"{df['Date'].min().strftime('%Y-%m')} to {df['Date'].max().strftime('%Y-%m')}")
                with col4:
                    out_of_range = df['Out of Range'].sum()
                    st.metric("Out of Range", out_of_range, delta=None, delta_color="inverse")
                
                # Tabs for different views
                col_tabs = st.columns(4)
                with col_tabs[0]:
                    if st.button("📊 Overview", use_container_width=True, key="tab_overview"):
                        st.session_state.active_tab = 0
                with col_tabs[1]:
                    if st.button("📈 Trends", use_container_width=True, key="tab_trends"):
                        st.session_state.active_tab = 1
                with col_tabs[2]:
                    if st.button("🔍 Detailed Data", use_container_width=True, key="tab_detailed"):
                        st.session_state.active_tab = 2
                with col_tabs[3]:
                    if st.button("📥 Export", use_container_width=True, key="tab_export"):
                        st.session_state.active_tab = 3
                
                st.markdown("---")
                
                if st.session_state.active_tab == 0:
                    st.header("Recent Results Overview")
                    visualizer = LabVisualizer(df)
                    
                    # Filters
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        categories = sorted(df['Test Category'].unique())
                        selected_category = st.selectbox("Filter by Category", ["All"] + categories)
                    
                    with col2:
                        min_date = df['Date'].min()
                        max_date = df['Date'].max()
                        date_start = st.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
                    
                    with col3:
                        date_end = st.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)
                    
                    # Apply filters
                    filtered_df = df[
                        (df['Date'].dt.date >= date_start) & 
                        (df['Date'].dt.date <= date_end)
                    ]
                    
                    if selected_category != "All":
                        filtered_df = filtered_df[filtered_df['Test Category'] == selected_category]
                    
                    st.markdown("---")
                    
                    # Category comparison
                    st.subheader("Category Overview")
                    filtered_visualizer = LabVisualizer(filtered_df)
                    category_fig = filtered_visualizer.create_category_heatmap()
                    if category_fig:
                        st.plotly_chart(category_fig, use_container_width=True)
                    
                    # Latest results summary
                    st.subheader("Latest Results")
                    latest_results = visualizer.get_latest_results(filtered_df)
                    
                    # Display latest results as cards
                    for idx, row in latest_results.iterrows():
                        test_name = row['Standardized Test']
                        status_emoji = "🔴" if row['Out of Range'] else "🟢"
                        
                        # Create columns for layout
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**{status_emoji} {test_name}**")
                            st.markdown(f"{row['Result']} {row['Units']} (Ref: {row['Reference Interval']})")
                            if row['Trend']:
                                st.markdown(f"*Trend: {row['Trend']}*")
                        
                        with col2:
                            st.markdown(f"*{row['Date'].strftime('%Y-%m-%d')}*")
                            st.markdown(f"*{row['Test Category']}*")
                        
                        # Create a mini trend chart if the test has history
                        test_history = df[df['Standardized Test'] == test_name]
                        if len(test_history) > 1:
                            test_history = test_history.sort_values('Date')
                            # Create mini trend chart
                            mini_fig = go.Figure()
                            
                            # Add reference range band (horizontal band)
                            interval_min = test_history['Interval Min'].iloc[0]
                            interval_max = test_history['Interval Max'].iloc[0]
                            
                            mini_fig.add_hrect(
                                y0=interval_min,
                                y1=interval_max,
                                fillcolor="green",
                                opacity=0.1,
                                layer="below",
                                line_width=0,
                            )
                            
                            mini_fig.add_trace(go.Scatter(
                                x=test_history['Date'],
                                y=test_history['Result'],
                                mode='lines+markers',
                                name=test_name,
                                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Result: %{y}<extra></extra>'
                            ))
                            mini_fig.update_layout(
                                height=200,
                                margin=dict(l=40, r=20, t=20, b=40),
                                hovermode='x unified',
                                showlegend=False,
                                template='plotly_white'
                            )
                            
                            # Clickable chart
                            if st.button("Click to view full trend →", key=f"trend_{idx}", use_container_width=True):
                                st.session_state.selected_test = test_name
                                st.session_state.active_tab = 1
                                st.rerun()
                            
                            st.plotly_chart(mini_fig, use_container_width=True, config={'displayModeBar': False})
                        
                        st.markdown("---")
                
                elif st.session_state.active_tab == 1:
                    st.header("Trend Analysis")
                    visualizer = LabVisualizer(df)
                    
                    # Test selector for trend analysis
                    tests_with_history = df.groupby('Standardized Test').size()
                    tests_with_history = tests_with_history[tests_with_history > 1].index.tolist()
                    
                    if tests_with_history:
                        # Use selected test from session state if available
                        default_test = st.session_state.selected_test if st.session_state.selected_test in tests_with_history else sorted(tests_with_history)[0]
                        selected_test = st.selectbox("Select Test to View Trend", sorted(tests_with_history), index=sorted(tests_with_history).index(default_test))
                        
                        if selected_test:
                            # Generate trend chart
                            fig = visualizer.create_trend_chart(selected_test)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Show historical data table for this test
                            st.subheader("Historical Values")
                            test_history = df[df['Standardized Test'] == selected_test].sort_values('Date', ascending=False)
                            st.dataframe(
                                test_history[['Date', 'Result', 'Units', 'Reference Interval', 'Out of Range', 'Provider']],
                                hide_index=True,
                                use_container_width=True
                            )
                    else:
                        st.info("No tests with multiple results found. Upload more historical data to see trends.")
                
                elif st.session_state.active_tab == 2:
                    st.header("Detailed Data View")
                    
                    # Filters
                    col1, col2 = st.columns(2)
                    with col1:
                        category_filter = st.multiselect(
                            "Filter by Category",
                            options=sorted(df['Test Category'].unique()),
                            default=None
                        )
                    with col2:
                        range_filter = st.selectbox(
                            "Filter by Range Status",
                            options=["All", "In Range", "Out of Range"]
                        )
                    
                    # Apply filters
                    filtered_data = df.copy()
                    if category_filter:
                        filtered_data = filtered_data[filtered_data['Test Category'].isin(category_filter)]
                    if range_filter == "In Range":
                        filtered_data = filtered_data[~filtered_data['Out of Range']]
                    elif range_filter == "Out of Range":
                        filtered_data = filtered_data[filtered_data['Out of Range']]
                    
                    # Display filtered data
                    st.dataframe(
                        filtered_data.sort_values('Date', ascending=False),
                        hide_index=True,
                        use_container_width=True
                    )
                
                elif st.session_state.active_tab == 3:
                    st.header("Export Data")
                    st.markdown("Download your enhanced lab data with standardized test names and categories.")
                    
                    # Prepare export data
                    export_df = df.copy()
                    csv = export_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download Enhanced CSV",
                        data=csv,
                        file_name=f"enhanced_lab_results_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
                    st.info("The exported file includes standardized test names, categories, and out-of-range indicators.")
            
            else:
                st.error("No data found in the uploaded file. Please check the file format.")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.error("Please ensure your CSV has the required columns: Date, Test, Result, Units, Reference Interval, Interval Min, Interval Max, Provider, Note")
    
    else:
        # Show instructions when no file is uploaded
        st.info("👆 Upload your lab results CSV file to get started")
        
        with st.expander("📋 Required CSV Format"):
            st.markdown("""
            Your CSV file must contain the following columns:
            - **Date**: Date of the test (YYYY-MM-DD format preferred)
            - **Test**: Name of the lab test
            - **Result**: Numeric or text result
            - **Units**: Measurement units
            - **Reference Interval**: Normal range as text (e.g., "50-100")
            - **Interval Min**: Minimum normal value
            - **Interval Max**: Maximum normal value
            - **Provider**: Healthcare provider or lab name
            - **Note**: Any additional notes (can be empty)
            """)
        
        with st.expander("🔄 Test Crosswalk (Optional)"):
            st.markdown("""
            Upload a crosswalk CSV to standardize test names and assign categories.
            
            Required columns:
            - **Original Test Name**: Test name as it appears in your lab results
            - **Standardized Test Name**: Preferred standardized name
            - **Test Category**: Category for grouping (e.g., "Lipid Panel", "Kidney Function")
            
            If no crosswalk is provided, the app will use the original test names and attempt basic categorization.
            """)
        
        # Sample data preview
        with st.expander("📄 Sample Data Format"):
            sample_data = pd.DataFrame({
                'Date': ['2024-01-15', '2024-01-15', '2024-06-20'],
                'Test': ['Cholesterol, Total', 'HDL Cholesterol', 'Glucose'],
                'Result': [195, 52, 98],
                'Units': ['mg/dL', 'mg/dL', 'mg/dL'],
                'Reference Interval': ['<200', '>40', '70-100'],
                'Interval Min': [0, 40, 70],
                'Interval Max': [200, 999, 100],
                'Provider': ['Quest Diagnostics', 'Quest Diagnostics', 'LabCorp'],
                'Note': ['', '', 'Fasting']
            })
            st.dataframe(sample_data, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
