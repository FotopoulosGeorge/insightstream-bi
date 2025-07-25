import pandas as pd
import numpy as np
import streamlit as st
from sklearn.datasets import load_iris, load_wine, make_classification
from datetime import datetime, timedelta
import os

class DemoDatasets:
    """
    Provides curated test datasets for demo purposes
    """
    
    @staticmethod
    def is_deployed():
        import os
        import sys
        
        # Method 1: Check for Streamlit Cloud specific paths
        try:
            current_path = os.getcwd()
            python_path = sys.executable
            
            # Streamlit Cloud characteristics
            streamlit_indicators = [
                '/mount/src' in current_path,
                '/app' in current_path,
                'streamlit' in current_path.lower(),
                'site-packages/streamlit' in str(sys.path),
                '/opt/conda' in python_path,  # Streamlit Cloud uses conda
            ]
            
            if any(streamlit_indicators):
                return True
                
        except Exception:
            pass
        
        # Method 2: Check for cloud-specific Python environment
        try:
            # Streamlit Cloud has specific Python installation patterns
            if '/opt/conda/bin/python' in sys.executable:
                return True
            if '/usr/local/bin/python' in sys.executable and os.path.exists('/app'):
                return True
        except Exception:
            pass
        
        # Method 3: Check for lack of typical local development indicators
        try:
            # Local development usually has these
            local_indicators = [
                os.path.exists(os.path.expanduser('~/.bashrc')),
                os.path.exists(os.path.expanduser('~/.profile')),
                os.path.exists('/Users'),  # macOS
                os.path.exists('/home') and os.path.exists('/usr/local'),  # Linux desktop
            ]
            
            # If none of these exist, probably in a minimal container (cloud)
            if not any(local_indicators):
                return True
                
        except Exception:
            pass
        
        # Method 4: Check for specific file system characteristics
        try:
            # Streamlit Cloud has specific directory structure
            if os.path.exists('/app') and not os.path.exists('/home'):
                return True
            if os.path.exists('/opt/conda') and not os.path.exists('/usr/local/bin'):
                return True
        except Exception:
            pass
        
        # Method 5: Check environment size 
        try:
            env_vars = len(os.environ)
            # Cloud environments typically have fewer environment variables
            if env_vars < 50:  # Arbitrary threshold
                return True
        except Exception:
            pass
        
        # Default: assume local 
        return False
    
    @staticmethod
    def get_available_datasets():
        """
        Get list of available demo datasets
        """
        return {
            "🌸 Iris Flowers": {
                "description": "Classic classification dataset - predict flower species",
                "type": "Classification",
                "samples": 150,
                "features": 4,
                "target": "Species",
                "use_cases": ["Supervised Learning", "Clustering", "Visualization"]
            },
            "🍷 Wine Quality": {
                "description": "Wine classification - predict wine type from chemical properties", 
                "type": "Classification",
                "samples": 178,
                "features": 13,
                "target": "Wine Type",
                "use_cases": ["Supervised Learning", "Feature Engineering", "AutoML"]
            },
            "🏠 California Housing": {
                "description": "Regression dataset - predict house values in California",
                "type": "Regression", 
                "samples": 20640,
                "features": 8,
                "target": "House Price",
                "use_cases": ["Regression", "Feature Engineering", "AutoML"]
            },
            "📈 Sales Time Series": {
                "description": "Synthetic sales data with trends and seasonality",
                "type": "Time Series",
                "samples": 365,
                "features": 3,
                "target": "Sales",
                "use_cases": ["Time Series Forecasting", "Trend Analysis"]
            },
            "🛒 E-commerce Transactions": {
                "description": "Synthetic transaction data for pattern mining",
                "type": "Transactional",
                "samples": 1000,
                "features": 8,
                "target": "Purchase Amount",
                "use_cases": ["Pattern Mining", "Association Rules", "Anomaly Detection"]
            }
        }
    
    @staticmethod
    def load_dataset(dataset_name):
        """
        Load the specified demo dataset
        """
        if dataset_name == "🌸 Iris Flowers":
            return DemoDatasets._load_iris()
        elif dataset_name == "🍷 Wine Quality":
            return DemoDatasets._load_wine()
        elif dataset_name == "🏠 California Housing":
            return DemoDatasets._load_california_housing()
        elif dataset_name == "📈 Sales Time Series":
            return DemoDatasets._create_time_series()
        elif dataset_name == "🛒 E-commerce Transactions":
            return DemoDatasets._create_ecommerce_data()
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
    
    @staticmethod
    def _load_iris():
        """Load Iris dataset"""
        iris = load_iris()
        df = pd.DataFrame(iris.data, columns=iris.feature_names)
        df['Species'] = pd.Categorical.from_codes(iris.target, iris.target_names)
        return df
    
    @staticmethod
    def _load_wine():
        """Load Wine dataset"""
        wine = load_wine()
        df = pd.DataFrame(wine.data, columns=wine.feature_names)
        df['Wine_Type'] = pd.Categorical.from_codes(wine.target, wine.target_names)
        return df
    
    @staticmethod
    def _load_california_housing():
        """Load California Housing dataset"""
        try:
            from sklearn.datasets import fetch_california_housing
            housing = fetch_california_housing()
            df = pd.DataFrame(housing.data, columns=housing.feature_names)
            df['House_Price'] = housing.target
            return df
        except ImportError:
            # Fallback to synthetic housing data
            return DemoDatasets._create_housing_data()
    
    @staticmethod
    def _create_time_series():
        """Create synthetic time series data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # Create trend + seasonality + noise
        trend = np.linspace(1000, 1500, len(dates))
        seasonal = 200 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
        weekly = 50 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
        noise = np.random.normal(0, 50, len(dates))
        
        sales = trend + seasonal + weekly + noise
        
        df = pd.DataFrame({
            'Date': dates,
            'Sales': sales,
            'Month': dates.month,
            'DayOfWeek': dates.dayofweek,
            'IsWeekend': (dates.dayofweek >= 5).astype(int)
        })
        
        return df
    
    @staticmethod
    def _create_ecommerce_data():
        """Create synthetic e-commerce transaction data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Create realistic e-commerce data
        customer_ids = np.random.randint(1, 201, n_samples)
        products = np.random.choice(['Electronics', 'Clothing', 'Books', 'Home', 'Sports'], n_samples)
        categories = np.random.choice(['Premium', 'Standard', 'Budget'], n_samples)
        
        # Create correlated features
        base_price = np.where(products == 'Electronics', 500,
                     np.where(products == 'Clothing', 80,
                     np.where(products == 'Books', 25,
                     np.where(products == 'Home', 150, 60))))
        
        price_multiplier = np.where(categories == 'Premium', 1.5,
                           np.where(categories == 'Standard', 1.0, 0.7))
        
        prices = base_price * price_multiplier * np.random.uniform(0.8, 1.2, n_samples)
        quantities = np.random.poisson(2, n_samples) + 1
        
        df = pd.DataFrame({
            'Customer_ID': customer_ids,
            'Product_Category': products,
            'Product_Tier': categories,
            'Unit_Price': np.round(prices, 2),
            'Quantity': quantities,
            'Purchase_Amount': np.round(prices * quantities, 2),
            'Day_of_Week': np.random.randint(0, 7, n_samples),
            'Hour_of_Day': np.random.randint(8, 22, n_samples),
            'Is_Weekend': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
        })
        
        return df
    
    @staticmethod
    def _create_housing_data():
        """Create synthetic housing data if Boston dataset unavailable"""
        np.random.seed(42)
        n_samples = 500
        
        # Create realistic housing features
        rooms = np.random.normal(6, 1.5, n_samples)
        age = np.random.uniform(5, 100, n_samples)
        distance = np.random.exponential(5, n_samples)
        crime_rate = np.random.exponential(3, n_samples)
        
        # Create correlated price
        price = (rooms * 50 - age * 2 - distance * 10 - crime_rate * 5 + 
                np.random.normal(200, 50, n_samples))
        price = np.maximum(price, 50)  # Minimum price
        
        df = pd.DataFrame({
            'Rooms': np.round(rooms, 1),
            'Age_Years': np.round(age, 0),
            'Distance_to_Center': np.round(distance, 2),
            'Crime_Rate': np.round(crime_rate, 3),
            'Tax_Rate': np.random.uniform(200, 800, n_samples),
            'Pupil_Teacher_Ratio': np.random.uniform(12, 22, n_samples),
            'House_Price': np.round(price, 1)
        })
        
        return df