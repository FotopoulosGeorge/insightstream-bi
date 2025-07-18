# data_filter.py - Independent filtering module
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date

class DataFilter:
    """
    Independent filtering class that handles all data filtering logic
    Returns filtered dataframes without scope issues
    """
    
    def __init__(self, df):
        """Initialize with original dataframe"""
        self.original_df = df.copy()
        self.filtered_df = df.copy()
        self.filter_info = {
            'active': False,
            'type': None,
            'original_count': len(df),
            'filtered_count': len(df),
            'filters_applied': []
        }
    
    def get_column_info(self):
        """Get column type information"""
        return {
            'numeric': self.original_df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': self.original_df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime': self.original_df.select_dtypes(include=['datetime64']).columns.tolist(),
            'all': self.original_df.columns.tolist()
        }
    
    def render_filter_ui(self):
        """
        Render the filtering UI and return filtered dataframe
        Returns: (filtered_df, filter_applied)
        """
        st.markdown("*Filter data using simple controls, advanced queries, or join datasets*")
        
        # Check if multiple datasets are available for joining
        datasets = st.session_state.get('datasets', {})
        
        if len(datasets) > 1:
            # Filter type selection with join option
            filter_type = st.radio(
                "Choose operation:",
                ["🎛️ Simple Filters", "⚡ Query Builder", "🔗 Join Datasets"],
                horizontal=True
            )
        else:
            # Filter type selection without join option
            filter_type = st.radio(
                "Choose filter mode:",
                ["🎛️ Simple Filters", "⚡ Query Builder"],
                horizontal=True
            )
        
        filtered_df = self.original_df.copy()
        filters_applied = False
        applied_filter_details = []
        
        if filter_type == "🎛️ Simple Filters":
            filtered_df, filters_applied, applied_filter_details = self._simple_filters()
        elif filter_type == "⚡ Query Builder":
            filtered_df, filters_applied, applied_filter_details = self._query_builder()
        elif filter_type == "🔗 Join Datasets":
            filtered_df, filters_applied, applied_filter_details = self._join_datasets()
        else:
            filtered_df, filters_applied, applied_filter_details = self._simple_filters()
        
        # Update internal state
        self.filtered_df = filtered_df
        self.filter_info = {
            'active': filters_applied,
            'type': filter_type,
            'original_count': len(self.original_df),
            'filtered_count': len(filtered_df),
            'filters_applied': applied_filter_details
        }
        
        # Show filter results
        if filters_applied:
            reduction_pct = ((len(self.original_df) - len(filtered_df)) / len(self.original_df) * 100)
            st.info(f"🔍 **Filtered:** {len(filtered_df):,} rows ({reduction_pct:.1f}% reduction)")
        
        return filtered_df, filters_applied
    
    def _simple_filters(self):
        """Handle simple filtering UI"""
        column_info = self.get_column_info()
        
        filter_columns = st.multiselect(
            "Select columns to filter:",
            options=self.original_df.columns.tolist(),
            help="Choose columns to create filters for"
        )
        
        if not filter_columns:
            return self.original_df.copy(), False, []
        filtered_df = self.original_df.copy()
        filters_applied = False
        applied_filter_details = []
        
        filter_cols = st.columns(min(2, len(filter_columns)))
        
        for i, col in enumerate(filter_columns):
            with filter_cols[i % 2]:
                st.write(f"**{col}** *({self.original_df[col].dtype})*")
                
                if self.original_df[col].dtype in ['object', 'category']:
                    filtered_df, col_filtered, filter_detail = self._handle_categorical_filter(filtered_df, col)
                elif self.original_df[col].dtype in ['int64', 'float64']:
                    filtered_df, col_filtered, filter_detail = self._handle_numeric_filter(filtered_df, col)
                elif 'datetime' in str(self.original_df[col].dtype):
                    filtered_df, col_filtered, filter_detail = self._handle_datetime_filter(filtered_df, col)
                
                if col_filtered:
                    filters_applied = True
                    applied_filter_details.append(filter_detail)
        
        return filtered_df, filters_applied, applied_filter_details
    
    def _join_datasets(self):
        """Handle dataset joining"""
        st.subheader("🔗 Join Datasets")
        
        datasets = st.session_state.get('datasets', {})
        dataset_names = list(datasets.keys())
        
        if len(dataset_names) < 2:
            st.warning("Need at least 2 datasets to perform join")
            return self.original_df.copy(), False, []
        
        # Find current dataset name
        current_dataset_name = None
        for name, df in datasets.items():
            if df.equals(self.original_df):
                current_dataset_name = name
                break
        
        join_col1, join_col2, join_col3 = st.columns(3)
        
        with join_col1:
            # Set current dataset as default left dataset
            left_default_idx = dataset_names.index(current_dataset_name) if current_dataset_name in dataset_names else 0
            left_dataset = st.selectbox("Left Dataset:", dataset_names, index=left_default_idx, key="left_ds")
            
        with join_col2:
            right_options = [name for name in dataset_names if name != left_dataset]
            right_dataset = st.selectbox("Right Dataset:", right_options, key="right_ds")
            
        with join_col3:
            join_type = st.selectbox(
                "Join Type:",
                ["inner", "left", "right", "outer"],
                help="Inner: Only matching rows | Left: All left + matches | Right: All right + matches | Outer: Everything",
                key="join_type"
            )
        
        if left_dataset and right_dataset:
            left_df = datasets[left_dataset].copy()
            right_df = datasets[right_dataset].copy()
            
            join_key_col1, join_key_col2 = st.columns(2)
            
            with join_key_col1:
                left_key = st.selectbox(
                    f"Join key from {left_dataset}:",
                    left_df.columns.tolist(),
                    key="left_key"
                )
                
            with join_key_col2:
                right_key = st.selectbox(
                    f"Join key from {right_dataset}:",
                    right_df.columns.tolist(),
                    key="right_key"
                )
            
            # Data type compatibility check
            if left_key and right_key:
                left_dtype = str(left_df[left_key].dtype)
                right_dtype = str(right_df[right_key].dtype)
                
                compatibility_col1, compatibility_col2 = st.columns(2)
                
                with compatibility_col1:
                    if left_dtype == right_dtype:
                        st.success(f"✅ Compatible types: `{left_dtype}`")
                        compatibility = True
                    else:
                        st.warning(f"⚠️ Type mismatch: `{left_dtype}` vs `{right_dtype}`")
                        compatibility = False
                
                with compatibility_col2:
                    auto_fix = st.checkbox(
                        "🔧 Auto-fix types", 
                        value=not compatibility,
                        help="Automatically convert data types to enable joining"
                    )
                
                # Join button
                if st.button("🔗 **Join Datasets**", type="primary", key="join_button"):
                    try:
                        left_prep = left_df.copy()
                        right_prep = right_df.copy()
                        
                        # Auto-fix data types if requested
                        if auto_fix and not compatibility:
                            try:
                                if 'object' in [left_dtype, right_dtype]:
                                    left_prep[left_key] = left_prep[left_key].astype(str)
                                    right_prep[right_key] = right_prep[right_key].astype(str)
                                elif 'int' in left_dtype and 'float' in right_dtype:
                                    left_prep[left_key] = left_prep[left_key].astype(float)
                                elif 'float' in left_dtype and 'int' in right_dtype:
                                    right_prep[right_key] = right_prep[right_key].astype(float)
                            except Exception as conv_error:
                                st.warning(f"Type conversion failed: {conv_error}")
                        
                        # Perform the join
                        joined_df = pd.merge(
                            left_prep, 
                            right_prep, 
                            left_on=left_key, 
                            right_on=right_key, 
                            how=join_type,
                            suffixes=('_left', '_right')
                        )
                        
                        # Success metrics
                        success_col1, success_col2, success_col3, success_col4 = st.columns(4)
                        with success_col1:
                            st.metric("✅ Result Rows", f"{len(joined_df):,}")
                        with success_col2:
                            st.metric("📊 Columns", len(joined_df.columns))
                        with success_col3:
                            efficiency = len(joined_df) / max(len(left_df), len(right_df)) * 100
                            st.metric("🎯 Efficiency", f"{efficiency:.1f}%")
                        with success_col4:
                            st.metric("🔗 Join Type", join_type.title())
                        
                        # Update the filter's original data to the joined result
                        self.original_df = joined_df.copy()
                        
                        return joined_df.copy(), True, [f"Joined {left_dataset} + {right_dataset} on {left_key}/{right_key}"]
                        
                    except Exception as e:
                        st.error(f"❌ Join failed: {str(e)}")
                        if "dtype" in str(e).lower():
                            st.info("💡 **Try**: Enable 'Auto-fix types' option")
        
        return self.original_df.copy(), False, []
        
    
    def _handle_categorical_filter(self, df, col):
        """Handle categorical column filtering"""
        unique_values = self.original_df[col].unique()
        
        if len(unique_values) <= 50:
            selected_values = st.multiselect(
                "Select values:",
                options=unique_values,
                default=unique_values,
                key=f"filter_{col}"
            )
            if len(selected_values) < len(unique_values):
                df = df[df[col].isin(selected_values)]
                return df, True, f"{col}: {len(selected_values)}/{len(unique_values)} values"
        else:
            search_term = st.text_input(f"Search in {col}:", key=f"search_{col}")
            if search_term:
                df = df[df[col].str.contains(search_term, case=False, na=False)]
                return df, True, f"{col}: contains '{search_term}'"
        
        return df, False, ""
    
    def _handle_numeric_filter(self, df, col):
        """Enhanced numeric column filtering with synchronized slider and manual input"""
        min_val, max_val = float(self.original_df[col].min()), float(self.original_df[col].max())
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Min Value", f"{min_val:.2f}")
        with col_info2:
            st.metric("Max Value", f"{max_val:.2f}")
        with col_info3:
            unique_count = self.original_df[col].nunique()
            st.metric("Unique Values", unique_count)

        # Input method selection
        filter_method = st.radio(
            "Filter method:",
            ["🎛️ Slider", "📝 Manual Input", "🔄 Both"],
            horizontal=True,
            key=f"method_{col}"
        )
        
        if filter_method == "🎛️ Slider":
            selected_range = st.slider(
                "Value range:",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                key=f"range_{col}"
            )
            final_min, final_max = selected_range
        
        elif filter_method == "📝 Manual Input":
            input_col1, input_col2 = st.columns(2)
            with input_col1:
                final_min = st.number_input(
                    "Minimum:",
                    value=min_val,
                    min_value=min_val,
                    max_value=max_val,
                    key=f"manual_min_{col}",
                    format="%.4f",
                    step=1.0
                )
            with input_col2:
                final_max = st.number_input(
                    "Maximum:",
                    value=max_val,
                    min_value=min_val,
                    max_value=max_val,
                    key=f"manual_max_{col}",
                    format="%.4f",
                    step=1.0                )
        
        else:  # Both method
            st.write("**Slider:**")
            selected_range = st.slider(
                "Quick selection:",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                key=f"range_{col}"
            )
            
            st.write("**Fine-tune with manual input:**")
            input_col1, input_col2 = st.columns(2)
            with input_col1:
                final_min = st.number_input(
                    "Exact minimum:",
                    value=float(selected_range[0]),
                    min_value=min_val,
                    max_value=max_val,
                    key=f"manual_min_{col}",
                    format="%.4f",
                    step=1.0
                )
            with input_col2:
                final_max = st.number_input(
                    "Exact maximum:",
                    value=float(selected_range[1]),
                    min_value=min_val,
                    max_value=max_val,
                    key=f"manual_max_{col}",
                    format="%.4f",
                    step=1.0
                )
        
        # Validation and filtering
        if final_min > final_max:
            st.error(f"❌ Minimum ({final_min}) cannot be greater than maximum ({final_max})")
            return df, False, ""
        
        # Apply filter if values changed
        if (final_min != min_val or final_max != max_val):
            filtered_df = df[(df[col] >= final_min) & (df[col] <= final_max)]
            
            # Show filter summary
            rows_before = len(df)
            rows_after = len(filtered_df)
            reduction = ((rows_before - rows_after) / rows_before * 100) if rows_before > 0 else 0
            
            st.success(f"✅ Filter applied: {rows_after:,} rows ({reduction:.1f}% filtered)")
            
            return filtered_df, True, f"{col}: {final_min} to {final_max}"
        
        return df, False, ""
    
    def _handle_datetime_filter(self, df, col):
        """Handle datetime column filtering"""
        min_date = self.original_df[col].min().date()
        max_date = self.original_df[col].max().date()
        
        date_range = st.date_input(
            "Date range:",
            value=(min_date, max_date),
            key=f"date_{col}"
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            if start_date != min_date or end_date != max_date:
                df = df[(df[col].dt.date >= start_date) & (df[col].dt.date <= end_date)]
                return df, True, f"{col}: {start_date} to {end_date}"
        
        return df, False, ""
    
    def _query_builder(self):
        """Handle query builder filtering with  UI-based construction"""
        st.subheader("⚡ Query Builder")
        
        # Validate data exists
        if self.original_df.empty:
            st.warning("No data available for querying")
            return self.original_df.copy(), False, []
        
        # Get column info 
        try:
            numeric_cols = self.original_df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = self.original_df.select_dtypes(include=['object', 'category']).columns.tolist()
            all_cols = self.original_df.columns.tolist()
        except Exception as e:
            st.error(f"Error accessing column information: {str(e)}")
            return self.original_df.copy(), False, []
        
        if not all_cols:
            st.warning("No columns available for querying")
            return self.original_df.copy(), False, []
        
        # Build query using UI components
        query_parts = []
        
        # Add multiple conditions
        num_conditions = st.number_input("Number of conditions:", 1, 5, 1, key="query_num_conditions")
        
        for i in range(num_conditions):
            st.markdown(f"**Condition {i+1}:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                column = st.selectbox(
                    f"Column:", 
                    all_cols, 
                    key=f"query_col_{i}"
                )
            
            with col2:
                # Check column type and provide appropriate operators
                if column and column in numeric_cols:
                    operator = st.selectbox(
                        "Operator:", 
                        [">", "<", ">=", "<=", "==", "!="], 
                        key=f"query_op_{i}"
                    )
                    value = st.number_input(
                        "Value:", 
                        key=f"query_val_{i}"
                    )
                    # Safe query construction for numeric
                    query_parts.append(f"`{column}` {operator} {value}")
                    
                elif column and column in categorical_cols:
                    operator = st.selectbox(
                        "Operator:", 
                        ["==", "!=", "contains"], 
                        key=f"query_op_{i}"
                    )
                    value = st.text_input(
                        "Value:", 
                        key=f"query_val_{i}"
                    )
                    
                    # Safe query construction for categorical
                    if value:  # Only add if value is provided
                        if operator == "contains":
                            # Escape user input safely
                            escaped_value = value.replace("'", "\\'").replace('"', '\\"')
                            query_parts.append(f"`{column}`.str.contains('{escaped_value}', case=False, na=False)")
                        else:
                            escaped_value = value.replace("'", "\\'").replace('"', '\\"')
                            query_parts.append(f"`{column}` {operator} '{escaped_value}'")
                
                else:
                    # Fallback for other column types (datetime, etc.)
                    st.info(f"Column type: {self.original_df[column].dtype if column else 'Unknown'}")
                    operator = st.selectbox(
                        "Operator:", 
                        ["==", "!="], 
                        key=f"query_op_{i}"
                    )
                    value = st.text_input(
                        "Value:", 
                        key=f"query_val_{i}"
                    )
                    if value:
                        escaped_value = value.replace("'", "\\'").replace('"', '\\"')
                        query_parts.append(f"`{column}` {operator} '{escaped_value}'")
            
            with col3:
                if i < num_conditions - 1:
                    logic = st.selectbox(
                        "Logic:", 
                        ["and", "or"], 
                        key=f"query_logic_{i}"
                    )
                    if len(query_parts) > 0:  # Only add logic if we have a condition
                        query_parts.append(logic)
        
        # Show generated query (safe to display)
        if query_parts:
            # Remove any trailing logic operators
            if query_parts[-1] in ["and", "or"]:
                query_parts.pop()
            
            final_query = " ".join(query_parts)
            
            if final_query.strip():  # Only show if we have a real query
                st.subheader("📋 Generated Query")
                st.code(final_query, language="python")
                
                if st.button("🔍 **Apply Query**", key="apply_safe_query"):
                    try:
                        # This is now safe because we control the query construction
                        filtered_df = self.original_df.query(final_query)
                        st.success(f"✅ Query applied: {len(filtered_df):,} rows returned")
                        return filtered_df, True, [f"Safe Query: {final_query}"]
                    except Exception as e:
                        st.error(f"Query error: {str(e)}")
                        st.info("💡 Try adjusting your conditions or check data types")
        
        # Show example for guidance
        with st.expander("💡 Query Builder Help"):
            st.markdown("""
            **How to use:**
            1. Select number of conditions
            2. For each condition, choose column, operator, and value
            3. Use 'and'/'or' to combine conditions
            
            **Safe operators:**
            - **Numeric**: >, <, >=, <=, ==, !=
            - **Text**: ==, !=, contains
            
            """)
        
        return self.original_df.copy(), False, []
    
    def get_filtered_data(self):
        """Get current filtered dataframe"""
        return self.filtered_df.copy()
    
    def get_filter_info(self):
        """Get current filter information"""
        return self.filter_info.copy()
    
    def clear_filters(self):
        """Clear all filters and return original data"""
        self.filtered_df = self.original_df.copy()
        self.filter_info = {
            'active': False,
            'type': None,
            'original_count': len(self.original_df),
            'filtered_count': len(self.original_df),
            'filters_applied': []
        }
        return self.filtered_df.copy()
    
    def render_filter_summary(self):
        """Render filter summary if filters are active"""
        if self.filter_info['active']:
            filter_col1, filter_col2 = st.columns([4, 1])
            
            with filter_col1:
                reduction_pct = ((self.filter_info['original_count'] - self.filter_info['filtered_count']) / self.filter_info['original_count'] * 100)
                st.markdown(f"""
                🔍 **Active Filter:** {self.filter_info['type']} • 
                Showing **{self.filter_info['filtered_count']:,}** of **{self.filter_info['original_count']:,}** rows 
                ({reduction_pct:.1f}% filtered)
                """)
            
            with filter_col2:
                if st.button("❌ Clear All Filters", key="clear_filters"):
                    return True  # Signal to clear filters
        
        return False  # No clear action