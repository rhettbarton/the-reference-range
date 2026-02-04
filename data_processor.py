import pandas as pd
import numpy as np
from datetime import datetime
import io
from typing import Optional, Dict, Any

class LabDataProcessor:
    """Processes lab result data, validates format, and enriches with crosswalk data."""
    
    REQUIRED_COLUMNS = [
        'Date', 'Test', 'Result', 'Units', 'Reference Interval',
        'Interval Min', 'Interval Max', 'Provider', 'Note'
    ]
    
    def __init__(self, crosswalk_file: Optional[Any] = None) -> None:
        """
        Initialize the processor with optional crosswalk data.
        
        Args:
            crosswalk_file: File object containing crosswalk CSV
        """
        self.crosswalk: Optional[pd.DataFrame] = None
        self.crosswalk_dict: Dict[str, Dict[str, str]] = {}
        if crosswalk_file is not None:
            self.load_crosswalk(crosswalk_file)
    
    def load_crosswalk(self, crosswalk_file: Any) -> bool:
        """Load and validate crosswalk file."""
        try:
            self.crosswalk = pd.read_csv(crosswalk_file)
            
            # Validate crosswalk columns
            required_cols = ['Original Test Name', 'Standardized Test Name', 'Test Category']
            missing_cols = [col for col in required_cols if col not in self.crosswalk.columns]
            
            if missing_cols:
                raise ValueError(f"Crosswalk missing required columns: {missing_cols}")
            
            # Create lookup dictionary for faster processing
            self.crosswalk_dict = {}
            for _, row in self.crosswalk.iterrows():
                original = str(row['Original Test Name']).strip()
                self.crosswalk_dict[original.lower()] = {
                    'standardized': row['Standardized Test Name'],
                    'category': row['Test Category']
                }
            
            return True
        
        except Exception as e:
            raise ValueError(f"Error loading crosswalk: {str(e)}")
    
    def load_lab_data(self, lab_file: Any) -> Optional[pd.DataFrame]:
        """
        Load and process lab results CSV.
        
        Args:
            lab_file: File object containing lab results CSV
            
        Returns:
            Processed DataFrame with enriched data
        """
        try:
            # Read CSV
            df = pd.read_csv(lab_file)
            
            # Validate required columns
            missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"CSV missing required columns: {missing_cols}")
            
            # Process the data
            df = self._clean_data(df)
            df = self._enrich_data(df)
            df = self._calculate_flags(df)
            
            return df
        
        except Exception as e:
            raise ValueError(f"Error loading lab data: {str(e)}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data types."""
        # Parse dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Convert numeric columns
        df['Result'] = pd.to_numeric(df['Result'], errors='coerce')
        df['Interval Min'] = pd.to_numeric(df['Interval Min'], errors='coerce')
        df['Interval Max'] = pd.to_numeric(df['Interval Max'], errors='coerce')
        
        # Clean string columns
        df['Test'] = df['Test'].astype(str).str.strip()
        df['Units'] = df['Units'].astype(str).str.strip()
        df['Provider'] = df['Provider'].astype(str).str.strip()
        df['Note'] = df['Note'].fillna('').astype(str).str.strip()
        
        # Remove rows with invalid dates or missing test names
        df = df.dropna(subset=['Date', 'Test'])
        
        return df
    
    def _enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich data with standardized test names and categories."""
        if self.crosswalk is not None:
            # Apply crosswalk mapping
            df['Standardized Test'] = df['Test'].apply(self._map_test_name)
            df['Test Category'] = df['Test'].apply(self._map_test_category)
        else:
            # Use original test names and basic categorization
            df['Standardized Test'] = df['Test']
            df['Test Category'] = df['Test'].apply(self._auto_categorize)
        
        return df
    
    def _map_test_name(self, test_name: str) -> str:
        """Map test name using crosswalk."""
        lookup_key = str(test_name).strip().lower()
        if lookup_key in self.crosswalk_dict:
            return self.crosswalk_dict[lookup_key]['standardized']
        return test_name  # Return original if not found
    
    def _map_test_category(self, test_name: str) -> str:
        """Map test category using crosswalk."""
        lookup_key = str(test_name).strip().lower()
        if lookup_key in self.crosswalk_dict:
            return self.crosswalk_dict[lookup_key]['category']
        return 'Other'  # Default category
    
    def _auto_categorize(self, test_name: str) -> str:
        """
        Attempt basic categorization when no crosswalk is provided.
        This is a simple rule-based approach.
        """
        test_lower = str(test_name).lower()
        
        # Lipid panel
        if any(term in test_lower for term in ['cholesterol', 'hdl', 'ldl', 'triglyceride', 'lipid']):
            return 'Lipid Panel'
        
        # Metabolic/Blood Sugar
        elif any(term in test_lower for term in ['glucose', 'a1c', 'hemoglobin a1c', 'hba1c']):
            return 'Metabolic'
        
        # Kidney Function
        elif any(term in test_lower for term in ['creatinine', 'bun', 'egfr', 'kidney', 'urea']):
            return 'Kidney Function'
        
        # Liver Function
        elif any(term in test_lower for term in ['alt', 'ast', 'alp', 'bilirubin', 'liver', 'albumin']):
            return 'Liver Function'
        
        # Thyroid
        elif any(term in test_lower for term in ['tsh', 'thyroid', 't3', 't4']):
            return 'Thyroid'
        
        # Complete Blood Count
        elif any(term in test_lower for term in ['wbc', 'rbc', 'hemoglobin', 'hematocrit', 'platelet', 'mcv', 'mch']):
            return 'Complete Blood Count'
        
        # Electrolytes
        elif any(term in test_lower for term in ['sodium', 'potassium', 'chloride', 'co2', 'calcium']):
            return 'Electrolytes'
        
        # Vitamins
        elif any(term in test_lower for term in ['vitamin', 'b12', 'folate', 'vit ']):
            return 'Vitamins'
        
        else:
            return 'Other'
    
    def _calculate_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate whether results are out of range and identify trends."""
        def is_out_of_range(row):
            """Check if a result is outside the reference interval."""
            try:
                result = row['Result']
                min_val = row['Interval Min']
                max_val = row['Interval Max']
                
                # Skip if any value is missing
                if pd.isna(result) or pd.isna(min_val) or pd.isna(max_val):
                    return False
                
                # Check if out of range
                return result < min_val or result > max_val
            
            except (ValueError, TypeError):
                return False
        
        df['Out of Range'] = df.apply(is_out_of_range, axis=1)
        
        # Calculate trend for tests with multiple results
        df['Trend'] = ''
        for test_name in df['Standardized Test'].unique():
            try:
                test_data = df[df['Standardized Test'] == test_name].sort_values('Date')
                
                if len(test_data) >= 2:
                    # Get last two results
                    results = test_data['Result'].dropna()
                    if len(results) >= 2:
                        last_result = results.iloc[-1]
                        previous_result = results.iloc[-2]
                        
                        if pd.notna(last_result) and pd.notna(previous_result):
                            if last_result > previous_result * 1.05:  # 5% threshold
                                trend = '↑ Increasing'
                            elif last_result < previous_result * 0.95:
                                trend = '↓ Decreasing'
                            else:
                                trend = '→ Stable'
                            
                            # Update only the most recent result
                            most_recent_idx = test_data.index[-1]
                            df.loc[most_recent_idx, 'Trend'] = trend
            
            except Exception:
                # Skip trend calculation for this test if any error occurs
                continue
        
        return df
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the dataset."""
        stats = {
            'total_tests': len(df),
            'unique_tests': df['Standardized Test'].nunique(),
            'date_range': (df['Date'].min(), df['Date'].max()),
            'out_of_range_count': df['Out of Range'].sum(),
            'categories': df['Test Category'].value_counts().to_dict(),
            'providers': df['Provider'].value_counts().to_dict()
        }
        return stats
