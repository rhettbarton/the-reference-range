import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

class LabVisualizer:
    """Creates visualizations for lab result data."""
    
    def __init__(self, df):
        """
        Initialize visualizer with processed lab data.
        
        Args:
            df: Processed DataFrame from LabDataProcessor
        """
        self.df = df
    
    def get_latest_results(self, df=None):
        """
        Get the most recent result for each test.
        
        Args:
            df: Optional filtered DataFrame (uses self.df if not provided)
            
        Returns:
            DataFrame with latest results per test
        """
        if df is None:
            df = self.df
        
        # Sort by date and get latest result per test
        latest = df.sort_values('Date').groupby('Standardized Test').last().reset_index()
        latest = latest.sort_values('Date', ascending=False)
        
        return latest
    
    def create_trend_chart(self, test_name):
        """
        Create an interactive trend chart for a specific test.
        
        Args:
            test_name: Name of the test to visualize
            
        Returns:
            Plotly figure object
        """
        # Filter data for the specific test
        test_data = self.df[self.df['Standardized Test'] == test_name].copy()
        test_data = test_data.sort_values('Date')
        
        if len(test_data) == 0:
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Get reference range (use first available)
        ref_min = test_data['Interval Min'].iloc[0]
        ref_max = test_data['Interval Max'].iloc[0]
        units = test_data['Units'].iloc[0]
        
        # Add reference range as shaded area
        if pd.notna(ref_min) and pd.notna(ref_max):
            fig.add_trace(go.Scatter(
                x=test_data['Date'],
                y=[ref_max] * len(test_data),
                fill=None,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=test_data['Date'],
                y=[ref_min] * len(test_data),
                fill='tonexty',
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(0, 255, 0, 0.1)',
                name='Normal Range',
                hovertemplate=f'Normal Range: {ref_min}-{ref_max} {units}<extra></extra>'
            ))
        
        # Add actual results
        colors = ['red' if x else 'blue' for x in test_data['Out of Range']]
        
        fig.add_trace(go.Scatter(
            x=test_data['Date'],
            y=test_data['Result'],
            mode='lines+markers',
            name='Your Results',
            line=dict(color='blue', width=2),
            marker=dict(
                size=10,
                color=colors,
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br>' +
                         f'<b>Result:</b> %{{y}} {units}<br>' +
                         '<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title=f'{test_name} Over Time',
            xaxis_title='Date',
            yaxis_title=f'Result ({units})',
            hovermode='closest',
            template='plotly_white',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add annotations for out-of-range values
        out_of_range_data = test_data[test_data['Out of Range']]
        for _, row in out_of_range_data.iterrows():
            fig.add_annotation(
                x=row['Date'],
                y=row['Result'],
                text="⚠",
                showarrow=False,
                font=dict(size=16, color='red'),
                yshift=15
            )
        
        return fig
    
    def create_category_heatmap(self):
        """
        Create a heatmap showing test results by category over time.
        
        Returns:
            Plotly figure object
        """
        # Get latest result for each test
        latest = self.get_latest_results()
        
        # Group by category
        category_counts = latest.groupby('Test Category').agg({
            'Standardized Test': 'count',
            'Out of Range': 'sum'
        }).reset_index()
        
        category_counts.columns = ['Category', 'Total Tests', 'Out of Range']
        category_counts['In Range'] = category_counts['Total Tests'] - category_counts['Out of Range']
        
        # Create stacked bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='In Range',
            x=category_counts['Category'],
            y=category_counts['In Range'],
            marker_color='green',
            hovertemplate='<b>%{x}</b><br>In Range: %{y}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Out of Range',
            x=category_counts['Category'],
            y=category_counts['Out of Range'],
            marker_color='red',
            hovertemplate='<b>%{x}</b><br>Out of Range: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Test Results by Category (Latest Values)',
            xaxis_title='Category',
            yaxis_title='Number of Tests',
            barmode='stack',
            template='plotly_white',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_multi_test_comparison(self, test_names):
        """
        Create a comparison chart for multiple related tests.
        
        Args:
            test_names: List of test names to compare
            
        Returns:
            Plotly figure object
        """
        if not test_names or len(test_names) == 0:
            return None
        
        fig = go.Figure()
        
        for test_name in test_names:
            test_data = self.df[self.df['Standardized Test'] == test_name].copy()
            test_data = test_data.sort_values('Date')
            
            if len(test_data) > 0:
                fig.add_trace(go.Scatter(
                    x=test_data['Date'],
                    y=test_data['Result'],
                    mode='lines+markers',
                    name=test_name,
                    hovertemplate=f'<b>{test_name}</b><br>' +
                                 'Date: %{x|%Y-%m-%d}<br>' +
                                 'Result: %{y}<br>' +
                                 '<extra></extra>'
                ))
        
        fig.update_layout(
            title='Multiple Test Comparison',
            xaxis_title='Date',
            yaxis_title='Result (normalized)',
            hovermode='closest',
            template='plotly_white',
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_timeline_view(self):
        """
        Create a timeline view showing all tests over time.
        
        Returns:
            Plotly figure object
        """
        # Prepare data for timeline
        timeline_data = self.df.copy()
        timeline_data = timeline_data.sort_values('Date')
        
        # Color by out of range status
        timeline_data['Color'] = timeline_data['Out of Range'].apply(
            lambda x: 'Out of Range' if x else 'In Range'
        )
        
        fig = px.scatter(
            timeline_data,
            x='Date',
            y='Standardized Test',
            color='Color',
            color_discrete_map={'In Range': 'green', 'Out of Range': 'red'},
            hover_data=['Result', 'Units', 'Reference Interval', 'Provider'],
            title='Complete Test Timeline'
        )
        
        fig.update_layout(
            height=max(400, len(timeline_data['Standardized Test'].unique()) * 30),
            template='plotly_white',
            yaxis={'categoryorder': 'category ascending'},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_distribution_chart(self, test_name):
        """
        Create a distribution/histogram of results for a test.
        
        Args:
            test_name: Name of the test to visualize
            
        Returns:
            Plotly figure object
        """
        test_data = self.df[self.df['Standardized Test'] == test_name].copy()
        
        if len(test_data) == 0:
            return None
        
        units = test_data['Units'].iloc[0]
        ref_min = test_data['Interval Min'].iloc[0]
        ref_max = test_data['Interval Max'].iloc[0]
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=test_data['Result'],
            name='Results',
            marker_color='lightblue',
            hovertemplate='Range: %{x}<br>Count: %{y}<extra></extra>'
        ))
        
        # Add reference range lines
        if pd.notna(ref_min):
            fig.add_vline(
                x=ref_min,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Min: {ref_min}"
            )
        
        if pd.notna(ref_max):
            fig.add_vline(
                x=ref_max,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Max: {ref_max}"
            )
        
        fig.update_layout(
            title=f'Distribution of {test_name}',
            xaxis_title=f'Result ({units})',
            yaxis_title='Frequency',
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return fig
