import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

class LabVisualizer:
    """Creates visualizations for lab result data."""
    
    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initialize visualizer with processed lab data.
        
        Args:
            df: Processed DataFrame from LabDataProcessor
        """
        self.df = df
    
    def get_latest_results(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
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
    
    def create_trend_chart(self, test_name: str) -> Optional[go.Figure]:
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
    
    def create_category_heatmap(self) -> Optional[go.Figure]:
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
    
    def create_comparison_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all tests.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_tests': len(self.df),
            'unique_tests': self.df['Standardized Test'].nunique(),
            'out_of_range_count': self.df['Out of Range'].sum(),
            'categories': self.df['Test Category'].unique().tolist()
        }
